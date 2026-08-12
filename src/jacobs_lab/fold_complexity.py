"""Compatibility alias: fold_complexity -> jacobs_lab.instruments.fold_complexity."""

from .instruments import fold_complexity as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
