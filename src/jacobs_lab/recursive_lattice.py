"""Compatibility alias: recursive_lattice -> jacobs_lab.core.recursive_lattice."""

from .core import recursive_lattice as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
