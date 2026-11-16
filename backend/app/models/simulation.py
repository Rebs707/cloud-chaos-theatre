
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ServiceState, EvidenceKind


class SimulationConfig(BaseModel):
    """Configuration controlling a deterministic simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recovery_duration: int = Field(default=1, ge=1)
    max_steps: int = Field(default=100, ge=1, le=100)
    seed: int = 0


class Fault(BaseModel):
    """A scheduled fault affecting one service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    service_id: str
    start_step: int = Field(ge=0)
    clear_step: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_clear_step(self):
        if self.clear_step is not None and self.clear_step <= self.start_step:
            raise ValueError("clear_step must be later than start_step")
        return self


class ServiceSnapshot(BaseModel):
    """State and recovery progress for one service at a simulation step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    service_id: str
    state: ServiceState
    recovery_counter: int = Field(default=0, ge=0)


class SimulationSnapshot(BaseModel):
    """Immutable collection of service states at one simulation step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step: int = Field(ge=0)
    services: tuple[ServiceSnapshot, ...]

    @model_validator(mode="after")
    def validate_unique_services(self):
        service_ids = [service.service_id for service in self.services]

        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Snapshot contains duplicate service IDs")

        return self


class SimulationEvent(BaseModel):
    """Evidence recorded during a simulation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step: int = Field(ge=0)
    kind: EvidenceKind
    service_id: str
    description: str = Field(min_length=1)
