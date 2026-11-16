
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def test_recovery_counter_resets_when_fault_reoccurs():
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

    faults = (
        Fault(service_id="database", start_step=1, clear_step=2),
        Fault(service_id="database", start_step=4, clear_step=5),
    )

    # Step 1: First fault takes the database down.
    step_one = advance_snapshot(
        topology, initial, faults, recovery_duration=3
    )
    assert step_one.services[0].state == ServiceState.DOWN

    # Step 2: First fault clears; recovery starts.
    step_two = advance_snapshot(
        topology, step_one, faults, recovery_duration=3
    )
    assert step_two.services[0].state == ServiceState.RECOVERING
    assert step_two.services[0].recovery_counter == 1

    # Step 3: Recovery continues.
    step_three = advance_snapshot(
        topology, step_two, faults, recovery_duration=3
    )
    assert step_three.services[0].state == ServiceState.RECOVERING
    assert step_three.services[0].recovery_counter == 2

    # Step 4: A second fault occurs during recovery.
    step_four = advance_snapshot(
        topology, step_three, faults, recovery_duration=3
    )
    assert step_four.services[0].state == ServiceState.DOWN
    assert step_four.services[0].recovery_counter == 0

    # Step 5: Second fault clears; recovery starts from zero.
    step_five = advance_snapshot(
        topology, step_four, faults, recovery_duration=3
    )
    assert step_five.services[0].state == ServiceState.RECOVERING
    assert step_five.services[0].recovery_counter == 1

    # Step 6: Recovery continues.
    step_six = advance_snapshot(
        topology, step_five, faults, recovery_duration=3
    )
    assert step_six.services[0].state == ServiceState.RECOVERING
    assert step_six.services[0].recovery_counter == 2

    # Step 7: Recovery duration is finally satisfied.
    step_seven = advance_snapshot(
        topology, step_six, faults, recovery_duration=3
    )
    assert step_seven.services[0].state == ServiceState.HEALTHY
    assert step_seven.services[0].recovery_counter == 0
