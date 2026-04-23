import logging
from flask import Flask, request, jsonify
from app.config import config

logger = logging.getLogger(__name__)

app = Flask(__name__)


def parse_alert(payload: dict) -> dict:
    """Extract relevant fields from a Falcosidekick webhook payload."""
    output_fields = payload.get("output_fields", {})
    return {
        "rule": payload.get("rule", ""),
        "priority": payload.get("priority", ""),
        "output": payload.get("output", ""),
        "container_id": output_fields.get("container.id", ""),
        "container_name": output_fields.get("container.name", ""),
        "proc_name": output_fields.get("proc.name", ""),
        "proc_pid": output_fields.get("proc.pid", ""),
    }


def get_target_container_id(alert: dict) -> str:
    """Resolve which container ID to act on."""
    if config.TARGET_CONTAINER:
        return config.TARGET_CONTAINER
    container_id = alert.get("container_id", "")
    if not container_id:
        raise ValueError("Cannot determine target container: no container.id in alert")
    return container_id


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True)
    if not payload:
        logger.warning("Received empty or non-JSON webhook payload")
        return jsonify({"status": "error", "message": "invalid payload"}), 400

    logger.info("Received Falco alert: rule=%s priority=%s",
                payload.get("rule"), payload.get("priority"))

    alert = parse_alert(payload)

    try:
        container_id = get_target_container_id(alert)
    except ValueError as e:
        logger.error("Failed to resolve target container: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 422

    from app.vcd_flow import run_vcd_flow
    run_vcd_flow(container_id, alert)

    return jsonify({"status": "ok", "container_id": container_id}), 200


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200
