import sys

from .lab_cli import main


def main_entry():
    return main()


if __name__ == "__main__":
    sys.exit(main_entry())
