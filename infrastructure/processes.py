"""Cross-platform ownership records for development processes.

Never adopt a PID based on a name or listening port. A launch token, project path
and creation timestamp must match before a process can be terminated.
"""

from pathlib import Path
import json
import os
import subprocess
from uuid import uuid4

import psutil


def load_record(path: Path) -> dict | None:
    try:
        record = json.loads(path.read_text())
        if record.get("version") != 1 or not record.get("token") or not record.get("project"):
            return None
        return record
    except (OSError, ValueError, AttributeError):
        return None


def members(record: dict) -> list[psutil.Process]:
    if record.get("version") != 1:
        return []
    try:
        parent = psutil.Process(record["pid"])
        if abs(parent.create_time() - record["created_at"]) > 0.01:
            return []  # PID reuse: do not interpret the new process as ours.
    except psutil.NoSuchProcess:
        pass  # Orphaned children still carry our unique launch token.
    except (psutil.AccessDenied, KeyError):
        return []
    owned = []
    for process in psutil.process_iter():
        try:
            env = process.environ()
            if (
                env.get("AX_STACK_TOKEN") == record["token"]
                and env.get("AX_PROJECT_ROOT") == record["project"]
                and process.status() != psutil.STATUS_ZOMBIE
            ):
                owned.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return owned


def start(record_path: Path, root: Path, log_path: Path, command: list[str]):
    previous = load_record(record_path)
    if previous and members(previous):
        raise RuntimeError("Recorded service is still running")
    root = root.resolve()
    token = uuid4().hex
    env = {**os.environ, "AX_STACK_TOKEN": token, "AX_PROJECT_ROOT": str(root)}
    record_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with log_path.open("a") as log:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            **options,
        )
    try:
        created = psutil.Process(process.pid).create_time()
        record_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "pid": process.pid,
                    "created_at": created,
                    "token": token,
                    "project": str(root),
                }
            )
        )
    except psutil.NoSuchProcess:
        process.wait()
        raise RuntimeError("Service exited before its ownership could be recorded") from None
    return process


def stop(record_path: Path) -> None:
    record = load_record(record_path)
    if record:
        owned = members(record)
        for process in reversed(owned):
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(owned, timeout=3)
        for process in alive:
            # Re-check ownership and creation identity before escalation.
            if process in members(record):
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
        psutil.wait_procs(alive, timeout=3)
    record_path.unlink(missing_ok=True)
