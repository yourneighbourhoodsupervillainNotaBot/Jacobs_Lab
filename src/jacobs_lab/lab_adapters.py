"""Compatibility alias: lab_adapters -> jacobs_lab.trace.lab_adapters."""

from .trace import lab_adapters as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
