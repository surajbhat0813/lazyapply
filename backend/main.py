from fastapi import FastAPI

from backend.api.sessions import router as sessions_router
from backend.api.jobs import router as jobs_router

app = FastAPI(title="JobAgent API", version="0.1.0")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sessions_router)
app.include_router(jobs_router)
