
from app.models.enums import ServiceState


def induced_state(
    dependency_state: ServiceState,
    criticality: str,
) -> ServiceState | None:
    """Determine the state induced by one dependency.

    Returns None when the dependency imposes no constraint.
    """
    if criticality not in {"hard", "soft"}:
        raise ValueError(f"Invalid dependency criticality: {criticality}")

    if dependency_state == ServiceState.HEALTHY:
        return None

    if criticality == "soft":
        if dependency_state == ServiceState.DOWN:
            return ServiceState.DEGRADED
        return None

    # Hard dependency
    if dependency_state == ServiceState.DOWN:
        return ServiceState.DOWN

    if dependency_state in {
        ServiceState.DEGRADED,
        ServiceState.RECOVERING,
    }:
        return ServiceState.DEGRADED

    return None
