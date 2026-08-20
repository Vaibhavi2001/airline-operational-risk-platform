"""Download and extract monthly BTS flight-performance data."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

import requests

BASE_URL = "https://transtats.bts.gov/PREZIP"
FILE_TEMPLATE = (
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "flight_performance"


def validate_period(year: int, month: int) -> None:
    """Validate the requested year and month."""

    if year < 1987:
        raise ValueError("BTS on-time performance data begins in 1987.")

    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")


def download_file(url: str, destination: Path) -> None:
    """Download a file using streaming to avoid loading it into memory."""

    temporary_path = destination.with_suffix(destination.suffix + ".part")

    print(f"Downloading: {url}")

    with requests.get(url, stream=True, timeout=(15, 300)) as response:
        response.raise_for_status()

        total_bytes = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0

        with temporary_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue

                output_file.write(chunk)
                downloaded_bytes += len(chunk)

                if total_bytes:
                    percent = downloaded_bytes / total_bytes * 100
                    print(
                        f"\rDownloaded {percent:6.2f}%",
                        end="",
                        flush=True,
                    )

    temporary_path.replace(destination)
    print(f"\nSaved ZIP file to: {destination}")


def validate_zip(zip_path: Path) -> None:
    """Verify that the downloaded ZIP archive is readable."""

    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Downloaded file is not a valid ZIP archive: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        corrupted_member = archive.testzip()

    if corrupted_member is not None:
        raise ValueError(f"Corrupted ZIP member detected: {corrupted_member}")

    print("ZIP validation successful.")


def extract_csv(zip_path: Path, output_path: Path) -> None:
    """Extract the CSV file safely from the BTS ZIP archive."""

    if output_path.exists():
        print(f"CSV already exists, skipping extraction: {output_path}")
        return

    with zipfile.ZipFile(zip_path) as archive:
        csv_members = [
            member for member in archive.namelist() if member.lower().endswith(".csv")
        ]

        if len(csv_members) != 1:
            raise ValueError(
                "Expected exactly one CSV file in the BTS archive, "
                f"but found {len(csv_members)}."
            )

        with (
            archive.open(csv_members[0]) as source,
            output_path.open("wb") as destination,
        ):
            shutil.copyfileobj(source, destination)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Extracted CSV to: {output_path}")
    print(f"Extracted size: {size_mb:,.2f} MB")


def download_month(year: int, month: int) -> Path:
    """Download, validate, and extract one month of BTS data."""

    validate_period(year, month)

    filename = FILE_TEMPLATE.format(year=year, month=month)
    url = f"{BASE_URL}/{filename}"

    month_directory = RAW_DATA_DIR / f"year={year}" / f"month={month:02d}"
    month_directory.mkdir(parents=True, exist_ok=True)

    zip_path = month_directory / filename
    csv_path = month_directory / f"flights_{year}_{month:02d}.csv"

    if zip_path.exists():
        print(f"ZIP already exists, skipping download: {zip_path}")
    else:
        download_file(url, zip_path)

    validate_zip(zip_path)
    extract_csv(zip_path, csv_path)

    return csv_path


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Download one month of BTS flight-performance data."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)

    return parser.parse_args()


def main() -> None:
    """Run the monthly BTS ingestion process."""

    arguments = parse_arguments()
    csv_path = download_month(arguments.year, arguments.month)
    print(f"Monthly ingestion completed successfully: {csv_path}")


if __name__ == "__main__":
    main()
