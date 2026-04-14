from fastapi import APIRouter, HTTPException

from backend.sessions.session_manager import (
    PLATFORMS,
    cancel_session_login,
    delete_session,
    complete_session_login,
    is_login_pending,
    is_session_saved,
    start_session_login,
    verify_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _validate_platform(platform: str) -> str:
    if platform not in PLATFORMS:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported platform '{platform}'.",
        )
    return platform


@router.get("/platforms")
def list_platforms() -> dict[str, list[str]]:
    return {"platforms": sorted(PLATFORMS.keys())}


@router.get("/{platform}/status")
def get_session_status(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)

    return {
        "platform": platform,
        "saved": is_session_saved(platform),
        "login_in_progress": is_login_pending(platform),
    }


@router.post("/{platform}/save/start")
def start_session_save(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)

    if is_login_pending(platform):
        raise HTTPException(
            status_code=409,
            detail=f"Login is already in progress for '{platform}'.",
        )

    started = start_session_login(platform)
    if not started:
        raise HTTPException(
            status_code=409,
            detail=f"Login is already in progress for '{platform}'.",
        )

    return {
        "platform": platform,
        "started": True,
        "message": "Browser opened. Log in manually, then call the complete endpoint.",
    }


@router.post("/{platform}/save/complete")
def complete_session_save(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)
    cookie_count = complete_session_login(platform)

    if cookie_count is None:
        raise HTTPException(
            status_code=409,
            detail=f"No login is currently in progress for '{platform}'.",
        )

    return {
        "platform": platform,
        "saved": True,
        "cookie_count": cookie_count,
    }


@router.post("/{platform}/save/cancel")
def cancel_session_save(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)
    cancelled = cancel_session_login(platform)

    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail=f"No login is currently in progress for '{platform}'.",
        )

    return {
        "platform": platform,
        "cancelled": True,
    }


@router.post("/{platform}/verify")
def verify_saved_session(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)

    try:
        result = verify_session(platform)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No saved session found for '{platform}'.",
        )

    return result


@router.delete("/{platform}")
def remove_session(platform: str) -> dict[str, object]:
    platform = _validate_platform(platform)

    session_was_saved = is_session_saved(platform)
    delete_session(platform)

    return {
        "platform": platform,
        "deleted": session_was_saved,
    }
