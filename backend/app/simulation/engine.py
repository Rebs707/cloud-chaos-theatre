
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import Topology
from app.simulation.graph import build_dependency_graph
from app.simulation.propagation import induced_state


_STATE_SEVERITY = {
    ServiceState.HEALTHY: 0,
    ServiceState.DEGRADED: 1,
    ServiceState.DOWN: 2,
}


def _worse_state(
    first: ServiceState,
    second: ServiceState,
) -> ServiceState:
    """Return the more severe of two operational states."""
    return (
        first
        if _STATE_SEVERITY[first] >= _STATE_SEVERITY[second]
        else second
    )


def advance_snapshot(
    topology: Topology,
    previous: SimulationSnapshot,
    faults: tuple[Fault, ...],
    recovery_duration: int = 1,
) -> SimulationSnapshot:
    """Calculate the next simulation snapshot deterministically.

    Every service is evaluated using the previous snapshot only.

    Fault start_step is inclusive.
    Fault clear_step is exclusive.

    A service must enter RECOVERING before it can become HEALTHY.
    """

    if recovery_duration < 1:
        raise ValueError("recovery_duration must be at least 1")

    next_step = previous.step + 1

    graph = build_dependency_graph(topology)

    previous_services = {
        service.service_id: service
        for service in previous.services
    }

    previous_states = {
        service_id: service.state
        for service_id, service in previous_services.items()
    }

    topology_ids = set(graph.nodes)

    if set(previous_states) != topology_ids:
        raise ValueError(
            "Snapshot services must exactly match topology services"
        )

    for fault in faults:
        if fault.service_id not in topology_ids:
            raise ValueError(
                f"Fault references unknown service: {fault.service_id}"
            )

    next_services = []

    for service_id in sorted(topology_ids):
        previous_service = previous_services[service_id]

        # Check whether a fault is active at the next simulation step.
        active_fault = any(
            fault.service_id == service_id
            and fault.start_step <= next_step
            and (
                fault.clear_step is None
                or next_step < fault.clear_step
            )
            for fault in faults
        )

        # An active fault keeps the service down.
        if active_fault:
            next_services.append(
                ServiceSnapshot(
                    service_id=service_id,
                    state=ServiceState.DOWN,
                    recovery_counter=0,
                )
            )
            continue

        # Evaluate dependency effects using the previous snapshot.
        dependency_impact = None
        all_dependencies_healthy = True

        for dependency_id in sorted(graph.successors(service_id)):
            dependency_state = previous_states[dependency_id]

            if dependency_state != ServiceState.HEALTHY:
                all_dependencies_healthy = False

            criticality = graph[service_id][dependency_id]["criticality"]

            impact = induced_state(
                dependency_state,
                criticality,
            )

            if impact is not None:
                if dependency_impact is None:
                    dependency_impact = impact
                else:
                    dependency_impact = _worse_state(
                        dependency_impact,
                        impact,
                    )

        # Dependency failures override recovery progress.
        if dependency_impact is not None:
            next_services.append(
                ServiceSnapshot(
                    service_id=service_id,
                    state=dependency_impact,
                    recovery_counter=0,
                )
            )
            continue

        # Continue recovery for a service already recovering.
        if previous_service.state == ServiceState.RECOVERING:
            recovery_counter = min(
                previous_service.recovery_counter + 1,
                recovery_duration,
            )

            if (
                all_dependencies_healthy
                and recovery_counter >= recovery_duration
            ):
                next_services.append(
                    ServiceSnapshot(
                        service_id=service_id,
                        state=ServiceState.HEALTHY,
                        recovery_counter=0,
                    )
                )
            else:
                next_services.append(
                    ServiceSnapshot(
                        service_id=service_id,
                        state=ServiceState.RECOVERING,
                        recovery_counter=recovery_counter,
                    )
                )

            continue

        # A previously degraded or down service starts recovery.
        if previous_service.state in {
            ServiceState.DOWN,
            ServiceState.DEGRADED,
        }:
            next_services.append(
                ServiceSnapshot(
                    service_id=service_id,
                    state=ServiceState.RECOVERING,
                    recovery_counter=1,
                )
            )
            continue

        # A nonhealthy soft dependency blocks healthy status,
        # but does not necessarily block recovery progress.
        if not all_dependencies_healthy:
            next_services.append(
                ServiceSnapshot(
                    service_id=service_id,
                    state=ServiceState.RECOVERING,
                    recovery_counter=0,
                )
            )
            continue

        # No active fault, no dependency impact, and no recovery required.
        next_services.append(
            ServiceSnapshot(
                service_id=service_id,
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            )
        )

    return SimulationSnapshot(
        step=next_step,
        services=tuple(next_services),
    )


def has_reached_fixed_point(
    previous: SimulationSnapshot,
    current: SimulationSnapshot,
    faults: tuple[Fault, ...],
) -> bool:
    """Check whether service states and recovery counters have stabilised.

    A future fault injection or scheduled fault clearing prevents
    fixed-point detection.
    """

    previous_services = {
        service.service_id: (
            service.state,
            service.recovery_counter,
        )
        for service in previous.services
    }

    current_services = {
        service.service_id: (
            service.state,
            service.recovery_counter,
        )
        for service in current.services
    }

    # States and recovery counters must both be unchanged.
    if previous_services != current_services:
        return False

    # Check for future fault injections or fault clearing events.
    for fault in faults:
        if fault.start_step > current.step:
            return False

        if (
            fault.clear_step is not None
            and fault.clear_step > current.step
        ):
            return False

    return True

  

        