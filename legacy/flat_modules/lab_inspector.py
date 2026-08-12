from __future__ import annotations

import json
import math
from typing import List

from lab_compat import apply_pyglet_label_guard
from lab_trace import LabTrace


def _short(s: str, n: int = 110) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def _short_value(v, n: int = 88) -> str:
    if isinstance(v, (dict, list, tuple, set, frozenset)):
        try:
            s = json.dumps(v, sort_keys=True, default=str)
        except Exception:
            s = str(v)
    else:
        s = str(v)

    return _short(s, n)


def _add_mapping_lines(lines: List[str], label: str, value) -> None:
    lines.append(label)

    if isinstance(value, dict):
        if not value:
            lines.append("  {}")
        else:
            for k, v in value.items():
                lines.append(f"  {k}: {_short_value(v)}")
    else:
        lines.append(f"  {_short_value(value)}")


def show_lab_trace(
    trace: LabTrace,
    title: str | None = None,
    step_interval: float = 0.45,
):
    if not trace.events:
        print("Trace is empty.")
        return

    apply_pyglet_label_guard()

    import pyglet
    from pyglet import shapes
    from pyglet.window import key

    WINDOW_W, WINDOW_H = 1400, 800

    EVENT_LINES = 30
    DETAIL_LINES = 20

    CANVAS_X = 430
    CANVAS_Y = 40
    CANVAS_W = WINDOW_W - 460
    CANVAS_H = 260

    window = pyglet.window.Window(
        WINDOW_W,
        WINDOW_H,
        caption=title or trace.title,
    )

    pyglet.gl.glClearColor(0.07, 0.07, 0.06, 1.0)

    batch = pyglet.graphics.Batch()
    canvas_batch = pyglet.graphics.Batch()

    header = pyglet.text.Label(
        "",
        x=20,
        y=WINDOW_H - 30,
        font_size=14,
        color=(255, 255, 255, 255),
        batch=batch,
    )

    status = pyglet.text.Label(
        "",
        x=20,
        y=WINDOW_H - 55,
        font_size=10,
        color=(190, 190, 190, 255),
        batch=batch,
    )

    event_labels = []
    for i in range(EVENT_LINES):
        event_labels.append(
            pyglet.text.Label(
                "",
                x=20,
                y=WINDOW_H - 90 - i * 17,
                font_size=10,
                color=(220, 220, 220, 255),
                batch=batch,
            )
        )

    detail_labels = []
    for i in range(DETAIL_LINES):
        detail_labels.append(
            pyglet.text.Label(
                "",
                x=430,
                y=WINDOW_H - 90 - i * 17,
                font_size=10,
                color=(220, 220, 220, 255),
                batch=batch,
            )
        )

    canvas_shapes = []
    canvas_labels = []
    for _ in range(180):
        canvas_labels.append(
            pyglet.text.Label(
                "",
                x=0,
                y=0,
                font_size=8,
                color=(220, 220, 220, 255),
                batch=canvas_batch,
            )
        )

    canvas_state = {"label_i": 0}

    state = {
        "i": 0,
        "top": 0,
        "playing": False,
    }

    def clear_canvas():
        while canvas_shapes:
            obj = canvas_shapes.pop()
            try:
                obj.delete()
            except Exception:
                pass

        canvas_state["label_i"] = 0

    def canvas_text(
        x,
        y,
        s,
        size=8,
        color=(220, 220, 220, 255),
        anchor_x="center",
        anchor_y="center",
    ):
        i = canvas_state["label_i"]
        if i >= len(canvas_labels):
            return

        lbl = canvas_labels[i]
        lbl.text = _short(str(s), 90)
        lbl.x = x
        lbl.y = y
        lbl.font_size = size
        lbl.color = color
        lbl.anchor_x = anchor_x
        lbl.anchor_y = anchor_y

        canvas_state["label_i"] += 1

    def make_line(x1, y1, x2, y2, color, width=1.0):
        try:
            line = shapes.Line(
                x1,
                y1,
                x2,
                y2,
                width=width,
                color=color,
                batch=canvas_batch,
            )
        except TypeError:
            line = shapes.Line(
                x1,
                y1,
                x2,
                y2,
                thickness=width,
                color=color,
                batch=canvas_batch,
            )

        canvas_shapes.append(line)
        return line

    def render_folding_vm(e):
        def draw_cells(cells, y, changed=()):
            n = len(cells)

            if n == 0:
                canvas_text(CANVAS_X + 30, y + 20, "(empty)", anchor_x="left")
                return

            visible = min(n, 16)
            cell_w = min(56, max(26, (CANVAS_W - 60) // max(visible, 1) - 6))

            for i, c in enumerate(cells[:visible]):
                x = CANVAS_X + 30 + i * (cell_w + 6)

                color = (58, 58, 54)

                if i in changed:
                    color = (126, 50, 40)
                elif c.get("portal"):
                    color = (140, 110, 30)
                elif len(c.get("members", [])) > 1:
                    color = (38, 86, 96)

                rect = shapes.Rectangle(
                    x,
                    y,
                    x + cell_w,
                    y + 42,
                    color=color,
                    batch=canvas_batch,
                )
                canvas_shapes.append(rect)

                canvas_text(
                    x + cell_w / 2,
                    y + 28,
                    str(c.get("value", "?")),
                    size=10,
                    color=(255, 255, 255, 255),
                )

                members = c.get("members", [])
                if len(members) > 1 or c.get("portal"):
                    canvas_text(
                        x + cell_w / 2,
                        y + 11,
                        ",".join(str(m) for m in members),
                        size=6,
                    )

            if n > visible:
                canvas_text(
                    CANVAS_X + 30 + visible * (cell_w + 6) + 10,
                    y + 20,
                    f"+{n - visible}",
                    anchor_x="left",
                )

        before = e.before.get("cells", [])
        after = e.after.get("cells", [])
        changed = set(e.meta.get("changed", []))

        canvas_text(CANVAS_X + 20, CANVAS_Y + CANVAS_H - 18, "before", anchor_x="left")
        draw_cells(before, CANVAS_Y + CANVAS_H - 78)

        canvas_text(CANVAS_X + 20, CANVAS_Y + 72, "after", anchor_x="left")
        draw_cells(after, CANVAS_Y + 18, changed)

    def render_root_grid(e, get_pos):
        cell = 20
        origin_x = CANVAS_X + 60
        origin_y = CANVAS_Y + 30

        for x in range(1, 10):
            for y in range(1, 10):
                sx = origin_x + (x - 1) * cell
                sy = origin_y + (y - 1) * cell

                color = (70, 60, 30) if x == y else (38, 38, 36)

                rect = shapes.Rectangle(
                    sx + 1,
                    sy + 1,
                    sx + cell - 1,
                    sy + cell - 1,
                    color=color,
                    batch=canvas_batch,
                )
                canvas_shapes.append(rect)

        def mark(pos, color, label=None):
            if not pos:
                return

            x, y = pos

            if not (1 <= x <= 9 and 1 <= y <= 9):
                return

            sx = origin_x + (x - 1) * cell
            sy = origin_y + (y - 1) * cell

            circ = shapes.Circle(
                sx + cell / 2,
                sy + cell / 2,
                6,
                color=color,
                batch=canvas_batch,
            )
            canvas_shapes.append(circ)

            if label:
                canvas_text(sx + cell / 2, sy + cell + 8, label, size=7)

        before = get_pos(e.before)
        after = get_pos(e.after)

        mark(before, (130, 130, 130), "before")
        mark(after, (240, 205, 90), "after")

    def _test_walk_pos(state):
        x = state.get("x_root")
        y = state.get("y_root")

        if x is None or y is None:
            return None

        return (int(x), int(y))

    def _pathfinding_pos(state):
        pos = state.get("pos")
        if not pos or len(pos) < 2:
            return None

        return (int(pos[0]), int(pos[1]))

    def render_triangle(e):
        order = ["F", "G", "E", "D", "C", "B", "A"]
        current = e.after.get("letter")

        cx = CANVAS_X + CANVAS_W // 2
        cy = CANVAS_Y + CANVAS_H // 2
        rx = min(230, CANVAS_W // 2 - 60)
        ry = 85

        pos = {}

        for i, L in enumerate(order):
            angle = -math.pi / 2 + 2 * math.pi * i / len(order)
            px = cx + math.cos(angle) * rx
            py = cy + math.sin(angle) * ry
            pos[L] = (px, py)

        for i in range(len(order)):
            a = pos[order[i]]
            b = pos[order[(i + 1) % len(order)]]
            make_line(a[0], a[1], b[0], b[1], (70, 70, 65), width=1.0)

        for L, (px, py) in pos.items():
            color = (240, 205, 90) if L == current else (70, 70, 65)

            circ = shapes.Circle(px, py, 14, color=color, batch=canvas_batch)
            canvas_shapes.append(circ)

            canvas_text(px, py, L, size=10, color=(20, 20, 20, 255))

    def render_flexagon(e):
        packet = e.after.get("packet", [])
        n = len(packet)

        if n == 0:
            canvas_text(CANVAS_X + 30, CANVAS_Y + CANVAS_H // 2, "(empty packet)")
            return

        slot_w = min(68, max(36, (CANVAS_W - 80) // max(n, 1) - 8))

        for i, s in enumerate(packet):
            x = CANVAS_X + 40 + i * (slot_w + 8)

            top_y = CANVAS_Y + CANVAS_H - 95
            bottom_y = CANVAS_Y + 55

            top_color = (50, 80, 95)
            bottom_color = (95, 60, 50)

            if i == 0:
                top_color = (120, 95, 35)
                bottom_color = (120, 95, 35)

            top = shapes.Rectangle(
                x,
                top_y,
                x + slot_w,
                top_y + 42,
                color=top_color,
                batch=canvas_batch,
            )
            canvas_shapes.append(top)

            bottom = shapes.Rectangle(
                x,
                bottom_y,
                x + slot_w,
                bottom_y + 42,
                color=bottom_color,
                batch=canvas_batch,
            )
            canvas_shapes.append(bottom)

            canvas_text(x + slot_w / 2, top_y + 21, s.get("front", "?"), size=10)
            canvas_text(x + slot_w / 2, bottom_y + 21, s.get("back", "?"), size=10)
            canvas_text(x + slot_w / 2, CANVAS_Y + 25, str(i), size=7)

    def render_category(e):
        a = e.before.get("root")
        b = e.after.get("root")

        y = CANVAS_Y + CANVAS_H // 2
        xs = {}

        for r in range(1, 10):
            x = CANVAS_X + 60 + (r - 1) * (CANVAS_W - 120) // 8
            xs[r] = x

            circ = shapes.Circle(x, y, 10, color=(70, 70, 65), batch=canvas_batch)
            canvas_shapes.append(circ)

            canvas_text(x, y - 20, str(r), size=8)

        if a is not None and b is not None:
            a = int(a)
            b = int(b)

            if a in xs and b in xs:
                make_line(xs[a], y, xs[b], y, (240, 205, 90), width=2.0)

                ca = shapes.Circle(
                    xs[a], y, 12, color=(90, 160, 220), batch=canvas_batch
                )
                cb = shapes.Circle(
                    xs[b], y, 12, color=(220, 120, 90), batch=canvas_batch
                )

                canvas_shapes.append(ca)
                canvas_shapes.append(cb)

        letter = ""
        if "[" in e.path:
            letter = e.path.split("[")[-1].rstrip("]")

        canvas_text(
            CANVAS_X + 30,
            CANVAS_Y + CANVAS_H - 20,
            f"component {letter}",
            anchor_x="left",
        )

    def render_three_body(e):
        positions = e.after.get("positions")

        cx = CANVAS_X + CANVAS_W // 2
        cy = CANVAS_Y + CANVAS_H // 2
        scale = 85

        colors = [
            (90, 160, 220),
            (220, 120, 90),
            (240, 205, 90),
        ]

        if not positions:
            canvas_text(cx, cy, "(no positions)")
            return

        for i, p in enumerate(positions[:3]):
            px = cx + float(p[0]) * scale
            py = cy + float(p[1]) * scale

            circ = shapes.Circle(px, py, 7, color=colors[i % 3], batch=canvas_batch)
            canvas_shapes.append(circ)

    def render_fold_complexity(e):
        fc = e.after.get("fc")

        if fc is None:
            canvas_text(CANVAS_X + 30, CANVAS_Y + CANVAS_H // 2, "(no FC value)")
            return

        fc = float(fc)

        x = CANVAS_X + 60
        y = CANVAS_Y + CANVAS_H // 2 - 20
        w = CANVAS_W - 120

        bg = shapes.Rectangle(
            x, y, x + w, y + 26, color=(45, 45, 42), batch=canvas_batch
        )
        canvas_shapes.append(bg)

        fill = shapes.Rectangle(
            x,
            y,
            x + int(w * min(1.0, fc)),
            y + 26,
            color=(212, 167, 44),
            batch=canvas_batch,
        )
        canvas_shapes.append(fill)

        canvas_text(x, y + 42, f"FC = {fc:.3f}", anchor_x="left")

    def render_canvas(e):
        border = shapes.Rectangle(
            CANVAS_X,
            CANVAS_Y,
            CANVAS_X + CANVAS_W,
            CANVAS_Y + CANVAS_H,
            color=(30, 30, 28),
            batch=canvas_batch,
        )
        canvas_shapes.append(border)

        source = trace.source

        if source == "folding_vm":
            render_folding_vm(e)

        elif source == "test_walk":
            render_root_grid(e, _test_walk_pos)

        elif source == "pathfinding":
            render_root_grid(e, _pathfinding_pos)

        elif source == "triangle_state_machine":
            render_triangle(e)

        elif source == "flexagon":
            render_flexagon(e)

        elif source == "category_theory":
            render_category(e)

        elif source == "three_body":
            render_three_body(e)

        elif source == "fold_complexity":
            render_fold_complexity(e)

        else:
            canvas_text(
                CANVAS_X + 30,
                CANVAS_Y + CANVAS_H // 2,
                f"{e.kind} {e.path}",
                anchor_x="left",
            )

    def update():
        idx = state["i"]
        e = trace.events[idx]

        header.text = _short(f"{title or trace.title}  [{trace.source}]", 110)

        mode = "playing" if state["playing"] else "paused"
        status.text = _short(
            f"step {idx + 1}/{len(trace.events)} | {e.kind} | {mode} | "
            "LEFT/RIGHT step | SPACE play | HOME/END jump | Q quit",
            150,
        )

        top = state["top"]

        if idx < top:
            top = idx

        if idx >= top + EVENT_LINES:
            top = idx - EVENT_LINES + 1

        top = max(0, min(top, max(0, len(trace.events) - EVENT_LINES)))
        state["top"] = top

        for j, lbl in enumerate(event_labels):
            k = top + j

            if k < len(trace.events):
                ev = trace.events[k]
                marker = ">" if k == idx else " "
                lbl.text = _short(f"{marker}{ev.step:4d} {ev.kind:<16} {ev.path}", 70)
                lbl.color = (255, 220, 120, 255) if k == idx else (210, 210, 210, 255)
            else:
                lbl.text = ""

        lines: List[str] = []

        lines.append(f"kind: {e.kind}")
        lines.append(f"path: {e.path}")

        if e.t is not None:
            lines.append(f"t: {e.t}")

        if e.meta:
            _add_mapping_lines(lines, "meta:", e.meta)

        _add_mapping_lines(lines, "before:", e.before)
        _add_mapping_lines(lines, "after:", e.after)

        for j, lbl in enumerate(detail_labels):
            lbl.text = _short(lines[j], 96) if j < len(lines) else ""

        clear_canvas()
        render_canvas(e)

        for j in range(canvas_state["label_i"], len(canvas_labels)):
            canvas_labels[j].text = ""

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.RIGHT:
            state["i"] = min(len(trace.events) - 1, state["i"] + 1)
            update()

        elif symbol == key.LEFT:
            state["i"] = max(0, state["i"] - 1)
            update()

        elif symbol == key.SPACE:
            state["playing"] = not state["playing"]
            update()

        elif symbol == key.HOME:
            state["i"] = 0
            update()

        elif symbol == key.END:
            state["i"] = len(trace.events) - 1
            update()

        elif symbol in (key.Q, key.ESCAPE):
            window.close()

    def tick(dt):
        if state["playing"]:
            if state["i"] < len(trace.events) - 1:
                state["i"] += 1
                update()
            else:
                state["playing"] = False
                update()

    pyglet.clock.schedule_interval(tick, step_interval)

    @window.event
    def on_draw():
        window.clear()
        batch.draw()
        canvas_batch.draw()

    update()
    pyglet.app.run()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python lab_inspector.py <trace.json>")
        raise SystemExit(1)

    trace = LabTrace.load(sys.argv[1])
    show_lab_trace(trace)
