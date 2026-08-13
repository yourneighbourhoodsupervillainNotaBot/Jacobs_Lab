"""Spectral SDF ray-marching subsystem.

This subsystem renders signed distance functions by sphere tracing and
uses a stylized 9-band spectral model inspired by the Jacobs 9-root
structure.

It is intended to be wrapped by the existing Jacobs layers:

- folding / portal structure
- trace/event inspection
- sonification
- structural domain transforms
"""

__version__ = "0.1.0"