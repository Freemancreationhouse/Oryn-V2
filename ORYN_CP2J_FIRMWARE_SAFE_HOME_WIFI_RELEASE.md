# ORYN Studio V2 — CP2J Safe Connection + Native Wi-Fi

**Product:** ORYN — Designed to Move, by Studio Kinematics™.

## Correction scope
- GRBL 1.1h firmware identification from the controller's `$I` `[VER:...]` response; no firmware flash.
- Serial connection no longer issues automatic GRBL soft reset, work-coordinate reset, or inferred physical home. Machine home remains unverified until deliberately referenced.
- Startup does not perform unattended homing or playlist execution by default; deliberate machine commands remain available from the V2 Motion screen.
- V2 System now includes native read-only Wi-Fi status and scan, saved profile handling, and confirmed router switching.
- Fallback ORYN setup hotspot uses SSID `ORYN` when no saved router is reachable **if the Pi hotspot profile and recovery timer are installed**. A Pi with one Wi-Fi radio normally does not broadcast its setup hotspot while connected as a client to the home router.
- Existing source motion transformations, motor ratios and GRBL controller settings are unchanged. ORYN standard ratio remains 10:1.

## Prepare deployment (customer device)
1. Switch Arduino motor power OFF. You can keep the USB serial cable connected.
2. Publish the contents of this `oryn/` source folder to your existing `Freemancreationhouse/Oryn-V2` GitHub repository using GitHub Desktop, preserving `.git` and local `state.json` / `settings.json` on the Pi.
3. On the Pi: `cd ~/oryn && git pull --ff-only origin main` (stop if Git finds conflicts).
4. `sudo systemctl restart oryn` and confirm `sudo systemctl is-active oryn` prints `active`.
5. Verify installed + served frontend hashes: `sha256sum ~/oryn/static/dist/oryn-v2-live.js` and `curl -fsS http://127.0.0.1/oryn-v2-live.js | sha256sum` must match.
6. Open `http://192.168.0.224/#system` (address from prior Pi session; may change if network changes). Refresh with Ctrl+Shift+R.
7. Firmware and home status should show read-only GRBL identification and physical home NOT verified.
8. Open System > Wi-Fi & ORYN hotspot. Scan; save another router profile without leaving the current router, or use **Connect** knowingly (the browser/SSH may disconnect and IP may change).

## One-time fallback hotspot setup (only if absent)
While connected to the current router with SSH and with no active AP setup session:
`cd ~/oryn && sudo bash wifi/setup-wifi.sh`

This installs the NetworkManager `ORYN` hotspot profile and recovery timer. It is not intended to switch the current working router connection. **Do not force hotspot mode while using the Pi over that same Wi-Fi radio**; the SSH/web connection would be lost. Without a second Wi-Fi adapter, the `ORYN` setup SSID normally appears only when the Pi cannot connect to saved Wi-Fi.

## Verification and limitations
- Offline regressions must pass; no physical motor power was available in the test environment.
- Only a successful manual HOME and observed correct physical position can establish a reference; a GRBL `MPos=0` is not proof of home.
- Short-term 10:1 ratio and physical gear-tooth questions are unchanged; do not tune motion mathematics without intentional engineering change.
- This package contains upstream third-party legal notices where required; they are not customer-facing ORYN brand content.
