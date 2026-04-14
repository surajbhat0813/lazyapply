from fastapi import FastAPI

from backend.api.sessions import router as sessions_router

app = FastAPI(title="JobAgent API", version="0.1.0")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sessions_router)
