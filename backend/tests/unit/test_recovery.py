
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def test_cleared_fault_moves_service_into_recovering():
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

    # Step 1: The database experiences the fault.
    faulted_snapshot = advance_snapshot(
        topology,
        initial,
        (fault,),
    )

    assert faulted_snapshot.services[0].state == ServiceState.DOWN

    # Step 2: The fault is cleared.
    recovering_snapshot = advance_snapshot(
        topology,
        faulted_snapshot,
        (fault,),
    )

    assert recovering_snapshot.services[0].state == ServiceState.RECOVERING
