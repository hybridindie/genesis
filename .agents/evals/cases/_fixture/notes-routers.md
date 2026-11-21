Planning notes — two new backend features, 2026-11-15

Marco: two independent features this sprint.
- Audit log API: new package backend/app/audit/ with its own router at /audit.
  Needs the `structlog` dependency.
- Favorites API: new package backend/app/favorites/ with a router at
  /favorites. Needs the `sqlalchemy-utils` dependency.
Both routers get mounted in backend/app/main.py, and both add a dependency to
backend/pyproject.toml (which regenerates backend/uv.lock). Otherwise the two
features share nothing and different people want to work on them at once.
Each feature gets its own tests file.
