from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def _rebuild_text_for_embedding(df: pd.DataFrame) -> None:
    """Rebuild fields derived from values intentionally changed by corruption."""
    df["summary"] = df["summary"].fillna("").astype(str)
    df["summary_chars"] = df["summary"].str.len().astype(int)
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


def _operation(
    corruption_type: str,
    paper_ids: list[str],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "corruption_type": corruption_type,
        "affected_count": len(paper_ids),
        "paper_ids": paper_ids,
        "parameters": parameters,
    }


def corrupt_clean_dataframe(clean_df: pd.DataFrame, log_path) -> pd.DataFrame:
    """Inject six deterministic data failures and persist a complete audit log."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "categories_joined",
        "published",
        "age_days",
        "text_for_embedding",
    }
    missing_columns = required_columns - set(clean_df.columns)
    if missing_columns:
        raise ValueError(f"Clean dataframe is missing columns: {sorted(missing_columns)}")
    if len(clean_df) < 10:
        raise ValueError("At least 10 clean rows are required for the corruption suite.")

    corrupted = clean_df.copy(deep=True)
    corrupted["published"] = pd.to_datetime(corrupted["published"], errors="coerce", utc=True)
    if corrupted["published"].isna().any():
        raise ValueError("All published values must be valid before corruption.")

    operations: list[dict[str, Any]] = []

    # 1. Remove ceil(20%) of the newest records.
    drop_count = max(1, math.ceil(len(corrupted) * 0.20))
    latest_indices = corrupted.nlargest(drop_count, "published").index.tolist()
    dropped_ids = corrupted.loc[latest_indices, "paper_id"].astype(str).tolist()
    corrupted = corrupted.drop(index=latest_indices).reset_index(drop=True)
    operations.append(
        _operation(
            "drop_latest_records",
            dropped_ids,
            {"fraction": 0.20, "rounding": "ceil", "dropped_rows": drop_count},
        )
    )

    # Use disjoint deterministic rows so every non-drop failure is observable.
    rows_per_mutation = max(1, min(2, len(corrupted) // 8))
    mutation_indices = {
        "blank_summary": list(range(0, rows_per_mutation)),
        "inject_noise": list(range(rows_per_mutation, rows_per_mutation * 2)),
        "truncate_title": list(range(rows_per_mutation * 2, rows_per_mutation * 3)),
        "stale_date": list(range(rows_per_mutation * 3, rows_per_mutation * 4)),
        "duplicate_rows": list(range(rows_per_mutation * 4, rows_per_mutation * 5)),
    }

    # 2. Blank summaries.
    indices = mutation_indices["blank_summary"]
    paper_ids = corrupted.loc[indices, "paper_id"].astype(str).tolist()
    corrupted.loc[indices, "summary"] = ""
    operations.append(_operation("blank_summary", paper_ids, {"replacement": ""}))

    # 3. Inject an unmistakable noise sequence into summaries.
    indices = mutation_indices["inject_noise"]
    paper_ids = corrupted.loc[indices, "paper_id"].astype(str).tolist()
    noise = " [CORRUPTED_NOISE] ###@@@ 0000 lorem-noise-token"
    corrupted.loc[indices, "summary"] = corrupted.loc[indices, "summary"].astype(str) + noise
    operations.append(_operation("inject_noise", paper_ids, {"noise": noise.strip()}))

    # 4. Truncate titles to seven characters (strictly below eight).
    indices = mutation_indices["truncate_title"]
    paper_ids = corrupted.loc[indices, "paper_id"].astype(str).tolist()
    corrupted.loc[indices, "title"] = corrupted.loc[indices, "title"].astype(str).str.slice(0, 7)
    operations.append(_operation("truncate_title", paper_ids, {"max_characters": 7}))

    # 5. Move publication dates back by exactly one year and update age_days.
    indices = mutation_indices["stale_date"]
    paper_ids = corrupted.loc[indices, "paper_id"].astype(str).tolist()
    corrupted.loc[indices, "published"] = corrupted.loc[indices, "published"] - pd.Timedelta(days=365)
    ages = pd.to_numeric(corrupted.loc[indices, "age_days"], errors="coerce").fillna(0)
    corrupted.loc[indices, "age_days"] = ages + 365
    operations.append(_operation("stale_date", paper_ids, {"days_shifted_back": 365}))

    corrupted["published"] = corrupted["published"].dt.strftime("%Y-%m-%d")
    _rebuild_text_for_embedding(corrupted)

    # 6. Append exact duplicates last so the uniqueness gate can detect them.
    indices = mutation_indices["duplicate_rows"]
    duplicate_frame = corrupted.loc[indices].copy(deep=True)
    duplicate_ids = duplicate_frame["paper_id"].astype(str).tolist()
    corrupted = pd.concat([corrupted, duplicate_frame], ignore_index=True)
    operations.append(
        _operation("duplicate_rows", duplicate_ids, {"copies_added": len(duplicate_frame)})
    )

    log_payload = {
        "source_rows": int(len(clean_df)),
        "corrupted_rows": int(len(corrupted)),
        "net_row_change": int(len(corrupted) - len(clean_df)),
        "operation_count": len(operations),
        "operations": operations,
    }
    write_json(Path(log_path), log_payload)
    return corrupted.reset_index(drop=True)
