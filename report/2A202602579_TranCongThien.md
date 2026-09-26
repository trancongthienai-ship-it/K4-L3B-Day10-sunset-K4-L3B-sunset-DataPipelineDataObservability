# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Công Thiện             |
| MSSV               | 2A202602579                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | sunset     |
| Vai trò chính    | Trưởng nhóm / Pipeline Integrator                 |
| Repository         | K4-L3-DAY10-sunset-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Thiết lập config dự án | `core/config.py` | Biến môi trường .env | Cấu hình Settings cho toàn bộ Pipeline | Hoàn thành |
| Phase 1 Pipeline | `src/pipelines/phase1.py` | Data từ API | Các file csv, json, thư mục DB và báo cáo | Hoàn thành |
| Corruption Flow | `src/pipelines/corruption_flow.py` | Data sạch từ Phase 1 | Kết quả so sánh 3 trạng thái của RAG | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Cấu hình `sys.path` | Các file script chạy `run_phase1.py` | Giải quyết lỗi `ModuleNotFoundError` khi chạy script ở thư mục gốc |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Chạy thành công luồng 1 | `script/run_phase1.py` | Sinh ra `data/reports/phase1_report.md` | Đọc file markdown kết quả |
| Chạy thành công luồng mô phỏng lỗi | `script/run_corruption_flow.py` | Sinh ra `data/reports/corruption_report.md` | Đọc bảng so sánh 3 trạng thái |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Việc gọi lẻ tẻ các file Data Cleaning, Embedding, RAG Agent rất phức tạp và khó tự động hóa. Cần một nơi gắn kết toàn bộ các logic này lại thành một "Đường ống" (Pipeline) duy nhất.

### Cách triển khai
Áp dụng mẫu thiết kế (design pattern) Orchestrator trong Data Engineering. Khởi tạo `Settings` làm xương sống truyền qua tất cả các hàm. Data được truyền từ hàm nọ sang hàm kia theo đúng thứ tự: Fetch -> Clean -> Embed -> Eval -> Quality Check -> Report.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Lệnh gọi từ shell `python script/run_phase1.py` |
| Output                         | Toàn bộ artifact trong thư mục `data/` |
| Module phụ thuộc             | `ingestion.*`, `retrieval.*`, `observability.*` |
| Điều kiện lỗi cần xử lý | Xử lý file `.env` nếu thiếu biến LLM hoặc API KEY |

### Cách xác minh

```bash
python script/run_phase1.py
```
- **Kết quả mong đợi:** Mã chạy suôn sẻ không báo lỗi, hiển thị progress bar của thư viện sentence-transformers.
- **Kết quả thực tế:** Chạy thành công, tạo đủ các file ở `data/reports`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Gặp lỗi `ModuleNotFoundError` khi chạy các script bằng lệnh `python script/run_phase1.py`.
- **Phương án đã chọn:** Dùng thư viện `Path` để tự động inject `src/` vào `sys.path`.
- **Lý do:** Giúp cho người chạy code không cần phải set PYTHONPATH thủ công trên terminal, tăng tính "Plug-and-play" cho dự án.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `TypeError: Cannot subtract tz-naive and tz-aware datetime-like objects.`
- **Nguyên nhân gốc:** Hàm `datetime.now(UTC)` trả về định dạng thời gian có đính kèm múi giờ, nhưng data load từ Pandas lại không có múi giờ, dẫn đến lỗi khi trừ đi ngày tháng để tính `age_days`.
- **Cách xử lý:** Sử dụng hàm `.tz_localize(None)` để xóa múi giờ khỏi biến hiện tại trước khi thực hiện phép trừ.

## 7. Hiểu biết về luồng end-to-end

1. Từ Crossref, data được tải về dưới dạng JSON thô. Đi qua `cleaning.py` để gộp chuỗi, thành DataFrame. Sau đó DataFrame này được cấp cho `LocalEmbeddingIndex` băm thành Vector và đẩy vào ChromaDB.
2. Ground-truth doc IDs để tính xem mô hình có tìm đúng tài liệu hay không (Context Recall / Precision), nếu tìm đúng tài liệu mà vẫn trả lời sai thì lỗi là do Prompt/LLM.
3. Quality check kiểm tra cấu trúc dữ liệu (như null, type, độ dài chuỗi). Còn Freshness monitoring kiểm tra độ cũ/mới của dữ liệu so với hiện tại.
4. Cùng một test set mới đo được biến động của LLM. Nếu mỗi lần lấy một bài thi khác nhau, điểm cao hay thấp là do đề thi dễ/khó, không phải do chất lượng dữ liệu.
5. Repair thành công khi các metric (như `retrieval_hit_rate`) trở lại mức 1.0 (như Baseline) và số expectation rớt giảm xuống.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0 | 0.5 | 1.0 | Tụt rõ rệt khi data bị hỏng, hồi phục tốt |
| `mean_token_f1`      | 0.42 | 0.21 | 0.42 | AI sinh ra từ vô nghĩa khi không tìm thấy data |
| `judge_accuracy`     | 0.5 | 0.25 | 0.5 | Rớt một nửa |
| `mean_judge_score`   | 2.5 | 1.75 | 2.5 | Đánh giá tổng quát cho thấy AI trở nên rất tệ |
| Quality checks         | 5/6 | 3/6 | 5/6 | Chặn được rác thành công |
| Freshness status       | False | False | False | Do bài lab dùng data giả lập quá hạn mức |

### Kết luận từ số liệu
1. Dữ liệu bị tiêm noise/xóa summary → Báo cáo Quality báo lỗi fail 3/6 → Model không tìm được đáp án (hit rate còn 0.5).
2. Chạy hàm Repair khôi phục file → Data Quality phục hồi về 5/6 → AI tìm đúng lại đáp án (hit rate lên 1.0).

## 9. Điều học được và hướng cải thiện

1. Data Pipeline cần sự kết dính tốt, phải làm chủ được cấu trúc thư mục.
2. Data Observability là tấm khiên vững chắc giúp kỹ sư yên tâm nhắm mắt chạy model.
3. RAG model thông minh cỡ nào, thiếu dữ liệu hoặc bị nhiễu cũng chỉ là kẻ chém gió.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Công Thiện
**Ngày xác nhận:** 2026-09-26
