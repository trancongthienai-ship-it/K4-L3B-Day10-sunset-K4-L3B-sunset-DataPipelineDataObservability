# Corruption and Repair Comparison Report

The same evaluation set is used for Baseline, Corrupted, and Repaired states.

## Three-state metric comparison

| Metric | Baseline | Corrupted | Repaired | Corruption delta | Repair delta |
|---|---:|---:|---:|---:|---:|
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | +0.2000 |
| `mean_token_f1` | 1.0000 | 0.9000 | 1.0000 | -0.1000 | +0.1000 |
| `judge_accuracy` | 1.0000 | 0.9000 | 1.0000 | -0.1000 | +0.1000 |
| `mean_judge_score` | 5.0000 | 4.7000 | 5.0000 | -0.3000 | +0.3000 |

## Data quality and freshness

| Signal | Baseline | Corrupted | Repaired |
|---|---|---|---|
| GX quality gate | See Phase 1 report | FAIL | PASS |
| Combined gate | See Phase 1 report | FAIL | PASS |
| Freshness | See Phase 1 report | FRESH | FRESH |
| Stale rows | See Phase 1 report | 3 | 1 |
| Stale ratio | See Phase 1 report | 0.1429 | 0.0417 |

## Evidence-based observations

1. Corruption changed retrieval hit rate by **-0.2000** and mean token F1 by **-0.1000** relative to baseline.
2. Repair from the trusted raw snapshot changed retrieval hit rate by **+0.2000** and mean token F1 by **+0.1000** relative to corrupted data.
3. The corrupted quality gate was **FAIL**; after repair it was **PASS**.

No impact is claimed where a measured delta is zero. Detailed evidence is stored in the metrics, answers, quality, freshness, and corruption-log artifacts.

## Artifacts

- `data/results/corruption_log.json`
- `data/results/baseline_metrics.json`
- `data/results/corrupted_metrics.json`
- `data/results/repaired_metrics.json`
- `data/quality/corrupted_quality_report.json`
- `data/quality/repaired_quality_report.json`
