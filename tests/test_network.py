import pytest
from unittest.mock import patch, MagicMock
from app.network import get_container_ip, isolate_container, remove_isolation


def _mock_container(ip: str) -> MagicMock:
    container = MagicMock()
    container.attrs = {
        "NetworkSettings": {
            "Networks": {
                "bridge": {"IPAddress": ip}
            }
        }
    }
    return container


def test_get_container_ip():
    with patch("app.network._get_docker_client") as mock_client:
        mock_client.return_value.containers.get.return_value = _mock_container("172.17.0.5")
        ip = get_container_ip("abc123")
    assert ip == "172.17.0.5"


def test_get_container_ip_no_ip():
    container = MagicMock()
    container.attrs = {"NetworkSettings": {"Networks": {"bridge": {"IPAddress": ""}}}}
    with patch("app.network._get_docker_client") as mock_client:
        mock_client.return_value.containers.get.return_value = container
        with pytest.raises(RuntimeError, match="No IP address"):
            get_container_ip("abc123")


def test_isolate_container_calls_iptables():
    with patch("app.network._get_docker_client") as mock_client, \
         patch("app.network._run_iptables") as mock_ipt:
        mock_client.return_value.containers.get.return_value = _mock_container("172.17.0.5")
        ip = isolate_container("abc123")

    assert ip == "172.17.0.5"
    assert mock_ipt.call_count == 2
    calls = [str(c) for c in mock_ipt.call_args_list]
    assert any("172.17.0.5" in c and "-s" in c for c in calls)
    assert any("172.17.0.5" in c and "-d" in c for c in calls)


def test_remove_isolation_calls_iptables():
    with patch("app.network._run_iptables") as mock_ipt:
        remove_isolation("172.17.0.5")
    assert mock_ipt.call_count == 2


def test_remove_isolation_logs_warning_on_failure():
    with patch("app.network._run_iptables", side_effect=RuntimeError("fail")):
        # should not raise — errors are logged as warnings
        remove_isolation("172.17.0.5")
