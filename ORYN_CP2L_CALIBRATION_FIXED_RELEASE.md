# ORYN Studio V2 — CP2L Calibration Controls (2026-11-10)

**Customer identity:** ORYN — Designed to Move, by Studio Kinematics™.

## Fixed
- Calibration start returns explicit active session status from the Pi backend.
- After confirmation, frontend reads the real session state and visibly enables +/- jog controls.
- Corrected the misparsed theta/rho jog button identifiers and the +/- signs.
- Errors from a failed start or jog are shown directly within the calibration card, not offscreen.
- Separate feedback for rotation and radial teaching; calibrated travel increments survive UI redraws.
- A calibration jog is submitted only once if its acknowledgment is uncertain; the session is disarmed and position marked uncertain on timeout/no Idle.
- 10:1 gear-ratio configuration, universal machine model and original theta/rho kinematics are unchanged.

## How to test safely
1. **First with motor power OFF:** Pi connected to UNO, open Motion → 2 Rotation 360° or 3 Table radius; select Start teaching. If the controller is idle, session must show **TEACHING SESSION ACTIVE** and enable the labeled +/- jog buttons. Do NOT press jog with power off.
2. If Start fails, error appears inside the card. For radial calibration, a reported radius not near zero blocks teaching: use approved physical HOME/center process first, do not falsify coordinates.
3. With actual motor power ON, real HOME verified and mechanism cleared, perform only **one small jog** while supervised, with accessible emergency power cutoff. Verify physical motion and the displayed session travel before another jog.
4. Theta: stop after exactly one physical full rotation and save only after visually confirming it. Rho: start at true center and stop before the safe usable perimeter, then save. Do not attempt full patterns/cleaning before verifying both calibrations.

## Verification performed
- Virtual frontend POST/GET request and button-sign test: theta +/-, rho +/-, save, rejected-start lockout.
- Backend FastAPI function tests with mocked motors for start, jog, reverse, save, non-center rejection and Idle timeout fail-closed handling.
- Existing source/motion/LED regression suite.
- Static source and archive checks. **Physical motors/Pi were not accessed from this environment.**

## GitHub / Pi update
Extract the single complete source archive; replace *application source* inside the existing GitHub Desktop repository, preserve `.git`, and do not overwrite the Pi's saved settings or playlists. Commit and push from GitHub Desktop. On the Pi, stop with motors off, `git pull --ff-only origin main`, run `python3 scripts/verify_pi_v2_bundle.py`, `sudo systemctl restart oryn`, then `python3 scripts/verify_served_v2.py http://127.0.0.1`. Do not use `git reset --hard` or delete local machine settings.
