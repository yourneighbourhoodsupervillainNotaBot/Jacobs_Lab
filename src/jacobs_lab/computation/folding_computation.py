"""Compatibility alias: folding_computation -> folding_computations."""

from . import folding_computations as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
