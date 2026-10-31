"""Launch an isolated ORYN Studio V2 CP1.2 read-only Windows preview.

Explicit preview URL only. Does not change firmware, profiles, calibration,
application settings, or saved files. Never sends motion commands.
The safe backend binds only to 127.0.0.1 and disables auto-connect/playback.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
BACKEND_URL = "http://127.0.0.1:8080/api/version"
PREVIEW_URL = "http://127.0.0.1:5173/studio-v2"


def ensure_free(port: int) -> None:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(
                f"Port {port} is already in use. Stop earlier ORYN/backend or Vite CMD windows "
                "(Ctrl+C), then retry. No existing process will be killed."
            )


def command(*args: str, cwd: Path = ROOT) -> None:
    print("RUN:", " ".join(args), flush=True)
    subprocess.run(list(args), cwd=str(cwd), check=True)


def wait_for(url: str, process: subprocess.Popen, seconds: int = 90) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"A server exited during startup (exit {process.returncode}). Check preview_logs.")
        try:
            with urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 400:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}. Check preview_logs.")


def main() -> int:
    if sys.platform != "win32":
        print("This one-click launcher is for Windows CMD only.")
        return 1

    print("ORYN Studio V2 CP1.2 — local read-only preview", flush=True)
    print("Preserving the original ORYN application and motion engine.", flush=True)
    ensure_free(8080)
    ensure_free(5173)

    if not VENV_PY.is_file():
        command(sys.executable, "-m", "venv", str(ROOT / ".venv"))

    check = subprocess.run(
        [str(VENV_PY), "-c", "import fastapi, uvicorn, serial, dotenv, svgpathtools, ezdxf"],
        capture_output=True,
    )
    if check.returncode != 0:
        print("Installing Windows Python dependencies (first run only)...", flush=True)
        command(str(VENV_PY), "-m", "pip", "install", "-r", "requirements-nonrpi.txt")

    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js was not found. Install Node.js or add it to PATH.")
    vite = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite.is_file():
        print("Installing V2 frontend dependencies (first run only)...", flush=True)
        npm_cli = ROOT / "tools" / "npm-10.9.2" / "bin" / "npm-cli.js"
        if not npm_cli.is_file():
            raise RuntimeError(f"Bundled npm not found at {npm_cli}. Do not use broken global npm.")
        command(node, str(npm_cli), "ci", cwd=FRONTEND)

    logs = ROOT / "preview_logs"
    logs.mkdir(exist_ok=True)
    processes: list[subprocess.Popen] = []
    files = []
    try:
        # The same safe configuration that previously passed the user's Windows backend test.
        backend_code = (
            "import main; from modules.core.state import state; "
            "state.preferred_port='__none__'; "
            "state.auto_play_enabled=False; "
            "state.led_provider='none'; "
            "import uvicorn; uvicorn.run(main.app, host='127.0.0.1', port=8080, workers=1)"
        )
        back_log = open(logs / "backend.log", "w", encoding="utf-8")
        files.append(back_log)
        print("Starting local backend with motor auto-connect disabled...", flush=True)
        back = subprocess.Popen(
            [str(VENV_PY), "-u", "-c", backend_code], cwd=str(ROOT),
            stdin=subprocess.DEVNULL, stdout=back_log, stderr=subprocess.STDOUT,
        )
        processes.append(back)
        wait_for(BACKEND_URL, back)
        print("Backend ready on 127.0.0.1:8080", flush=True)

        front_log = open(logs / "frontend.log", "w", encoding="utf-8")
        files.append(front_log)
        env = os.environ.copy()
        env["VITE_ORYN_V2_PREVIEW"] = "1"  # Also supports earlier CP1.1 builds.
        front = subprocess.Popen(
            [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=str(FRONTEND), env=env, stdin=subprocess.DEVNULL,
            stdout=front_log, stderr=subprocess.STDOUT,
        )
        processes.append(front)
        wait_for(PREVIEW_URL, front)
        print("\nPreview ready:", PREVIEW_URL, flush=True)
        print("Only the preview reads machine data; the machine should remain unplugged.", flush=True)
        print("Press Ctrl+C in this window to stop both servers.", flush=True)
        webbrowser.open_new_tab(PREVIEW_URL)
        while all(proc.poll() is None for proc in processes):
            time.sleep(1)
        raise RuntimeError("A server stopped unexpectedly. Check preview_logs.")
    except KeyboardInterrupt:
        print("\nStopping ORYN preview servers...", flush=True)
        return 0
    finally:
        for proc in reversed(processes):
            if proc.poll() is None:
                proc.terminate()
        for proc in reversed(processes):
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        for file in files:
            file.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print("\nPREVIEW STARTUP FAILED:", exc, file=sys.stderr)
        print("If there is a backend error, open oryn\\preview_logs\\backend.log", file=sys.stderr)
        print("If there is a frontend error, open oryn\\preview_logs\\frontend.log", file=sys.stderr)
        sys.exit(1)
