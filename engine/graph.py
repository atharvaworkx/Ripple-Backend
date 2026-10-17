"""In-memory dependency graph for codebase impact analysis."""

from typing import Dict, List, Any, Optional, Set

class GraphNode:
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str,  # 'function', 'method', 'class', 'endpoint', 'test'
        file_path: str,
        lineno: int,
        end_lineno: int,
        parent_class: Optional[str] = None,
        is_endpoint: bool = False,
        is_test: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.file_path = file_path.replace("\\", "/")
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.parent_class = parent_class
        self.is_endpoint = is_endpoint
        self.is_test = is_test
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "name": self.name,
            "type": self.node_type,
            "file_path": self.file_path,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "parent_class": self.parent_class,
            "is_endpoint": self.is_endpoint,
            "is_test": self.is_test,
            "metadata": self.metadata
        }

class GraphEdge:
    def __init__(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,  # 'calls', 'imports', 'contains'
        evidence: str,
        lineno: Optional[int] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.evidence = evidence
        self.lineno = lineno

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type,
            "evidence": self.evidence,
            "lineno": self.lineno
        }

class DependencyGraph:
    """Directed dependency graph storing functions, classes, endpoints, and calls."""
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        # outgoing: source_id -> list of (target_id, GraphEdge)
        self.adjacency: Dict[str, List[GraphEdge]] = {}
        # incoming: target_id -> list of (source_id, GraphEdge)
        self.reverse_adjacency: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []
        if node.node_id not in self.reverse_adjacency:
            self.reverse_adjacency[node.node_id] = []

    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        self.adjacency.setdefault(edge.source_id, []).append(edge)
        self.reverse_adjacency.setdefault(edge.target_id, []).append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id)

    def get_callers(self, node_id: str) -> List[GraphEdge]:
        """Nodes that call or depend on node_id (incoming edges)."""
        return self.reverse_adjacency.get(node_id, [])

    def get_callees(self, node_id: str) -> List[GraphEdge]:
        """Nodes that node_id calls (outgoing edges)."""
        return self.adjacency.get(node_id, [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges]
        }
