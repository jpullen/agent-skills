"""A deliberately loose table gate (scenario: upstream reopened). It does not check the error message,
so a table whose message is wrong is accepted and the defect surfaces at the cli gate (cause b)."""
import pytest
from units.table import convert


def test_convert_numbers():
    assert convert(5, "km", "m") == pytest.approx(5000.0)
    assert convert(1, "mi", "ft") == pytest.approx(5280.0)


def test_unknown_raises():
    with pytest.raises(ValueError):
        convert(1, "parsec", "m")
