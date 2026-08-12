"""Compatibility alias: Level_tree -> jacobs_lab.structure.Level_tree."""

from .structure import Level_tree as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
