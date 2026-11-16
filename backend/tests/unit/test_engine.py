
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def make_initial_snapshot(service_ids: list[str]) -> SimulationSnapshot:
    """Create a healthy initial snapshot at step zero."""
    return SimulationSnapshot(
        step=0,
        services=tuple(
            ServiceSnapshot(
                service_id=service_id,
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            )
            for service_id in service_ids
        ),
    )


def test_database_fault_does_not_propagate_in_same_step():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    })

    initial = make_initial_snapshot(["database", "api"])
    fault = Fault(service_id="database", start_step=1)

    result = advance_snapshot(topology, initial, (fault,))

    states = {
        service.service_id: service.state
        for service in result.services
    }

    assert result.step == 1
    assert states["database"] == ServiceState.DOWN
    assert states["api"] == ServiceState.HEALTHY


def test_database_failure_propagates_to_api_on_next_step():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    })

    initial = make_initial_snapshot(["database", "api"])
    fault = Fault(service_id="database", start_step=1)

    first_step = advance_snapshot(topology, initial, (fault,))
    second_step = advance_snapshot(topology, first_step, (fault,))

    states = {
        service.service_id: service.state
        for service in second_step.services
    }

    assert second_step.step == 2
    assert states["database"] == ServiceState.DOWN
    assert states["api"] == ServiceState.DOWN


def test_soft_dependency_failure_degrades_dependent_service():
    topology = load_topology({
        "services": [
            {"id": "cache", "name": "Cache"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "cache",
                "criticality": "soft",
            }
        ],
    })

    initial = make_initial_snapshot(["cache", "api"])
    fault = Fault(service_id="cache", start_step=1)

    first_step = advance_snapshot(topology, initial, (fault,))
    second_step = advance_snapshot(topology, first_step, (fault,))

    states = {
        service.service_id: service.state
        for service in second_step.services
    }

    assert states["cache"] == ServiceState.DOWN
    assert states["api"] == ServiceState.DEGRADED


def test_independent_service_remains_healthy():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
            {"id": "worker", "name": "Worker"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    })

    initial = make_initial_snapshot(
        ["database", "api", "worker"]
    )
    fault = Fault(service_id="database", start_step=1)

    first_step = advance_snapshot(topology, initial, (fault,))
    second_step = advance_snapshot(topology, first_step, (fault,))

    states = {
        service.service_id: service.state
        for service in second_step.services
    }

    assert states["worker"] == ServiceState.HEALTHY
