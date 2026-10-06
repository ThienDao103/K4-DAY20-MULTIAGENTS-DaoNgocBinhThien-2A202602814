---
name: enforce-python-type-hints
description: Use when writing or modifying Python packages that require strict public function type annotations.
---
# Enforce Python Type Hints

1. Identify all public functions and methods in every module (names not starting with an underscore `_`).
2. Add explicit type annotations to all parameters (e.g., `item: dict`, `threshold: int = 5`).
3. Add explicit return type annotations to all public functions (e.g., `-> Decimal`, `-> list[str]`).
4. Run static analysis or linter checks to verify that every public signature is fully annotated before finishing.
