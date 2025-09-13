import os

try:
    import PyQt6  # noqa: F401
except Exception:
    opts = os.environ.get("PYTEST_ADDOPTS", "")
    if "-p no:pytestqt" not in opts:
        os.environ["PYTEST_ADDOPTS"] = (opts + " -p no:pytestqt").strip()
