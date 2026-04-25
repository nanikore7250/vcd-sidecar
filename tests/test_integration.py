"""
Integration tests — require a running Docker daemon.

Run with:
    pytest tests/test_integration.py -v -m integration

These tests spin up a real container, send a webhook, and verify the
VCD flow executes end-to-end without network isolation (no NET_ADMIN
required in CI). Termination is verified via Docker API.
"""
import json
import os
import time
import pytest
import docker as docker_sdk
from unittest.mock import patch

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def docker_client():
    try:
        client = docker_sdk.from_env()
        client.ping()
        return client
    except Exception:
        pytest.skip("Docker daemon not available")


@pytest.fixture
def target_container(docker_client):
    """Start a short-lived Alpine container as the VCD target."""
    container = docker_client.containers.run(
        "alpine:latest",
        command="sleep 300",
        detach=True,
        remove=False,
    )
    yield container
    try:
        container.remove(force=True)
    except docker_sdk.errors.NotFound:
        pass  # vcd_flow already removed it — that's expected


@pytest.fixture
def flask_client():
    from app.webhook import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_payload(container_id: str, pid: str = "1") -> dict:
    return {
        "rule": "VCD - Shell spawned in container",
        "priority": "WARNING",
        "output": "Integration test alert",
        "output_fields": {
            "container.id": container_id,
            "container.name": "test-target",
            "proc.name": "sh",
            "proc.pid": pid,
        },
    }


def test_webhook_triggers_termination(flask_client, target_container, docker_client, tmp_path):
    container_id = target_container.id

    with patch("app.config.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = ""
        mock_cfg.FORENSICS_DIR = str(tmp_path)
        mock_cfg.MEMORY_DUMP = False
        mock_cfg.TERMINATE_MODE = "strict"
        mock_cfg.TERMINATE_TIMEOUT = 10

        # Bypass iptables (no NET_ADMIN in test environment)
        with patch("app.network.isolate_container"):
            resp = flask_client.post(
                "/webhook",
                data=json.dumps(_make_payload(container_id)),
                content_type="application/json",
            )

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    # Wait for the background thread to terminate and remove the container
    deadline = time.time() + 10
    removed = False
    while time.time() < deadline:
        try:
            target_container.reload()
            if target_container.status in ("exited", "dead", "removing"):
                break
        except docker_sdk.errors.NotFound:
            removed = True
            break
        time.sleep(0.5)

    if not removed:
        try:
            target_container.reload()
            final_status = target_container.status
        except docker_sdk.errors.NotFound:
            final_status = "removed"
        assert final_status in ("exited", "dead", "removed"), (
            f"Container was not terminated: status={final_status}"
        )


def test_forensics_file_written(flask_client, target_container, docker_client, tmp_path):
    container_id = target_container.id

    with patch("app.config.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = ""
        mock_cfg.FORENSICS_DIR = str(tmp_path)
        mock_cfg.MEMORY_DUMP = False
        mock_cfg.TERMINATE_MODE = "strict"
        mock_cfg.TERMINATE_TIMEOUT = 10

        with patch("app.network.isolate_container"):
            flask_client.post(
                "/webhook",
                data=json.dumps(_make_payload(container_id, pid="1")),
                content_type="application/json",
            )

    # Allow background thread to complete
    time.sleep(2)

    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) >= 1, "No forensic evidence file was written"

    with open(json_files[0]) as f:
        data = json.load(f)

    assert data["container_id"] == container_id
    assert "timestamp" in data
    assert "proc" in data
