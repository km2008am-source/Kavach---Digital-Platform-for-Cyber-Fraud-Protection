import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()
DEMO_SERVICES = Path(__file__).resolve().parents[3] / "web" / "public" / "demo" / "services.json"
LOCAL_SERVICES = Path(__file__).with_name("services.json")


@router.get("/api/services")
async def services():
    path = LOCAL_SERVICES if LOCAL_SERVICES.exists() else DEMO_SERVICES
    return json.loads(path.read_text(encoding="utf-8"))
