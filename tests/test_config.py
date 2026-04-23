import os
import pytest
import importlib


def _reload_config(env: dict):
    """Reload config module with patched environment."""
    with pytest.MonkeyPatch().context() as mp:
        for k, v in env.items():
            mp.setenv(k, v)
        import app.config as cfg_mod
        importlib.reload(cfg_mod)
        return cfg_mod.Config()


def test_defaults():
    cfg = _reload_config({})
    assert cfg.WEBHOOK_PORT == 8888
    assert cfg.FORENSICS_DIR == "/var/vcd/forensics"
    assert cfg.MEMORY_DUMP is False
    assert cfg.TERMINATE_MODE == "graceful"
    assert cfg.TERMINATE_TIMEOUT == 30
    assert cfg.TARGET_CONTAINER == ""


def test_env_overrides():
    cfg = _reload_config({
        "VCD_WEBHOOK_PORT": "9999",
        "VCD_FORENSICS_DIR": "/tmp/forensics",
        "VCD_MEMORY_DUMP": "true",
        "VCD_TERMINATE_MODE": "strict",
        "VCD_TERMINATE_TIMEOUT": "60",
        "VCD_TARGET_CONTAINER": "myapp",
    })
    assert cfg.WEBHOOK_PORT == 9999
    assert cfg.FORENSICS_DIR == "/tmp/forensics"
    assert cfg.MEMORY_DUMP is True
    assert cfg.TERMINATE_MODE == "strict"
    assert cfg.TERMINATE_TIMEOUT == 60
    assert cfg.TARGET_CONTAINER == "myapp"


def test_validate_invalid_mode():
    cfg = _reload_config({"VCD_TERMINATE_MODE": "invalid"})
    with pytest.raises(ValueError, match="VCD_TERMINATE_MODE"):
        cfg.validate()


def test_validate_invalid_timeout():
    cfg = _reload_config({"VCD_TERMINATE_TIMEOUT": "0"})
    with pytest.raises(ValueError, match="VCD_TERMINATE_TIMEOUT"):
        cfg.validate()


def test_validate_valid_modes():
    for mode in ("graceful", "strict", "timeout"):
        cfg = _reload_config({"VCD_TERMINATE_MODE": mode})
        cfg.validate()  # must not raise
