"""extract_images_from_text 함수 테스트."""

import os
from unittest.mock import patch

from cli_onprem.services.docker import (
    extract_images_from_text,
    extract_images_from_yaml,
)


class TestExtractImagesFromText:
    """extract_images_from_text 함수 테스트."""

    def test_extract_simple_image_with_tag(self):
        """태그가 있는 단순한 이미지 추출."""
        text = "image: docker.io/nginx:1.21"
        result = extract_images_from_text(text)
        assert result == {"docker.io/nginx:1.21"}

    def test_extract_image_with_digest(self):
        """다이제스트가 있는 이미지 추출."""
        text = (
            "quay.io/prometheus/prometheus@sha256:"
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )
        result = extract_images_from_text(text)
        assert result == {
            "quay.io/prometheus/prometheus@sha256:"
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        }

    def test_extract_from_command_args(self):
        """커맨드 라인 인자에서 이미지 추출."""
        text = """
        args:
          - --prometheus-config-reloader=quay.io/prometheus-operator/\
prometheus-config-reloader:v0.81.0
          - --config-reloader-image=gcr.io/kubebuilder/kube-rbac-proxy:v0.13.0
        """
        result = extract_images_from_text(text)
        expected = {
            "quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0",
            "gcr.io/kubebuilder/kube-rbac-proxy:v0.13.0",
        }
        assert result == expected

    def test_extract_multiple_images(self):
        """여러 이미지 추출."""
        text = """
        image: docker.io/grafana/grafana:11.6.0
        sidecar: quay.io/kiwigrid/k8s-sidecar:1.30.0
        init: registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.5.2
        """
        result = extract_images_from_text(text)
        expected = {
            "docker.io/grafana/grafana:11.6.0",
            "quay.io/kiwigrid/k8s-sidecar:1.30.0",
            "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.5.2",
        }
        assert result == expected

    def test_extract_with_namespace(self):
        """네임스페이스가 있는 이미지 추출."""
        text = "image=ghcr.io/actions/runner:2.308.0"
        result = extract_images_from_text(text)
        assert result == {"ghcr.io/actions/runner:2.308.0"}

    def test_extract_with_default_tag(self):
        """태그가 없는 이미지는 latest 추가."""
        text = "docker.io/nginx"
        result = extract_images_from_text(text)
        assert result == {"docker.io/nginx:latest"}

    def test_custom_registries(self):
        """커스텀 레지스트리 목록 사용."""
        text = "myregistry.io/myapp:v1.0.0"
        result = extract_images_from_text(text, registries=["myregistry.io"])
        assert result == {"myregistry.io/myapp:v1.0.0"}

    def test_environment_variable_registries(self):
        """환경변수로 추가 레지스트리 설정."""
        text = "custom.registry.com/app:latest"
        with patch.dict(os.environ, {"CLI_ONPREM_REGISTRIES": "custom.registry.com"}):
            result = extract_images_from_text(text)
            assert result == {"custom.registry.com/app:latest"}

    def test_no_match_for_non_registry(self):
        """레지스트리 목록에 없는 도메인은 매칭 안됨."""
        text = "unknown.com/image:tag"
        result = extract_images_from_text(text)
        assert result == set()

    def test_extract_from_quoted_strings(self):
        """따옴표로 둘러싸인 문자열에서 추출."""
        text = """
        "--image='docker.io/busybox:1.35'"
        '--sidecar="quay.io/prometheus/node-exporter:v1.9.0"'
        """
        result = extract_images_from_text(text)
        expected = {
            "docker.io/busybox:1.35",
            "quay.io/prometheus/node-exporter:v1.9.0",
        }
        assert result == expected

    def test_complex_yaml_content(self):
        """복잡한 YAML 내용에서 추출."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test
spec:
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.21
        args:
        - --prometheus-config-reloader=quay.io/prometheus-operator/\
prometheus-config-reloader:v0.81.0
      - name: sidecar
        image: docker.io/grafana/promtail:3.0.0
        env:
        - name: RELATED_IMAGE
          value: gcr.io/google-containers/pause:3.9
"""
        # extract_from_text=True로 모든 이미지 추출
        result = extract_images_from_yaml(
            yaml_content, normalize=False, extract_from_text=True
        )

        # 구조화된 필드와 텍스트 패턴 모두에서 찾은 이미지
        assert "nginx:1.21" in result
        assert "docker.io/grafana/promtail:3.0.0" in result
        assert (
            "quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0" in result
        )
        assert "gcr.io/google-containers/pause:3.9" in result

    def test_extract_from_yaml_without_text_extraction(self):
        """텍스트 추출 없이 YAML에서만 추출."""
        yaml_content = """
spec:
  containers:
  - image: nginx:1.21
    args:
    - --config-reloader=quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0
"""
        # extract_from_text=False로 구조화된 필드만 추출
        result = extract_images_from_yaml(
            yaml_content, normalize=False, extract_from_text=False
        )

        assert "nginx:1.21" in result
        # args의 이미지는 추출되지 않음
        assert (
            "quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0"
            not in result
        )

    def test_ignore_invalid_formats(self):
        """잘못된 형식은 무시."""
        text = """
        not-a-registry/image:tag
        http://docker.io/image:tag
        docker.io/image:tag:extra
        docker.io//double-slash:tag
        """
        result = extract_images_from_text(text)
        # 유효한 레지스트리가 아니거나 형식이 잘못된 것들은 무시됨
        assert result == set()

    def test_case_insensitive_matching(self):
        """대소문자 구분 없이 매칭."""
        text = "Docker.IO/Nginx:Latest"
        result = extract_images_from_text(text)
        assert result == {"Docker.IO/Nginx:Latest"}

    def test_multiple_registries_in_env(self):
        """환경변수에 여러 레지스트리 설정."""
        text = """
        custom1.io/app1:v1
        custom2.io/app2:v2
        docker.io/nginx:latest
        """
        with patch.dict(os.environ, {"CLI_ONPREM_REGISTRIES": "custom1.io,custom2.io"}):
            result = extract_images_from_text(text)
            expected = {
                "custom1.io/app1:v1",
                "custom2.io/app2:v2",
                "docker.io/nginx:latest",
            }
            assert result == expected

    def test_extract_from_complex_command_line(self):
        """복잡한 커맨드 라인에서 추출."""
        text = """
        command: ["/bin/sh"]
        args: [
            "-c",
            "prometheus --storage.tsdb.path=/prometheus "
            "--config.file=/etc/prometheus/prometheus.yml "
            "--web.enable-lifecycle "
            "--config.reloader.url=http://localhost:8080 "
            "--config.reloader.image=quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0"
        ]
        """
        result = extract_images_from_text(text)
        assert result == {
            "quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0"
        }
