from __future__ import annotations
from typing import List
from .triangle_state_machine import TriangleStateMachine, Mode
from .sonify import SonifiedStep, chord_freqs, root_freq, render, write_wav, SAMPLE_RATE
from .test_harness import TestResult, run_all_tests


def sonify_test_results(
    results: List[TestResult],
    sm: TriangleStateMachine = None,
    start_letter: str = "F",
    base_duration: float = 0.45,
) -> List[SonifiedStep]:
    """
    One triangle-state-machine step per test, walked linearly (cycling
    through the 7-letter loop as tests run past 7). PASS gets the normal
    ternary chord for that letter (same construction as sonify.sonify_walk).
    FAIL gets a deliberately dissonant 'wrong note': the letter's root tone
    clashing against its immediate neighbor one 9-EDO step away -- the
    closest possible interval in this tuning, plus a sub-octave for a
    buzzer-like weight -- held slightly longer so failures are unmistakable
    rather than just quieter.
    """
    sm = sm or TriangleStateMachine()
    steps: List[SonifiedStep] = []
    letter = start_letter
    for r in results:
        state = sm.state(letter)
        t = sm.transition(letter)
        if r.passed:
            freqs = chord_freqs(state.root)
            arpeggiate = state.mode == Mode.CONTINUE
            duration = base_duration
            label = f"PASS: {r.module}"
        else:
            clash_root = state.root
            clash_neighbor = (clash_root % 9) + 1
            freqs = (
                root_freq(clash_root),
                root_freq(clash_neighbor),
                root_freq(clash_root) / 2,
            )
            arpeggiate = False
            duration = base_duration * 1.6
            label = f"FAIL: {r.module}"

        steps.append(
            SonifiedStep(
                letter=letter,
                root=state.root,
                freqs=freqs,
                duration=duration,
                accent=not r.passed,
                label=label,
                arpeggiate=arpeggiate,
            )
        )
        letter = t.dst
    return steps


def _run_self_tests():
    import numpy as np

    def mk(name, passed):
        return TestResult(name, passed, 0.001, None if passed else "boom")

    results = [mk("a", True), mk("b", False), mk("c", True)]
    steps = sonify_test_results(results, base_duration=0.2)

    assert len(steps) == 3
    assert steps[0].label.startswith("PASS") and not steps[0].accent
    assert steps[1].label.startswith("FAIL") and steps[1].accent
    assert steps[2].label.startswith("PASS")

    # The FAIL step's duration is longer than a same-letter PASS would be,
    # and it is never arpeggiated (always a struck block chord).
    assert steps[1].duration > 0.2
    assert steps[1].arpeggiate is False

    audio = render(steps)
    assert audio.dtype == np.float32
    assert np.max(np.abs(audio)) <= 1.0 + 1e-6
    assert len(audio) > 0

    print("All test-sonify self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()

    print("\nRunning the full lab suite and sonifying it...")
    results = run_all_tests()
    n_pass = sum(r.passed for r in results)
    print(f"{n_pass}/{len(results)} passed")

    steps = sonify_test_results(results, base_duration=0.45)
    audio = render(steps)
    write_wav("test_suite.wav", audio)
    print(f"Wrote {len(audio)/SAMPLE_RATE:.1f}s of audio to test_suite.wav")

    # Also render a version with a synthetic failure injected, so the
    # dissonant 'wrong note' treatment is actually demonstrated in the
    # deliverable -- the real suite currently has zero failures.
    demo_results = list(results)
    demo_results[5] = TestResult(
        demo_results[5].module, False, 0.0, "synthetic failure for demonstration"
    )
    demo_steps = sonify_test_results(demo_results, base_duration=0.45)
    demo_audio = render(demo_steps)
    write_wav("synthetic_failure.wav", demo_audio)
    print(
        "Wrote test_suite_with_synthetic_failure.wav (one injected FAIL, to demonstrate the clash sound)"
    )
