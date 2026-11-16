
import pytest

from app.models.enums import ServiceState
from app.simulation.propagation import induced_state


@pytest.mark.parametrize(
    "dependency_state, criticality, expected",
    [
        (ServiceState.HEALTHY, "hard", None),
        (ServiceState.HEALTHY, "soft", None),
        (ServiceState.DEGRADED, "hard", ServiceState.DEGRADED),
        (ServiceState.DEGRADED, "soft", None),
        (ServiceState.DOWN, "hard", ServiceState.DOWN),
        (ServiceState.DOWN, "soft", ServiceState.DEGRADED),
        (ServiceState.RECOVERING, "hard", ServiceState.DEGRADED),
        (ServiceState.RECOVERING, "soft", None),
    ],
)
def test_induced_state(dependency_state, criticality, expected):
    assert induced_state(dependency_state, criticality) == expected


def test_invalid_criticality_is_rejected():
    with pytest.raises(ValueError):
        induced_state(ServiceState.DOWN, "medium")
