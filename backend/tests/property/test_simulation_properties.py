
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import EvidenceKind, ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationConfig,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.runner import run_simulation


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


def make_topology():
    return load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })


@settings(max_examples=50, deadline=None)
@given(
    start_step=st.integers(min_value=1, max_value=5),
    fault_duration=st.integers(min_value=1, max_value=4),
    recovery_duration=st.integers(min_value=1, max_value=3),
)
def test_simulation_is_deterministic_and_recovers(
    start_step,
    fault_duration,
    recovery_duration,
):
    topology = make_topology()

    fault = Fault(
        service_id="database",
        start_step=start_step,
        clear_step=start_step + fault_duration,
    )

    config = SimulationConfig(
        recovery_duration=recovery_duration,
        max_steps=30,
        seed=42,
    )

    first_result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(),
        faults=(fault,),
        config=config,
    )

    second_result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(),
        faults=(fault,),
        config=config,
    )

    # Identical inputs must produce identical simulation results.
    assert first_result == second_result

    # The simulation must terminate at a fixed point.
    assert first_result.termination_reason == "fixed_point"

    # The database must eventually return to HEALTHY.
    assert (
        first_result.final_snapshot.services[0].state
        == ServiceState.HEALTHY
    )

    # Both fault lifecycle events must be recorded.
    event_kinds = {
        event.kind for event in first_result.events
    }

    assert EvidenceKind.FAULT_INJECTED in event_kinds
    assert EvidenceKind.FAULT_CLEARED in event_kinds
