ORYN STUDIO V2 CP1.3 — GALLERY AND OFFLINE STATUS UI FIX (TEST CANDIDATE)
Date: 2026-10-10
Source: CP1.2 full source candidate; DO NOT overwrite prior accepted ORYN.

Observed in user recording 2026-10-10 13:59:
- Gallery successfully loads 168 patterns but only the first 16 thumbnails are real.
- Studio draws real THR trajectories correctly in read-only preview.
- Cleaning preview and other navigational workspaces render.
- Machine is intentionally offline; calibration labels were misleading.

Changes only in V2 Preview .tsx, .css, plus this document and four UI tests:
- Every currently visible Gallery card requests original cached artwork in batches of 8.
- No fabricated decorative circular thumbnails; transparent loading/unavailable label until image appears.
- Artwork-first gallery cards enlarged at desktop widths.
- Backend online vs physical-controller offline distinguished.
- Offline calibration is UNKNOWN, not inaccurately "NOT SAVED".
- "Original ORYN controls" link explicitly identifies preserved legacy control pages.

Protected: original Dune Weaver-related motion math, GRBL / FluidNC / direct board adapters,
  Python backend, .thr patterns, calibrations, hardware control/entrypoint, app router,
  preview read-only policy, CP1.2 Windows launcher.

OFFLINE VERIFICATION: 31 motion + 10 CP1.1 preview + 4 CP1.3 UI checks passed.
  TypeScript/JSX transpilation syntax check passed.
  Full production Vite build was not possible in this environment and MUST be
  verified on the user's Windows machine. No physical machine motion was tested.

WINDOWS TEST (physical ORYN disconnected):
1. Extract this ZIP to a NEW folder. Do not overwrite CP1.2 or working ORYN.
2. Stop any previous CP1.2 launcher/backend/frontend windows with Ctrl+C.
3. In extracted oryn folder, run START_ORYN_V2_PREVIEW_WINDOWS.cmd.
4. Browse http://127.0.0.1:5173/studio-v2
5. Gallery: scroll through 36 cards and click Show More. Verify different real artwork
   (avoid equating real simple rings with fake previews). If images unavailable they show
   "Preview loading / unavailable" instead of made-up pattern artwork.
6. Studio: click at least two complex patterns and check point count and geometry.
7. Clean: switch outward, inward and sideways paths; verify different canvas drawings.
8. Motion: when machine disconnected, calibration values should show OFFLINE · UNKNOWN.
9. Verify Original ORYN link still opens legacy interface. It is intentionally preserved.

Do not send physical motion commands from this preview. CP2 hardware-motion acceptance
  remains pending, including the cleaning-after-10–12-revolutions fault and misdrawing.
