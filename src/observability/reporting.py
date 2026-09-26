from __future__ import annotations

from typing import Any


import json
from pathlib import Path

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 1: Baseline Report

## 1. Source Summary
```json
{json.dumps(source_summary, indent=2)}
```

## 2. Evaluation Metrics
```json
{json.dumps(metrics, indent=2)}
```

## 3. Data Quality
```json
{json.dumps(quality.get("statistics", quality) if isinstance(quality, dict) else quality, indent=2)}
```

## 4. Freshness
```json
{json.dumps(freshness, indent=2)}
```
"""
    path_obj = Path(report_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        f.write(content)


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
    rb = baseline_metrics.get("ragas", {})
    rc = corrupted_metrics.get("ragas", {})
    rr = repaired_metrics.get("ragas", {})
    
    content = f"""# Phase 2: Corruption & Repair Report

## 1. Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| **judge_accuracy** | {baseline_metrics.get('judge_accuracy', 'N/A')} | {corrupted_metrics.get('judge_accuracy', 'N/A')} | {repaired_metrics.get('judge_accuracy', 'N/A')} |
| **mean_judge_score** | {baseline_metrics.get('mean_judge_score', 'N/A')} | {corrupted_metrics.get('mean_judge_score', 'N/A')} | {repaired_metrics.get('mean_judge_score', 'N/A')} |
| **mean_token_f1** | {baseline_metrics.get('mean_token_f1', 'N/A')} | {corrupted_metrics.get('mean_token_f1', 'N/A')} | {repaired_metrics.get('mean_token_f1', 'N/A')} |
| **retrieval_hit_rate** | {baseline_metrics.get('retrieval_hit_rate', 'N/A')} | {corrupted_metrics.get('retrieval_hit_rate', 'N/A')} | {repaired_metrics.get('retrieval_hit_rate', 'N/A')} |
| answer_relevancy (ragas) | {rb.get('answer_relevancy', 'N/A')} | {rc.get('answer_relevancy', 'N/A')} | {rr.get('answer_relevancy', 'N/A')} |
| faithfulness (ragas) | {rb.get('faithfulness', 'N/A')} | {rc.get('faithfulness', 'N/A')} | {rr.get('faithfulness', 'N/A')} |
| context_precision (ragas) | {rb.get('context_precision', 'N/A')} | {rc.get('context_precision', 'N/A')} | {rr.get('context_precision', 'N/A')} |
| context_recall (ragas) | {rb.get('context_recall', 'N/A')} | {rc.get('context_recall', 'N/A')} | {rr.get('context_recall', 'N/A')} |

## 2. Quality & Freshness

### Corrupted State
**Quality Statistics:**
```json
{json.dumps(corrupted_quality.get("statistics", corrupted_quality) if isinstance(corrupted_quality, dict) else corrupted_quality, indent=2)}
```
**Freshness:**
```json
{json.dumps(corrupted_freshness, indent=2)}
```

### Repaired State
**Quality Statistics:**
```json
{json.dumps(repaired_quality.get("statistics", repaired_quality) if isinstance(repaired_quality, dict) else repaired_quality, indent=2)}
```
**Freshness:**
```json
{json.dumps(repaired_freshness, indent=2)}
```
"""
    path_obj = Path(report_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        f.write(content)
