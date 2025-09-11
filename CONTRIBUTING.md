# Contributing

1. Fork & branch from `main`.
2. Create a virtualenv; `pip install -e .[dev,gui]` (PyQt6 GUI tests included).
3. Add tests in `tests/`; run `pytest -q`.
   - For headless GUI testing: set `QT_QPA_PLATFORM=offscreen`.
4. Update docs if behavior changes.
5. Open a PR with a clear description.

We keep **poisoning** features **opt-in** and clearly documented. Avoid dark patterns.