# ORYN Studio V2 — CP2E Reverse-Overtravel Safety Candidate

**Status: SOFTWARE CANDIDATE ONLY — NOT PHYSICALLY CERTIFIED.**

## Preserved baselines

- CP1.4 approved V2 UI, including its eight workspaces, Pattern Studio, Gallery gold thumbnails and read-only preview.
- All `.thr` artwork and original 11 clearing pattern files are byte-identical to CP1.4.
- Dune Weaver theta/rho transform and standard 10:1 gear default (Mini default 6.25) are unchanged.
- Firmware, GRBL settings, and machine connection adapters remain unchanged; UNO/GRBL, ESP32/FluidNC, MKS DLC32 support not removed.
- This package DOES NOT change the controller settings `$100=205`, `$101=143.504`, `$3=2` or saved user calibrations.

## Fault addressed in software

The legacy pattern movement sender used an unsafe timeout path: it could treat GRBL `Idle` as proof that a specific move completed; it could then retry a move whose acceptance was uncertain. This is dangerous particularly when a HOME command uses relative `$J` movement. CP2E now requires an explicit `ok` ACK for each legacy move, has no automatic move retry on uncertain command acceptance, and fails closed with feed hold and a position-uncertain flag on error/timeouts. The calibrated relative sender additionally marks position uncertain on rejection, transport failures and interrupted movement.

The controller's `ok` only means **planner acceptance**, NOT an optical measurement of motor or ball position. A missed motor step, mechanical slippage or backlash can still produce physical overtravel with perfectly valid `ok` responses.

## Offline test results

- 54/54 Python motion-contract regression tests passed in this build environment.
- All 168 bundled `.thr` files inspected. 167 valid files pass mathematical full-path and inverse-delta checks; 11 cleaning files pass.
- `pattern-superellipse.thr` is **blocked at the final 1.005 rho point** (outside 0–1). It is not silently clamped or modified; the original file is retained.
- 9 patterns contain unusually large per-point jumps and are noted in `CP2E_OFFLINE_MOTION_REPORT.txt` for inspection, not automatically classified as corrupt.
- Tests cover: 10:1 original Dune transform parity, positive/reverse compensated deltas, fail-closed on silent/lost ACK, status-only responses, stale replies, transport exceptions, controller errors/alarms, and relative jog non-replay.

## How to test safely on Windows (no hardware commands)

1. Extract the full ZIP into a new directory, away from your previously accepted installation.
2. Open the extracted `oryn` directory.
3. Double-click `RUN_CP2E_OFFLINE_TESTS_WINDOWS.cmd`. If Python lacks pytest: `python -m pip install pytest python-dotenv`.
4. Read the generated `CP2E_OFFLINE_MOTION_REPORT.txt`. The report deliberately notes outstanding hardware risk.
5. For a read-only V2 UI preview with no motor connection, use the existing `START_ORYN_V2_PREVIEW_WINDOWS.cmd` and keep the machine disconnected.

## BEFORE real hardware pattern or cleaning tests

- Your supplied gear teeth 150 and 16 imply **9.375:1** physically (if direct drive), whereas you expressly requested retaining software's **10:1** standard default. Both facts are retained; CP2E does not hide this mismatch. Under the same axis convention the coupling coefficient differs by 6.25% of the 9.375:1 requirement, which can accumulate over repeated theta revolutions.
- You observed physical reverse overtravel after several compensated jogs. No encoder/physical position sensor evidence has ruled out backlash, binding, motor steps lost, or duplicate human-issued jogs.
- **Do not run an unattended long cleaning or full pattern yet.** Use only supervised checks after confirming physical home, installed mechanical ratio, the active runtime profile, and emergency power cutoff. If any return position is wrong, stop and do not issue a compensating jog based solely on GRBL's logical `MPos`.
- Only an on-machine forward/reverse positional witness and sustained cleaning + pattern tests can certify the physical issue is resolved.

## Package change scope

Existing CP1.4 source modifications are limited to:

1. `modules/core/pattern_manager.py` — fail-closed movement dispatch + safe THR input guard.
2. `modules/core/kinematics_contract.py` — added path validation; **existing transform body is unchanged**.

Additional files are CP2E tests, offline report runner, Windows launcher, and this readme. No UI source or pattern files were modified.
