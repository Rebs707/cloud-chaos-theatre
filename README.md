# Cloud Chaos Theatre

### Interactive Cloud Infrastructure Failure Simulation Platform

**Kiroween 2026 · Frankenstein Category**

Cloud Chaos Theatre is an interactive platform for simulating cloud infrastructure failures, exploring cascading service dependencies, and understanding incident behaviour through visualisation and structured analysis.

It combines deterministic simulation, dependency-graph modelling, incident diagnosis, recovery planning and an interactive operational dashboard.

All infrastructure and incidents are simulated. The application does not modify live cloud infrastructure.

## The Problem

Cloud infrastructure consists of interconnected services. A failure in one component can affect dependent services, creating cascading incidents that are difficult to understand in isolation.

Cloud Chaos Theatre provides a controlled environment to explore failure propagation, service-state transitions, incident timelines and recovery behaviour.

## Features

- Interactive infrastructure topology.
- Database, API Service and Worker Service failure scenarios.
- Hard and soft dependency modelling.
- Deterministic failure propagation.
- Healthy, degraded, down and recovering service states.
- Visual incident timeline and event tracking.
- Root-cause diagnosis with supporting evidence.
- Prioritised recovery recommendations.
- Structured Incident Commander briefing.
- Reset and replay functionality.

## How It Works

The simulated infrastructure contains three services:

| Service | Depends on |
|---|---|
| Worker Service | API Service |
| API Service | Database |
| Database | None |

A user selects a failure scenario. The backend executes a deterministic simulation, evaluates dependency relationships, tracks service states and recovery progress, and produces structured incident results.

The frontend visualises the resulting infrastructure behaviour and incident analysis.

## Architecture

```text
             React Dashboard
                    |
                    v
                FastAPI
                    |
                    v
          Request Validation
                    |
                    v
        Infrastructure Topology
                    |
                    v
       Deterministic Simulation
                    |
                    v
          Simulation Results
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Diagnosis Recovery Commentary
          |         |         |
          +---------+---------+
                    |
                    v
             Incident Response
                    |
                    v
             React Dashboard
```

### Backend

Python, FastAPI, NetworkX and Pydantic handle topology validation, dependency graphs, failure propagation, recovery simulation, diagnosis, recommendations and commentary.

### Frontend

React 19, TypeScript, Vite and React Flow provide the interactive dashboard, topology visualisation, scenario controls and incident timeline.

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Graph modelling | NetworkX |
| Validation | Pydantic |
| Backend testing | Pytest, Hypothesis |
| Frontend | React 19, TypeScript |
| Build tooling | Vite |
| Visualisation | React Flow |
| Frontend testing | Vitest, Testing Library |

## Repository Structure

```text
cloud-chaos-theatre/
├── .kiro/
│   └── steering/
│       └── project-context.md
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── public/
│   └── src/
├── src/
│   └── components/
├── LICENSE
└── README.md
```

## Running Locally

### Prerequisites

- Python 3.12 or compatible version
- Node.js
- npm

### 1. Backend

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`

Health check: `http://localhost:8000/health`

API documentation: `http://localhost:8000/docs`

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests to `http://localhost:8000`.

Open the local URL displayed by Vite.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/api/incidents/analyze` | Run incident simulation and analysis |

The incident endpoint accepts topology, initial service states, faults and simulation configuration. It returns simulation snapshots, events, diagnosis, recovery plan and commentary.

Invalid topology or request values return HTTP 422.

## Testing

### Backend

```bash
cd backend
pytest
```

The backend suite includes unit and property-based tests covering graph behaviour, propagation, recovery and simulation termination.

### Frontend

```bash
cd frontend
npm test
npm run build
```

The production build runs TypeScript compilation and Vite.

## Engineering Principles

- Deterministic and reproducible simulation.
- Separation of simulation and incident-analysis responsibilities.
- Evidence-based diagnosis and recommendations.
- Dependency-aware failure and recovery behaviour.
- Bounded simulation execution.
- Testable implementation and explicit service states.

## Development with Kiro

Kiro was an integral development partner throughout the creation of Cloud Chaos Theatre.

Its involvement extended across the development lifecycle, including:

1. **Project planning and requirements exploration:** Refining the project concept, exploring requirements and defining expected application behaviour.
2. **Architecture and technical design:** Exploring system architecture, dependency modelling and the separation of simulation, analysis and presentation.
3. **Implementation:** Supporting development across the Python backend, simulation engine, API and React frontend.
4. **Technical problem-solving:** Working through dependency relationships, failure propagation, service-state transitions, recovery behaviour and integration challenges.
5. **Iterative development:** Refining implementation decisions and application behaviour through continued technical discussions and feedback.
6. **Validation and debugging:** Investigating application behaviour, identifying defects, validating changes and implementing subsequent improvements.

Kiro was used throughout the development process as a technical development partner, not merely for isolated code generation or final debugging.

The `.kiro/steering/` directory contains current project context and development guidance.

## Project Scope

Cloud Chaos Theatre operates entirely within a simulated infrastructure environment. It does not connect to or control live AWS, Azure, GCP or other cloud infrastructure.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.