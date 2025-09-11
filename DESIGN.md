# DESIGN.md — Metadata Multitool

## Mission
Local-first privacy tool for photographers/creators to prep images safely, with optional defenses against data scraping.

## Architecture
- `src/metadata_multitool/`
  - `cli.py`  — argparse entrypoint.
  - `core.py` — discovery, logging, helpers.
  - `exif.py` — exiftool wrapper + Pillow fallback.
  - `clean.py`— safe copy & strip.
  - `poison.py`— presets, sidecars, CSV mapping, rename & HTML.
  - `html.py` — HTML snippet generation.
  - `revert.py`— undo logic (sidecars, metadata, renames).
  - `gui_qt/` — modern PyQt6 GUI (only supported GUI)

## Commands
### `mm clean <paths...> [--copy-folder safe_upload] [--backup|--no-backup]`
- Copies into `safe_upload` and strips metadata.

### `mm poison <paths...> --preset <preset> [--backup|--no-backup]`
Flags:
- `--preset {label_flip,clip_confuse,style_bloat}`
- `--true-hint TEXT` (helps `label_flip` choose)
- Surfaces: `--xmp --iptc --exif --sidecar --json`
- CSV mapping: `--csv mapping.csv`
- Rename: `--rename-pattern "{stem}_toaster"` (vars: `{stem}`, `{rand}`)
- HTML export: `--html`

### `mm revert <paths...>`
- Removes sidecars, clears fields we set, and restores filenames where logged.

## Testing
- CLI flows without exiftool (sidecars path).
- Rename + revert restoration.
- CSV mapping overrides.
- PyQt6 GUI tests via `pytest-qt` (skipped if unavailable locally).

## Future
- PyQt6 GUI enhancements.
- Filename poison templates with dictionaries.
- Optional perceptual micro-jitter (separate, default off).