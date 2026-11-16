
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def get_states(snapshot):
    return {
        service.service_id: service.state
        for service in snapshot.services
    }


def test_api_waits_for_database_to_recover():
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

    initial = SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
            ServiceSnapshot(
                service_id="api",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
        ),
    )

    fault = Fault(
        service_id="database",
        start_step=1,
        clear_step=2,
    )

    # Step 1: Database goes down.
    step_one = advance_snapshot(topology, initial, (fault,))
    states = get_states(step_one)

    assert states["database"] == ServiceState.DOWN
    assert states["api"] == ServiceState.HEALTHY

    # Step 2: Database starts recovering.
    # API still sees the database as DOWN in the previous snapshot.
    step_two = advance_snapshot(topology, step_one, (fault,))
    states = get_states(step_two)

    assert states["database"] == ServiceState.RECOVERING
    assert states["api"] == ServiceState.DOWN

    # Step 3: Database recovers.
    # API sees the database as RECOVERING in the previous snapshot.
    step_three = advance_snapshot(topology, step_two, (fault,))
    states = get_states(step_three)

    assert states["database"] == ServiceState.HEALTHY
    assert states["api"] == ServiceState.DEGRADED

    # Step 4: API begins its own recovery.
    step_four = advance_snapshot(topology, step_three, (fault,))
    states = get_states(step_four)

    assert states["api"] == ServiceState.RECOVERING

    # Step 5: API completes recovery.
    step_five = advance_snapshot(topology, step_four, (fault,))
    states = get_states(step_five)

    assert states["api"] == ServiceState.HEALTHY


