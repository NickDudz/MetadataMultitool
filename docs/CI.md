# CI Plan

- GitHub Actions matrix: {ubuntu-latest, windows-latest} x Python {3.13}
- Steps:
  - Setup Python
  - Install project with dev+gui extras: `pip install -e .[dev,gui]`
  - Install ExifTool (apt/choco)
  - Set headless Qt env: `QT_QPA_PLATFORM=offscreen`
  - Run tests with coverage and upload artifacts
- See `.github/workflows/ci.yml` for the authoritative configuration.