# Phase 2: Corruption & Repair Report

## 1. Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| **judge_accuracy** | 0.5 | 0.25 | 0.5 |
| **mean_judge_score** | 2.5 | 1.75 | 2.5 |
| **mean_token_f1** | 0.4218227902825426 | 0.21478658536585366 | 0.4218227902825426 |
| **retrieval_hit_rate** | 1.0 | 0.5 | 1.0 |
| answer_relevancy (ragas) | N/A | N/A | N/A |
| faithfulness (ragas) | N/A | N/A | N/A |
| context_precision (ragas) | N/A | N/A | N/A |
| context_recall (ragas) | N/A | N/A | N/A |

## 2. Quality & Freshness

### Corrupted State
**Quality Statistics:**
```json
{
  "evaluated_expectations": 6,
  "successful_expectations": 3,
  "unsuccessful_expectations": 3,
  "success_percent": 50.0
}
```
**Freshness:**
```json
{
  "latest_published": "2026-07-05",
  "oldest_published": "2026-03-28",
  "stale_rows": 2,
  "total_rows": 23,
  "is_fresh": false
}
```

### Repaired State
**Quality Statistics:**
```json
{
  "evaluated_expectations": 6,
  "successful_expectations": 5,
  "unsuccessful_expectations": 1,
  "success_percent": 83.33333333333334
}
```
**Freshness:**
```json
{
  "latest_published": "2026-07-22",
  "oldest_published": "2026-03-28",
  "stale_rows": 1,
  "total_rows": 24,
  "is_fresh": false
}
```
