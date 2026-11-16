
from app.commentary.engine import generate_fallback_commentary
from app.commentary.models import IncidentCommentary
from app.diagnosis.analyzer import diagnose_incident
from app.diagnosis.models import IncidentDiagnosis
from app.models.topology import Topology
from app.recommendation.engine import generate_recovery_plan
from app.recommendation.models import RecoveryPlan
from app.simulation.runner import SimulationResult


def run_incident_commander(
    topology: Topology,
    simulation_result: SimulationResult,
) -> tuple[IncidentDiagnosis, RecoveryPlan, IncidentCommentary]:
    """Orchestrate diagnosis, recovery planning, and incident commentary."""

    diagnosis = diagnose_incident(
        topology=topology,
        result=simulation_result,
    )

    recovery_plan = generate_recovery_plan(
        topology=topology,
        diagnosis=diagnosis,
        final_snapshot=simulation_result.final_snapshot,
    )

    commentary = generate_fallback_commentary(
        diagnosis=diagnosis,
        recovery_plan=recovery_plan,
    )

    return diagnosis, recovery_plan, commentary
