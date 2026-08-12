from __future__ import annotations

import argparse
from typing import List, Optional, Tuple

try:
    from jacobs_lab.computation.folding_computations import (
        Cell,
        Combine,
        FoldRecord,
        Instr,
        Pred,
        run_program_traced,
    )
except ImportError:
    try:
        from jacobs_lab.computation.folding_computations import (
            Cell,
            Combine,
            FoldRecord,
            Instr,
            Pred,
            run_program_traced,
        )
    except ImportError as exc:
        raise SystemExit(
            "fold_trace_inspector.py requires the run_program_traced() patch "
            "in folding_computations.py or folding_computation.py."
        ) from exc


def _short(s, n: int = 130) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def _cell_str(cell) -> str:
    mark = "*" if cell.portal else ""
    members = sorted(cell.members) if cell.members else []

    if len(members) == 1 and members[0] == cell.value and not cell.portal:
        return str(cell.value)

    mem = ",".join(str(m) for m in members)
    return f"{cell.value}{mark}{{{mem}}}"


def _cells_str(cells, max_cells: int = 18) -> str:
    if not cells:
        return "(empty)"

    parts = [_cell_str(c) for c in cells[:max_cells]]

    if len(cells) > max_cells:
        parts.append(f"... +{len(cells) - max_cells} more")

    return " ".join(parts)


def format_step(step) -> str:
    lines = []
    lines.append(f"#{step.index:>3} {step.op:<6} {step.path}")
    lines.append(f"     detail:  {_short(step.detail, 160)}")
    lines.append(f"     before:  {_cells_str(step.before)}")
    lines.append(f"     after:   {_cells_str(step.after)}")
    lines.append(f"     outputs: {list(step.outputs)}")

    if step.changed_cells:
        lines.append(f"     changed: {list(step.changed_cells)}")

    if step.branch_taken is not None:
        lines.append(f"     branch:  {step.branch_taken}")

    if step.record is not None:
        lines.append(
            f"     fold:    pivot={step.record.pivot} pairs={step.record.pairs}"
        )

    return "\n".join(lines)


def print_trace(trace, limit: Optional[int] = None) -> None:
    for i, step in enumerate(trace):
        if limit is not None and i >= limit:
            print(f"... {len(trace) - limit} more steps ...")
            break

        print(format_step(step))
        print()


# ----------------------------------------------------------------------
# Demos
# ----------------------------------------------------------------------
def demo_fold_branch_slide():
    """Fold the GFEABCD strip, detect the portal, READ it, SLIDE it."""
    values = [6, 6, 7, 3, 5, 8, 9]

    program = (
        Instr("FOLD", 3),
        Instr(
            "BRANCH",
            pred=Pred("is_portal", 0),
            then_prog=(Instr("READ", 0),),
            else_prog=(Instr("READ", 2),),
        ),
        Instr("SLIDE", 0, k=1),
        Instr("READ", 0),
    )

    return values, program


def demo_glue_sum():
    """Glue 3, 5, 8 by digital sum down to one cell."""
    values = [3, 5, 8]

    program = (
        Instr("GLUE", 0, Combine.DIGITAL_SUM),
        Instr("GLUE", 0, Combine.DIGITAL_SUM),
        Instr("READ", 0),
    )

    return values, program


def demo_while_slide():
    """SLIDE a level-encoded 3 up to 30 inside a WHILE loop."""
    values = [3]

    program = (
        Instr(
            "WHILE",
            pred=Pred("value_neq", 0, 30),
            body=(Instr("SLIDE", 0, k=1),),
        ),
        Instr("READ", 0),
    )

    return values, program


DEMOS = {
    "fold": demo_fold_branch_slide,
    "glue": demo_glue_sum,
    "while": demo_while_slide,
}


def run_demo(name: str):
    values, program = DEMOS[name]()
    cells, out, history, trace = run_program_traced(values, program)
    return trace, out


# ----------------------------------------------------------------------
# Visual inspector
# ----------------------------------------------------------------------
def show_trace(
    trace, title: str = "Folding computation trace", step_interval: float = 0.7
):
    import pyglet
    from pyglet import shapes
    from pyglet.window import key

    if not trace:
        print("Trace is empty.")
        return

    WINDOW_W, WINDOW_H = 1280, 680

    window = pyglet.window.Window(WINDOW_W, WINDOW_H, caption=title)
    pyglet.gl.glClearColor(0.09, 0.09, 0.08, 1.0)

    batch = pyglet.graphics.Batch()
    objects = []

    state = {
        "i": 0,
        "playing": False,
    }

    def clear():
        while objects:
            obj = objects.pop()
            try:
                obj.delete()
            except Exception:
                pass

    def label(
        text,
        x,
        y,
        size=11,
        color=(230, 230, 230, 255),
        anchor_x="left",
        anchor_y="top",
    ):
        lbl = pyglet.text.Label(
            _short(text, 150),
            x=x,
            y=y,
            font_size=size,
            color=color,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            batch=batch,
        )
        objects.append(lbl)

    def draw_strip(cells, y, name, changed=()):
        label(name, 30, y + 58, size=12, color=(200, 200, 200, 255))

        if not cells:
            label("(empty)", 30, y + 20)
            return

        max_visible = min(len(cells), 18)
        available = WINDOW_W - 80
        cell_w = min(64, max(32, (available // max(max_visible, 1)) - 8))
        gap = 8

        for i, c in enumerate(cells[:max_visible]):
            x = 40 + i * (cell_w + gap)

            if i in changed:
                color = (126, 50, 40)
            elif c.portal:
                color = (140, 110, 30)
            elif len(c.members) > 1:
                color = (38, 86, 96)
            else:
                color = (58, 58, 54)

            rect = shapes.Rectangle(
                x,
                y,
                x + cell_w,
                y + 54,
                color=color,
                batch=batch,
            )
            objects.append(rect)

            val_label = pyglet.text.Label(
                str(c.value),
                x=x + cell_w // 2,
                y=y + 36,
                font_size=13,
                color=(255, 255, 255, 255),
                anchor_x="center",
                anchor_y="center",
                batch=batch,
            )
            objects.append(val_label)

            if len(c.members) > 1 or c.portal:
                mem = ",".join(str(m) for m in sorted(c.members))
                mem_label = pyglet.text.Label(
                    mem,
                    x=x + cell_w // 2,
                    y=y + 14,
                    font_size=8,
                    color=(220, 220, 220, 255),
                    anchor_x="center",
                    anchor_y="center",
                    batch=batch,
                )
                objects.append(mem_label)

        if len(cells) > max_visible:
            label(
                f"+{len(cells) - max_visible} more",
                40 + max_visible * (cell_w + gap),
                y + 22,
            )

    def update():
        clear()

        idx = state["i"]
        step = trace[idx]

        label(
            f"{title}: step {idx + 1}/{len(trace)}",
            30,
            WINDOW_H - 30,
            size=15,
            color=(255, 255, 255, 255),
        )

        label(f"path: {step.path or 'root'}", 30, WINDOW_H - 58, size=11)
        label(f"op: {step.op}", 30, WINDOW_H - 78, size=11)
        label(f"detail: {step.detail}", 30, WINDOW_H - 98, size=11)
        label(f"outputs: {list(step.outputs)}", 30, WINDOW_H - 118, size=11)

        if step.branch_taken is not None:
            label(
                f"branch taken: {step.branch_taken}",
                420,
                WINDOW_H - 118,
                size=11,
                color=(170, 220, 255, 255),
            )

        if step.changed_cells:
            label(
                f"changed cells: {list(step.changed_cells)}",
                650,
                WINDOW_H - 118,
                size=11,
                color=(255, 180, 160, 255),
            )

        if step.record is not None:
            label(
                f"pivot: {step.record.pivot}  pairs: {step.record.pairs}",
                30,
                WINDOW_H - 138,
                size=11,
                color=(220, 200, 140, 255),
            )

        draw_strip(step.before, WINDOW_H - 260, "before")
        draw_strip(step.after, WINDOW_H - 400, "after", changed=set(step.changed_cells))

        mode = "playing" if state["playing"] else "paused"
        label(
            "LEFT/RIGHT step | SPACE play/pause | HOME/END jump | Q quit",
            30,
            30,
            size=10,
            color=(170, 170, 170, 255),
        )
        label(mode, WINDOW_W - 120, 30, size=10, color=(170, 220, 170, 255))

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.RIGHT:
            state["i"] = min(len(trace) - 1, state["i"] + 1)
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
            state["i"] = len(trace) - 1
            update()

        elif symbol == key.Q:
            window.close()

    def tick(dt):
        if state["playing"]:
            if state["i"] < len(trace) - 1:
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


# ----------------------------------------------------------------------
# Self-tests
# ----------------------------------------------------------------------
def _run_self_tests():
    trace, out = run_demo("glue")
    assert out == [7]
    assert any(s.op == "GLUE" for s in trace)

    trace, out = run_demo("fold")
    assert out[0] == 6
    assert out[-1] == 15
    assert any(s.op == "FOLD" for s in trace)
    assert any(s.op == "BRANCH" for s in trace)
    assert any(s.op == "SLIDE" for s in trace)

    trace, out = run_demo("while")
    assert out == [30]
    assert any(s.op == "WHILE" for s in trace)
    assert any(s.op == "SLIDE" for s in trace)

    print("All fold-trace-inspector self-tests passed.")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Inspector for folding_computations.py VM traces."
    )
    ap.add_argument(
        "--demo",
        choices=tuple(DEMOS.keys()),
        default="fold",
        help="Built-in demo program to trace.",
    )
    ap.add_argument(
        "--text",
        action="store_true",
        help="Print trace as text instead of opening the pyglet visual inspector.",
    )
    ap.add_argument(
        "--test",
        action="store_true",
        help="Run fold-trace-inspector self-tests.",
    )

    args = ap.parse_args(argv)

    if args.test:
        _run_self_tests()
        return

    trace, out = run_demo(args.demo)
    print(f"demo={args.demo} final outputs={out}")

    if args.text:
        print_trace(trace)
    else:
        try:
            show_trace(trace, title=f"Folding computation trace: {args.demo}")
        except ImportError:
            print("pyglet is not available; printing text trace instead.")
            print_trace(trace)
        except Exception as e:
            print(f"Could not open pyglet window ({e}); printing text trace instead.")
            print_trace(trace)


if __name__ == "__main__":
    main()
