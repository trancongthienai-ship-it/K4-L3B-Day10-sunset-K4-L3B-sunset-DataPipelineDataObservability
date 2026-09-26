from __future__ import annotations

from dataclasses import replace
import json

import requests

from core.config import load_settings
from ingestion.crossref import fetch_source_records, parse_crossref_payload


def _payload() -> dict:
    return {
        "status": "ok",
        "message": {
            "items": [
                {
                    "DOI": " 10.1000/example ",
                    "title": ["  Data   <i>Quality</i>  "],
                    "abstract": "<jats:p>Reliable &amp; observable <b>data</b>.</jats:p>",
                    "author": [
                        {"given": "Ada", "family": "Lovelace"},
                        {"name": "Data Consortium"},
                    ],
                    "subject": ["Data Science", "Observability"],
                    "published": {"date-parts": [[2026, 9, 7]]},
                    "created": {"date-time": "2026-09-08T10:30:00Z"},
                    "URL": "https://doi.org/10.1000/example",
                    "link": [
                        {
                            "URL": "https://example.org/paper.pdf",
                            "content-type": "application/pdf",
                        }
                    ],
                },
                {
                    "DOI": "10.1000/missing-summary",
                    "title": ["Incomplete record"],
                },
            ]
        },
    }


def test_parse_crossref_payload_normalizes_fields_and_skips_incomplete_records() -> None:
    records = parse_crossref_payload(_payload())

    assert len(records) == 1
    assert records[0].paper_id == "10.1000/example"
    assert records[0].title == "Data Quality"
    assert records[0].summary == "Reliable & observable data."
    assert records[0].authors == ["Ada Lovelace", "Data Consortium"]
    assert records[0].categories == ["Data Science", "Observability"]
    assert records[0].primary_category == "Data Science"
    assert records[0].published == "2026-09-07"
    assert records[0].updated == "2026-09-08"
    assert records[0].abs_url == "https://doi.org/10.1000/example"
    assert records[0].pdf_url == "https://example.org/paper.pdf"


def test_fetch_source_records_falls_back_to_snapshot_and_writes_records(tmp_path, monkeypatch) -> None:
    settings = replace(load_settings(tmp_path), refresh_source=True)
    settings.paths.raw_api_response.parent.mkdir(parents=True)
    settings.paths.raw_api_response.write_text(json.dumps(_payload()), encoding="utf-8")

    attempts = 0

    def fail_request(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("ingestion.crossref.requests.get", fail_request)

    records = fetch_source_records(settings)

    assert attempts == 3
    assert len(records) == 1
    stored = json.loads(settings.paths.raw_records_json.read_text(encoding="utf-8"))
    assert stored[0]["paper_id"] == "10.1000/example"
    assert json.loads(settings.paths.raw_api_response.read_text(encoding="utf-8")) == _payload()


def test_fetch_source_records_uses_existing_snapshot_without_network(tmp_path, monkeypatch) -> None:
    settings = load_settings(tmp_path)
    settings.paths.raw_api_response.parent.mkdir(parents=True)
    settings.paths.raw_api_response.write_text(json.dumps(_payload()), encoding="utf-8")

    def unexpected_request(*args, **kwargs):
        raise AssertionError("network must not be used when refresh_source is false")

    monkeypatch.setattr("ingestion.crossref.requests.get", unexpected_request)

    records = fetch_source_records(settings)

    assert len(records) == 1
    assert settings.paths.raw_records_json.exists()
