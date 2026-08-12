"""Compatibility alias: three_body_lab -> jacobs_lab.instruments.three_body_lab."""

from .instruments import three_body_lab as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
