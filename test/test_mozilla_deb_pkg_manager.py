import sys
import types

import mozilla_deb_pkg_manager  # noqa


def test_mozilla_deb_pkg_manager():
    assert "mozilla_deb_pkg_manager" in sys.modules


def test_cli():
    assert isinstance(mozilla_deb_pkg_manager.cli, types.ModuleType)
