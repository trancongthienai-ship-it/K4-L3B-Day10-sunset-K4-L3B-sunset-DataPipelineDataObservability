# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Thanh Thái |
| MSSV | 2A202602454 |
| Khóa/Lớp | K4 |
| Tên nhóm | sunset |
| Vai trò chính | RAG & Vector Index |
| Repository | [K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability](https://github.com/trancongthienai-ship-it/K4-L3B-Day10-sunset-K4-L3B-sunset-DataPipelineDataObservability) |
| Branch cá nhân | `tranthai239` |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Khởi tạo và lưu Vector DB | `src/retrieval/index.py` — `LocalEmbeddingIndex.build`, `load`, `search`, `lookup` | DataFrame sạch có `paper_id`, `title`, `text_for_embedding` và metadata | ChromaDB tại `data/chroma/`, manifest embedding JSON và kết quả Top-K | Hoàn thành |
| Embedding | `src/retrieval/embeddings.py` — `MiniLMEmbeddings` | Danh sách văn bản hoặc một query | Vector chuẩn hóa từ SentenceTransformers | Hoàn thành |
| Agent logic | `src/retrieval/agent.py` — `build_agent`, `run_agent_question` | Câu hỏi người dùng và `LocalEmbeddingIndex` | Câu trả lời có dữ liệu từ công cụ semantic search/lookup | Hoàn thành |
| QA extraction | `src/retrieval/qa.py` — `answer_question`, `_extract_answer` | Câu hỏi và kết quả Top-K | Câu trả lời đúng trường summary/authors/date/categories cùng nguồn đã truy xuất | Hoàn thành |
| LLM adapter | `src/retrieval/llm.py` — `build_llm` | Cấu hình provider/model trong `Settings` | LangChain chat model tương ứng | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| --- | --- | --- |
| Hỗ trợ cấu hình LLM qua `.env` | Thiện và phần evaluation | `build_llm()` đọc provider/model từ `Settings`; secret không được ghi vào repository |
| Cải thiện ingestion Crossref | Module ingestion | Commit `3cc84bf`; bổ sung normalize, retry và fallback snapshot, có test tự động |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Tạo collection ChromaDB persistent | `src/retrieval/index.py`, `data/chroma/` | Collection baseline, corrupted và repaired lưu trên đĩa | Chạy `python script/run_phase1.py`; kiểm tra `data/chroma/chroma.sqlite3` |
| Sinh embedding và manifest | `src/retrieval/embeddings.py`, `data/embeddings/*.json` | Model, collection name, persist path và documents dùng để tái nạp index | Mở `data/embeddings/papers_embeddings.json` |
| Truy xuất semantic Top-K | `LocalEmbeddingIndex.search()` | Danh sách `SearchResult` gồm DOI, title, score, content và metadata | Đối chiếu `retrieved_doc_ids` trong `data/results/baseline_answers.json` |
| Hỗ trợ agent gọi công cụ retrieval | `src/retrieval/agent.py` | Hai tool: `semantic_search_papers` và `lookup_paper` | Gọi `build_agent()` với index đã load và đặt câu hỏi mẫu |
| Đánh giá retrieval | `data/results/*_metrics.json` | Baseline hit rate `1.0`, corrupted `0.5`, repaired `1.0` | Đối chiếu ba file metrics |

Artifact cụ thể của phần việc là `data/embeddings/papers_embeddings.json`, collection trong `data/chroma/`, cùng `retrieved_doc_ids` và `retrieved_contexts` trong `data/results/baseline_answers.json`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Tìm kiếm keyword không nhận ra tốt các câu hỏi diễn đạt khác văn bản gốc. Phần retrieval cần chuyển tài liệu và query sang cùng không gian vector, tìm các bài báo gần nhau về ngữ nghĩa, rồi cung cấp context có nguồn cho QA hoặc agent.

### Cách triển khai

1. Ghép `title`, `authors_joined` và `summary` thành `text_for_embedding` ở bước cleaning.
2. Dùng SentenceTransformers qua `MiniLMEmbeddings`; vector được normalize để phù hợp cosine similarity.
3. Tạo ChromaDB collection persistent với HNSW cosine tại `data/chroma/`.
4. Lưu mỗi document cùng `paper_id`, title, ngày xuất bản, tác giả, category và URL dưới dạng metadata primitive.
5. Khi nhận query, embed query, gọi ChromaDB lấy Top-K và đổi cosine distance thành score bằng `1 - distance`.
6. Agent có thể semantic search cho câu hỏi mở hoặc exact lookup theo DOI/title. Nếu corpus không có kết quả, tool trả thông báo rõ thay vì chuỗi rỗng.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Pandas DataFrame có `paper_id`, `title`, `text_for_embedding`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url` |
| Output | `LocalEmbeddingIndex`; mỗi truy vấn trả `list[SearchResult]` |
| Module phụ thuộc | `core/config.py`, `core/utils.py`, `pandas`, `chromadb`, `sentence-transformers` |
| Module sử dụng output | `retrieval/qa.py`, `retrieval/agent.py`, `evaluation/metrics.py` |
| Điều kiện lỗi cần xử lý | Timestamp/NaN trong metadata, collection chưa tồn tại, query không có kết quả, provider LLM thiếu credential |

### Cách xác minh

```bash
PYTHONPATH=src python -m pytest tests/test_retrieval.py -q
python script/run_phase1.py
```

- **Kết quả mong đợi:** test metadata và empty-result đều pass; pipeline tạo collection và artifact baseline.
- **Kết quả thực tế:** ngày 2026-09-26, toàn bộ test hiện có chạy `6 passed`; regression test xác nhận metadata, empty-result và cách diễn đạt authors/categories. Lần chạy mới của pipeline bị chặn trước khi thực thi vì `.venv` thiếu package `langchain`, nên metrics bên dưới vẫn là artifacts đã có và không được mô tả là kết quả chạy mới.
- **Artifact/log:** `data/chroma/`, `data/embeddings/papers_embeddings.json`, `data/results/baseline_answers.json`, `data/results/baseline_metrics.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** ChromaDB không nhận Pandas `Timestamp`, `NaN` hoặc `pd.NA` làm metadata.
- **Các phương án đã cân nhắc:**
  1. Chỉ format và `.fillna("")` trong cleaning.
  2. Chuẩn hóa metadata ngay tại boundary `LocalEmbeddingIndex._build_documents()`.
  3. Loại bỏ các trường metadata có giá trị trống.
- **Phương án đã chọn:** Vẫn format ngày tại cleaning, đồng thời chuẩn hóa lần cuối tại Vector Index: Timestamp thành `YYYY-MM-DD`, giá trị thiếu thành chuỗi rỗng, primitive hợp lệ giữ nguyên và kiểu khác đổi thành string.
- **Lý do:** Index là boundary trực tiếp với ChromaDB. Kiểm tra tại đây bảo vệ cả các DataFrame không đi qua cleaning, vẫn giữ schema metadata ổn định cho lookup/filter.
- **Bằng chứng quyết định phù hợp:** `tests/test_retrieval.py::test_build_documents_normalizes_chromadb_metadata_values` kiểm tra Timestamp, `None`, `NaN` và `pd.NA`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValueError: Expected metadata value to be a str, int, float, bool, SparseVector, list, or None, got 2026-07-22 00:00:00 which is a Timestamp in add.`
- **Lệnh hoặc bước tái hiện:** Tạo DataFrame chứa `pd.Timestamp`/`NaN`, gọi `LocalEmbeddingIndex._build_documents()`, rồi truyền metadata vào `collection.add()`.
- **Nguyên nhân gốc:** Pandas giữ kiểu dữ liệu riêng trong record; ChromaDB chỉ serialize metadata primitive.
- **Cách xử lý:** Chuẩn hóa mọi metadata tại `_build_documents()` trước `collection.add()`.
- **Cách xác minh sau khi sửa:** `PYTHONPATH=src python -m pytest tests/test_retrieval.py -q`.
- **Điều học được:** Validation cần đặt tại boundary của hệ thống ngoài, không chỉ phụ thuộc bước xử lý upstream.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref đến vector index:** Crossref payload được parse thành `PaperRecord`, cleaning chuẩn hóa text/ngày và tạo `text_for_embedding`. MiniLM embed trường này; ChromaDB lưu vector, document và metadata. Manifest JSON ghi cấu hình để load lại index.
2. **Evaluation set và ground truth:** Test set chứa question, expected answer và `ground_truth_doc_ids`. Retrieval đúng khi một document ID được lấy ra trùng ground truth. Token F1 và judge so sánh answer với expected answer.
3. **Quality checks và freshness:** Quality checks kiểm tra cấu trúc/nội dung như row count, DOI unique, title/summary hợp lệ. Freshness đo độ mới theo `published` và số row quá SLA. Dữ liệu có thể đúng schema nhưng vẫn stale.
4. **Cùng test set cho ba trạng thái:** Giữ nguyên câu hỏi và ground truth giúp khác biệt metric phản ánh corruption/repair, không phải do đổi mẫu đánh giá.
5. **Tiêu chí repair thành công:** So sánh metrics, quality report và freshness report. Repair phục hồi retrieval hit rate và answer metrics về baseline; quality cũng phục hồi. Freshness hiện vẫn `false` vì còn một record vượt ngưỡng, nên chỉ được kết luận là phục hồi về baseline, không phải đạt mọi quality gate.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | Corruption làm mất một nửa retrieval hit; repair phục hồi hoàn toàn |
| `mean_token_f1` | 0.4218 | 0.2148 | 0.4218 | Answer overlap giảm gần một nửa rồi trở lại baseline |
| `judge_accuracy` | 0.5000 | 0.2500 | 0.5000 | Judge đang dùng fallback heuristic vì LLM evaluator không khả dụng |
| `mean_judge_score` | 2.5000 | 1.7500 | 2.5000 | Cùng xu hướng với token F1 |
| Quality checks | 83.33% | 50.00% | 83.33% | Corruption tạo DOI trùng, summary trống và age bất thường; repair loại các lỗi mới |
| Freshness status | Không đạt, 1 stale row | Không đạt, 2 stale rows | Không đạt, 1 stale row | Repair phục hồi về baseline nhưng baseline vẫn chưa đạt SLA |

### Kết luận từ số liệu

1. Xóa record mới, tạo DOI trùng, làm trống summary và đặt `age_days` bất thường → quality giảm `83.33% → 50%`, stale rows tăng `1 → 2` → retrieval hit giảm `1.0 → 0.5`, token F1 giảm `0.4218 → 0.2148`.
2. Khôi phục dataset và rebuild embedding/index → quality trở lại `83.33%`, stale rows trở lại `1` → retrieval hit và answer metrics trở lại đúng baseline.

Corruption ảnh hưởng rõ nhất là mất/sai nội dung dùng để embedding vì dense retrieval phụ thuộc trực tiếp vào representation của tài liệu. DOI trùng còn làm mapping ground-truth không ổn định; summary trống làm context mất tín hiệu ngữ nghĩa.

Kết quả khác kỳ vọng là retrieval hit baseline đạt `1.0` nhưng answer quality chỉ đạt token F1 `0.4218` và judge accuracy `0.5`. Kiểm tra `baseline_answers.json` cho thấy các câu hỏi authors/categories thường trả summary. Nguyên nhân là `_extract_answer()` chưa nhận cách diễn đạt `Who are the authors...` và `What are the categories...` trong test set; router đã được sửa và có regression test. Chưa cập nhật bảng metrics vì lần chạy pipeline mới bị chặn bởi dependency `langchain` còn thiếu. Ngoài ra, log judge ghi rõ fallback heuristic được dùng; không nên mô tả các answer baseline là output trực tiếp từ OpenAI.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Vector index cần contract dữ liệu rõ và validation ngay trước boundary ChromaDB.
2. Data quality/freshness phải theo dõi cùng retrieval metrics; corruption có thể không làm pipeline crash nhưng vẫn giảm chất lượng RAG mạnh.
3. Retrieval hit cao chỉ chứng minh lấy đúng tài liệu; answer generation/extraction vẫn cần đánh giá riêng.

### Nếu có thêm thời gian

Cải thiện answer routing theo `question_type` hoặc dùng agent/LLM thật để trích xuất authors/categories thay vì mặc định trả câu đầu summary. Đo lại trên cùng test set; mục tiêu giữ retrieval hit `1.0` nhưng tăng `mean_token_f1` và `judge_accuracy`. Đồng thời xử lý record stale còn lại để quality/freshness baseline đạt toàn bộ gate.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải là bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Thanh Thái

**Ngày xác nhận:** 2026-09-26
