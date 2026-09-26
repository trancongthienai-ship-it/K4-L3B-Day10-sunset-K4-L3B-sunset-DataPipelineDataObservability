# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `sunset`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | | | | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`) | `report/<MSSV1>_HoTen.md` |
| 2 | Phùng Gia Bảo | 2A202602386 | — | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, `corruption.py`, raw snapshot & repair) | `report/individual_report.md` |
| 3 | | | | RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/<MSSV3>_HoTen.md` |
| 4 | | | | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, reporting) | `report/<MSSV4>_HoTen.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

## # Cá nhân

### ## HoVaTen1-MSSV1
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Kiểm tra tính nhất quán của các artifacts và theo dõi Contributor tracking trên GitHub nhánh `main`.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## Phùng Gia Bảo - 2A202602386
- **Vai trò:** Data Foundation & Recovery — phụ trách thu thập, chuẩn hóa, bảo toàn nguồn gốc, mô phỏng lỗi và phục hồi dữ liệu.
- **Công việc chi tiết đã hoàn thành:**
  - Hoàn thiện `src/ingestion/crossref.py`: thu thập metadata từ Crossref REST API, retry/backoff khi gặp lỗi tạm thời, fallback sang snapshot offline và chuẩn hóa 24 bản ghi thành `PaperRecord`.
  - Bảo toàn hai raw artifacts phục vụ Data Lineage: `data/raw/crossref_response.json` và `data/raw/crossref_records.json`; dữ liệu raw chỉ bị ghi đè sau khi response mới được tải và parse thành công.
  - Hoàn thiện `src/ingestion/cleaning.py`: loại JATS/HTML và khoảng trắng thừa, chuẩn hóa tác giả/lĩnh vực/ngày tháng, khử trùng `paper_id`, tính `age_days`, `summary_chars` và tạo `text_for_embedding` gồm 5 phần.
  - Hoàn thiện `src/ingestion/corruption.py`: triển khai đủ 6 kịch bản gồm drop latest records, blank summary, inject noise, truncate title, stale date và duplicate rows; ghi đầy đủ DOI, số dòng và tham số vào `data/results/corruption_log.json`.
  - Xây dựng `repair_from_raw_snapshot()` trong `src/pipelines/corruption_flow.py`: tái tạo dữ liệu sạch từ raw snapshot đáng tin cậy, không vá trực tiếp dữ liệu hỏng, đồng thời kiểm tra tính idempotent với cùng snapshot và thời điểm chạy.
  - Bàn giao các artifacts phục hồi `papers_clean_repaired.csv/json`; kết quả repaired trở lại 24 dòng duy nhất và đạt toàn bộ Quality Gate.
- **Kết quả và bằng chứng:**
  - Baseline có 24 bản ghi sạch; corrupted còn 21 dòng sau khi bỏ 5 dòng mới nhất và thêm 2 dòng trùng.
  - Quality Gate phát hiện dữ liệu corrupted: 4 occurrence trùng `paper_id` và 2 summary không đạt độ dài tối thiểu.
  - Sau repair, `retrieval_hit_rate` phục hồi từ `0.80` lên `1.00`, `mean_token_f1` từ `0.90` lên `1.00`; quality và freshness đều `PASS`.
  - Bằng chứng: `data/results/corruption_log.json`, `data/results/repaired_metrics.json`, `data/quality/repaired_quality_report.json` và `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Hiểu cách Data Lineage và Raw Preservation tạo điểm neo phục hồi đáng tin cậy, giúp pipeline có thể tái tạo dữ liệu thay vì che hoặc vá lỗi trên dữ liệu đã bị corruption.
  - Nắm được quan hệ nhân quả giữa chất lượng dữ liệu và hiệu năng RAG: corruption làm giảm Hit Rate/Token F1, còn repair idempotent giúp khôi phục cả dữ liệu, Quality Gate và các chỉ số AI.

### ## HoVaTen3-MSSV3
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`.
  - Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Xây dựng QA Agent truy vấn ngữ cảnh chính xác theo tài liệu.
- **Điều học được / Đóng góp chính:**
  - Cách cô lập các không gian vector để so sánh khách quan giữa dữ liệu sạch và dữ liệu bị lỗi.

### ## HoVaTen4-MSSV4
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ câu hỏi đánh giá chuẩn trong `src/evaluation/testset.py`.
  - Đo lường và xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Cách thiết lập hệ thống cảnh báo sớm chặn đứng hiện tượng Silent Failure trước khi dữ liệu vào serving layer.
