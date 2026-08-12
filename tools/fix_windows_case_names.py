from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "jacobs_lab"

FIXES = [
    ("core", "Nested_mapper.py", "nested_mapper.py"),
    ("structure", "Level_tree.py", "level_tree.py"),
]


def exact_file_names(directory: pathlib.Path):
    return {p.name for p in directory.iterdir() if p.is_file()}


def force_case_rename(subpackage: str, old_name: str, new_name: str) -> bool:
    directory = PKG / subpackage

    if not directory.exists():
        print(f"MISSING directory: {directory}")
        return False

    names = exact_file_names(directory)

    if new_name in names:
        print(f"OK: {subpackage}/{new_name} already exists")
        return True

    candidates = [name for name in names if name.lower() == old_name.lower()]

    if not candidates:
        print(f"MISSING file: {subpackage}/{old_name}")
        return False

    ok = True

    for name in candidates:
        src = directory / name
        tmp = directory / f"{new_name}.case_tmp.py"
        dest = directory / new_name

        try:
            if tmp.exists():
                tmp.unlink()

            src.rename(tmp)
            tmp.rename(dest)

            print(f"RENAMED: {subpackage}/{name} -> {subpackage}/{new_name}")

        except Exception as exc:
            print(f"FAILED: {subpackage}/{name} -> {subpackage}/{new_name}: {exc}")
            ok = False

    return ok


def main():
    ok = True

    for subpackage, old_name, new_name in FIXES:
        ok = force_case_rename(subpackage, old_name, new_name) and ok

    if not ok:
        raise SystemExit(1)

    print()
    print("Windows case-name repair complete.")
    print()
    print("Next steps:")
    print("  python -m pip uninstall -y jacobs-lab")
    print("  python -m pip install -e .")
    print('  python -c "import jacobs_lab.core.nested_mapper as m; print(m.__file__)"')
    print(
        '  python -c "import jacobs_lab.structure.level_tree as m; print(m.__file__)"'
    )


if __name__ == "__main__":
    main()
