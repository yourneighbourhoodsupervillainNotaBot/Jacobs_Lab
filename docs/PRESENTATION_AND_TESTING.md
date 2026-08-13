# Presentation & testing

## Audio (sonify.py)
- Pitch: 9-EDO, one step per root — the tuning the radix *actually* has.
- Chords: each root's mod-3 residue class is an exact 3-way division of the
  9-EDO octave (the analog of an augmented triad) — a structural property, not a
  decoration.
- Articulation is read off machine state: jumps accented and longer, same-root
  shorter, CONTINUE = arpeggio, DISCONTINUE = block chord.

## Test sonification (test_sonify.py)
One state-machine step per test. PASS = the letter's ternary chord; FAIL = a
deliberate clash (root + nearest 9-EDO neighbor + sub-octave), held longer and
accented. Outputs `test_suite.wav` plus a synthetic-failure demo.

## Test-suite walk (test_walk_engine + previews)
- PASS advances X (RIGHT/double), FAIL advances Y (UP/half). A zero-failure run
  never touches Y — itself an honest signal.
- Each node keeps the taken child plus an untaken "preview" stub, so the picture
  shows the story and "what didn't happen".
- `test_tree_preview` renders a static PNG; `pyglet_visualizer` reveals nodes on
  the same cumulative timeline as the audio, so sound and picture share one clock.

## Test harness
- Every module exposes `_run_self_tests()`; `test_harness.run_all_tests` imports
  and runs them, capturing pass/fail/duration/error.
- `run_all_tests.py` prints a grouped ledger, supports `--fast`, and returns a
  non-zero exit code on failure (CI-friendly).
- The harness's own self-test uses synthetic ok/fail modules so both branches are
  exercised without depending on a real failure.