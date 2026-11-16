from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CauseKind


class EvidenceReference(BaseModel):
    """A reference to a recorded simulation event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step: int = Field(ge=0)
    service_id: str
    description: str = Field(min_length=1)


class RootCause(BaseModel):
    """An evidence-backed explanation of an identified incident cause."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    service_id: str
    service_name: str
    cause_kind: CauseKind
    explanation: str = Field(min_length=1)
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)


class AffectedService(BaseModel):
    """A service affected by an identified root cause."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    service_id: str
    service_name: str
    current_state: str
    root_cause_service_id: str
    dependency_path: tuple[str, ...] = Field(min_length=1)


class IncidentDiagnosis(BaseModel):
    """Structured diagnosis produced from simulation evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1)
    root_causes: tuple[RootCause, ...]
    affected_services: tuple[AffectedService, ...]
    evidence: tuple[EvidenceReference, ...]
    termination_reason: str