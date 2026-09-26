from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import run_phase1_pipeline
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(
    settings: Settings,
    run_date: datetime | None = None,
) -> pd.DataFrame:
    """Rebuild the canonical dataset only from the immutable raw snapshot."""
    if not settings.paths.raw_records_json.exists():
        raise FileNotFoundError(
            f"Cannot repair without the trusted raw snapshot: {settings.paths.raw_records_json}"
        )
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date or now_utc())
    if repaired_df.empty:
        raise RuntimeError("Repair produced an empty dataframe.")
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    return repaired_df


def _ensure_baseline(settings: Settings) -> None:
    required = (
        settings.paths.clean_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
    )
    if not all(path.exists() for path in required):
        run_phase1_pipeline(settings)


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Evaluate corrupted data, repair from raw lineage, and compare all states."""
    _ensure_baseline(settings)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_df = pd.read_json(settings.paths.clean_json)

    # 1. Corrupt, persist, index, and evaluate with the unchanged benchmark.
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, corrupted_freshness_path
    )

    # 2. Repair from trusted raw data; never patch or reuse the corrupted frame.
    repair_run_date = now_utc()
    repaired_df = repair_from_raw_snapshot(settings, repair_run_date)
    idempotency_check = build_clean_dataframe(
        load_raw_records(settings.paths.raw_records_json), repair_run_date
    )
    repair_idempotent = repaired_df.equals(idempotency_check)
    if not repair_idempotent:
        raise RuntimeError("Repair is not idempotent for the same raw snapshot and run date.")

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)

    # 3. Produce the evidence-backed three-state comparison.
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_evaluation.summary,
        repaired_metrics=repaired_evaluation.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    return {
        "success": bool(repaired_quality["success"] and repair_idempotent),
        "repair_idempotent": repair_idempotent,
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_evaluation.summary,
        "repaired_metrics": repaired_evaluation.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_freshness": corrupted_freshness,
        "repaired_freshness": repaired_freshness,
        "report_path": str(settings.paths.comparison_report),
    }


def main() -> None:
    """CLI entry point for the corruption and recovery experiment."""
    result = run_corruption_flow_pipeline(load_settings())
    print("Phase 2 corruption and repair flow completed.")
    print("Metric                 Baseline   Corrupted   Repaired")
    for metric in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        print(
            f"{metric:<22}"
            f"{float(result['baseline_metrics'].get(metric, 0)):<11.4f}"
            f"{float(result['corrupted_metrics'].get(metric, 0)):<12.4f}"
            f"{float(result['repaired_metrics'].get(metric, 0)):.4f}"
        )
    print(f"Repair idempotent: {result['repair_idempotent']}")
    print(f"Report: {result['report_path']}")
