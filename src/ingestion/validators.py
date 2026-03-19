from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".html", ".htm"}


def validate_file_extension(filename: str) -> str | None:
    """Returns the lowercase extension if allowed, or None if rejected."""
    suffix = Path(filename).suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix
    return None
