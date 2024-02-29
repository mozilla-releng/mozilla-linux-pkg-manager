import os
import pytest
import sys
import types

import mozilla_linux_pkg_manager  # noqa

DATA_PATH = os.path.join("test", "data")


def test_mozilla_linux_pkg_manager():
    assert "mozilla_linux_pkg_manager" in sys.modules


def test_cli():
    assert isinstance(mozilla_linux_pkg_manager.cli, types.ModuleType)


async def get_repository(args):
    repository = mozilla_linux_pkg_manager.cli.load_protocol_buffers(
        os.path.join(DATA_PATH, "repository.bin"),
        mozilla_linux_pkg_manager.cli.artifactregistry_v1.Repository,
    )
    return repository


@pytest.mark.asyncio
async def test_clean_up():
    args = mozilla_linux_pkg_manager.cli.argparse.Namespace(
        **{
            "command": "clean-up",
            "package": "^firefox-(devedition|beta)(-l10n-.+)?$",
            "repository": "mozilla",
            "region": "us",
            "retention_days": 60,
            "dry_run": False,
            "skip_delete": True,
        }
    )
    assert await get_repository(args)
