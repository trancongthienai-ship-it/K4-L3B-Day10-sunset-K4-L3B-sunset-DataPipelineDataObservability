# Thiết kế bổ sung đủ yêu cầu bắt buộc

## Mục tiêu

Hoàn thiện các yêu cầu bắt buộc trong `README.md`, `docs/CHECKPOINTS.md`, `docs/RUBRIC.md` và `docs/SUBMISSION.md` trên branch `tranthai239`. Giữ nguyên phần vượt yêu cầu nếu không cản trở nghiệm thu. Không sửa `main` hoặc branch thành viên khác.

## Phạm vi

### 1. Cleaning contract 5 phần

`text_for_embedding` phải gồm đủ năm phần có sẵn trong dữ liệu sạch:

1. `paper_id`
2. `title`
3. `authors_joined`
4. `categories_joined`
5. `summary`

Dùng cùng một hàm dựng text cho baseline, corrupted và repaired để tránh lệch contract. Không thêm dependency hoặc abstraction ngoài nhu cầu này.

### 2. Great Expectations và Freshness SLA

Quality gate giữ tối thiểu bốn loại expectation bắt buộc:

- row count hợp lệ;
- `paper_id` không null;
- `paper_id` unique;
- độ dài `summary` hợp lệ.

Có thể giữ thêm check title. Freshness không yêu cầu mọi record trẻ hơn 180 ngày. Báo cáo tính:

- `stale_rows`: số dòng có `age_days > freshness_threshold_days`;
- `stale_ratio`: `stale_rows / total_rows`, hoặc `0.0` khi dataset rỗng;
- `is_fresh`: `stale_ratio <= 0.25`.

Quality gate thêm expectation theo tỷ lệ để baseline có thể pass khi tối đa 25% record stale, còn corruption vẫn bị phát hiện qua các check khác.

### 3. Evaluation set

Giữ bộ 16 câu hiện tại vì đã phủ đủ bốn loại `summary`, `authors`, `date`, `categories`, vượt mức tối thiểu 10 câu. Không giảm dữ liệu chỉ để khớp ví dụ checkpoint. Baseline, corrupted và repaired tiếp tục dùng đúng cùng file `data/eval/test_set.json`.

### 4. Sáu corruption scenarios và log

Giữ đủ sáu lỗi bắt buộc:

- drop latest 20%;
- blank summary;
- inject noise;
- truncate title xuống dưới 8 ký tự;
- stale published date;
- duplicate row.

Sửa drop từ số cố định sang 20% số dòng. Stale corruption thay đổi cả `published` và `age_days`, không chỉ sửa derived field. Sau corruption, dựng lại `text_for_embedding` bằng cùng contract 5 phần.

`corruption_log.json` ghi từng scenario với loại lỗi, record IDs bị tác động, số lượng và tham số cần thiết. Giữ các trường tổng hợp cũ nếu hữu ích.

### 5. Repair và artifacts

Repair tiếp tục tái dựng dataset từ raw records đáng tin cậy qua `build_clean_dataframe()`. Chạy lại repair phải cho cùng dữ liệu theo cùng `run_date`, không cộng dồn corruption. Pipeline phải sinh đủ:

- baseline/corrupted/repaired clean data;
- ba vector collections/manifests;
- ba answer/metrics files;
- baseline/corrupted/repaired quality và freshness reports;
- `phase1_report.md`;
- `corruption_report.md` có bảng ba trạng thái.

Không sửa tay metrics do pipeline sinh.

### 6. Báo cáo

Điền `report/group_report.md` từ code, config và artifact đã xác minh. Không bịa trạng thái chạy. Nếu full pipeline chưa chạy được vì dependency hoặc mạng, ghi đúng blocker thay vì đánh dấu thành công.

Báo cáo cá nhân của Trần Thanh Thái chỉ cập nhật khi metrics hoặc freshness mới khác số hiện tại.

### 7. Kiểm thử và bảo mật

Thêm test nhỏ, không thêm framework, cho:

- cleaning tạo đủ năm phần;
- freshness pass ở đúng 25% và fail khi vượt 25%;
- corruption tạo đủ sáu scenario, drop 20%, title ngắn, stale date và log record IDs;
- repair determinism ở cấp hàm nếu phù hợp.

Xác minh theo thứ tự:

1. toàn bộ `pytest`;
2. compile các Python file thay đổi;
3. checkpoint import dependencies;
4. `python script/run_phase1.py`;
5. `python script/run_corruption_flow.py`;
6. đối chiếu artifacts và reports;
7. scan source, tracked files và Git history cho tên secret phổ biến mà không in giá trị bí mật;
8. `git diff --check` và `git status`.

## Ngoài phạm vi

- Không xây dashboard hoặc bonus feature.
- Không đổi provider/model nếu cấu hình hiện tại chạy được.
- Không giảm test set 16 câu.
- Không merge hoặc push vào `main`.
- Không thực hiện live demo hay nộp LMS thay người dùng.
- Không che giấu lỗi dependency, mạng hoặc credential.

## Tiêu chí hoàn thành

Code đáp ứng đủ tiêu chí bắt buộc có thể kiểm tra trong repository; tests xanh; hai entrypoint exit code 0 nếu môi trường đầy đủ; artifacts khớp code và reports; không phát hiện secret đã commit; thay đổi chỉ được commit và push lên `tranthai239`. Các bước bên ngoài repository — live demo, merge vào `main`, Contributors và nộp LMS — được liệt kê rõ để nhóm thực hiện.