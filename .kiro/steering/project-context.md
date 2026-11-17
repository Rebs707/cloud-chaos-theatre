# Cloud Chaos Theatre — Project Context

## Project Overview

Cloud Chaos Theatre is an interactive cloud infrastructure failure simulation and incident analysis platform developed for Kiroween 2026, Frankenstein category.

The application simulates failures across interconnected cloud services, visualises cascading effects, presents incident timelines, identifies root causes, and provides recovery recommendations.

Kiro has been used extensively throughout development, supporting project planning, requirements exploration, architectural discussions, implementation, technical problem-solving, iterative refinement, validation, and debugging.

This document records the current project context and guidance for continued development. It is not a reconstruction of the original development specifications.

## Current Architecture

### Backend
- Python
- FastAPI
- NetworkX
- Pydantic
- Pytest and Hypothesis

Responsibilities:
- Infrastructure topology validation
- Dependency graph processing
- Deterministic failure propagation
- Service-state transitions
- Recovery simulation
- Incident diagnosis
- Recovery recommendations
- Structured incident commentary

### Frontend
- React 19
- TypeScript
- Vite
- React Flow (@xyflow/react)
- Vitest and Testing Library

Responsibilities:
- Interactive infrastructure topology
- Failure scenario selection
- Incident metrics and timeline
- Root-cause and evidence presentation
- Recovery recommendations
- Reset and replay interactions

### API
- GET /health
- POST /api/incidents/analyze

The frontend uses the relative API path /api/incidents/analyze. Vite proxies /api requests to http://localhost:8000 during development.

## Simulation Model

The simulated infrastructure contains three services:
- Database
- API Service
- Worker Service

Dependencies:
- Worker depends on API.
- API depends on Database.

The simulation models hard and soft dependencies and uses explicit service states:
- HEALTHY
- DEGRADED
- DOWN
- RECOVERING

Simulation behaviour must remain deterministic and reproducible for a given configuration.

## Engineering Principles

1. Keep simulation logic independent of the presentation layer.
2. Keep incident diagnosis and recommendations grounded in actual simulation output.
3. Never invent simulation events, service states, or recovery outcomes.
4. Preserve deterministic behaviour and bounded simulation termination.
5. Handle dependency relationships and cyclic graph behaviour deliberately.
6. Prefer small, testable changes over broad refactoring.
7. Preserve existing working functionality.

## Development Guidance

- Understand the relevant implementation before proposing changes.
- Do not inspect or rewrite the entire repository without a specific reason.
- Do not introduce features outside the agreed project scope.
- Do not make speculative refactors or cosmetic changes during submission preparation.
- Identify the exact files affected before implementing a change.
- Explain the reason for each proposed modification.
- Run relevant tests and builds after implementation.
- Report test results accurately.
- Do not commit, push, or overwrite project files without explicit approval.

## Submission Preparation

The immediate priority is a stable, demonstrable application and an accurate Kiroween submission.

Avoid feature expansion. Prioritise genuine defects, reproducibility, documentation, test validation, and judge accessibility.
