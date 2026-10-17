"""Graph builder: constructs DependencyGraph from analyzed Python files."""

from typing import Dict, List, Optional
from engine.ast_parser import PythonFileAnalyzer, ASTDefinition
from engine.graph import DependencyGraph, GraphNode, GraphEdge

def make_node_id(file_path: str, def_name: str, parent_class: Optional[str] = None) -> str:
    norm_path = file_path.replace("\\", "/").strip("/")
    if parent_class:
        return f"{norm_path}::{parent_class}.{def_name}"
    return f"{norm_path}::{def_name}"

def build_dependency_graph(analyzers: List[PythonFileAnalyzer]) -> DependencyGraph:
    graph = DependencyGraph()

    # 1. Register all nodes and build name lookup tables
    # lookup by short name: name -> list of node_ids
    name_to_nodes: Dict[str, List[str]] = {}
    # lookup by module + name
    module_to_nodes: Dict[str, List[str]] = {}

    for analyzer in analyzers:
        file_path = analyzer.file_path
        # Derive module name from file path: e.g. billing/pricing.py -> billing.pricing
        mod_key = file_path.replace("/", ".").replace(".py", "")

        for d in analyzer.definitions:
            node_id = make_node_id(file_path, d.name, d.parent_class)
            
            node_type = d.def_type
            if d.is_endpoint:
                node_type = "endpoint"
            elif d.is_test:
                node_type = "test"

            metadata = {
                "docstring": d.docstring,
                "decorators": d.decorators,
                "is_endpoint": d.is_endpoint,
                "endpoint_info": d.endpoint_info,
                "is_test": d.is_test
            }

            node = GraphNode(
                node_id=node_id,
                name=d.name,
                node_type=node_type,
                file_path=file_path,
                lineno=d.lineno,
                end_lineno=d.end_lineno,
                parent_class=d.parent_class,
                is_endpoint=d.is_endpoint,
                is_test=d.is_test,
                metadata=metadata
            )
            graph.add_node(node)

            name_to_nodes.setdefault(d.name, []).append(node_id)
            module_to_nodes.setdefault(f"{mod_key}.{d.name}", []).append(node_id)

    # 2. Build edges based on AST calls and imports
    for analyzer in analyzers:
        file_path = analyzer.file_path

        # Map local imported names to target modules
        imported_symbols: Dict[str, str] = {}
        for imp in analyzer.imports:
            if imp["type"] == "from":
                target_mod = imp["module"]
                sym_name = imp.get("name")
                alias = imp.get("alias", sym_name)
                imported_symbols[alias] = f"{target_mod}.{sym_name}" if target_mod else sym_name
            elif imp["type"] == "import":
                imported_symbols[imp["alias"]] = imp["module"]

        for d in analyzer.definitions:
            source_id = make_node_id(file_path, d.name, d.parent_class)

            for call in d.calls:
                target_call_name = call["target_name"]
                lineno = call["lineno"]
                resolved_target_id = None
                evidence = ""

                # Check if target_call_name is an imported alias
                if target_call_name in imported_symbols:
                    full_sym = imported_symbols[target_call_name]
                    # Check in module_to_nodes
                    if full_sym in module_to_nodes and module_to_nodes[full_sym]:
                        resolved_target_id = module_to_nodes[full_sym][0]
                        evidence = f"Imported call to {full_sym} at line {lineno}"
                    # Fallback to name_to_nodes
                    elif full_sym.split(".")[-1] in name_to_nodes:
                        resolved_target_id = name_to_nodes[full_sym.split(".")[-1]][0]
                        evidence = f"Direct AST call to {target_call_name} at line {lineno}"

                # Check dot attribute calls: e.g. obj.method or mod.func
                elif "." in target_call_name:
                    parts = target_call_name.split(".")
                    attr_name = parts[-1]
                    prefix = parts[0]
                    # If prefix was imported module:
                    if prefix in imported_symbols:
                        full_mod = imported_symbols[prefix]
                        qualified = f"{full_mod}.{attr_name}"
                        if qualified in module_to_nodes and module_to_nodes[qualified]:
                            resolved_target_id = module_to_nodes[qualified][0]
                            evidence = f"Qualified call to {qualified} at line {lineno}"

                    if not resolved_target_id and attr_name in name_to_nodes:
                        # Match candidate
                        resolved_target_id = name_to_nodes[attr_name][0]
                        evidence = f"Method invocation of .{attr_name}() at line {lineno}"

                # Check simple function name
                elif target_call_name in name_to_nodes:
                    # Filter out self-calls or choose most likely
                    candidates = [nid for nid in name_to_nodes[target_call_name] if nid != source_id]
                    if candidates:
                        resolved_target_id = candidates[0]
                        evidence = f"Direct function call to {target_call_name}() at line {lineno}"

                if resolved_target_id and resolved_target_id in graph.nodes:
                    graph.add_edge(GraphEdge(
                        source_id=source_id,
                        target_id=resolved_target_id,
                        edge_type="calls",
                        evidence=evidence,
                        lineno=lineno
                    ))

    return graph
