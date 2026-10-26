# Member 3: /api/pulse/*, thin routes over Member 2's pulse module.
import inspect

from fastapi import APIRouter, Query, Request

from kavach.analysis import pulse
from kavach.api.errors import ApiError
from kavach.web_settings import settings
from kavach.analysis.models import PulseAlert

router = APIRouter()


async def _maybe_await(value):
    # section 5 shows alerts() as sync; replay() is not specified, so accept either
    return await value if inspect.isawaitable(value) else value


@router.get("/api/pulse/alerts", response_model=list[PulseAlert])
async def alerts(hours: int = Query(72, ge=1, le=720)):
    return await _maybe_await(pulse.alerts(hours))


@router.post("/api/pulse/replay")
async def replay(request: Request):
    # Section 11: no admin endpoints on the public app. Replay only exists while DEMO_MODE=1.
    if not settings.DEMO_MODE:
        raise ApiError("replay_disabled", "The demo replay is switched off.", 403)
    await _maybe_await(pulse.replay())
    return {"ok": True, "demo_data": True}
