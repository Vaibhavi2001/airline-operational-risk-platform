"""Unit tests for the BTS download utilities."""

import pytest

from src.ingestion.download_bts import validate_period


@pytest.mark.parametrize(
    ("year", "month"),
    [
        (1987, 1),
        (2025, 12),
        (2026, 6),
    ],
)
def test_validate_period_accepts_valid_values(
    year: int,
    month: int,
) -> None:
    """Valid BTS periods should not raise an exception."""

    validate_period(year, month)


@pytest.mark.parametrize(
    ("year", "month", "expected_message"),
    [
        (1986, 1, "begins in 1987"),
        (2026, 0, "between 1 and 12"),
        (2026, 13, "between 1 and 12"),
    ],
)
def test_validate_period_rejects_invalid_values(
    year: int,
    month: int,
    expected_message: str,
) -> None:
    """Invalid BTS periods should raise clear validation errors."""

    with pytest.raises(ValueError, match=expected_message):
        validate_period(year, month)
