"""Compatibility alias: flexagon -> jacobs_lab.structure.flexagon."""

from .structure import flexagon as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
