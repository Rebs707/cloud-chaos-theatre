
from dataclasses import dataclass

from app.models.enums import EvidenceKind, ServiceState
from app.models.simulation import (
    Fault,
    SimulationConfig,
    SimulationEvent,
    SimulationSnapshot,
)
from app.models.topology import Topology
from app.simulation.engine import (
    advance_snapshot,
    has_reached_fixed_point,
)


@dataclass(frozen=True)
class SimulationResult:
    """Complete result of a deterministic simulation run."""

    snapshots: tuple[SimulationSnapshot, ...]
    events: tuple[SimulationEvent, ...]
    termination_reason: str

    @property
    def final_snapshot(self) -> SimulationSnapshot:
        return self.snapshots[-1]


def _state_signature(snapshot: SimulationSnapshot) -> tuple:
    """Represent service states and recovery counters independently of step."""
    return tuple(
        (
            service.service_id,
            service.state,
            service.recovery_counter,
        )
        for service in sorted(
            snapshot.services,
            key=lambda item: item.service_id,
        )
    )


def _has_pending_fault_events(
    current_step: int,
    faults: tuple[Fault, ...],
) -> bool:
    """Check whether a future fault injection or clearing event remains."""
    return any(
        fault.start_step > current_step
        or (
            fault.clear_step is not None
            and fault.clear_step > current_step
        )
        for fault in faults
    )


def _record_events(
    previous: SimulationSnapshot,
    current: SimulationSnapshot,
    faults: tuple[Fault, ...],
) -> list[SimulationEvent]:
    """Record fault events and service state transitions."""
    events = []

    for fault in faults:
        if fault.start_step == current.step:
            events.append(
                SimulationEvent(
                    step=current.step,
                    kind=EvidenceKind.FAULT_INJECTED,
                    service_id=fault.service_id,
                    description=f"Fault injected into {fault.service_id}",
                )
            )

        if fault.clear_step == current.step:
            events.append(
                SimulationEvent(
                    step=current.step,
                    kind=EvidenceKind.FAULT_CLEARED,
                    service_id=fault.service_id,
                    description=f"Fault cleared from {fault.service_id}",
                )
            )

    previous_services = {
        service.service_id: service
        for service in previous.services
    }

    for service in current.services:
        old_state = previous_services[service.service_id].state
        new_state = service.state

        if old_state == new_state:
            continue

        events.append(
            SimulationEvent(
                step=current.step,
                kind=EvidenceKind.SERVICE_STATE_CHANGE,
                service_id=service.service_id,
                description=(
                    f"{service.service_id} changed "
                    f"from {old_state.value} to {new_state.value}"
                ),
            )
        )

        if new_state == ServiceState.RECOVERING:
            events.append(
                SimulationEvent(
                    step=current.step,
                    kind=EvidenceKind.RECOVERY_STARTED,
                    service_id=service.service_id,
                    description=f"Recovery started for {service.service_id}",
                )
            )

        elif (
            old_state == ServiceState.RECOVERING
            and new_state == ServiceState.HEALTHY
        ):
            events.append(
                SimulationEvent(
                    step=current.step,
                    kind=EvidenceKind.RECOVERY_COMPLETED,
                    service_id=service.service_id,
                    description=f"Recovery completed for {service.service_id}",
                )
            )

    return events


def run_simulation(
    topology: Topology,
    initial_snapshot: SimulationSnapshot,
    faults: tuple[Fault, ...] = (),
    config: SimulationConfig | None = None,
) -> SimulationResult:
    """Run until a fixed point, repeated state, or maximum step limit."""

    config = config or SimulationConfig()

    snapshots = [initial_snapshot]
    events = []

    # Only remember states after all scheduled fault events are processed.
    seen_states = {}

    current = initial_snapshot

    for _ in range(config.max_steps):
        next_snapshot = advance_snapshot(
            topology=topology,
            previous=current,
            faults=faults,
            recovery_duration=config.recovery_duration,
        )

        events.extend(
            _record_events(current, next_snapshot, faults)
        )

        snapshots.append(next_snapshot)

        if has_reached_fixed_point(
            current,
            next_snapshot,
            faults,
        ):
            return SimulationResult(
                snapshots=tuple(snapshots),
                events=tuple(events),
                termination_reason="fixed_point",
            )

        signature = _state_signature(next_snapshot)

        if not _has_pending_fault_events(
            next_snapshot.step,
            faults,
        ):
            if signature in seen_states:
                return SimulationResult(
                    snapshots=tuple(snapshots),
                    events=tuple(events),
                    termination_reason="cycle_detected",
                )

            seen_states[signature] = next_snapshot.step

        current = next_snapshot

    return SimulationResult(
        snapshots=tuple(snapshots),
        events=tuple(events),
        termination_reason="max_steps_reached",
    )

