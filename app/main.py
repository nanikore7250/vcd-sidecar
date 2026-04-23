import logging
import os
import sys

from app.config import config
from app.webhook import app as flask_app


def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        stream=sys.stdout,
    )


def main():
    _setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config.validate()
    except ValueError as e:
        logger.critical("Invalid configuration: %s", e)
        sys.exit(1)

    os.makedirs(config.FORENSICS_DIR, exist_ok=True)

    logger.info(
        "vcd-sidecar starting on port %d (mode=%s, memory_dump=%s)",
        config.WEBHOOK_PORT,
        config.TERMINATE_MODE,
        config.MEMORY_DUMP,
    )

    flask_app.run(
        host="0.0.0.0",
        port=config.WEBHOOK_PORT,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
