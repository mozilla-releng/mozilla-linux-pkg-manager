import sys
import types
from argparse import Namespace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.cloud import artifactregistry_v1

import mozilla_linux_pkg_manager  # noqa
from mozilla_linux_pkg_manager.cli import (
    batch_delete_versions,
    clean_up,
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
@pytest.mark.parametrize("dry_run", [True, False])
async def test_batch_delete_versions(dry_run):
    mock_client = AsyncMock()
    mock_operation = AsyncMock()
    mock_client.batch_delete_versions.return_value = mock_operation

    package_name = "projects/test-project/locations/us-central1/repositories/my-repo/packages/firefox"
    tb_package_name = "projects/test-project/locations/us-central1/repositories/my-repo/packages/thunderbird"
    version_names = [f"{package_name}/versions/42.0.{i}" for i in range(120)]
    tb_version_names = [f"{tb_package_name}/versions/42.0.{i}" for i in range(10)]
    targets = {package_name: set(version_names), tb_package_name: set(tb_version_names)}
    args = Namespace(dry_run=dry_run)

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
        assert call_kwargs["request"].validate_only is dry_run
        assert len(call_kwargs["request"].names) == expected_batch_size
        all_deleted_versions.update(call_kwargs["request"].names)

    assert all_deleted_versions == set(version_names) | set(tb_version_names)
    assert mock_operation.result.call_count == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [True, False])
async def test_clean_up(dry_run):
    async def async_iter(items):
        for item in items:
            yield item

    repo_name = "projects/test-project/locations/us-central1/repositories/my-repo"
    package_name = f"{repo_name}/packages/firefox"
    package_name_no_match = f"{repo_name}/packages/thunderbird"

    mock_repository = artifactregistry_v1.Repository(name=repo_name)
    mock_package = artifactregistry_v1.Package(name=package_name)
    mock_package_no_match = artifactregistry_v1.Package(name=package_name_no_match)

    now = datetime.now(UTC)
    expired_version = MagicMock()
    expired_version.name = f"{package_name}/versions/43.0.0"
    expired_version.create_time = now - timedelta(days=100)

    fresh_version = MagicMock()
    fresh_version.name = f"{package_name}/versions/42.0.0"
    fresh_version.create_time = now - timedelta(days=5)

    args = Namespace(
        package="^firefox$",
        retention_days=30,
        dry_run=dry_run,
        skip_delete=False,
    )

    with (
        patch(
            "mozilla_linux_pkg_manager.cli.get_repository",
            return_value=mock_repository,
        ),
        patch(
            "mozilla_linux_pkg_manager.cli.list_packages",
            return_value=async_iter([mock_package, mock_package_no_match]),
        ),
        patch(
            "mozilla_linux_pkg_manager.cli.list_versions",
            return_value=async_iter([expired_version, fresh_version]),
        ) as mock_list_versions,
        patch(
            "mozilla_linux_pkg_manager.cli.batch_delete_versions",
        ) as mock_batch_delete,
    ):
        await clean_up(args)

    # list_versions should only be called for matching package (firefox, not thunderbird in this case)
    mock_list_versions.assert_called_once_with(mock_package)

    mock_batch_delete.assert_called_once()
    call_args = mock_batch_delete.call_args
    targets = call_args[0][0]

    assert package_name in targets
    assert package_name_no_match not in targets
    assert targets[package_name] == {expired_version.name}
    assert call_args[0][1] == args
