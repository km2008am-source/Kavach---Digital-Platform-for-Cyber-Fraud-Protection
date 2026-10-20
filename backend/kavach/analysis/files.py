"""Upload limits shared by every analysis path that opens a user's file (images, APKs).

Guide section 11: max 20 MB per file. The check uses the size on disk (`stat()`), so an
oversized upload is refused before a single byte is read, hashed or decoded.
"""
from pathlib import Path

from kavach.analysis.settings import settings


class FileTooLarge(ValueError):
    pass


def check_size(path: str | Path) -> None:
    limit = settings.MAX_FILE_BYTES
    if Path(path).stat().st_size > limit:
        raise FileTooLarge(f"larger than {limit / (1024 * 1024):g} MB")
