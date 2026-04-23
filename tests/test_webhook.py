import json
import pytest
from unittest.mock import patch
from app.webhook import app, parse_alert, get_target_container_id


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


SAMPLE_PAYLOAD = {
    "rule": "VCD - Shell spawned in container",
    "priority": "WARNING",
    "output": "Shell spawned...",
    "output_fields": {
        "container.id": "abc123def456",
        "container.name": "myapp",
        "proc.name": "bash",
        "proc.pid": "1234",
    },
}


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_webhook_valid_payload(client):
    with patch("app.vcd_flow.run_vcd_flow") as mock_flow:
        resp = client.post(
            "/webhook",
            data=json.dumps(SAMPLE_PAYLOAD),
            content_type="application/json",
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["container_id"] == "abc123def456"
    mock_flow.assert_called_once()


def test_webhook_empty_body(client):
    resp = client.post("/webhook", data="", content_type="application/json")
    assert resp.status_code == 400


def test_webhook_no_container_id(client):
    payload = {**SAMPLE_PAYLOAD, "output_fields": {}}
    with patch("app.config.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = ""
        resp = client.post(
            "/webhook",
            data=json.dumps(payload),
            content_type="application/json",
        )
    assert resp.status_code == 422


def test_parse_alert():
    alert = parse_alert(SAMPLE_PAYLOAD)
    assert alert["container_id"] == "abc123def456"
    assert alert["proc_pid"] == "1234"
    assert alert["rule"] == "VCD - Shell spawned in container"


def test_get_target_container_id_from_alert():
    from unittest.mock import patch
    with patch("app.webhook.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = ""
        alert = {"container_id": "abc123"}
        assert get_target_container_id(alert) == "abc123"


def test_get_target_container_id_from_env():
    from unittest.mock import patch
    with patch("app.webhook.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = "forced-container"
        alert = {"container_id": "abc123"}
        assert get_target_container_id(alert) == "forced-container"


def test_get_target_container_id_missing():
    from unittest.mock import patch
    with patch("app.webhook.config") as mock_cfg:
        mock_cfg.TARGET_CONTAINER = ""
        with pytest.raises(ValueError):
            get_target_container_id({"container_id": ""})
