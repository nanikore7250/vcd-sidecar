import pytest
from unittest.mock import patch, MagicMock
from app.terminator import terminate_container


def _mock_container() -> MagicMock:
    return MagicMock()


def test_graceful_mode():
    with patch("app.terminator._get_docker_client") as mock_client:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container
        terminate_container("abc123", mode="graceful")
    container.stop.assert_called_once_with()
    container.kill.assert_not_called()


def test_strict_mode():
    with patch("app.terminator._get_docker_client") as mock_client:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container
        terminate_container("abc123", mode="strict")
    container.kill.assert_called_once_with(signal="SIGKILL")
    container.stop.assert_not_called()


def test_timeout_mode():
    with patch("app.terminator._get_docker_client") as mock_client:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container
        terminate_container("abc123", mode="timeout", timeout=45)
    container.stop.assert_called_once_with(timeout=45)
    container.kill.assert_not_called()


def test_default_mode_is_graceful():
    with patch("app.terminator._get_docker_client") as mock_client:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container
        terminate_container("abc123")
    container.stop.assert_called_once_with()
