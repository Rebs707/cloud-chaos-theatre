
from hypothesis import given, settings, strategies as st

from app.models.topology import load_topology
from app.simulation.graph import build_dependency_graph


@st.composite
def random_topologies(draw):
    service_count = draw(st.integers(min_value=1, max_value=8))

    service_ids = [
        f"service-{index}"
        for index in range(service_count)
    ]

    possible_edges = [
        (dependent, dependency)
        for dependent in service_ids
        for dependency in service_ids
        if dependent != dependency
    ]

    if possible_edges:
        selected_indices = draw(
            st.sets(
                st.integers(
                    min_value=0,
                    max_value=len(possible_edges) - 1,
                ),
                max_size=len(possible_edges),
            )
        )
    else:
        selected_indices = set()

    edges = []

    for index in sorted(selected_indices):
        dependent, dependency = possible_edges[index]

        criticality = draw(
            st.sampled_from(["hard", "soft"])
        )

        edges.append({
            "dependent": dependent,
            "dependency": dependency,
            "criticality": criticality,
        })

    topology_data = {
        "services": [
            {"id": service_id, "name": service_id}
            for service_id in service_ids
        ],
        "edges": edges,
    }

    return topology_data, service_ids, edges


@settings(max_examples=100, deadline=None)
@given(random_topologies())
def test_random_topologies_preserve_all_services_and_edges(
    generated,
):
    topology_data, service_ids, expected_edges = generated

    topology = load_topology(topology_data)
    graph = build_dependency_graph(topology)

    # Every declared service must appear in the graph.
    assert set(graph.nodes) == set(service_ids)

    # Every declared dependency must be preserved.
    assert graph.number_of_edges() == len(expected_edges)

    for edge in expected_edges:
        dependent = edge["dependent"]
        dependency = edge["dependency"]
        criticality = edge["criticality"]

        assert graph.has_edge(dependent, dependency)

        assert (
            graph[dependent][dependency]["criticality"]
            == criticality
        )
