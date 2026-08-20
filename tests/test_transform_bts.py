"""Unit tests for the BTS transformation pipeline."""

from pathlib import Path

import polars as pl

from src.ingestion.transform_bts import build_transformation


def create_test_csv(path: Path) -> None:
    """Create a small representative BTS dataset."""

    test_data = pl.DataFrame(
        {
            "Year": [2026, 2026, 2026],
            "Month": [6, 6, 6],
            "DayofMonth": [1, 1, 1],
            "DayOfWeek": [1, 1, 1],
            "FlightDate": [
                "2026-06-01",
                "2026-06-01",
                "2026-06-01",
            ],
            "Reporting_Airline": ["AA", "DL", "UA"],
            "Flight_Number_Reporting_Airline": [101, 202, 303],
            "Origin": ["BOS", "JFK", "ORD"],
            "Dest": ["JFK", "ATL", "LAX"],
            "CRSDepTime": [5, 2400, 1330],
            "CRSArrTime": [120, 200, 1600],
            "CRSElapsedTime": [75.0, 120.0, 210.0],
            "Distance": [187.0, 760.0, 1744.0],
            "ArrDelay": [10.0, None, 75.0],
            "Cancelled": [0.0, 1.0, 0.0],
            "CancellationCode": [None, "B", None],
            "Diverted": [0.0, 0.0, 0.0],
        }
    )

    test_data.write_csv(path)


def test_build_transformation_preserves_rows(
    tmp_path: Path,
) -> None:
    """Transformation should preserve all input flight records."""

    csv_path = tmp_path / "flights.csv"
    create_test_csv(csv_path)

    result = build_transformation(csv_path).collect()

    assert result.height == 3
    assert result.width == 21


def test_major_disruption_target(tmp_path: Path) -> None:
    """Cancellation and 60-minute delay should produce positive labels."""

    csv_path = tmp_path / "flights.csv"
    create_test_csv(csv_path)

    result = build_transformation(csv_path).collect().sort("flight_number")

    assert result["major_disruption"].to_list() == [0, 1, 1]


def test_scheduled_time_conversion(tmp_path: Path) -> None:
    """BTS schedule times should convert to minutes after midnight."""

    csv_path = tmp_path / "flights.csv"
    create_test_csv(csv_path)

    result = build_transformation(csv_path).collect().sort("flight_number")

    assert result["scheduled_departure_minutes"].to_list() == [
        5,
        0,
        810,
    ]

    assert result["scheduled_departure_hour"].to_list() == [
        0,
        0,
        13,
    ]


def test_route_creation(tmp_path: Path) -> None:
    """Origin and destination should form a directional route."""

    csv_path = tmp_path / "flights.csv"
    create_test_csv(csv_path)

    result = build_transformation(csv_path).collect().sort("flight_number")

    assert result["route"].to_list() == [
        "BOS-JFK",
        "JFK-ATL",
        "ORD-LAX",
    ]
