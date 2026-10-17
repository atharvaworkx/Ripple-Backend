"""Impact analysis tracer and risk scoring engine."""

from typing import List, Dict, Any, Set, Optional
from engine.graph import DependencyGraph, GraphNode, GraphEdge

class ImpactFinding:
    def __init__(
        self,
        finding_id: str,
        title: str,
        category: str,  # verified_test_failure, statically_established_dependency, potential_behavioral_risk, missing_or_insufficient_test_coverage, unresolved_or_uncertain_dependency
        severity: str,  # HIGH, MEDIUM, LOW
        confidence: str,  # HIGH, MEDIUM, LOW
        affected_component: str,
        explanation: str,
        dependency_path: List[str],
        file_path: str,
        line_number: int,
        relevant_tests: List[str],
        recommended_validation: str,
        verified_by_execution: bool = False
    ):
        self.finding_id = finding_id
        self.title = title
        self.category = category
        self.severity = severity
        self.confidence = confidence
        self.affected_component = affected_component
        self.explanation = explanation
        self.dependency_path = dependency_path
        self.file_path = file_path
        self.line_number = line_number
        self.relevant_tests = relevant_tests
        self.recommended_validation = recommended_validation
        self.verified_by_execution = verified_by_execution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.finding_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "affected_component": self.affected_component,
            "explanation": self.explanation,
            "dependency_path": self.dependency_path,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "relevant_tests": self.relevant_tests,
            "recommended_validation": self.recommended_validation,
            "verified_by_execution": self.verified_by_execution
        }

def trace_impact(
    graph: DependencyGraph,
    changed_node_ids: List[str],
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Traverses reverse dependencies (callers) to identify affected components,
    API routes, and associated tests.
    """
    findings: List[ImpactFinding] = []
    affected_nodes: Dict[str, Dict[str, Any]] = {}
    finding_counter = 1

    # Traverse upward from changed nodes to find callers
    for start_id in changed_node_ids:
        start_node = graph.get_node(start_id)
        if not start_node:
            continue

        # Add changed node itself
        affected_nodes[start_id] = {
            "node": start_node.to_dict(),
            "depth": 0,
            "paths": [[start_id]],
            "is_source": True
        }

        # BFS Queue: (current_node_id, current_path, current_depth)
        queue = [(start_id, [start_id], 0)]
        visited_nodes: Set[str] = {start_id}

        while queue:
            curr_id, path, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # Incoming edges: who calls curr_id?
            incoming = graph.get_callers(curr_id)
            for edge in incoming:
                caller_id = edge.source_id
                caller_node = graph.get_node(caller_id)
                if not caller_node:
                    continue

                new_path = path + [caller_id]

                if caller_id not in affected_nodes:
                    affected_nodes[caller_id] = {
                        "node": caller_node.to_dict(),
                        "depth": depth + 1,
                        "paths": [new_path],
                        "is_source": False
                    }
                else:
                    if len(affected_nodes[caller_id]["paths"]) < 3:
                        affected_nodes[caller_id]["paths"].append(new_path)

                if caller_id not in visited_nodes:
                    visited_nodes.add(caller_id)
                    queue.append((caller_id, new_path, depth + 1))

    # Now synthesize evidence-backed findings for affected nodes
    for node_id, info in affected_nodes.items():
        node_data = info["node"]
        depth = info["depth"]
        is_source = info["is_source"]
        primary_path = info["paths"][0] if info["paths"] else [node_id]

        # Gather relevant tests for this node
        # Check if any tests call this node directly
        tests_calling_node = []
        for edge in graph.get_callers(node_id):
            source = graph.get_node(edge.source_id)
            if source and source.is_test:
                tests_calling_node.append(source.name)

        if is_source:
            # Finding for the modified component itself
            cat = "statically_established_dependency"
            sev = "HIGH"
            conf = "HIGH"
            title = f"Direct Change in {node_data['name']}"
            explanation = (
                f"Function '{node_data['name']}' in {node_data['file_path']} was directly modified by the commit/diff. "
                f"Any changes to return types, edge conditions, or precision directly impact all upstream consumers."
            )
            validation = f"Verify unit tests directly exercising {node_data['name']} across normal, boundary, and edge inputs."

            findings.append(ImpactFinding(
                finding_id=f"FIND-{finding_counter:03d}",
                title=title,
                category=cat,
                severity=sev,
                confidence=conf,
                affected_component=node_id,
                explanation=explanation,
                dependency_path=primary_path,
                file_path=node_data["file_path"],
                line_number=node_data["lineno"],
                relevant_tests=tests_calling_node,
                recommended_validation=validation,
                verified_by_execution=False
            ))
            finding_counter += 1

        elif node_data.get("is_endpoint"):
            # Public API endpoint is affected!
            title = f"Public API Route Affected: {node_data['name']}"
            endpoint_meta = node_data.get("metadata", {}).get("endpoint_info", {})
            http_method = endpoint_meta.get("http_method", "API")
            route_path = endpoint_meta.get("path", "")
            route_desc = f"{http_method} {route_path}" if route_path else node_data['name']

            explanation = (
                f"Public endpoint '{route_desc}' traces downstream to modified component. "
                f"Dependency path length: {depth} hops. Regressions here will directly break public clients or frontends."
            )
            validation = f"Run integration and contract tests against endpoint {route_desc} with representative client payloads."

            findings.append(ImpactFinding(
                finding_id=f"FIND-{finding_counter:03d}",
                title=title,
                category="potential_behavioral_risk",
                severity="HIGH",
                confidence="HIGH",
                affected_component=node_id,
                explanation=explanation,
                dependency_path=primary_path,
                file_path=node_data["file_path"],
                line_number=node_data["lineno"],
                relevant_tests=tests_calling_node,
                recommended_validation=validation,
                verified_by_execution=False
            ))
            finding_counter += 1

        elif not node_data.get("is_test"):
            # Internal service or helper function
            sev = "HIGH" if depth == 1 else "MEDIUM"
            title = f"Call-Chain Impact on {node_data['name']}"
            explanation = (
                f"Component '{node_data['name']}' at {node_data['file_path']} depends on modified behavior. "
                f"Separated by {depth} call hop(s) along confirmed AST call graph."
            )
            validation = f"Execute regression suite covering {node_data['name']}."

            findings.append(ImpactFinding(
                finding_id=f"FIND-{finding_counter:03d}",
                title=title,
                category="statically_established_dependency",
                severity=sev,
                confidence="HIGH" if depth == 1 else "MEDIUM",
                affected_component=node_id,
                explanation=explanation,
                dependency_path=primary_path,
                file_path=node_data["file_path"],
                line_number=node_data["lineno"],
                relevant_tests=tests_calling_node,
                recommended_validation=validation,
                verified_by_execution=False
            ))
            finding_counter += 1

    return {
        "affected_nodes": affected_nodes,
        "findings": [f.to_dict() for f in findings]
    }
