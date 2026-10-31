# ORYN Studio V2 — Windows Python Startup Fix1

Use the **full-source ZIP** if your previous download failed. Extract it into a **new directory**, then open `oryn` and run `run_kinetiq_windows.bat`.

## Why this update exists
The previous launcher used `py -3`, which selected a corrupted Python 3.14 installation on the user's PC (`NameError: name 'sys' is not defined` inside Python's standard library). `venv` creation therefore failed, causing subsequent `.venv\\Scripts\\python.exe` path errors.

## Corrected launch behaviour
- Prefer a working **Python 3.12** (fallback 3.11 or 3.13) with `sys`, `ssl`, `venv` and `ensurepip` imports verified in a subprocess. Reject broken Python 3.14.
- Ignore inherited `PYTHONHOME` and `PYTHONPATH` in the main launcher.
- If a partial/failed `.venv` exists, **rename it to `.venv_failed_...` without deleting it**, then create a fresh environment.
- Verify `venv` creation and installation steps before starting ORYN.
- Run the frontend only after checking the Vite dependency is present; start backend and frontend from explicit working folders.
- Use the same interpreter selector for safe V2 preview, CP2E offline tests and Magic Home LED discovery.

## If no healthy Python was found
Install Python 3.12 (64-bit) from `https://www.python.org/downloads/`; then rerun the launcher. Node.js LTS and npm are also required. Python package installation requires an internet connection on first setup.

## Important preservation statement
Only Windows launcher/tool entrypoints and startup documentation are changed or added. All original CP2E motion files, 10:1 Dune Weaver settings, controller protocols, physical test status, preview UI, patterns, and Magic Home implementation are byte-identical to the previous CP2E Magic Home full source package.

**This update fixes only Windows Python interpreter selection and launcher robustness.** It does **not** certify physical cleaning, drawing, or eliminate the historical mechanical reverse-overtravel fault by itself.

## Validation status
Static archive content audit, source-byte preservation, and Windows launcher contract checks were run in the packaging environment. Native Windows / user hardware launch remains unverified here.
