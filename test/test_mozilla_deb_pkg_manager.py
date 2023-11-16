import sys
import types

import mozilla_linux_pkg_manager  # noqa


def test_mozilla_linux_pkg_manager():
    assert "mozilla_linux_pkg_manager" in sys.modules


def test_cli():
    assert isinstance(mozilla_linux_pkg_manager.cli, types.ModuleType)
