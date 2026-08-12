from __future__ import annotations

import wave
import struct
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from legacy.flat_modules.triangle_state_machine import TriangleStateMachine, Mode

SAMPLE_RATE = 44100


# ----------------------------------------------------------------------
# 1) Pitch: a 9-tone equal division of the octave (9-EDO), one step per
#    root value 1..9 -- directly matching radix=9, rather than forcing
#    the system onto a 12-tone piano scale it has no natural relationship to.
# ----------------------------------------------------------------------


def root_freq(root: int, base_freq: float = 220.0, radix: int = 9) -> float:
    """9-EDO frequency for a given root (1..radix). root=1 is the base."""
    return base_freq * 2 ** ((root - 1) / radix)


# ----------------------------------------------------------------------
# 2) Ternary chords: NOT an arbitrary 3-note stack. Because radix=9 is
#    divisible by 3, every root's mod-3 class {3,6,9}/{1,4,7}/{2,5,8} is
#    already an exact 3-way equal division of the 9-EDO octave (3 steps
#    apart each) -- the direct 9-EDO analog of a 12-EDO augmented triad.
#    This is where 'ternary system instead of binary' and 'chords' come
#    from: a real structural property of the radix, not a decoration.
# ----------------------------------------------------------------------


def mod3_chord_roots(root: int, radix: int = 9) -> Tuple[int, int, int]:
    """The three roots sharing root's residue mod 3, in ascending order."""
    residue = root % 3
    members = [r for r in range(1, radix + 1) if r % 3 == residue]
    assert len(members) == 3, "chord construction assumes radix divisible by 3"
    return tuple(members)  # type: ignore[return-value]


def chord_freqs(root: int, base_freq: float = 220.0) -> Tuple[float, float, float]:
    roots = mod3_chord_roots(root)
    return tuple(root_freq(r, base_freq) for r in roots)  # type: ignore[return-value]


# ----------------------------------------------------------------------
# 3) Synthesis
# ----------------------------------------------------------------------


def _tone(freq: float, duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """A single tone: fundamental + two weak harmonics, simple ADSR envelope."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave_ = (
        1.00 * np.sin(2 * np.pi * freq * t)
        + 0.30 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.15 * np.sin(2 * np.pi * freq * 3 * t)
    )
    n = len(t)
    a, d, r = int(0.05 * n), int(0.15 * n), int(0.25 * n)
    s = max(n - a - d - r, 0)
    env = np.concatenate([
        np.linspace(0, 1, a, endpoint=False) if a else np.array([]),
        np.linspace(1, 0.7, d, endpoint=False) if d else np.array([]),
        np.full(s, 0.7),
        np.linspace(0.7, 0, r, endpoint=True) if r else np.array([]),
    ])
    env = env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))
    return wave_ * env


def _chord(freqs: Tuple[float, ...], duration: float, accent: bool = False) -> np.ndarray:
    tones = [_tone(f, duration) for f in freqs]
    mixed = sum(tones) / len(tones)
    if accent:
        mixed = mixed * 1.25
    return mixed


# ----------------------------------------------------------------------
# 4) The actual mapping from the triangle state machine's walk to audio.
#    Every decision below is read directly off real machine state -- no
#    free-standing musical choices that don't trace back to the structure.
# ----------------------------------------------------------------------


@dataclass
class SonifiedStep:
    letter: str
    root: int
    freqs: Tuple[float, float, float]
    duration: float
    accent: bool
    label: str  # the classify_root_pair() result driving articulation
    arpeggiate: bool  # True for CONTINUE states, False (block chord) for DISCONTINUE


def sonify_walk(
    sm: TriangleStateMachine, start: str = "F", loops: int = 3, base_duration: float = 0.5
) -> List[SonifiedStep]:
    steps: List[SonifiedStep] = []
    total = loops * len(sm.transitions)
    letter = start
    for i in range(total):
        state = sm.state(letter)
        t = sm.transition(letter)
        label = sm.classify_transition(t)

        # Jumps between the two underlying cycles get an accent and a
        # slightly longer duration -- they're the harmonically 'furthest'
        # moves the structure makes. Same-root transitions (state-only
        # change, e.g. F->G) get a shorter duration since no root moved.
        accent = "jump" in label
        duration = base_duration
        if "same root" in label:
            duration = base_duration * 0.6
        elif accent:
            duration = base_duration * 1.3

        steps.append(SonifiedStep(
            letter=letter,
            root=state.root,
            freqs=chord_freqs(state.root),
            duration=duration,
            accent=accent,
            label=label,
            arpeggiate=(state.mode == Mode.CONTINUE),
        ))
        letter = t.dst
    return steps


def render(steps: List[SonifiedStep], sr: int = SAMPLE_RATE) -> np.ndarray:
    chunks = []
    for s in steps:
        if s.arpeggiate:
            # CONTINUE: ascending arpeggio across the ternary chord.
            third = s.duration / 3
            parts = [_tone(f, third) for f in sorted(s.freqs)]
            chunk = np.concatenate(parts)
        else:
            # DISCONTINUE: struck as a single block chord.
            chunk = _chord(s.freqs, s.duration, accent=s.accent)
        gap = np.zeros(int(sr * 0.03))
        chunks.append(chunk)
        chunks.append(gap)
    full = np.concatenate(chunks) if chunks else np.zeros(1)
    peak = np.max(np.abs(full)) or 1.0
    return (full / peak * 0.85).astype(np.float32)


def write_wav(path: str, audio: np.ndarray, sr: int = SAMPLE_RATE):
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    # mod-3 chord construction: every root's chord partition is exact and
    # symmetric (radix=9 divides evenly into 3 classes of 3).
    for r in range(1, 10):
        chord = mod3_chord_roots(r)
        assert len(chord) == 3
        assert all(c % 3 == r % 3 for c in chord)
        assert len(set(chord)) == 3

    # 9-EDO: root 1 and root 10-equivalent (root 1 an octave up) differ by
    # exactly a factor of 2 (one octave), confirming the tuning is correct.
    assert abs(root_freq(1, 220.0) * 2 - root_freq(1, 220.0) * 2) < 1e-9
    assert abs(root_freq(10, 220.0, radix=9) / root_freq(1, 220.0, radix=9) - 2.0) < 1e-9

    sm = TriangleStateMachine()
    steps = sonify_walk(sm, start="F", loops=2, base_duration=0.3)
    assert len(steps) == 14  # 2 loops * 7 states
    assert [s.letter for s in steps[:7]] == ["F", "G", "E", "D", "C", "B", "A"]

    # Jump transitions are exactly the ones classify_root_pair calls jumps.
    jump_letters = {s.letter for s in steps[:7] if s.accent}
    expected_jumps = {t.src for t, lab in sm.classify_all() if "jump" in lab}
    assert jump_letters == expected_jumps

    audio = render(steps)
    assert audio.dtype == np.float32
    assert np.max(np.abs(audio)) <= 1.0 + 1e-6
    assert len(audio) > 0

    print("All sonification self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()

    sm = TriangleStateMachine()
    steps = sonify_walk(sm, start="F", loops=4, base_duration=0.45)

    print("\nWalk:")
    for s in steps[:7]:
        print(f"  {s.letter} (root {s.root}): chord={[round(f,1) for f in s.freqs]}Hz "
              f"mode={'arpeggio' if s.arpeggiate else 'block'} "
              f"{'[ACCENT: ' + s.label + ']' if s.accent else ''}")

    audio = render(steps)
    write_wav("/home/claude/triangle_walk.wav", audio)
    print(f"\nWrote {len(audio)/SAMPLE_RATE:.1f}s of audio to triangle_walk.wav")
