# DataPulse

A data observability platform for ingesting, transforming, validating, and monitoring real-world data pipelines.

## Local development on Windows

Run the commands in this guide in **PowerShell**, from the **repository root**: the `datapulse` folder that contains `docker-compose.yml`, `.env.example`, and this `README.md`. Do not run the Docker Compose commands from `backend\`. If you are not there already, open the repository folder in VS Code and choose **Terminal → New Terminal**, or change to your clone's path:

```powershell
Set-Location 'C:\path\to\datapulse'
Get-Location
Test-Path .\docker-compose.yml
```

The last command should return `True`.

### Prerequisites

- **Docker Desktop for Windows**, configured to use the **WSL 2 backend**. Start Docker Desktop and wait until its engine is running.
- **Git for Windows**, to clone the repository.
- **Python 3.12** and a virtual environment are optional for running the backend directly on Windows instead of in a container.
- For the direct local backend option, PostgreSQL 16 must be available on `localhost:5432`. You can install PostgreSQL locally, or use Docker Desktop to run only the database.

Open a new PowerShell window after installing Docker Desktop, then confirm Docker and Compose are available:

```powershell
docker --version
docker compose version
```

### Configure and start with Docker Compose

Run these commands from the repository root:

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
docker compose config
docker compose up --build -d
```

The first command creates `.env` from the tracked example only when `.env` does not already exist, so it preserves your existing local settings. Review `.env` if you need to change ports or credentials. The sample credentials are for local development only.

`docker compose config` validates the Compose file and resolved environment before starting. The API container waits for the PostgreSQL health check before it starts.

Check service status and follow logs:

```powershell
docker compose ps
docker compose logs -f
```

Press **Ctrl+C** to stop following logs; this does not stop the services. To inspect just one service, use `docker compose logs -f api` or `docker compose logs -f db`.

Test API liveness and database readiness from PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/ready
```

Liveness should return `status: ok`. Readiness should return `status: ready` and `database: connected`. A readiness failure means the API cannot reach PostgreSQL yet. The interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

The default host ports are API `8000` and PostgreSQL `5432`. If you change `API_PORT` or `POSTGRES_PUBLISHED_PORT` in `.env`, use the corresponding API port when testing the endpoints.

### Stop the services

From the repository root:

```powershell
docker compose down
```

This stops and removes the containers while preserving the database volume. To intentionally delete the local database and all its data as well:

```powershell
docker compose down --volumes
```

### Run the backend directly on Windows

This option runs FastAPI in a Python virtual environment. PostgreSQL must still be running and reachable at `localhost:5432`. Either install PostgreSQL 16 locally and create the configured database/user, or start just the Compose database from the repository root:

```powershell
docker compose up -d db
```

Then switch into the backend directory, create and activate a virtual environment, and install the dependencies:

```powershell
Set-Location .\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, allow scripts for this terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Set the same development connection values used by `.env.example` for this PowerShell session, then start the API:

```powershell
$env:POSTGRES_USER = 'datapulse'
$env:POSTGRES_PASSWORD = 'datapulse_dev_password'
$env:POSTGRES_DB = 'datapulse'
$env:POSTGRES_HOST = 'localhost'
$env:POSTGRES_PORT = '5432'
python -m uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`. In another PowerShell window, test it with:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/ready
```

Stop the local API with **Ctrl+C**. If you started the database with Compose, return to the repository root before stopping it:

```powershell
Set-Location ..
docker compose down
```

### Apply database migrations

The API image includes Alembic. Start the Compose services from the repository root, then apply the schema migration:

```powershell
docker compose up -d --build
docker compose exec api alembic upgrade head
```

For a backend running directly in the virtual environment, run the migration from `backend\` after setting the PostgreSQL environment variables from the direct backend setup above:

```powershell
alembic upgrade head
```

Alembic reads the same `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, and `POSTGRES_PORT` settings as the API. To check the current revision, run `alembic current` from `backend\`. New schema changes should be added as Alembic revisions; do not use `Base.metadata.create_all()` in application startup.

## System architecture

<img width="722" height="731" alt="DataPulse system architecture" src="https://github.com/user-attachments/assets/e36bd943-9d33-4278-9744-a607ca0c8a63" />

## Technology stack

<img width="725" height="527" alt="DataPulse technology stack" src="https://github.com/user-attachments/assets/3f2f9480-5b3e-4ed3-a3d6-516153766867" />

## Repository layout

```text
datapulse/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── schemas/
│   ├── Dockerfile
│   └── requirements.txt
├── ingestion/
│   ├── sources/
│   ├── pipelines/
│   ├── storage/
│   └── main.py
├── orchestration/
│   └── flows/
├── dbt/
│   └── models/
├── frontend/
│   └── src/
├── data/
│   └── bronze/
├── infrastructure/
├── docker-compose.yml
├── .env.example
└── README.md
```

### Run the Open-Meteo weather pipeline

The pipeline fetches one day of hourly weather for the configured coordinates, stores each observation and its source payload, and records the run outcome in `pipeline_runs`. The defaults point to Delhi. Set `OPEN_METEO_LATITUDE` and `OPEN_METEO_LONGITUDE` in `.env` to change the location; the Compose API service passes these values to the pipeline.

Apply database migrations first, then run the pipeline from the repository root:

```powershell
docker compose exec api python -m app.ingestion.weather
```

For a backend running directly in the virtual environment, run the same command from `backend\` after applying migrations:

```powershell
python -m app.ingestion.weather
```

The command prints the run ID, status, and number of persisted observations. Each invocation creates a new pipeline run and a new forecast snapshot.
