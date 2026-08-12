"""Compatibility alias: named_aliases -> jacobs_lab.core.named_aliases."""

from .core import named_aliases as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
