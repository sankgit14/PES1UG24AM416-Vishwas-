import pytest
from train_fare import base_fare, concession, tatkal_charge

# ─────────────────────────────────────────────
# base_fare() tests
# ─────────────────────────────────────────────

# Example test case (provided)
def test_sleeper_fare():
    """Normal SL fare above minimum."""
    assert base_fare("SL", 500) == 500


def test_base_fare_unknown_class():
    """Raises ValueError for an unknown travel class."""
    with pytest.raises(ValueError, match="unknown class"):
        base_fare("EC", 100)


def test_base_fare_invalid_distance_zero():
    """Raises ValueError when distance is 0."""
    with pytest.raises(ValueError, match="invalid distance"):
        base_fare("SL", 0)


def test_base_fare_invalid_distance_negative():
    """Raises ValueError when distance is negative."""
    with pytest.raises(ValueError, match="invalid distance"):
        base_fare("3A", -10)


def test_base_fare_minimum_fare_applied():
    """Fare below 50 should be raised to 50 (SL, 10 km → 10 < 50)."""
    assert base_fare("SL", 10) == 50


def test_base_fare_exactly_50():
    """Fare exactly at 50 is returned as-is (SL, 50 km → 50)."""
    assert base_fare("SL", 50) == 50


def test_base_fare_3a_class():
    """3A class fare calculation (rate=2)."""
    assert base_fare("3A", 100) == 200


def test_base_fare_2a_class():
    """2A class fare calculation (rate=3)."""
    assert base_fare("2A", 100) == 300


def test_base_fare_1a_class():
    """1A class fare calculation (rate=5)."""
    assert base_fare("1A", 100) == 500


# ─────────────────────────────────────────────
# concession() tests
# ─────────────────────────────────────────────

# Example test case (provided)
def test_adult_no_concession():
    """Working-age adult gets no concession."""
    assert concession(30, "M", False) == 0


def test_concession_tatkal_no_concession():
    """Tatkal booking: concession is always 0 regardless of age/gender."""
    assert concession(5, "M", True) == 0


def test_concession_tatkal_infant():
    """Tatkal booking for infant still returns 0 (tatkal overrides)."""
    assert concession(3, "F", True) == 0


def test_concession_infant_under_5():
    """Child under 5 gets 100% concession."""
    assert concession(4, "M", False) == 100


def test_concession_age_zero():
    """Newborn (age 0) gets 100% concession."""
    assert concession(0, "F", False) == 100


def test_concession_child_5_to_12():
    """Child aged 5-12 gets 50% concession."""
    assert concession(10, "M", False) == 50


def test_concession_child_age_5_boundary():
    """Child exactly age 5 gets 50% concession (lower boundary of 5-12 range)."""
    assert concession(5, "F", False) == 50


def test_concession_child_age_12_boundary():
    """Child exactly age 12 gets 50% concession (upper boundary of 5-12 range)."""
    assert concession(12, "M", False) == 50


def test_concession_senior_female():
    """Senior female citizen (>=60) gets 50% concession."""
    assert concession(65, "F", False) == 50


def test_concession_senior_male():
    """Senior male citizen (>=60) gets 40% concession."""
    assert concession(60, "M", False) == 40


def test_concession_senior_age_60_boundary():
    """Age exactly 60 (female) gets senior concession of 50."""
    assert concession(60, "F", False) == 50


def test_concession_working_age_female():
    """Working-age female (13-59) gets no concession."""
    assert concession(25, "F", False) == 0


# ─────────────────────────────────────────────
# tatkal_charge() tests
# ─────────────────────────────────────────────

def test_tatkal_charge_sl_normal():
    """SL class: charge = fare // 10, within 100-400 range."""
    assert tatkal_charge("SL", 2000) == 200


def test_tatkal_charge_sl_below_minimum():
    """SL class: charge floored at 100 when fare // 10 < 100."""
    assert tatkal_charge("SL", 100) == 100


def test_tatkal_charge_sl_above_maximum():
    """SL class: charge capped at 400 when fare // 10 > 400."""
    assert tatkal_charge("SL", 5000) == 400


def test_tatkal_charge_non_sl_normal():
    """Non-SL class: charge = fare * 3 // 10, within 100-400 range."""
    assert tatkal_charge("3A", 1000) == 300


def test_tatkal_charge_non_sl_below_minimum():
    """Non-SL class: charge floored at 100 when fare * 3 // 10 < 100."""
    assert tatkal_charge("2A", 100) == 100


def test_tatkal_charge_non_sl_above_maximum():
    """Non-SL class: charge capped at 400 when fare * 3 // 10 > 400."""
    assert tatkal_charge("1A", 2000) == 400


def test_tatkal_charge_non_sl_at_boundary_100():
    """Non-SL class: charge exactly at lower boundary (100)."""
    assert tatkal_charge("3A", 334) == 100


def test_tatkal_charge_non_sl_at_boundary_400():
    """Non-SL class: charge exactly at upper boundary (400)."""
    assert tatkal_charge("1A", 1334) == 400
