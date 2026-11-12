# ORYN Studio V2 — CP2Q controller endpoint verification (12 November 2026)

## What was objectively wrong in CP2P

`_confirm_controller_endpoint()` compared a target with `state.machine_x/y`, even though those fields were maintained as *commanded* coordinates and could be overwritten by `check_idle_async()`. The apparent endpoint verification could be self-referential and could not reliably distinguish planned motion from a GRBL position report.

CP2Q requires **two fresh, stable Idle replies with actual numeric controller positions**, acquired through the transaction-locked status query, in a consistent `MPos` or `WPos` frame. Neither status query changes ORYN's commanded `machine_x/y` values. The comparison fails closed when position is missing, inconsistent or disconnected, without replaying any motion blocks. An ACK remains planner acceptance, *not* motor-position confirmation.

## Preserved

- Original 10:1 gearbox parameter and coupling direction/equations, 205.0/143.504 controller steps, and current local calibration values (Theta=78.000, Rho=51.504) are **not modified**.
- CP2P frontend, Gallery, Pattern Forge, eight V2 workspaces, queue/Next Up, Magic Home RGB, universal profiles, USB/WiFi setup, original patterns unchanged.
- No auto-rehome, no hidden axis reset, no guesses about mechanical sign or calibration.

## What CP2Q cannot repair or establish remotely

- GRBL `MPos/WPos` is derived from motor steps commanded, not from an encoder tracking the ball. It will not detect a slipping pulley, lost step, poor motor current, mechanical binding, ball magnet slippage, or an incorrect motion coupling direction.
- `No serial ports available` is a startup connectivity error; inspect whether a serial port successfully connects afterward. Do not attribute motor drift to this line alone.
- Actual physical pattern tracking is **not accepted/passed** until the owner observes the Pi machine after a deliberately supervised test.

## Installation, motor power OFF

This archive is a **complete source tree**, with root folder `oryn/`. Stop the ORYN service, back up `~/oryn` and then use a file manager or archive extraction to replace source *while preserving* the owner's existing `settings.json`, `state.json`, `.env`, `.venv`, playlists, and generated artwork. Do not copy settings/state from any packaged default, do not delete user content, and do not blindly overwrite the live working tree. Python dependency versions are unchanged. Restart only once the backup and preserved files are confirmed.

## Physical acceptance — low risk, operator in control

1. Inspect radial drive, motor gear engagement, pulleys, steps/microsteps, power supply and hand-movable mechanism while **motor power is off**. Remove sand/ball load if practical.
2. Reconnect to the correct USB/controller port. If the controller is missing, diagnose port/USB first; do not attempt HOME or patterns.
3. Perform a single supervised HOME and visually confirm actual center. Keep hand near power cut-off. If HOME is wrong or binding, stop; do not keep retrying.
4. At low speed, center→perimeter→center and a short small-radius spiral/loop. Compare physical direction with on-screen trace immediately. If divergence begins at theta-only movement, test winding/coupling direction mechanically before touching gear values.
5. At the first offset, stop, do not run a longer pattern, record controller status (`?` only when safely idle), the step at which drift begins and the full ORYN service log. Note whether it is a sudden jump (missed step or slip) or systematic wrong-direction Y compensation. Never repeatedly crash-home to hide missed position.

## Source-only test outcome

93 / 93 motion-contract tests passed in Linux Python 3.13 with `PYTHONPATH=.`. These tests are not native Pi/GRBL/FluidNC physical acceptance and do not prove physical motion tracking.
