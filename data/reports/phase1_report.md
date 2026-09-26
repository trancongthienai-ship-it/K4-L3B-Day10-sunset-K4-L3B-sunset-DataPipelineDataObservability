# Phase 1 Baseline Pipeline Report

Generated at: `2026-09-26T03:28:15.910085+00:00`

## Source and lineage

| Property | Value |
|---|---|
| Source | Crossref REST API |
| Query | agentic retrieval augmented generation large language model |
| Filter | from-pub-date:2026-03-30,has-abstract:true |
| Raw records | 24 |
| Clean records | 24 |
| Vector collection | `papers-baseline` |
| Evaluation questions | 10 |

## Baseline evaluation

| Metric | Value |
|---|---:|
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |

## Great Expectations quality gate

Overall GX status: **PASS**  
Combined quality gate: **PASS**

| Expectation | Column | Status |
|---|---|---|
| ExpectTableRowCountToBeBetween | - | PASS |
| ExpectColumnValuesToNotBeNull | paper_id | PASS |
| ExpectColumnValuesToNotBeNull | title | PASS |
| ExpectColumnValuesToNotBeNull | text_for_embedding | PASS |
| ExpectColumnValuesToBeUnique | paper_id | PASS |
| ExpectColumnValueLengthsToBeBetween | summary | PASS |

## Freshness SLA

| Property | Value |
|---|---:|
| Threshold (days) | 180 |
| Maximum stale ratio | 0.2500 |
| Stale rows | 1 |
| Total rows | 24 |
| Stale ratio | 0.0417 |
| Latest publication | 2026-07-22 |
| Oldest publication | 2026-03-28 |
| Status | PASS |

## Artifacts

- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\raw\crossref_response.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\raw\crossref_records.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\clean\papers_clean.csv`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\clean\papers_clean.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\embeddings\papers_embeddings.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\eval\test_set.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\results\baseline_metrics.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\results\baseline_answers.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\quality\baseline_quality_report.json`
- `D:\AITC VinUni\K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability\data\quality\freshness_report.json`
