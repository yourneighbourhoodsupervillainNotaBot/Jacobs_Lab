"""Compatibility alias: category_theory -> jacobs_lab.math_lenses.category_theory."""

from .math_lenses import category_theory as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
