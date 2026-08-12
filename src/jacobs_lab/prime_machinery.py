"""Compatibility alias: prime_machinery -> jacobs_lab.instruments.prime_machinery."""

from .instruments import prime_machinery as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
