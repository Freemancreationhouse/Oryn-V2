# ORYN Studio V2 — CP2R coupled Theta calibration (13 November 2026)

## Symptom and source cause

A 360-degree Theta teach jog was executed as an X-only GRBL `$J=G91 G21 X...` move. That physically changes radial position on a mechanically coupled Theta–Rho table, drawing a spiral. The normal CP2Q pattern executor already adds Y compensation.

## Surgical correction

- Rotation-calibration jog now calculates a **zero logical-rho** movement through exactly the normal `dune_coupled_delta` transform.
- Sends one coordinated relative GRBL/FluidNC `$J=G91 G21 X... Y... F...` jog, not two separately scheduled axis motions. No replay on an uncertain ACK.
- Saves **only X** units as the Theta revolution scale; does not add Y compensation into calibration. Reverse jog automatically reverses compensation.
- Rejects non-finite/zero/oversized increments or position uncertainty before sending a motor command.
- Existing Rho teaching flow, HOME, CP2Q pattern execution, UI, GRBL profiles, original 10:1 gearbox, motor steps and pattern files are unchanged.

For this user's stored motor step scales X=205, Y=143.504 and gear ratio=10, mechanical compensation is +0.142853... Y per +1.000 X controller unit for the standard profile. (The sign is profile-dependent; do not force a sign on other machines.)

## Deployment

This ZIP contains the **complete source tree** inside `oryn/`. Upload/update the source files in your existing GitHub repository before updating the Raspberry Pi, but do not overwrite the live Pi's `settings.json`, `state.json`, `.env`, `.venv`, or user pattern data. The Pi has local commits ahead of origin and a preserved stash, so do **not** run `git reset --hard`, `git stash pop`, or `git clean`; use the known cautious merge procedure.

After deployment, motor/controller ON and attended: HOME, move to a moderate fixed radius, start Theta rotation calibration; jog +1 or +2 X units at a low but practical feed, watching the ball. It should stay at nearly constant radius. Repeat +5, reverse -5 to check closure, then approach one full physical revolution in multiple increments, recording total X travel. Do not save if radial drift occurs. Stop and re-HOME on any uncertain/interrupted motion. Keep the existing Theta=78.000, Rho=51.504, gear=10:1 unless the *physical circular* calibration accurately establishes a new Theta count.

## Verification

106/106 Python motion-contract tests PASSED in Linux/Python 3.13; this is **source-only** verification. No real Pi/controller/ball test was performed here. GRBL status is an open-loop position report and cannot detect physical slipping or missed steps.
