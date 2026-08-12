"""Compatibility alias: triangle_state_machine -> jacobs_lab.structure.triangle_state_machine."""

from .structure import triangle_state_machine as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
