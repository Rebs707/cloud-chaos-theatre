
from app.commentary.models import IncidentCommentary
from app.diagnosis.models import IncidentDiagnosis
from app.models.enums import ServiceState
from app.recommendation.models import RecoveryPlan


def generate_fallback_commentary(
    diagnosis: IncidentDiagnosis,
    recovery_plan: RecoveryPlan,
) -> IncidentCommentary:
    """Generate factual incident commentary without an AI provider."""

    root_cause_names = [
        cause.service_name
        for cause in diagnosis.root_causes
    ]

    affected_names = sorted({
        service.service_name
        for service in diagnosis.affected_services
    })

    recommendations = recovery_plan.recommendations

    if root_cause_names:
        headline = (
            f"Incident detected: {', '.join(root_cause_names)}"
        )
        key_findings = tuple(
            cause.explanation
            for cause in diagnosis.root_causes
        )
    else:
        headline = "Incident analysis: no explicit root cause identified"
        key_findings = (
            "No explicit fault injection was recorded.",
            "An active-fault root cause could not be established.",
        )

    if affected_names:
        key_findings += (
            f"Affected services: {', '.join(affected_names)}.",
        )

    immediate_actions = tuple(
        recommendation.action
        for recommendation in recommendations
    )

    if not recommendations:
        recovery_status = (
            "No diagnosed non-healthy services require recovery actions."
        )
    else:
        state_counts = {
            state: sum(
                recommendation.current_state == state
                for recommendation in recommendations
            )
            for state in ServiceState
        }

        recovery_status = (
            f"{len(recommendations)} recovery action(s) recommended. "
            f"{state_counts[ServiceState.DOWN]} down, "
            f"{state_counts[ServiceState.DEGRADED]} degraded, "
            f"{state_counts[ServiceState.RECOVERING]} recovering."
        )

    summary = (
        f"{diagnosis.summary} "
        f"{recovery_plan.summary}"
    )

    return IncidentCommentary(
        headline=headline,
        summary=summary,
        key_findings=key_findings,
        immediate_actions=immediate_actions,
        recovery_status=recovery_status,
        source="deterministic_fallback",
    )
