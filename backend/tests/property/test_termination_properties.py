
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationConfig,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.runner import run_simulation


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
    max_steps=st.integers(min_value=1, max_value=10),
    clear_step=st.integers(min_value=12, max_value=20),
)
def test_simulation_never_exceeds_configured_step_limit(
    max_steps,
    clear_step,
):
    topology = make_topology()

    fault = Fault(
        service_id="database",
        start_step=1,
        clear_step=clear_step,
    )

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(),
        faults=(fault,),
        config=SimulationConfig(max_steps=max_steps),
    )

    assert result.final_snapshot.step <= max_steps

    if result.final_snapshot.step == max_steps:
        assert result.termination_reason == "max_steps_reached"


@settings(max_examples=50, deadline=None)
@given(
    fault_start=st.integers(min_value=1, max_value=5),
    fault_duration=st.integers(min_value=1, max_value=5),
)
def test_independent_service_eventually_reaches_fixed_point(
    fault_start,
    fault_duration,
):
    topology = make_topology()

    fault = Fault(
        service_id="database",
        start_step=fault_start,
        clear_step=fault_start + fault_duration,
    )

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(),
        faults=(fault,),
        config=SimulationConfig(max_steps=30),
    )

    assert result.termination_reason == "fixed_point"

    assert (
        result.final_snapshot.services[0].state
        == ServiceState.HEALTHY
    )

    assert result.final_snapshot.step <= 30
