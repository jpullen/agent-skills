import pytest
from units.parse import parse_args

def test_ok():
    assert parse_args(["2.5", "km", "m"]) == (2.5, "km", "m")

@pytest.mark.parametrize("argv", [["1", "km"], ["1", "km", "m", "x"], ["one", "km", "m"], []])
def test_bad(argv):
    with pytest.raises(SystemExit) as e:
        parse_args(argv)
    assert e.value.code == 2
