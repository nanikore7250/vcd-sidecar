import os


class Config:
    WEBHOOK_PORT: int = int(os.environ.get("VCD_WEBHOOK_PORT", "8888"))
    FORENSICS_DIR: str = os.environ.get("VCD_FORENSICS_DIR", "/var/vcd/forensics")
    MEMORY_DUMP: bool = os.environ.get("VCD_MEMORY_DUMP", "false").lower() == "true"
    TERMINATE_MODE: str = os.environ.get("VCD_TERMINATE_MODE", "graceful")
    TERMINATE_TIMEOUT: int = int(os.environ.get("VCD_TERMINATE_TIMEOUT", "30"))
    TARGET_CONTAINER: str = os.environ.get("VCD_TARGET_CONTAINER", "")

    @classmethod
    def validate(cls):
        if cls.TERMINATE_MODE not in ("graceful", "strict", "timeout"):
            raise ValueError(
                f"Invalid VCD_TERMINATE_MODE: {cls.TERMINATE_MODE!r}. "
                "Must be one of: graceful, strict, timeout"
            )
        if cls.TERMINATE_TIMEOUT <= 0:
            raise ValueError("VCD_TERMINATE_TIMEOUT must be a positive integer")


config = Config()
