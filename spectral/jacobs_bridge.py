from __future__ import annotations

import numpy as np

try:
    from .scene_shapes import default_scene_shapes, evaluate_shapes
except ImportError:
    from scene_shapes import default_scene_shapes, evaluate_shapes

try:
    from .sdf import (
        angular_fold,
        diagonal_fold,
        op_smooth_subtraction,
        op_smooth_union,
        rotate_z,
        sd_box,
        sd_sphere,
        sd_torus,
    )
except ImportError:
    from sdf import (
        angular_fold,
        diagonal_fold,
        op_smooth_subtraction,
        op_smooth_union,
        rotate_z,
        sd_box,
        sd_sphere,
        sd_torus,
    )


def _import_folding():
    try:
        import folding_computations as fc

        return fc
    except ImportError:
        try:
            import jacobs_lab.computation.folding_computations as fc

            return fc
        except ImportError:
            return None


def _import_named_aliases():
    try:
        import named_aliases as na

        return na
    except ImportError:
        try:
            import jacobs_lab.core.named_aliases as na

            return na
        except ImportError:
            return None


def fold_signature():
    """Use the original GFEABCD fold as a structural signature.

    This does not directly define the SDF geometry, but it feeds the
    trace and sonification layers with the canonical fold/portal event.
    """
    fc = _import_folding()
    if fc is None:
        return {"error": "folding_computations not available"}

    na = _import_named_aliases()
    if na is None:
        return {"error": "named_aliases not available"}

    try:
        strip = [fc.make_cell(na.LETTER_TO_ROOT[l]) for l in "GFEABCD"]
        res = fc.fold_strip(strip, 3, fc.Combine.PORTAL_MERGE)

        return {
            "strip": "GFEABCD",
            "pivot": int(res.record.pivot),
            "pairs": [list(pair) for pair in res.record.pairs],
            "classes": [sorted(c) for c in res.classes],
            "portal": any(c.portal for c in res.cells),
        }
    except Exception as exc:
        return {"error": str(exc)}


class JacobsSpectralScene:
    """A stylized folded/portal SDF scene.

    Structural influences:

    - 9-sector angular fold from radix-9 topology
    - diagonal fold inspired by (x, y) ~ (y, x) portal quotient
    - portal cut inspired by the {6, 9} portal pair
    - band-dependent dispersion for the 9 spectral bands
    """

    def __init__(
        self,
        sectors: int = 9,
        diagonal: bool = True,
        dispersion: float = 0.18,
        portal_cut: bool = True,
    ):
        self.sectors = int(sectors)
        self.diagonal = bool(diagonal)
        self.dispersion = float(dispersion)
        self.portal_cut = bool(portal_cut)
        self.fold_info = fold_signature()

    def settings(self):
        return {
            "engine": "spectral_sdf_raymarcher",
            "spectral_bands": 9,
            "sectors": self.sectors,
            "diagonal_fold": self.diagonal,
            "dispersion": self.dispersion,
            "portal_cut": self.portal_cut,
            "fold_signature": self.fold_info,
        }

    def sdf(self, p: np.ndarray, band_index: int) -> np.ndarray:
        band_phase = float(band_index) / 9.0

        # Spectral dispersion as a small band-dependent rotation.
        angle_offset = (
            band_phase * (2.0 * np.pi / float(max(1, self.sectors))) * self.dispersion
        )

        q = rotate_z(p, angle_offset)

        # 9-fold kaleidoscopic domain fold.
        if self.sectors > 1:
            q = angular_fold(q, sectors=self.sectors, mirror=True)

        # Portal quotient analogue: (x, y) ~ (y, x).
        if self.diagonal:
            q = diagonal_fold(q)

        # Evaluate the user-editable shape list.
        d = evaluate_shapes(q, default_scene_shapes(), band_index)

        if self.portal_cut:
            # A small cut near the folded diagonal, inspired by the
            # portal pair {6, 9}.
            cut_radius = 0.22 + 0.02 * np.sin(4.0 * np.pi * band_phase)
            d_cut = sd_sphere(q, (0.85, 0.85, 0.0), cut_radius)
            d = op_smooth_subtraction(d, d_cut, 0.08)

        return d
