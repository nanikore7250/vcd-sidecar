import logging
import threading

from app.config import config
from app.network import isolate_container, remove_isolation
from app.forensics import collect_forensics, collect_memory_dump
from app.terminator import terminate_container

logger = logging.getLogger(__name__)

_active: set[str] = set()
_active_lock = threading.Lock()


def _execute_flow(container_id: str, alert: dict):
    """Execute the VCD flow: isolate → forensics → (optional dump) → terminate → cleanup."""
    pid = alert.get("proc_pid", "")
    isolated_ip: str = ""

    # ① Network isolation (must be first)
    try:
        isolated_ip = isolate_container(container_id)
    except Exception as e:
        logger.error("Network isolation failed for %s: %s", container_id, e)
        # Continue — termination is more important than clean isolation

    # ② Lightweight forensics
    try:
        collect_forensics(container_id, pid, config.FORENSICS_DIR, alert)
    except Exception as e:
        logger.error("Forensics collection failed for %s: %s", container_id, e)

    # ③ Optional memory dump (slow — runs after network isolation)
    if config.MEMORY_DUMP and pid:
        try:
            collect_memory_dump(pid, config.FORENSICS_DIR)
        except Exception as e:
            logger.error("Memory dump failed for pid %s: %s", pid, e)

    # ④ Terminate (stop + remove so Docker Compose recreates a clean container)
    try:
        terminate_container(
            container_id,
            mode=config.TERMINATE_MODE,
            timeout=config.TERMINATE_TIMEOUT,
        )
    except Exception as e:
        logger.error("Termination failed for %s: %s", container_id, e)

    # ⑤ Remove the container so restart: always recreates it fresh from the image.
    #    Without this, Docker merely restarts the same writable layer (dirty state).
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.remove(force=True)
        logger.info("Container %s removed; Docker will recreate it on next restart", container_id)
    except Exception as e:
        logger.error("Container remove failed for %s: %s", container_id, e)

    # ⑥ Remove iptables isolation rules so the recreated container has clean network access.
    if isolated_ip:
        remove_isolation(isolated_ip)

    with _active_lock:
        _active.discard(container_id)


def run_vcd_flow(container_id: str, alert: dict):
    """Kick off the VCD flow in a background thread so the webhook returns fast."""
    with _active_lock:
        if container_id in _active:
            logger.info("VCD flow already in progress for %s, skipping duplicate alert", container_id)
            return
        _active.add(container_id)

    thread = threading.Thread(
        target=_execute_flow,
        args=(container_id, alert),
        daemon=False,
        name=f"vcd-flow-{container_id[:12]}",
    )
    thread.start()
    logger.info("VCD flow started for container %s", container_id)
