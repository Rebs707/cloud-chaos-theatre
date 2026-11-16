
from app.diagnosis.analyzer import diagnose_incident
from app.models.enums import CauseKind, ServiceState
from app.models.simulation import (
    Fault,
    ServiceSnapshot,
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


def test_diagnosis_identifies_injected_fault_as_root_cause():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
        ],
        "edges": [],
    })

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(["database"]),
        faults=(
            Fault(
                service_id="database",
                start_step=1,
                clear_step=2,
            ),
        ),
    )

    diagnosis = diagnose_incident(topology, result)

    assert len(diagnosis.root_causes) == 1
    root_cause = diagnosis.root_causes[0]

    assert root_cause.service_id == "database"
    assert root_cause.service_name == "Database"
    assert root_cause.cause_kind == CauseKind.ACTIVE_FAULT
    assert root_cause.evidence[0].step == 1
    assert diagnosis.termination_reason == "fixed_point"


def test_diagnosis_traces_affected_downstream_service():
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
        faults=(
            Fault(
                service_id="database",
                start_step=1,
                clear_step=2,
            ),
        ),
    )

    diagnosis = diagnose_incident(topology, result)

    assert len(diagnosis.root_causes) == 1
    assert diagnosis.root_causes[0].service_id == "database"
    assert len(diagnosis.affected_services) == 1

    affected = diagnosis.affected_services[0]

    assert affected.service_id == "api"
    assert affected.service_name == "API"
    assert affected.root_cause_service_id == "database"
    assert affected.dependency_path == ("api", "database")
    assert affected.current_state == "healthy"


def test_diagnosis_does_not_invent_root_cause_without_fault():
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

    diagnosis = diagnose_incident(topology, result)

    assert diagnosis.root_causes == ()
    assert diagnosis.affected_services == ()
    assert "No explicit fault injection" in diagnosis.summary


def test_diagnosis_identifies_multiple_simultaneous_faults():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "cache", "name": "Cache"},
        ],
        "edges": [],
    })

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["database", "cache"]
        ),
        faults=(
            Fault(
                service_id="database",
                start_step=1,
                clear_step=2,
            ),
            Fault(
                service_id="cache",
                start_step=1,
                clear_step=2,
            ),
        ),
    )

    diagnosis = diagnose_incident(topology, result)

    root_cause_ids = {
        cause.service_id
        for cause in diagnosis.root_causes
    }

    assert root_cause_ids == {"database", "cache"}
    assert len(diagnosis.root_causes) == 2
    assert diagnosis.affected_services == ()

    assert all(
        cause.cause_kind == CauseKind.ACTIVE_FAULT
        for cause in diagnosis.root_causes
    )


def test_diagnosis_identifies_affected_service_with_soft_dependency():
    topology = load_topology({
        "services": [
            {"id": "database", "name": "Database"},
            {"id": "api", "name": "API"},
        ],
        "edges": [
            {
                "dependent": "api",
                "dependency": "database",
                "criticality": "soft",
            }
        ],
    })

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["database", "api"]
        ),
        faults=(
            Fault(
                service_id="database",
                start_step=1,
                clear_step=2,
            ),
        ),
    )

    diagnosis = diagnose_incident(topology, result)

    assert len(diagnosis.root_causes) == 1
    assert diagnosis.root_causes[0].service_id == "database"

    affected = next(
        service
        for service in diagnosis.affected_services
        if service.service_id == "api"
    )

    assert affected.root_cause_service_id == "database"
    assert affected.dependency_path == ("api", "database")
    assert affected.current_state == "healthy"

    api_states = [
        service.state
        for snapshot in result.snapshots
        for service in snapshot.services
        if service.service_id == "api"
    ]

    assert ServiceState.DEGRADED in api_states
    assert ServiceState.DOWN not in api_states


def test_diagnosis_handles_cyclic_dependencies():
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

    result = run_simulation(
        topology=topology,
        initial_snapshot=make_initial_snapshot(
            ["service-a", "service-b"]
        ),
        faults=(
            Fault(
                service_id="service-a",
                start_step=1,
                clear_step=2,
            ),
        ),
    )

    diagnosis = diagnose_incident(topology, result)

    assert len(diagnosis.root_causes) == 1
    assert diagnosis.root_causes[0].service_id == "service-a"

    affected = next(
        service
        for service in diagnosis.affected_services
        if service.service_id == "service-b"
    )

    assert affected.root_cause_service_id == "service-a"
    assert affected.dependency_path == (
        "service-b",
        "service-a",
    )

