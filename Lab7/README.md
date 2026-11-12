# Lab 7 – Fuzz Testing with Hypothesis (Train PNR System)

## Overview

This lab demonstrates **fuzz testing** (property-based testing) using the
[Hypothesis](https://hypothesis.readthedocs.io/) library.

The system under test is a **Train PNR Parser** (`train_fare.py`) with three functions:
- `parse_pnr()` — splits a PNR string into zone and number
- `journey_distance()` — computes total journey distance from a CSV of station distances
- `berth_type()` — determines coach and berth type from a seat string

---

## Project Structure

```
Lab7/
├── train_fare.py        # Source code (system under test)
├── test_train_fare.py   # Fuzz + unit test suite
├── README.md            # This file
└── requirements.txt     # Python dependencies
```

---

## Functions Under Test

### `parse_pnr(pnr: str) -> (int, int)`
Splits a PNR string: first character = zone number, rest = ticket number.
Example: `"4521367890"` → `(4, 521367890)`

### `journey_distance(distances_csv: str) -> int`
Parses a comma-separated list of distances and returns `last - first`.
Example: `"0,120,340"` → `340`

### `berth_type(seat: str) -> (str, str)`
Parses a seat string like `"S3-45"` and returns `(coach, berth_type)`.
Berth types cycle through: `["SU", "LB", "MB", "UB", "LB", "MB", "UB", "SL"]`
Example: `"S3-45"` → `("S3", "MB")` (45 % 8 = 5 → "MB")

---

## Test Strategy

### 1. Fuzz Tests (Hypothesis — arbitrary random inputs)
Tests that functions **never crash** the interpreter on any input.
Invalid inputs raise expected exceptions (`ValueError`, `IndexError`, etc.) — not crashes.

### 2. Valid-input Fuzz Tests (Hypothesis — structured valid inputs)
Hypothesis generates **valid** inputs to verify correctness properties:
- `parse_pnr` correctly splits zone and number
- `journey_distance` returns correct arithmetic result
- `berth_type` returns a valid berth from the BERTHS list

### 3. Unit Tests (specific known values)
Direct assertions on known inputs to verify exact expected outputs.

---

## Test Results

| Test Type | Tests | Result |
|---|---|---|
| Fuzz (crash safety) | 3 | ✅ Pass |
| Valid-input fuzz | 3 | ✅ Pass |
| Unit tests | 16 | ✅ Pass |
| **Total** | **22** | ✅ All Pass |

---

## How to Run

### 1. Install dependencies
```bash
pip install pytest pytest-cov hypothesis
```

### 2. Run all tests
```bash
python -m pytest test_train_fare.py -v
```

### 3. Run with coverage
```bash
python -m pytest test_train_fare.py -v --cov=train_fare --cov-report=term-missing
```
