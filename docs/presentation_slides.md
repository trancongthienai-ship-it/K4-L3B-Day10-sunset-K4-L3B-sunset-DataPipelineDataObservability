---
marp: true
theme: default
paginate: true
---

# 🚀 Báo Cáo Đồ Án Day 10
## Xây dựng Data Pipeline & Hệ thống Data Observability cho RAG Agent
**Nhóm:** sunset
**Khóa/Lớp:** K4-L3-DAY10

**Thành viên:**
1. Trần Công Thiện (Trưởng nhóm / Pipeline Integrator)
2. Phùng Gia Bảo (Data Foundation & Recovery)
3. Trần Thanh Thái (RAG & Vector Index)
4. Dương Hữu Đạt (Observability & Evaluation)

---

# 1. Bối Cảnh & Mục Tiêu Dự Án

- **Bài toán:** Hệ thống RAG (Retrieval-Augmented Generation) rất nhạy cảm với dữ liệu đầu vào. Nếu dữ liệu bị bẩn, thiếu sót hoặc lỗi thời, AI sẽ bị "ảo giác" (hallucinate).
- **Mục tiêu:** 
  - Xây dựng một **Data Pipeline tự động** (từ lúc lấy dữ liệu thô đến lúc băm vector vào ChromaDB).
  - Tích hợp **Data Observability (Great Expectations)** làm chốt chặn kiểm duyệt chất lượng dữ liệu trước khi nạp vào AI.
  - Kiểm thử khả năng chịu đựng của hệ thống bằng kịch bản tiêm lỗi giả lập (Chaos Engineering).

---

# 2. Kiến Trúc Data Pipeline (Luồng End-to-End)

Đường ống dữ liệu được thiết kế theo các module độc lập:
1. **Fetch (Crossref API):** Kéo metadata của các bài báo khoa học.
2. **Clean (Pandas):** Xử lý null, nối chuỗi, ép chuẩn định dạng ngày tháng.
3. **Quality Gate (Great Expectations):** Kiểm tra cấu trúc (schema, độ dài, trùng lặp) và độ trễ (Freshness).
4. **Embed & Index (SentenceTransformers):** Băm văn bản sạch thành Vector và nạp vào ChromaDB.
5. **Retrieval & Agent (Langchain):** Tìm kiếm Semantic Search và nhồi Context cho LLM trả lời.

---

# 3. Kịch Bản "Thảm Họa" (Corruption Flow)

Để chứng minh tầm quan trọng của Data Quality, nhóm đã thiết lập một luồng thử nghiệm:
- **Baseline:** Chạy dữ liệu sạch hoàn hảo.
- **Corrupted:** Cố tình xóa cột "Summary", tiêm chữ rác (Noise) vào dữ liệu, và sửa đổi năm xuất bản thành quá khứ.
- **Repaired:** Kỹ sư dữ liệu can thiệp và khôi phục dữ liệu về nguyên bản.

👉 *Mục đích: Quan sát xem Bot AI sẽ cư xử tệ hại như thế nào khi tìm kiếm trên tập dữ liệu bị "đầu độc".*

---

# 4. Vai Trò Của Data Observability

Sử dụng thư viện **Great Expectations (GX 1.x)** để lập ra bộ luật (Expectations):
- Bắt buộc phải có Tiêu đề (Title) và Tóm tắt (Summary).
- Độ dài Tóm tắt không được quá ngắn (< 50 ký tự) hoặc quá dài.
- ID bài báo không được trùng lặp.
- Dữ liệu không được quá hạn (Freshness < 1000 ngày).

👉 *Kết quả: Khi tiêm dữ liệu bẩn, Quality Gate lập tức cảnh báo tỉ lệ Success giảm từ 5/6 xuống còn 3/6.*

---

# 5. Kết Quả & Đánh Giá AI

| Chỉ số AI (Metric) | Baseline (Chuẩn) | Corrupted (Lỗi) | Repaired (Đã Sửa) |
| :--- | :---: | :---: | :---: |
| **Tỉ lệ tìm đúng tài liệu (Hit Rate)** | 1.0 (100%) | 0.5 (50%) | 1.0 (100%) |
| **Độ chính xác của Giám Khảo AI** | 50% | 25% | 50% |
| **Điểm số trung bình (Mean Score)** | 2.5 | 1.75 | 2.5 |
| **Tình trạng Dữ liệu (Quality Pass)** | 5/6 | 3/6 | 5/6 |

**👉 Nhận xét:** Khi dữ liệu bị lỗi, Bot tìm sai tài liệu (rớt 50% hit rate) dẫn đến việc trả lời sai hoàn toàn. Sau khi Data Engineer khôi phục dữ liệu, bot thông minh trở lại.

---

# 6. Bài Học Rút Ra (Lesson Learned)

1. **RAG Model = Data + LLM.** LLM dù mạnh cỡ nào (như GPT-4, Gemini Flash) nhưng nếu dữ liệu (Vector) đưa vào bị nhiễu, nó cũng chỉ trả lời sai hoặc chém gió (Garbage In, Garbage Out).
2. **Data Observability là tấm khiên thép.** Việc check chất lượng dữ liệu tự động giúp chặn đứng rác trước khi nó chui vào Database và phá hỏng cả hệ thống AI.
3. Kỹ năng làm việc nhóm trên cùng một Pipeline, giải quyết các rắc rối về Môi trường (Environment), Dependencies và Data Types (Timezone/Timestamp).

---

# Cảm Ơn Thầy & Các Bạn Đã Lắng Nghe!
## Q & A
