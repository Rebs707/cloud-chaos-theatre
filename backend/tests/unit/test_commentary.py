
from app.commentary.engine import generate_fallback_commentary
from app.diagnosis.models import (
    AffectedService,
    EvidenceReference,
    IncidentDiagnosis,
    RootCause,
)
from app.models.enums import CauseKind, ServiceState
from app.recommendation.models import (
    RecoveryPlan,
    RecoveryRecommendation,
)


def make_diagnosis():
    evidence = EvidenceReference(
        step=1,
        service_id="database",
        description="Fault injected into Database",
    )

    return IncidentDiagnosis(
        summary="Database failure affected API.",
        root_causes=(
            RootCause(
                service_id="database",
                service_name="Database",
                cause_kind=CauseKind.ACTIVE_FAULT,
                explanation="A fault was injected into Database at step 1.",
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
        ),
        evidence=(evidence,),
        termination_reason="fixed_point",
    )


def make_recovery_plan():
    return RecoveryPlan(
        summary="Generated 2 recovery recommendations.",
        recommendations=(
            RecoveryRecommendation(
                service_id="database",
                service_name="Database",
                priority=1,
                action="Restore Database and verify its health checks.",
                reason="The service is down and requires restoration.",
                current_state=ServiceState.DOWN,
            ),
            RecoveryRecommendation(
                service_id="api",
                service_name="API",
                priority=2,
                action="Investigate and resolve the condition degrading API.",
                reason="The service is operating in a degraded state.",
                current_state=ServiceState.DEGRADED,
            ),
        ),
    )


def test_fallback_commentary_identifies_root_cause():
    commentary = generate_fallback_commentary(
        make_diagnosis(),
        make_recovery_plan(),
    )

    assert "Database" in commentary.headline
    assert commentary.source == "deterministic_fallback"


def test_fallback_commentary_includes_affected_services():
    commentary = generate_fallback_commentary(
        make_diagnosis(),
        make_recovery_plan(),
    )

    assert any(
        "API" in finding
        for finding in commentary.key_findings
    )


def test_fallback_commentary_uses_recovery_plan_actions():
    recovery_plan = make_recovery_plan()

    commentary = generate_fallback_commentary(
        make_diagnosis(),
        recovery_plan,
    )

    assert commentary.immediate_actions == tuple(
        item.action
        for item in recovery_plan.recommendations
    )

    assert "2 recovery action(s) recommended" in commentary.recovery_status
    assert "1 down" in commentary.recovery_status
    assert "1 degraded" in commentary.recovery_status


def test_fallback_commentary_handles_no_explicit_root_cause():
    diagnosis = IncidentDiagnosis(
        summary="No explicit fault was recorded.",
        root_causes=(),
        affected_services=(),
        evidence=(),
        termination_reason="fixed_point",
    )

    recovery_plan = RecoveryPlan(
        summary="No recovery actions are required.",
        recommendations=(),
    )

    commentary = generate_fallback_commentary(
        diagnosis,
        recovery_plan,
    )

    assert "no explicit root cause identified" in commentary.headline
    assert any(
        "No explicit fault injection" in finding
        for finding in commentary.key_findings
    )
    assert commentary.immediate_actions == ()
    assert "No diagnosed non-healthy services" in commentary.recovery_status
