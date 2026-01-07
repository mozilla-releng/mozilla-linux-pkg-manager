import sys
import types
from argparse import Namespace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
import requests.exceptions as requests_exceptions
from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import artifactregistry_v1

import mozilla_linux_pkg_manager  # noqa
from mozilla_linux_pkg_manager.cli import (
    batch_delete_versions,
    clean_up,
    get_repository,
    list_packages,
    list_versions,
    should_retry,
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

    with (
        patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}),
        patch(
            "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
            return_value=mock_client,
        ),
    ):
        result = await get_repository("us-central1", "my-repo")

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
async def test_batch_delete_versions_multiple_repositories():
    mock_client = AsyncMock()
    mock_operation = AsyncMock()
    mock_client.batch_delete_versions.return_value = mock_operation

    repo1_package = "projects/test-project/locations/us-central1/repositories/repo1/packages/firefox"
    repo2_package = "projects/test-project/locations/us-central1/repositories/repo2/packages/firefox-rpm"
    repo1_versions = [f"{repo1_package}/versions/42.0.{i}" for i in range(3)]
    repo2_versions = [f"{repo2_package}/versions/43.0.{i}" for i in range(2)]
    targets = {repo1_package: set(repo1_versions), repo2_package: set(repo2_versions)}
    args = Namespace(dry_run=False)

    with patch(
        "mozilla_linux_pkg_manager.cli.artifactregistry_v1.ArtifactRegistryAsyncClient",
        return_value=mock_client,
    ):
        await batch_delete_versions(targets, args)

    assert mock_client.batch_delete_versions.call_count == 2

    for call in mock_client.batch_delete_versions.call_args_list:
        call_kwargs = call.kwargs
        parent = call_kwargs["request"].parent
        versions = set(call_kwargs["request"].names)

        # Verify that each parent only receives its own versions
        if parent == repo1_package:
            assert versions == set(repo1_versions)
        elif parent == repo2_package:
            assert versions == set(repo2_versions)
        else:
            pytest.fail(f"Unexpected parent: {parent}")

    assert mock_operation.result.call_count == 2


async def async_iter(items):
    for item in items:
        yield item


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [True, False])
async def test_clean_up(dry_run):
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
        repository=["my-repo"],
        region="us-central1",
        retention_days=30,
        dry_run=dry_run,
        skip_delete=False,
    )

    with (
        patch(
            "mozilla_linux_pkg_manager.cli.get_repository",
            return_value=mock_repository,
        ) as mock_get_repo,
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

    mock_get_repo.assert_called_once_with("us-central1", "my-repo")

    # list_versions should only be called for matching package (firefox, not thunderbird in this case)
    mock_list_versions.assert_called_once_with(mock_package)

    mock_batch_delete.assert_called_once()
    call_args = mock_batch_delete.call_args
    targets = call_args[0][0]

    assert package_name in targets
    assert package_name_no_match not in targets
    assert targets[package_name] == {expired_version.name}
    assert call_args[0][1] == args


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [True, False])
async def test_clean_up_multiple_repositories(dry_run):
    repo1_name = "projects/test-project/locations/us-central1/repositories/repo1"
    repo2_name = "projects/test-project/locations/us-central1/repositories/repo2"
    package1_name = f"{repo1_name}/packages/firefox"
    package2_name = f"{repo2_name}/packages/firefox-rpm"

    mock_repository1 = artifactregistry_v1.Repository(name=repo1_name)
    mock_repository2 = artifactregistry_v1.Repository(name=repo2_name)
    mock_package1 = artifactregistry_v1.Package(name=package1_name)
    mock_package2 = artifactregistry_v1.Package(name=package2_name)

    now = datetime.now(UTC)
    expired_version1 = MagicMock()
    expired_version1.name = f"{package1_name}/versions/43.0.0"
    expired_version1.create_time = now - timedelta(days=100)

    expired_version2 = MagicMock()
    expired_version2.name = f"{package2_name}/versions/43.0.0"
    expired_version2.create_time = now - timedelta(days=100)

    args = Namespace(
        package="^firefox.*$",
        repository=["repo1", "repo2"],
        region="us-central1",
        retention_days=30,
        dry_run=dry_run,
        skip_delete=False,
    )

    async def mock_get_repo_side_effect(region, repo_name):
        if repo_name == "repo1":
            return mock_repository1
        return mock_repository2

    def mock_list_packages_side_effect(repo):
        if repo.name == repo1_name:
            return async_iter([mock_package1])
        return async_iter([mock_package2])

    def mock_list_versions_side_effect(package):
        if package.name == package1_name:
            return async_iter([expired_version1])
        return async_iter([expired_version2])

    with (
        patch(
            "mozilla_linux_pkg_manager.cli.get_repository",
            side_effect=mock_get_repo_side_effect,
        ) as mock_get_repo,
        patch(
            "mozilla_linux_pkg_manager.cli.list_packages",
            side_effect=mock_list_packages_side_effect,
        ),
        patch(
            "mozilla_linux_pkg_manager.cli.list_versions",
            side_effect=mock_list_versions_side_effect,
        ),
        patch(
            "mozilla_linux_pkg_manager.cli.batch_delete_versions",
        ) as mock_batch_delete,
    ):
        await clean_up(args)

    assert mock_get_repo.call_count == 2
    mock_get_repo.assert_any_call("us-central1", "repo1")
    mock_get_repo.assert_any_call("us-central1", "repo2")

    mock_batch_delete.assert_called_once()
    call_args = mock_batch_delete.call_args
    targets = call_args[0][0]

    assert package1_name in targets
    assert package2_name in targets
    assert targets[package1_name] == {expired_version1.name}
    assert targets[package2_name] == {expired_version2.name}


@pytest.mark.parametrize(
    "exc,expected",
    [
        (api_exceptions.TooManyRequests(""), True),
        (api_exceptions.InternalServerError(""), True),
        (api_exceptions.BadGateway(""), True),
        (api_exceptions.ServiceUnavailable(""), True),
        (api_exceptions.GatewayTimeout(""), True),
        (ConnectionError(""), True),
        (requests.ConnectionError(""), True),
        (requests_exceptions.ChunkedEncodingError(""), True),
        (requests_exceptions.Timeout(""), True),
        (MagicMock(spec=api_exceptions.GoogleAPICallError, code=408), True),
        (MagicMock(spec=api_exceptions.GoogleAPICallError, code=404), False),
        (auth_exceptions.TransportError(ConnectionError("")), True),
        (auth_exceptions.TransportError(ValueError("")), False),
        (ValueError(""), False),
    ],
)
def test_should_retry(exc, expected):
    assert should_retry(exc) is expected
