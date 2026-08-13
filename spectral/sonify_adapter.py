from __future__ import annotations

import pathlib

try:
    from sonify import SonifiedStep, chord_freqs, render, write_wav
except ImportError:
    try:
        from jacobs_lab.audio.sonify import (
            SonifiedStep,
            chord_freqs,
            render,
            write_wav,
        )
    except ImportError:
        SonifiedStep = None
        chord_freqs = None
        render = None
        write_wav = None


_DOUBLING_ROOTS = {1, 2, 4, 8, 7, 5}


def sonify_render(
    band_stats,
    out_wav: str,
    base_duration: float = 0.35,
    fold_info=None,
) -> bool:
    if SonifiedStep is None:
        return False

    steps = []

    # Portal fold event, if the original fold signature found the portal.
    if fold_info and fold_info.get("portal"):
        steps.append(
            SonifiedStep(
                letter="G",
                root=6,
                freqs=chord_freqs(6),
                duration=base_duration * 1.25,
                accent=True,
                label="portal_fold",
                arpeggiate=False,
            )
        )

    for stats in band_stats:
        root = int(stats.get("root", 3))
        hit = float(stats.get("hit_fraction", 0.0))

        duration = base_duration * (0.18 + 0.85 * hit)

        # Doubling-cycle roots arpeggiate; 3-6-9 roots strike as chords.
        arpeggiate = root in _DOUBLING_ROOTS

        steps.append(
            SonifiedStep(
                letter=str(root),
                root=root,
                freqs=chord_freqs(root),
                duration=duration,
                accent=hit > 0.20,
                label=f"band:{stats.get('wavelength', 0.0):.1f}nm",
                arpeggiate=arpeggiate,
            )
        )

    if not steps:
        return False

    audio = render(steps)

    out = pathlib.Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)

    write_wav(str(out), audio)
    return True
