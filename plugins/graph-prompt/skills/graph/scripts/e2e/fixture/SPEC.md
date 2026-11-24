# units — specification

S1. `units/table.py` defines `FACTORS`, a dict from unit symbol to its length in metres: `m` 1, `km` 1000, `cm` 0.01, `mm` 0.001, `mi` 1609.344, `ft` 0.3048. No other symbols.
S2. `units/table.py` defines `convert(value, src, dst)`, returning `value * FACTORS[src] / FACTORS[dst]` as a float; an unknown `src` or `dst` raises `ValueError` whose message is `unknown unit: <symbol>`.
S3. `units/parse.py` defines `parse_args(argv)`, taking a list of three strings `VALUE SRC DST` and returning `(float(VALUE), SRC, DST)`; a wrong count or a VALUE that is not a number raises `SystemExit` with code 2.
S4. `cli.py` defines `main(argv)` and runs `sys.exit(main(sys.argv[1:]))` when executed: it prints the converted value formatted with `%g` to stdout and returns 0; an unknown unit prints the `ValueError` message to stderr and returns 1.
S5. Only the standard library is used.
