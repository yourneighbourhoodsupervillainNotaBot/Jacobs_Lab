"""Compatibility alias: galois_fields -> jacobs_lab.math_lenses.galois_fields."""

from .math_lenses import galois_fields as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
