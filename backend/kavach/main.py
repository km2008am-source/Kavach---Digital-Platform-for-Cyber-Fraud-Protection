"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from kavach import db
from kavach.whatsapp.webhook import router as whatsapp_router
from kavach.api.services import router as services_router
import asyncio
from kavach.whatsapp.cleanup import delete_expired_files

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.initialize()

    # Clean expired files at startup, then check once an hour.
    await asyncio.to_thread(delete_expired_files)

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(60 * 60)
            await asyncio.to_thread(delete_expired_files)

    cleanup_task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Kavach API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(whatsapp_router)
app.include_router(services_router)

@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}