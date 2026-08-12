"""Deprecated alias: Level_tree -> level_tree."""

from . import level_tree as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
