# Development Plan (Phase A + v1)

## Scope

Deliver an end-to-end deterministic ingest and analytics loop using simulator events and HTTP APIs.

## Milestones

1. Project and package skeleton
2. SQLAlchemy models and Alembic baseline migration
3. Domain entities/value objects and repository interfaces
4. Infrastructure repository implementations and mappers
5. `IngestEventService` and `AnalyticsEngine` v1
6. HTTP v1 endpoint wiring
7. `SimulatorProvider` feed loop
8. Test coverage for determinism and idempotency
9. README runbook and replay demo commands

## Definition Of Done (v1)

- idempotent event ingest works
- deterministic replay produces equal analytics
- latest match state and analytics query endpoints work
- simulator can feed full-match event stream
- lint/format/test commands pass locally

## Non-Goals (v1)

- asynchronous worker split
- external provider polling adapters
- advanced tactical/xT models
- production container orchestration
