import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


REQUIRED_COLUMNS = (
    "order_id",
    "customer_id",
    "order_date",
    "product",
    "quantity",
    "unit_price",
    "country",
)
COUNTRY_NAMES = {
    "australia": "Australia",
    "canada": "Canada",
    "united kingdom": "United Kingdom",
    "united states": "United States",
}
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y")


def parse_order_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError("invalid order_date")


def clean_row(row):
    values = {key: (value or "").strip() for key, value in row.items()}
    missing = [key for key in REQUIRED_COLUMNS if not values.get(key)]
    if missing:
        raise ValueError(f"missing required value: {', '.join(missing)}")

    try:
        quantity = int(values["quantity"])
    except ValueError as error:
        raise ValueError("quantity must be a positive integer") from error
    if quantity <= 0:
        raise ValueError("quantity must be a positive integer")

    try:
        unit_price = float(values["unit_price"])
    except ValueError as error:
        raise ValueError("unit_price must be a non-negative number") from error
    if unit_price < 0:
        raise ValueError("unit_price must be a non-negative number")

    country = COUNTRY_NAMES.get(values["country"].casefold())
    if country is None:
        raise ValueError("unrecognized country")

    return {
        "order_id": values["order_id"].upper(),
        "customer_id": values["customer_id"].upper(),
        "order_date": parse_order_date(values["order_date"]),
        "product": values["product"].title(),
        "quantity": quantity,
        "unit_price": f"{unit_price:.2f}",
        "country": country,
        "total": f"{quantity * unit_price:.2f}",
    }


def run_pipeline(input_path, output_path, report_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    seen_order_ids = set()
    cleaned_rows = []
    rejected_rows = 0
    duplicate_rows = 0

    with input_path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        missing_columns = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Input is missing columns: {', '.join(sorted(missing_columns))}")

        for row in reader:
            order_id = (row.get("order_id") or "").strip().upper()
            if order_id and order_id in seen_order_ids:
                duplicate_rows += 1
                continue
            if order_id:
                seen_order_ids.add(order_id)

            try:
                cleaned_rows.append(clean_row(row))
            except ValueError:
                rejected_rows += 1

    output_columns = (*REQUIRED_COLUMNS, "total")
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    report = {
        "input_file": str(input_path),
        "rows_read": len(cleaned_rows) + rejected_rows + duplicate_rows,
        "rows_written": len(cleaned_rows),
        "rows_rejected": rejected_rows,
        "duplicate_rows_removed": duplicate_rows,
        "output_file": str(output_path),
    }
    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)
        report_file.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description="Clean the sample orders CSV dataset.")
    parser.add_argument("--input", default="data/raw_orders.csv")
    parser.add_argument("--output", default="data/cleaned_orders.csv")
    parser.add_argument("--report", default="data/quality_report.json")
    arguments = parser.parse_args()

    report = run_pipeline(arguments.input, arguments.output, arguments.report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()