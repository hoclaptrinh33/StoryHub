from __future__ import annotations

import base64
import binascii
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024

_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def resolve_runtime_root() -> Path:
    """
    Resolve runtime root so storage lives next to executable/runtime folder.

    Priority:
    1) STORYHUB_RUNTIME_ROOT env
    2) frozen executable directory
    3) project root when cwd is backend
    4) current working directory
    """
    runtime_override = os.getenv("STORYHUB_RUNTIME_ROOT", "").strip()
    if runtime_override:
        return Path(runtime_override).expanduser().resolve()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    cwd = Path.cwd().resolve()
    if cwd.name.lower() == "backend":
        return cwd.parent
    return cwd


def get_storage_root() -> Path:
    storage_root = resolve_runtime_root() / "storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root


def ensure_storage_tree() -> Path:
    covers_dir = get_storage_root() / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)
    return covers_dir


def is_remote_image_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme.lower() in {"http", "https"}


def save_cover_from_url(isbn: str, image_url: str) -> str:
    normalized_url = image_url.strip()
    if not normalized_url:
        raise ValueError("Link anh khong duoc de trong.")
    if not is_remote_image_url(normalized_url):
        raise ValueError("Link anh phai bat dau bang http:// hoac https://.")

    request = Request(
        normalized_url,
        headers={
            "User-Agent": "StoryHub-CoverFetcher/1.0",
            "Accept": "image/*",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            content_type = (
                str(response.headers.get("Content-Type", ""))
                .split(";")[0]
                .strip()
                .lower()
            )
            raw_bytes = response.read(MAX_IMAGE_SIZE_BYTES + 1)
    except HTTPError as exc:
        raise ValueError(f"Khong tai duoc anh (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise ValueError("Khong the ket noi den link anh.") from exc
    except TimeoutError as exc:
        raise ValueError("Het thoi gian tai anh tu link.") from exc

    if len(raw_bytes) == 0:
        raise ValueError("Anh tai ve rong hoac khong hop le.")
    if len(raw_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Anh qua lon. Gioi han toi da 8MB.")

    extension = _detect_extension(
        content_type=content_type,
        source_url=normalized_url,
        image_bytes=raw_bytes,
    )
    return _write_cover_file(isbn=isbn, image_bytes=raw_bytes, extension=extension)


def save_cover_from_base64(isbn: str, image_base64: str) -> str:
    payload = (image_base64 or "").strip()
    if not payload:
        raise ValueError("Du lieu anh khong duoc de trong.")

    content_type = ""
    data_part = payload
    if payload.startswith("data:"):
        if "," not in payload:
            raise ValueError("Du lieu anh base64 khong hop le.")
        header, data_part = payload.split(",", 1)
        content_type = header[5:].split(";", 1)[0].strip().lower()
        if ";base64" not in header.lower():
            raise ValueError("Chi ho tro data URL base64.")

    try:
        raw_bytes = base64.b64decode(data_part, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Du lieu base64 cua anh khong hop le.") from exc

    if len(raw_bytes) == 0:
        raise ValueError("Anh tai len rong hoac khong hop le.")
    if len(raw_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Anh qua lon. Gioi han toi da 8MB.")

    extension = _detect_extension(
        content_type=content_type,
        source_url=None,
        image_bytes=raw_bytes,
    )
    return _write_cover_file(isbn=isbn, image_bytes=raw_bytes, extension=extension)


def _normalize_isbn_for_filename(isbn: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]", "", (isbn or "")).upper()
    if len(normalized) < 5:
        raise ValueError("ISBN khong hop le de dat ten file anh.")
    return normalized


def _detect_extension(content_type: str, source_url: str | None, image_bytes: bytes) -> str:
    if content_type in _CONTENT_TYPE_TO_EXT:
        return _CONTENT_TYPE_TO_EXT[content_type]

    if source_url:
        parsed = urlparse(source_url)
        suffix = Path(parsed.path).suffix.lower().lstrip(".")
        if suffix in _ALLOWED_EXTENSIONS:
            return "jpg" if suffix == "jpeg" else suffix

    sniffed = _sniff_extension(image_bytes)
    if sniffed:
        return sniffed

    raise ValueError("Khong xac dinh duoc dinh dang anh hop le.")


def _sniff_extension(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return "gif"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "webp"
    return None


def _write_cover_file(isbn: str, image_bytes: bytes, extension: str) -> str:
    normalized_isbn = _normalize_isbn_for_filename(isbn)
    covers_dir = ensure_storage_tree()

    # Keep only one active file per ISBN regardless of extension.
    for existing_file in covers_dir.glob(f"{normalized_isbn}.*"):
        if existing_file.is_file():
            existing_file.unlink(missing_ok=True)

    normalized_ext = "jpg" if extension.lower() == "jpeg" else extension.lower()
    if normalized_ext not in {"jpg", "png", "webp", "gif"}:
        raise ValueError("Dinh dang anh khong duoc ho tro.")

    target_file = covers_dir / f"{normalized_isbn}.{normalized_ext}"
    temp_file = covers_dir / f"{target_file.name}.tmp"
    temp_file.write_bytes(image_bytes)
    temp_file.replace(target_file)

    return f"/storage/covers/{target_file.name}"