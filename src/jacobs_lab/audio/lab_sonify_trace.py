from __future__ import annotations

from typing import List

try:
    from jacobs_lab.core.general_recursive_mapper import digital_root
    from jacobs_lab.trace.lab_trace import LabTrace, TraceBuilder
    from jacobs_lab.audio.sonify import (
        SonifiedStep,
        chord_freqs,
        render,
        root_freq,
        write_wav,
    )
except ImportError:
    from jacobs_lab.core.general_recursive_mapper import digital_root
    from jacobs_lab.trace.lab_trace import LabTrace, TraceBuilder
    from jacobs_lab.audio.sonify import (
        SonifiedStep,
        chord_freqs,
        render,
        root_freq,
        write_wav,
    )


BASE_DURATIONS = {
    "init": 1.2,
    "read": 1.3,
    "slide": 0.9,
    "fold": 1.5,
    "glue": 1.2,
    "branch": 1.1,
    "while_enter": 1.0,
    "while_check": 0.45,
    "while_exit": 1.2,
    "test_node": 1.0,
    "transition": 0.9,
    "move": 0.7,
    "symbol": 0.8,
    "component": 0.9,
    "corpus": 1.0,
    "certificate": 1.3,
    "astar_summary": 1.4,
}

ACCENT_KINDS = {
    "fold",
    "branch",
    "read",
    "certificate",
    "astar_summary",
    "roundtrip",
}

ARPEGGIO_KINDS = {
    "transition",
    "move",
    "symbol",
    "corpus",
    "while_check",
}


def _clamp_root(r) -> int:
    try:
        r = int(r)
    except Exception:
        return 3

    return max(1, min(9, r))


def _event_root(trace: LabTrace, e) -> int:
    src = trace.source
    after = e.after or {}

    if src == "folding_vm":
        cells = after.get("cells")
        if cells:
            return _clamp_root(digital_root(int(cells[0].get("value", 3))))

    if src == "test_walk":
        return _clamp_root(after.get("x_root", 3))

    if src == "triangle_state_machine":
        return _clamp_root(after.get("root", 3))

    if src == "pathfinding":
        pos = after.get("pos")
        if pos:
            return _clamp_root(pos[0])

    if src == "three_body":
        return _clamp_root(after.get("symbol", 3))

    if src == "category_theory":
        return _clamp_root(after.get("root", 3))

    if src == "flexagon":
        return 6

    return _clamp_root(hash(e.kind) % 9 + 1)


def _is_fail(e) -> bool:
    return e.kind == "test_node" and e.meta.get("passed") is False


def sonify_trace(trace: LabTrace, base_duration: float = 0.18) -> List[SonifiedStep]:
    steps: List[SonifiedStep] = []

    for e in trace.events:
        root = _event_root(trace, e)

        duration = base_duration * BASE_DURATIONS.get(e.kind, 1.0)

        accent = e.kind in ACCENT_KINDS or bool(e.meta.get("portal")) or _is_fail(e)

        arpeggiate = e.kind in ARPEGGIO_KINDS

        label = f"{trace.source}:{e.kind}"

        if _is_fail(e):
            neighbor = (root % 9) + 1
            freqs = (
                root_freq(root),
                root_freq(neighbor),
                root_freq(root) / 2,
            )
            arpeggiate = False
            duration = base_duration * 1.6
        else:
            freqs = chord_freqs(root)

        steps.append(
            SonifiedStep(
                letter=e.kind[:1].upper() if e.kind else "?",
                root=root,
                freqs=freqs,
                duration=duration,
                accent=accent,
                label=label,
                arpeggiate=arpeggiate,
            )
        )

    return steps


def write_trace_wav(
    trace: LabTrace,
    path: str,
    base_duration: float = 0.18,
) -> float:
    steps = sonify_trace(trace, base_duration=base_duration)
    audio = render(steps)
    write_wav(path, audio)
    return len(audio)


def _run_self_tests():
    import numpy as np

    b = TraceBuilder("demo", "Sonify demo", initial={})

    b.event("init", after={})

    b.event(
        "fold",
        after={
            "cells": [
                {
                    "value": 6,
                    "members": [6, 9],
                    "portal": True,
                }
            ]
        },
        portal=True,
    )

    b.event("test_node", passed=False)

    tr = b.build()

    steps = sonify_trace(tr)

    assert len(steps) == 3
    assert steps[2].accent

    audio = render(steps)

    assert audio.dtype == np.float32
    assert len(audio) > 0

    print("All lab-sonify-trace self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
