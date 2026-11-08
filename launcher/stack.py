"""
一键开聊编排：Windows 后端 +（必要时）WSL 前端。

Hindsight 提供长期记忆；日常路径不再依赖用户手敲 PowerShell。
"""

from __future__ import annotations

import json
import os
import re
import shlex
from infrastructure.processes import load_record, members, start as start_owned, stop as stop_owned
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


FRONTEND_URL = "http://127.0.0.1:3000/solo"
BACKEND_HEALTH_URL = "http://127.0.0.1:8000/api/v1/health"
PROACTIVE_PENDING_URL = "http://127.0.0.1:8000/api/v1/proactive/pending"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
HINDSIGHT_PORT = 8888

_WSL_UNC_RE = re.compile(
    r"^\\\\(?:wsl\.localhost|wsl\$)\\([^\\]+)\\(.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ServiceStatus:
    hindsight: bool
    backend: bool
    frontend: bool

    @property
    def all_up(self) -> bool:
        return self.hindsight and self.backend and self.frontend

    @property
    def ready_for_browser(self) -> bool:
        return self.hindsight and self.backend and self.frontend

    @property
    def label(self) -> str:
        if self.ready_for_browser:
            return "就绪"
        if self.backend or self.frontend:
            return "启动中"
        return "未启动"


def _looks_like_project_root(root: Path) -> bool:
    try:
        return (root / "main.py").is_file() or (
            root / "scripts" / "dev_stack.ps1"
        ).is_file()
    except OSError:
        return False


def find_project_root(start: Optional[Path] = None) -> Path:
    """定位仓库根。

    注意：从 ``\\\\wsl.localhost\\...`` 双击 .cmd 时，CMD 不能把 UNC 当 cwd，
    常误落到 ``C:\\Windows``。因此优先信任 ``start`` / ``__file__``，
    仅在 ``AX_PROJECT_ROOT`` 指向真实项目时才采用环境变量。
    """
    candidates: list[Path] = []

    def _add(p: Optional[Path]) -> None:
        if p is None:
            return
        try:
            candidates.append(p.resolve())
        except Exception:
            candidates.append(p)

    _add(start)

    env = (os.environ.get("AX_PROJECT_ROOT") or "").strip()
    if env:
        env_root = Path(env).expanduser()
        try:
            env_root = env_root.resolve()
        except Exception:
            pass
        if _looks_like_project_root(env_root):
            return env_root

    if getattr(sys, "frozen", False):
        _add(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            _add(Path(meipass))
    _add(Path(__file__).resolve().parent)
    try:
        _add(Path.cwd())
    except Exception:
        pass

    seen: set[Path] = set()
    for base in candidates:
        cur = base
        for _ in range(8):
            if cur in seen:
                break
            seen.add(cur)
            if (cur / "main.py").is_file() and (cur / "frontend").is_dir():
                return cur
            if (cur / "scripts" / "dev_stack.ps1").is_file():
                return cur
            if cur.parent == cur:
                break
            cur = cur.parent

    raise FileNotFoundError(
        "找不到项目根。请在仓库根运行，或设置有效的 AX_PROJECT_ROOT（勿指向 C:\\Windows）。"
    )


def local_data_dir() -> Path:
    # 与日常手工启动保持同一数据目录，避免“换启动器就换库”
    path = Path.home() / ".axiodrasil"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    env = (os.environ.get("AX_DB_PATH") or "").strip()
    if env:
        return Path(env)
    return local_data_dir() / "axiodrasil_core.db"


def logs_dir(root: Optional[Path] = None) -> Path:
    """优先本机目录，避免写 WSL UNC 日志卡顿。"""
    path = local_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pid_file() -> Path:
    return local_data_dir() / "launcher_pids.json"


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_ok(url: str, timeout: float = 10.0) -> bool:
    """本机 health 偶发 4s+（SQLite）；默认超时放宽。"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(getattr(resp, "status", 200)) < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def probe_status() -> ServiceStatus:
    # 启动器以端口为准：health 过慢会导致误判“未就绪”并误杀进程
    hindsight = port_open("127.0.0.1", HINDSIGHT_PORT)
    backend = port_open("127.0.0.1", BACKEND_PORT)
    frontend = port_open("127.0.0.1", FRONTEND_PORT)
    return ServiceStatus(hindsight=hindsight, backend=backend, frontend=frontend)


def _norm_unc(path: Path) -> str:
    # Path 在部分环境下会把 \\ 收成 \；探测时用字符串更稳
    s = str(path)
    if s.startswith("\\\\"):
        return s
    # pathlib 偶发变成 \wsl.localhost\...
    if s.lower().startswith("\\wsl"):
        return "\\" + s
    return s


def wsl_linux_path(root: Path) -> Optional[str]:
    """若项目根在 WSL UNC，返回 Linux 绝对路径；否则 None。"""
    raw = _norm_unc(root)
    m = _WSL_UNC_RE.match(raw.replace("/", "\\"))
    if not m:
        # 也尝试 resolve 后的字符串
        try:
            raw2 = _norm_unc(root.resolve())
        except Exception:
            raw2 = raw
        m = _WSL_UNC_RE.match(raw2.replace("/", "\\"))
    if not m:
        return None
    rest = m.group(2).replace("\\", "/").lstrip("/")
    return "/" + rest


def wsl_distro(root: Path) -> Optional[str]:
    raw = _norm_unc(root).replace("/", "\\")
    m = _WSL_UNC_RE.match(raw)
    if m:
        return m.group(1)
    return None


def _quote_ps(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _record(root: Path, name: str) -> Path:
    return root / ".devstack" / f"windows-{name}.json"


def _ensure_backend(root: Path, lines: list[str], _pids: dict) -> None:
    record = load_record(_record(root, "backend"))
    if port_open("127.0.0.1", BACKEND_PORT):
        if record and members(record):
            lines.append("后端已在运行")
            return
        raise RuntimeError("8000 端口被未验证归属的进程占用；请在原终端管理该进程。")
    db = default_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    command = f"$env:AX_DB_PATH={_quote_ps(str(db))}; python -m uvicorn main:app --host 127.0.0.1 --port 8000"
    start_owned(_record(root, "backend"), root, logs_dir(root) / "backend.log",
                ["powershell", "-NoProfile", "-Command", command])
    lines.append("后端已启动")


def _ensure_frontend(root: Path, lines: list[str], _pids: dict) -> None:
    linux, distro = wsl_linux_path(root), wsl_distro(root)
    if linux and distro:
        # WSL owns its own process record; never scan names or terminate by port.
        command = f"cd {shlex.quote(linux)} && {shlex.quote(linux + "/.venv/bin/python")} scripts/stack_process.py start .devstack/frontend.json -- bash -lc {shlex.quote('cd ' + shlex.quote(linux + '/frontend') + ' && npm run dev')}"
        if port_open("127.0.0.1", FRONTEND_PORT):
            status = f"cd {shlex.quote(linux)} && {shlex.quote(linux + "/.venv/bin/python")} scripts/stack_process.py status .devstack/frontend.json"
            subprocess.run(["wsl", "-d", distro, "--", "bash", "-lc", status], check=True)
            return
        subprocess.run(["wsl", "-d", distro, "--", "bash", "-lc", command], check=True)
    else:
        record = load_record(_record(root, "frontend"))
        if port_open("127.0.0.1", FRONTEND_PORT):
            if record and members(record):
                return
            raise RuntimeError("3000 端口被未验证归属的进程占用。")
        command = f"Set-Location {_quote_ps(str(root / 'frontend'))}; npm run dev"
        start_owned(_record(root, "frontend"), root, logs_dir(root) / "frontend.log",
                    ["powershell", "-NoProfile", "-Command", command])
    lines.append("前端已启动")


def start_stack(root: Path, services: set[str] | None = None) -> tuple[int, str]:
    """启动 Hindsight、后端和前端。返回 (0|非0, 日志文本)。"""
    lines: list[str] = []
    targets = services or {"hindsight", "backend", "frontend"}
    st = probe_status()

    log_dir = logs_dir(root)
    pids = {}

    if "hindsight" in targets and not st.hindsight:
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "hindsight"],
            cwd=root, capture_output=True, text=True, timeout=300,
        )
        if result.returncode:
            return result.returncode, result.stderr
        lines.append("Hindsight 已启动")

    if "backend" in targets:
        _ensure_backend(root, lines, pids)
    if "frontend" in targets:
        _ensure_frontend(root, lines, pids)

    # 等待端口就绪（冷启动 / WSL 前端可能偏慢）
    deadline = time.time() + 90
    while time.time() < deadline:
        if all(getattr(probe_status(), name) for name in targets):
            lines.append("Bina已就绪，可以开聊。")
            return 0, "\n".join(lines)
        time.sleep(0.8)

    if all(getattr(probe_status(), name) for name in targets):
        lines.append("Bina已就绪，可以开聊。")
        return 0, "\n".join(lines)

    lines.append("启动超时：后端或前端尚未就绪，可查看日志。")
    lines.append(f"日志目录：{log_dir}")
    return 1, "\n".join(lines)


def stop_stack(root: Path, services: set[str] | None = None) -> tuple[int, str]:
    """Stop only verified launches. Legacy PID-only records are deliberately ignored."""
    targets = services or {"hindsight", "backend", "frontend"}
    for name in targets - {"hindsight"}:
        stop_owned(_record(root, name))
    linux, distro = wsl_linux_path(root), wsl_distro(root)
    if "frontend" in targets and linux and distro:
        command = f"cd {shlex.quote(linux)} && {shlex.quote(linux + "/.venv/bin/python")} scripts/stack_process.py stop .devstack/frontend.json"
        subprocess.run(["wsl", "-d", distro, "--", "bash", "-lc", command], check=True)
    if "hindsight" not in targets:
        return 0, "已停止本项目记录的进程。"
    result = subprocess.run(["docker", "compose", "stop", "hindsight"], cwd=root,
                            capture_output=True, text=True, timeout=90)
    return result.returncode, "已停止本项目记录的进程。" + (result.stderr or "")


def run_dev_stack(root: Path, action: str, *, timeout: float = 180.0) -> tuple[int, str]:
    """兼容旧入口：start/stop 走一键编排；其余仍可委托 ps1。"""
    action = (action or "").strip().lower()
    if action == "start":
        return start_stack(root)
    if action == "stop":
        return stop_stack(root)
    if action == "restart":
        code1, out1 = stop_stack(root)
        code2, out2 = start_stack(root)
        return (0 if code2 == 0 else max(code1, code2)), (out1 + "\n" + out2).strip()

    script = root / "scripts" / "dev_stack.ps1"
    if not script.is_file():
        return 1, f"未知动作 {action}，且缺少 {script}"

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-Action",
        action,
        "-All",
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        return 124, out.strip() or f"dev_stack {action} timed out after {timeout}s"

    out = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return int(completed.returncode), out


def open_frontend_in_browser() -> None:
    import webbrowser

    webbrowser.open(FRONTEND_URL)


def fetch_proactive_pending(timeout: float = 4.0) -> list[dict]:
    """拉取后端未读主动消息；失败返回空列表。"""
    try:
        with urllib.request.urlopen(PROACTIVE_PENDING_URL, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
    except Exception:
        return []
    return []


def ensure_frontend(root: Path, *, timeout: float = 90.0) -> bool:
    """确保前端端口可用；必要时只补启前端。"""
    lines: list[str] = []
    pids = {}
    _ensure_frontend(root, lines, pids)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_open("127.0.0.1", FRONTEND_PORT):
            return True
        time.sleep(0.8)
    return port_open("127.0.0.1", FRONTEND_PORT)


def _xml_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def show_windows_toast(title: str, body: str) -> None:
    """Windows 通知（PowerShell Toast）；失败则静默。"""
    t = _xml_escape(title or "Axiodrasil")
    b = _xml_escape((body or "")[:180])
    # 用双引号 here-string，避免单引号字符串无法嵌入复杂内容
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; "
        f"$template = @\"\n<toast><visual><binding template=\"ToastGeneric\">"
        f"<text>{t}</text><text>{b}</text></binding></visual></toast>\n\"@; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$xml.LoadXml($template); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Axiodrasil').Show($toast)"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=12,
            shell=False,
        )
    except Exception:
        pass
