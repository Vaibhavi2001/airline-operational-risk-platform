"""Unit tests for the multi-month ingestion orchestrator."""

import pytest

from src.ingestion.run_pipeline import iter_months


def test_iter_months_within_one_year() -> None:
    """Month ranges within a year should be inclusive."""

    result = list(iter_months(2026, 4, 2026, 6))

    assert result == [
        (2026, 4),
        (2026, 5),
        (2026, 6),
    ]


def test_iter_months_across_year_boundary() -> None:
    """Month ranges should continue correctly into a new year."""

    result = list(iter_months(2025, 11, 2026, 2))

    assert result == [
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
    ]


@pytest.mark.parametrize(
    (
        "start_year",
        "start_month",
        "end_year",
        "end_month",
        "expected_message",
    ),
    [
        (2026, 0, 2026, 1, "Start month"),
        (2026, 1, 2026, 13, "End month"),
        (2026, 6, 2026, 5, "must not be after"),
    ],
)
def test_iter_months_rejects_invalid_ranges(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    expected_message: str,
) -> None:
    """Invalid monthly ranges should raise clear errors."""

    with pytest.raises(ValueError, match=expected_message):
        list(
            iter_months(
                start_year,
                start_month,
                end_year,
                end_month,
            )
        )
