from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from legacy.flat_modules.general_recursive_mapper import RecursiveMapper

LETTER_TO_ROOT: Dict[str, int] = {
    "D": 9,
    "E": 7,
    "F": 6,
    "C": 8,
    "B": 5,
    "A": 3,
    "G": 6,  # drawn as 6(9) -- see PORTAL_LETTERS
}

PORTAL_LETTERS: Dict[str, Tuple[int, int]] = {"G": (6, 9)}

# Context-sensitive portal resolution (T2): in a D-aligned context G acts as 9.
PORTAL_CONTEXTS: Dict[str, Dict[str, int]] = {"G": {"D": 9}}

UNNAMED_ROOTS = (1, 2, 4)


def root_to_letters(root: int) -> List[str]:
    letters = [l for l, r in LETTER_TO_ROOT.items() if r == root]
    for letter, (a, b) in PORTAL_LETTERS.items():
        if root in (a, b) and letter not in letters:
            letters.append(letter)
    return letters


def letter_to_root(letter: str) -> int:
    if letter not in LETTER_TO_ROOT:
        raise KeyError(f"'{letter}' is not in the drawing's letter table")
    return LETTER_TO_ROOT[letter]


def resolve_letter_root(letter: str, context: Optional[str] = None) -> int:
    if letter in PORTAL_CONTEXTS and context in PORTAL_CONTEXTS[letter]:
        return PORTAL_CONTEXTS[letter][context]
    return LETTER_TO_ROOT[letter]


class NamedMapper:
    def __init__(self):
        self.mapper = RecursiveMapper(radix=9, multiplier=2)

    def advance(self, letter: str, steps: int = 1) -> List[str]:
        return root_to_letters(
            self.mapper.topology.advance(letter_to_root(letter), steps)
        )

    def retreat(self, letter: str, steps: int = 1) -> List[str]:
        return root_to_letters(
            self.mapper.topology.retreat(letter_to_root(letter), steps)
        )

    def is_portal(self, letter: str) -> bool:
        return letter in PORTAL_LETTERS


def _run_self_tests():
    nm = NamedMapper()
    for letter, root in LETTER_TO_ROOT.items():
        assert letter in root_to_letters(root)
    assert nm.is_portal("G") and not nm.is_portal("D")
    assert set(PORTAL_LETTERS["G"]) == {6, 9}
    assert resolve_letter_root("G") == 6
    assert resolve_letter_root("G", "D") == 9
    assert nm.advance("C", 2) == root_to_letters(5)
    assert nm.retreat("B", 2) == root_to_letters(8)
    assert nm.advance("D", 1) == root_to_letters(3)
    assert nm.advance("D", 3) == root_to_letters(9)
    print("All named-aliases self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    nm = NamedMapper()
    print("Letter table:", LETTER_TO_ROOT)
    print("Portal letters:", PORTAL_LETTERS)
    print("Portal contexts:", PORTAL_CONTEXTS)
    print("Unnamed roots:", UNNAMED_ROOTS)
    for letter in ("A", "B", "C", "D", "E", "F", "G"):
        print(
            f"{letter} (root {letter_to_root(letter)}): "
            f"+1 -> {nm.advance(letter)}   -1 -> {nm.retreat(letter)}"
        )
