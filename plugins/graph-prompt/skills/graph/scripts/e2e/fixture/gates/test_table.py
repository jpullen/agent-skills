import pytest
from units.table import FACTORS, convert

def test_factors_exact():
    assert FACTORS == {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048}

@pytest.mark.parametrize("v,s,d,want", [(5, "km", "m", 5000.0), (1, "mi", "ft", 5280.0), (250, "cm", "m", 2.5), (3, "m", "mm", 3000.0)])
def test_convert(v, s, d, want):
    got = convert(v, s, d)
    assert isinstance(got, float) and got == pytest.approx(want)

@pytest.mark.parametrize("s,d,bad", [("parsec", "m", "parsec"), ("m", "yd", "yd")])
def test_unknown(s, d, bad):
    with pytest.raises(ValueError, match=f"^unknown unit: {bad}$"):
        convert(1, s, d)
