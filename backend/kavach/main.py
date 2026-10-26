"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from kavach import db
from kavach.whatsapp.webhook import router as whatsapp_router
from kavach.api.services import router as services_router
from kavach.api import errors, store
from kavach.api.analyze import router as analyze_router
from kavach.api.news import router as news_router
from kavach.api.news_fetch import refresh as refresh_news
from kavach.api.pulse import router as pulse_router
from kavach.api.sim import router as sim_router
from kavach.calls.twilio_routes import router as calls_router
from kavach.web_settings import settings as web_settings
import asyncio
from kavach.whatsapp.cleanup import delete_expired_files

STATIC_DIR = Path(__file__).resolve().parent / "static"
WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.initialize()
    store.init()

    # Clean expired files at startup, then check once an hour.
    await asyncio.to_thread(delete_expired_files)

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(60 * 60)
            await asyncio.to_thread(delete_expired_files)

    cleanup_task = asyncio.create_task(cleanup_loop())
    news_task = asyncio.create_task(refresh_news())      # never blocks startup, never raises
    try:
        yield
    finally:
        news_task.cancel()
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
app.add_middleware(CORSMiddleware, allow_origins=web_settings.WEB_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
errors.install(app)          # one {"error", "message"} format for every /api/* failure

app.include_router(whatsapp_router)
app.include_router(services_router)
app.include_router(analyze_router)
app.include_router(sim_router)
app.include_router(pulse_router)
app.include_router(news_router)
app.include_router(calls_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


# The built website is served last, so it never shadows an API or webhook route.
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
