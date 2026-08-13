from __future__ import annotations

from typing import Dict, List

import numpy as np

try:
    from .sdf import (
        length,
        op_smooth_subtraction,
        op_smooth_union,
        sd_box,
        sd_sphere,
        sd_torus,
    )
except ImportError:
    from sdf import (
        length,
        op_smooth_subtraction,
        op_smooth_union,
        sd_box,
        sd_sphere,
        sd_torus,
    )


# ----------------------------------------------------------------------
# Extra SDF primitives
# ----------------------------------------------------------------------
def sd_capsule(
    p: np.ndarray,
    a=(0.0, 0.0, 0.0),
    b=(0.0, 1.0, 0.0),
    radius: float = 0.1,
) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    pa = p - a
    ba = b - a

    denom = float(np.dot(ba, ba))
    h = np.clip(np.sum(pa * ba, axis=-1) / max(denom, 1e-9), 0.0, 1.0)
    h = np.expand_dims(h, axis=-1)

    return length(pa - ba * h) - radius


def sd_cylinder(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    radius: float = 0.2,
    height: float = 0.5,
) -> np.ndarray:
    center = np.asarray(center, dtype=float)

    q = p - center
    r = length(q[..., [0, 2]]) - radius
    y = np.abs(q[..., 1]) - height / 2.0

    outside = length(np.maximum(np.stack((r, y), axis=-1), 0.0))
    inside = np.minimum(np.maximum(r, y), 0.0)

    return outside + inside


def sd_cone(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    radius: float = 0.2,
    height: float = 0.5,
) -> np.ndarray:
    center = np.asarray(center, dtype=float)

    q = p - center
    r = length(q[..., [0, 2]])
    y = q[..., 1]

    t = np.clip((y + height / 2.0) / max(height, 1e-9), 0.0, 1.0)

    side = r - radius * (1.0 - t)
    cap = np.abs(y) - height / 2.0

    return np.maximum(side, cap)


def sd_ellipsoid(
    p: np.ndarray,
    center=(0.0, 0.0, 0.0),
    radii=(0.3, 0.2, 0.2),
) -> np.ndarray:
    center = np.asarray(center, dtype=float)
    radii = np.asarray(radii, dtype=float)

    q = p - center

    k0 = length(q / radii)
    k1 = length(q / (radii * radii))

    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_plane(
    p: np.ndarray,
    normal=(0.0, 1.0, 0.0),
    offset: float = 0.0,
) -> np.ndarray:
    normal = np.asarray(normal, dtype=float)
    normal = normal / max(float(np.linalg.norm(normal)), 1e-9)

    return np.sum(p * normal, axis=-1) + offset


# ----------------------------------------------------------------------
# Shape evaluation
# ----------------------------------------------------------------------
def evaluate_shape(
    p: np.ndarray,
    spec: Dict,
    band_index: int = 0,
) -> np.ndarray:
    kind = spec.get("kind", "sphere")

    pulse = float(spec.get("pulse", 0.0))
    phase = float(spec.get("phase", 0.0))
    band_phase = float(band_index) / 9.0

    swell = pulse * np.sin(2.0 * np.pi * (band_phase + phase))

    if kind == "sphere":
        radius = max(1e-4, float(spec.get("radius", 0.2)) + float(swell))
        return sd_sphere(p, spec.get("center", (0.0, 0.0, 0.0)), radius)

    if kind == "box":
        size = np.asarray(spec.get("size", (0.2, 0.2, 0.2)), dtype=float)
        size = np.maximum(size + float(swell), 1e-4)
        return sd_box(p, spec.get("center", (0.0, 0.0, 0.0)), size)

    if kind == "torus":
        major = float(spec.get("major", 1.0)) + 0.25 * float(swell)
        minor = max(1e-4, float(spec.get("minor", 0.1)) + float(swell))
        return sd_torus(p, spec.get("center", (0.0, 0.0, 0.0)), major, minor)

    if kind == "capsule":
        radius = max(1e-4, float(spec.get("radius", 0.1)) + float(swell))
        return sd_capsule(
            p,
            spec.get("a", (0.0, 0.0, 0.0)),
            spec.get("b", (0.0, 1.0, 0.0)),
            radius,
        )

    if kind == "cylinder":
        radius = max(1e-4, float(spec.get("radius", 0.2)) + float(swell))
        height = max(1e-4, float(spec.get("height", 0.5)))
        return sd_cylinder(
            p,
            spec.get("center", (0.0, 0.0, 0.0)),
            radius,
            height,
        )

    if kind == "cone":
        radius = max(1e-4, float(spec.get("radius", 0.2)) + float(swell))
        height = max(1e-4, float(spec.get("height", 0.5)))
        return sd_cone(
            p,
            spec.get("center", (0.0, 0.0, 0.0)),
            radius,
            height,
        )

    if kind == "ellipsoid":
        radii = np.asarray(spec.get("radii", (0.3, 0.2, 0.2)), dtype=float)
        radii = np.maximum(radii + float(swell), 1e-4)
        return sd_ellipsoid(
            p,
            spec.get("center", (0.0, 0.0, 0.0)),
            radii,
        )

    if kind == "plane":
        offset = float(spec.get("offset", 0.0)) + float(swell)
        return sd_plane(
            p,
            spec.get("normal", (0.0, 1.0, 0.0)),
            offset,
        )

    raise ValueError(f"unknown shape kind: {kind}")


def evaluate_shapes(
    p: np.ndarray,
    shapes: List[Dict],
    band_index: int = 0,
) -> np.ndarray:
    d = None

    for spec in shapes:
        sd = evaluate_shape(p, spec, band_index)
        blend = float(spec.get("blend", 0.0))
        subtract = bool(spec.get("subtract", False))

        if subtract:
            if d is None:
                d = -sd
            elif blend > 0.0:
                d = op_smooth_subtraction(d, sd, blend)
            else:
                d = np.maximum(d, -sd)
        else:
            if d is None:
                d = sd
            elif blend > 0.0:
                d = op_smooth_union(d, sd, blend)
            else:
                d = np.minimum(d, sd)

    if d is None:
        return sd_sphere(p, (0.0, 0.0, 0.0), 0.5)

    return d


# ----------------------------------------------------------------------
# Default scene shapes
# ----------------------------------------------------------------------
def default_scene_shapes() -> List[Dict]:
    """
    Edit this list to add/remove shapes.

    Important: because the main scene applies a 9-sector fold, shapes
    placed here will be folded into the kaleidoscopic domain.
    """
    return [
        {
            "kind": "sphere",
            "center": (0.0, 0.0, 0.0),
            "radius": 0.52,
            "blend": 0.14,
            "pulse": 0.05,
            "phase": 0.0,
        },
        {
            "kind": "torus",
            "center": (0.0, 0.0, 0.0),
            "major": 1.02,
            "minor": 0.08,
            "blend": 0.12,
            "pulse": 0.03,
            "phase": 0.25,
        },
        {
            "kind": "box",
            "center": (-0.55, 0.25, 0.15),
            "size": (0.18, 0.18, 0.18),
            "blend": 0.08,
            "pulse": 0.02,
            "phase": 0.5,
        },
        {
            "kind": "capsule",
            "a": (-0.45, -0.35, 0.10),
            "b": (0.35, 0.15, 0.10),
            "radius": 0.09,
            "blend": 0.08,
            "pulse": 0.015,
            "phase": 0.75,
        },
        {
            "kind": "cylinder",
            "center": (0.55, -0.25, 0.20),
            "radius": 0.15,
            "height": 0.50,
            "blend": 0.08,
            "pulse": 0.02,
            "phase": 0.33,
        },
        {
            "kind": "ellipsoid",
            "center": (-0.15, 0.55, -0.25),
            "radii": (0.30, 0.18, 0.18),
            "blend": 0.08,
            "pulse": 0.02,
            "phase": 0.66,
        },
        {
            "kind": "cone",
            "center": (0.20, 0.45, 0.35),
            "radius": 0.20,
            "height": 0.45,
            "blend": 0.08,
            "pulse": 0.02,
            "phase": 0.10,
        },
    ]
