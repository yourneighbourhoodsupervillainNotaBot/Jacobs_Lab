from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
from legacy.flat_modules.recursive_lattice import RecursiveLattice
from legacy.flat_modules.Level_tree import TreeNode, flatten
from legacy.flat_modules.test_harness import TestResult

# PASS advances the X axis (RIGHT / double), FAIL advances the Y axis
# (UP / half) -- reusing RecursiveLattice's existing two directions rather
# than inventing a third meaning for a test outcome. A run with zero
# failures (as the real lab currently has) never touches the Y axis at all,
# which is itself an honest signal: nothing to hide, no failures to visit.
MOVE_FOR = {True: "RIGHT", False: "UP"}


def build_test_tree(
    results: List[TestResult],
    lattice: RecursiveLattice = None,
    start_x: int = 1,
    start_y: int = 1,
) -> Tuple[TreeNode, Dict[int, TestResult]]:
    """
    Builds a genuine Level_tree.TreeNode chain: child[0] at each node is the
    move the test suite actually took (PASS->RIGHT, FAIL->UP), continuing
    the chain; child[1], when present, is the untaken alternative, added as
    a childless leaf -- a 'branch preview' stub, not a road walked. This
    reuses TreeNode exactly as build_level_tree/build_triangle_state_path
    do, rather than a parallel structure.

    Returns (root, result_by_depth) -- test outcomes are kept in a side
    dict rather than overloading TreeNode's triangle_state/state_action
    fields, which mean something different (they belong to the OTHER
    visualization, the triangle-state-machine walk).
    """
    lattice = lattice or RecursiveLattice(radix=9, x_multiplier=2)
    root = TreeNode(start_x, start_y, 0, None, portal=(start_x == start_y))
    result_by_depth: Dict[int, TestResult] = {}
    current = root
    x, y = start_x, start_y
    for i, r in enumerate(results, start=1):
        taken_move = MOVE_FOR[r.passed]
        other_move = "UP" if taken_move == "RIGHT" else "RIGHT"
        tx, ty = lattice.move(x, y, taken_move)
        ox, oy = lattice.move(x, y, other_move)

        taken_node = TreeNode(tx, ty, i, taken_move, portal=(tx == ty))
        preview_node = TreeNode(
            ox, oy, i, other_move, portal=(ox == oy)
        )  # leaf, no children

        current.children.append(taken_node)
        current.children.append(preview_node)
        result_by_depth[i] = r

        current, x, y = taken_node, tx, ty
    return root, result_by_depth


def taken_path(root: TreeNode) -> List[TreeNode]:
    """The actual walked chain: at each node, child[0] (if present)."""
    path = [root]
    node = root
    while node.children:
        node = node.children[0]
        path.append(node)
    return path


# ----------------------------------------------------------------------
# Layout: positions every node needs on screen (or canvas), independent of
# whether the renderer is matplotlib or pyglet. This is the one function
# both renderers call, so 'does the shape look right' only needs checking
# once, with a tool that doesn't need a display.
# ----------------------------------------------------------------------


@dataclass
class LayoutNode:
    node: TreeNode
    x: float
    y: float
    is_preview: bool  # True for an untaken-branch stub, False for the real path


def layout_test_tree(
    root: TreeNode, x_spacing: float = 90.0, y_jitter_amplitude: float = 22.0
) -> List[LayoutNode]:
    """
    Deterministic left-to-right spine layout for the taken path (depth
    drives x; the taken move nudges y so runs of the same move visibly
    drift and a change of move visibly kinks), plus each preview stub
    placed as a short offshoot near its parent -- readable without a
    legend: the spine is the story, the stubs are 'what didn't happen'.
    """
    out = []
    y_by_node = {id(root): 0.0}
    path = taken_path(root)
    for i, n in enumerate(path):
        y_by_node[id(n)] = y_by_node.get(id(n), 0.0)
        out.append(LayoutNode(n, x=i * x_spacing, y=y_by_node[id(n)], is_preview=False))
        if n.children:
            taken, preview = n.children[0], n.children[1]
            dy = (
                y_jitter_amplitude if taken.move == "UP" else -y_jitter_amplitude * 0.15
            )
            y_by_node[id(taken)] = y_by_node[id(n)] + dy
            # Preview stub: offset perpendicular to the spine's local direction.
            preview_dy = (
                -y_jitter_amplitude * 1.4
                if preview.move == "UP"
                else y_jitter_amplitude * 1.4
            )
            out.append(
                LayoutNode(
                    preview,
                    x=i * x_spacing + x_spacing * 0.5,
                    y=y_by_node[id(n)] + preview_dy,
                    is_preview=True,
                )
            )
    return out


def _run_self_tests():
    def mk(name, passed):
        return TestResult(name, passed, 0.001, None if passed else "boom")

    # Synthetic mixed pass/fail sequence so both branch colors are exercised.
    results = [mk("a", True), mk("b", True), mk("c", False), mk("d", True)]
    lattice = RecursiveLattice(radix=9, x_multiplier=2)
    root, result_by_depth = build_test_tree(results, lattice, start_x=1, start_y=1)

    assert root.depth == 0 and root.move is None and root.x_root == root.y_root == 1
    assert len(result_by_depth) == 4
    assert result_by_depth[3].passed is False  # test 'c' failed

    path = taken_path(root)
    assert len(path) == 5  # root + 4 tests

    # Manually recompute the expected taken path and check it matches exactly.
    x, y = 1, 1
    for n, r in zip(path[1:], results):
        expected_move = MOVE_FOR[r.passed]
        ex, ey = lattice.move(x, y, expected_move)
        assert n.move == expected_move
        assert (n.x_root, n.y_root) == (ex, ey)
        x, y = ex, ey

    # Every non-leaf node on the path has exactly one taken child and one
    # preview (untaken) child, and they genuinely differ.
    for n in path[:-1]:
        assert len(n.children) == 2
        taken, preview = n.children
        assert taken.move != preview.move
        assert (taken.x_root, taken.y_root) != (preview.x_root, preview.y_root)

    laid_out = layout_test_tree(root)
    # spine nodes (5) + preview stubs (4, one per non-leaf spine node) = 9
    assert len(laid_out) == 9
    assert sum(1 for ln in laid_out if not ln.is_preview) == 5
    assert sum(1 for ln in laid_out if ln.is_preview) == 4

    print("All test-walk-engine self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
