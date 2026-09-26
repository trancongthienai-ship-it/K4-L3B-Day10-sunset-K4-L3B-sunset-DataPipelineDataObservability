# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Thanh Thái             |
| MSSV               | 2A202602454                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | sunset     |
| Vai trò chính    | RAG & Vector Index                 |
| Repository         | K4-L3-DAY10-sunset-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Khởi tạo Vector DB | `src/retrieval/index.py` | Dataframe từ bước Clean | ChromaDB Folder & Embeddings JSON | Hoàn thành |
| Agent logic | `src/retrieval/agent.py` | Query của người dùng | Kết quả truy xuất & Trả lời từ LLM | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Đọc file `.env` LLM | Hỗ trợ Thiện config LLM | Trỏ đúng về mô hình OpenAI qua Langchain |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Khởi tạo Collection ChromaDB | `src/retrieval/index.py` | Folder `data/chroma/` | Thấy thư mục sinh ra và file size tăng lên |
| LLM API | `src/retrieval/llm.py` | Trả lời từ OpenAI | Check logs trong file `baseline_answers.json` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Cần một nơi lưu trữ tối ưu hóa cho phép tìm kiếm theo ngữ nghĩa (Semantic Search) thay vì tìm theo keyword thông thường. Từ đó đưa văn bản vào trong Prompt (Context window) để LLM trả lời.

### Cách triển khai
Dùng `SentenceTransformers` model `MiniLM` để tính toán ma trận vector. Sau đó nạp dữ liệu này vào ChromaDB dưới dạng Persistence Mode (lưu xuống ổ cứng tại `data/chroma`). Hàm truy xuất sẽ tính toán cosine similarity để lấy ra Top-K bài báo có liên quan.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Pandas Dataframe có cột `text_for_embedding` |
| Output                         | Đối tượng LocalEmbeddingIndex |
| Module phụ thuộc             | `core/config.py`, `pandas` |

### Cách xác minh

```bash
python script/run_phase1.py
```
- **Kết quả mong đợi:** Progress bar tải mô hình MiniLM hiển thị đầy đủ, không báo lỗi.
- **Kết quả thực tế:** Hoạt động đúng, Vector được ghi vào ổ cứng.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** ChromaDB không nhận giá trị Metadata là Timestamp hoặc NaN.
- **Phương án đã chọn:** Format cột `published` trở lại thành string dạng `YYYY-MM-DD` và điền chuỗi rỗng bằng `.fillna("")` cho các giá trị trống.
- **Lý do:** ChromaDB chỉ chấp nhận Primitive Types cho Metadata nhằm phục vụ việc filter một cách nhanh chóng. Ép kiểu về String giúp quá trình serialize diễn ra an toàn.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValueError: Expected metadata value to be a str, int, float, bool, SparseVector, list, or None, got 2026-07-22 00:00:00 which is a Timestamp in add.`
- **Nguyên nhân gốc:** Pandas tự nhận diện và ép kiểu Data cho Metadata.
- **Cách xử lý:** Sử dụng `dt.strftime` để format lại thành chuỗi trước khi đưa vào hàm `LocalEmbeddingIndex.build()`.

## 7. Hiểu biết về luồng end-to-end

(Giống với các thành viên khác trong nhóm)

## 8. Phân tích kết quả

(Giống với phân tích tổng hợp của team trong báo cáo)

## 9. Điều học được và hướng cải thiện

1. Cách vận hành của ChromaDB và cách nhúng dữ liệu thủ công.
2. Cần phải để ý rất kỹ Data Types khi đẩy dữ liệu vào Database ngoài (NoSQL/VectorDB).
3. Retrieval mạnh đến mấy nhưng dữ liệu nhiễu (Corruption) thì cũng không thể tìm được văn bản tốt.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact để đối chiếu.
- [x] Báo cáo không chứa API key.
- [x] Báo cáo không phải là bản sao chép.

**Họ và tên:** Trần Thanh Thái
**Ngày xác nhận:** 2026-09-26
