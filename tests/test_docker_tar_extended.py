"""Additional tests for docker-tar command to improve coverage."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.commands.docker_tar import (
    check_image_exists,
    generate_filename,
    parse_image_reference,
    run_docker_command,
)

runner = CliRunner()


def test_parse_image_reference_simple() -> None:
    """Test parsing simple image reference."""
    registry, namespace, image, tag = parse_image_reference("nginx")
    assert registry == "docker.io"
    assert namespace == "library"
    assert image == "nginx"
    assert tag == "latest"


def test_parse_image_reference_with_tag() -> None:
    """Test parsing image reference with tag."""
    registry, namespace, image, tag = parse_image_reference("nginx:1.19")
    assert registry == "docker.io"
    assert namespace == "library"
    assert image == "nginx"
    assert tag == "1.19"


def test_parse_image_reference_with_namespace() -> None:
    """Test parsing image reference with namespace."""
    registry, namespace, image, tag = parse_image_reference("user/image")
    assert registry == "docker.io"
    assert namespace == "user"
    assert image == "image"
    assert tag == "latest"


def test_parse_image_reference_with_registry() -> None:
    """Test parsing image reference with registry."""
    registry, namespace, image, tag = parse_image_reference(
        "registry.example.com/image"
    )
    assert registry == "registry.example.com"
    assert namespace == "library"
    assert image == "image"
    assert tag == "latest"


def test_parse_image_reference_full() -> None:
    """Test parsing full image reference."""
    registry, namespace, image, tag = parse_image_reference(
        "registry.example.com/namespace/image:tag"
    )
    assert registry == "registry.example.com"
    assert namespace == "namespace"
    assert image == "image"
    assert tag == "tag"


def test_generate_filename() -> None:
    """Test generating filename from image parts."""
    filename = generate_filename("docker.io", "library", "nginx", "latest", "amd64")
    assert filename == "nginx__latest__amd64.tar"


def test_generate_filename_with_registry() -> None:
    """Test generating filename with non-default registry."""
    filename = generate_filename(
        "registry.example.com", "library", "nginx", "latest", "amd64"
    )
    assert filename == "registry.example.com__nginx__latest__amd64.tar"


def test_generate_filename_with_namespace() -> None:
    """Test generating filename with non-default namespace."""
    filename = generate_filename("docker.io", "user", "nginx", "latest", "amd64")
    assert filename == "user__nginx__latest__amd64.tar"


def test_check_image_exists_true() -> None:
    """Test checking image exists returns true."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "inspect", "--type=image", "test:image"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

        result = check_image_exists("test:image")

        assert result is True
        mock_run.assert_called_once()


def test_check_image_exists_false() -> None:
    """Test checking image exists returns false."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "inspect", "--type=image", "nonexistent:image"],
        )

        result = check_image_exists("nonexistent:image")

        assert result is False
        mock_run.assert_called_once()


def test_run_docker_command_success() -> None:
    """Test running docker command successfully."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "command"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

        success, error = run_docker_command(["docker", "command"])

        assert success is True
        assert error == ""
        mock_run.assert_called_once()


def test_run_docker_command_failure() -> None:
    """Test running docker command with failure."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "command"],
            stderr="Command failed",
        )

        success, error = run_docker_command(["docker", "command"])

        assert success is False
        assert error == "Command failed"
        mock_run.assert_called_once()


def test_docker_tar_save_stdout() -> None:
    """Test docker-tar save command with stdout option."""
    with mock.patch("cli_onprem.commands.docker_tar.check_image_exists") as mock_check:
        mock_check.return_value = True  # 이미지가 이미 로컬에 있다고 가정

        with mock.patch(
            "cli_onprem.commands.docker_tar.run_docker_command"
        ) as mock_run:
            mock_run.return_value = (True, "")  # 성공적으로 저장

            result = runner.invoke(
                app, ["docker-tar", "save", "test:image", "--stdout"]
            )

            assert result.exit_code == 0
            assert mock_run.call_args[0][0][0:2] == ["docker", "save"]
            assert mock_run.call_args[1]["stdout"] == subprocess.STDOUT


def test_docker_tar_save_with_output() -> None:
    """Test docker-tar save command with output option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_file = tmp_path / "output.tar"

        with mock.patch(
            "cli_onprem.commands.docker_tar.check_image_exists"
        ) as mock_check:
            mock_check.return_value = True  # 이미지가 이미 로컬에 있다고 가정

            with mock.patch(
                "cli_onprem.commands.docker_tar.run_docker_command"
            ) as mock_run:
                mock_run.return_value = (True, "")  # 성공적으로 저장

                result = runner.invoke(
                    app,
                    ["docker-tar", "save", "test:image", "--output", str(output_file)],
                )

                assert result.exit_code == 0
                cmd = mock_run.call_args[0][0]
                assert cmd[0:3] == ["docker", "save", "-o"]
                assert str(output_file) in cmd
