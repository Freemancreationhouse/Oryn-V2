# ORYN Studio V2 — CP1 protected source + motion contract candidate

**Status:** DEVELOPMENT / HARDWARE UNVERIFIED — NOT a production replacement.
**Inputs:** User-uploaded `github.zip` (current ORYN), `dune-weaver-main(2).zip` (original reference).
**Approved UI:** Hybrid ORYN Studio V2 with compact left rail, large central canvas, and Home/Gallery/Studio/Sequence/Clean/Motion/Light/System workspaces.

## What CP1 actually implements

- Full original ORYN source preserved (no machine configuration or saved user calibration overwritten).
- Pure auditable `modules/core/kinematics_contract.py`: original Dune Weaver motor coupling, with ORYN's saved full-circle and perimeter calibration scales retained.
- Production pattern executor calls the pure contract; no intentional change to successful calibrated motion output.
- Unknown relative G-code ACK **does not** count as success just because FluidNC reports `Run`/`Idle`. The command is never resent. A realtime feed hold is requested, dispatch halts, the motion position is marked uncertain and further patterns are denied until successful HOME.
- Failed pre-pattern cleaning does not advance to main pattern; failed moves no longer report 100% progress or move the logical position forward.
- Original cleaning `*.thr` bytes remain preserved; classification expanded to include suffix variants.
- React `/studio-v2` opt-in read-only eight-page UI preview: actual status and original THR canvas; Gallery art tiles and Lighting render are **illustrative**. The machine-path tab remains explicitly locked pending verified math/actual hardware.
- Original React app and all existing operational pages remain default, unchanged in function. No V2 machine operation controls are enabled.

## Implementation stages / gates

| Gate | Status | Acceptance |
| --- | --- | --- |
| CP0 — source preservation and Dune math audit | Complete offline | Diff + checksums, cleaning files compared, original formulas extracted |
| CP1 — offline motor safety contract | Candidate, 31 tests passed | Numerical parity, 25-turn trajectory, uncertain ACK, calibration rejection |
| CP1 — UI shell preview | Source added, TypeScript syntax parsed | Eight sections, real read-only telemetry and THR previews; npm build still needed |
| CP2 — controller bench validation | NOT DONE | Homing; separate theta + rho; correct compensation sign; no missed ACK |
| CP3 — repeated cleaning and pattern drawing | NOT DONE | 20+ revolutions without stationary spin; actual ball follows preview |
| CP4 — new execution interface | NOT DONE | Actual transformed machine path, pause/resume/queue with authentication and safety |
| CP5 — complete V2 rollout | NOT DONE | Migrated machine + lighting + system workspaces, desktop/mobile, full regressions |

## Run offline checks

From the root folder:

```bash
python -m pytest -q tests/motion_contract
python -m compileall -q main.py modules/core modules/connection
```

Source-specific results at packaging time: **31/31 isolated Python motion-contract tests passed**, Python bytecode compilation passed, modified TSX files parsed with TypeScript `transpileModule` with **0 syntax diagnostics**. Complete TypeScript typechecking, `vite build`, full Python integration tests and hardware evaluation were **not performed** here. The container could not finish fetching JavaScript dependencies.

## Preview the new V2 workspaces without commanding motors

Use Node.js (20+ is recommended) on a machine with npm network access, from `frontend/`:

**Windows PowerShell**
```powershell
npm ci
$env:VITE_ORYN_V2_PREVIEW='1'
npm run build
npm run dev
```

**Linux shell / WSL**
```bash
npm ci
VITE_ORYN_V2_PREVIEW=1 npm run build
VITE_ORYN_V2_PREVIEW=1 npm run dev
```

Open `http://localhost:5173/studio-v2`. The Vite development proxy expects an ORYN backend at `localhost:8080`; without it, you can inspect layout but patterns and telemetry are unavailable. Production `npm run build` outputs to `static/dist` and changes the served frontend bundle, so do this **only in a backup/test checkout** before approval. Without the environment variable the current working frontend remains the default and V2 route shows a disabled-preview notice.

**Important:** The `frontend/node_modules` folder is intentionally not included in the source ZIP. A clean `npm ci` is required on your workstation.

## Actual hardware test — cautious order

**Only on a supervised test machine after a backup of state/calibration and with physical stops accessible.** Do not run the full 20-turn test first.

1. Check original saved `.json` calibration and FluidNC `$` settings; back them up. Verify physical table type, X/Y steps-per-unit and gear ratio. Do not replace firmware or reset EEPROM as part of this checkpoint.
2. Home from the existing ORYN UI. Record physical location, theta=0 and rho=0. If HOME does not finish at centre, stop and diagnose before patterns.
3. Run one low-speed **360-degree theta test at rho≈0.8** and ensure ball returns to the same angular point and radial distance. Wrong radial direction indicates coupling sign/profile mismatch; stop, do not compensate blindly in software.
4. Run **centre → 0.8 → centre** (separate rho test) at low speed, confirm retracing exactly. Verify that theta and rho scales are both saved (no half-calibration).
5. Run one small short-span pattern at low speed and compare physical curve against actual THR viewer. If it misdraws, note direction, dimensions, end-point, and logs before increasing duration.
6. Run standard cleaning from perimeter with first **two** revolutions only, physically inspect whether rho advances as expected. Then test 5, 12 and 20+ turns in increments **only if prior stages pass**. Large `clear_from_out_Ultra` files are not appropriate for initial testing.
7. Force/observe an uncertain ACK in a simulated serial test only; confirm the code halts dispatch, never replays a delta and requires successful rehoming. Do not intentionally break live serial or physically jam the table to test this.
8. Run one full known-good THR, then normal pre-clean → pattern, then playlist; confirm progress, failure handling, correct machine path and restart behaviour. Recheck LED, Wi-Fi, security, manual moves and original UI.

Stop immediately for unexpected radial movement, obstruction, overheating, or unexpected motion. Do not enable unattended execution before complete hardware acceptance.

## Rollback

Use your untouched original `github.zip` ORYN source and original backups of machine/state calibration. CP1 has not been flashed or deployed by the assistant. To remove only the opt-in frontend preview, revert changes to `frontend/src/App.tsx` and `frontend/src/components/layout/Layout.tsx` and delete `frontend/src/pages/V2Preview.tsx` and `v2Preview.css`. To revert motion contract, use the original `modules/core/pattern_manager.py` and `modules/connection/connection_manager.py` and `main.py` from `github.zip`. Never overwrite saved machine calibration with the reference Dune Weaver values.

## Proven vs not proven

- **Proven offline:** parity of default Dune formula, mathematical consistency across 25 turns, preserved original cleaning files, fail-safe unknown ACK handler simulation.
- **Not yet proven:** physical winding and actual motor-axis sign, 12-turn spin root cause, correct pattern execution on this specific machine, source building in the user's PC environment, responsive UI browser functionality, hardware-specific homing and playlist stability.

ORYN's original `LICENSE` and `LICENSE-GPL-3.0` notices remain intact.
