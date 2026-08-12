"""Compatibility alias: fold_codec -> jacobs_lab.instruments.fold_codec."""

from .instruments import fold_codec as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
