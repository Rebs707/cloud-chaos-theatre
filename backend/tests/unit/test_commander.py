
from app.commentary.commander import run_incident_commander
from app.models.enums import ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.runner import run_simulation


def make_topology():
    return load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
            {"id": "worker", "name": "Worker"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            },
            {
                "dependent": "worker",
                "dependency": "api",
                "criticality": "hard",
            },
        ],
    })


def make_initial_snapshot():
    return SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
            ServiceSnapshot(
                service_id="api",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
            ServiceSnapshot(
                service_id="worker",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
        ),
    )


def test_incident_commander_runs_complete_incident_workflow():
    topology = make_topology()

    simulation_result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(),
        faults=(
            Fault(
                service_id="database",
                start_step=1,
            ),
        ),
    )

    diagnosis, recovery_plan, commentary = run_incident_commander(
        topology=topology,
        simulation_result=simulation_result,
    )

    assert len(diagnosis.root_causes) == 1
    assert diagnosis.root_causes[0].service_id == "database"

    assert {
        service.service_id
        for service in diagnosis.affected_services
    } == {"api", "worker"}

    assert [
        recommendation.service_id
        for recommendation in recovery_plan.recommendations
    ] == ["database", "api", "worker"]

    assert commentary.source == "deterministic_fallback"
    assert "Database" in commentary.headline
    assert len(commentary.immediate_actions) == 3


def test_incident_commander_handles_healthy_system():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })

    initial_snapshot = SimulationSnapshot(
        step=0,
        services=(
            ServiceSnapshot(
                service_id="database",
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            ),
        ),
    )

    simulation_result = run_simulation(
        topology=topology,
        initial_snapshot=initial_snapshot,
    )

    diagnosis, recovery_plan, commentary = run_incident_commander(
        topology=topology,
        simulation_result=simulation_result,
    )

    assert diagnosis.root_causes == ()
    assert recovery_plan.recommendations == ()
    assert commentary.immediate_actions == ()
    assert "No explicit fault injection" in commentary.key_findings[0]

