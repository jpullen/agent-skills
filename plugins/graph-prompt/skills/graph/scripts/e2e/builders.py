"""Scripted builders: each takes its worktree path and writes files, as a builder subagent would."""
TABLE = '''# section: factors
FACTORS = {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048}


# section: convert
def convert(value, src, dst):
    for unit in (src, dst):
        if unit not in FACTORS:
            raise ValueError(%s)
    return float(value * FACTORS[src] / FACTORS[dst])
'''
PARSE = '''# section: parse_args
def parse_args(argv):
    if len(argv) != 3:
        raise SystemExit(2)
    try:
        return float(argv[0]), argv[1], argv[2]
    except ValueError:
        raise SystemExit(2)
'''
CLI = '''import sys

from units.parse import parse_args
from units.table import convert


# section: main
def main(argv):
    value, src, dst = parse_args(argv)
    try:
        result = convert(value, src, dst)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    print("%g" % result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def table(tree):
    (tree / "units" / "table.py").write_text(TABLE % '"unknown unit: " + unit')


def table_wrong_message(tree):
    """Passes the loose table gate; the defect surfaces downstream (cause b)."""
    (tree / "units" / "table.py").write_text(TABLE % '"no such unit " + unit')


def parse(tree):
    (tree / "units" / "parse.py").write_text(PARSE)


def parse_out_of_scope(tree):
    """I03: also writes a file that belongs to another node."""
    parse(tree)
    (tree / "units" / "table.py").write_text("# placeholder\n")


def parse_undo(tree):
    (tree / "units" / "table.py").unlink()


def cli(tree):
    (tree / "cli.py").write_text(CLI)


def killed_before_writing(tree):
    """I12: the builder was stopped before it wrote anything."""


def killed_after_writing(tree):
    """I12: the builder was stopped after writing, before running its check or returning."""
    cli(tree)


def nothing(tree):
    """A re-gate: the node's own files need no change."""
