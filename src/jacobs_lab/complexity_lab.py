"""Compatibility alias: complexity_lab -> jacobs_lab.computation.complexity_lab."""

from .computation import complexity_lab as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
