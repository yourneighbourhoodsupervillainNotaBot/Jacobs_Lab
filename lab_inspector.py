from __future__ import annotations

import json
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
    from pyglet.window import key

    WINDOW_W, WINDOW_H = 1280, 720
    EVENT_LINES = 22
    DETAIL_LINES = 28

    window = pyglet.window.Window(
        WINDOW_W,
        WINDOW_H,
        caption=title or trace.title,
    )

    pyglet.gl.glClearColor(0.07, 0.07, 0.06, 1.0)

    batch = pyglet.graphics.Batch()

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
                y=WINDOW_H - 90 - i * 18,
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
                x=620,
                y=WINDOW_H - 90 - i * 18,
                font_size=10,
                color=(220, 220, 220, 255),
                batch=batch,
            )
        )

    state = {
        "i": 0,
        "top": 0,
        "playing": False,
    }

    def update():
        idx = state["i"]
        e = trace.events[idx]

        header.text = _short(f"{title or trace.title}  [{trace.source}]", 110)

        mode = "playing" if state["playing"] else "paused"
        status.text = _short(
            f"step {idx + 1}/{len(trace.events)} | {e.kind} | {mode} | "
            "LEFT/RIGHT step | SPACE play | HOME/END jump | Q quit",
            140,
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
                lbl.text = _short(
                    f"{marker}{ev.step:4d} {ev.kind:<16} {ev.path}",
                    72,
                )
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
            lbl.text = _short(lines[j], 100) if j < len(lines) else ""

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

    update()
    pyglet.app.run()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python lab_inspector.py <trace.json>")
        raise SystemExit(1)

    trace = LabTrace.load(sys.argv[1])
    show_lab_trace(trace)
