"""Compatibility alias: universality_probe -> jacobs_lab.computation.universality_probe."""

from .computation import universality_probe as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
