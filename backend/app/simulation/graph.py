
import networkx as nx

from app.models.topology import Topology


def build_dependency_graph(topology: Topology) -> nx.DiGraph:
    """Build a directed dependency graph from a validated topology.

    Edge A -> B means service A depends on service B.
    graph.predecessors(B) returns services that depend on B.
    """
    graph = nx.DiGraph()

    for service in topology.services:
        graph.add_node(
            service.id,
            name=service.name,
        )

    for edge in topology.edges:
        graph.add_edge(
            edge.dependent,
            edge.dependency,
            criticality=edge.criticality,
        )

    return graph
