"""Tests for docker_args module."""

import os
from unittest import mock

from cli_onprem.services.docker_args import extract_images_from_args

PROMETHEUS_CONFIG_RELOADER = (
    "quay.io/prometheus-operator/prometheus-config-reloader:v0.81.0"
)


def test_extract_images_from_args_basic():
    """Test extracting images from command line arguments."""
    yaml_content = f"""
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - --prometheus-config-reloader={PROMETHEUS_CONFIG_RELOADER}
            - --config-reloader-cpu-request=0
    """

    images = extract_images_from_args(yaml_content)
    assert len(images) == 1
    assert PROMETHEUS_CONFIG_RELOADER in images


def test_extract_images_from_args_multiple():
    """Test extracting multiple images from command line arguments."""
    thanos_image = "quay.io/thanos/thanos:v0.30.2"
    alertmanager_image = "docker.io/prom/alertmanager:v0.25.0"

    yaml_content = f"""
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - --prometheus-config-reloader={PROMETHEUS_CONFIG_RELOADER}
            - --thanos-image={thanos_image}
            - --alertmanager-image={alertmanager_image}
    """

    images = extract_images_from_args(yaml_content)
    assert len(images) == 3
    assert PROMETHEUS_CONFIG_RELOADER in images
    assert thanos_image in images
    assert alertmanager_image in images


def test_extract_images_from_args_with_custom_patterns():
    """Test extracting images with custom registry patterns."""
    yaml_content = """
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - --image=custom.registry.io/app:v1.0.0
            - --sidecar=docker.io/nginx:latest
    """

    images = extract_images_from_args(
        yaml_content, registry_patterns=["custom.registry.io", "docker.io"]
    )
    assert len(images) == 2
    assert "custom.registry.io/app:v1.0.0" in images
    assert "docker.io/nginx:latest" in images


def test_extract_images_from_args_with_environment_variable():
    """Test extracting images with registry patterns from environment variable."""
    yaml_content = """
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - --image=custom.registry.io/app:v1.0.0
            - --sidecar=docker.io/nginx:latest
    """

    with mock.patch.dict(
        os.environ, {"CLI_ONPREM_REGISTRY_PATTERNS": "custom.registry.io,example.io"}
    ):
        images = extract_images_from_args(yaml_content, registry_patterns=[])
        assert len(images) == 1
        assert "custom.registry.io/app:v1.0.0" in images


def test_extract_images_from_args_with_quotes():
    """Test extracting images with different quote styles."""
    yaml_content = """
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - "--image=quay.io/app:v1.0.0"
            - '--sidecar=docker.io/nginx:latest'
    """

    images = extract_images_from_args(yaml_content)
    assert len(images) == 2
    assert "quay.io/app:v1.0.0" in images
    assert "docker.io/nginx:latest" in images


def test_extract_images_from_args_with_different_formats():
    """Test extracting images with different argument formats."""
    prometheus_image = "docker.io/prom/prometheus:v2.45.0"
    kube_metrics_image = "registry.k8s.io/kube-state-metrics:v2.8.0"

    yaml_content = f"""
    apiVersion: apps/v1
    kind: Deployment
    spec:
      template:
        spec:
          containers:
          - args:
            - --prometheus-config-reloader={PROMETHEUS_CONFIG_RELOADER}
            - -image={prometheus_image}
            - image: {kube_metrics_image}
    """

    images = extract_images_from_args(yaml_content)
    assert len(images) == 3
    assert PROMETHEUS_CONFIG_RELOADER in images
    assert prometheus_image in images
    assert kube_metrics_image in images
