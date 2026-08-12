"""Compatibility alias: natural_transformations -> jacobs_lab.math_lenses.natural_transformations."""

from .math_lenses import natural_transformations as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
