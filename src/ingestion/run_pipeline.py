"""Orchestrate BTS ingestion, validation, and transformation."""

from __future__ import annotations

import argparse
from collections.abc import Iterator

from src.ingestion.download_bts import download_month
from src.ingestion.transform_bts import transform_month
from src.ingestion.validate_bts import save_report, validate_dataset


def iter_months(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> Iterator[tuple[int, int]]:
    """Yield inclusive year-month values in chronological order."""

    if not 1 <= start_month <= 12:
        raise ValueError("Start month must be between 1 and 12.")

    if not 1 <= end_month <= 12:
        raise ValueError("End month must be between 1 and 12.")

    start_index = start_year * 12 + start_month - 1
    end_index = end_year * 12 + end_month - 1

    if start_index > end_index:
        raise ValueError("Start period must not be after end period.")

    for month_index in range(start_index, end_index + 1):
        year, zero_based_month = divmod(month_index, 12)
        yield year, zero_based_month + 1


def run_pipeline(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    continue_on_error: bool = False,
) -> None:
    """Run the complete pipeline for an inclusive monthly range."""

    periods = list(
        iter_months(
            start_year,
            start_month,
            end_year,
            end_month,
        )
    )
    failures: list[str] = []

    for position, (year, month) in enumerate(periods, start=1):
        period_name = f"{year}-{month:02d}"

        print("\n" + "=" * 72)
        print(f"Processing {period_name} ({position} of {len(periods)})")
        print("=" * 72)

        try:
            download_month(year, month)

            report = validate_dataset(year, month)
            report_path = save_report(report, year, month)
            print(f"Quality report saved to: {report_path}")

            transform_month(year, month)

        except Exception as error:
            failure_message = f"{period_name}: {type(error).__name__}: {error}"
            failures.append(failure_message)
            print(f"\nPipeline failed for {failure_message}")

            if not continue_on_error:
                raise

    print("\n" + "=" * 72)
    print("PIPELINE SUMMARY")
    print("=" * 72)
    print(f"Requested months: {len(periods)}")
    print(f"Successful months: {len(periods) - len(failures)}")
    print(f"Failed months: {len(failures)}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
    else:
        print("All requested months completed successfully.")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Download, validate, and transform a range of BTS data.")
    )
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--start-month", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--end-month", type=int, required=True)
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing later months after a failure.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the pipeline from command-line arguments."""

    arguments = parse_arguments()

    run_pipeline(
        start_year=arguments.start_year,
        start_month=arguments.start_month,
        end_year=arguments.end_year,
        end_month=arguments.end_month,
        continue_on_error=arguments.continue_on_error,
    )


if __name__ == "__main__":
    main()
