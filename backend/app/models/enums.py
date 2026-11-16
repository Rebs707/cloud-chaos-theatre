
from enum import Enum


class ServiceState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RECOVERING = "recovering"


class CauseKind(str, Enum):
    ACTIVE_FAULT = "active_fault"
    DEPENDENCY_FAILURE = "dependency_failure"


class EvidenceKind(str, Enum):
    SERVICE_STATE_CHANGE = "service_state_change"
    FAULT_INJECTED = "fault_injected"
    FAULT_CLEARED = "fault_cleared"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"

