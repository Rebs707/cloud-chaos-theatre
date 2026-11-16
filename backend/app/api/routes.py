
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.commentary.commander import run_incident_commander
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationConfig,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.runner import run_simulation


router = APIRouter()


class IncidentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topology: dict
    initial_snapshot: SimulationSnapshot
    faults: tuple[Fault, ...] = ()
    config: SimulationConfig = Field(
        default_factory=SimulationConfig
    )


class IncidentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation: dict
    diagnosis: dict
    recovery_plan: dict
    commentary: dict


@router.post("/incidents/analyze", response_model=IncidentResponse)
def analyze_incident(request: IncidentRequest):
    """Run a cloud failure simulation and produce an incident briefing."""

    try:
        topology = load_topology(request.topology)

        simulation_result = run_simulation(
            topology=topology,
            initial_snapshot=request.initial_snapshot,
            faults=request.faults,
            config=request.config,
        )

        diagnosis, recovery_plan, commentary = run_incident_commander(
            topology=topology,
            simulation_result=simulation_result,
        )

        return IncidentResponse(
            simulation={
                "termination_reason": simulation_result.termination_reason,
                "snapshots": [
                    snapshot.model_dump(mode="json")
                    for snapshot in simulation_result.snapshots
                ],
                "events": [
                    event.model_dump(mode="json")
                    for event in simulation_result.events
                ],
            },
            diagnosis=diagnosis.model_dump(mode="json"),
            recovery_plan=recovery_plan.model_dump(mode="json"),
            commentary=commentary.model_dump(mode="json"),
        )

    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
