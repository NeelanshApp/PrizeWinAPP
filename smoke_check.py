"""Start the real Streamlit server, check local HTTP health, then stop it."""

from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


def main():
    root = Path(__file__).resolve().parent
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
    except OSError as exc:
        print(f"FAIL: Cannot open a local server socket: {exc}", file=sys.stderr)
        return 1
    opener = build_opener(ProxyHandler({}))
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless=true",
             "--server.address=127.0.0.1", f"--server.port={port}"],
            cwd=root, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with opener.open(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as response:
                        healthy = response.status == 200 and response.read() == b"ok"
                    if healthy:
                        with opener.open(f"http://127.0.0.1:{port}/", timeout=2) as response:
                            if response.status == 200 and b"<html" in response.read().lower():
                                print("PASS: Streamlit health endpoint and app HTML respond over local HTTP.")
                                return 0
                except (URLError, TimeoutError, ConnectionError):
                    pass
                time.sleep(0.25)
            log.seek(0)
            print("FAIL: Streamlit did not start correctly.\n" + log.read(), file=sys.stderr)
            return 1
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
