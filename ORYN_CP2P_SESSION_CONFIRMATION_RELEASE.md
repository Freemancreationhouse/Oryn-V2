# ORYN Studio V2 CP2P — Trusted Session Controls (12 Nov 2026)

## Reproduced frontend defect

The user had to tick an `I have physically referenced/homed` checkbox separately in Studio, Clean and Sequence. The checkbox was cleared on every page navigation and was **not** forwarded to the backend, although the backend already enforces `require_referenced_motion` and physical HOME confirmation. This caused redundant prompts and was not a reliable safety state.

## CP2P correction

- Replace the redundant checkbox with read-only **HOME verified for this session / HOME not verified** status in Studio, Clean and Sequence.
- When the controller is connected, `physical_home_verified` is true, `position_uncertain` is false, the motion engine is idle and both calibrations are saved, the user can click Run directly. No per-pattern checkbox or duplicate browser confirmation.
- Continue to reject attempts to start if HOME is unverified, position is uncertain, controller disconnected/busy, or calibration incomplete. The server still independently enforces `require_referenced_motion` for direct HTTP calls.
- Redraw the status on `physical_home_verified` updates, instead of waiting for unrelated motion-state changes.
- Preserve the existing physical HOME visual confirmation in Motion. Never persist approval in a browser cookie/localStorage or across controller resets/reconnects.
- Preserve CP2O acknowledgement and HOME protection, the original locked **10:1** kinematics, local saved Theta **78.000** and radial **51.504** values, all eight V2 workspaces, the Home right-side **Next Up** preview/queue, Wi-Fi and Magic Home RGB.

## Safety scope

This is a **frontend usability change**, not evidence that sensorless HOME or subsequent patterns now physically track the ball. Do not run motor tests before verifying HOME and mechanical clearances. The released archive changes only the native V2 frontend and read-only release audit scripts/docs; no backend, serial, kinematic, motor or calibration files changed.
