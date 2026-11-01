from fastapi import FastAPI

app = FastAPI(title="Datapulse API", version="0.1.0")


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to Datapulse API"}


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}
