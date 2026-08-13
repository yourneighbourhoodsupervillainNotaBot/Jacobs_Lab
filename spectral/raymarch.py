from __future__ import annotations

import numpy as np

try:
    from .spectrum9 import BAND_ROOTS, BAND_WAVELENGTHS, spectral_to_rgb
except ImportError:
    from spectrum9 import BAND_ROOTS, BAND_WAVELENGTHS, spectral_to_rgb


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def camera_rays(
    width: int,
    height: int,
    eye,
    target,
    up,
    fov_deg: float = 50.0,
) -> np.ndarray:
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(target, dtype=float)
    up = np.asarray(up, dtype=float)

    forward = normalize(target - eye)
    right = normalize(np.cross(forward, up))
    real_up = np.cross(right, forward)

    aspect = width / height
    scale = np.tan(np.radians(fov_deg) / 2.0)

    i, j = np.meshgrid(
        np.arange(width),
        np.arange(height),
        indexing="xy",
    )

    x = (2.0 * (i + 0.5) / width - 1.0) * aspect * scale
    y = (1.0 - 2.0 * (j + 0.5) / height) * scale

    directions = (
        forward[None, None, :]
        + x[..., None] * right[None, None, :]
        + y[..., None] * real_up[None, None, :]
    )

    return normalize(directions)


def raymarch(
    origin: np.ndarray,
    direction: np.ndarray,
    sdf_fn,
    max_steps: int = 96,
    max_dist: float = 30.0,
    eps: float = 1e-3,
):
    """Vectorized sphere tracing."""
    shape = origin.shape[:-1]

    t = np.zeros(shape, dtype=float)
    hit = np.zeros(shape, dtype=bool)
    active = np.ones(shape, dtype=bool)

    for _ in range(max_steps):
        p = origin + direction * t[..., None]
        d = sdf_fn(p)

        step = np.maximum(d, eps * 0.25)

        hit_now = active & (d < eps)
        hit |= hit_now

        active &= ~hit_now
        active &= t < max_dist

        t += step * active

        if not np.any(active):
            break

    hit &= t <= max_dist
    return hit, t


def estimate_normal(p: np.ndarray, sdf_fn, eps: float = 1e-3) -> np.ndarray:
    dx = np.asarray([eps, 0.0, 0.0], dtype=float)
    dy = np.asarray([0.0, eps, 0.0], dtype=float)
    dz = np.asarray([0.0, 0.0, eps], dtype=float)

    nx = sdf_fn(p + dx) - sdf_fn(p - dx)
    ny = sdf_fn(p + dy) - sdf_fn(p - dy)
    nz = sdf_fn(p + dz) - sdf_fn(p - dz)

    return normalize(np.stack((nx, ny, nz), axis=-1))


def raymarch_debug(
    origin,
    direction,
    sdf_fn,
    max_steps: int = 96,
    max_dist: float = 30.0,
    eps: float = 1e-3,
):
    """Trace one ray and return per-step events for inspection."""
    origin = np.asarray(origin, dtype=float)
    direction = np.asarray(direction, dtype=float)

    t = 0.0
    events = []

    for step in range(max_steps):
        p = origin + direction * t
        d_raw = sdf_fn(p)
        d = float(np.asarray(d_raw).reshape(-1)[0])

        events.append(
            {
                "step": step,
                "t": float(t),
                "p": [float(p[0]), float(p[1]), float(p[2])],
                "distance": d,
            }
        )

        if d < eps:
            events[-1]["hit"] = True
            break

        if t > max_dist:
            events[-1]["miss"] = True
            break

        t += max(d, eps * 0.25)

    return events


def render_spectral(
    width: int,
    height: int,
    scene_sdf,
    eye,
    target,
    up,
    fov_deg: float = 50.0,
    max_steps: int = 96,
    max_dist: float = 30.0,
    eps: float = 1e-3,
):
    """Render a 9-band spectral image.

    scene_sdf must have signature:

        scene_sdf(p, band_index) -> distance
    """
    eye = np.asarray(eye, dtype=float)

    directions = camera_rays(width, height, eye, target, up, fov_deg)
    origin = np.broadcast_to(eye, directions.shape)

    spectral = np.zeros((height, width, 9), dtype=float)
    band_stats = []

    light_dir = normalize(np.asarray([0.55, 0.75, -0.55], dtype=float))

    for band in range(9):

        def sdf(p, band=band):
            return scene_sdf(p, band)

        hit, t = raymarch(
            origin,
            directions,
            sdf,
            max_steps=max_steps,
            max_dist=max_dist,
            eps=eps,
        )

        p = origin + directions * t[..., None]
        n = estimate_normal(p, sdf)

        diffuse = np.clip(np.sum(n * light_dir, axis=-1), 0.0, 1.0)
        fog = np.exp(-0.045 * np.clip(t, 0.0, max_dist))

        intensity = np.where(
            hit,
            (0.16 + 0.84 * diffuse) * fog,
            0.0,
        )

        spectral[..., band] = intensity

        band_stats.append(
            {
                "band": band,
                "root": int(BAND_ROOTS[band]),
                "wavelength": float(BAND_WAVELENGTHS[band]),
                "hit_fraction": float(hit.mean()),
                "max_intensity": float(intensity.max()),
            }
        )

    rgb = spectral_to_rgb(spectral)
    return rgb, spectral, band_stats
