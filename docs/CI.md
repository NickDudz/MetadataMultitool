# CI Plan

- GitHub Actions matrix: {ubuntu, macos, windows} x Python {3.9–3.12}
- Steps: setup Python, install, (optionally) install exiftool, run tests, upload coverage.
- See `.github/workflows/ci.yml`.