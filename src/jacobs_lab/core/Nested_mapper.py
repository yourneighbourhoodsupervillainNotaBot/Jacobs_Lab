from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from jacobs_lab.core.general_recursive_mapper import RecursiveMapper


@dataclass
class RecursiveNode:
    """Nested address chain; optional `meta` carries symbolic annotations
    (triangle state) without affecting equality or decoding."""

    level: int
    root: int
    child: Optional["RecursiveNode"] = None
    meta: Optional[dict] = None

    def __iter__(self):
        node = self
        while node is not None:
            yield node
            node = node.child

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, RecursiveNode):
            return NotImplemented
        a, b = list(self), list(other)
        return len(a) == len(b) and all(
            x.level == y.level and x.root == y.root for x, y in zip(a, b)
        )


class NestedMapper:
    """Reversible ND encoding: R' = T^-L(R); decode: R = T^L(R'), x = L*radix + R."""

    def __init__(self, radix: int = 9, multiplier: int = 2):
        self.mapper = RecursiveMapper(radix, multiplier)

    def encode(self, coordinates: Sequence[int]) -> Optional[RecursiveNode]:
        if not coordinates:
            return None
        topology = self.mapper.topology
        head = tail = None
        for x in coordinates:
            if x < 1:
                raise ValueError(f"coordinate components must be >= 1, got {x}")
            c = self.mapper.decode_num(x)
            node = RecursiveNode(c.level, topology.retreat(c.root, c.level), None)
            if head is None:
                head = node
            else:
                tail.child = node
            tail = node
        return head

    def decode(self, node: Optional[RecursiveNode]) -> Tuple[int, ...]:
        topology = self.mapper.topology
        out = []
        while node is not None:
            out.append(
                self.mapper.encode_num(
                    node.level, topology.advance(node.root, node.level)
                )
            )
            node = node.child
        return tuple(out)


def annotate_with_triangle_states(node, letters: Sequence[str], machine=None):
    """Attach triangle-state metadata per dimension (decode unchanged)."""
    if node is None:
        if letters:
            raise ValueError("cannot annotate a None node with non-empty letters")
        return None
    if machine is None:
        from jacobs_lab.structure.triangle_state_machine import TriangleStateMachine

        machine = TriangleStateMachine()
    nodes = list(node)
    if len(nodes) != len(letters):
        raise ValueError("letter sequence length must match node depth")
    for n, letter in zip(nodes, letters):
        s = machine.state(letter)
        n.meta = {
            "triangle_letter": s.letter,
            "triangle_root": s.root,
            "triangle_mode": s.mode.value,
            "triangle_ab": s.ab.value,
            "triangle_c": s.c.value,
            "triangle_bits": "/".join(s.bits),
        }
    return node


def _run_self_tests():
    import random

    nm = NestedMapper(radix=9, multiplier=2)
    for _ in range(200):
        d = random.randint(1, 12)
        coords = tuple(random.randint(1, 500) for _ in range(d))
        assert nm.decode(nm.encode(coords)) == coords
    assert nm.encode(()) is None
    assert len(nm.encode((1, 2, 3, 4, 5))) == 5
    for d in (1, 2, 3, 10, 100, 1000):
        coords = tuple(range(1, d + 1))
        assert nm.decode(nm.encode(coords)) == coords
    x = 137
    node = nm.encode((x,))
    c = nm.mapper.decode_num(x)
    assert node.level == c.level
    assert node.root == nm.mapper.topology.retreat(c.root, c.level)

    node3 = nm.encode((10, 20, 30))
    annotate_with_triangle_states(node3, ("A", "B", "C"))
    assert [n.meta["triangle_letter"] for n in node3] == ["A", "B", "C"]
    assert nm.decode(node3) == (10, 20, 30)
    assert node3 == nm.encode((10, 20, 30))  # equality ignores meta
    print("All nested-mapper self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    nm = NestedMapper()
    X = (123, 45, 6789)
    node = nm.encode(X)
    annotate_with_triangle_states(node, ("A", "B", "C"))
    print(f"\nX = {X}")
    n, depth = node, 0
    while n is not None:
        tag = f"  state={n.meta['triangle_letter']}" if n.meta else ""
        print(f"  {'  ' * depth}dim {depth + 1}: level={n.level}, root={n.root}{tag}")
        n, depth = n.child, depth + 1
    print("Decoded back:", nm.decode(node))
    assert nm.decode(node) == X
