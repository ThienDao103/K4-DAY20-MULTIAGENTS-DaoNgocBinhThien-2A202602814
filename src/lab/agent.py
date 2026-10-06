"""GUIDE Phần 1 - Dựng tác tử (agent) bằng Deep Agents.   >>> SINH VIÊN CÀI ĐẶT make_backend VÀ build_agent <<<

Pseudo-code: guides/pseudocode/01_agent.md
Kiểm tra:    pytest tests/test_02_agent.py
"""
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from .model import make_model
from .subagents import get_subagents

# ---- CÓ SẴN, KHÔNG SỬA: system prompt dùng chung cho mọi sinh viên (để đường cơ sở so sánh được) ----
PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)
# --------------------------------------------------------------------------------------------------


class ShLocalShellBackend(LocalShellBackend):
    def execute(self, command: str, *, timeout: int | None = None):
        sh_exe = r"C:\Program Files\Git\bin\sh.exe"
        if sys.platform == "win32" and Path(sh_exe).exists():
            import subprocess
            orig_run = subprocess.run
            def win_run(*a, **k):
                k["shell"] = False
                return orig_run([sh_exe, "-c", command], **k)
            subprocess.run = win_run
            try:
                return super().execute(command, timeout=timeout)
            finally:
                subprocess.run = orig_run
        return super().execute(command, timeout=timeout)


def make_backend(sandbox: Path):
    """Tạo backend (môi trường thực thi) cho tác tử.

    Yêu cầu:
      - Thư mục gốc (root_dir) là `sandbox`; đường dẫn tương đối `workspace/...` và `skills/...`
        phải dùng được ở CẢ công cụ tệp lẫn shell (shell chạy với thư mục làm việc = `sandbox`).
      - Tác tử chạy được lệnh shell và gọi được `python` (cần đặt PATH).
      - KHÔNG chuyển biến môi trường của bạn vào shell của tác tử (khóa API không được lộ).
    """
    python_bin = str(Path(sys.executable).parent)
    bin_dir = sandbox / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    py3_script = bin_dir / "python3"
    if not py3_script.exists():
        py3_script.write_text("#!/bin/sh\nexec python \"$@\"\n", encoding="utf-8")

    if sys.platform == "win32":
        path_parts = [str(bin_dir), python_bin]
        git_usr_bin = Path("C:/Program Files/Git/usr/bin")
        if git_usr_bin.exists():
            path_parts.append(str(git_usr_bin))
        git_bin = Path("C:/Program Files/Git/bin")
        if git_bin.exists():
            path_parts.append(str(git_bin))
        path_parts.extend(["C:/Windows/System32", "C:/Windows"])
        path_str = ";".join(path_parts)
    else:
        path_str = f"{bin_dir}:{python_bin}:/usr/local/bin:/usr/bin:/bin"

    env = {
        "PATH": path_str,
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    return ShLocalShellBackend(
        root_dir=sandbox,
        virtual_mode=True,
        inherit_env=False,
        env=env,
        timeout=120,
    )



def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    """Tạo tác tử Deep Agents.

    Tham số:
      sandbox:    thư mục chứa `workspace/` (và `skills/` nếu có).
      mode:       "single"    -> tác tử mặc định (có subagent `general-purpose` sẵn của Deep Agents)
                  "subagents" -> thêm các subagent từ `get_subagents()` (nối PATHS_NOTE vào `system_prompt` của MỖI subagent,
                                 vì subagent không nhận BASE_PROMPT) và thêm SUBAGENTS_NOTE vào prompt chính
      use_skills: True -> nạp thư mục "/skills/" qua tham số `skills=` của create_deep_agent
                  và thêm SKILLS_NOTE vào prompt.
      model:      mô hình ngôn ngữ; None -> dùng `make_model()`.
    mode không hợp lệ -> ném ValueError.
    Trả về: đồ thị (graph) đã biên dịch, gọi bằng `.invoke({"messages": [...]})`.
    """
    if mode not in {"single", "subagents"}:
        raise ValueError(f"Invalid mode: {mode}. Must be 'single' or 'subagents'.")

    kwargs = {}
    prompt = BASE_PROMPT

    if mode == "subagents":
        kwargs["subagents"] = [
            {**sub, "system_prompt": sub["system_prompt"] + " " + PATHS_NOTE}
            for sub in get_subagents()
        ]
        prompt = prompt + SUBAGENTS_NOTE

    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt = prompt + SKILLS_NOTE

    llm = model if model is not None else make_model()

    # Thêm cơ chế tự động chờ và thử lại khi gặp giới hạn tốc độ (429 RateLimit)
    if hasattr(llm, "_generate") and not getattr(llm, "_is_resilient", False):
        orig_gen = llm._generate
        def resilient_generate(*args, **kwargs):
            if type(llm).__name__ != "ScriptedChatModel":
                import time
                time.sleep(4.0)
            for attempt in range(8):
                try:
                    return orig_gen(*args, **kwargs)
                except Exception as exc:
                    err_str = str(exc)
                    if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "RateLimit" in err_str) and attempt < 7:
                        import re, time
                        delay_match = re.search(r"retry in ([0-9.]+)s", err_str)
                        delay = float(delay_match.group(1)) + 2.0 if delay_match else 10.0
                        time.sleep(delay)
                    else:
                        raise
            return orig_gen(*args, **kwargs)
        llm._generate = resilient_generate
        llm._is_resilient = True


    return create_deep_agent(
        model=llm,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )


