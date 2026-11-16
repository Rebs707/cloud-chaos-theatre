
from app.models.enums import EvidenceKind, ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
    SimulationConfig,
    SimulationSnapshot,
)
from app.models.topology import load_topology
from app.simulation.runner import run_simulation


def make_initial_snapshot(service_ids):
    return SimulationSnapshot(
        step=0,
        services=tuple(
            ServiceSnapshot(
                service_id=service_id,
                state=ServiceState.HEALTHY,
                recovery_counter=0,
            )
            for service_id in service_ids
        ),
    )


def test_healthy_topology_terminates_at_fixed_point():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "hard",
            }
        ],
    })

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["database", "api"]
        ),
    )

    assert result.termination_reason == "fixed_point"
    assert len(result.snapshots) == 2

    assert all(
        service.state == ServiceState.HEALTHY
        for service in result.final_snapshot.services
    )


def test_hard_dependency_cycle_is_detected():
    topology = load_topology({
        "services": [
            {"id": "service-a", "name": "Service A"},
            {"id": "service-b", "name": "Service B"},
        ],
        "edges": [
            {
                "dependent": "service-a",
                "dependency": "service-b",
                "criticality": "hard",
            },
            {
                "dependent": "service-b",
                "dependency": "service-a",
                "criticality": "hard",
            },
        ],
    })

    fault = Fault(
        service_id="service-a",
        start_step=1,
        clear_step=2,
    )

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["service-a", "service-b"]
        ),
        faults=(fault,),
        config=SimulationConfig(max_steps=20),
    )

    assert result.termination_reason == "cycle_detected"
    assert result.final_snapshot.step < 20

    event_kinds = {event.kind for event in result.events}

    assert EvidenceKind.FAULT_INJECTED in event_kinds
    assert EvidenceKind.FAULT_CLEARED in event_kinds


def test_simulation_respects_maximum_step_limit():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })

    fault = Fault(
        service_id="database",
        start_step=1,
        clear_step=20,
    )

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["database"]
        ),
        faults=(fault,),
        config=SimulationConfig(max_steps=3),
    )

    assert result.termination_reason == "max_steps_reached"
    assert result.final_snapshot.step == 3


def test_fault_recovery_lifecycle_records_timeline_events():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })

    fault = Fault(
        service_id="database",
        start_step=1,
        clear_step=2,
    )

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(["database"]),
        faults=(fault,),
        config=SimulationConfig(max_steps=20),
    )

    assert result.termination_reason == "fixed_point"

    event_kinds = [
        event.kind for event in result.events
    ]

    assert EvidenceKind.FAULT_INJECTED in event_kinds
    assert EvidenceKind.FAULT_CLEARED in event_kinds
    assert EvidenceKind.SERVICE_STATE_CHANGE in event_kinds
    assert EvidenceKind.RECOVERY_STARTED in event_kinds
    assert EvidenceKind.RECOVERY_COMPLETED in event_kinds

    assert result.final_snapshot.services[0].state == ServiceState.HEALTHY
