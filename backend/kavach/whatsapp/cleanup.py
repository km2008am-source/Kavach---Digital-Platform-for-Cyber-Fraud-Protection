"""Remove expired temporary media and generated files."""

from datetime import datetime, timedelta
from pathlib import Path

from kavach.config import settings


def delete_expired_files(
    directory: str | Path | None = None,
    max_age_hours: int = 24,
) -> int:
    """Delete files older than max_age_hours; return the number removed."""
    target = Path(directory or settings.files_dir)
    if not target.exists():
        return 0

    cutoff = datetime.now().timestamp() - timedelta(hours=max_age_hours).total_seconds()
    deleted = 0

    for path in target.iterdir():
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
        except FileNotFoundError:
            # Another cleanup pass may have removed it already.
            continue

    return deleted