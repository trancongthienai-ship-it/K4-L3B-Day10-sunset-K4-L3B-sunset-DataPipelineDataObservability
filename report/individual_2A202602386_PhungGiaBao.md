# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Phùng Gia Bảo |
| MSSV | 2A202602386 |
| Khóa/Lớp | K4 — L3B |
| Tên nhóm | sunset |
| Vai trò chính | Data Foundation & Recovery |
| Repository | `https://github.com/trancongthienai-ship-it/K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability` |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Crossref ingestion | `src/ingestion/crossref.py` — `parse_crossref_payload()`, `fetch_source_records()`, `load_raw_records()` | Crossref REST payload hoặc snapshot offline | 24 `PaperRecord`, hai raw artifacts | Hoàn thành |
| Data cleaning | `src/ingestion/cleaning.py` — `build_clean_dataframe()` | Danh sách `PaperRecord`, `run_date` | Clean DataFrame 24 dòng, CSV/JSON | Hoàn thành |
| Corruption suite | `src/ingestion/corruption.py` — `corrupt_clean_dataframe()` | Clean DataFrame | Corrupted DataFrame và corruption log | Hoàn thành |
| Safe recovery | `src/pipelines/corruption_flow.py` — `repair_from_raw_snapshot()` | Raw-record snapshot đáng tin cậy | Repaired CSV/JSON và kiểm tra idempotency | Hoàn thành |

Phần việc của tôi cung cấp dữ liệu đầu vào sạch cho Vector Index và Evaluation. Khi corruption được kích hoạt, module phục hồi tái tạo dữ liệu từ raw snapshot thay vì sửa trực tiếp dữ liệu hỏng, sau đó bàn giao repaired dataset cho bước index và đánh giá lại.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Tích hợp Phase 1 | `src/pipelines/phase1.py` | Clean artifacts được lưu đúng contract để ChromaDB và evaluation sử dụng |
| Tích hợp Phase 2 | Observability & Evaluation | Corrupted/repaired artifacts có schema nhất quán để so sánh ba trạng thái |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Thu thập và bóc tách Crossref | `crossref.py`, `data/raw/` | 24 bản ghi hợp lệ, loại JATS khỏi abstract | Chạy `fetch_source_records()` và kiểm tra số lượng |
| Chuẩn hóa dữ liệu | `cleaning.py`, `data/clean/papers_clean.*` | 24 DOI duy nhất, không thiếu trường bắt buộc | Kiểm tra `df.paper_id.is_unique` và số dòng |
| Tiêm lỗi có kiểm soát | `corruption.py`, `corruption_log.json` | Đủ 6 loại corruption, 24 dòng thành 21 dòng | Kiểm tra `operation_count == 6` |
| Phục hồi từ raw snapshot | `repair_from_raw_snapshot()` | Repaired dataset trở lại 24 dòng và Quality Gate PASS | Chạy Phase 2 và đọc repaired quality report |

Output tiêu biểu là `data/results/corruption_log.json`. Artifact này ghi đầy đủ sáu loại lỗi, DOI bị ảnh hưởng, số bản ghi và tham số corruption. Nó giúp truy vết thay đổi dữ liệu và liên hệ trực tiếp với quality signal cùng RAG metrics.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần biến metadata không đồng nhất từ Crossref thành dữ liệu có schema ổn định, bảo toàn nguồn gốc để có thể chạy offline và phục hồi an toàn khi dữ liệu downstream bị mất, rỗng, nhiễu, cũ hoặc trùng lặp.

### Cách triển khai

Ở ingestion, payload được kiểm tra cấu trúc trước khi đọc `message.items`. DOI được chuẩn hóa chữ thường; title, abstract, author, subject, ngày xuất bản và URL được chuyển thành `PaperRecord`. Abstract được loại JATS/HTML. API sử dụng timeout và retry/backoff cho lỗi tạm thời; nếu không truy cập được mạng hoặc gặp lỗi 429/5xx, pipeline đọc snapshot local.

Ở cleaning, dữ liệu được chuẩn hóa khoảng trắng, danh sách tác giả/lĩnh vực được khử trùng, ngày được parse theo UTC và các bản ghi thiếu DOI, title, summary hoặc published bị loại. `paper_id` được deduplicate; `age_days`, `summary_chars`, `authors_joined`, `categories_joined` và `text_for_embedding` năm phần được tạo trước khi index.

Ở corruption, sáu lỗi được áp dụng theo vị trí xác định để kết quả có thể tái lập. Sau khi sửa title, summary hoặc published, các trường dẫn xuất được xây dựng lại. Recovery luôn đọc `crossref_records.json`, chạy lại cleaning và ghi repaired artifacts. Với cùng snapshot và `run_date`, hai lần repair phải tạo DataFrame giống hệt nhau.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Crossref JSON hoặc `list[PaperRecord]`; clean DataFrame; UTC `run_date` |
| Output | Raw JSON, clean/corrupted/repaired CSV và JSON, corruption log |
| Module phụ thuộc | `core.config`, `core.utils`, `pandas`, `requests` |
| Module sử dụng output | `retrieval.index`, `evaluation.metrics`, `observability.quality`, các pipeline |
| Điều kiện lỗi cần xử lý | Offline/429/5xx, payload sai schema, ngày không hợp lệ, DOI trùng, snapshot thiếu |

### Cách xác minh

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python .\script\run_phase1.py
python .\script\run_corruption_flow.py
```

- **Kết quả mong đợi:** 24 raw/clean records; quality baseline PASS; corrupted quality FAIL; repaired quality PASS; repair idempotent.
- **Kết quả thực tế:** Baseline 24 dòng, corrupted 21 dòng, repaired 24 dòng; kết quả đúng kỳ vọng.
- **Artifact/log:** `data/results/corruption_log.json`, `data/quality/repaired_quality_report.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần phục hồi sau khi dữ liệu clean đã bị corruption.
- **Các phương án đã cân nhắc:** (1) Vá từng lỗi trực tiếp trên corrupted DataFrame; (2) tái tạo toàn bộ dataset từ raw snapshot bất biến.
- **Phương án đã chọn:** Tái tạo từ `data/raw/crossref_records.json` bằng cùng cleaning pipeline.
- **Lý do:** Vá tại chỗ có thể bỏ sót lỗi và không phục hồi được record đã bị drop. Tái tạo từ nguồn tin cậy dễ kiểm chứng, tái lập và idempotent hơn.
- **Bằng chứng quyết định phù hợp:** Repaired dataset trở lại 24 dòng, Quality Gate chuyển từ FAIL sang PASS, Hit Rate phục hồi từ 0.80 lên 1.00 và Token F1 từ 0.90 lên 1.00.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `FileNotFoundError: data/clean/papers_clean.json does not exist` khi chạy Quality Gate.
- **Lệnh hoặc bước tái hiện:** Gọi `pd.read_json(s.paths.clean_json)` trước khi clean DataFrame được ghi thành artifact.
- **Nguyên nhân gốc:** `build_clean_dataframe()` mới trả về DataFrame trong bộ nhớ, còn bước persist clean artifacts chưa được thực thi.
- **Cách xử lý:** Lưu DataFrame bằng `write_csv()` và `write_json()` trước khi Quality Gate đọc dữ liệu.
- **Cách xác minh sau khi sửa:** Đọc lại `papers_clean.json`, xác nhận đủ 24 dòng và chạy Quality Gate nhận `success = true`.
- **Điều học được:** Cần phân biệt output trong bộ nhớ với artifact đã persist và bảo đảm đúng thứ tự producer–consumer trong pipeline.

## 7. Hiểu biết về luồng end-to-end

1. Crossref payload được tải hoặc đọc từ snapshot, parse thành `PaperRecord`, làm sạch thành DataFrame, tạo `text_for_embedding`, sau đó MiniLM sinh vector và ChromaDB lưu ba collection riêng cho baseline, corrupted và repaired.
2. Evaluation set chứa câu hỏi, ground-truth answer và DOI chuẩn. Retrieval Hit Rate kiểm tra DOI chuẩn có nằm trong các tài liệu truy hồi; Token F1 đo mức trùng khớp token giữa câu trả lời và ground truth.
3. Quality checks kiểm tra cấu trúc và nội dung tại thời điểm chạy như row count, null, uniqueness và độ dài summary. Freshness monitoring đo tỷ lệ record có `age_days > 180` và so sánh với SLA 25%.
4. Cùng một test set phải được giữ nguyên để thay đổi metrics phản ánh thay đổi dữ liệu, không phải thay đổi độ khó của câu hỏi.
5. Repair thành công khi repaired dataset được tái tạo từ raw snapshot, Quality Gate trở lại PASS, freshness phục hồi, metrics quay về baseline và phép kiểm tra idempotency đạt.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.00 | 0.80 | 1.00 | Drop latest records làm mất ground-truth documents; repair phục hồi đầy đủ |
| `mean_token_f1` | 1.00 | 0.90 | 1.00 | Dữ liệu hỏng làm giảm độ khớp câu trả lời |
| `judge_accuracy` | 1.00 | 0.90 | 1.00 | Judge ghi nhận một phần câu trả lời không còn chính xác |
| `mean_judge_score` | 5.00 | 4.70 | 5.00 | Điểm giảm 0.30 rồi phục hồi hoàn toàn |
| Quality checks | PASS | FAIL | PASS | Corrupted vi phạm uniqueness và độ dài summary |
| Freshness status | PASS | PASS | PASS | Corrupted có 14.29% stale, vẫn dưới SLA 25% |

### Kết luận từ số liệu

1. Drop records, blank summary và duplicate rows → GX phát hiện 4 occurrence DOI trùng cùng 2 summary quá ngắn → Hit Rate giảm 0.20 và Token F1 giảm 0.10.
2. Tái tạo từ raw snapshot → số dòng và uniqueness phục hồi, Quality Gate trở lại PASS → Hit Rate và Token F1 quay lại 1.00.

Corruption ảnh hưởng rõ nhất đến retrieval là `drop_latest_records`, vì tài liệu ground truth bị loại hoàn toàn khỏi index nên semantic search không thể truy hồi đúng DOI. Blank summary và truncate title ảnh hưởng nội dung embedding, còn duplicate rows được GX phát hiện rõ dù không nhất thiết làm metric giảm mạnh.

Kết quả khác kỳ vọng là freshness của corrupted dataset vẫn PASS. Nguyên nhân là chỉ 3/21 dòng stale, tương đương 14.29%, thấp hơn ngưỡng cảnh báo 25%. Tôi kiểm tra lại `corrupted_freshness_report.json` và xác nhận đây là hành vi đúng theo SLA, không phải lỗi triển khai.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw snapshot cần được giữ bất biến để hỗ trợ lineage, reproducibility và disaster recovery.
2. Quality Gate phát hiện được lỗi dữ liệu mà ứng dụng vẫn có thể tiếp tục chạy, qua đó hạn chế Silent Failure.
3. Chất lượng retrieval và câu trả lời phụ thuộc trực tiếp vào tính đầy đủ, duy nhất và sạch của corpus được index.

### Nếu có thêm thời gian

Tôi sẽ bổ sung manifest chứa checksum cho raw/clean/repaired artifacts và kiểm tra schema version trước khi repair. Hiệu quả có thể đo bằng việc cố ý thay đổi snapshot, xác nhận checksum mismatch chặn pipeline và chứng minh repaired data chỉ được tạo từ artifact đã xác thực.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phùng Gia Bảo  
**Ngày xác nhận:** 2026-09-26
