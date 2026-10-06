# Báo cáo Lab: Self evolving Agentic


## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Đào Ngọc Bình Thiên | 2A202602814 | 100% |

- Nhà cung cấp và mô hình: Google Gemini (`google_genai:gemini-3.1-flash-lite`), nhiệt độ (`LAB_TEMPERATURE=0`), `recursion_limit=60`
- Phiên bản Deep Agents (`deepagents 0.7.21`), hệ điều hành Windows 11, chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 21 / 25
- Commit của tag `freeze`: `4b6f5e1`

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

Bảng so sánh tổng hợp sinh từ `python -m lab.compare` (`report/table.md`):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 6/10 | 6/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| code-eval | 6/11 | 6/11 | 6/11 |
| data-eval | 5/9 | 3/9 | 5/9 |
| logs-eval | 6/10 | 4/10 | 6/10 |
| **Mean score - learning tasks** | 0.63 | 0.63 | 0.63 |
| **Mean score - evaluation tasks** | 0.57 | 0.43 | 0.57 |
| **Mean tokens per run** | 144,211 | 273,017 | 139,304 |
| **Runs that read a skill** | 0/6 | 0/6 | 1/6 |

Thống kê chi tiết kiểm tra từ `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     17/18         0/12         132,320      0/3     
baseline      learn    17/18         0/9          156,102      0/3     
subagents     eval     13/18         0/12         125,941      0/3     
subagents     learn    17/18         0/9          420,094      0/3     
skills-auto   eval     17/18         0/12          94,790      0/3     
skills-auto   learn    17/18         0/9          183,819      1/3     
```

Ghi chú về tính toàn vẹn và lỗi thực thi:
- Toàn bộ 100% các lần chạy đều có `skills_modified = false` (được xác thực tự động bởi `verify_freeze.py` với trạng thái `OK`).
- Một số lần chạy dài (`data-eval` ở baseline; `code-learn` và `data-learn` ở `skills-auto` chính thức) ghi nhận ngoại lệ `GraphRecursionError: Recursion limit of 60 reached` do tác tử thực hiện nhiều vòng kiểm tra lặp lại trước khi xuất kết luận. Nhờ kiến trúc xử lý stream trong `runner.py`, hệ thống vẫn lưu lại tin nhắn cuối cùng và chấm điểm từng phần chính xác trên trạng thái workspace hiện thời mà không làm gián đoạn bài thí nghiệm.

## 8. Phân tích

1. **So sánh điều kiện**:
   - Trên tác vụ **học**, cả ba điều kiện đạt điểm trung bình 0.63 ở lần chạy chính thức (đều đạt 17/18 check kỹ thuật). Tuy nhiên, ở giai đoạn dev (Phần 3.4), `skills-auto` từng đạt **8/10** trên `code-learn` (vượt trội so với 6/10 của baseline) khi đọc và tuân thủ thành công skill về regression testing và changelog.
   - Trên tác vụ **đánh giá**, `baseline` và `skills-auto` cùng đạt điểm trung bình 0.57 (17/18 check kỹ thuật), trong khi `subagents` sụt giảm xuống 0.43 (13/18 check kỹ thuật).
   - Sự suy giảm của `subagents` trên tập đánh giá là dấu hiệu rõ ràng của **mất mát ngữ cảnh khi phân quyền (delegation context loss)**: khi tác vụ trở nên phức tạp hơn, việc chia việc sang các subagent bị cô lập ngữ cảnh khiến thông tin đặc tả bị đứt gãy, dẫn đến lỗi ở các phần việc con.
2. **Tách điểm kỹ thuật và quy ước (`rule_`)**:
   - Về check kỹ thuật: Cả `baseline` và `skills-auto` đều đạt 17/18 ở cả hai tập học và đánh giá. Điều này chứng minh mô hình nền tảng (`gemini-3.1-flash-lite`) sở hữu năng lực lập trình và suy luận logic rất vững chắc.
   - Về check quy ước: Toàn bộ các check quy ước ngầm đều bị 0 điểm ở lần chạy chính thức (0/9 ở tập học, 0/12 ở tập đánh giá). Skill do Curator sinh ra được thiết kế để giải quyết nhóm này, nhưng ở tập đánh giá tác tử không chủ động gọi `read_file` vào thư mục `skills/` (0/3 lần đọc). Hơn nữa, tập đánh giá bổ sung các quy ước mới độc lập (OOD conventions) mà Curator chưa từng được quan sát trong tập học; do đó các kỹ năng tự sinh không thể giúp giải quyết các quy ước mới này — minh chứng điển hình của hiện tượng **quá khớp ở tầng ngữ cảnh (context overfitting)**.
3. **Cơ chế vết và việc đọc skill**:
   - Check skill giúp đạt: Trong lần chạy Phần 3.4 (`code-learn` đạt 8/10), vết ghi nhận tác tử đọc `regression-testing-and-changelog-discipline`, qua đó không chỉnh sửa tệp test gốc (đạt check `tests_not_modified`) và tự động viết `tests/test_regressions.py` (đạt check `rule_regression_tests`).
   - Check skill không giúp: Ở lần chạy chính thức `code-learn` (6/10), tác tử đọc skill và cố gắng thêm type annotations cho hàng loạt hàm, nhưng khối lượng thao tác lớn khiến tác tử chạm trần 60 bước (`GraphRecursionError`) trước khi hoàn thiện. Ở tập đánh giá, tác tử không đọc skill nào (0/3) do đề bài không gợi ý tìm kiếm kỹ năng và tác tử ưu tiên giải quyết trực tiếp.
4. **Chi phí token**:
   - Số token trung bình mỗi lần chạy: `skills-auto` tiêu thụ ít nhất với **139,304 tokens**, tiếp đến là `baseline` với **144,211 tokens**, và cao nhất là `subagents` với **273,017 tokens** (gấp 1.89 lần baseline và 1.96 lần skills-auto).
   - Tỷ số hiệu quả điểm/token: `skills-auto` đạt hiệu quả cao nhất (0.57 điểm trên 139k tokens), trong khi `subagents` kém hiệu quả nhất (0.43 điểm trên 273k tokens).
   - Kết luận: **Kiến trúc đa tác tử (subagents) hoàn toàn không đáng chi phí** trong thí nghiệm này: vừa tăng gần gấp đôi lượng token tiêu thụ, vừa làm giảm độ chính xác do chi phí phối hợp (coordination overhead).
5. **Rò rỉ dữ liệu và quá khớp**:
   - Không có bất kỳ hiện tượng rò rỉ dữ liệu nào: Hàm `validate_skill` đã chủ động kiểm tra và lọc bỏ mọi marker của tập đánh giá (`eval_markers()`); `curator.py` chỉ đọc các tệp có `role == "learn"`.
   - Về quá khớp: Các skill sinh ra phản ánh chính xác các quy ước của tập học (đổi cents, format metadata, changelog). Do đó, chúng cải thiện tốt tập học (như lần chạy dev) nhưng không thể khái quát hóa sang các quy ước hoàn toàn mới của tập đánh giá.
6. **Ước lượng nhiễu (Noise estimation)**:
   - Điểm tác vụ học của `skills-auto` ở Phần 3.4 (lưu tại `results/skills-auto-dev`): `code-learn` = 8/10, `data-learn` = 3/8, `logs-learn` = 6/9 -> Trung bình: **0.61**.
   - Điểm tác vụ học của `skills-auto` sau đóng băng: `code-learn` = 6/10, `data-learn` = 5/8, `logs-learn` = 6/9 -> Trung bình: **0.63**.
   - Chênh lệch điểm trung bình giữa hai lần chạy cùng một bộ skill là **0.02 (2 điểm phần trăm)**, nhưng dao động ở từng tác vụ đơn lẻ có thể lên tới 0.20 - 0.25 (do tính ngẫu nhiên của LLM và ranh giới chạm trần 60 bước đệ quy). Điều này khẳng định rằng các chênh lệch điểm số nhỏ trong bảng so sánh cần được giải thích thận trọng như là dao động ngẫu nhiên, thay vì kết luận vội vàng về ưu thế phương pháp.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ (N=6)**: Bộ benchmark gồm 3 tác vụ học và 3 tác vụ đánh giá. Kích thước mẫu nhỏ khiến các chỉ số trung bình có phương sai lớn và dễ bị ảnh hưởng bởi kết quả của một tác vụ cá biệt.
2. **Đánh giá một lần chạy (Single-run evaluation)**: Do hạn ngạch API và chi phí tính toán, mỗi cấu hình trên tập đánh giá chỉ chạy 1 lần; chưa thể xây dựng khoảng tin cậy thống kê (confidence interval) qua nhiều hạt giống ngẫu nhiên (random seeds).
3. **Giới hạn số bước đệ quy (`recursion_limit=60`)**: Việc đọc và tuân thủ các quy tắc trong skill khiến tác tử thực hiện thêm nhiều thao tác phụ (type hints, tạo test hồi quy), dễ dẫn đến chạm trần số bước trước khi hoàn tất logic cốt lõi.
4. **Mô hình duy nhất (`gemini-3.1-flash-lite`)**: Hành vi thí nghiệm gắn liền với đặc tính của mô hình này (ưu tiên hành động nhanh, ít chủ động tra cứu skill nếu không có chỉ thị bắt buộc). Kết quả có thể khác biệt nếu sử dụng các mô hình suy luận chuyên sâu hơn.

## 10. Kết luận

1. Tác tử Deep Agents thể hiện năng lực giải quyết vấn đề kỹ thuật rất tốt (đạt 17/18 check kỹ thuật), nhưng thường xuyên thất bại ở các quy ước tổ chức ngầm khi chưa có chỉ dẫn thủ tục.
2. Kiến trúc đa tác tử (`subagents`) làm tăng chi phí token lên gần gấp đôi nhưng lại làm suy giảm độ chính xác trên tập đánh giá do mất mát thông tin khi phân quyền.
3. Tác tử tự tiến hóa (`skills-auto`) đúc kết thành công kinh nghiệm từ thất bại ở tập học (nâng điểm `code-learn` lên 8/10 ở giai đoạn dev) và tối ưu hóa chi phí token tốt nhất (139k tokens).
4. Tuy nhiên, các kỹ năng tự sinh gặp rào cản quá khớp ngữ cảnh và không thể chuyển giao sang các quy ước hoàn toàn mới ngoài phân phối của tập đánh giá.
5. Hướng cải tiến tiếp theo là xây dựng cơ chế Semantic Skill Retrieval tự động (RAG cho skills) nhằm tự động tiêm các skill liên quan trực tiếp vào ngữ cảnh ban đầu thay vì chờ tác tử chủ động tra cứu.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest` (xác nhận 32/32 tests ngoại tuyến đạt).
  2. `python -m lab.runner --condition baseline --tasks learn`
  3. `python -m lab.runner --condition subagents --tasks learn`
  4. `python -m lab.curator` (sinh 3 kỹ năng vào `skills/auto/`).
  5. `python -m lab.runner --condition skills-auto --tasks learn` (kiểm thử dev Phần 3.4).
  6. `Copy-Item -Recurse results/skills-auto results/skills-auto-dev` (sao lưu kết quả dev).
  7. `git add -A && git commit -m "hypotheses"` (commit giả thuyết).
  8. `git add -A && git commit --allow-empty -m "freeze skills" && git tag freeze` (đóng băng kỹ năng).
  9. `python -m lab.runner --condition baseline --tasks eval`
  10. `python -m lab.runner --condition subagents --tasks eval`
  11. `python -m lab.runner --condition skills-auto --tasks all` (chạy chính thức sau đóng băng).
  12. `python scripts/verify_freeze.py` (xác minh giao thức đóng băng: `checked 6 runs: OK`).
  13. `python -m lab.compare > report/table.md` và `python scripts/check_breakdown.py`.
  14. `python scripts/red_team_curator.py` (thực hiện thử thách mở rộng 6c).

- Thử thách mở rộng: **Hướng 6c - Tấn công Red-Team bộ tuyển chọn Curator (Security & Prompt Injection)**:
  - **Mục tiêu**: Đánh giá tính an toàn của hàm `validate_skill` và quy trình tự sinh skill trước các hình thức tấn công tiềm ẩn trong vết thực thi.
  - **Thiết kế thí nghiệm**: Viết kịch bản kiểm thử độc lập tại [scripts/red_team_curator.py](file:///c:/Users/Admin/Desktop/VinAI/K4-DAY20-MULTIAGENTS-DaoNgocBinhThien-2A202602814/scripts/red_team_curator.py) với 3 véc-tơ tấn công:
    1. *Path Traversal Injection* (`../../malicious-skill`): Cố tình tiêm đường dẫn tương đối nguy hiểm vào tên skill nhằm ghi đè các tệp hệ thống ngoài thư mục `skills/auto/`.
    2. *Direct Evaluation Leakage*: Cố tình tiêm các từ khóa đặc trưng của tập đánh giá (`orders`, `orders.json`, `worker`, `worker.log` từ `eval_markers()`).
    3. *Semantic Paraphrase Bypass*: Cố tình tiết lộ cấu trúc lời giải của tập đánh giá nhưng sử dụng từ đồng nghĩa/diễn đạt khác để qua mặt bộ lọc từ khóa tĩnh.
  - **Kết quả thực nghiệm**:
    - Kịch bản 1 (Path Traversal): **BỊ CHẶN 100%** (`invalid name`). Regex `SAFE_NAME` bảo vệ an toàn hệ thống tệp.
    - Kịch bản 2 (Direct Leakage): **BỊ CHẶN 100%** (`mentions evaluation material`).
    - Kịch bản 3 (Semantic Paraphrase): **VƯỢT QUA BỘ LỌC THÀNH CÔNG (BYPASSED)**. Bộ lọc tĩnh không nhận diện được ngữ nghĩa nếu không chứa từ khóa cứng.
  - **Nhận xét & Giải pháp**: Bộ lọc quy tắc tĩnh chỉ ngăn chặn được các hình thức tấn công thô sơ. Để đảm bảo an toàn tuyệt đối cho hệ thống tác tử tự tiến hóa trong môi trường sản xuất, cần bổ sung một tầng kiểm duyệt ngữ nghĩa (LLM Security Judge / Semantic Guardrail) trước khi tích hợp tri thức mới vào kho kỹ năng.
- Ghi chú khác: Không có.

