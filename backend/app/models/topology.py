
import re
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class TopologyValidationError(ValueError):
    """Raised when a topology contains invalid services or dependencies."""


class Service(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str = Field(min_length=1)


    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", value):
            raise ValueError(
                "Service ID must start with a lowercase letter "
                "and contain only lowercase letters, numbers, or hyphens"
            )
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Service name cannot be blank")
        return value


class DependencyEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dependent: str
    dependency: str
    criticality: str

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, value: str) -> str:
        if value not in {"hard", "soft"}:
            raise ValueError("Criticality must be 'hard' or 'soft'")
        return value


class Topology(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    services: tuple[Service, ...]
    edges: tuple[DependencyEdge, ...]

    @model_validator(mode="after")
    def validate_topology(self):
        service_ids = [service.id for service in self.services]

        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Topology contains a duplicate service ID")

        known_ids = set(service_ids)
        seen_edges = set()

        for edge in self.edges:
            edge_name = f"{edge.dependent} -> {edge.dependency}"

            if edge.dependent == edge.dependency:
                raise ValueError(f"Self-loop is not allowed: {edge_name}")

            if edge.dependent not in known_ids or edge.dependency not in known_ids:
                raise ValueError(f"Unknown service in edge: {edge_name}")

            edge_key = (edge.dependent, edge.dependency)

            if edge_key in seen_edges:
                raise ValueError(f"Duplicate edge: {edge_name}")

            seen_edges.add(edge_key)

        return self


def load_topology(data: Mapping[str, Any]) -> Topology:
    """Validate and load topology data.

    Cycles are intentionally allowed. Simulation logic is responsible
    for evaluating cyclic dependencies safely.
    """
    try:
        services = tuple(
            Service.model_validate(item)
            for item in data.get("services", [])
        )
    except ValidationError as exc:
        raise TopologyValidationError(
            f"Invalid service definition: {exc}"
        ) from exc

    service_ids = {service.id for service in services}

    if len(service_ids) != len(services):
        raise TopologyValidationError("Topology contains a duplicate service ID")

    edges = []

    for item in data.get("edges", []):
        dependent = item.get("dependent", "<missing>")
        dependency = item.get("dependency", "<missing>")
        edge_name = f"{dependent} -> {dependency}"

        try:
            edge = DependencyEdge.model_validate(item)
        except (ValidationError, AttributeError) as exc:
            raise TopologyValidationError(
                f"Invalid edge {edge_name}: {exc}"
            ) from exc

        if edge.dependent == edge.dependency:
            raise TopologyValidationError(
                f"Self-loop is not allowed: {edge_name}"
            )

        if edge.dependent not in service_ids or edge.dependency not in service_ids:
            raise TopologyValidationError(
                f"Unknown service in edge: {edge_name}"
            )

        if any(
            existing.dependent == edge.dependent
            and existing.dependency == edge.dependency
            for existing in edges
        ):
            raise TopologyValidationError(f"Duplicate edge: {edge_name}")

        edges.append(edge)

    try:
        return Topology(services=services, edges=tuple(edges))
    except ValidationError as exc:
        raise TopologyValidationError(str(exc)) from exc
