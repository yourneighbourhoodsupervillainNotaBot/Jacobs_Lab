from __future__ import annotations

import argparse
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PKG = ROOT / "src" / "jacobs_lab"
LEGACY = ROOT / "legacy" / "flat_modules"

KNOWN_FLAT_MODULES = {
    "__init__",
    "category_theory",
    "complexity_lab",
    "flexagon",
    "fold_codec",
    "fold_complexity",
    "fold_trace_inspector",
    "folding_computation",
    "folding_computations",
    "folding_graph",
    "galois_fields",
    "general_recursive_mapper",
    "lab_adapters",
    "lab_adapters_extended",
    "lab_cli",
    "lab_compat",
    "lab_export",
    "lab_inspector",
    "lab_sonify_trace",
    "lab_trace",
    "Level_tree",
    "level_tree",
    "named_aliases",
    "natural_transformations",
    "Nested_mapper",
    "nested_mapper",
    "node_inspector",
    "pathfinding_lab",
    "prime_machinery",
    "pyglet_visualizer",
    "quintic_analysis",
    "recursive_lattice",
    "run_all_tests",
    "set_theory",
    "sonify",
    "test_harness",
    "test_sonify",
    "test_tree_preview",
    "test_walk_engine",
    "three_body_lab",
    "triangle_state_machine",
    "turing_universality",
    "universality_probe",
}

DOC_PAGES = {
    "docs/ARCHITECTURE.md": (
        "# Jacobs Lab Architecture\n\n"
        "Source of truth: `src/jacobs_lab/`\n\n"
        "Legacy flat modules: `legacy/flat_modules/`\n\n"
        "Canonical imports use subpackage paths, for example:\n\n"
        "```python\n"
        "from jacobs_lab.core.general_recursive_mapper import RecursiveMapper\n"
        "from jacobs_lab.structure.level_tree import TreeNode\n"
        "from jacobs_lab.computation.folding_computations import run_program\n"
        "```\n"
    ),
    "docs/TRACE.md": (
        "# Trace Layer\n\n"
        "Unified trace/event system modules:\n\n"
        "- `jacobs_lab.trace.lab_trace`\n"
        "- `jacobs_lab.trace.lab_adapters`\n"
        "- `jacobs_lab.trace.lab_adapters_extended`\n"
        "- `jacobs_lab.trace.lab_export`\n\n"
        "Use `python -m jacobs_lab trace --help` for commands.\n"
    ),
    "docs/VISUALIZATION.md": (
        "# Visualization\n\n"
        "Canonical inspector: `jacobs_lab.viz.lab_inspector`\n\n"
        "Headless export formats: JSON, text, HTML, PNG.\n"
    ),
    "docs/MATH.md": (
        "# Mathematical Scope\n\n"
        "This repository computes structural relationships honestly.\n\n"
        "It does not solve unsolved problems such as P vs NP, closed-form primes,\n"
        "general three-body closed forms, or radical solutions for general quintics.\n"
    ),
    "docs/PACKAGING.md": (
        "# Packaging\n\n"
        "Install editable:\n\n"
        "```bash\n"
        "python -m pip install -e .\n"
        "```\n\n"
        "Test:\n\n"
        "```bash\n"
        "python -m jacobs_lab test\n"
        "python -m jacobs_lab.testing.run_all_tests\n"
        "```\n\n"
        "Python imports are case-sensitive. Canonical module names are lowercase.\n"
    ),
    "legacy/README.md": (
        "# Legacy\n\n"
        "The `flat_modules/` directory contains pre-package repository-root modules.\n\n"
        "Source of truth is now `src/jacobs_lab/`.\n"
    ),
}

GITIGNORE_ENTRIES = [
    "__pycache__/",
    "*.pyc",
    "*.egg-info/",
    ".venv/",
    "venv/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".hypothesis/",
    "backup_jacobs_lab*/",
    "traces/*",
    "!traces/.gitkeep",
    "*.wav",
]


def ensure_dirs():
    directories = [
        ROOT / "docs",
        ROOT / "tests" / "property",
        ROOT / "examples",
        ROOT / "scripts",
        ROOT / "traces",
        ROOT / "legacy" / "flat_modules",
    ]

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)

    keep = ROOT / "traces" / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")


def write_simple_files(force: bool):
    written = 0
    skipped = 0

    for rel, content in DOC_PAGES.items():
        path = ROOT / rel

        if path.exists() and not force:
            print(f"skip existing: {rel}")
            skipped += 1
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote: {rel}")
        written += 1

    print(f"wrote {written} files, skipped {skipped} existing files")


def append_gitignore():
    gitignore = ROOT / ".gitignore"

    existing = set()
    if gitignore.exists():
        existing = {
            line.strip()
            for line in gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    missing = [entry for entry in GITIGNORE_ENTRIES if entry not in existing]

    if not missing:
        print(".gitignore already up to date")
        return

    with gitignore.open("a", encoding="utf-8") as f:
        f.write("\n# added by tools/normalize_repository.py\n")
        for entry in missing:
            f.write(entry + "\n")

    print(f"added {len(missing)} entries to .gitignore")


def canonical_package_ready() -> bool:
    if not SRC_PKG.exists():
        return False

    def has_exact(dirpath: pathlib.Path, name: str) -> bool:
        if not dirpath.exists():
            return False

        return any(p.name == name for p in dirpath.iterdir() if p.is_file())

    return (
        has_exact(SRC_PKG / "core", "nested_mapper.py")
        and has_exact(SRC_PKG / "structure", "level_tree.py")
        and (SRC_PKG / "__init__.py").exists()
        and (SRC_PKG / "__main__.py").exists()
    )


def unique_destination(dest: pathlib.Path) -> pathlib.Path:
    if not dest.exists():
        return dest

    i = 1

    while True:
        candidate = dest.with_name(f"{dest.stem}.duplicate_{i}{dest.suffix}")

        if not candidate.exists():
            return candidate

        i += 1


def move_legacy_modules():
    LEGACY.mkdir(parents=True, exist_ok=True)

    root_py_files = {p.name.lower(): p for p in ROOT.glob("*.py")}

    moved = 0

    for stem in sorted(KNOWN_FLAT_MODULES):
        p = root_py_files.get(stem.lower())

        if p is None or not p.exists():
            continue

        dest = unique_destination(LEGACY / p.name)
        shutil.move(str(p), str(dest))

        print(f"moved {p.name} -> legacy/flat_modules/{dest.name}")
        moved += 1

    if moved == 0:
        print("no legacy root modules found to move")
    else:
        print(f"moved {moved} legacy modules")


def main():
    ap = argparse.ArgumentParser(
        description="Final repository normalization for Jacobs Lab."
    )

    ap.add_argument(
        "--move-legacy",
        action="store_true",
        help="Move known repository-root flat modules into legacy/flat_modules.",
    )

    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite normalization placeholder files if they already exist.",
    )

    ap.add_argument(
        "--allow-uncanonical",
        action="store_true",
        help="Allow legacy movement even if canonical package checks fail.",
    )

    args = ap.parse_args()

    ensure_dirs()
    write_simple_files(args.force)
    append_gitignore()

    if args.move_legacy:
        if not canonical_package_ready() and not args.allow_uncanonical:
            raise SystemExit(
                "Canonical package does not appear ready.\n"
                "Expected exact files:\n"
                "  src/jacobs_lab/core/nested_mapper.py\n"
                "  src/jacobs_lab/structure/level_tree.py\n\n"
                "Run the case-repair/canonicalization tools first, or use\n"
                "--allow-uncanonical if you really want to proceed."
            )

        move_legacy_modules()

    print()
    print("Repository normalization complete.")
    print()
    print("Next steps:")
    print('  python -m pip install -e ".[dev,audio]"')
    print("  python -m pytest -q")
    print("  python -m jacobs_lab test")


if __name__ == "__main__":
    main()