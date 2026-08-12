"""
Live pyglet visualization of the test suite's walk through the lattice,
synced to the sonified audio, with an interactive node inspector.

Setup:
    pip install pyglet numpy

Run:
    python pyglet_visualizer.py

Controls:
    click       inspect node
    LEFT/RIGHT  scrub along the taken spine
    F           follow latest revealed node again
    I           toggle inspector panel
"""

from __future__ import annotations

import pyglet
from pyglet import shapes
from pyglet.window import key

from .recursive_lattice import RecursiveLattice
from .test_harness import run_all_tests
from .test_walk_engine import build_test_tree, taken_path, layout_test_tree
from .test_sonify import sonify_test_results
from .sonify import render, write_wav, SAMPLE_RATE
from .node_inspector import NodeInspector, draw_inspector

# ----------------------------------------------------------------------
# Pyglet cleanup compatibility
# ----------------------------------------------------------------------
try:
    from pyglet.text import DocumentLabel

    _original_document_label_del = DocumentLabel.__del__

    def _safe_document_label_del(self):
        try:
            if hasattr(self, "_boxes"):
                _original_document_label_del(self)
        except Exception:
            pass

    DocumentLabel.__del__ = _safe_document_label_del

except Exception:
    pass

TEAL = (47, 158, 143)
CORAL = (217, 119, 87)
AMBER = (212, 167, 44)
GRAY = (154, 151, 143)
RED = (192, 57, 43)
BG = (24, 24, 22)

WINDOW_W, WINDOW_H = 1280, 800


def _make_line(x1, y1, x2, y2, color, batch, width=1.0):
    """Compatibility helper for pyglet Line keyword naming."""
    try:
        return shapes.Line(x1, y1, x2, y2, width=width, color=color, batch=batch)
    except TypeError:
        return shapes.Line(x1, y1, x2, y2, thickness=width, color=color, batch=batch)


def main(
    start_letter: str = "F",
    base_duration: float = 0.45,
    audio_path: str = "test_suite.wav",
):
    print("Running the full lab suite...")
    results = run_all_tests()
    n_pass = sum(r.passed for r in results)
    print(f"{n_pass}/{len(results)} passed")

    lattice = RecursiveLattice(radix=9, x_multiplier=2)

    root, result_by_depth = build_test_tree(
        results,
        lattice,
        start_x=1,
        start_y=1,
    )

    laid_out = layout_test_tree(root)

    spine = taken_path(root)
    path_ids = {id(n) for n in spine}
    spine_by_depth = {n.depth: n for n in spine}

    parent_by_id = {id(root): None}

    def link(node: TreeNode):
        for child in node.children:
            parent_by_id[id(child)] = node
            link(child)

    link(root)

    # Same steps/durations used for the audio, so visuals and sound share one clock.
    steps = sonify_test_results(
        results,
        start_letter=start_letter,
        base_duration=base_duration,
    )

    audio = render(steps)
    write_wav(audio_path, audio)

    cumulative = [0.0]
    for s in steps:
        cumulative.append(cumulative[-1] + s.duration + 0.03)

    window = pyglet.window.Window(
        WINDOW_W,
        WINDOW_H,
        caption="Test Suite Lattice Walk + Node Inspector",
    )
    pyglet.gl.glClearColor(*(c / 255 for c in BG), 1.0)

    batch = pyglet.graphics.Batch()
    inspector_batch = pyglet.graphics.Batch()

    shapes_drawn = []
    inspector_objects = []

    revealed = set()

    selected = {
        "node": root,
        "follow": True,
    }

    latest_depth = {"v": 0}
    inspector_visible = {"v": True}

    status_label = pyglet.text.Label(
        f"0 / {len(results)} tests",
        x=16,
        y=WINDOW_H - 28,
        font_size=16,
        color=(255, 255, 255, 255),
        batch=batch,
    )

    controls_label = pyglet.text.Label(
        "click: inspect node | LEFT/RIGHT: scrub | F: follow audio | I: toggle inspector",
        x=16,
        y=WINDOW_H - 52,
        font_size=11,
        color=(190, 190, 190, 255),
        batch=batch,
    )

    xs = [ln.x for ln in laid_out]
    x_min, x_max = (min(xs), max(xs)) if xs else (0, 1)
    x_span = max(x_max - x_min, 1)

    graph_w = max(320, WINDOW_W - 520)

    def to_screen(x, y):
        sx = 40 + (x - x_min) / x_span * graph_w
        sy = WINDOW_H / 2 - y * 2.2
        return sx, sy

    screen_pos = {id(ln.node): to_screen(ln.x, ln.y) for ln in laid_out}
    node_by_id = {id(ln.node): ln.node for ln in laid_out}

    inspector = NodeInspector(lattice)

    def clear_inspector():
        while inspector_objects:
            obj = inspector_objects.pop()

            # Pyglet Labels can double-delete during garbage collection in
            # some versions. Instead of manually deleting them, detach them
            # from the batch and clear their text.
            if hasattr(obj, "text") and hasattr(obj, "batch"):
                try:
                    obj.batch = None
                    obj.text = ""
                except Exception:
                    pass
                continue

            # Shapes are usually safe to delete directly.
            try:
                obj.delete()
            except Exception:
                pass

    def update_inspector(node):
        clear_inspector()

        if not inspector_visible["v"]:
            return

        parent = parent_by_id.get(id(node))
        result = result_by_depth.get(node.depth)
        note = "taken path" if id(node) in path_ids else "preview stub"

        info = inspector.inspect(node, parent, result, note)
        draw_inspector(
            info,
            inspector_batch,
            inspector_objects,
            WINDOW_W,
            WINDOW_H,
        )

    def reveal(index: int):
        """Reveal node(s) belonging to test index, 1-based."""
        revealed.add(index)

        n_ok = sum(1 for r in results[:index] if r.passed)
        status_label.text = f"{index} / {len(results)} tests   ({n_ok} pass)"

        for ln in laid_out:
            if ln.node.depth != index:
                continue

            sx, sy = to_screen(ln.x, ln.y)
            is_spine = id(ln.node) in path_ids
            r = result_by_depth.get(index)
            move = (ln.node.move or "").strip()

            if ln.node.portal:
                color = AMBER
            elif not is_spine:
                color = GRAY
            elif r is not None and not r.passed:
                color = RED
            else:
                color = TEAL if move == "RIGHT" else CORAL

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

            # Edge from parent to this node.
            for other_ln in laid_out:
                if any(c is ln.node for c in other_ln.node.children):
                    psx, psy = to_screen(other_ln.x, other_ln.y)

                    line = _make_line(
                        psx,
                        psy,
                        sx,
                        sy,
                        color=color,
                        batch=batch,
                        width=2.5 if is_spine else 1.0,
                    )

                    if hasattr(line, "opacity"):
                        line.opacity = 255 if is_spine else 90

                    shapes_drawn.append(line)
                    break

        latest_depth["v"] = index

        if selected["follow"]:
            selected["node"] = spine_by_depth.get(index, selected["node"])
            update_inspector(selected["node"])

    @window.event
    def on_mouse_press(x, y, button, modifiers):
        best = None
        best_d2 = 18 * 18

        for node_id, (sx, sy) in screen_pos.items():
            d2 = (x - sx) ** 2 + (y - sy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best = node_by_id[node_id]

        if best is not None:
            selected["node"] = best
            selected["follow"] = False
            update_inspector(best)

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.LEFT:
            depth = selected["node"].depth
            new_depth = max(0, depth - 1)
            selected["node"] = spine_by_depth.get(new_depth, selected["node"])
            selected["follow"] = False
            update_inspector(selected["node"])

        elif symbol == key.RIGHT:
            depth = selected["node"].depth
            new_depth = min(len(results), depth + 1)
            selected["node"] = spine_by_depth.get(new_depth, selected["node"])
            selected["follow"] = False
            update_inspector(selected["node"])

        elif symbol == key.F:
            selected["follow"] = True
            selected["node"] = spine_by_depth.get(latest_depth["v"], root)
            update_inspector(selected["node"])

        elif symbol == key.I:
            inspector_visible["v"] = not inspector_visible["v"]
            update_inspector(selected["node"])

    for i in range(1, len(results) + 1):
        pyglet.clock.schedule_once(
            lambda dt, idx=i: reveal(idx),
            cumulative[i - 1],
        )

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
        inspector_batch.draw()

    update_inspector(root)
    pyglet.app.run()


if __name__ == "__main__":
    main()
