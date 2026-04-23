import logging
import threading

from app.config import config
from app.network import isolate_container
from app.forensics import collect_forensics, collect_memory_dump
from app.terminator import terminate_container

logger = logging.getLogger(__name__)


def _execute_flow(container_id: str, alert: dict):
    """Execute the VCD flow: isolate → forensics → (optional dump) → terminate."""
    pid = alert.get("proc_pid", "")

    # ① Network isolation (must be first)
    try:
        isolate_container(container_id)
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

    # ④ Terminate
    try:
        terminate_container(
            container_id,
            mode=config.TERMINATE_MODE,
            timeout=config.TERMINATE_TIMEOUT,
        )
    except Exception as e:
        logger.error("Termination failed for %s: %s", container_id, e)


def run_vcd_flow(container_id: str, alert: dict):
    """Kick off the VCD flow in a background thread so the webhook returns fast."""
    thread = threading.Thread(
        target=_execute_flow,
        args=(container_id, alert),
        daemon=True,
        name=f"vcd-flow-{container_id[:12]}",
    )
    thread.start()
    logger.info("VCD flow started for container %s", container_id)
