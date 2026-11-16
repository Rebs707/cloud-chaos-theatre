
from pydantic import BaseModel, ConfigDict, Field


class IncidentCommentary(BaseModel):
    """Structured incident briefing for the incident commander."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    key_findings: tuple[str, ...]
    immediate_actions: tuple[str, ...]
    recovery_status: str = Field(min_length=1)
    source: str = Field(min_length=1)
