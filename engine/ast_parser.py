"""AST parsing engine for Python codebases."""

import ast
from typing import List, Dict, Any, Optional, Set, Tuple

class ASTDefinition:
    def __init__(
        self,
        name: str,
        def_type: str,  # 'function', 'method', 'class'
        lineno: int,
        end_lineno: int,
        parent_class: Optional[str] = None,
        docstring: Optional[str] = None,
        calls: Optional[List[Dict[str, Any]]] = None,
        decorators: Optional[List[str]] = None,
        is_test: bool = False,
        is_endpoint: bool = False,
        endpoint_info: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.def_type = def_type
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.parent_class = parent_class
        self.docstring = docstring
        self.calls = calls or []
        self.decorators = decorators or []
        self.is_test = is_test
        self.is_endpoint = is_endpoint
        self.endpoint_info = endpoint_info or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "def_type": self.def_type,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "parent_class": self.parent_class,
            "docstring": self.docstring,
            "calls": self.calls,
            "decorators": self.decorators,
            "is_test": self.is_test,
            "is_endpoint": self.is_endpoint,
            "endpoint_info": self.endpoint_info
        }

class CallVisitor(ast.NodeVisitor):
    """Visits function and method bodies to record all outgoing calls."""
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        call_name = ""
        callee_type = "function"

        if isinstance(func, ast.Name):
            call_name = func.id
        elif isinstance(func, ast.Attribute):
            # e.g., obj.method() or module.func()
            callee_type = "attribute"
            prefix = ""
            if isinstance(func.value, ast.Name):
                prefix = func.value.id
            call_name = f"{prefix}.{func.attr}" if prefix else func.attr
        
        if call_name:
            self.calls.append({
                "target_name": call_name,
                "callee_type": callee_type,
                "lineno": node.lineno
            })
        self.generic_visit(node)

class PythonFileAnalyzer:
    """Analyzes a single Python source file using AST."""
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path.replace("\\", "/")
        self.source_code = source_code
        self.syntax_error: Optional[str] = None
        self.tree: Optional[ast.AST] = None
        self.imports: List[Dict[str, Any]] = []
        self.definitions: List[ASTDefinition] = []

    def analyze(self) -> bool:
        """Parse source code and extract AST metadata."""
        try:
            self.tree = ast.parse(self.source_code, filename=self.file_path)
        except SyntaxError as e:
            self.syntax_error = f"Syntax error at line {e.lineno}: {e.msg}"
            return False
        except Exception as e:
            self.syntax_error = str(e)
            return False

        self._extract_imports()
        self._extract_definitions()
        return True

    def _extract_imports(self):
        """Extract all import statements."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname or alias.name,
                        "lineno": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    self.imports.append({
                        "type": "from",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname or alias.name,
                        "lineno": node.lineno
                    })

    def _extract_decorator_name(self, dec_node: ast.expr) -> Tuple[str, Dict[str, str]]:
        """Extract decorator representation and detect HTTP route patterns."""
        route_info: Dict[str, str] = {}
        dec_str = ""

        if isinstance(dec_node, ast.Name):
            dec_str = dec_node.id
        elif isinstance(dec_node, ast.Attribute):
            dec_str = f"{ast.unparse(dec_node.value)}.{dec_node.attr}"
        elif isinstance(dec_node, ast.Call):
            func = dec_node.func
            dec_str = ast.unparse(func)
            # Detect route decorators e.g. @app.get('/path'), @api_router.post('/path')
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in dec_str.lower():
                    route_info["http_method"] = method.upper()
                    if dec_node.args and isinstance(dec_node.args[0], ast.Constant):
                        route_info["path"] = str(dec_node.args[0].value)
                    break

        return dec_str, route_info

    def _extract_definitions(self):
        """Extract top-level and class-level functions and classes."""
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self._record_function(node, parent_class=None)
            elif isinstance(node, ast.ClassDef):
                self._record_class(node)

    def _record_function(self, node: ast.FunctionDef, parent_class: Optional[str] = None):
        """Record function / method definition."""
        decorators: List[str] = []
        is_endpoint = False
        endpoint_info = {}

        for d in node.decorator_list:
            dec_name, r_info = self._extract_decorator_name(d)
            decorators.append(dec_name)
            if r_info:
                is_endpoint = True
                endpoint_info = r_info

        # Extract calls within body
        visitor = CallVisitor()
        for stmt in node.body:
            visitor.visit(stmt)

        name = node.name
        is_test = name.startswith("test_") or (parent_class and parent_class.startswith("Test"))

        doc = ast.get_docstring(node)
        def_type = "method" if parent_class else "function"

        # Safe line ranges
        lineno = node.lineno
        end_lineno = getattr(node, "end_lineno", lineno)

        self.definitions.append(ASTDefinition(
            name=name,
            def_type=def_type,
            lineno=lineno,
            end_lineno=end_lineno,
            parent_class=parent_class,
            docstring=doc,
            calls=visitor.calls,
            decorators=decorators,
            is_test=is_test,
            is_endpoint=is_endpoint,
            endpoint_info=endpoint_info
        ))

    def _record_class(self, node: ast.ClassDef):
        """Record class definition and its internal methods."""
        lineno = node.lineno
        end_lineno = getattr(node, "end_lineno", lineno)
        doc = ast.get_docstring(node)
        is_test_class = node.name.startswith("Test")

        self.definitions.append(ASTDefinition(
            name=node.name,
            def_type="class",
            lineno=lineno,
            end_lineno=end_lineno,
            docstring=doc,
            is_test=is_test_class
        ))

        # Check methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                self._record_function(item, parent_class=node.name)

def find_definitions_intersecting_lines(
    definitions: List[ASTDefinition],
    line_ranges: List[Tuple[int, int]]
) -> List[ASTDefinition]:
    """Find AST definitions that overlap with changed line ranges."""
    matched = []
    for d in definitions:
        for (start, end) in line_ranges:
            # Overlap condition: start <= d.end_lineno and end >= d.lineno
            if start <= d.end_lineno and end >= d.lineno:
                matched.append(d)
                break
    return matched
