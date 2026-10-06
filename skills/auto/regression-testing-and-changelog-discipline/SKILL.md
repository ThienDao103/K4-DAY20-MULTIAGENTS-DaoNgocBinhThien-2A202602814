---
name: regression-testing-and-changelog-discipline
description: Use when fixing bugs or implementing code changes that require regression tests and changelog entries.
---
# Regression Testing and Changelog Discipline

1. Never modify existing files in the test suite directory unless explicitly permitted; always add new test files (e.g., `tests/test_regressions.py`).
2. Add at least one distinct test function in `tests/test_regressions.py` for each bug fixed or feature added.
3. Record each bug fix or change in `CHANGELOG.md` under the heading `## Unreleased` using the format: `- fix(<function name>): <short description>`.
4. Ensure all newly added regression tests pass successfully before completing the task.
