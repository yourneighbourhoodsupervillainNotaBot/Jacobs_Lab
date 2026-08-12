"""Compatibility alias: quintic_analysis -> jacobs_lab.math_lenses.quintic_analysis."""

from .math_lenses import quintic_analysis as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
