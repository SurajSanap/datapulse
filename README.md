# DataPulse

A data observability platform for ingesting, transforming, validating, and monitoring real-world data pipelines.

## Local development

### Prerequisites

- Docker Desktop (or Docker Engine) with the Docker Compose plugin
- Git

### Start the API and PostgreSQL

```bash
cp .env.example .env
docker compose up --build
```

The API container waits until PostgreSQL passes its health check before starting.

Once the containers are running:

- API: http://localhost:8000
- API liveness check: http://localhost:8000/health
- API readiness check (includes PostgreSQL connectivity): http://localhost:8000/health/ready
- Interactive API docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

The liveness endpoint reports whether the API process is responding. The readiness endpoint runs a lightweight `SELECT 1` query against PostgreSQL and returns HTTP 503 if the database cannot be reached.

The default credentials in `.env.example` are for local development only. Change them for any shared or deployed environment. The root `.env` file is ignored by Git; keep secrets out of commits.

### Useful commands

```bash
# Validate the Compose configuration
docker compose config

# Start in the background
docker compose up --build -d

# Follow service logs
docker compose logs -f

# Check service status
docker compose ps

# Stop containers (keeps database data)
docker compose down

# Stop containers and delete the local database volume
docker compose down -v
```

PostgreSQL data is stored in the named Docker volume `datapulse_postgres_data`, so it survives a normal `docker compose down`. Use `docker compose down -v` only when you intentionally want to reset the local database.

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
