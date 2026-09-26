from __future__ import annotations


import json
from datetime import datetime, UTC
import pandas as pd

from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report
from core.utils import read_json

def main() -> None:
    settings = load_settings()
    
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    df_clean = pd.read_json(settings.paths.clean_json)
    
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    df_corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)
    
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    bundle_corrupted = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )
    
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, settings.paths.corrupted_quality_report.name)
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(df_corrupted, settings, corrupted_freshness_path)
    
    records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(records, datetime.now(UTC))
    
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    df_repaired.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)
    
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    
    bundle_repaired = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )
    
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired_quality_report.json")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(df_repaired, settings, repaired_freshness_path)
    
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=bundle_corrupted.summary,
        repaired_metrics=bundle_repaired.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness
    )
