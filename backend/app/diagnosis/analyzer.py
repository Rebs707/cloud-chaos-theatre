from collections import defaultdict

import networkx as nx

from app.diagnosis.models import (
    AffectedService,
    EvidenceReference,
    IncidentDiagnosis,
    RootCause,
)
from app.models.enums import CauseKind, EvidenceKind, ServiceState
from app.models.topology import Topology
from app.simulation.graph import build_dependency_graph
from app.simulation.runner import SimulationResult


def _to_evidence_reference(event) -> EvidenceReference:
    """Convert a simulation event into a diagnosis evidence reference."""
    return EvidenceReference(
        step=event.step,
        service_id=event.service_id,
        description=event.description,
    )


def diagnose_incident(
    topology: Topology,
    result: SimulationResult,
) -> IncidentDiagnosis:
    """Produce a deterministic, evidence-backed incident diagnosis."""

    if not result.snapshots:
        raise ValueError("Simulation result must contain at least one snapshot")

    service_names = {
        service.id: service.name
        for service in topology.services
    }

    graph = build_dependency_graph(topology)

    fault_events_by_service = defaultdict(list)

    for event in sorted(
        result.events,
        key=lambda item: (item.step, item.service_id, item.kind.value),
    ):
        if event.kind == EvidenceKind.FAULT_INJECTED:
            if event.service_id not in service_names:
                continue

            fault_events_by_service[event.service_id].append(event)

    final_states = {
        service.service_id: service.state
        for service in result.final_snapshot.services
    }

    root_causes = []
    affected_services = []

    for root_service_id in sorted(fault_events_by_service):
        fault_events = fault_events_by_service[root_service_id]
        first_fault_step = min(event.step for event in fault_events)

        root_service_name = service_names[root_service_id]

        root_causes.append(
            RootCause(
                service_id=root_service_id,
                service_name=root_service_name,
                cause_kind=CauseKind.ACTIVE_FAULT,
                explanation=(
                    f"An explicit fault was injected into "
                    f"{root_service_name} at step "
                    f"{first_fault_step}."
                ),
                evidence=tuple(
                    _to_evidence_reference(event)
                    for event in fault_events
                ),
            )
        )

        for affected_service_id in sorted(service_names):
            if affected_service_id == root_service_id:
                continue

            if not nx.has_path(
                graph,
                source=affected_service_id,
                target=root_service_id,
            ):
                continue

            was_nonhealthy_after_fault = any(
                snapshot.step >= first_fault_step
                and any(
                    service.service_id == affected_service_id
                    and service.state != ServiceState.HEALTHY
                    for service in snapshot.services
                )
                for snapshot in result.snapshots
            )

            if not was_nonhealthy_after_fault:
                continue

            dependency_path = tuple(
                nx.shortest_path(
                    graph,
                    source=affected_service_id,
                    target=root_service_id,
                )
            )

            affected_services.append(
                AffectedService(
                    service_id=affected_service_id,
                    service_name=service_names[affected_service_id],
                    current_state=final_states[
                        affected_service_id
                    ].value,
                    root_cause_service_id=root_service_id,
                    dependency_path=dependency_path,
                )
            )

    all_evidence = tuple(
        _to_evidence_reference(event)
        for event in sorted(
            result.events,
            key=lambda item: (
                item.step,
                item.service_id,
                item.kind.value,
            ),
        )
    )

    if root_causes:
        summary = (
            f"Identified {len(root_causes)} service fault(s) "
            f"and {len(affected_services)} affected service relationship(s)."
        )
    else:
        summary = (
            "No explicit fault injection was recorded. "
            "No active-fault root cause could be established."
        )

    return IncidentDiagnosis(
        summary=summary,
        root_causes=tuple(root_causes),
        affected_services=tuple(affected_services),
        evidence=all_evidence,
        termination_reason=result.termination_reason,
    )