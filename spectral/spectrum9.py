from __future__ import annotations

import numpy as np

try:
    from general_recursive_mapper import RecursiveTopology
except ImportError:
    try:
        from jacobs_lab.core.general_recursive_mapper import RecursiveTopology
    except ImportError:
        RecursiveTopology = None


if RecursiveTopology is not None:
    _TOPO = RecursiveTopology(radix=9, multiplier=2)
    TOPOLOGY_ORDER = tuple(_TOPO.cycles[0]) + tuple(_TOPO.cycles[1])
else:
    TOPOLOGY_ORDER = (1, 2, 4, 8, 7, 5, 3, 6, 9)


BAND_ROOTS = TOPOLOGY_ORDER
ROOT_TO_BAND = {root: i for i, root in enumerate(BAND_ROOTS)}

# Stylized visible-range wavelengths, one per topology band.
# This is not a physically calibrated CIE spectral model; it is a
# structural 9-band spectral system.
BAND_WAVELENGTHS = tuple(380.0 + i * (700.0 - 380.0) / 8.0 for i in range(9))

_W = np.asarray(BAND_WAVELENGTHS, dtype=float)


def _gauss(center: float, width: float) -> np.ndarray:
    return np.exp(-0.5 * ((_W - center) / width) ** 2)


# Very rough RGB spectral response curves for stylized rendering.
R_WEIGHTS = _gauss(610.0, 55.0)
G_WEIGHTS = _gauss(545.0, 50.0)
B_WEIGHTS = _gauss(455.0, 55.0)

R_WEIGHTS = R_WEIGHTS / max(float(np.sum(R_WEIGHTS)), 1e-9)
G_WEIGHTS = G_WEIGHTS / max(float(np.sum(G_WEIGHTS)), 1e-9)
B_WEIGHTS = B_WEIGHTS / max(float(np.sum(B_WEIGHTS)), 1e-9)


def spectral_to_rgb(samples: np.ndarray) -> np.ndarray:
    """Convert a 9-band spectral image or vector into stylized RGB.

    Args:
        samples: array with last dimension equal to 9.

    Returns:
        RGB array with last dimension equal to 3.
    """
    samples = np.asarray(samples, dtype=float)

    rgb = np.stack(
        [
            (samples * R_WEIGHTS).sum(axis=-1),
            (samples * G_WEIGHTS).sum(axis=-1),
            (samples * B_WEIGHTS).sum(axis=-1),
        ],
        axis=-1,
    )

    rgb = np.clip(rgb, 0.0, None)

    peak = float(rgb.max())
    if peak > 0.0:
        rgb = rgb / peak

    # Simple gamma correction for display.
    return np.power(rgb, 1.0 / 2.2)


def root_to_rgb(root: int) -> np.ndarray:
    """Return the stylized RGB color of a single root/band."""
    if root not in ROOT_TO_BAND:
        raise ValueError(f"root must be one of {tuple(ROOT_TO_BAND)}")

    one_hot = np.zeros(9, dtype=float)
    one_hot[ROOT_TO_BAND[root]] = 1.0

    return spectral_to_rgb(one_hot)


def band_palette() -> np.ndarray:
    """Return RGB colors for all nine topology bands."""
    return np.stack([root_to_rgb(root) for root in BAND_ROOTS], axis=0)
