import sys
import types
from argparse import Namespace
from unittest.mock import AsyncMock, patch

import pytest
from google.cloud import artifactregistry_v1

import mozilla_linux_pkg_manager  # noqa
from mozilla_linux_pkg_manager.cli import (
    batch_delete_versions,
    get_repository,
    list_packages,
    list_versions,
)


def test_mozilla_linux_pkg_manager():
    assert "mozilla_linux_pkg_manager" in sys.modules


def test_cli():
    assert isinstance(mozilla_linux_pkg_manager.cli, types.ModuleType)


@pytest.mark.asyncio
async def test_get_repository():
    mock_client = AsyncMock()
    mock_repository = AsyncMock()
    mock_client.get_repository.return_value = mock_repository

    args = Namespace(region="us-central1", repository="my-repo")

    with (
        patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}),
        patch(
            "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
            return_value=mock_client,
        ),
    ):
        result = await get_repository(args)

    mock_client.get_repository.assert_called_once()
    call_kwargs = mock_client.get_repository.call_args.kwargs
    assert (
        call_kwargs["request"].name
        == "projects/test-project/locations/us-central1/repositories/my-repo"
    )
    assert result == mock_repository


@pytest.mark.asyncio
async def test_list_packages():
    mock_client = AsyncMock()
    mock_packages = AsyncMock()
    mock_client.list_packages.return_value = mock_packages

    repository = artifactregistry_v1.Repository(
        name="projects/test-project/locations/us-central1/repositories/my-repo"
    )

    with patch(
        "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
        return_value=mock_client,
    ):
        result = await list_packages(repository)

    mock_client.list_packages.assert_called_once()
    call_kwargs = mock_client.list_packages.call_args.kwargs
    assert (
        call_kwargs["request"].parent
        == "projects/test-project/locations/us-central1/repositories/my-repo"
    )
    assert call_kwargs["request"].page_size == 1000
    assert result == mock_packages


@pytest.mark.asyncio
async def test_list_versions():
    mock_client = AsyncMock()
    mock_versions = AsyncMock()
    mock_client.list_versions.return_value = mock_versions

    package = artifactregistry_v1.Package(
        name="projects/test-project/locations/us-central1/repositories/my-repo/packages/firefox"
    )

    with patch(
        "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
        return_value=mock_client,
    ):
        result = await list_versions(package)

    mock_client.list_versions.assert_called_once()
    call_kwargs = mock_client.list_versions.call_args.kwargs
    assert (
        call_kwargs["request"].parent
        == "projects/test-project/locations/us-central1/repositories/my-repo/packages/firefox"
    )
    assert call_kwargs["request"].page_size == 1000
    assert result == mock_versions


@pytest.mark.asyncio
async def test_batch_delete_versions():
    mock_client = AsyncMock()
    mock_operation = AsyncMock()
    mock_client.batch_delete_versions.return_value = mock_operation

    package_name = "projects/test-project/locations/us-central1/repositories/my-repo/packages/firefox"
    tb_package_name = "projects/test-project/locations/us-central1/repositories/my-repo/packages/thunderbird"
    version_names = [f"{package_name}/versions/42.0.{i}" for i in range(120)]
    tb_version_names = [f"{tb_package_name}/versions/42.0.{i}" for i in range(10)]
    targets = {package_name: set(version_names), tb_package_name: set(tb_version_names)}
    args = Namespace(dry_run=True)

    with patch(
        "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
        return_value=mock_client,
    ):
        await batch_delete_versions(targets, args)

    assert mock_client.batch_delete_versions.call_count == 4

    all_deleted_versions = set()
    expected_batch_sizes = iter((50, 50, 20, 10))
    for call in mock_client.batch_delete_versions.call_args_list:
        expected_batch_size = next(expected_batch_sizes)
        call_kwargs = call.kwargs
        expected_parent = package_name if expected_batch_size != 10 else tb_package_name
        assert call_kwargs["request"].parent == expected_parent
        assert call_kwargs["request"].validate_only is True
        assert len(call_kwargs["request"].names) == expected_batch_size
        all_deleted_versions.update(call_kwargs["request"].names)

    assert all_deleted_versions == set(version_names) | set(tb_version_names)
    assert mock_operation.result.call_count == 4
