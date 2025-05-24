"""Additional tests for docker-tar command to improve coverage."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.services.docker import (
    check_image_exists,
    parse_image_reference,
)
from cli_onprem.services.docker import (
    generate_tar_filename as generate_filename,
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
        "quay.io/namespace/image:tag"
    )
    assert registry == "quay.io"
    assert namespace == "namespace"
    assert image == "image"
    assert tag == "tag"


def test_parse_image_reference_complex() -> None:
    """Test parsing complex image reference."""
    registry, namespace, image, tag = parse_image_reference(
        "myregistry.com/my/deep/path/image:v1.0"
    )
    assert registry == "myregistry.com"
    assert namespace == "my"
    assert image == "deep/path/image"
    assert tag == "v1.0"


def test_generate_filename_simple() -> None:
    """Test filename generation for simple image."""
    filename = generate_filename("docker.io", "library", "nginx", "latest", "amd64")
    assert filename == "nginx__latest__amd64.tar"


def test_generate_filename_with_namespace() -> None:
    """Test filename generation with namespace."""
    filename = generate_filename("docker.io", "user", "image", "v1", "amd64")
    assert filename == "user__image__v1__amd64.tar"


def test_generate_filename_with_registry() -> None:
    """Test filename generation with registry."""
    filename = generate_filename("quay.io", "namespace", "image", "tag", "arm64")
    assert filename == "quay.io__namespace__image__tag__arm64.tar"


def test_generate_filename_special_chars() -> None:
    """Test filename generation with special characters."""
    filename = generate_filename(
        "reg.io", "ns/sub", "img/path", "tag/slash", "linux/amd64"
    )
    assert filename == "reg.io__ns_sub__img_path__tag_slash__linux_amd64.tar"


def test_check_image_exists_true() -> None:
    """Test checking if image exists - image exists."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "inspect", "--type=image", "test:image"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

        exists = check_image_exists("test:image")

        assert exists is True
        mock_run.assert_called_once()


def test_check_image_exists_false() -> None:
    """Test checking if image exists - image does not exist."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "inspect", "--type=image", "test:image"],
            stderr=b"",
        )

        exists = check_image_exists("test:image")

        assert exists is False


# run_docker_command tests removed - functionality moved to service layer


def test_docker_tar_save_stdout() -> None:
    """Test docker-tar save command with stdout option."""
    with mock.patch("subprocess.run") as mock_subprocess:
        mock_subprocess.return_value = mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch(
            "cli_onprem.utils.shell.check_command_exists"
        ) as mock_check_cmd:
            mock_check_cmd.return_value = True  # Docker가 설치되어 있다고 가정

            result = runner.invoke(
                app, ["docker-tar", "save", "test:image", "--stdout"]
            )

            assert result.exit_code == 0
            # stdout의 경우 stderr로만 출력되고 stdout은 아무것도 포함 안함
            assert any(
                "save" in str(call) and "test:image" in str(call)
                for call in mock_subprocess.call_args_list
            )


def test_docker_tar_save_with_destination() -> None:
    """Test docker-tar save command with destination option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_file = tmp_path / "output.tar"

        with mock.patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch(
                "cli_onprem.utils.shell.check_command_exists"
            ) as mock_check_cmd:
                mock_check_cmd.return_value = True  # Docker가 설치되어 있다고 가정

                result = runner.invoke(
                    app,
                    [
                        "docker-tar",
                        "save",
                        "test:image",
                        "--destination",
                        str(output_file),
                    ],
                )

                assert result.exit_code == 0
                # save 명령어가 호출되었는지 확인
                assert any(
                    "save" in str(call) and str(output_file) in str(call)
                    for call in mock_subprocess.call_args_list
                )


def test_docker_tar_save_create_directory(tmp_path: Path) -> None:
    """Destination directory should be created when absent."""
    dest_dir = tmp_path / "2025"

    with mock.patch("subprocess.run") as mock_subprocess:
        mock_subprocess.return_value = mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch(
            "cli_onprem.utils.shell.check_command_exists"
        ) as mock_check_cmd:
            mock_check_cmd.return_value = True

            result = runner.invoke(
                app,
                ["docker-tar", "save", "test:image", "--destination", str(dest_dir)],
            )

            assert result.exit_code == 0
            assert dest_dir.is_dir()
            expected_path = dest_dir / "test__image__amd64.tar"
            # save 명령어에 올바른 경로가 포함되었는지 확인
            assert any(
                "save" in str(call) and expected_path.name in str(call)
                for call in mock_subprocess.call_args_list
            )


def test_docker_cli_not_installed() -> None:
    """Test error when Docker CLI is not installed."""
    # Mock both the utils function and the direct shutil.which call
    with mock.patch("cli_onprem.utils.shell.check_command_exists", return_value=False):
        with mock.patch("shutil.which", return_value=None):
            result = runner.invoke(app, ["docker-tar", "save", "test:image"])

            assert result.exit_code == 1
            assert "Docker CLI가 설치되어 있지 않습니다" in result.output
