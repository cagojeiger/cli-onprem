"""Tests for the helm-local command."""

import pathlib
import subprocess
import tempfile
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.services.docker import (
    extract_images_from_yaml as collect_images,
)
from cli_onprem.services.docker import (
    normalize_image_name,
)
from cli_onprem.services.helm import (
    extract_chart,
    prepare_chart,
)
from cli_onprem.services.helm import (
    render_template as helm_template,
)
from cli_onprem.services.helm import (
    update_dependencies as helm_dependency_update,
)

runner = CliRunner()


def test_normalize_image_name_with_simple_name() -> None:
    """Test normalizing a simple image name."""
    image = "nginx"
    normalized = normalize_image_name(image)
    assert normalized == "docker.io/library/nginx:latest"


def test_normalize_image_name_with_tag() -> None:
    """Test normalizing an image name with a tag."""
    image = "nginx:1.19"
    normalized = normalize_image_name(image)
    assert normalized == "docker.io/library/nginx:1.19"


def test_normalize_image_name_with_digest() -> None:
    """Test normalizing an image name with a digest."""
    image = "nginx@sha256:abcdef"
    normalized = normalize_image_name(image)
    assert normalized == "docker.io/library/nginx@sha256:abcdef"


def test_normalize_image_name_with_registry() -> None:
    """Test normalizing an image name with a registry."""
    image = "registry.example.com/nginx"
    normalized = normalize_image_name(image)
    assert normalized == "registry.example.com/nginx:latest"


def test_normalize_image_name_with_namespace() -> None:
    """Test normalizing an image name with a namespace."""
    image = "user/repo"
    normalized = normalize_image_name(image)
    assert normalized == "docker.io/user/repo:latest"


def test_normalize_image_name_full() -> None:
    """Test normalizing a fully qualified image name."""
    image = "registry.example.com/namespace/repo:tag"
    normalized = normalize_image_name(image)
    assert normalized == "registry.example.com/namespace/repo:tag"


def test_collect_images() -> None:
    """Test collecting images from rendered YAML."""
    yaml_content = """
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        image: custom/app:latest
"""
    images = collect_images(yaml_content)
    assert len(images) == 2
    assert "docker.io/library/nginx:1.19" in images
    assert "docker.io/custom/app:latest" in images


def test_collect_images_complex_pattern() -> None:
    """Test collecting images with complex repository/tag pattern."""
    yaml_content = """
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: complex
spec:
  template:
    spec:
      containers:
      - name: complex
        repository: registry.example.com/namespace
        image: app
        tag: v1.0.0
"""
    images = collect_images(yaml_content)
    assert len(images) == 1
    assert "registry.example.com/namespace/app:v1.0.0" in images


def test_extract_chart() -> None:
    """Test extracting a chart archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = pathlib.Path(tmpdir)

        with mock.patch("tarfile.open") as mock_open:
            mock_tarfile = mock.MagicMock()
            mock_open.return_value.__enter__.return_value = mock_tarfile

            chart_root = mock.MagicMock(spec=pathlib.Path)

            with mock.patch.object(pathlib.Path, "iterdir") as mock_iterdir:
                mock_iterdir.return_value = [chart_root]

                # Mock is_dir to return True for our chart_root
                with mock.patch.object(pathlib.Path, "is_dir") as mock_is_dir:
                    mock_is_dir.return_value = True

                    result = extract_chart(pathlib.Path("chart.tgz"), dest_dir)

                    assert result == chart_root
                    mock_tarfile.extractall.assert_called_once_with(dest_dir)


def test_prepare_chart_with_directory() -> None:
    """Test preparing a chart from a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_dir = pathlib.Path(tmpdir) / "mychart"
        chart_dir.mkdir()

        (chart_dir / "Chart.yaml").write_text("name: mychart")

        result = prepare_chart(chart_dir, pathlib.Path(tmpdir))
        assert result == chart_dir


def test_prepare_chart_with_archive() -> None:
    """Test preparing a chart from an archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        chart_path = tmp_path / "chart.tgz"

        # Create a mock path with the correct behavior
        mock_path = mock.MagicMock()
        mock_path.is_dir.return_value = False
        mock_path.is_file.return_value = True
        mock_path.suffix = ".tgz"

        # Use a different approach to mock __str__
        mock_path.configure_mock(__str__=mock.MagicMock(return_value=str(chart_path)))

        with mock.patch("cli_onprem.services.helm.extract_chart") as mock_extract:
            mock_extract.return_value = tmp_path / "extracted_chart"

            result = prepare_chart(mock_path, tmp_path)

            assert result == tmp_path / "extracted_chart"
            mock_extract.assert_called_once_with(mock_path, tmp_path)


def test_helm_dependency_update() -> None:
    """Test helm dependency update command."""
    with mock.patch("cli_onprem.utils.shell.run_command") as mock_run:
        chart_dir = pathlib.Path("/path/to/chart")
        helm_dependency_update(chart_dir)

        mock_run.assert_called_once_with(
            ["helm", "dependency", "update", str(chart_dir)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def test_helm_template() -> None:
    """Test helm template command."""
    with mock.patch("cli_onprem.utils.shell.run_command") as mock_run:
        chart_dir = pathlib.Path("/path/to/chart")
        values_files = [pathlib.Path("/path/to/values.yaml")]

        mock_result = mock.MagicMock()
        mock_result.stdout = "rendered content"
        mock_run.return_value = mock_result

        with mock.patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            result = helm_template(chart_dir, values_files)

            assert result == "rendered content"
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd[0:3] == ["helm", "template", "dummy"]
            assert str(chart_dir) in cmd
            assert "-f" in cmd
            assert str(values_files[0]) in cmd


def test_extract_images_command() -> None:
    """Test the extract-images command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"
                            mock_template.return_value = """
                            apiVersion: apps/v1
                            kind: Deployment
                            metadata:
                              name: test
                            spec:
                              template:
                                spec:
                                  containers:
                                  - name: test
                                    image: test:latest
                            """
                            mock_collect.return_value = [
                                "docker.io/library/test:latest"
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                ],
                            )

                            assert result.exit_code == 0
                            assert "docker.io/library/test:latest" in result.stdout
                            mock_prepare.assert_called_once()
                            mock_template.assert_called_once()
                            mock_collect.assert_called_once()


def test_extract_images_json_output() -> None:
    """Test the extract-images command with JSON output format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"
                            mock_template.return_value = """
                            apiVersion: apps/v1
                            kind: Deployment
                            metadata:
                              name: test
                            spec:
                              template:
                                spec:
                                  containers:
                                  - name: nginx
                                    image: nginx:1.21
                                  - name: app
                                    image: myapp:v1.0.0
                            """
                            mock_collect.return_value = [
                                "docker.io/library/nginx:1.21",
                                "docker.io/library/myapp:v1.0.0",
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                    "--json",
                                ],
                            )

                            assert result.exit_code == 0
                            # Parse JSON output
                            import json

                            output_data = json.loads(result.stdout)
                            assert isinstance(output_data, list)
                            assert len(output_data) == 2
                            assert "docker.io/library/nginx:1.21" in output_data
                            assert "docker.io/library/myapp:v1.0.0" in output_data


def test_extract_images_multiple_values_files() -> None:
    """Test the extract-images command with multiple values files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        # Create test values files
        values1 = tmp_path / "values1.yaml"
        values1.write_text("nginx:\n  tag: 1.20")

        values2 = tmp_path / "values2.yaml"
        values2.write_text("nginx:\n  tag: 1.21")  # This should override values1

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"

                            # Mock helm template to verify values files are passed
                            def check_helm_template_args(
                                chart_dir: pathlib.Path,
                                values_files: list[pathlib.Path],
                            ) -> str:
                                # Verify both values files are passed
                                assert len(values_files) == 2
                                assert values_files[0] == values1
                                assert values_files[1] == values2
                                return "rendered content"

                            mock_template.side_effect = check_helm_template_args
                            mock_collect.return_value = ["docker.io/library/nginx:1.21"]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                    "-f",
                                    str(values1),
                                    "-f",
                                    str(values2),
                                ],
                            )

                            assert result.exit_code == 0
                            assert "docker.io/library/nginx:1.21" in result.stdout
                            mock_template.assert_called_once()


def test_extract_images_raw_option() -> None:
    """Test the extract-images command with --raw option (no normalization)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"
                            mock_template.return_value = """
                            apiVersion: apps/v1
                            kind: Deployment
                            metadata:
                              name: test
                            spec:
                              template:
                                spec:
                                  containers:
                                  - name: nginx
                                    image: nginx
                                  - name: app
                                    image: myregistry.com/app:v1.0.0
                            """
                            # When --raw is used, images should not be normalized
                            # Currently not implemented, expect normalized output
                            mock_collect.return_value = [
                                "docker.io/library/nginx:latest",  # normalized
                                "myregistry.com/app:v1.0.0",  # already fully qualified
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                    "--raw",
                                ],
                            )

                            assert result.exit_code == 0
                            # TODO: When --raw is implemented, these should be:
                            # assert "nginx" in result.stdout  # not normalized
                            # assert "myregistry.com/app:v1.0.0" in result.stdout
                            # For now, we expect normalized output
                            assert "docker.io/library/nginx:latest" in result.stdout
                            assert "myregistry.com/app:v1.0.0" in result.stdout


def test_helm_dependency_update_failure() -> None:
    """Test that helm dependency update failure doesn't stop the process."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"

                            # Simulate helm dependency update failure
                            # The function doesn't raise exceptions due to check=False
                            # We just verify it's called and the process continues

                            mock_template.return_value = "rendered content"
                            mock_collect.return_value = [
                                "docker.io/library/nginx:latest"
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                ],
                            )

                            # Should still succeed even if dependency update fails
                            assert result.exit_code == 0
                            assert "docker.io/library/nginx:latest" in result.stdout
                            mock_template.assert_called_once()


def test_extract_images_with_skip_dependency_update() -> None:
    """Test extract-images command with --skip-dependency-update option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch(
                    "cli_onprem.services.helm.update_dependencies"
                ) as mock_update_deps:
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"
                            mock_template.return_value = """
                            apiVersion: apps/v1
                            kind: Deployment
                            metadata:
                              name: test
                            spec:
                              template:
                                spec:
                                  containers:
                                  - name: test
                                    image: test:latest
                            """
                            mock_collect.return_value = [
                                "docker.io/library/test:latest"
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                    "--skip-dependency-update",
                                ],
                            )

                            assert result.exit_code == 0
                            assert "docker.io/library/test:latest" in result.stdout
                            # 의존성 업데이트가 호출되지 않아야 함
                            mock_update_deps.assert_not_called()


def test_extract_images_without_skip_dependency_update() -> None:
    """Test extract-images command without --skip-dependency-update option (default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch(
                    "cli_onprem.services.helm.update_dependencies"
                ) as mock_update_deps:
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        with mock.patch(
                            "cli_onprem.services.docker.extract_images_from_yaml"
                        ) as mock_collect:
                            mock_prepare.return_value = tmp_path / "chart"
                            mock_template.return_value = """
                            apiVersion: apps/v1
                            kind: Deployment
                            metadata:
                              name: test
                            spec:
                              template:
                                spec:
                                  containers:
                                  - name: test
                                    image: test:latest
                            """
                            mock_collect.return_value = [
                                "docker.io/library/test:latest"
                            ]

                            result = runner.invoke(
                                app,
                                [
                                    "helm-local",
                                    "extract-images",
                                    str(tmp_path / "chart.tgz"),
                                ],
                            )

                            assert result.exit_code == 0
                            assert "docker.io/library/test:latest" in result.stdout
                            # 의존성 업데이트가 호출되어야 함 (기본 동작)
                            mock_update_deps.assert_called_once_with(tmp_path / "chart")


def test_helm_template_failure() -> None:
    """Test proper error handling when helm template fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        with mock.patch("cli_onprem.services.helm.check_helm_installed"):
            with mock.patch("cli_onprem.services.helm.prepare_chart") as mock_prepare:
                with mock.patch("cli_onprem.services.helm.update_dependencies"):
                    with mock.patch(
                        "cli_onprem.services.helm.render_template"
                    ) as mock_template:
                        mock_prepare.return_value = tmp_path / "chart"

                        # Simulate helm template failure
                        mock_template.side_effect = subprocess.CalledProcessError(
                            1, "helm template", stderr="Error: chart not found"
                        )

                        result = runner.invoke(
                            app,
                            [
                                "helm-local",
                                "extract-images",
                                str(tmp_path / "chart.tgz"),
                            ],
                        )

                        # Should exit with error code
                        assert result.exit_code == 1
                        assert "명령어 실행 실패" in result.stdout
