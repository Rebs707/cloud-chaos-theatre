
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import ServiceState
from app.models.simulation import (
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.engine import advance_snapshot


@settings(max_examples=50, deadline=None)
@given(
    criticality=st.sampled_from(["hard", "soft"]),
    recovery_duration=st.integers(min_value=1, max_value=5),
)
def test_service_cannot_become_healthy_while_dependency_is_unhealthy(
    criticality,
    recovery_duration,
):
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": criticality,
            }
        ],
    })

    # The database has reached its recovery duration,
    # but is still RECOVERING in the previous snapshot.
    previous_snapshot = SimulationSnapshot(
        step=1,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=ServiceState.RECOVERING,
                recovery_counter=recovery_duration,
            ),
            ServiceSnapshot(
                service_id="api",
                state=ServiceState.RECOVERING,
                recovery_counter=recovery_duration,
            ),
        ),
    )

    next_snapshot = advance_snapshot(
        topology,
        previous_snapshot,
        faults=(),
        recovery_duration=recovery_duration,
    )

    states = {
        service.service_id: service.state
        for service in next_snapshot.services
    }

    # Database completes recovery.
    assert states["database"] == ServiceState.HEALTHY

    # API must not become healthy because its dependency
    # was RECOVERING in the previous snapshot.
    assert states["api"] != ServiceState.HEALTHY

