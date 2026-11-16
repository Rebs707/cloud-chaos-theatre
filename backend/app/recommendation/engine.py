
import networkx as nx

from app.diagnosis.models import IncidentDiagnosis
from app.models.enums import ServiceState
from app.models.simulation import SimulationSnapshot
from app.models.topology import Topology
from app.recommendation.models import (
    RecoveryPlan,
    RecoveryRecommendation,
)
from app.simulation.graph import build_dependency_graph


def _recovery_action(
    state: ServiceState,
    service_name: str,
) -> tuple[str, str]:
    """Return a deterministic recovery action and its rationale."""

    if state == ServiceState.DOWN:
        return (
            f"Restore {service_name} and verify that its health checks pass.",
            "The service is down and requires restoration.",
        )

    if state == ServiceState.DEGRADED:
        return (
            f"Investigate and resolve the condition degrading {service_name}.",
            "The service is operating in a degraded state.",
        )

    if state == ServiceState.RECOVERING:
        return (
            f"Monitor {service_name} until it returns to a healthy state.",
            "The service is recovering; verify recovery before taking further action.",
        )

    return (
        f"Verify the health of {service_name}.",
        "The service requires a final health verification.",
    )


def generate_recovery_plan(
    topology: Topology,
    diagnosis: IncidentDiagnosis,
    final_snapshot: SimulationSnapshot,
) -> RecoveryPlan:
    """Generate a deterministic recovery plan from simulation evidence."""

    service_names = {
        service.id: service.name
        for service in topology.services
    }

    final_states = {
        service.service_id: service.state
        for service in final_snapshot.services
    }

    if set(final_states) != set(service_names):
        raise ValueError(
            "Final snapshot services must match the topology services"
        )

    graph = build_dependency_graph(topology)

    root_cause_ids = {
        cause.service_id
        for cause in diagnosis.root_causes
    }

    affected_roots = {}

    for affected in diagnosis.affected_services:
        affected_roots.setdefault(affected.service_id, set()).add(
            affected.root_cause_service_id
        )

    candidates = []

    for service_id, state in final_states.items():
        if state == ServiceState.HEALTHY:
            continue

        if service_id in root_cause_ids:
            candidates.append(
                ((0, 0, service_id), service_id, state)
            )
            continue

        contributing_roots = affected_roots.get(service_id, set())

        if not contributing_roots:
            continue

        distances = []

        for root_id in contributing_roots:
            if root_id not in service_names:
                continue

            if nx.has_path(graph, service_id, root_id):
                distances.append(
                    nx.shortest_path_length(
                        graph,
                        source=service_id,
                        target=root_id,
                    )
                )

        if not distances:
            continue

        dependency_distance = min(distances)

        candidates.append(
            (
                (1, dependency_distance, service_id),
                service_id,
                state,
            )
        )

    candidates.sort(key=lambda item: item[0])

    recommendations = []

    for priority, (_, service_id, state) in enumerate(
        candidates,
        start=1,
    ):
        service_name = service_names[service_id]
        action, reason = _recovery_action(state, service_name)

        recommendations.append(
            RecoveryRecommendation(
                service_id=service_id,
                service_name=service_name,
                priority=priority,
                action=action,
                reason=reason,
                current_state=state,
            )
        )

    if recommendations:
        summary = (
            f"Generated {len(recommendations)} recovery recommendation(s), "
            "prioritised by root cause and dependency order."
        )
    else:
        summary = (
            "No recovery actions are required. "
            "No diagnosed service remains non-healthy."
        )

    return RecoveryPlan(
        summary=summary,
        recommendations=tuple(recommendations),
    )
