# ORYN Studio V2 — Product Branding Fix

**This is a display-only update.** It changes the customer-facing wording on the approved V2 System and Motion screens, plus their bundled frontend copies. It does not change motion code, GRBL, saved configuration, file playback, LED drivers or homing.

The System screen reports **Motion gear ratio: 10:1 (ORYN standard configuration)** and **ORYN Studio V2 · Studio Kinematics™**.

## Applying to the Pi you already installed

1. Make sure no patterns are currently running.
2. Copy `ORYN_V2_PI_BRANDING_FIX_PATCH.zip` to `/home/oryn/`.
3. On the Pi, run:
   ```bash
   cd ~/oryn
   unzip -o ~/ORYN_V2_PI_BRANDING_FIX_PATCH.zip
   ```
4. Refresh the ORYN browser tab (Ctrl+Shift+R). No service restart is necessary.
5. Open System and Motion; the previous upstream wording should not appear.

## Updating GitHub Desktop
Extract the patch into the root of your Windows `Oryn-V2` repository, inspect changes, commit and push.

Third-party copyright and license obligations remain in source legal files; do not remove them.
