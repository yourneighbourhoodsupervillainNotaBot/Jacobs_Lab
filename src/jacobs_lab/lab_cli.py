"""Compatibility alias: lab_cli -> jacobs_lab.cli.lab_cli."""

from .cli import lab_cli as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
