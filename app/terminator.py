import logging
import docker

logger = logging.getLogger(__name__)

_docker_client = None


def _get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def terminate_container(
    container_id: str,
    mode: str = "graceful",
    timeout: int = 30,
):
    """Terminate the target container.

    Modes:
      graceful — docker stop (SIGTERM, then SIGKILL after default 10 s)
      strict   — docker kill (immediate SIGKILL, no waiting)
      timeout  — docker stop -t N (SIGTERM, then SIGKILL after N seconds)

    Note: SIGTERM-based graceful drain only works when the containerised app
    handles SIGTERM correctly. If it doesn't, the daemon kills it after the
    timeout regardless — this is a known constraint documented in SECURITY.md.
    """
    client = _get_docker_client()
    container = client.containers.get(container_id)

    if mode == "strict":
        logger.info("Terminating container %s (strict / SIGKILL)", container_id)
        container.kill(signal="SIGKILL")

    elif mode == "timeout":
        logger.info(
            "Terminating container %s (timeout=%ds, then SIGKILL)", container_id, timeout
        )
        container.stop(timeout=timeout)

    else:
        # graceful: docker stop uses SIGTERM then SIGKILL after 10 s
        logger.info("Terminating container %s (graceful / SIGTERM→SIGKILL)", container_id)
        container.stop()

    logger.info("Container %s terminated (mode=%s)", container_id, mode)
