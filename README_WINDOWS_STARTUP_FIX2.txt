ORYN Studio V2 CP2E / Magic Home — Windows Startup Fix2
===========================================================

Fixes a Windows npm installation failure:
  Error: Cannot find module ...\npm\node_modules\graceful-fs

Fix2 bundles an isolated npm 10.9.2 JavaScript CLI with its LICENSE and dependencies.
The ORYN launcher runs npm through the detected Node.exe, avoiding the damaged
npm.cmd under the user's AppData\Roaming\npm directory. Node.js itself must work.

1) Extract the full ZIP (recommended) to a new folder, keeping its oryn directory.
2) Inside oryn, double-click run_kinetiq_windows.bat.
3) The launcher should report Python, Node and isolated npm as OK.
4) It then installs frontend dependencies and opens separate backend/frontend windows.
5) Check http://127.0.0.1:5173 after both processes start.

The small PATCH zip is for an existing CP2E + Magic Home Fix1 installation.
Extract its oryn directory over the EXISTING parent folder, preserving other files.
Do not place oryn inside another oryn folder.

Node.js requirements: a working installation on PATH; reported Node v24.21.0 is fine
for this bootstrap. npm 10.9.2 is included only for ORYN, and no global npm
repair, machine config changes, GRBL writes, or application motion changes occur.

To check isolated npm manually from the oryn directory:
  node tools\npm-10.9.2\bin\npm-cli.js --version

Security: bundled npm files include their upstream licenses; internet is still needed
for first-time frontend dependency installation. Installer has not been run on
Windows or on physical hardware within this environment.
