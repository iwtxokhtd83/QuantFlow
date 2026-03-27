"""Generate sample OHLCV data for testing."""

import csv
import random
from datetime import datetime, timedelta


def generate_ohlcv(filename: str = "data/sample_ohlcv.csv", days: int = 1000, start_price: float = 100.0) -> None:
    """Generate realistic synthetic OHLCV data."""
    random.seed(42)
    date = datetime(2020, 1, 1)
    price = start_price

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "open", "high", "low", "close", "volume"])

        for _ in range(days):
            if date.weekday() >= 5:  # skip weekends
                date += timedelta(days=1)
                continue

            open_price = price
            change = random.gauss(0.0003, 0.015)  # slight upward drift
            close_price = open_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.005)))
            volume = int(random.gauss(1_000_000, 300_000))

            writer.writerow([
                date.strftime("%Y-%m-%d"),
                f"{open_price:.2f}",
                f"{high_price:.2f}",
                f"{low_price:.2f}",
                f"{close_price:.2f}",
                max(volume, 100_000),
            ])

            price = close_price
            date += timedelta(days=1)

    print(f"Generated {filename} with {days} trading days.")


if __name__ == "__main__":
    generate_ohlcv()
