
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


def test_soft_dependency_allows_recovery_but_blocks_healthy():
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

    initial = SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="cache",
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
        service_id="cache",
        start_step=1,
        clear_step=2,
    )

    # Step 1: Cache goes down; API has not yet observed the failure.
    step_one = advance_snapshot(topology, initial, (fault,))
    states = get_states(step_one)

    assert states["cache"] == ServiceState.DOWN
    assert states["api"] == ServiceState.HEALTHY

    # Step 2: Cache starts recovering.
    # API becomes degraded because its soft dependency was DOWN.
    step_two = advance_snapshot(topology, step_one, (fault,))
    states = get_states(step_two)

    assert states["cache"] == ServiceState.RECOVERING
    assert states["api"] == ServiceState.DEGRADED

    # Step 3: Cache becomes healthy.
    # API can enter recovery because a recovering soft dependency
    # does not impose a degraded-state constraint.
    step_three = advance_snapshot(topology, step_two, (fault,))
    states = get_states(step_three)

    assert states["cache"] == ServiceState.HEALTHY
    assert states["api"] == ServiceState.RECOVERING

    # Step 4: API becomes healthy after its dependency is healthy.
    step_four = advance_snapshot(topology, step_three, (fault,))
    states = get_states(step_four)

    assert states["api"] == ServiceState.HEALTHY
