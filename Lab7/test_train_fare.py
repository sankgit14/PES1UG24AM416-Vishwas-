import pytest
from hypothesis import given, settings, strategies as st
from train_fare import parse_pnr, journey_distance, berth_type

# ─────────────────────────────────────────────────────────────────
# Fuzz Tests — property: functions must never crash the interpreter
# (they may raise exceptions, but must not cause unhandled errors)
# ─────────────────────────────────────────────────────────────────

@given(st.text() | st.none())
def test_parse_pnr_no_crash(s):
    """
    Fuzz test: parse_pnr() must never cause an unhandled crash.
    Valid input: a string whose first char is a digit and the rest
    are also digits (e.g. "4521367890").
    For arbitrary/random text, we expect ValueError/IndexError —
    those are acceptable; a raw crash is not.
    """
    try:
        parse_pnr(s)
    except (ValueError, IndexError, TypeError, AttributeError):
        pass  # Expected exceptions for invalid input — not a crash


@given(st.text() | st.none())
def test_journey_distance_no_crash(s):
    """
    Fuzz test: journey_distance() must never cause an unhandled crash.
    Valid input: comma-separated integers (e.g. "0,120,340").
    For arbitrary text, ValueError/IndexError are acceptable.
    """
    try:
        journey_distance(s)
    except (ValueError, IndexError, TypeError, AttributeError):
        pass  # Expected exceptions for invalid input — not a crash


@given(st.text() | st.none())
def test_berth_type_no_crash(s):
    """
    Fuzz test: berth_type() must never cause an unhandled crash.
    Valid input: coach-seat string like "S3-45".
    For arbitrary text, ValueError/IndexError are acceptable.
    """
    try:
        berth_type(s)
    except (ValueError, IndexError, TypeError, AttributeError):
        pass  # Expected exceptions for invalid input — not a crash


# ─────────────────────────────────────────────────────────────────
# Valid-input Fuzz Tests — Hypothesis generates valid inputs
# ─────────────────────────────────────────────────────────────────

@given(
    zone=st.integers(min_value=1, max_value=9),
    number=st.integers(min_value=0, max_value=999999999)
)
def test_parse_pnr_valid_input(zone, number):
    """
    Fuzz test with valid PNR strings.
    parse_pnr must correctly split zone (first digit) and number (rest).
    """
    pnr = f"{zone}{number:09d}"  # e.g. "4521367890"
    result_zone, result_number = parse_pnr(pnr)
    assert result_zone == zone
    assert result_number == int(pnr[1:])


@given(
    distances=st.lists(
        st.integers(min_value=0, max_value=10000),
        min_size=2,
        max_size=10
    ).map(sorted)
)
def test_journey_distance_valid_input(distances):
    """
    Fuzz test with valid CSV distance strings.
    journey_distance must return last - first value.
    """
    csv = ",".join(str(d) for d in distances)
    result = journey_distance(csv)
    assert result == distances[-1] - distances[0]


@given(
    coach=st.text(
        alphabet=st.characters(whitelist_categories=("Lu",)),
        min_size=1,
        max_size=3
    ),
    seat_number=st.integers(min_value=0, max_value=999)
)
def test_berth_type_valid_input(coach, seat_number):
    """
    Fuzz test with valid seat strings like 'S3-45'.
    berth_type must return the correct coach and a valid BERTH type.
    """
    BERTHS = ["SU", "LB", "MB", "UB", "LB", "MB", "UB", "SL"]
    seat = f"{coach}-{seat_number}"
    result_coach, result_berth = berth_type(seat)
    assert result_coach == coach.upper()
    assert result_berth in BERTHS


# ─────────────────────────────────────────────────────────────────
# Unit Tests — specific known inputs to verify correctness
# ─────────────────────────────────────────────────────────────────

class TestParsePnr:
    def test_standard_pnr(self):
        """Zone=4, number=521367890 for PNR '4521367890'."""
        assert parse_pnr("4521367890") == (4, 521367890)

    def test_zone_1(self):
        """Zone digit 1."""
        assert parse_pnr("1000000000") == (1, 0)

    def test_zone_9(self):
        """Zone digit 9."""
        zone, number = parse_pnr("9123456789")
        assert zone == 9

    def test_empty_string_raises(self):
        """Empty string should raise an exception."""
        with pytest.raises((ValueError, IndexError)):
            parse_pnr("")

    def test_non_numeric_raises(self):
        """Non-numeric PNR should raise ValueError."""
        with pytest.raises((ValueError, IndexError, TypeError)):
            parse_pnr("ABCDEFGHIJ")


class TestJourneyDistance:
    def test_simple_two_stations(self):
        """Distance from 0 to 340 = 340."""
        assert journey_distance("0,340") == 340

    def test_three_stations(self):
        """0,120,340 → 340 - 0 = 340."""
        assert journey_distance("0,120,340") == 340

    def test_non_zero_start(self):
        """100,250,500 → 500 - 100 = 400."""
        assert journey_distance("100,250,500") == 400

    def test_single_segment(self):
        """50,150 → 100."""
        assert journey_distance("50,150") == 100

    def test_invalid_csv_raises(self):
        """Non-numeric CSV should raise ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            journey_distance("abc,def")

    def test_none_raises(self):
        """None input should raise AttributeError."""
        with pytest.raises((AttributeError, TypeError)):
            journey_distance(None)


class TestBerthType:
    def test_seat_0_is_su(self):
        """Seat 0 → index 0 → SU (side upper)."""
        assert berth_type("S1-0") == ("S1", "SU")

    def test_seat_1_is_lb(self):
        """Seat 1 → index 1 → LB (lower berth)."""
        assert berth_type("S1-1") == ("S1", "LB")

    def test_seat_8_wraps_to_su(self):
        """Seat 8 → 8 % 8 = 0 → SU."""
        assert berth_type("A1-8") == ("A1", "SU")

    def test_seat_45_example(self):
        """Seat 45 → 45 % 8 = 5 → MB."""
        assert berth_type("S3-45") == ("S3", "MB")

    def test_coach_uppercase(self):
        """Coach letters are returned uppercase."""
        coach, _ = berth_type("s3-10")
        assert coach == "S3"

    def test_no_dash_raises(self):
        """Missing '-' separator should raise ValueError."""
        with pytest.raises((ValueError, TypeError)):
            berth_type("S345")

    def test_none_raises(self):
        """None input should raise AttributeError."""
        with pytest.raises((AttributeError, TypeError)):
            berth_type(None)
