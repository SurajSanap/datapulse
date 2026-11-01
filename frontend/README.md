# DataPulse frontend

The React/Vite dashboard reads run history from the FastAPI service at `VITE_API_BASE_URL`. The default is `http://localhost:8000`.

## Run the API and database

From the repository root, start PostgreSQL and the API, then apply the migrations:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
```

The API allows browser requests from the default Vite origins `http://localhost:3000` and `http://127.0.0.1:3000`. To use a different Vite origin, set `CORS_ORIGINS` in the root `.env` file to a comma-separated list of allowed origins, then recreate the API container:

```dotenv
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

```powershell
docker compose up -d --build api
```

## Run Vite

In a new PowerShell terminal from the repository root:

```powershell
Set-Location .\frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Vite reads `.env.local` and passes `VITE_API_BASE_URL` to the dashboard. Change that value if the API is running at a different URL, then restart Vite.

For a backend started directly from `backend/`, set `CORS_ORIGINS` in that PowerShell session before starting Uvicorn. The default Vite origins are already allowed.