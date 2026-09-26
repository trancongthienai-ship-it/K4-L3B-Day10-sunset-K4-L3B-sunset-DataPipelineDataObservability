# Phase 1: Baseline Report

## 1. Source Summary
```json
{
  "raw_records": 24,
  "clean_records": 24,
  "source_api": "Crossref REST API"
}
```

## 2. Evaluation Metrics
```json
{
  "samples": 16,
  "retrieval_hit_rate": 1.0,
  "mean_token_f1": 0.4218227902825426,
  "judge_accuracy": 0.5,
  "mean_judge_score": 2.5,
  "ragas": {
    "skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."
  }
}
```

## 3. Data Quality
```json
{
  "evaluated_expectations": 6,
  "successful_expectations": 5,
  "unsuccessful_expectations": 1,
  "success_percent": 83.33333333333334
}
```

## 4. Freshness
```json
{
  "latest_published": "2026-07-22",
  "oldest_published": "2026-03-28",
  "stale_rows": 1,
  "total_rows": 24,
  "is_fresh": false
}
```
