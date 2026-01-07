import sys
import types
from argparse import Namespace
from unittest.mock import AsyncMock, patch

import pytest
from google.cloud import artifactregistry_v1

import mozilla_linux_pkg_manager  # noqa
from mozilla_linux_pkg_manager.cli import get_repository, list_packages, list_versions


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
