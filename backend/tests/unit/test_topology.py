
import pytest

from app.models.topology import load_topology, TopologyValidationError


def service(service_id):
    return {"id": service_id, "name": service_id.title()}


def test_valid_topology_is_accepted():
    data = {
        "services": [service("api"), service("database")],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    }

    topology = load_topology(data)

    assert len(topology.services) == 2
    assert len(topology.edges) == 1


@pytest.mark.parametrize(
    "data",
    [
        {
            "services": [service("api"), service("api")],
            "edges": [],
        },
        {
            "services": [service("api")],
            "edges": [
                {
                    "dependent": "api",
                    "dependency": "api",
                    "criticality": "hard",
                }
            ],
        },
        {
            "services": [service("api")],
            "edges": [
                {
                    "dependent": "api",
                    "dependency": "missing",
                    "criticality": "hard",
                }
            ],
        },
        {
            "services": [service("api"), service("database")],
            "edges": [
                {
                    "dependent": "api",
                    "dependency": "database",
                    "criticality": "medium",
                }
            ],
        },
        {
            "services": [service("api"), service("database")],
            "edges": [
                {
                    "dependent": "api",
                    "dependency": "database",
                    "criticality": "hard",
                },
                {
                    "dependent": "api",
                    "dependency": "database",
                    "criticality": "soft",
                },
            ],
        },
    ],
)
def test_invalid_topologies_are_rejected(data):
    with pytest.raises(TopologyValidationError):
        load_topology(data)


def test_missing_criticality_is_rejected():
    data = {
        "services": [service("api"), service("database")],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
            }
        ],
    }

    with pytest.raises(TopologyValidationError):
        load_topology(data)


def test_cycles_are_allowed():
    data = {
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
    }

    topology = load_topology(data)

    assert len(topology.edges) == 2


def test_service_ids_must_be_valid():
    data = {
        "services": [{"id": "Bad_Id", "name": "Invalid ID"}],
        "edges": [],
    }

    with pytest.raises(TopologyValidationError):
        load_topology(data)
