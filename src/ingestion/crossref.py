from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import html
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _first_text(value: Any) -> str:
    """Return the first non-empty text value used by Crossref list fields."""
    if isinstance(value, list):
        value = value[0] if value else ""
    return normalize_whitespace(str(value or ""))


def _clean_markup(value: Any) -> str:
    """Remove JATS/HTML markup while preserving readable abstract text."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def _crossref_date(value: Any) -> str:
    """Convert a Crossref date object to an ISO date without inventing parts."""
    if not isinstance(value, dict):
        return ""
    parts_container = value.get("date-parts")
    if not isinstance(parts_container, list) or not parts_container:
        return ""
    parts = parts_container[0]
    if not isinstance(parts, list) or not parts:
        return ""
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return date(year, month, day).isoformat()
    except (TypeError, ValueError):
        return ""


def _updated_date(item: dict[str, Any], published: str) -> str:
    for field in ("updated", "indexed", "deposited", "created"):
        value = item.get(field)
        if isinstance(value, dict):
            date_time = value.get("date-time")
            if date_time:
                return str(date_time)
            parsed = _crossref_date(value)
            if parsed:
                return parsed
    return published


def _pdf_url(item: dict[str, Any]) -> str:
    links = item.get("link") or []
    if not isinstance(links, list):
        return ""
    for link in links:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type", "")).lower()
        url = str(link.get("URL", ""))
        if url and ("pdf" in content_type or url.lower().endswith(".pdf")):
            return url
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref API payload into normalized ``PaperRecord`` objects."""
    if not isinstance(payload, dict):
        raise ValueError("Crossref payload must be a JSON object.")
    message = payload.get("message")
    items = message.get("items") if isinstance(message, dict) else None
    if not isinstance(items, list):
        raise ValueError("Invalid Crossref payload: message.items must be a list.")

    records: list[PaperRecord] = []
    seen_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = _first_text(item.get("DOI")).lower()
        title = _first_text(item.get("title"))
        if not paper_id or not title or paper_id in seen_ids:
            continue

        authors: list[str] = []
        for author in item.get("author") or []:
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(
                " ".join(part for part in (str(author.get("given", "")), str(author.get("family", ""))) if part)
            )
            if name:
                authors.append(name)

        categories = [
            normalize_whitespace(str(subject))
            for subject in (item.get("subject") or [])
            if normalize_whitespace(str(subject))
        ]
        published = _crossref_date(
            item.get("published") or item.get("published-print") or item.get("published-online")
        )
        abs_url = _first_text(item.get("URL")) or f"https://doi.org/{paper_id}"
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_clean_markup(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=_updated_date(item, published),
                abs_url=abs_url,
                pdf_url=_pdf_url(item),
                comment=_first_text(item.get("note") or item.get("subtitle")),
            )
        )
        seen_ids.add(paper_id)
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref records and fall back safely to the bundled raw snapshot.

    The existing snapshot is never overwritten unless a complete API response has
    been downloaded and parsed successfully, so it remains a recovery anchor.
    """
    raw_response_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    if not settings.refresh_source:
        if raw_records_path.exists():
            return load_raw_records(raw_records_path)
        if raw_response_path.exists():
            records = parse_crossref_payload(read_json(raw_response_path))
            write_json(raw_records_path, [asdict(record) for record in records])
            return records

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,created,indexed,deposited,URL,link,subtitle",
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "VinUni-Day10-DataObservability-Lab/1.0 (educational use)",
    }
    last_error: Exception | None = None
    payload: dict[str, Any] | None = None

    for attempt in range(3):
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params=params,
                headers=headers,
                timeout=30,
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                raise requests.HTTPError(f"Crossref returned retryable status {response.status_code}")
            response.raise_for_status()
            candidate = response.json()
            records = parse_crossref_payload(candidate)
            if not records:
                raise ValueError("Crossref returned no usable records.")
            payload = candidate
            break
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)

    if payload is None:
        if not raw_response_path.exists():
            raise RuntimeError("Crossref fetch failed and no local snapshot is available.") from last_error
        payload = read_json(raw_response_path)
        records = parse_crossref_payload(payload)
    else:
        write_json(raw_response_path, payload)

    write_json(raw_records_path, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the normalized raw-record artifact into typed objects."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Raw records file must contain a JSON list: {path}")

    records: list[PaperRecord] = []
    field_names = set(PaperRecord.__dataclass_fields__)
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Raw record at index {index} is not a JSON object.")
        missing = field_names - set(item)
        if missing:
            raise ValueError(f"Raw record at index {index} is missing fields: {sorted(missing)}")
        records.append(PaperRecord(**{name: item[name] for name in field_names}))
    return records
