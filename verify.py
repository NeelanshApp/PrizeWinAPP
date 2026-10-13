"""Run tests and the real-server check, saving output for the next session."""

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    log_path = root / "verification.log"
    with log_path.open("w", encoding="utf-8", buffering=1) as log:
        def report(message):
            print(message, flush=True)
            log.write(message + "\n")

        report(f"Verification started: {datetime.now(timezone.utc).isoformat()}")
        report(f"Python: {sys.version.split()[0]} ({sys.executable})")
        report(f"Project: {root}")
        report("An incomplete log is not a pass. Look for the final RESULT line.")
        failed = False
        for label, args in (
            ("Ticket logic tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_ticket_logic.py", "-v"]),
            ("Session and backup tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_session_model.py", "-v"]),
            ("Streamlit interaction tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_app.py", "-v"]),
            ("Real Streamlit HTTP startup", ["smoke_check.py"]),
        ):
            report(f"\n{label}")
            try:
                # A file captures diagnostics even if this runner is interrupted.
                result = subprocess.run(
                    [sys.executable, "-u", *args], cwd=root,
                    stdout=log, stderr=subprocess.STDOUT, timeout=180,
                )
                passed = result.returncode == 0
                report(f"{'PASS' if passed else 'FAIL'}: {label} (exit {result.returncode})")
            except (OSError, subprocess.TimeoutExpired) as exc:
                passed = False
                report(f"FAIL: {label}: {exc}")
            failed |= not passed
        report("\nRESULT: " + ("FAILED - see errors above." if failed else "PASS - all checks completed."))
        print(f"Details saved to {log_path}", flush=True)
        return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
