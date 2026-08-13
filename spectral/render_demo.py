from __future__ import annotations

import argparse
import pathlib

import numpy as np

try:
    from .jacobs_bridge import JacobsSpectralScene
    from .raymarch import camera_rays, raymarch_debug, render_spectral
    from .sonify_adapter import sonify_render
    from .trace_adapter import save_trace, trace_render
except ImportError:
    from jacobs_bridge import JacobsSpectralScene
    from raymarch import camera_rays, raymarch_debug, render_spectral
    from sonify_adapter import sonify_render
    from trace_adapter import save_trace, trace_render


def save_image(path, rgb):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Prefer PNG/JPEG through matplotlib if available.
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.imsave(path, rgb)
            return path
        except Exception:
            path = path.with_suffix(".ppm")

    # Fallback: binary PPM.
    rgb8 = (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)

    with open(path, "wb") as f:
        header = f"P6\n{rgb8.shape[1]} {rgb8.shape[0]}\n255\n"
        f.write(header.encode("ascii"))
        f.write(rgb8.tobytes())

    return path


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render a stylized 9-band spectral SDF ray-marching scene."
    )

    ap.add_argument("--width", type=int, default=320)
    ap.add_argument("--height", type=int, default=200)
    ap.add_argument("--steps", type=int, default=80)
    ap.add_argument("--fov", type=float, default=50.0)

    ap.add_argument("--output", default="renders/spectral_fold.png")
    ap.add_argument("--trace", default="traces/spectral_fold.json")
    ap.add_argument("--wav", default=None)

    ap.add_argument("--sectors", type=int, default=9)
    ap.add_argument("--dispersion", type=float, default=0.18)
    ap.add_argument("--debug-band", type=int, default=4)

    ap.add_argument(
        "--no-diagonal",
        action="store_true",
        help="Disable the diagonal portal fold.",
    )
    ap.add_argument(
        "--no-portal",
        action="store_true",
        help="Disable the portal cut.",
    )

    args = ap.parse_args(argv)

    scene = JacobsSpectralScene(
        sectors=args.sectors,
        diagonal=not args.no_diagonal,
        dispersion=args.dispersion,
        portal_cut=not args.no_portal,
    )

    eye = np.asarray([2.7, 1.7, -3.1], dtype=float)
    target = np.asarray([0.0, 0.0, 0.0], dtype=float)
    up = np.asarray([0.0, 1.0, 0.0], dtype=float)

    print("Rendering spectral SDF scene...")

    rgb, spectral, band_stats = render_spectral(
        width=args.width,
        height=args.height,
        scene_sdf=scene.sdf,
        eye=eye,
        target=target,
        up=up,
        fov_deg=args.fov,
        max_steps=args.steps,
    )

    image_path = save_image(args.output, rgb)
    print(f"Wrote image: {image_path}")

    settings = scene.settings()
    settings.update(
        {
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "fov": args.fov,
            "eye": list(eye),
            "target": list(target),
            "up": list(up),
        }
    )

    # Trace a single debug ray through one spectral band.
    directions = camera_rays(
        args.width,
        args.height,
        eye,
        target,
        up,
        args.fov,
    )

    cy = args.height // 2
    cx = args.width // 2
    debug_dir = directions[cy, cx]

    debug_band = max(0, min(8, args.debug_band))

    debug_events = raymarch_debug(
        origin=eye,
        direction=debug_dir,
        sdf_fn=lambda p: scene.sdf(p, debug_band),
        max_steps=min(args.steps, 160),
    )

    trace = trace_render(
        settings=settings,
        band_stats=band_stats,
        debug_events=debug_events,
        fold_info=scene.fold_info,
    )

    save_trace(trace, args.trace)
    print(f"Wrote trace: {args.trace}")

    if args.wav:
        ok = sonify_render(
            band_stats,
            args.wav,
            fold_info=scene.fold_info,
        )

        if ok:
            print(f"Wrote audio: {args.wav}")
        else:
            print("Audio not written: sonify layer unavailable or no band events.")

    print()
    print("Band stats:")
    for stats in band_stats:
        print(
            f"  band {stats['band']} | root {stats['root']} | "
            f"{stats['wavelength']:6.1f} nm | hit {stats['hit_fraction']:0.3f}"
        )


if __name__ == "__main__":
    main()
