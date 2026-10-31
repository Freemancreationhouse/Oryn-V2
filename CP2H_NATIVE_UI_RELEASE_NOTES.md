# ORYN Studio V2 — CP2H Native Controls Update

Product: ORYN — Designed to Move, by Studio Kinematics™.

This update replaces the prior embedded controls window in the Pi V2 frontend with native ORYN UI. No backend, motor math, firmware, GRBL settings, or saved calibration is modified.

## Native features in this update
- Motion: Pi serial port scanning and connection, home and center/perimeter actions, physical calibration controls for one full theta revolution and center-to-perimeter rho travel, calibrated values and read-only status.
- System: controller/firmware status, machine readiness and supported transports. A disconnected controller displays "Connect controller to identify" rather than a misleading firmware-failure claim. Firmware is NEVER automatically flashed.
- Sequence: basic native playlist creation, selection and reordering.
- Studio: source-backed Pattern Forge upload/preview/save and THR import. Original artwork and motion execution remain handled by the existing backend.
- Gallery, Clean, Light: native V2 screens preserved; Magic Home + ORYN GPIO selected provider controls routed to their corresponding backend endpoints.
- The former complete-controls iframe is not reachable from the frontend; the prior UI entry page redirects to V2.

## Important limitations
- Tested with a simulated browser backend; not physically tested on your Pi with your particular controller.
- Some advanced source-backed options (e.g. all custom GPIO effects, scheduled rules, network provisioning, security settings, advanced playlist run modes) do not yet have full native V2 configuration screens. Their backend implementation is retained. No claim of complete feature parity.
- Firmware display requires a real connected controller and a successful firmware identification response. An unidentified connection is not proof that firmware is absent.
- Home, pattern and cleaning require real physical homing/calibration verification. Do not trust GRBL MPos alone for position.

## Safe install on an already working Pi
With motors disabled and controller disconnected during update, transfer ZIP to Pi home folder. Then run:

    cd ~
    unzip -o ORYN_V2_PI_CP2H_NATIVE_UI_PATCH.zip

No service restart is necessary for these static frontend-only changes. Visit http://192.168.0.224 and press Ctrl+Shift+R.

If using GitHub Desktop, apply the same files to your ORYN V2 clone, commit and push. A direct Pi patch creates local Git working tree changes; commit the same changes upstream before using git pull again.

## Source preservation
All files outside the six frontend files above remain byte-for-byte unchanged from the provided CP2G base archive. The core protected verification passes (81 source files). Original 10:1 configuration is unchanged.

Required third-party copyright/license notices, where applicable, remain in the source/legal materials and are not presented as product branding.
