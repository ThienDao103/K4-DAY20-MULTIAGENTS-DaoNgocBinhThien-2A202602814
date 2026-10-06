"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when you need to explore and understand the workspace, inspect data files, read docstrings, "
                "or analyze file structures before planning any changes. Does not modify any files."
            ),
            "system_prompt": (
                "You are an explorer subagent. Your role is to examine the workspace, read files, analyze logs or data, "
                "and report factual findings concisely without modifying any files."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when you need to write or edit code, transform data files, create outputs, or execute test commands "
                "to apply the planned modifications."
            ),
            "system_prompt": (
                "You are an implementer subagent. Your role is to perform file edits, data transformations, and run shell tests "
                "to implement solutions accurately according to instructions. Report the exact actions taken."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use when you need to independently verify changes, test suites, edge cases, and ensure compliance "
                "with all task rules and requirements before completion."
            ),
            "system_prompt": (
                "You are a reviewer subagent. Your role is to perform independent verification on the modified workspace. "
                "Check edge cases, inspect output schemas and run tests without changing code unless instructed. "
                "Report a clear pass/fail status with discrepancies found."
            ),
        },
    ]

