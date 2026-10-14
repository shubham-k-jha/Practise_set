import csv
import random
from datetime import date, timedelta
from pathlib import Path


OUTPUT_PATH = Path(__file__).parent / "data" / "raw_orders.csv"
ROW_COUNT = 2_500


def build_rows():
    randomizer = random.Random(42)
    products = ["Notebook", "Pen Set", "Desk Lamp", "Water Bottle", "Backpack"]
    countries = ["United States", "Canada", "United Kingdom", "Australia"]
    start_date = date(2024, 1, 1)
    rows = []

    for index in range(ROW_COUNT):
        if index and index % 97 == 0:
            duplicate = rows[-1].copy()
            duplicate["order_id"] = rows[-2]["order_id"]
            rows.append(duplicate)
            continue

        order_date = start_date + timedelta(days=randomizer.randrange(365))
        date_formats = [
            order_date.isoformat(),
            order_date.strftime("%m/%d/%Y"),
            order_date.strftime("%d-%b-%Y"),
        ]
        row = {
            "order_id": f"ORD-{index + 1:05d}",
            "customer_id": f"CUST-{randomizer.randint(1, 800):04d}",
            "order_date": randomizer.choice(date_formats),
            "product": randomizer.choice(products),
            "quantity": str(randomizer.randint(1, 8)),
            "unit_price": f"{randomizer.uniform(3, 180):.2f}",
            "country": randomizer.choice(countries),
        }

        if index % 11 == 0:
            row["product"] = f"  {row['product'].lower()}  "
        if index % 13 == 0:
            row["country"] = f" {row['country'].upper()} "
        if index % 101 == 0:
            row["order_date"] = "not-a-date"
        if index % 127 == 0:
            row["quantity"] = "unknown"
        if index % 149 == 0:
            row["unit_price"] = ""
        if index % 173 == 0:
            row["customer_id"] = " "
        if index % 191 == 0:
            row["product"] = ""

        rows.append(row)

    return rows


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "order_id",
                "customer_id",
                "order_date",
                "product",
                "quantity",
                "unit_price",
                "country",
            ],
        )
        writer.writeheader()
        writer.writerows(build_rows())
    print(f"Generated {ROW_COUNT} rows at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()