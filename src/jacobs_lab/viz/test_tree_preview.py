from __future__ import annotations
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from jacobs_lab.testing.test_harness import run_all_tests
from jacobs_lab.testing.test_walk_engine import build_test_tree, taken_path, layout_test_tree

TEAL = "#2f9e8f"
CORAL = "#d97757"
AMBER = "#d4a72c"
GRAY = "#9a978f"


def render_preview(results, path_out="test_tree_preview.png"):
    root, result_by_depth = build_test_tree(results, start_x=1, start_y=1)
    laid_out = layout_test_tree(root)
    path_nodes = {id(n) for n in taken_path(root)}

    fig, ax = plt.subplots(figsize=(16, 5))
    pos = {id(ln.node): (ln.x, ln.y) for ln in laid_out}

    # Edges: spine (solid) and preview stubs (dashed, faint)
    for ln in laid_out:
        n = ln.node
        if n.move is None:
            continue
        parent_pos = None
        for other in laid_out:
            if other.node is not n and any(c is n for c in other.node.children):
                parent_pos = (other.x, other.y)
                break
        if parent_pos is None:
            continue
        is_spine = id(n) in path_nodes
        ax.plot(
            [parent_pos[0], ln.x],
            [parent_pos[1], ln.y],
            color=(TEAL if n.move == "RIGHT" else CORAL) if is_spine else GRAY,
            linewidth=2.2 if is_spine else 1.0,
            linestyle="-" if is_spine else "--",
            alpha=1.0 if is_spine else 0.5,
            zorder=1,
        )

    # Nodes
    for ln in laid_out:
        n = ln.node
        is_spine = id(n) in path_nodes
        r = result_by_depth.get(n.depth) if is_spine and n.depth > 0 else None
        if n.portal:
            color = AMBER
        elif not is_spine:
            color = GRAY
        elif r is not None and not r.passed:
            color = "#c0392b"
        else:
            color = TEAL if n.move == "RIGHT" else CORAL
        size = 90 if is_spine else 35
        ax.scatter(
            [ln.x],
            [ln.y],
            s=size,
            color=color,
            alpha=1.0 if is_spine else 0.55,
            zorder=2,
            edgecolors="black" if is_spine else "none",
            linewidths=0.6,
        )
        if is_spine and n.depth > 0 and r is not None:
            ax.annotate(
                r.module,
                (ln.x, ln.y),
                textcoords="offset points",
                xytext=(0, 10 if n.move == "RIGHT" else -14),
                fontsize=6,
                rotation=60,
                ha="left",
                color=("#c0392b" if not r.passed else "#333333"),
            )

    ax.set_title(
        "Test suite walk through the recursive lattice "
        "(spine = actual path, dashed = untaken branch, gold = portal)"
    )
    ax.set_yticks([])
    ax.set_xlabel("test index (left to right)")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    plt.savefig(path_out, dpi=150)
    plt.close(fig)
    return path_out


if __name__ == "__main__":
    results = run_all_tests()
    out = render_preview(results)
    print(f"Wrote preview to {out}")
