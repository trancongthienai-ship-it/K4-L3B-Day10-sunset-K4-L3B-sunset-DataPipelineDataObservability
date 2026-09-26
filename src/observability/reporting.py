from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _format_metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the reproducible baseline pipeline report from real artifacts."""
    expectation_rows = []
    for item in quality.get("expectation_results", []):
        expectation_rows.append(
            f"| {item.get('expectation_type', '')} | {item.get('column') or '-'} "
            f"| {'PASS' if item.get('success') else 'FAIL'} |"
        )
    if not expectation_rows:
        expectation_rows.append("| No validation results | - | FAIL |")

    metric_names = (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    metric_rows = [
        f"| `{name}` | {_format_metric(metrics.get(name, 'N/A'))} |" for name in metric_names
    ]
    report = "\n".join(
        [
            "# Phase 1 Baseline Pipeline Report",
            "",
            f"Generated at: `{source_summary.get('run_at', 'unknown')}`",
            "",
            "## Source and lineage",
            "",
            "| Property | Value |",
            "|---|---|",
            f"| Source | {source_summary.get('source_api', 'N/A')} |",
            f"| Query | {source_summary.get('source_query', 'N/A')} |",
            f"| Filter | {source_summary.get('source_filter', 'N/A')} |",
            f"| Raw records | {source_summary.get('raw_records', 0)} |",
            f"| Clean records | {source_summary.get('clean_records', 0)} |",
            f"| Vector collection | `{source_summary.get('collection_name', 'N/A')}` |",
            f"| Evaluation questions | {source_summary.get('evaluation_questions', 0)} |",
            "",
            "## Baseline evaluation",
            "",
            "| Metric | Value |",
            "|---|---:|",
            *metric_rows,
            "",
            "## Great Expectations quality gate",
            "",
            f"Overall GX status: **{'PASS' if quality.get('gx_success') else 'FAIL'}**  ",
            f"Combined quality gate: **{'PASS' if quality.get('success') else 'FAIL'}**",
            "",
            "| Expectation | Column | Status |",
            "|---|---|---|",
            *expectation_rows,
            "",
            "## Freshness SLA",
            "",
            "| Property | Value |",
            "|---|---:|",
            f"| Threshold (days) | {freshness.get('threshold_days', 'N/A')} |",
            f"| Maximum stale ratio | {_format_metric(freshness.get('max_stale_ratio', 'N/A'))} |",
            f"| Stale rows | {freshness.get('stale_rows', 'N/A')} |",
            f"| Total rows | {freshness.get('total_rows', 'N/A')} |",
            f"| Stale ratio | {_format_metric(freshness.get('stale_ratio', 'N/A'))} |",
            f"| Latest publication | {freshness.get('latest_published', 'N/A')} |",
            f"| Oldest publication | {freshness.get('oldest_published', 'N/A')} |",
            f"| Status | {'PASS' if freshness.get('is_fresh') else 'FAIL'} |",
            "",
            "## Artifacts",
            "",
            *[f"- `{path}`" for path in source_summary.get("artifacts", [])],
            "",
        ]
    )
    write_text(Path(report_path), report)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write the Baseline/Corrupted/Repaired comparison from measured values."""
    metric_names = (
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    metric_rows: list[str] = []
    for name in metric_names:
        baseline = float(baseline_metrics.get(name, 0.0))
        corrupted = float(corrupted_metrics.get(name, 0.0))
        repaired = float(repaired_metrics.get(name, 0.0))
        degradation = corrupted - baseline
        recovery = repaired - corrupted
        metric_rows.append(
            f"| `{name}` | {baseline:.4f} | {corrupted:.4f} | {repaired:.4f} "
            f"| {degradation:+.4f} | {recovery:+.4f} |"
        )

    hit_drop = float(corrupted_metrics.get("retrieval_hit_rate", 0.0)) - float(
        baseline_metrics.get("retrieval_hit_rate", 0.0)
    )
    f1_drop = float(corrupted_metrics.get("mean_token_f1", 0.0)) - float(
        baseline_metrics.get("mean_token_f1", 0.0)
    )
    hit_recovery = float(repaired_metrics.get("retrieval_hit_rate", 0.0)) - float(
        corrupted_metrics.get("retrieval_hit_rate", 0.0)
    )
    f1_recovery = float(repaired_metrics.get("mean_token_f1", 0.0)) - float(
        corrupted_metrics.get("mean_token_f1", 0.0)
    )

    report = "\n".join(
        [
            "# Corruption and Repair Comparison Report",
            "",
            "The same evaluation set is used for Baseline, Corrupted, and Repaired states.",
            "",
            "## Three-state metric comparison",
            "",
            "| Metric | Baseline | Corrupted | Repaired | Corruption delta | Repair delta |",
            "|---|---:|---:|---:|---:|---:|",
            *metric_rows,
            "",
            "## Data quality and freshness",
            "",
            "| Signal | Baseline | Corrupted | Repaired |",
            "|---|---|---|---|",
            f"| GX quality gate | See Phase 1 report | {'PASS' if corrupted_quality.get('gx_success') else 'FAIL'} | {'PASS' if repaired_quality.get('gx_success') else 'FAIL'} |",
            f"| Combined gate | See Phase 1 report | {'PASS' if corrupted_quality.get('success') else 'FAIL'} | {'PASS' if repaired_quality.get('success') else 'FAIL'} |",
            f"| Freshness | See Phase 1 report | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'} | {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'} |",
            f"| Stale rows | See Phase 1 report | {corrupted_freshness.get('stale_rows', 'N/A')} | {repaired_freshness.get('stale_rows', 'N/A')} |",
            f"| Stale ratio | See Phase 1 report | {_format_metric(corrupted_freshness.get('stale_ratio', 'N/A'))} | {_format_metric(repaired_freshness.get('stale_ratio', 'N/A'))} |",
            "",
            "## Evidence-based observations",
            "",
            f"1. Corruption changed retrieval hit rate by **{hit_drop:+.4f}** and mean token F1 by **{f1_drop:+.4f}** relative to baseline.",
            f"2. Repair from the trusted raw snapshot changed retrieval hit rate by **{hit_recovery:+.4f}** and mean token F1 by **{f1_recovery:+.4f}** relative to corrupted data.",
            f"3. The corrupted quality gate was **{'PASS' if corrupted_quality.get('success') else 'FAIL'}**; after repair it was **{'PASS' if repaired_quality.get('success') else 'FAIL'}**.",
            "",
            "No impact is claimed where a measured delta is zero. Detailed evidence is stored in the metrics, answers, quality, freshness, and corruption-log artifacts.",
            "",
            "## Artifacts",
            "",
            "- `data/results/corruption_log.json`",
            "- `data/results/baseline_metrics.json`",
            "- `data/results/corrupted_metrics.json`",
            "- `data/results/repaired_metrics.json`",
            "- `data/quality/corrupted_quality_report.json`",
            "- `data/quality/repaired_quality_report.json`",
            "",
        ]
    )
    write_text(Path(report_path), report)
