import sys
sys.path.insert(0, ".")

from format import format_idr, format_phone, SHORT_PHONE

def test_format_idr():
    assert format_idr(98820000) == "Rp 98.820.000"
    assert format_idr(1250000) == "Rp 1.250.000"
    assert format_idr(0) == "Rp 0"
    assert format_idr(None) == "Rp 0"
    assert format_idr(250000000) == "Rp 250.000.000"
    assert format_idr(3800) == "Rp 3.800"

def test_format_phone():
    assert format_phone("+6281725996882") == "+62 817-2599-6882"
    assert format_phone("+6281234567890") == "+62 812-3456-7890"
    assert format_phone("") == ""
    assert format_phone(None) == ""

def test_short_phone():
    assert SHORT_PHONE("+6281725996882") == "+62...6882"
    assert SHORT_PHONE("1234") == "1234"
    assert SHORT_PHONE("") == ""
    assert SHORT_PHONE(None) == ""
