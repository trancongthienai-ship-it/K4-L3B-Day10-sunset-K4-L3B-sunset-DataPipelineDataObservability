from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
import json
from pathlib import Path
import great_expectations as gx


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    context = gx.get_context(mode="ephemeral")
    
    data_source = context.data_sources.add_pandas("pandas")
    data_asset = data_source.add_dataframe_asset("papers")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_definition")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    
    suite = context.suites.add(gx.ExpectationSuite(name="papers_suite"))
    
    suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=1))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=1))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="age_days", min_value=0, max_value=settings.freshness_threshold_days))
    
    validation_results = batch.validate(suite)
    result_dict = validation_results.to_json_dict()
    
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.paths.quality_dir / report_name
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
    return result_dict


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    latest_published = df["published"].max() if not df.empty and "published" in df else None
    oldest_published = df["published"].min() if not df.empty and "published" in df else None
    total_rows = len(df)
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if not df.empty and "age_days" in df else 0
    is_fresh = stale_rows == 0
    
    report = {
        "latest_published": str(latest_published),
        "oldest_published": str(oldest_published),
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    report_path_obj = Path(report_path)
    report_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path_obj, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report
