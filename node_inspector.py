from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from recursive_lattice import RecursiveLattice
from Level_tree import TreeNode


@dataclass(frozen=True)
class CycleView:
    axis: str
    root: int
    pattern: int
    position: int
    cycle: Tuple[int, ...]
    prev_root: int
    next_root: int

    @property
    def name(self) -> str:
        if self.cycle == (1, 2, 4, 8, 7, 5):
            return "doubling"
        if self.cycle == (3, 6, 9):
            return "3-6-9"
        return f"cycle {self.pattern}"


@dataclass(frozen=True)
class NodeInspection:
    node: TreeNode
    parent: Optional[TreeNode]
    result: Optional[object]
    note: str
    x: CycleView
    y: CycleView
    changed_axis: Optional[str]
    transition_line: str
    portal: bool
    lines: List[str]


class NodeInspector:
    """Derives a readable/visual inspection object from a TreeNode."""

    def __init__(self, lattice: Optional[RecursiveLattice] = None):
        self.lattice = lattice or RecursiveLattice(radix=9, x_multiplier=2)

    def _cycle_view(self, axis: str, root: int) -> CycleView:
        topo = self.lattice.x_topology if axis == "X" else self.lattice.y_topology
        pattern = topo.pattern(root)
        cycle = topo.cycles[pattern]
        position = topo.position_by_root[root]
        return CycleView(
            axis=axis,
            root=root,
            pattern=pattern,
            position=position,
            cycle=cycle,
            prev_root=topo.retreat(root),
            next_root=topo.advance(root),
        )

    def inspect(
        self,
        node: TreeNode,
        parent: Optional[TreeNode] = None,
        result: Optional[object] = None,
        note: str = "",
    ) -> NodeInspection:
        x = self._cycle_view("X", node.x_root)
        y = self._cycle_view("Y", node.y_root)

        move = (node.move or "").strip()
        changed_axis: Optional[str] = None

        if move == "RIGHT" and parent is not None:
            changed_axis = "X"
            transition_line = (
                f"RIGHT: X {parent.x_root} -> {node.x_root} "
                f"(cycle {x.name}, pos {x.position + 1}/{len(x.cycle)}); "
                f"Y stays {node.y_root}"
            )
        elif move == "UP" and parent is not None:
            changed_axis = "Y"
            transition_line = (
                f"UP: Y {parent.y_root} -> {node.y_root} "
                f"(cycle {y.name}, pos {y.position + 1}/{len(y.cycle)}); "
                f"X stays {node.x_root}"
            )
        elif move:
            changed_axis = "X" if move == "RIGHT" else "Y"
            transition_line = f"move: {move}"
        else:
            transition_line = "root node"

        radix = self.lattice.radix

        lines: List[str] = []
        lines.append(f"depth: {node.depth}")
        lines.append(f"move: {move if move else 'root'}")
        lines.append(f"roots: X={node.x_root}, Y={node.y_root}")
        lines.append(f"portal: {'yes' if node.portal else 'no'}")
        lines.append(f"children: {len(node.children)}")
        lines.append(
            "encoded if level=depth: "
            f"X={node.depth * radix + node.x_root}, "
            f"Y={node.depth * radix + node.y_root}"
        )

        if note:
            lines.append(f"layer: {note}")

        if node.triangle_state:
            lines.append(f"triangle state: {node.triangle_state}")

        if node.state_action:
            lines.append(f"state action: {node.state_action}")

        if result is not None:
            module = getattr(result, "module", "?")
            passed = getattr(result, "passed", False)
            duration = getattr(result, "duration", None)
            error = getattr(result, "error", None)

            lines.append(f"test: {module}")
            lines.append(f"result: {'PASS' if passed else 'FAIL'}")

            if duration is not None:
                lines.append(f"duration: {duration * 1000:.1f} ms")

            if error:
                lines.append(f"error: {error}")

        lines.append(transition_line)
        lines.append(f"X cycle: {x.name}, prev {x.prev_root}, next {x.next_root}")
        lines.append(f"Y cycle: {y.name}, prev {y.prev_root}, next {y.next_root}")

        if parent is not None:
            lines.append(
                f"parent: ({parent.x_root}, {parent.y_root}) depth {parent.depth}"
            )

        return NodeInspection(
            node=node,
            parent=parent,
            result=result,
            note=note,
            x=x,
            y=y,
            changed_axis=changed_axis,
            transition_line=transition_line,
            portal=node.portal,
            lines=lines,
        )


def _truncate(s: object, n: int = 62) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def draw_inspector(
    info: NodeInspection,
    batch,
    objects: List,
    window_w: int,
    window_h: int,
    panel_width: int = 390,
    margin: int = 16,
) -> None:
    """
    Draws an inspector panel into a pyglet batch.

    `objects` should be a list owned by the caller. The caller is responsible
    for deleting/clearing old inspector objects before calling this again.
    """
    try:
        from pyglet import shapes, text
    except ImportError:
        return

    panel_w = min(panel_width, max(260, window_w - 2 * margin - 420))
    panel_h = max(240, window_h - 2 * margin)
    panel_x = window_w - panel_w - margin
    panel_y = margin

    def keep(obj):
        objects.append(obj)
        return obj

    def add_line(x1, y1, x2, y2, color, width=1.0):
        try:
            line = shapes.Line(x1, y1, x2, y2, width=width, color=color, batch=batch)
        except TypeError:
            line = shapes.Line(
                x1, y1, x2, y2, thickness=width, color=color, batch=batch
            )
        keep(line)
        return line

    bg = shapes.Rectangle(
        panel_x,
        panel_y,
        panel_x + panel_w,
        panel_y + panel_h,
        color=(26, 26, 24),
        batch=batch,
    )
    if hasattr(bg, "opacity"):
        bg.opacity = 235
    keep(bg)

    y_cursor = [panel_y + panel_h - 18]

    def add_label(
        s,
        x=None,
        y=None,
        font_size=10,
        color=(230, 230, 230, 255),
        anchor_x="left",
        anchor_y="top",
        bold=False,
        advance=True,
        line_spacing=6,
    ):
        if y is None:
            y = y_cursor[0]

        label_kwargs = dict(
            x=x if x is not None else panel_x + 12,
            y=y,
            font_size=font_size,
            color=color,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            batch=batch,
        )

        try:
            lbl = text.Label(_truncate(s), bold=bold, **label_kwargs)
        except TypeError:
            # Some pyglet versions do not support bold= on Label.
            lbl = text.Label(_truncate(s), **label_kwargs)

        keep(lbl)

        if advance:
            y_cursor[0] = y - (font_size + line_spacing)

        return lbl

        if advance:
            y_cursor[0] = y - (font_size + line_spacing)

        return lbl

    add_label(
        "Node Inspector",
        font_size=14,
        color=(255, 255, 255, 255),
        bold=True,
    )

    if info.portal:
        add_label(
            "PORTAL: x == y",
            font_size=10,
            color=(240, 205, 90, 255),
            bold=True,
        )

    add_label(
        info.transition_line,
        font_size=10,
        color=(170, 210, 255, 255),
    )

    def draw_cycle_dial(
        view: CycleView,
        cx: int,
        cy: int,
        radius: int,
        changed: bool = False,
    ):
        base_color = (90, 160, 220) if view.axis == "X" else (220, 120, 90)
        active_color = (240, 205, 90) if changed else base_color

        ring = shapes.Circle(cx, cy, radius + 16, color=(38, 38, 34), batch=batch)
        if hasattr(ring, "opacity"):
            ring.opacity = 170
        keep(ring)

        n = len(view.cycle)
        pts = []

        for i, root in enumerate(view.cycle):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            pts.append((px, py))

            current = i == view.position
            prev = root == view.prev_root and not current

            if current:
                col = active_color
                r = 9
            elif prev:
                col = (110, 180, 120)
                r = 6
            else:
                col = (150, 150, 145)
                r = 5

            dot = shapes.Circle(px, py, r, color=col, batch=batch)
            if hasattr(dot, "opacity"):
                dot.opacity = 255 if current else 180
            keep(dot)

            add_label(
                str(root),
                x=px,
                y=py + 12,
                font_size=8,
                color=(235, 235, 235, 255),
                anchor_x="center",
                anchor_y="bottom",
                advance=False,
            )

        prev_i = (view.position - 1) % n
        add_line(
            pts[prev_i][0],
            pts[prev_i][1],
            pts[view.position][0],
            pts[view.position][1],
            color=active_color,
            width=2.0,
        )

        add_label(
            f"{view.axis}: {view.root} ({view.name})",
            x=cx,
            y=cy - radius - 24,
            font_size=10,
            color=active_color,
            anchor_x="center",
            advance=False,
        )

    radius = min(52, max(32, panel_w // 4 - 12))
    dial_y = y_cursor[0] - radius - 26

    draw_cycle_dial(
        info.x,
        panel_x + radius + 34,
        dial_y,
        radius,
        changed=info.changed_axis == "X",
    )

    draw_cycle_dial(
        info.y,
        panel_x + panel_w - radius - 34,
        dial_y,
        radius,
        changed=info.changed_axis == "Y",
    )

    y_cursor[0] = dial_y - radius - 30

    add_label(
        "Details",
        font_size=11,
        color=(200, 200, 200, 255),
        bold=True,
    )

    for line in info.lines:
        add_label(line, font_size=9)


def _run_self_tests():
    lat = RecursiveLattice(radix=9, x_multiplier=2)

    root = TreeNode(1, 1, 0, None, True)

    x, y = lat.move(1, 1, "RIGHT")
    child = TreeNode(x, y, 1, "RIGHT", False)
    root.children.append(child)

    insp = NodeInspector(lat)
    info = insp.inspect(child, root, None, "taken path")

    assert info.changed_axis == "X"
    assert info.x.root == x
    assert info.y.root == 1
    assert "RIGHT" in info.transition_line

    x2, y2 = lat.move(x, y, "UP")
    child2 = TreeNode(x2, y2, 2, "UP", x2 == y2)
    info2 = insp.inspect(child2, child, None, "taken path")

    assert info2.changed_axis == "Y"
    assert "UP" in info2.transition_line
    assert info2.portal == (x2 == y2)

    print("All node-inspector self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
