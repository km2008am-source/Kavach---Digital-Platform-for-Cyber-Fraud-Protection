"""Image -> text with Tesseract (English + Tamil).

Needs the Tesseract binary with the `tam` language pack (`tesseract --list-langs`). It is
found via TESSERACT_CMD, then PATH, then the Windows installer's default folder. If it is
missing, `read()` raises `OCRUnavailable`; callers fall back to the caption text and mark
the verdict as lower confidence.
"""
import re
import shutil
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

from kavach.analysis import files
from kavach.analysis.rules import clean_text
from kavach.analysis.settings import settings

WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


class OCRUnavailable(Exception):
    pass


def tesseract_cmd() -> str | None:
    if settings.TESSERACT_CMD:
        return settings.TESSERACT_CMD
    if shutil.which("tesseract"):
        return None                                         # pytesseract finds it on PATH
    return str(WINDOWS_DEFAULT) if WINDOWS_DEFAULT.exists() else None


@lru_cache(maxsize=1)
def _langs() -> str:
    import pytesseract
    cmd = tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        available = set(pytesseract.get_languages(config=""))
    except Exception as e:                                  # binary not installed / not on PATH
        raise OCRUnavailable(str(e)) from e
    return "+".join(l for l in ("eng", "tam") if l in available) or "eng"


def preprocess(img: Image.Image) -> Image.Image:
    """Greyscale + 2x upscale for small phone screenshots: noticeably better OCR."""
    img = ImageOps.exif_transpose(img).convert("L")
    if img.width < 1000:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return img


_WRAPPED_URL = re.compile(r"((?:https?://|www\.)\S*[-./_=?&])[ \t]*\n[ \t]*(?=\S)", re.I)


def rejoin_wrapped_links(text: str) -> str:
    """Phones wrap long links across lines ("http://sbi-kyc-" / "update.xyz/login").
    Rejoin them so the link checker sees the whole domain."""
    return _WRAPPED_URL.sub(r"\1", text)


def read(path: str) -> str:
    files.check_size(path)                                  # 20 MB cap, checked before decoding
    import pytesseract
    langs = _langs()
    with Image.open(path) as img:
        raw = pytesseract.image_to_string(preprocess(img), lang=langs)
    return rejoin_wrapped_links(clean_text(raw).strip())
