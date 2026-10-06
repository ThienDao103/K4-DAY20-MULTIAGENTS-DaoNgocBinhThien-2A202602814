# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Đào Ngọc Bình Thiên | 2A202602814 | 100% |

- Nhà cung cấp và mô hình: Google Gemini (`google_genai:gemini-3.1-flash-lite`), nhiệt độ (`LAB_TEMPERATURE=0`), `recursion_limit=60`
- Phiên bản Deep Agents (`deepagents 0.7.21`), hệ điều hành Windows 11, chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 25
- Commit của tag `freeze`: (sẽ cập nhật sau khi tạo tag freeze)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): `subagents` sẽ đạt điểm tương đương `baseline` trên các tác vụ đánh giá (chênh lệch không đáng kể), nhưng chi phí token sẽ cao hơn gấp 2 đến 3 lần. Căn cứ: theo kết quả tập học (17/18 check kỹ thuật đạt ở cả 2 điều kiện), tác tử không gặp khó khăn về khả năng giải quyết vấn đề kỹ thuật mà chủ yếu thất bại ở các quy ước tổ chức ngầm (`house rules`). Việc chia nhỏ việc cho subagent không cung cấp thêm tri thức thủ tục mà chỉ gia tăng overhead phân rã và truyền thông tin qua lại.
- H2 (skills-auto so với baseline): `skills-auto` sẽ đạt điểm cao hơn `baseline` trên các check quy ước lặp lại giữa tập học và tập đánh giá (ví dụ type annotations, changelog format, cents formatting), nhưng sẽ không cải thiện đối với các quy ước hoàn toàn mới của tập đánh giá. Căn cứ: nghiên cứu SkillEvolBench chỉ ra rằng các kỹ năng tự sinh từ phản hồi của tập học có xu hướng khớp với các quy ước đã quan sát và khó khái quát hóa sang quy ước chưa từng gặp (overfitting ở tầng ngữ cảnh).
- H3 (tác vụ học so với tác vụ đánh giá): Điểm trung bình của `skills-auto` trên tác vụ đánh giá sẽ thấp hơn trên tác vụ học. Căn cứ: tập đánh giá đưa vào các quy tắc kiểm tra mới độc lập mà bộ tuyển chọn (Curator) chưa từng được học; ngoài ra việc đọc thêm skill có thể gây phân mảnh ngữ cảnh khiến tác tử tốn thêm bước gọi công cụ dẫn tới chạm giới hạn đệ quy ở một số tác vụ phức tạp.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: 7 công cụ tệp (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`), 1 công cụ shell (`execute`) và 1 công cụ subagent (`task`). Công cụ cho phép chạy lệnh shell trên hệ thống là `execute`.
2. Mô tả của công cụ `task` nêu rằng subagent `general-purpose` được dùng để nghiên cứu các câu hỏi phức tạp, tìm kiếm tệp/nội dung và thực thi tác vụ nhiều bước khi không chắc chắn tìm đúng ngay lần đầu; nó có quyền truy cập tất cả công cụ như tác tử chính. Subagent này hoàn toàn bị cô lập ngữ cảnh (mặc định stateless), chỉ nhìn thấy nội dung prompt mà tác tử chính truyền sang và trả về một báo cáo duy nhất, không thấy ngữ cảnh hội thoại trước đó của tác tử chính.
3. - Câu hướng dẫn hành vi từ mô tả công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."*
   - Câu hướng dẫn hành vi từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `tests_not_modified` | C | "the original files in tests/ must not be modified (new test files are allowed)": Tác tử sửa trực tiếp file test trong `tests/` để pass kiểm tra thay vì sửa logic trong package. |
| `code-learn` | `rule_type_hints` | E | "RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value." |
| `code-learn` | `rule_regression_tests` | E | "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass." |
| `code-learn` | `rule_changelog` | E | "RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets)." |
| `data-learn` | `rule_money_in_cents` | E | "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)." |
| `data-learn` | `rule_meta_block` | E | "RULE: answer.json has an object `meta` = {\"source\": <input file name>, \"rows_in\": <number of data rows in the input file, duplicates included>, \"rows_used\": <number of distinct orders with a known amount>}." |
| `data-learn` | `rule_clean_csv` | E | "RULE: save cleaned data to workspace/clean.csv with ISO dates (YYYY-MM-DD) and normalized column names." |
| `logs-learn` | `rule_service_names` | E | "RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)." |
| `logs-learn` | `rule_sorted_errors` | E | "RULE: `errors` is sorted by service, then by timestamp_utc, ascending." |
| `logs-learn` | `rule_schema_header` | E | "RULE: the top-level object has \"schema_version\": 2 and \"generated_by\": \"log-triage\"." |

Nhận xét:
- Nhóm lỗi chiếm đa số tuyệt đối là **Nhóm E (Vi phạm quy ước tổ chức)** với 9/10 check thất bại.
- Bằng chứng phủ định: Tác tử đạt 17/18 check kỹ thuật (nhóm A, B, D) từ `scripts/check_breakdown.py`, chứng tỏ mô hình có năng lực phân tích dữ liệu, đọc hiểu logic và lập trình rất tốt; lỗi duy nhất xuất phát từ việc đề bài không cung cấp các quy ước nội bộ của tổ chức.
- Một skill hoàn toàn có thể phòng ngừa nhóm lỗi E vì đây là các quy ước thủ tục (procedural checklist) có thể ghi nhớ vào ngữ cảnh để tác tử tuân theo.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa:
  1. `explorer`: Phân tích cấu trúc thư mục làm việc, kiểm tra dữ liệu/docstring mà không sửa đổi tệp tin. Dùng khi bắt đầu tác vụ để nắm bắt bối cảnh.
  2. `implementer`: Trực tiếp chỉnh sửa mã nguồn, biến đổi tệp tin và chạy các lệnh kiểm thử theo kế hoạch.
  3. `reviewer`: Kiểm tra độc lập sản phẩm đầu ra, đối chiếu các trường hợp biên và kiểm tra tính toàn vẹn của tệp kết quả trước khi kết thúc tác vụ.
- `subagent_calls` ở từng tác vụ:
  - `code-learn`: 5 lần gọi subagent. Tác tử chính phân rã việc khám phá lỗi, chỉnh sửa từng hàm và kiểm tra test sang cho subagents.
  - `data-learn`: 1 lần gọi subagent (`explorer` để phân tích cấu trúc dữ liệu bán hàng).
  - `logs-learn`: 2 lần gọi subagent (`implementer` để parse logs và `reviewer` để kiểm tra kết quả).
- Thông tin khi giao việc: Tác tử chính truyền khá chi tiết đường dẫn và yêu cầu sang subagent. Tuy nhiên do subagent bị cô lập ngữ cảnh (stateless), tác tử chính phải tóm tắt lại các chỉ thị từ đầu, dẫn đến hiện tượng dư thừa thông tin lặp lại trong các lời gọi.
- Ảnh hưởng đến token và thời gian: Số token trung bình tăng từ 156,102 (`baseline`) lên 420,094 (`subagents`) - tăng gấp 2.69 lần. Thời gian thực thi cũng tăng tương ứng (ví dụ `logs-learn` từ 53.1s lên 297.7s) do overhead gọi và chờ phản hồi từ các subagents.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: Chạy curator 1 lần (`python -m lab.curator`), sinh ra 3 skill; 0 skill bị xóa vì cả 3 đều tuân thủ chặt chẽ định dạng YAML frontmatter, độ dài < 80 dòng, và không chứa bất kỳ từ khóa cấm/dấu hiệu rò rỉ nào từ tập đánh giá (`eval_markers()`).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `enforce-python-type-hints` | Tổng quát cho tất cả các package Python cần quy chuẩn type annotations. | Đúng hoàn toàn: hướng dẫn thêm type hints cho hàm public và chạy kiểm tra. | 11 dòng; `description`: "Use when writing or modifying Python packages that require strict public function type annotations."; `skills_read` = 1 (`code-learn`). |
| `regression-testing-and-changelog-discipline` | Tổng quát cho quy trình vá lỗi phần mềm và duy trì lịch sử thay đổi. | Đúng hoàn toàn: không sửa test gốc, tạo `tests/test_regressions.py`, ghi `CHANGELOG.md` dưới mục `## Unreleased`. | 11 dòng; `description`: "Use when fixing bugs or implementing code changes that require regression tests and changelog entries."; `skills_read` = 1 (`code-learn`). |
| `robust-data-cleaning-and-output-formatting` | Tổng quát cho các tác vụ xử lý bảng dữ liệu, chuẩn hóa số liệu tài chính và định dạng đầu ra. | Đúng: quy đổi tiền tệ sang integer cents, bổ sung khối metadata. | 11 dòng; `description`: "Use when processing CSV datasets, cleaning categorical/numeric fields, and writing structured JSON/CSV reports."; `skills_read` = 1 (`data-learn`). |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
