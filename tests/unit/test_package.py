"""Smoke test: the package is importable."""

import iqscope


def test_package_imports() -> None:
    assert iqscope.__all__ == []
