"""Smoke tests: the package is importable and carries a version."""

import re
from importlib.metadata import version

import iqscope


def test_package_imports() -> None:
    assert iqscope.__all__ == []


def test_version_is_derived_from_git_tag() -> None:
    # hatch-vcs: "0.2.0" on a tag, "0.2.1.devN+g<sha>" in between. A failed lookup would
    # show up as the fallback "0.0" / "0.1.dev1" or as an exception.
    assert re.fullmatch(r"\d+\.\d+\.\d+(\.dev\d+.*)?", version("iqscope"))
