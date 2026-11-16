
from app.diagnosis.models import (
    AffectedService,
    EvidenceReference,
    IncidentDiagnosis,
    RootCause,
)
from app.models.enums import CauseKind, ServiceState
from app.models.simulation import (
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.recommendation.engine import generate_recovery_plan


def make_snapshot(states):
    return SimulationSnapshot(
        step=5,
        services=tuple(
            ServiceSnapshot(
                service_id=service_id,
                state=state,
                recovery_counter=0,
            )
            for service_id, state in states.items()
        ),
    )


def make_diagnosis():
    evidence = EvidenceReference(
        step=1,
        service_id="database",
        description="Fault injected into Database",
    )

    return IncidentDiagnosis(
        summary="Database fault affected API and Worker.",
        root_causes=(
            RootCause(
                service_id="database",
                service_name="Database",
                cause_kind=CauseKind.ACTIVE_FAULT,
                explanation="An explicit fault was injected into Database.",
                evidence=(evidence,),
            ),
        ),
        affected_services=(
            AffectedService(
                service_id="api",
                service_name="API",
                current_state="down",
                root_cause_service_id="database",
                dependency_path=("api", "database"),
            ),
            AffectedService(
                service_id="worker",
                service_name="Worker",
                current_state="degraded",
                root_cause_service_id="database",
                dependency_path=("worker", "api", "database"),
            ),
        ),
        evidence=(evidence,),
        termination_reason="fixed_point",
    )


def make_topology():
    return load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
            {"id": "worker", "name": "Worker"},
            {"id": "cache", "name": "Cache"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            },
            {
                "dependent": "worker",
                "dependency": "api",
                "criticality": "hard",
            },
        ],
    })


def test_recovery_plan_prioritises_root_cause_before_dependents():
    topology = make_topology()
    diagnosis = make_diagnosis()

    snapshot = make_snapshot({
        "database": ServiceState.DOWN,
        "api": ServiceState.DOWN,
        "worker": ServiceState.DEGRADED,
        "cache": ServiceState.HEALTHY,
    })

    plan = generate_recovery_plan(topology, diagnosis, snapshot)

    assert [
        recommendation.service_id
        for recommendation in plan.recommendations
    ] == ["database", "api", "worker"]

    assert [
        recommendation.priority
        for recommendation in plan.recommendations
    ] == [1, 2, 3]


def test_recovery_plan_excludes_healthy_services():
    topology = make_topology()
    diagnosis = make_diagnosis()

    snapshot = make_snapshot({
        "database": ServiceState.DOWN,
        "api": ServiceState.DOWN,
        "worker": ServiceState.DEGRADED,
        "cache": ServiceState.HEALTHY,
    })

    plan = generate_recovery_plan(topology, diagnosis, snapshot)

    recommended_ids = {
        recommendation.service_id
        for recommendation in plan.recommendations
    }

    assert "cache" not in recommended_ids
    assert "database" in recommended_ids


def test_recovering_service_receives_monitoring_recommendation():
    topology = make_topology()
    diagnosis = make_diagnosis()

    snapshot = make_snapshot({
        "database": ServiceState.HEALTHY,
        "api": ServiceState.RECOVERING,
        "worker": ServiceState.HEALTHY,
        "cache": ServiceState.HEALTHY,
    })

    plan = generate_recovery_plan(topology, diagnosis, snapshot)

    assert len(plan.recommendations) == 1

    recommendation = plan.recommendations[0]

    assert recommendation.service_id == "api"
    assert recommendation.current_state == ServiceState.RECOVERING
    assert "Monitor" in recommendation.action


def make_overlapping_topology():
    return load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "cache", "name": "Cache"},
            {"id": "api", "name": "API"},
            {"id": "worker", "name": "Worker"},
            {"id": "batch", "name": "Batch"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            },
            {
                "dependent": "worker",
                "dependency": "api",
                "criticality": "hard",
            },
            {
                "dependent": "worker",
                "dependency": "cache",
                "criticality": "hard",
            },
            {
                "dependent": "batch",
                "dependency": "worker",
                "criticality": "hard",
            },
        ],
    })


def make_overlapping_diagnosis():
    database_evidence = EvidenceReference(
        step=1,
        service_id="database",
        description="Fault injected into Database",
    )
    cache_evidence = EvidenceReference(
        step=1,
        service_id="cache",
        description="Fault injected into Cache",
    )

    return IncidentDiagnosis(
        summary="Database and Cache faults affected dependent services.",
        root_causes=(
            RootCause(
                service_id="database",
                service_name="Database",
                cause_kind=CauseKind.ACTIVE_FAULT,
                explanation="A fault was injected into Database.",
                evidence=(database_evidence,),
            ),
            RootCause(
                service_id="cache",
                service_name="Cache",
                cause_kind=CauseKind.ACTIVE_FAULT,
                explanation="A fault was injected into Cache.",
                evidence=(cache_evidence,),
            ),
        ),
        affected_services=(
            AffectedService(
                service_id="api",
                service_name="API",
                current_state="down",
                root_cause_service_id="database",
                dependency_path=("api", "database"),
            ),
            AffectedService(
                service_id="worker",
                service_name="Worker",
                current_state="down",
                root_cause_service_id="database",
                dependency_path=("worker", "api", "database"),
            ),
            AffectedService(
                service_id="worker",
                service_name="Worker",
                current_state="down",
                root_cause_service_id="cache",
                dependency_path=("worker", "cache"),
            ),
            AffectedService(
                service_id="batch",
                service_name="Batch",
                current_state="degraded",
                root_cause_service_id="database",
                dependency_path=("batch", "worker", "api", "database"),
            ),
        ),
        evidence=(database_evidence, cache_evidence),
        termination_reason="fixed_point",
    )


def test_overlapping_root_causes_use_shortest_dependency_distance():
    topology = make_overlapping_topology()
    diagnosis = make_overlapping_diagnosis()

    snapshot = make_snapshot({
        "database": ServiceState.DOWN,
        "cache": ServiceState.DOWN,
        "api": ServiceState.DOWN,
        "worker": ServiceState.DOWN,
        "batch": ServiceState.DEGRADED,
    })

    plan = generate_recovery_plan(topology, diagnosis, snapshot)

    recommended_ids = [
        recommendation.service_id
        for recommendation in plan.recommendations
    ]

    assert recommended_ids == [
        "cache",
        "database",
        "api",
        "worker",
        "batch",
    ]


def test_recovery_order_is_deterministic():
    topology = make_overlapping_topology()
    diagnosis = make_overlapping_diagnosis()

    snapshot = make_snapshot({
        "database": ServiceState.DOWN,
        "cache": ServiceState.DOWN,
        "api": ServiceState.DOWN,
        "worker": ServiceState.DOWN,
        "batch": ServiceState.DEGRADED,
    })

    first_plan = generate_recovery_plan(topology, diagnosis, snapshot)
    second_plan = generate_recovery_plan(topology, diagnosis, snapshot)

    first_order = [
        item.service_id for item in first_plan.recommendations
    ]
    second_order = [
        item.service_id for item in second_plan.recommendations
    ]

    assert first_order == second_order

