import json
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.forensics import collect_forensics, collect_memory_dump


SAMPLE_ALERT = {
    "rule": "VCD - Shell spawned in container",
    "priority": "WARNING",
    "container_id": "abc123",
    "proc_pid": "1",
}


def test_collect_forensics_writes_json(tmp_path):
    pid = str(os.getpid())  # use the test process PID — /proc/{pid} exists

    out_path = collect_forensics(
        container_id="abc123def456",
        pid=pid,
        output_dir=str(tmp_path),
        alert=SAMPLE_ALERT,
    )

    assert os.path.exists(out_path)
    with open(out_path) as f:
        data = json.load(f)

    assert data["container_id"] == "abc123def456"
    assert data["proc"]["pid"] == pid
    assert "falco_alert" in data
    assert "timestamp" in data


def test_collect_forensics_missing_pid(tmp_path):
    # pid "0" does not exist — should write file with empty strings, not raise
    out_path = collect_forensics(
        container_id="abc123",
        pid="999999999",
        output_dir=str(tmp_path),
        alert=SAMPLE_ALERT,
    )
    assert os.path.exists(out_path)
    with open(out_path) as f:
        data = json.load(f)
    assert data["proc"]["cmdline"] == ""


def test_collect_forensics_creates_output_dir(tmp_path):
    nested = tmp_path / "deep" / "nested"
    collect_forensics("abc", "999999999", str(nested), SAMPLE_ALERT)
    assert nested.exists()


def test_collect_memory_dump_gcore_failure(tmp_path):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="gcore: permission denied")
        with pytest.raises(RuntimeError, match="gcore failed"):
            collect_memory_dump("1234", str(tmp_path))


def test_collect_memory_dump_success(tmp_path):
    core_file = tmp_path / "core.1234.1234"
    core_file.touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = collect_memory_dump("1234", str(tmp_path))

    assert result == str(tmp_path / "core.1234.1234")
