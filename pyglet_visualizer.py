"""
Live pyglet visualization of the test suite's walk through the lattice,
synced to the sonified audio.


Setup:
    pip install pyglet numpy
    python pyglet_visualizer.py
"""

from __future__ import annotations
import pyglet
from pyglet import shapes

from test_harness import run_all_tests
from test_walk_engine import build_test_tree, taken_path, layout_test_tree
from test_sonify import sonify_test_results
from sonify import render, write_wav, SAMPLE_RATE

TEAL = (47, 158, 143)
CORAL = (217, 119, 87)
AMBER = (212, 167, 44)
GRAY = (154, 151, 143)
RED = (192, 57, 43)
BG = (24, 24, 22)

WINDOW_W, WINDOW_H = 1100, 500


def main(
    start_letter: str = "F",
    base_duration: float = 0.45,
    audio_path: str = "test_suite.wav",
):
    print("Running the full lab suite...")
    results = run_all_tests()
    n_pass = sum(r.passed for r in results)
    print(f"{n_pass}/{len(results)} passed")

    root, result_by_depth = build_test_tree(results, start_x=1, start_y=1)
    laid_out = layout_test_tree(root)
    path_ids = {id(n) for n in taken_path(root)}

    # Same steps/durations used for the audio -- reveal timing below is
    # derived from these, so visuals and sound share one clock, not two
    # independently-guessed ones.
    steps = sonify_test_results(
        results, start_letter=start_letter, base_duration=base_duration
    )
    audio = render(steps)
    write_wav(audio_path, audio)

    cumulative = [0.0]
    for s in steps:
        cumulative.append(
            cumulative[-1] + s.duration + 0.03
        )  # matches render()'s inter-step gap

    window = pyglet.window.Window(WINDOW_W, WINDOW_H, caption="Test Suite Lattice Walk")
    pyglet.gl.glClearColor(*(c / 255 for c in BG), 1.0)

    batch = pyglet.graphics.Batch()
    shapes_drawn = []  # keep references alive (pyglet requires this)
    revealed = set()

    status_label = pyglet.text.Label(
        f"0 / {len(results)} tests",
        x=16,
        y=WINDOW_H - 28,
        font_size=16,
        color=(255, 255, 255, 255),
        batch=batch,
    )

    # World-to-screen: fit the spine's x-extent into the window, with a
    # small left margin; y is centered vertically and scaled down since
    # layout_test_tree's y-jitter is deliberately small relative to spacing.
    xs = [ln.x for ln in laid_out]
    x_min, x_max = min(xs), max(xs) if xs else (0, 1)
    x_span = max(x_max - x_min, 1)

    def to_screen(x, y):
        sx = 60 + (x - x_min) / x_span * (WINDOW_W - 120)
        sy = WINDOW_H / 2 - y * 2.2
        return sx, sy

    node_by_id = {id(ln.node): ln for ln in laid_out}

    def reveal(index: int):
        """Called on schedule: reveal the node(s) belonging to test `index`
        (1-based, matching TreeNode.depth) plus its preview stub."""
        revealed.add(index)
        n_done = sum(1 for r in results[:index] if True)
        n_ok = sum(1 for r in results[:index] if r.passed)
        status_label.text = f"{index} / {len(results)} tests   ({n_ok} pass)"

        for ln in laid_out:
            if ln.node.depth != index:
                continue
            sx, sy = to_screen(ln.x, ln.y)
            is_spine = id(ln.node) in path_ids
            r = result_by_depth.get(index)
            if ln.node.portal:
                color = AMBER
            elif not is_spine:
                color = GRAY
            elif r is not None and not r.passed:
                color = RED
            else:
                color = TEAL if ln.node.move == "RIGHT" else CORAL

            radius = 9 if is_spine else 4
            circ = shapes.Circle(sx, sy, radius, color=color, batch=batch)
            shapes_drawn.append(circ)

            if is_spine and r is not None:
                label = pyglet.text.Label(
                    r.module,
                    x=sx,
                    y=sy + 14,
                    font_size=8,
                    color=(255, 255, 255, 220),
                    anchor_x="center",
                    batch=batch,
                )
                shapes_drawn.append(label)

            # Edge from parent (previous spine node) to this node.
            for other_ln in laid_out:
                if any(c is ln.node for c in other_ln.node.children):
                    psx, psy = to_screen(other_ln.x, other_ln.y)
                    line = shapes.Line(
                        psx,
                        psy,
                        sx,
                        sy,
                        thickness=2.5 if is_spine else 1.0,
                        color=color,
                        batch=batch,
                    )
                    line.opacity = 255 if is_spine else 90
                    shapes_drawn.append(line)
                    break

    # Schedule every reveal against the same cumulative timeline as the audio.
    for i in range(1, len(results) + 1):
        pyglet.clock.schedule_once(lambda dt, idx=i: reveal(idx), cumulative[i - 1])

    player = pyglet.media.Player()
    try:
        source = pyglet.media.load(audio_path)
        player.queue(source)
        player.play()
    except Exception as e:
        print(
            f"(audio playback unavailable: {e} -- visualization will still run silently)"
        )

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    pyglet.app.run()


if __name__ == "__main__":
    main()
