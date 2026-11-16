
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def test_service_waits_for_configured_recovery_duration():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })

    initial = SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="database",
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
    faulted = advance_snapshot(
        topology,
        initial,
        (fault,),
        recovery_duration=2,
    )

    assert faulted.services[0].state == ServiceState.DOWN

    # Step 2: Fault is cleared; recovery begins.
    recovering = advance_snapshot(
        topology,
        faulted,
        (fault,),
        recovery_duration=2,
    )

    assert recovering.services[0].state == ServiceState.RECOVERING
    assert recovering.services[0].recovery_counter == 1

    # Step 3: Recovery duration is satisfied.
    recovered = advance_snapshot(
        topology,
        recovering,
        (fault,),
        recovery_duration=2,
    )

    assert recovered.services[0].state == ServiceState.HEALTHY
    assert recovered.services[0].recovery_counter == 0
