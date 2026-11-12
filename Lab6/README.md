# Lab 6 – Code & Branch Coverage (Train Fare Calculator)

## Overview

This lab demonstrates **code coverage** and **branch coverage** testing using `pytest` and `pytest-cov`.

The system under test is a **Train Fare Calculator** (`train_fare.py`) that computes:
- **Base fare** for different travel classes and distances
- **Concession** percentages based on age, gender, and booking type
- **Tatkal surcharge** based on travel class and fare amount

---

## Project Structure

```
Lab6/
├── train_fare.py          # Source code (system under test)
├── test_train_fare.py     # Pytest test suite (29 test cases)
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

---

## Functions Under Test

### `base_fare(travel_class, distance_km)`
Calculates the base fare based on class rates (SL=Rs.1/km, 3A=Rs.2/km, 2A=Rs.3/km, 1A=Rs.5/km).
Minimum fare is Rs.50. Raises `ValueError` for invalid inputs.

### `concession(age, gender, is_tatkal)`
Returns the concession percentage:

| Condition | Concession |
|---|---|
| Tatkal booking | 0% |
| Age < 5 | 100% |
| Age 5-12 | 50% |
| Age >= 60, Female | 50% |
| Age >= 60, Male | 40% |
| All others | 0% |

### `tatkal_charge(travel_class, fare)`
Returns the tatkal surcharge (10% for SL, 30% for others), capped between Rs.100-400.

---

## Test Coverage Results

| Metric | Result |
|---|---|
| **Statements covered** | 31 / 31 (100%) |
| **Branches covered** | 22 / 22 (100%) |
| **Total test cases** | 29 |
| **All tests passing** | Yes |

---

## How to Run

### 1. Install dependencies
```bash
pip install pytest pytest-cov
```

### 2. Run tests with branch coverage
```bash
python -m pytest test_train_fare.py -v --cov=train_fare --cov-report=term-missing --cov-branch
```
