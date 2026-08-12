"""Compatibility alias: Level_tree -> jacobs_lab.structure.level_tree."""

from .structure import level_tree as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
