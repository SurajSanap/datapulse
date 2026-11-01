# DataPulse dbt project

This project uses dbt Core with the PostgreSQL adapter and reads the weather records written by the backend.

## Prerequisites

- Python 3.12 with a virtual environment.
- PostgreSQL running with the DataPulse migrations applied, including `weather_observations`.
- The PostgreSQL environment variables used by the backend.

The tracked `profiles.yml` uses environment variable lookups only; it does not store credentials. Its development target writes dbt models to the `analytics` schema by default. The source table stays in `public`.

## Install the adapter

From the repository root in PowerShell:

```powershell
Set-Location .\dbt
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, allow scripts for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Configure and check the connection

When running dbt from a machine outside Docker, connect through the published PostgreSQL port. Set the values to match your local `.env` (the values below match `.env.example`):

```powershell
$env:POSTGRES_USER = 'datapulse'
$env:POSTGRES_PASSWORD = 'datapulse_dev_password'
$env:POSTGRES_DB = 'datapulse'
$env:POSTGRES_HOST = 'localhost'
$env:POSTGRES_PORT = '5432'
$env:DBT_SCHEMA = 'analytics'
```

Do not commit real credentials. From the `dbt\` directory, check the connection and project configuration:

```powershell
dbt debug --profiles-dir .
```

The `--profiles-dir .` option tells dbt to load the checked-in, environment-only profile from the current project directory. Run future dbt commands from `dbt\` and include the same option, for example:

```powershell
dbt parse --profiles-dir .
```

When running dbt inside a container on the Compose network, set `POSTGRES_HOST=db` and `POSTGRES_PORT=5432`; for a direct Windows session use `localhost` and the published port instead.

## Weather source

The `models/sources.yml` file documents `public.weather_observations`, including the normalized columns and the raw Open-Meteo payload. Reference it in models with:

```sql
select *
from {{ source('weather', 'weather_observations') }}
```


## Staging model

`models/staging/stg_weather_observations.sql` selects the declared Open-Meteo source and gives its columns stable analytics names and explicit SQL types. It preserves the raw JSON payload and keeps each ingested forecast snapshot; it does not collapse repeated observations from different runs.

The staging properties in `models/staging/schema.yml` document the output types and descriptions. They test the observation ID for uniqueness and required fields for nulls. `tests/weather_measurement_ranges.sql` checks humidity stays within 0–100 percent and precipitation and wind speed are nonnegative. Weather measures that are nullable in the source remain nullable.

After applying backend migrations and setting the connection environment, run the model and its tests from `dbt/\`:

```powershell
dbt build --profiles-dir .
```
