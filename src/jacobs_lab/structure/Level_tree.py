from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from jacobs_lab.core.recursive_lattice import RecursiveLattice
from jacobs_lab.structure.triangle_state_machine import TriangleStateMachine


@dataclass
class TreeNode:
    x_root: int
    y_root: int
    depth: int
    move: Optional[str]
    portal: bool
    children: List["TreeNode"] = field(default_factory=list)
    triangle_state: Optional[str] = None
    state_action: Optional[str] = None

    def count_nodes(self) -> int:
        return 1 + sum(c.count_nodes() for c in self.children)

    def count_portals(self) -> int:
        return (1 if self.portal else 0) + sum(c.count_portals() for c in self.children)


def build_level_tree(
    lattice: RecursiveLattice, start_x: int, start_y: int, depth: int
) -> TreeNode:
    def node(x: int, y: int, d: int, move: Optional[str]) -> TreeNode:
        n = TreeNode(x, y, d, move, portal=(x == y))
        if d < depth:
            rx, ry = lattice.move(x, y, "RIGHT")
            ux, uy = lattice.move(x, y, "UP")
            n.children.append(node(rx, ry, d + 1, "RIGHT"))
            n.children.append(node(ux, uy, d + 1, "UP"))
        return n

    return node(start_x, start_y, 0, None)


def build_triangle_state_path(
    machine: Optional[TriangleStateMachine] = None,
    start_state: str = "A",
    steps: int = 7,
) -> TreeNode:
    """Linear tree projecting the state-machine loop into TreeNode form."""
    if machine is None:
        machine = TriangleStateMachine()
    start = machine.state(start_state)
    root = TreeNode(start.root, start.root, 0, None, True, [], start_state, None)
    current_letter, current_node = start_state, root
    for i in range(steps):
        t = machine.transition(current_letter)
        cur, nxt = machine.state(current_letter), machine.state(t.dst)
        child = TreeNode(
            cur.root,
            nxt.root,
            i + 1,
            t.action,
            cur.root == nxt.root,
            [],
            t.dst,
            t.action,
        )
        current_node.children.append(child)
        current_node, current_letter = child, t.dst
    return root


def flatten(root: TreeNode) -> List[TreeNode]:
    out = [root]
    for c in root.children:
        out.extend(flatten(c))
    return out


def _run_self_tests():
    lat = RecursiveLattice(radix=9, x_multiplier=2)
    tree = build_level_tree(lat, start_x=1, start_y=1, depth=3)
    assert tree.count_nodes() == 15
    assert tree.portal and tree.x_root == tree.y_root == 1
    leaves = [n for n in flatten(tree) if not n.children]
    assert len(leaves) == 8 and all(n.depth == 3 for n in leaves)
    for n in flatten(tree):
        for child in n.children:
            assert (child.x_root, child.y_root) == lat.move(
                n.x_root, n.y_root, child.move
            )

    path = build_triangle_state_path(steps=7)
    nodes = flatten(path)
    assert len(nodes) == 8
    assert [n.triangle_state for n in nodes] == ["A", "F", "G", "E", "D", "C", "B", "A"]
    assert all(len(n.children) <= 1 for n in nodes)
    print("All level-tree self-tests passed.")
    return tree


if __name__ == "__main__":
    tree = _run_self_tests()
    print(f"\nNodes: {tree.count_nodes()}, portals: {tree.count_portals()}")
    for n in flatten(tree):
        move = f"[{n.move}]  " if n.move else ""
        tag = "  <- portal" if n.portal else ""
        print(f"{'   ' * n.depth}{move}({n.x_root}, {n.y_root}){tag}")
    print("\nTriangle state path:")
    for n in flatten(build_triangle_state_path(steps=7)):
        move = f"[{n.move}]  " if n.move else ""
        tag = "  <- portal" if n.portal else ""
        print(
            f"{'   ' * n.depth}{move}({n.x_root} -> {n.y_root}) state={n.triangle_state}{tag}"
        )
