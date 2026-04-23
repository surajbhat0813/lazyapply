from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_connection, init_db

router = APIRouter(prefix="/tracker", tags=["tracker"])

init_db()

VALID_STATUSES = {"saved", "applied", "interviewing", "offer", "rejected"}


class SaveJobRequest(BaseModel):
    title: str
    company: str
    location: str = ""
    url: str = ""
    platform: str = ""
    score: int | None = None
    recommendation: str = ""
    description: str = ""


class UpdateStatusRequest(BaseModel):
    status: str
    notes: str | None = None


class UpdateNotesRequest(BaseModel):
    notes: str


def row_to_dict(row) -> dict:
    return dict(row)


@router.post("/save")
def save_job(req: SaveJobRequest):
    with get_connection() as conn:
        # Prevent duplicate saves for the same URL
        if req.url:
            existing = conn.execute(
                "SELECT id FROM applications WHERE url = ?", (req.url,)
            ).fetchone()
            if existing:
                return {"id": existing["id"], "already_saved": True}

        cursor = conn.execute(
            """
            INSERT INTO applications
                (title, company, location, url, platform, score, recommendation, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.title, req.company, req.location, req.url,
                req.platform, req.score, req.recommendation, req.description,
            ),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "already_saved": False}


@router.get("")
def list_applications(status: str | None = None):
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY saved_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY saved_at DESC"
            ).fetchall()
        return [row_to_dict(r) for r in rows]


@router.patch("/{app_id}/status")
def update_status(app_id: int, req: UpdateStatusRequest):
    if req.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")

    with get_connection() as conn:
        row = conn.execute("SELECT id FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")

        if req.status == "applied":
            conn.execute(
                "UPDATE applications SET status = ?, notes = COALESCE(?, notes), applied_at = datetime('now') WHERE id = ?",
                (req.status, req.notes, app_id),
            )
        else:
            conn.execute(
                "UPDATE applications SET status = ?, notes = COALESCE(?, notes) WHERE id = ?",
                (req.status, req.notes, app_id),
            )
        conn.commit()
        updated = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return row_to_dict(updated)


@router.patch("/{app_id}/notes")
def update_notes(app_id: int, req: UpdateNotesRequest):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        conn.execute("UPDATE applications SET notes = ? WHERE id = ?", (req.notes, app_id))
        conn.commit()
        return {"ok": True}


@router.delete("/{app_id}")
def delete_application(app_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        return {"ok": True}
