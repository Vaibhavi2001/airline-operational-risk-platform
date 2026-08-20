"""Transform raw BTS CSV data into a typed Parquet base table."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "flight_performance"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim" / "flight_performance"

COLUMN_MAPPING = {
    "Year": "year",
    "Month": "month",
    "DayofMonth": "day_of_month",
    "DayOfWeek": "day_of_week",
    "FlightDate": "flight_date",
    "Reporting_Airline": "reporting_airline",
    "Flight_Number_Reporting_Airline": "flight_number",
    "Origin": "origin",
    "Dest": "destination",
    "CRSDepTime": "scheduled_departure_time",
    "CRSArrTime": "scheduled_arrival_time",
    "CRSElapsedTime": "scheduled_elapsed_minutes",
    "Distance": "distance_miles",
    "ArrDelay": "arrival_delay_minutes",
    "Cancelled": "cancelled",
    "CancellationCode": "cancellation_code",
    "Diverted": "diverted",
}


def get_raw_path(year: int, month: int) -> Path:
    """Return the expected raw CSV path."""

    return (
        RAW_DATA_DIR
        / f"year={year}"
        / f"month={month:02d}"
        / f"flights_{year}_{month:02d}.csv"
    )


def get_output_path(year: int, month: int) -> Path:
    """Return the transformed Parquet path."""

    return (
        INTERIM_DATA_DIR
        / f"year={year}"
        / f"month={month:02d}"
        / f"flights_{year}_{month:02d}.parquet"
    )


def build_transformation(raw_path: Path) -> pl.LazyFrame:
    """Build a leakage-aware transformation for one monthly file."""

    flights = pl.scan_csv(
        raw_path,
        infer_schema_length=10_000,
        null_values=[""],
    )

    available_columns = set(flights.collect_schema().names())
    missing_columns = sorted(set(COLUMN_MAPPING) - available_columns)

    if missing_columns:
        raise ValueError(
            "Transformation cannot continue because columns are missing:\n- "
            + "\n- ".join(missing_columns)
        )

    selected = (
        flights.select(list(COLUMN_MAPPING))
        .rename(COLUMN_MAPPING)
        .with_columns(
            pl.col("year").cast(pl.Int16),
            pl.col("month").cast(pl.Int8),
            pl.col("day_of_month").cast(pl.Int8),
            pl.col("day_of_week").cast(pl.Int8),
            pl.col("flight_date").str.strptime(pl.Date, strict=True),
            pl.col("flight_number").cast(pl.Int32),
            pl.col("scheduled_departure_time").cast(pl.Int16),
            pl.col("scheduled_arrival_time").cast(pl.Int16),
            pl.col("scheduled_elapsed_minutes").cast(pl.Float32),
            pl.col("distance_miles").cast(pl.Float32),
            pl.col("arrival_delay_minutes").cast(pl.Float32),
            pl.col("cancelled").fill_null(0).cast(pl.Int8),
            pl.col("diverted").fill_null(0).cast(pl.Int8),
        )
    )

    scheduled_departure_minutes = (
        pl.when(pl.col("scheduled_departure_time") == 2400)
        .then(0)
        .otherwise(
            (pl.col("scheduled_departure_time") // 100) * 60
            + (pl.col("scheduled_departure_time") % 100)
        )
        .cast(pl.Int16)
    )

    major_disruption = (
        (pl.col("cancelled") == 1)
        | (pl.col("arrival_delay_minutes") >= 60).fill_null(False)
    ).cast(pl.Int8)

    return (
        selected.with_columns(
            pl.concat_str(
                ["origin", "destination"],
                separator="-",
            ).alias("route"),
            scheduled_departure_minutes.alias("scheduled_departure_minutes"),
            major_disruption.alias("major_disruption"),
        )
        .with_columns(
            (pl.col("scheduled_departure_minutes") // 60)
            .cast(pl.Int8)
            .alias("scheduled_departure_hour")
        )
        .sort(
            [
                "flight_date",
                "scheduled_departure_time",
                "reporting_airline",
                "flight_number",
            ]
        )
    )


def transform_month(year: int, month: int) -> Path:
    """Transform one month of raw BTS flight data."""

    raw_path = get_raw_path(year, month)
    output_path = get_output_path(year, month)

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {raw_path}\n"
            "Run download_bts.py before transformation."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading raw data from: {raw_path}")
    transformed = build_transformation(raw_path).collect(engine="streaming")

    transformed.write_parquet(
        output_path,
        compression="zstd",
        statistics=True,
    )

    row_count = transformed.height
    disruption_count = transformed["major_disruption"].sum()
    disruption_rate = disruption_count / row_count
    output_size_mb = output_path.stat().st_size / (1024 * 1024)

    print("\nTransformation completed successfully.")
    print(f"Rows: {row_count:,}")
    print(f"Columns: {transformed.width}")
    print(f"Major disruptions: {disruption_count:,}")
    print(f"Major-disruption rate: {disruption_rate:.4%}")
    print(f"Parquet size: {output_size_mb:,.2f} MB")
    print(f"Saved to: {output_path}")

    return output_path


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Transform one month of raw BTS data to Parquet."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)

    return parser.parse_args()


def main() -> None:
    """Run the monthly transformation."""

    arguments = parse_arguments()
    transform_month(arguments.year, arguments.month)


if __name__ == "__main__":
    main()
