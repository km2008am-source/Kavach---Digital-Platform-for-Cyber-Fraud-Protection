"""Government Services Hub endpoint."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from kavach.contracts import ServiceEntry


router = APIRouter(prefix="/api", tags=["services"])
_DATA_FILE = Path(__file__).with_name("services.json")


@router.get("/services", response_model=list[ServiceEntry])
async def get_services() -> list[ServiceEntry]:
    try:
        data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        return [ServiceEntry.model_validate(item) for item in data]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Services data is unavailable",
        ) from exc