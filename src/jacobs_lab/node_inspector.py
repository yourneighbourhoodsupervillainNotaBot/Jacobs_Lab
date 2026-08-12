"""Compatibility alias: node_inspector -> jacobs_lab.viz.node_inspector."""

from .viz import node_inspector as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
