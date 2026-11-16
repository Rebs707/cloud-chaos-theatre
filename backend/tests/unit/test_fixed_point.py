
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.simulation.engine import has_reached_fixed_point


def make_snapshot(
    step: int,
    state: ServiceState = ServiceState.HEALTHY,
    recovery_counter: int = 0,
) -> SimulationSnapshot:
    return SimulationSnapshot(
        step=step,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=state,
                recovery_counter=recovery_counter,
            ),
        ),
    )


def test_stable_snapshots_without_pending_faults_reach_fixed_point():
    previous = make_snapshot(1)
    current = make_snapshot(2)

    assert has_reached_fixed_point(
        previous,
        current,
        faults=(),
    )


def test_changing_service_state_is_not_a_fixed_point():
    previous = make_snapshot(1, ServiceState.DOWN)
    current = make_snapshot(2, ServiceState.RECOVERING, 1)

    assert not has_reached_fixed_point(
        previous,
        current,
        faults=(),
    )


def test_changing_recovery_counter_is_not_a_fixed_point():
    previous = make_snapshot(
        1,
        ServiceState.RECOVERING,
        recovery_counter=1,
    )
    current = make_snapshot(
        2,
        ServiceState.RECOVERING,
        recovery_counter=2,
    )

    assert not has_reached_fixed_point(
        previous,
        current,
        faults=(),
    )


def test_future_fault_prevents_fixed_point():
    previous = make_snapshot(1)
    current = make_snapshot(2)

    future_fault = Fault(
        service_id="database",
        start_step=5,
    )

    assert not has_reached_fixed_point(
        previous,
        current,
        faults=(future_fault,),
    )
