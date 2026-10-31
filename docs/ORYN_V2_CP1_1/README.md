# ORYN Studio V2 — CP1.1 FRONTEND DATA REPAIR (Candidate)

Status: **CANDIDATE; NOT ACCEPTED BY USER; NO HARDWARE TEST.**

## Source baseline
- Based on `ORYN_STUDIO_V2_CP1_FULL_SOURCE_CANDIDATE_20261009.zip` exactly.
- The only existing files modified in CP1.1 are:
  - `oryn/frontend/src/pages/V2Preview.tsx`
  - `oryn/frontend/src/pages/v2Preview.css`
- Added: `oryn/tests/v2_preview/test_cp11_preview_contract.py` and this document.
- All other existing files (including backend motion, firmware, calibration, original UI, and original THR files) remain byte-identical to CP1.

## CP1.1 scope
- **Fixes a provable CP1 bug:** `usePatterns` would empty the gallery upon `apiClient` URL change without refetching. CP1.1 uses isolated same-origin read-only API calls independent of saved remote table selection.
- Displays loading/errors + working retry buttons; no more unexplained blank views on API failure.
- Gallery supports all existing pattern records using incremental Show More (36 records at a time); fetches original backend-generated pattern thumbnail images for the first 16 visible records (fallback decorative art remains if preview unavailable).
- Home and Studio load original THR coordinates; Cleaning offers all 11 stock cleaning patterns and loads original paths directly.
- Sequences reads saved playlist names. Light/System read settings/version (display only).
- Original motion, firmware, cleaning files, calibration, connected machine APIs, playlists and legacy control pages are **NOT** modified.

## Important limits
- **The approved V2 interface is NOT complete.** Some pages are previews with links to original controls; true motor toolpath and actual machine control are NOT enabled.
- Backend connection status and physical controller connection are different: when backend is working in preview-safe mode, the machine can legitimately display "Offline".
- The 31 original math/acknowledgment regression tests plus 10 new read-only source contract checks passed in the build sandbox (41/41 total).
- TypeScript/TSX syntax transpilation passed; a **full npm/TypeScript/Vite production build has not been verified in this environment** (npm dependency installation did not complete). Verify on Windows before accepting CP1.1.
- No real-machine tests have been run; keep hardware disconnected during CP1.1 acceptance.

## Windows install/test — side by side, safely
1. Do **not** delete CP1 or your current live ORYN installation.
2. Extract the full CP1.1 candidate archive into a **new folder**, with `oryn` inside it.
3. Keep the existing CP1-safe-mode backend running at port 8080. Its existing read-only API endpoints are sufficient for CP1.1. Do not connect motors yet.
4. Stop the old CP1 Vite terminal (`Ctrl+C`) so port 5173 becomes free.
5. In a **new CMD terminal** navigate to `...\ORYN_STUDIO_V2_CP1_1_FULL_SOURCE_CANDIDATE_20261010\oryn\frontend`.
6. Install frontend dependencies into this new candidate source:

```cmd
node "%ProgramFiles%\nodejs\node_modules\npm\bin\npm-cli.js" ci
```

7. Run a TypeScript + production build check:

```cmd
set "VITE_ORYN_V2_PREVIEW=1"
node "%ProgramFiles%\nodejs\node_modules\npm\bin\npm-cli.js" run build
```

8. If build passes, launch read-only Vite server:

```cmd
node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173 --strictPort
```

9. Open `http://127.0.0.1:5173/studio-v2` on the same Windows computer. Force refresh (`Ctrl+Shift+R`) to bypass an old browser bundle.
10. Verify:
   - Home shows the total discovered pattern count.
   - Gallery lists patterns; first visible images load where available; Show More works.
   - Selecting a Gallery pattern opens Studio with more than zero THR coordinates and a real drawing.
   - Clean shows more than zero points; change between `clear_from_out`, `clear_from_in`, and `clear_sideway` and compare visual paths.
   - Sequence, Motion, Light, and System pages open, even if serial status is disconnected.
   - No UI action in V2 starts motors; Machine Path remains disabled.

## Offline regression commands from `oryn` root
```cmd
python -m pytest -q tests/motion_contract tests/v2_preview
```

If you get `ModuleNotFoundError: pytest`, install `pytest` in the active Python environment.

## If Gallery is still blank
Open `http://127.0.0.1:5173/list_theta_rho_files_with_metadata` in a browser. It should return an array of pattern records. If backend on port 8080 works but this Vite address fails, check the proxy startup log. If this address returns a list but the screen does not, take a screenshot of Gallery and the browser Console (F12) with the first error. CP1.1 will also show an error with a Retry button.

## Next acceptance gate
Do not begin CP2 motor testing until CP1.1 browser build and data display pass. CP2 will separately verify actual original-Dune-compatible angular/radial trajectory, 10–12-turn cleaning regression, short-pattern accuracy, and long-cleaning stability on the real machine.
