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

## Commands
### `mm clean <path> [--copy-folder safe_upload]`
- Copies into `safe_upload` and strips metadata.

### `mm poison <path>`
Flags:
- `--preset {label_flip,clip_confuse,style_bloat}`
- `--true-hint TEXT` (helps `label_flip` choose)
- Surfaces: `--xmp --iptc --exif --sidecar --json`
- CSV mapping: `--csv mapping.csv`
- Rename: `--rename-pattern "{stem}_toaster"` (vars: `{stem}`, `{rand}`)
- HTML export: `--html`

### `mm revert <path>`
- Removes sidecars, clears fields we set, and restores filenames where logged.

## Testing
- CLI flows without exiftool (sidecars path).
- Rename + revert restoration.
- CSV mapping overrides.

## Future
- GUI stubs (Tkinter/Qt).
- Filename poison templates with dictionaries.
- Optional perceptual micro-jitter (separate, default off).