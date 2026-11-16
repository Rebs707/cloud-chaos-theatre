
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ServiceState


class RecoveryRecommendation(BaseModel):
    """A deterministic recovery action for an affected service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    service_id: str
    service_name: str
    priority: int = Field(ge=1)
    action: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    current_state: ServiceState


class RecoveryPlan(BaseModel):
    """Ordered recovery recommendations for an incident."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1)
    recommendations: tuple[RecoveryRecommendation, ...]
