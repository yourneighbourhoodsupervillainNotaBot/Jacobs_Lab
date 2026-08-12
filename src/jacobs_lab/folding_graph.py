"""Compatibility alias: folding_graph -> jacobs_lab.structure.folding_graph."""

from .structure import folding_graph as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
