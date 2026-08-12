"""Compatibility alias: turing_universality -> jacobs_lab.computation.turing_universality."""

from .computation import turing_universality as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
