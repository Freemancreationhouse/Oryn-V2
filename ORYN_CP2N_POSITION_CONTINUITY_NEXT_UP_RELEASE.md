# ORYN Studio V2 — CP2N Position Continuity & Next Up (2026-11-12)

**Authoritative source baseline:** CP2M, with only the changes described below. This is a full-source forward release, not a patch. ORYN — Designed to Move, by Studio Kinematics™.

## User physical acceptance that motivated this change

- Saved Theta = **78.000 controller units / revolution**, Rho = **51.504 controller units center-to-safe-perimeter**.
- Calibrations, supervised HOME and center ↔ perimeter commands were physically confirmed working in CP2M.
- Consecutive pattern continuity failed: a second pattern required re-HOME; adaptive cleaning appeared at a different actual radius from the on-screen center indicator.
- User additionally requested Home > **right-side Next Up**, with small next-pattern preview and the ability to add a future pattern during current execution.

## Root cause and protected correction

- The CP2M executor updated commanded THR state on GRBL `ok` planner acceptance, which does not prove the physical endpoint is reached.
- A single GRBL Idle response can be transient or stale. CP2N now requires **two consecutive matching GRBL Idle + reported controller-coordinate observations** at the initial entry point and final point, before progressing to drawing/next pattern. Controller-coordinate mismatch, disconnection, timeout or interrupted motion locks out further playback and requires supervised HOME. Relative moves are never retransmitted to fix uncertain acknowledgments.
- The screen remains a **reported/queued waypoint display**, not a physical ball encoder. If the motor skips steps, a belt slips, or power is lost while GRBL stays logically alive, controller reports alone cannot detect that physical error.
- The existing adaptive clearing selection is preserved. Newly queued Next Up patterns **do not inherit automatic cleaning** from the current pattern, preventing unrequested clearing while multi-pattern continuity is still under hardware acceptance.
- Next Up uses the existing live single-pass execution list and existing playlist execution engine. Adding does not interrupt the playing pattern. Removal applies only to future items. Up to 12 pending designs; path traversal and disconnected/unknown-reference submissions are rejected.
- The Home workspace's **right column** contains real Next Up preview/list/actions; actual preview thumbnails are reused, with true THR SVG fallback when image cache is unavailable.
- A new Play request no longer silently cancels a pattern already running; it returns a clear 409 and directs the user to Add Next.

## Preserved baseline and exclusions

- Original locked 10:1 gear ratio and Dune-compatible coupled theta/rho transform untouched.
- Original calibrated physical units 78.000/51.504 stay in the Pi's user settings/state; the source package does not replace them.
- All 8 approved native V2 workspaces, Pattern Forge, Gallery, playlist functions, firmware identification, Wi-Fi scanning/hotspot, Magic Home RGB, controller compatibility, legal third-party notices and saved playlists remain available.
- No machine state, ESP32/GRBL firmware, motor calibration, hardware position sensor or motor commands are included in the read-only verifier.

## Offline evidence

- 85/85 motion/LED regression tests passed (CP2E/J/L/M/N) including stale Idle telemetry, endpoint mismatch, disconnected fail-closed, Next Up validation and preserve-original-contract tests.
- Frontend JS `node --check` PASS, mirrored source/runtime equality PASS.
- Simulated Chromium UI Home layout + Add Next/queued cards PASS. **Real two-pattern hardware test NOT YET RUN.**

## Pi deployment / acceptance

1. Push this full-source contents to the existing Oryn-V2 repository using GitHub Desktop, preserving `.git` and existing user-specific settings.
2. With motion stopped and motors OFF, clone into a **new** `~/oryn-v2-cp2n-stage` and run `python3 ~/oryn-v2-cp2n-stage/scripts/verify_pi_v2_bundle.py`.
3. Only if verification passes, stop the service, rsync contents with `.git`, `.venv`, `settings.json`, `state.json`, `playlists.json`, `*.env` excluded, then start service and `python3 ~/oryn/scripts/verify_served_v2.py http://127.0.0.1`.
4. Browser hard-refresh. Check Home > NEXT UP right; idle Add Next must be disabled. Start with verified HOME and **a very short** supervised pattern; queue another short THR pattern. Compare physical ball position with displayed commanded path at each **completed** transition. No adaptive clean for the first hardware continuity test.
5. If the screen and physical ball diverge, STOP, remove motor power if unsafe and collect `sudo journalctl -u oryn -n 150 --no-pager` and screenshot. Do not mark physical continuity PASS or retry motion without supervised HOME.
