# Architecture

## Goals

Build a deterministic, provider-agnostic football analytics engine that runs comfortably on Raspberry Pi 4 (1GB) and supports future extension to external APIs.

## Layered Boundaries

- `domain`
  - Pure business logic.
  - No framework, ORM, or transport dependencies.
- `application`
  - Use-case orchestration.
  - Coordinates repositories and domain services.
- `infrastructure`
  - SQLAlchemy ORM models, repository implementations, provider adapters, simulator.
- `api`
  - HTTP and WebSocket transport layer, validation DTOs, dependency wiring.

Dependency direction:

- `api` -> `application` -> `domain`
- `infrastructure` implements interfaces defined in `domain` or `application`

## Runtime Flow (v1 synchronous ingest)

1. Client posts event to `POST /events`.
2. API validates input and forwards to `IngestEventService`.
3. Service deduplicates event (idempotency key).
4. Service persists event, updates match state, computes analytics snapshot.
5. Service persists latest snapshot and returns response payload.

## Provider-Agnostic Rule

All providers must map external payloads into a normalized domain event contract before touching core services.

## Persistence Rule

Application code uses ORM repositories only. No raw SQL outside Alembic migrations.

## Determinism Rule

Given identical ordered event streams for a match, output snapshots must be identical under the same model version and configuration.
