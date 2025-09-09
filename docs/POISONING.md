# POISONING.md — Optional Label Poisoning

**Goal**: Disrupt text–image alignment for models trained from scraped captions/filenames/alt-text.

## Presets
- **label_flip**: map frequent classes to unrelated targets (e.g., cat→toaster).
- **clip_confuse**: bag-of-words noise to dilute semantics.
- **style_bloat**: long style descriptors chain.

## Surfaces
- **XMP**: `dc:title`, `dc:description`, `dc:subject`
- **IPTC**: `Caption-Abstract`, `Keywords`
- **EXIF**: `UserComment`
- **Sidecars**: `<image>.txt` caption, `<image>.json` (LAION-like)
- **Filename**: optional rename patterns (e.g., `{stem}_toaster` or `toaster_{rand}`)
- **HTML**: optional per-image snippet with poisoned `alt`/`title`

## CSV Mapping
Provide a CSV with headers `real_label,poison_label` to override built-ins:
```
real_label,poison_label
cat,toaster
dog,sedan
```

## Undo/Logging
Writes a `.mm_poisonlog.json` in the target directory to track sidecars and renames. `mm revert` uses that log.

## Nightshade-Lite?
We do **not** ship pixel-space adversarial optimization. A future optional "micro-jitter" transform may be added as **separate** from metadata and off by default.