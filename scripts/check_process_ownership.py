"""Real process-ownership regression on Windows or Linux; uses only disposable children."""
from pathlib import Path
import json
import base64
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import psutil
from infrastructure.processes import load_record, members, start, stop


def check():
    if sys.platform == "win32":
        source = str(Path(__file__).resolve().parent / "dev_stack.ps1").replace("'", "''")
        script = ("$binaTokens=$null; $binaErrors=$null; "
                  "[System.Management.Automation.Language.Parser]::ParseFile('" + source +
                  "',[ref]$binaTokens,[ref]$binaErrors)|Out-Null; "
                  "if($binaErrors.Count){$binaErrors|ForEach-Object {$_.Message};exit 1}")
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], check=True)
        print("PASS (win32): PowerShell entrypoint parses")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        own, foreign = root / "own.json", root / "foreign.json"
        sleep = [sys.executable, "-c", "import time; time.sleep(90)"]
        # Child inherits the unique ownership token but is not tied to a service name.
        child_file = root / "child.pid"
        code = ("import subprocess,sys,time; from pathlib import Path; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(90)']); "
                f"Path({str(child_file)!r}).write_text(str(p.pid)); time.sleep(90)")
        ours = start(own, root, root / "own.log", [sys.executable, "-c", code])
        other = start(foreign, root, root / "foreign.log", sleep)
        child = None
        try:
            for _ in range(100):
                if child_file.exists():
                    break
                time.sleep(.05)
            child = psutil.Process(int(child_file.read_text()))
            record = load_record(own)
            assert len(members(record)) >= 2, "Parent and child must both prove ownership"
            reused = root / "reused.json"
            reused.write_text(json.dumps({**record, "created_at": record["created_at"] - 100}))
            stop(reused)
            assert ours.poll() is None and other.poll() is None
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"backend": other.pid}))
            stop(legacy)
            assert other.poll() is None
            # Verify orphan cleanup, too: ownership survives the parent going away.
            ours.terminate()
            ours.wait(timeout=3)
            stop(own)
            assert not child.is_running() or child.status() == psutil.STATUS_ZOMBIE
            assert other.poll() is None, "Another same-toolchain process must survive"
            print(f"PASS ({sys.platform}): stale PID, PID reuse, same-name foreign process, children and orphans")
        finally:
            stop(own)
            stop(foreign)
            ours.wait(timeout=3)
            other.wait(timeout=3)
            if child and child.is_running() and child.status() != psutil.STATUS_ZOMBIE:
                child.kill()


if __name__ == "__main__":
    check()
