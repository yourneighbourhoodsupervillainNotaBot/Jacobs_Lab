from __future__ import annotations

import numpy as np


def length(v: np.ndarray) -> np.ndarray:
    return np.linalg.norm(v, axis=-1)


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


# ----------------------------------------------------------------------
# primitives
# ----------------------------------------------------------------------
def sd_sphere(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    radius: float = 1.0,
) -> np.ndarray:
    center = np.asarray(center, dtype=float)
    return length(p - center) - radius


def sd_box(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    size=(1.0, 1.0, 1.0),
) -> np.ndarray:
    center = np.asarray(center, dtype=float)
    size = np.asarray(size, dtype=float)

    q = np.abs(p - center) - size
    outside = length(np.maximum(q, 0.0))
    inside = np.minimum(np.max(q, axis=-1), 0.0)

    return outside + inside


def sd_torus(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    major: float = 1.0,
    minor: float = 0.25,
) -> np.ndarray:
    center = np.asarray(center, dtype=float)

    q = p - center
    xz = length(q[..., [0, 2]]) - major

    return length(np.stack((xz, q[..., 1]), axis=-1)) - minor


# ----------------------------------------------------------------------
# combinators
# ----------------------------------------------------------------------
def op_union(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.minimum(a, b)


def op_subtraction(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.maximum(a, -b)


def op_smooth_union(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    h = np.clip(0.5 + 0.5 * (b - a) / max(k, 1e-9), 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)


def op_smooth_subtraction(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    return op_smooth_union(a, -b, k)


# ----------------------------------------------------------------------
# domain transforms
# ----------------------------------------------------------------------
def rotate_z(p: np.ndarray, angle: float) -> np.ndarray:
    c = np.cos(angle)
    s = np.sin(angle)

    x = p[..., 0]
    y = p[..., 1]
    z = p[..., 2]

    return np.stack(
        (
            x * c - y * s,
            x * s + y * c,
            z,
        ),
        axis=-1,
    )


def angular_fold(
    p: np.ndarray,
    sectors: int = 9,
    mirror: bool = True,
    angle_offset: float = 0.0,
) -> np.ndarray:
    """Fold angular space into a sector.

    With sectors=9, this creates a 9-fold kaleidoscopic domain directly
    inspired by the radix-9 structure.
    """
    x = p[..., 0]
    y = p[..., 1]
    z = p[..., 2]

    angle = np.arctan2(y, x) + angle_offset
    sector = 2.0 * np.pi / float(sectors)

    if mirror:
        angle = np.abs(((angle + 0.5 * sector) % sector) - 0.5 * sector)
    else:
        angle = angle % sector

    r = np.sqrt(x * x + y * y)

    return np.stack(
        (
            r * np.cos(angle),
            r * np.sin(angle),
            z,
        ),
        axis=-1,
    )


def diagonal_fold(p: np.ndarray) -> np.ndarray:
    """Fold across the x=y plane.

    This is the continuous SDF analogue of the lattice portal quotient
    idea: (x, y) ~ (y, x).
    """
    swap = np.stack(
        (
            p[..., 1],
            p[..., 0],
            p[..., 2],
        ),
        axis=-1,
    )

    mask = p[..., 0] > p[..., 1]
    return np.where(mask[..., None], swap, p)
