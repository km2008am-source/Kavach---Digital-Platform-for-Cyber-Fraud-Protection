# M1 owns main.py. Minimal version that mounts Member 3's routers; M1's real file replaces it
# and keeps the same include_router / install lines.
import asyncio, logging, os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from kavach.config import settings
from kavach.db import init_db
from kavach.api import errors
from kavach.api.analyze import router as analyze_router
from kavach.api.news import router as news_router
from kavach.api.news_fetch import refresh as refresh_news
from kavach.api.pulse import router as pulse_router
from kavach.api.sim import router as sim_router
from kavach.calls.twilio_routes import router as twilio_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
HERE = os.path.dirname(__file__)
STATIC = os.path.join(HERE, "static")
WEB_DIST = os.path.join(HERE, "..", "..", "web", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    news_task = asyncio.create_task(refresh_news())      # never blocks startup, never raises
    yield
    news_task.cancel()


app = FastAPI(title="Kavach", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.WEB_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
errors.install(app)
app.include_router(twilio_router)
app.include_router(analyze_router)
app.include_router(sim_router)
app.include_router(pulse_router)
app.include_router(news_router)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/health")
async def health():
    return {"ok": True}


# The built React app is served last, so it never shadows an API or webhook route.
if os.path.isdir(WEB_DIST):
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
