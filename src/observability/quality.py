from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


def evaluate_freshness_sla(
    df: pd.DataFrame,
    settings: Settings,
    max_stale_ratio: float = 0.25,
) -> dict[str, Any]:
    """Evaluate the lab SLA: at most 25% of rows may be older than the threshold."""
    total_rows = int(len(df))
    if "age_days" not in df.columns or total_rows == 0:
        return {
            "success": False,
            "is_fresh": False,
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio": max_stale_ratio,
            "stale_rows": 0,
            "total_rows": total_rows,
            "stale_ratio": 0.0,
            "reason": "age_days is missing or the dataframe is empty.",
        }

    ages = pd.to_numeric(df["age_days"], errors="coerce")
    invalid_age_rows = int(ages.isna().sum())
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows
    is_fresh = invalid_age_rows == 0 and stale_ratio <= max_stale_ratio
    return {
        "success": bool(is_fresh),
        "is_fresh": bool(is_fresh),
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": max_stale_ratio,
        "stale_rows": stale_rows,
        "invalid_age_rows": invalid_age_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 6),
        "reason": (
            "Freshness SLA passed."
            if is_fresh
            else "Freshness SLA failed because age_days is invalid or the stale ratio exceeds 25%."
        ),
    }


def _quality_report_path(settings: Settings, stage: str) -> Path:
    normalized_stage = stage.strip().lower()
    if normalized_stage == "baseline":
        return settings.paths.baseline_quality_report
    if normalized_stage == "corrupted":
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / f"{safe_slug(stage)}_quality_report.json"


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, stage: str) -> dict[str, Any]:
    """Run the four required GX 1.x quality gates plus the freshness SLA."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    # There are four required expectation types. The not-null requirement covers
    # all three contract columns and is therefore validated once per column.
    expectations = [
        gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    validation_results: list[dict[str, Any]] = []
    for expectation in expectations:
        validation = batch.validate(expectation)
        serialized = validation.to_json_dict()
        validation_results.append(
            {
                "expectation_type": expectation.__class__.__name__,
                "column": getattr(expectation, "column", None),
                "success": bool(validation.success),
                "result": serialized.get("result", {}),
            }
        )

    gx_success = all(item["success"] for item in validation_results)
    freshness = evaluate_freshness_sla(df, settings)
    payload = {
        "stage": stage,
        "success": bool(gx_success and freshness["success"]),
        "gx_success": bool(gx_success),
        "freshness_success": bool(freshness["success"]),
        "row_count": int(len(df)),
        "expectation_results": validation_results,
        "freshness": freshness,
    }
    write_json(_quality_report_path(settings, stage), payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist the standalone freshness artifact used by reports."""
    freshness = evaluate_freshness_sla(df, settings)
    published = pd.to_datetime(df.get("published"), errors="coerce", utc=True)
    valid_published = published.dropna()
    payload = {
        **freshness,
        "latest_published": (
            valid_published.max().date().isoformat() if not valid_published.empty else None
        ),
        "oldest_published": (
            valid_published.min().date().isoformat() if not valid_published.empty else None
        ),
    }
    write_json(Path(report_path), payload)
    return payload
