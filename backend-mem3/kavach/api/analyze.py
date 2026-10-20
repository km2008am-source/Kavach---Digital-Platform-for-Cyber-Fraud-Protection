# Member 3: POST /api/analyze. The web Scam Check page, and the backup for a WhatsApp outage.
# Accepts JSON {text, language, district} or multipart (file + the same fields).
import asyncio, os, re, uuid
from typing import Literal, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ValidationError

from kavach.analysis.scam_check import analyze
from kavach.api.errors import ApiError, rate_limit
from kavach.contracts import AnalysisRequest, AnalysisResult, InputType

router = APIRouter()

FILES_DIR = os.getenv("FILES_DIR", "files")
MAX_FILE = 20 * 1024 * 1024
MAX_TEXT = 5000
TIMEOUT = 28          # APK budget is 30 s (section 1)
_URL = re.compile(r"^(?:https?://|www\.)\S+$", re.I)

_IMAGE_MAGIC = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".gif": b"GIF8"}
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class AnalyzeBody(BaseModel):
    text: Optional[str] = Field(default=None, max_length=MAX_TEXT)
    language: Literal["ta", "en", "hi"] = "en"
    district: Optional[str] = Field(default=None, max_length=60)


def _is_image_bytes(ext: str, head: bytes) -> bool:
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return head.startswith(_IMAGE_MAGIC[ext])


def _kind(filename: str, mime: str) -> tuple[str, str]:
    """('apk' | 'image', safe_extension). Anything else is refused."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".apk" or mime == "application/vnd.android.package-archive":
        return "apk", ".apk"
    if ext in _IMAGE_EXT:
        return "image", ext
    raise ApiError("unsupported_file", "Please send a screenshot (PNG, JPG, WEBP) or an APK file.", 415)


@router.post("/api/analyze", response_model=AnalysisResult)
async def analyze_endpoint(request: Request):
    rate_limit(request, "analyze", limit=30)
    ctype = request.headers.get("content-type", "")
    path: str | None = None
    try:
        if ctype.startswith("multipart/form-data"):
            if int(request.headers.get("content-length") or 0) > MAX_FILE + 1_000_000:
                raise ApiError("file_too_large", "That file is larger than 20 MB.", 413)
            form = await request.form()
            try:
                body = AnalyzeBody(text=(form.get("text") or None), language=form.get("language") or "en",
                                   district=(form.get("district") or None))
            except ValidationError:
                raise ApiError("invalid_request", "That request was not understood.", 422)
            up = form.get("file")
            kind, ext = (None, None)
            if up is not None and hasattr(up, "read"):
                kind, ext = _kind(up.filename or "", up.content_type or "")
                data = await up.read(MAX_FILE + 1)
                if len(data) > MAX_FILE:
                    raise ApiError("file_too_large", "That file is larger than 20 MB.", 413)
                if not data:
                    raise ApiError("empty_input", "That file is empty.", 422)
                if kind == "image" and not _is_image_bytes(ext, data[:16]):
                    raise ApiError("unsupported_file", "That file does not look like a real image.", 415)
                os.makedirs(FILES_DIR, exist_ok=True)
                path = os.path.join(FILES_DIR, f"{uuid.uuid4().hex}{ext}")   # never the client's file name
                with open(path, "wb") as f:
                    f.write(data)
        else:
            try:
                body = AnalyzeBody(**(await request.json()))
            except (ValidationError, ValueError, TypeError):
                raise ApiError("invalid_request", "Send JSON like {\"text\": \"...\"}.", 422)
            kind = None

        text = (body.text or "").strip()
        if not text and not path:
            raise ApiError("empty_input", "Paste a message, a link, or add a screenshot or APK.", 422)
        if kind == "apk":
            itype = InputType.apk
        elif kind == "image":
            itype = InputType.image
        else:
            itype = InputType.url if _URL.match(text) else InputType.text
        req = AnalysisRequest(request_id=str(uuid.uuid4()), channel="web", input_type=itype,
                              text=text or None, file_path=path, language=body.language,
                              district=body.district)
        try:
            return await asyncio.wait_for(analyze(req), TIMEOUT)
        except asyncio.TimeoutError:
            raise ApiError("analysis_timeout", "The check took too long. Please try again.", 504)
    finally:
        if path and os.path.exists(path):   # web uploads are not kept at all (section 11)
            os.remove(path)
