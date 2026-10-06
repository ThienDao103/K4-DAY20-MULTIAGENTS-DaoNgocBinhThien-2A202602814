"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    target_out_dir = Path(out_dir) if out_dir is not None else (ROOT / "skills" / "auto")
    base_res = Path(results_dir) / source_condition

    runs = []
    if base_res.exists():
        for run_file in sorted(base_res.glob("*/run.json")):
            try:
                r = json.loads(run_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if r.get("role") != "learn":
                continue
            trace_file = run_file.parent / "trace.md"
            trace_text = ""
            if trace_file.exists():
                try:
                    trace_text = trace_file.read_text(encoding="utf-8")
                except Exception:
                    pass
            failed = [
                (c.get("name", ""), c.get("detail", ""))
                for c in r.get("checks", [])
                if not c.get("passed")
            ]
            runs.append({
                "task": r.get("task", run_file.parent.name),
                "failed": failed,
                "trace": trace_text,
            })

    if not any(run["failed"] for run in runs):
        print("Warning: Không có check thất bại ở tác vụ học. Bỏ qua gọi mô hình.")
        return []

    llm = model if model is not None else make_model()

    run_blocks = []
    for run in runs:
        if not run["failed"]:
            continue
        failed_lines = []
        for name, detail in run["failed"]:
            line = f"- Check '{name}' failed"
            if detail:
                line += f": {detail}"
            failed_lines.append(line)
        block = f"Task: {run['task']}\nFailed checks:\n" + "\n".join(failed_lines)
        if run["trace"]:
            block += f"\nRecent trace snippet:\n{run['trace'][-6000:]}"
        run_blocks.append(block)

    runs_text = "\n\n".join(run_blocks)
    prompt = (
        f"You are an expert engineer writing reusable procedural SKILLS for coding and data analysis agents.\n"
        f"Below are failed checks (names and review bot feedback) and execution traces from previous learning runs.\n"
        f"Identify common procedural errors and house rules violated (not task-specific hardcoded answers) "
        f"and write up to {max_skills} concise skills to help future agents avoid these mistakes on new tasks.\n\n"
        f"Rules:\n"
        f"- Generalize: Do not mention specific task IDs, hardcoded numbers, or specific file names unique to a single run. Do not use words like 'orders', 'worker', 'bookings'; use generic terms like 'records', 'items', 'entries', 'tasks', 'processes'.\n"
        f"- Each skill must have YAML frontmatter with `name` (lowercase alphanumeric with hyphens, max 64 chars) and `description` (one sentence: 'Use when ...'), followed by at most 40 lines of imperative procedural guidelines.\n"
        f"- Output format (strictly follow this block delimiter):\n"
        f"=== SKILL: <name> ===\n"
        f"---\n"
        f"name: <name>\n"
        f"description: Use when <trigger condition>\n"
        f"---\n"
        f"# <Title>\n\n"
        f"1. Step 1...\n"
        f"2. Step 2...\n"
        f"=== END ===\n\n"
        f"Failed runs:\n{runs_text}"
    )

    reply = llm.invoke(prompt)
    if hasattr(reply, "content"):
        if isinstance(reply.content, list):
            reply_text = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in reply.content)
        else:
            reply_text = str(reply.content)
    else:
        reply_text = str(reply)

    written = []
    for name, text in parse_skill_blocks(reply_text):
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        target = target_out_dir / name / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text.strip() + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)

