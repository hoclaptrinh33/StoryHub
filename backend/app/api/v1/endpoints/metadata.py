from __future__ import annotations

import asyncio
import json
import re
from datetime import timedelta
from typing import Literal
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import parse_iso_datetime, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import get_cached_response, store_cached_response

router = APIRouter(prefix="/metadata", tags=["metadata"])

_GOOGLE_BOOKS_ENDPOINT = "https://www.googleapis.com/books/v1/volumes"
_EXTERNAL_TIMEOUT_SECONDS = 1.8
_METADATA_CACHE_TTL = timedelta(hours=24)
_ISBN_PATTERN = re.compile(r"^(?:\d{9}[\dX]|97[89]\d{10})$")


class MetadataDetail(BaseModel):
    name: str
    author: str
    publisher: str
    genre: str
    description: str
    cover_url: str
    confidence: float = Field(ge=0, le=1)


class MetadataAutofillRequest(BaseModel):
    query_text: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=32)
    force_refresh: bool = False
    request_id: str = Field(min_length=6, max_length=128)


class MetadataAutofillPayload(BaseModel):
    source: Literal["cache", "external_api", "fallback"]
    cache_hit: bool
    metadata: MetadataDetail


_FALLBACK_METADATA_BY_ISBN: dict[str, MetadataDetail] = {
    "9784088826001": MetadataDetail(
        name="One Piece",
        author="Eiichiro Oda",
        publisher="Nha xuat ban Kim Dong",
        genre="Truyen tranh, Phieu luu",
        description="Hai tac Mu Rom tiep tuc chinh phuc Dai Hai Trinh.",
        cover_url="",
        confidence=0.86,
    ),
    "9784088812257": MetadataDetail(
        name="Detective Conan",
        author="Gosho Aoyama",
        publisher="Nha xuat ban Tre",
        genre="Trinh tham, Truyen tranh",
        description="Vu an bi an va hanh trinh truy tim to chuc ao den.",
        cover_url="",
        confidence=0.88,
    ),
}

_FALLBACK_METADATA_BY_QUERY: dict[str, MetadataDetail] = {
    "doraemon": MetadataDetail(
        name="Doraemon",
        author="Fujiko F. Fujio",
        publisher="Nha xuat ban Kim Dong",
        genre="Thieu nhi, Truyen tranh",
        description="Meo may den tu tuong lai va nhung bao boi than ky.",
        cover_url="",
        confidence=0.92,
    ),
    "conan": MetadataDetail(
        name="Detective Conan",
        author="Gosho Aoyama",
        publisher="Nha xuat ban Tre",
        genre="Trinh tham, Truyen tranh",
        description="Vu an bi an va hanh trinh truy tim to chuc ao den.",
        cover_url="",
        confidence=0.9,
    ),
}


def _normalize_isbn(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^0-9Xx]", "", value).upper()
    return normalized


def _build_query_key(isbn: str, query_text: str) -> str:
    if isbn:
        return f"isbn:{isbn}"
    return f"query:{query_text.casefold()}"


def _normalize_text(value: object) -> str:
    return str(value or "").strip()


def _sanitize_html(text_value: str) -> str:
    return re.sub(r"<[^>]+>", " ", text_value).replace("\n", " ").strip()


def _first_non_empty(*values: object) -> str:
    for value in values:
        normalized = _normalize_text(value)
        if normalized:
            return normalized
    return ""


def _coerce_metadata(payload: dict[str, object]) -> MetadataDetail | None:
    title = _first_non_empty(payload.get("name"), payload.get("title"))
    if not title:
        return None

    author_value = payload.get("author")
    if not author_value:
        authors = payload.get("authors")
        if isinstance(authors, list):
            author_value = ", ".join(
                _normalize_text(entry) for entry in authors if _normalize_text(entry)
            )

    genre_value = payload.get("genre")
    if not genre_value:
        categories = payload.get("categories")
        if isinstance(categories, list):
            genre_value = ", ".join(
                _normalize_text(entry) for entry in categories if _normalize_text(entry)
            )

    confidence_raw = payload.get("confidence", 0.75)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.75

    confidence = max(0.0, min(1.0, confidence))

    return MetadataDetail(
        name=title,
        author=_first_non_empty(author_value, "Unknown"),
        publisher=_first_non_empty(payload.get("publisher")),
        genre=_first_non_empty(genre_value),
        description=_sanitize_html(_first_non_empty(payload.get("description"))),
        cover_url=_first_non_empty(payload.get("cover_url"), payload.get("imageLinks")),
        confidence=confidence,
    )


def _extract_external_metadata(raw_payload: dict[str, object]) -> MetadataDetail | None:
    items = raw_payload.get("items")
    if not isinstance(items, list) or not items:
        return None

    vietnamese_entry: dict[str, object] | None = None
    first_entry: dict[str, object] | None = None
    for item in items:
        if not isinstance(item, dict):
            continue
        volume_info = item.get("volumeInfo")
        if not isinstance(volume_info, dict):
            continue
        if first_entry is None:
            first_entry = volume_info
        language = _normalize_text(volume_info.get("language")).lower()
        if language == "vi" or language.startswith("vi-"):
            vietnamese_entry = volume_info
            break

    selected = vietnamese_entry or first_entry
    if selected is None:
        return None

    cover_links = selected.get("imageLinks")
    cover_url = ""
    if isinstance(cover_links, dict):
        cover_url = _first_non_empty(
            cover_links.get("extraLarge"),
            cover_links.get("large"),
            cover_links.get("medium"),
            cover_links.get("thumbnail"),
            cover_links.get("smallThumbnail"),
        )

    authors = selected.get("authors")
    author = ""
    if isinstance(authors, list):
        author = ", ".join(_normalize_text(entry) for entry in authors if _normalize_text(entry))

    categories = selected.get("categories")
    genre = ""
    if isinstance(categories, list):
        genre = ", ".join(
            _normalize_text(entry) for entry in categories if _normalize_text(entry)
        )

    metadata = {
        "name": _first_non_empty(selected.get("title")),
        "author": author,
        "publisher": _first_non_empty(selected.get("publisher")),
        "genre": genre,
        "description": _first_non_empty(selected.get("description")),
        "cover_url": cover_url,
        "confidence": 0.82,
    }
    return _coerce_metadata(metadata)


async def _fetch_external_metadata(
    *,
    isbn: str,
    query_text: str,
) -> MetadataDetail | None:
    query = f"isbn:{isbn}" if isbn else query_text
    if not query:
        return None

    params = urlencode(
        {
            "q": query,
            "printType": "books",
            "maxResults": "8",
            "langRestrict": "vi",
        }
    )
    request = Request(
        f"{_GOOGLE_BOOKS_ENDPOINT}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "StoryHub-Metadata/1.0",
        },
    )

    def _download() -> dict[str, object]:
        with urlopen(request, timeout=_EXTERNAL_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            return parsed
        return {}

    try:
        payload = await asyncio.to_thread(_download)
    except TimeoutError as exc:
        raise TimeoutError("external-timeout") from exc
    except URLError as exc:
        reason_text = str(getattr(exc, "reason", exc)).lower()
        if "timed out" in reason_text:
            raise TimeoutError("external-timeout") from exc
        return None
    except Exception:
        return None

    return _extract_external_metadata(payload)


def _lookup_fallback_metadata(*, isbn: str, query_text: str) -> MetadataDetail | None:
    if isbn:
        from_isbn = _FALLBACK_METADATA_BY_ISBN.get(isbn)
        if from_isbn is not None:
            return from_isbn

    if query_text:
        query_key = query_text.casefold().strip()
        from_query = _FALLBACK_METADATA_BY_QUERY.get(query_key)
        if from_query is not None:
            return from_query
    return None


@router.post("/autofill", response_model=ResponseEnvelope[MetadataAutofillPayload])
async def autofill_title_metadata(
    payload: MetadataAutofillRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[MetadataAutofillPayload] | dict[str, object]:
    auth.require_role("cashier", "manager", "owner")
    auth.require_scope("metadata:read")

    cached_response = await get_cached_response(
        session,
        scope="metadata.autofill",
        request_id=payload.request_id,
    )
    if cached_response is not None:
        return cached_response.payload

    if session.in_transaction():
        await session.rollback()

    query_text = (payload.query_text or "").strip()
    normalized_isbn = _normalize_isbn(payload.isbn)

    if not query_text and not normalized_isbn:
        raise AppError(
            code="INVALID_QUERY",
            message="Can cung cap query_text hoac isbn de tra metadata.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if payload.isbn and not _ISBN_PATTERN.match(normalized_isbn):
        raise AppError(
            code="INVALID_ISBN",
            message="ISBN khong hop le.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    query_key = _build_query_key(normalized_isbn, query_text)
    now = utc_now()

    if not payload.force_refresh:
        cache_result = await session.execute(
            text(
                """
                SELECT payload_json, confidence, expire_at
                FROM metadata_cache
                WHERE query_key = :query_key;
                """
            ),
            {"query_key": query_key},
        )
        cache_row = cache_result.mappings().first()
        if cache_row is not None:
            expire_at_raw = cache_row.get("expire_at")
            if expire_at_raw and parse_iso_datetime(str(expire_at_raw)) > now:
                raw_payload = cache_row.get("payload_json")
                if isinstance(raw_payload, str):
                    try:
                        parsed_payload = json.loads(raw_payload)
                    except json.JSONDecodeError:
                        parsed_payload = {}
                else:
                    parsed_payload = {}

                metadata = _coerce_metadata(parsed_payload)
                if metadata is not None:
                    envelope = success_response(
                        MetadataAutofillPayload(
                            source="cache",
                            cache_hit=True,
                            metadata=metadata,
                        )
                    )
                    try:
                        if session.in_transaction():
                            await session.rollback()
                        async with session.begin():
                            await store_cached_response(
                                session,
                                scope="metadata.autofill",
                                request_id=payload.request_id,
                                status_code=status.HTTP_200_OK,
                                payload=envelope.model_dump(),
                            )
                    except IntegrityError:
                        await session.rollback()
                        replay = await get_cached_response(
                            session,
                            scope="metadata.autofill",
                            request_id=payload.request_id,
                        )
                        if replay is not None:
                            return replay.payload
                        raise
                    return envelope

    source: Literal["external_api", "fallback"] = "fallback"
    metadata: MetadataDetail | None = None

    try:
        metadata = await _fetch_external_metadata(isbn=normalized_isbn, query_text=query_text)
        if metadata is not None:
            source = "external_api"
    except TimeoutError as exc:
        metadata = _lookup_fallback_metadata(isbn=normalized_isbn, query_text=query_text)
        if metadata is None:
            raise AppError(
                code="EXTERNAL_API_TIMEOUT",
                message="Nguon metadata ben ngoai phan hoi qua cham.",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc

    if metadata is None:
        metadata = _lookup_fallback_metadata(isbn=normalized_isbn, query_text=query_text)

    if metadata is None:
        raise AppError(
            code="METADATA_NOT_FOUND",
            message="Khong tim thay metadata phu hop.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    cache_payload = {
        "name": metadata.name,
        "author": metadata.author,
        "publisher": metadata.publisher,
        "genre": metadata.genre,
        "description": metadata.description,
        "cover_url": metadata.cover_url,
        "confidence": metadata.confidence,
    }
    now_iso = to_iso_z(now)
    expire_at_iso = to_iso_z(now + _METADATA_CACHE_TTL)

    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        await session.execute(
            text(
                """
                INSERT INTO metadata_cache (
                    query_key,
                    source,
                    payload_json,
                    confidence,
                    cached_at,
                    expire_at
                )
                VALUES (
                    :query_key,
                    :source,
                    :payload_json,
                    :confidence,
                    :cached_at,
                    :expire_at
                )
                ON CONFLICT(query_key)
                DO UPDATE SET
                    source = excluded.source,
                    payload_json = excluded.payload_json,
                    confidence = excluded.confidence,
                    cached_at = excluded.cached_at,
                    expire_at = excluded.expire_at;
                """
            ),
            {
                "query_key": query_key,
                "source": source,
                "payload_json": json.dumps(cache_payload, ensure_ascii=True),
                "confidence": metadata.confidence,
                "cached_at": now_iso,
                "expire_at": expire_at_iso,
            },
        )

        if normalized_isbn and query_key != f"isbn:{normalized_isbn}":
            await session.execute(
                text(
                    """
                    INSERT INTO metadata_cache (
                        query_key,
                        source,
                        payload_json,
                        confidence,
                        cached_at,
                        expire_at
                    )
                    VALUES (
                        :query_key,
                        :source,
                        :payload_json,
                        :confidence,
                        :cached_at,
                        :expire_at
                    )
                    ON CONFLICT(query_key)
                    DO UPDATE SET
                        source = excluded.source,
                        payload_json = excluded.payload_json,
                        confidence = excluded.confidence,
                        cached_at = excluded.cached_at,
                        expire_at = excluded.expire_at;
                    """
                ),
                {
                    "query_key": f"isbn:{normalized_isbn}",
                    "source": source,
                    "payload_json": json.dumps(cache_payload, ensure_ascii=True),
                    "confidence": metadata.confidence,
                    "cached_at": now_iso,
                    "expire_at": expire_at_iso,
                },
            )

    envelope = success_response(
        MetadataAutofillPayload(
            source=source,
            cache_hit=False,
            metadata=metadata,
        )
    )

    try:
        if session.in_transaction():
            await session.rollback()
        async with session.begin():
            await store_cached_response(
                session,
                scope="metadata.autofill",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        replay = await get_cached_response(
            session,
            scope="metadata.autofill",
            request_id=payload.request_id,
        )
        if replay is not None:
            return replay.payload
        raise

    return envelope
