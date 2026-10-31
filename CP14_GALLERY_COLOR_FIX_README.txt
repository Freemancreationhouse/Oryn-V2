ORYN STUDIO V2 CP1.4 - GALLERY COLOR VISIBILITY FIX (2026-10-10)

Source baseline: ORYN_STUDIO_V2_CP1_3_FULL_SOURCE_GALLERY_STATUS_FIX_20261010.zip

Confirmed from 2026-10-10 14:50 screen recording: Studio uses sand-gold SVG paths,
Gallery fetched cached 512x512 WebPs with translucent black strokes. Against dark
cards the design appears nearly invisible.

Targeted change: frontend/src/pages/V2Preview.tsx and v2Preview.css only.
Preview images are recolored in the browser, with anti-aliased alpha boosted.
No changes to cached WebP files, THR coordinates, backend, firmware or motion.
Previously colorful pixels (nonblack) are preserved.

For Windows: extract full package to fresh folder, close previous ORYN Vite and
backend windows, keep physical device disconnected, run
  oryn/START_ORYN_V2_PREVIEW_WINDOWS.cmd
Then browse http://127.0.0.1:5173/studio-v2 and open Gallery.
Do not use the read-only preview to initiate motion.

Alternative: apply changed-files ZIP over a COPY of CP1.3 and restart Vite.

Acceptance:
  * Gallery cards are readable in the same warm gold as Studio.
  * Fine patterns remain visible across the first 36 and Show more batches.
  * Selecting a Gallery pattern opens the matching Studio pattern.
  * No unexpected motions, backend changes or corrupted THR files.
  * CP1.3 remains the rollback point.
