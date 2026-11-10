# ORYN Studio V2 — CP2K: Live Preview + Guided Machine Calibration

Customer product: ORYN — Designed to Move, by Studio Kinematics™.

## What this release changes

- Studio/overview/cleaning previews can display the pattern under execution with a moving toolpath cursor and a completed-path trace.
- The cursor is synchronized to the Raspberry Pi's **reported/queued** waypoint count. It is NOT encoder feedback or measured ball position, and can lead or lag physical motion. Large geometries use a sampled on-screen path to keep the Pi display responsive.
- A four-step guided calibration UI: establish physical center, teach one full rotation, teach the actual usable radius, then verify.
- The radius teaching page clearly identifies bigger-table setup and advises stopping before the mechanical end stop.
- No automatic motor jogs or changes to machine movement were added by this release.

## Preserved

- Existing motion engine and kinematics (standard 10:1 setting)
- Arduino GRBL, ESP32/FluidNC, and other existing controller abstractions
- Home and calibration backend endpoints, patterns, cleaning, lighting, and network functions
- Approved native V2 navigation and branding

## Limitations

- The live cursor represents the backend's queued/reported progress. Exact ball tracking requires physical position feedback not present in this hardware setup.
- Physical calibration and full-pattern/cleaning verification must be performed on the real machine, under supervision.
- A saved radial calibration is not automatically valid for a larger table. Always physically verify home and the safe outer radius.

## Installation

This is a complete source package for the existing ORYN V2 GitHub repository. Copy the contents of `oryn/` over the cloned repository (preserve `.git`, saved Pi settings, and secrets), commit/push, then `git pull --ff-only` and restart the ORYN service on the Pi. To confirm the Pi actually serves the updated UI, run `python3 scripts/verify_served_v2.py http://127.0.0.1`.

## Validation

- Node.js syntax check and simulated UI state/navigation tests
- Existing 67 offline motion/LED tests
- Whole-package release manifest and served-asset check
- Native Chromium test and physical motor test not claimed as passed
