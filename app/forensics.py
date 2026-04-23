import json
import logging
import os
import subprocess
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _read_proc_text(pid: str, path: str) -> str:
    full_path = f"/proc/{pid}/{path}"
    try:
        with open(full_path, "rb") as f:
            raw = f.read()
        # environ and cmdline are null-separated
        if path in ("environ", "cmdline"):
            return raw.replace(b"\x00", b"\n").decode("utf-8", errors="replace")
        return raw.decode("utf-8", errors="replace")
    except FileNotFoundError:
        logger.warning("proc path not found: %s", full_path)
        return ""
    except PermissionError:
        logger.warning("Permission denied reading: %s", full_path)
        return ""


def _read_proc_fd_links(pid: str) -> list[str]:
    fd_dir = f"/proc/{pid}/fd"
    try:
        fds = os.listdir(fd_dir)
    except (FileNotFoundError, PermissionError) as e:
        logger.warning("Cannot list %s: %s", fd_dir, e)
        return []

    links = []
    for fd in fds:
        try:
            target = os.readlink(f"{fd_dir}/{fd}")
            links.append(f"{fd} -> {target}")
        except OSError:
            pass
    return links


def collect_forensics(
    container_id: str,
    pid: str,
    output_dir: str,
    alert: dict,
) -> str:
    """Collect lightweight forensic data from /proc and write it as JSON.

    Returns the path to the written evidence file.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short_id = container_id[:12]

    evidence = {
        "timestamp": timestamp,
        "container_id": container_id,
        "falco_alert": alert,
        "proc": {
            "pid": pid,
            "cmdline": _read_proc_text(pid, "cmdline"),
            "environ": _read_proc_text(pid, "environ"),
            "net_tcp": _read_proc_text(pid, "net/tcp"),
            "net_tcp6": _read_proc_text(pid, "net/tcp6"),
            "open_files": _read_proc_fd_links(pid),
        },
    }

    out_path = os.path.join(output_dir, f"{timestamp}_{short_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=2)

    logger.info("Forensic evidence written to %s", out_path)
    return out_path


def collect_memory_dump(pid: str, output_dir: str) -> str:
    """Run gcore to capture a memory dump of the process.

    This is optional and slow — always call after network isolation.
    Returns the path to the core file.
    """
    os.makedirs(output_dir, exist_ok=True)
    core_prefix = os.path.join(output_dir, f"core.{pid}")

    logger.info("Starting gcore memory dump for pid %s", pid)
    result = subprocess.run(
        ["gcore", "-o", core_prefix, pid],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gcore failed for pid {pid}: {result.stderr.strip()}")

    core_path = f"{core_prefix}.{pid}"
    logger.info("Memory dump written to %s", core_path)
    return core_path
