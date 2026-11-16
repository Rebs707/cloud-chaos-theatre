
import networkx as nx

from app.models.topology import load_topology
from app.simulation.graph import build_dependency_graph


def service(service_id):
    return {"id": service_id, "name": service_id.title()}


def test_graph_contains_all_services():
    topology = load_topology({
        "services": [service("api"), service("database")],
        "edges": [],
    })

    graph = build_dependency_graph(topology)

    assert set(graph.nodes) == {"api", "database"}
    assert graph.nodes["api"]["name"] == "Api"


def test_dependency_direction_is_correct():
    topology = load_topology({
        "services": [service("api"), service("database")],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    })

    graph = build_dependency_graph(topology)

    assert graph.has_edge("api", "database")
    assert list(graph.predecessors("database")) == ["api"]


def test_hard_and_soft_dependencies_are_preserved():
    topology = load_topology({
        "services": [
            service("api"),
            service("database"),
            service("cache"),
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            },
            {
                "dependent": "api",
                "dependency": "cache",
                "criticality": "soft",
            },
        ],
    })

    graph = build_dependency_graph(topology)

    assert graph["api"]["database"]["criticality"] == "hard"
    assert graph["api"]["cache"]["criticality"] == "soft"


def test_cycles_are_preserved():
    topology = load_topology({
        "services": [service("api"), service("database")],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            },
            {
                "dependent": "database",
                "dependency": "api",
                "criticality": "soft",
            },
        ],
    })

    graph = build_dependency_graph(topology)

    assert isinstance(graph, nx.DiGraph)
    assert nx.is_directed_acyclic_graph(graph) is False
    assert graph.has_edge("api", "database")
    assert graph.has_edge("database", "api")


def test_empty_topology_creates_empty_graph():
    topology = load_topology({
        "services": [],
        "edges": [],
    })

    graph = build_dependency_graph(topology)

    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
