from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "jacobs_lab"

PKG.mkdir(parents=True, exist_ok=True)

count = 0

for p in sorted(ROOT.glob("*.py")):
    shutil.copy2(p, PKG / p.name)
    count += 1

INIT = """import os
import sys

_PKG_DIR = os.path.dirname(__file__)

if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

__version__ = "0.1.0"
"""

MAIN = """import sys

from lab_cli import main


def main_entry():
    return main()


if __name__ == "__main__":
    sys.exit(main_entry())
"""

(PKG / "__init__.py").write_text(INIT, encoding="utf-8")
(PKG / "__main__.py").write_text(MAIN, encoding="utf-8")

print(f"Synced {count} modules into {PKG}")
