"""ORYN Windows startup supervisor Fix4.

Only manages Python/Node installations and ORYN process startup. It does not
read or write GRBL/serial port settings, calibrations, or application source.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "startup_logs"
BACKEND = "http://127.0.0.1:8080/api/version"
FRONTEND = "http://127.0.0.1:5173/"
OPEN_UI = "http://127.0.0.1:5173/"
CREATE_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def info(message: str) -> None:
    print(message, flush=True)


def die(message: str) -> None:
    raise RuntimeError(message)


def check_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as reply:
            return 200 <= reply.status < 400
    except (OSError, urllib.error.URLError, ValueError):
        return False


def tail(path: Path, n: int = 55) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            lines = stream.readlines()
        return "".join(lines[-n:]).rstrip() or "(log empty)"
    except OSError as exc:
        return f"(log unavailable: {exc})"


def run_checked(cmd: list[str], *, cwd: Path, log: Path, label: str) -> None:
    info(f"[RUN] {label} — output also saved to {log.name}")
    with log.open("w", encoding="utf-8", errors="replace") as stream:
        process = subprocess.Popen(cmd, cwd=str(cwd), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, errors="replace", bufsize=1,
                                   creationflags=CREATE_FLAGS)
        assert process.stdout is not None
        for line in process.stdout:
            stream.write(line)
            stream.flush()
            info(line.rstrip("\n"))
        code = process.wait()
    if code:
        die(f"{label} failed (exit {code}). See {log}")


def python_healthy(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        result = subprocess.run(
            [str(path), "-I", "-c", "import sys,ssl,pip,venv; assert (3,11) <= sys.version_info[:2] <= (3,13)"],
            capture_output=True, timeout=12, creationflags=CREATE_FLAGS,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def module_healthy(path: Path) -> bool:
    try:
        result = subprocess.run(
            [str(path), "-I", "-c", "import fastapi,uvicorn,serial,dotenv,svgpathtools,ezdxf"],
            capture_output=True, timeout=25, creationflags=CREATE_FLAGS,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_python() -> Path:
    venv = ROOT / ".venv"
    python = venv / "Scripts" / "python.exe"
    if not python_healthy(python):
        if venv.exists():
            name = f".venv_failed_fix4_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup = ROOT / name
            info(f"[NOTICE] Previous Python environment is invalid; preserving it as {name}")
            venv.rename(backup)
        info(f"[SETUP] Creating virtual environment with {sys.executable}")
        run_checked([sys.executable, "-I", "-m", "venv", str(venv)], cwd=ROOT,
                    log=LOGS / "venv_setup.log", label="Python environment creation")
    if not python_healthy(python):
        die("Python environment still unhealthy; see startup_logs/venv_setup.log")
    info(f"[OK] Python 3 environment: {python}")
    if not module_healthy(python):
        info("[SETUP] Installing missing backend dependencies; not touching motor settings")
        run_checked([str(python), "-m", "pip", "install", "-r", "requirements-nonrpi.txt"],
                    cwd=ROOT, log=LOGS / "backend_install.log", label="Backend dependencies")
    if not module_healthy(python):
        die("Backend imports fail even after installation; see startup_logs/backend_install.log")
    info("[OK] Backend Python dependencies")
    return python


def ensure_node() -> tuple[str, Path]:
    node = shutil.which("node.exe") or shutil.which("node")
    if not node:
        die("Node.js not found. Node.js is required; Python alone cannot start ORYN V2 UI.")
    check = subprocess.run([node, "-e", "require('node:fs');require('node:path')"],
                           capture_output=True, timeout=12, creationflags=CREATE_FLAGS)
    if check.returncode:
        die(f"Node.js is not healthy: {node}")
    info(f"[OK] Node.js: {node}")
    vite = ROOT / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite.is_file():
        npm = ROOT / "tools" / "npm-10.9.2" / "bin" / "npm-cli.js"
        if not npm.is_file():
            die("Bundled isolated npm missing. Apply the Fix2 FULL package first, then Fix4.")
        info("[SETUP] Frontend packages missing; installing through bundled npm (not global npm)")
        run_checked([node, str(npm), "ci", "--no-audit", "--no-fund"], cwd=ROOT / "frontend",
                    log=LOGS / "frontend_install.log", label="Frontend dependencies")
    if not vite.is_file():
        die("Vite still missing after installation; see startup_logs/frontend_install.log")
    info("[OK] Frontend Vite executable")
    return node, vite


def start_process(cmd: list[str], *, cwd: Path, log: Path) -> tuple[subprocess.Popen, object]:
    fp = log.open("w", encoding="utf-8", errors="replace")
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdin=subprocess.DEVNULL,
                                stdout=fp, stderr=subprocess.STDOUT,
                                creationflags=CREATE_FLAGS)
    except BaseException:
        fp.close()
        raise
    return proc, fp


def wait_service(name: str, url: str, proc: subprocess.Popen, log: Path, deadline: float) -> None:
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            info(f"\n[FAIL] {name} exited with code {proc.returncode}. Recent log:\n{tail(log)}\n")
            die(f"{name} stopped during startup; see {log}")
        if http_ok(url):
            info(f"[OK] {name}: {url}")
            return
        time.sleep(1)
    info(f"\n[FAIL] {name} did not respond. Recent log:\n{tail(log)}\n")
    die(f"{name} did not become ready; see {log}")


def main() -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    info("=" * 62)
    info("  ORYN Studio V2 - WINDOWS STARTUP FIX4 (ONE WINDOW)")
    info("  Python 3.12 / Isolated npm / Saved logs / No silent exit")
    info("=" * 62)
    info(f"[INFO] Source folder: {ROOT}")
    info(f"[INFO] Log folder: {LOGS}")
    info("[SAFE] No GRBL settings, theta/rho math, machine profiles or LED settings are changed.")
    if sys.platform != "win32":
        die("This Fix4 launcher is for Windows only.")
    if not (ROOT / "main.py").is_file() or not (ROOT / "frontend" / "package.json").is_file():
        die("Fix4 script is not inside the ORYN root: expected main.py and frontend/package.json")
    busy = [p for p in (8080, 5173) if check_port(p)]
    if busy:
        info(f"[INFO] Listening port(s) already detected: {busy}")
        if http_ok(BACKEND) and http_ok(FRONTEND):
            info("[OK] Both ORYN services are already answering. Opening the V2 UI.")
            webbrowser.open(OPEN_UI)
            return 0
        die("A required port is already occupied, possibly by an old ORYN. Close its terminal windows and rerun Fix4. Fix4 will not kill programs.")
    py = ensure_python()
    node, vite = ensure_node()
    children: list[tuple[subprocess.Popen, object]] = []
    backlog = LOGS / "backend_runtime.log"
    frontlog = LOGS / "frontend_runtime.log"
    try:
        info("[START] Starting ORYN backend (port 8080) ...")
        backend, f = start_process([str(py), "-u", "main.py"], cwd=ROOT, log=backlog)
        children.append((backend, f))
        wait_service("Backend", BACKEND, backend, backlog, time.monotonic()+75)
        info("[START] Starting ORYN frontend (port 5173) ...")
        # Use absolute Vite executable, not npm.cmd or Node from the broken global package.
        frontend, f = start_process([node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
                                    cwd=ROOT / "frontend", log=frontlog)
        children.append((frontend, f))
        wait_service("Frontend", FRONTEND, frontend, frontlog, time.monotonic()+90)
        info("\n"+"="*62)
        info("[READY] ORYN frontend and backend are responding.")
        info("[OPEN]  http://127.0.0.1:5173 (standard app)")
        info("[PREVIEW ONLY] http://127.0.0.1:5173/studio-v2")
        info("[NOTE] HTTP readiness does not prove controller connection or physical motion.")
        info("[NOTE] Keep this FIX4 terminal OPEN while using ORYN.")
        info("[STOP] Press Ctrl+C here to stop both ORYN servers.")
        info("="*62+"\n")
        webbrowser.open(OPEN_UI)
        while True:
            for name, proc, log in (("Backend", backend, backlog), ("Frontend", frontend, frontlog)):
                if proc.poll() is not None:
                    info(f"[FAIL] {name} stopped unexpectedly (exit {proc.returncode}).\n{tail(log)}")
                    die(f"{name} stopped unexpectedly. Check {log}")
            time.sleep(2)
    except KeyboardInterrupt:
        info("\n[STOP] Closing ORYN backend/frontend. No machine settings changed.")
        return 0
    finally:
        for proc, fp in reversed(children):
            if proc.poll() is None:
                proc.terminate()
        for proc, fp in reversed(children):
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=8)
            finally:
                fp.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("\n[FIX4 STARTUP FAILED]", str(exc), flush=True)
        print("[LOGS]", LOGS, flush=True)
        traceback.print_exc()
        raise SystemExit(1)
