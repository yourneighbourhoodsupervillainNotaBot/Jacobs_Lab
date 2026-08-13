from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "jacobs_lab"
LEGACY = ROOT / "legacy" / "flat_modules"

REWRITES = [
    (
        "from general_recursive_mapper import",
        "from jacobs_lab.core.general_recursive_mapper import",
    ),
    ("from recursive_lattice import", "from jacobs_lab.core.recursive_lattice import"),
    ("from named_aliases import", "from jacobs_lab.core.named_aliases import"),
    (
        "from triangle_state_machine import",
        "from jacobs_lab.structure.triangle_state_machine import",
    ),
    (
        "from folding_computation import",
        "from jacobs_lab.computation.folding_computations import",
    ),
    (
        "from folding_computations import",
        "from jacobs_lab.computation.folding_computations import",
    ),
    (
        "from turing_universality import",
        "from jacobs_lab.computation.turing_universality import",
    ),
]


def rewrite(text: str) -> str:
    for old, new in REWRITES:
        text = text.replace(old, new)
    return text


def find_source(name: str):
    for base in (ROOT, LEGACY):
        p = base / name
        if p.is_file():
            return p
    return None


def restore(name: str, dest_rel: str) -> bool:
    src = find_source(name)
    dest = PKG / dest_rel
    if src is None:
        print(f"  ! source for {name} not found (root or legacy/flat_modules)")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rewrite(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"  restored {dest_rel} from {src.relative_to(ROOT)}")
    return True


def main():
    print("repairing package modules...")

    # 1) real modules clobbered by alias stubs -> restore full contents
    restore("Nested_mapper.py", "core/nested_mapper.py")
    restore("Level_tree.py", "structure/level_tree.py")

    # 2) addition_graph was never synced into the package
    restore("addition_graph.py", "core/addition_graph.py")

    # 3) complexity_lab sits in the wrong subpackage (or is absent)
    dest = PKG / "instruments" / "complexity_lab.py"
    if not dest.exists():
        found = [p for p in PKG.rglob("complexity_lab.py") if p != dest]
        if found:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(found[0]), str(dest))
            print(
                f"  moved {found[0].relative_to(ROOT)} -> instruments/complexity_lab.py"
            )
        else:
            restore("complexity_lab.py", "instruments/complexity_lab.py")

    # 4) make folding_computations independent of level_tree re-exports
    fc = PKG / "computation" / "folding_computations.py"
    text = fc.read_text(encoding="utf-8")
    fixed = text.replace(
        "from jacobs_lab.structure.level_tree import RecursiveLattice, build_level_tree, flatten",
        "from jacobs_lab.core.recursive_lattice import RecursiveLattice\n"
        "from jacobs_lab.structure.level_tree import build_level_tree, flatten",
    ).replace(
        "from Level_tree import RecursiveLattice, build_level_tree, flatten",
        "from jacobs_lab.core.recursive_lattice import RecursiveLattice\n"
        "from jacobs_lab.structure.level_tree import build_level_tree, flatten",
    )
    if fixed != text:
        fc.write_text(fixed, encoding="utf-8")
        print("  patched computation/folding_computations.py level-tree import")

    print("done. rerun: python -m jacobs_lab.testing.run_all_tests")


if __name__ == "__main__":
    main()
