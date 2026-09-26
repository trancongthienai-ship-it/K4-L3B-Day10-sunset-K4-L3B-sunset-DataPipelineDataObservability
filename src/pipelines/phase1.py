from __future__ import annotations

from typing import Any

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings) -> dict[str, Any]:
    """Run ingestion through baseline evaluation and persist every artifact."""
    run_at = now_utc()

    # 1. Ingest from cache/API with offline fallback and preserve raw lineage.
    raw_records = fetch_source_records(settings)
    if not raw_records:
        raise RuntimeError("Ingestion returned no Crossref records.")

    # 2. Clean and persist the canonical pre-embedding dataset.
    clean_df = build_clean_dataframe(raw_records, run_at)
    if clean_df.empty:
        raise RuntimeError("Cleaning removed every source record.")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    # 3. Build the baseline ChromaDB index and its document manifest.
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    # 4. Keep a stable benchmark across runs unless regeneration is requested.
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(settings.paths.eval_testset)
    else:
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
    if not isinstance(test_set, list) or len(test_set) != 10:
        raise RuntimeError("The evaluation set must contain exactly 10 questions.")

    # 5. Evaluate retrieval hit rate, token F1, and the configured judge.
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 6. Run the GX gate and freshness SLA, then report the observed results.
    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    source_summary = {
        "run_at": run_at.isoformat(),
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(raw_records),
        "clean_records": len(clean_df),
        "collection_name": index.collection_name,
        "evaluation_questions": len(test_set),
        "artifacts": [
            str(settings.paths.raw_api_response),
            str(settings.paths.raw_records_json),
            str(settings.paths.clean_csv),
            str(settings.paths.clean_json),
            str(settings.paths.embeddings_json),
            str(settings.paths.eval_testset),
            str(settings.paths.baseline_metrics),
            str(settings.paths.baseline_answers),
            str(settings.paths.baseline_quality_report),
            str(settings.paths.freshness_report),
        ],
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    result = {
        "success": bool(quality["success"]),
        "source_summary": source_summary,
        "metrics": evaluation.summary,
        "quality": quality,
        "freshness": freshness,
        "report_path": str(settings.paths.baseline_report),
    }
    if not quality["success"]:
        raise RuntimeError(
            f"Baseline artifacts and report were generated, but the quality gate failed: "
            f"{settings.paths.baseline_quality_report}"
        )
    return result


def main() -> None:
    """CLI entry point for the complete baseline pipeline."""
    result = run_phase1_pipeline(load_settings())
    metrics = result["metrics"]
    print("Phase 1 pipeline completed successfully.")
    print(f"Retrieval hit rate: {metrics['retrieval_hit_rate']:.4f}")
    print(f"Mean token F1: {metrics['mean_token_f1']:.4f}")
    print(f"Report: {result['report_path']}")
