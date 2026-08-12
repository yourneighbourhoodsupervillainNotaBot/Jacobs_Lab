"""Compatibility alias: pathfinding_lab -> jacobs_lab.instruments.pathfinding_lab."""

from .instruments import pathfinding_lab as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
