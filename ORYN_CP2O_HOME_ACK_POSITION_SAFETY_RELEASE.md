# ORYN Studio V2 — CP2O HOME ACK & Position Safety (2026-11-12)

**Full source, forward-only replacement; CP2M deployed Pi baseline plus the CP2N right-side Next Up addition.**

## Physical fault evidence supplied by owner

- 2026-11-12 13:26:06, explicit sensorless HOME command `$J=G91 G21 Y-51.50400 F257.520`.
- At that feed rate, completing a 51.504-unit jog requires **at least 12.00 seconds**, but CP2M marked `Crash homing completed` at 13:26:07, ~one second later.
- GRBL Y position went from `-357.391` to `-361.356`: only **-3.965 units** had registered before HOME reported success.
- Patterns subsequently reported `ORYN motion was not confirmed by the controller` and stopped at THR points `52/3449`, `3944/7449`, and `1788/6334`.
- Logs sometimes stated `Pattern execution completed, maintaining state for playlist` after failed motion; log wording was misleading.

## CP2O root fixes (source audited)

1. Status queries now own the connection's existing RLock during the full send/read transaction, preventing other threads from consuming the `ok` for streamed G91 motion. Queries are bounded, not infinite.
2. HOME requires a fresh Idle starting state, exactly one `$J` dispatch, explicit `ok`, expected GRBL-reported Y delta, enough time for the commanded travel, then two stable Idle/position samples. A premature Idle or partial travel fails closed; it does **not** set theta/rho to zero or mark HOME successful. No command replay on uncertain ACK. The failure sends GRBL realtime feed-hold (`!`).
3. An unconfirmed HOME marks motion position **uncertain** and blocks confirmed reference until an explicit successful HOME and **operator visual center confirmation**. There is no endstop or encoder on this sensorless table: GRBL position numbers still cannot physically prove center.
4. A failed pattern logs **FAILED**, not **completed**, and the playlist stops on failure. Sensorless automatic crash-home between patterns is suppressed to prevent unsafe unattended homing. Position memory continues across *successfully verified* consecutive patterns.
5. Home and Status errors are now specific about the verification failure instead of always saying “after 15 seconds”.
6. The existing CP2N Home **right-side Next Up** thumbnail preview, Add Next and remove queue are preserved. Queued next patterns never inherit an unintended adaptive clean.

## Preserved

- Original locked 10:1 mechanical ratio, coupled THR transform and controller step settings **unchanged**.
- Calibration **Theta 78.000**, **Rho 51.504** are owner-side saved values and not overwritten by this archive.
- All eight native V2 workspaces, patterns, Gallery, Pattern Forge, Wi-Fi, hotspot, Magic Home RGB and third-party notices remain intact.
- No archive operation overwrites local `settings.json`, `state.json`, `playlists.json`, `.env` or `.venv` during recommended deployment.

## Safety and acceptance

- Source-level and simulated tests DO NOT prove physical center, motor torque, gearbox coupling, radial travel or long-pattern reliability.
- **Do not test with power applied until the user inspects the mechanism and supervised recovery is planned.**
- No automatic behavior or physical motor commands were run during offline verification.
- Initial deployment must be motor-power OFF; verify served version and inspect status/error handling first. Then carry out deliberate supervised HOME and a short test; stop immediately on wrong-direction travel or drift.
