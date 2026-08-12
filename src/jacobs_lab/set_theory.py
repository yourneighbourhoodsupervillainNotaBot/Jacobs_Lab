"""Compatibility alias: set_theory -> jacobs_lab.math_lenses.set_theory."""

from .math_lenses import set_theory as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
