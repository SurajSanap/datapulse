# Deployment and release workflow

This guide describes the repository's current single-host Docker Compose deployment. It is suitable for local use and a controlled staging environment. The repository does not yet provide a cloud deployment target or production operations for secrets, TLS, backups, monitoring, or horizontal scaling; review the limitations below before exposing a deployment publicly.

## Configure a host

1. Install Docker Engine and the Docker Compose plugin, then clone the repository.
2. From the repository root, create a local environment file if needed:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

3. Edit `.env`. Replace the example PostgreSQL password, choose host ports that are available, and set the desired Open-Meteo coordinates. The frontend's `VITE_API_BASE_URL` defaults to `/api`, which is served through the same-origin Nginx proxy. This value is embedded when the frontend image is built, so rebuild the frontend after changing it. Do not commit `.env` or put secrets in `VITE_*` variables; frontend values are public to browser users.
4. Validate the resolved Compose configuration:

   ```powershell
   docker compose config --quiet
   ```

The example credentials are for local development only. A public production deployment needs secret injection, HTTPS termination, a production API server configuration, database backup and restore procedures, and a deployment platform appropriate to its availability and security requirements.

## Start and verify the stack

From the repository root:

```powershell
docker compose up --build -d
docker compose ps
```

The frontend waits for API readiness, and the API waits for PostgreSQL health. Apply pending schema migrations before using the application:

```powershell
docker compose exec api alembic upgrade head
```

Verify the API, database readiness, frontend page, and same-origin proxy:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/ready
(Invoke-WebRequest http://localhost:3000/ -UseBasicParsing).StatusCode
Invoke-RestMethod http://localhost:3000/api/health/ready
Invoke-RestMethod http://localhost:3000/api/pipeline-runs
```

The frontend is at `http://localhost:3000`; the API's direct health checks and interactive docs are at `http://localhost:8000/health`, `/health/ready`, and `/docs`. Set `FRONTEND_PORT`, `API_PORT`, or `POSTGRES_PUBLISHED_PORT` in `.env` if those defaults conflict with another service.

Review service logs with `docker compose logs --tail 100`. Stop the stack while keeping the database volume with `docker compose down`. Do not use `docker compose down --volumes` on a deployed database unless intentionally deleting its data.

## Release checklist

- [ ] All pull request checks pass on the commit being released.
- [ ] Review dependency changes, configuration changes, and Alembic revisions; test migrations against a disposable database.
- [ ] For a database with data, take and verify a recoverable backup before applying migrations.
- [ ] Confirm `.env` is host-specific, contains no sample credentials, and is not committed. Confirm frontend build-time variables contain no secrets.
- [ ] Build and start the exact release commit in staging with `docker compose config --quiet` and `docker compose up --build -d`.
- [ ] Apply migrations and run the endpoint checks in “Start and verify the stack.” Review service logs for errors.
- [ ] Create an annotated Git tag using `vMAJOR.MINOR.PATCH` (for example, `v0.1.0`) and publish release notes describing user-visible changes and any migration steps.
- [ ] Deploy the tagged commit, apply migrations, and repeat readiness and frontend/API smoke checks.

## Rollback and operational limits

To roll back application code, check out the previous release tag and rebuild/restart the Compose stack. Database changes may not be safely reversible: review each Alembic downgrade and use the verified database backup if a schema rollback would lose data. A database restore procedure is not automated by this repository.

The Compose setup is single-host and uses the API image's current Uvicorn command, which enables reload. It does not configure TLS, external secret storage, database backups, monitoring/alerting, or multi-instance scaling. Treat it as a development/staging deployment until those operational requirements are supplied for the target environment.
