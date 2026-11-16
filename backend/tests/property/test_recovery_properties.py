
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


def make_topology():
    return load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })


def make_initial_snapshot():
    return SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
        ),
    )


@settings(max_examples=50, deadline=None)
@given(
    recovery_duration=st.integers(min_value=1, max_value=8),
)
def test_service_recovers_only_after_configured_duration(
    recovery_duration,
):
    topology = make_topology()
    current = make_initial_snapshot()

    fault = Fault(
        service_id="database",
        start_step=1,
        clear_step=2,
    )

    faults = (fault,)

    # Step 1: The active fault takes the database DOWN.
    current = advance_snapshot(
        topology,
        current,
        faults,
        recovery_duration=recovery_duration,
    )

    assert current.services[0].state == ServiceState.DOWN
    assert current.services[0].recovery_counter == 0

    # Step 2: The fault clears and recovery begins.
    current = advance_snapshot(
        topology,
        current,
        faults,
        recovery_duration=recovery_duration,
    )

    assert current.services[0].state == ServiceState.RECOVERING
    assert current.services[0].recovery_counter == 1

    # Counters below the configured duration must remain RECOVERING.
    for expected_counter in range(2, recovery_duration):
        current = advance_snapshot(
            topology,
            current,
            faults,
            recovery_duration=recovery_duration,
        )

        assert current.services[0].state == ServiceState.RECOVERING
        assert current.services[0].recovery_counter == expected_counter

    # Reaching the configured duration completes recovery.
    recovered = advance_snapshot(
        topology,
        current,
        faults,
        recovery_duration=recovery_duration,
    )

    assert recovered.services[0].state == ServiceState.HEALTHY
    assert recovered.services[0].recovery_counter == 0

