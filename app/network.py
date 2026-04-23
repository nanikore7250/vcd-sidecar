import logging
import subprocess
import docker

logger = logging.getLogger(__name__)

_docker_client = None


def _get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def get_container_ip(container_id: str) -> str:
    client = _get_docker_client()
    container = client.containers.get(container_id)
    networks = container.attrs["NetworkSettings"]["Networks"]
    for net in networks.values():
        ip = net.get("IPAddress", "")
        if ip:
            return ip
    raise RuntimeError(f"No IP address found for container {container_id}")


def _run_iptables(args: list[str]):
    cmd = ["iptables"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"iptables failed: {result.stderr.strip()}")


def isolate_container(container_id: str) -> str:
    """Block all inbound and outbound FORWARD traffic for the container's IP.

    Returns the IP that was isolated so callers can clean it up later if needed.
    """
    ip = get_container_ip(container_id)
    logger.info("Isolating container %s at IP %s", container_id, ip)

    _run_iptables(["-I", "FORWARD", "-s", ip, "-j", "DROP"])
    _run_iptables(["-I", "FORWARD", "-d", ip, "-j", "DROP"])

    logger.info("Network isolation applied for %s (%s)", container_id, ip)
    return ip


def remove_isolation(ip: str):
    """Remove previously applied isolation rules (cleanup / rollback)."""
    try:
        _run_iptables(["-D", "FORWARD", "-s", ip, "-j", "DROP"])
        _run_iptables(["-D", "FORWARD", "-d", ip, "-j", "DROP"])
        logger.info("Network isolation removed for %s", ip)
    except RuntimeError as e:
        logger.warning("Failed to remove isolation rules for %s: %s", ip, e)
