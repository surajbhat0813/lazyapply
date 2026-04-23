from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.sessions import router as sessions_router
from backend.api.jobs import router as jobs_router
from backend.api.tracker import router as tracker_router
from backend.api.chat import router as chat_router

app = FastAPI(title="JobAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sessions_router)
app.include_router(jobs_router)
app.include_router(tracker_router)
app.include_router(chat_router)
