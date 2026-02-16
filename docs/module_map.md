# Module Map

This map shows intended ownership for each package in Phase A + v1.

## Source Tree

```text
src/football_engine/
  domain/
    entities/
    value_objects/
    enums/
    strategies/
    services/
    repositories/        # repository interfaces only
  application/
    services/            # use-case orchestration
    dto/
    ports/
  infrastructure/
    db/                  # SQLAlchemy models + session/unit-of-work
    repositories/        # ORM-backed repository implementations
    providers/           # simulator + external adapters
    mappers/             # domain <-> ORM/provider mappings
  api/
    http/v1/             # REST endpoints
    ws/v2/               # websocket streaming
    schemas/             # API request/response models
    dependencies/        # dependency wiring
```

## Supporting Tree

```text
docs/                    # architecture and implementation guidance
tests/
  unit/domain/
  unit/application/
  integration/api/
  fixtures/replay_cases/
alembic/versions/        # DB migrations
scripts/                 # local helper scripts for Pi workflows
```
