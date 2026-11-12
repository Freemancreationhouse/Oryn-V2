# ORYN Studio V2 — CP2M Position Reference and Pattern Continuity

**Product:** ORYN — Designed to Move, by Studio Kinematics™
**Release:** CP2M-REFERENCE-20261111
**Status:** Offline-tested source candidate; physical Pi test still required.

## Why this update exists
A logical GRBL zero or a saved position cannot prove that the carriage reached the physical center. CP2L also lacked dedicated commands for center-to-perimeter-to-center travel, and pattern starts were not gated by a trustworthy current-session physical reference.

## Changes
- A supervised explicit HOME followed by operator confirmation of the true physical center makes a session-local position reference; never auto-confirms from USB, GRBL MPos, or state.json.
- Native V2 Motion has **Confirm ball is at CENTER**, **Move to safe perimeter**, and **Return to center** with readiness and uncertainty feedback.
- Uses existing ORYN calibrated, coupled THR movement to traverse rho=0 or rho=1 without resetting theta or replacing the math.
- Pattern and cleaning operations reject unverified references; completed operations retain the last commanded theta/rho in the same continuous controller session.
- Stop, force-stop, reset, reconnect, and unconfirmed motion revoke position-reference trust. The UI describes commanded position, not physical encoder feedback.
- Existing machine settings, saved calibration and playlist data are not included in this release archive. Current user-confirmed Pi calibration: theta 78.000 controller units per 360°, rho 51.504 units full travel; **these are NOT hardcoded software defaults**.
- Original configured standard 10:1 gear ratio, kinematics contract, pattern coordinates, normal speed settings and lighting adapters are preserved.

## Validation
- Source tests: 76/76 motion/LED/reference tests passed in offline test environment.
- Static JS parse: Node syntax verification passed.
- Byte-for-byte source checks preserved kinematics_contract.py, state.py, Magic Home adapter and sampled original star/cleaning paths.
- Actual Pi frontend deployment, real center/edge return, and uninterrupted pattern-to-pattern operation need physical acceptance.

## Safety and operation
1. Install CP2M using a GitHub Desktop commit and deploy application source to Pi, excluding settings.json, state.json and playlists.json.
2. With the physical mechanism clear and motor power correctly supplied, run supervised HOME once after connecting.
3. Confirm the ball physically reached its true center, then press **Confirm ball is at CENTER** in Motion.
4. Inspect saved theta/rho values in Motion; do not overwrite verified calibration.
5. Try **Move to safe perimeter**, observe stationary reference, then **Return to center**. Stop if movement is wrong.
6. Test a short pattern without a cleaning prelude; if it completes, begin another to verify commanded position continuity. Stop on unexpected movement.
7. After a controller restart, disconnection, emergency stop or missed motion acknowledgement, perform HOME and confirmation again. Without a physical sensor/encoder it is unsafe to claim automatic position recovery across lost power.
