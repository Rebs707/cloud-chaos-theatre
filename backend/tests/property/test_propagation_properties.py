
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import ServiceState
from app.simulation.propagation import induced_state


@settings(max_examples=100, deadline=None)
@given(
    dependency_state=st.sampled_from(list(ServiceState)),
    criticality=st.sampled_from(["hard", "soft"]),
)
def test_induced_state_matches_dependency_rules(
    dependency_state,
    criticality,
):
    expected_states = {
        (ServiceState.HEALTHY, "hard"): None,
        (ServiceState.HEALTHY, "soft"): None,
        (ServiceState.DEGRADED, "hard"): ServiceState.DEGRADED,
        (ServiceState.DEGRADED, "soft"): None,
        (ServiceState.DOWN, "hard"): ServiceState.DOWN,
        (ServiceState.DOWN, "soft"): ServiceState.DEGRADED,
        (ServiceState.RECOVERING, "hard"): ServiceState.DEGRADED,
        (ServiceState.RECOVERING, "soft"): None,
    }

    expected = expected_states[
        (dependency_state, criticality)
    ]

    actual = induced_state(
        dependency_state,
        criticality,
    )

    assert actual == expected


@settings(max_examples=50, deadline=None)
@given(
    criticality=st.sampled_from(["hard", "soft"]),
)
def test_healthy_dependency_never_induces_failure(criticality):
    assert (
        induced_state(ServiceState.HEALTHY, criticality)
        is None
    )


@settings(max_examples=50, deadline=None)
@given(
    criticality=st.sampled_from(["hard", "soft"]),
)
def test_soft_dependency_never_propagates_down_state(criticality):
    if criticality == "soft":
        assert (
            induced_state(ServiceState.DOWN, criticality)
            == ServiceState.DEGRADED
        )
