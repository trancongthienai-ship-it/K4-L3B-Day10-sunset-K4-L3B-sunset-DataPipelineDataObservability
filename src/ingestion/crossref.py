from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html import unescape
from pathlib import Path
import re
import time

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


_CROSSREF_WORKS_URL = "https://api.crossref.org/works"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(value: str) -> str:
    text = normalize_whitespace(unescape(_TAG_RE.sub(" ", value)))
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def _date_from_parts(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts", [[]])
    if not parts or not parts[0]:
        return ""
    year, month, day = (list(parts[0]) + [1, 1])[:3]
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError):
        return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref works response into normalized paper records."""
    records: list[PaperRecord] = []
    message = payload.get("message", {})
    items = message.get("items", []) if isinstance(message, dict) else []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue

        paper_id = normalize_whitespace(str(item.get("DOI", "")))
        titles = item.get("title") or []
        title = _clean_text(str(titles[0])) if isinstance(titles, list) and titles else ""
        summary = _clean_text(str(item.get("abstract", "")))
        if not paper_id or not title or not summary:
            continue

        authors = []
        for author in item.get("author") or []:
            if not isinstance(author, dict):
                continue
            name = author.get("name") or " ".join(
                part for part in (author.get("given"), author.get("family")) if part
            )
            if name := normalize_whitespace(str(name)):
                authors.append(name)

        categories = [
            value
            for subject in (item.get("subject") or [])
            if (value := normalize_whitespace(str(subject)))
        ]
        published = _date_from_parts(item.get("published") or item.get("issued"))
        updated_value = item.get("created", {})
        updated = ""
        if isinstance(updated_value, dict):
            updated = str(updated_value.get("date-time", ""))[:10]
        updated = updated or published
        abs_url = normalize_whitespace(str(item.get("URL", ""))) or f"https://doi.org/{paper_id}"
        pdf_url = abs_url
        for link in item.get("link") or []:
            if isinstance(link, dict) and link.get("content-type") == "application/pdf" and link.get("URL"):
                pdf_url = normalize_whitespace(str(link["URL"]))
                break

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref data, falling back to the preserved local snapshot."""
    snapshot = settings.paths.raw_api_response
    payload = None
    if settings.refresh_source or not snapshot.exists():
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {"User-Agent": "DataPipelineDataObservability/1.0 (educational lab)"}
        for attempt in range(3):
            try:
                response = requests.get(_CROSSREF_WORKS_URL, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                payload = response.json()
                write_json(snapshot, payload)
                break
            except (requests.RequestException, ValueError):
                if attempt < 2:
                    time.sleep(2**attempt)

    if payload is None:
        if not snapshot.exists():
            raise RuntimeError("Crossref API failed and no local snapshot is available.")
        payload = read_json(snapshot)

    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("Crossref payload contains no valid records.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load preserved normalized records from JSON."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {path}.")
    return [PaperRecord(**item) for item in payload]
