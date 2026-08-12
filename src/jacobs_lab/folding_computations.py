"""Compatibility alias: folding_computations -> jacobs_lab.computation.folding_computations."""

from .computation import folding_computations as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
