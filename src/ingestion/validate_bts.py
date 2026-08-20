"""Validate the schema and basic quality of a BTS monthly dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "flight_performance"
REPORT_DIR = PROJECT_ROOT / "data" / "interim" / "quality_reports"

REQUIRED_COLUMNS = {
    "Year",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "FlightDate",
    "Reporting_Airline",
    "Flight_Number_Reporting_Airline",
    "Tail_Number",
    "Origin",
    "Dest",
    "CRSDepTime",
    "CRSArrTime",
    "DepDelay",
    "ArrDelay",
    "Cancelled",
    "Diverted",
    "CRSElapsedTime",
    "Distance",
}

FLIGHT_KEY = [
    "FlightDate",
    "Reporting_Airline",
    "Flight_Number_Reporting_Airline",
    "Origin",
    "Dest",
    "CRSDepTime",
]


def get_csv_path(year: int, month: int) -> Path:
    """Return the expected raw CSV location."""

    return (
        RAW_DATA_DIR
        / f"year={year}"
        / f"month={month:02d}"
        / f"flights_{year}_{month:02d}.csv"
    )


def validate_dataset(year: int, month: int) -> dict[str, object]:
    """Validate schema and calculate quality statistics."""

    csv_path = get_csv_path(year, month)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}\nRun download_bts.py before validation."
        )

    print(f"Validating: {csv_path}")

    flights = pl.scan_csv(
        csv_path,
        infer_schema_length=10_000,
        null_values=[""],
    )

    schema = flights.collect_schema()
    available_columns = set(schema.names())
    missing_columns = sorted(REQUIRED_COLUMNS - available_columns)

    if missing_columns:
        raise ValueError(
            "Required columns are missing:\n- " + "\n- ".join(missing_columns)
        )

    major_disruption = (pl.col("Cancelled").fill_null(0) == 1) | (
        pl.col("ArrDelay").fill_null(float("-inf")) >= 60
    )

    summary = (
        flights.select(
            pl.len().alias("row_count"),
            pl.col("FlightDate").min().alias("minimum_flight_date"),
            pl.col("FlightDate").max().alias("maximum_flight_date"),
            pl.col("Reporting_Airline").n_unique().alias("unique_airlines"),
            pl.col("Origin").n_unique().alias("unique_origin_airports"),
            pl.struct(["Origin", "Dest"]).n_unique().alias("unique_routes"),
            pl.col("Cancelled").fill_null(0).sum().alias("cancelled_flights"),
            major_disruption.cast(pl.Int64).sum().alias("major_disruptions"),
            pl.col("ArrDelay").is_null().mean().alias("arrival_delay_missing_rate"),
            pl.col("Tail_Number").is_null().mean().alias("tail_number_missing_rate"),
        )
        .collect()
        .to_dicts()[0]
    )

    duplicate_rows = (
        flights.group_by(FLIGHT_KEY)
        .len()
        .filter(pl.col("len") > 1)
        .select((pl.col("len") - 1).sum().fill_null(0).alias("duplicate_rows"))
        .collect()
        .item()
    )

    row_count = int(summary["row_count"])
    disruption_count = int(summary["major_disruptions"])

    summary["column_count"] = len(available_columns)
    summary["duplicate_rows"] = int(duplicate_rows)
    summary["major_disruption_rate"] = disruption_count / row_count if row_count else 0
    summary["source_file"] = str(csv_path)
    summary["validation_status"] = "passed"

    return summary


def save_report(
    report: dict[str, object],
    year: int,
    month: int,
) -> Path:
    """Save the validation report as JSON."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"bts_{year}_{month:02d}_quality.json"

    with report_path.open("w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=2, default=str)

    return report_path


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Validate one month of BTS flight data."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)

    return parser.parse_args()


def main() -> None:
    """Run monthly dataset validation."""

    arguments = parse_arguments()
    report = validate_dataset(arguments.year, arguments.month)
    report_path = save_report(
        report,
        arguments.year,
        arguments.month,
    )

    print("\nValidation passed.")
    print(json.dumps(report, indent=2, default=str))
    print(f"\nQuality report saved to: {report_path}")


if __name__ == "__main__":
    main()
