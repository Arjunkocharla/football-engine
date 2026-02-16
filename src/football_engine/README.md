# Source Package Guide

This package follows a layered architecture:

- `domain`: pure business logic and contracts
- `application`: orchestration services (use-cases)
- `infrastructure`: adapters and persistence implementations
- `api`: transport layer (HTTP/WS schemas and routes)

Read `docs/module_map.md` for full package ownership and navigation.

## Runtime entrypoint

- ASGI app module: `football_engine.main:app`
- Local run command: `make run`
