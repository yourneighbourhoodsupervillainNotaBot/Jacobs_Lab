from __future__ import annotations

from typing import Optional, Tuple

from jacobs_lab.core.general_recursive_mapper import RecursiveTopology


class RecursiveLattice:
    """2D lattice over topology roots: RIGHT advances X, UP advances Y."""

    def __init__(
        self, radix: int = 9, x_multiplier: int = 2, y_multiplier: Optional[int] = None
    ):
        self.radix = radix
        self.x_topology = RecursiveTopology(radix, x_multiplier)
        self.y_topology = RecursiveTopology(radix, y_multiplier or x_multiplier)

    def move(self, x: int, y: int, direction: str) -> Tuple[int, int]:
        if direction == "RIGHT":
            return self.x_topology.advance(x), y
        if direction == "UP":
            return x, self.y_topology.advance(y)
        if direction == "LEFT":
            return self.x_topology.retreat(x), y
        if direction == "DOWN":
            return x, self.y_topology.retreat(y)
        raise ValueError("direction must be RIGHT, UP, LEFT, or DOWN")


def _run_self_tests():
    lat = RecursiveLattice(radix=9, x_multiplier=2)
    assert lat.move(1, 1, "RIGHT") == (2, 1)
    assert lat.move(1, 1, "UP") == (1, 2)
    assert lat.move(5, 1, "RIGHT") == (1, 1)
    assert lat.move(9, 9, "RIGHT") == (3, 9)
    assert lat.move(3, 3, "UP") == (3, 6)
    assert lat.move(6, 6, "UP") == (6, 9)
    assert lat.move(9, 9, "UP") == (9, 3)
    assert lat.move(3, 9, "UP") == (3, 3)
    assert lat.move(2, 1, "LEFT") == (1, 1)
    assert lat.move(1, 2, "DOWN") == (1, 1)
    assert lat.move(1, 1, "LEFT") == (5, 1)  # wrap-around retreat
    assert lat.move(1, 1, "DOWN") == (1, 5)
    for x in (1, 2, 5, 9):
        nx, ny = lat.move(x, 1, "RIGHT")
        assert lat.move(nx, ny, "LEFT") == (x, 1)

    print("All recursive-lattice self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
