ORYN Studio V2 CP1.2 — LOCAL READ-ONLY WINDOWS PREVIEW
=======================================================

SOURCE BASELINE
- CP1.1 FULL SOURCE WINDOWS COMPILEFIX1, retained intact except:
  1. frontend/src/pages/V2Preview.tsx — direct /studio-v2 is now sufficient
     to opt into preview; no Vite environment-variable gate. Offline banner.
  2. frontend/vite.config.ts — proxy to 127.0.0.1:8080, avoiding
     localhost IPv4/IPv6 ambiguity.
  3. tests/v2_preview/test_cp11_preview_contract.py — updated test for
     the explicit opt-in route (motion tests unchanged).
  4. New Windows local preview launcher and these instructions.
- Original ORYN backend, Dune Weaver math, saved machine profiles,
  cleaning .thr files and legacy controls: UNCHANGED.

PROBLEM CONFIRMED BY USER VIDEO AND VITE LOG
- Video: 'ORYN Studio V2 preview is disabled' appears on /studio-v2.
  This happens if Vite is started without VITE_ORYN_V2_PREVIEW=1.
- Clicking 'Open original ORYN' then opened the legacy connection overlay.
- Vite build SUCCESSFUL (2714 modules transformed, built in 20.02s).
- Vite dev server SUCCESSFUL on port 5173.
- HTTP proxy continuously ECONNREFUSED because backend port 8080
  was not running/reachable during this recording.

HOW TO TEST
1. Extract this FULL SOURCE archive into its OWN new folder. Do not
   overwrite your previous accepted CP1/CP1.1 folders.
2. Disconnect physical ORYN hardware for all CP1.2 preview checks.
3. Close the old Vite and old backend CMD windows (Ctrl+C).
4. Double-click oryn/START_ORYN_V2_PREVIEW_WINDOWS.cmd
   - On first run it will create .venv, install Windows Python dependencies
     and install frontend dependencies if missing; internet is needed.
   - Later runs reuse installed dependencies.
   - It starts the backend bound to 127.0.0.1:8080 with serial auto-connect,
     auto-play and LED provider disabled; it starts the frontend on 5173.
   - It opens http://127.0.0.1:5173/studio-v2 automatically.
   - This launcher *does not* alter your other ORYN installations.
   - Local backend API is still capable of movement if separately commanded;
     do not connect hardware or use legacy motion controls during preview.
5. Click Gallery, Studio, Clean, Sequence, Motion, Light, System.
   Confirm Gallery thumbnails and THR point counts with real backend.
6. To stop, press Ctrl+C in the launcher CMD window; both processes stop.
7. If startup fails, send preview_logs/backend.log and
   preview_logs/frontend.log with a screenshot.

IF YOU PREFER MANUAL WINDOWS CMD
- Start backend from oryn root (in one CMD window):
    .venv\Scripts\python.exe -c "import main; from modules.core.state import state; state.preferred_port='__none__'; state.auto_play_enabled=False; state.led_provider='none'; import uvicorn; uvicorn.run(main.app, host='127.0.0.1', port=8080)"
- Start Vite from oryn\frontend (second CMD):
    node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173 --strictPort
- There is no need to set VITE_ORYN_V2_PREVIEW. It is harmless if set.

ACCEPTANCE GATE
- Offline tests are not evidence of real machine accuracy.
- Machine Path preview remains disabled until motion math validation.
- Do not run physical cleaning or pattern playback on this checkpoint.
- A full final Windows browser acceptance test is still required.
