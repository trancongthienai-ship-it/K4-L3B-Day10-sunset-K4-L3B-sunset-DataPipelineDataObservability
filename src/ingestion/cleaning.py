from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import html
import re

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def _clean_text(value: object) -> str:
    """Normalize whitespace and remove any JATS/HTML tags left in raw text."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def _clean_string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _clean_text(item)
        key = text.casefold()
        if text and key not in seen:
            cleaned.append(text)
            seen.add(key)
    return cleaned


def build_clean_dataframe(raw_records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Transform raw Crossref records into a deterministic pre-embedding table.

    Invalid rows without a paper ID, title, summary, or publication date are
    removed. Duplicate IDs keep the first normalized occurrence.
    """
    columns = [
        "paper_id",
        "title",
        "summary",
        "authors",
        "categories",
        "primary_category",
        "published",
        "updated",
        "abs_url",
        "pdf_url",
        "comment",
        "authors_joined",
        "categories_joined",
        "summary_chars",
        "age_days",
        "text_for_embedding",
    ]
    if not raw_records:
        return pd.DataFrame(columns=columns)

    normalized_rows: list[dict[str, object]] = []
    for record in raw_records:
        if not isinstance(record, PaperRecord):
            raise TypeError("raw_records must contain only PaperRecord objects.")

        row = asdict(record)
        row["paper_id"] = _clean_text(record.paper_id).lower()
        row["title"] = _clean_text(record.title)
        row["summary"] = _clean_text(record.summary)
        row["authors"] = _clean_string_list(record.authors)
        row["categories"] = _clean_string_list(record.categories)
        row["primary_category"] = _clean_text(record.primary_category)
        row["abs_url"] = _clean_text(record.abs_url)
        row["pdf_url"] = _clean_text(record.pdf_url)
        row["comment"] = _clean_text(record.comment)
        normalized_rows.append(row)

    df = pd.DataFrame(normalized_rows)
    df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["updated_parsed"] = pd.to_datetime(df["updated"], errors="coerce", utc=True)

    # These fields are the minimum contract required for retrieval and evaluation.
    valid = (
        df["paper_id"].ne("")
        & df["title"].ne("")
        & df["summary"].ne("")
        & df["published_parsed"].notna()
    )
    df = df.loc[valid].copy()
    df = df.drop_duplicates(subset="paper_id", keep="first")

    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")

    df["published"] = df["published_parsed"].dt.strftime("%Y-%m-%d")
    df["updated"] = df["updated_parsed"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["updated"] = df["updated"].fillna(df["published"])
    df["age_days"] = (run_timestamp.normalize() - df["published_parsed"].dt.normalize()).dt.days.astype(int)
    df["authors_joined"] = df["authors"].apply(lambda values: ", ".join(values) or "Unknown")
    df["categories_joined"] = df["categories"].apply(
        lambda values: ", ".join(values) or "Uncategorized"
    )
    df["primary_category"] = df.apply(
        lambda row: row["primary_category"]
        or (row["categories"][0] if row["categories"] else "Uncategorized"),
        axis=1,
    )
    df["summary_chars"] = df["summary"].str.len().astype(int)

    # Five labeled sections make embeddings consistent and retain useful metadata.
    df["text_for_embedding"] = df.apply(
        lambda row: "\n".join(
            [
                f"Title: {row['title']}",
                f"Summary: {row['summary']}",
                f"Authors: {row['authors_joined']}",
                f"Categories: {row['categories_joined']}",
                f"Published: {row['published']}",
            ]
        ),
        axis=1,
    )

    df = df.sort_values(["published_parsed", "paper_id"], ascending=[False, True])
    return df.loc[:, columns].reset_index(drop=True)
