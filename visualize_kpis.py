import argparse
import csv
import html
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


REQUIRED_COLUMNS = {
    "order_id",
    "customer_id",
    "order_date",
    "product",
    "quantity",
    "country",
    "total",
}


def load_orders(input_path):
    with Path(input_path).open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Input is missing columns: {', '.join(sorted(missing_columns))}")

        orders = []
        for row in reader:
            order_date = date.fromisoformat(row["order_date"])
            orders.append(
                {
                    "order_id": row["order_id"],
                    "customer_id": row["customer_id"],
                    "date": order_date,
                    "month": order_date.strftime("%Y-%m"),
                    "product": row["product"],
                    "country": row["country"],
                    "quantity": int(row["quantity"]),
                    "total": Decimal(row["total"]),
                }
            )
    if not orders:
        raise ValueError("Input dataset contains no orders")
    return orders


def format_money(amount):
    return f"${amount:,.2f}"


def svg_bar_chart(items, *, value_key, label_key, horizontal=False, color="#167c72"):
    width, height = 760, 340
    margin = {"top": 18, "right": 24, "bottom": 52, "left": 66}
    plot_width = width - margin["left"] - margin["right"]
    plot_height = height - margin["top"] - margin["bottom"]
    maximum = max((float(item[value_key]) for item in items), default=0)
    maximum = maximum * 1.15 if maximum else 1
    parts = [
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(label_key)} chart">'
    ]

    if horizontal:
        left = 170
        plot_width = width - left - margin["right"]
        row_height = plot_height / max(len(items), 1)
        for tick in range(5):
            x = left + plot_width * tick / 4
            value = maximum * tick / 4
            parts.append(f'<line class="grid" x1="{x:.1f}" y1="{margin["top"]}" x2="{x:.1f}" y2="{margin["top"] + plot_height}"/>')
            parts.append(f'<text class="axis" x="{x:.1f}" y="{height - 14}" text-anchor="middle">{format_money(Decimal(str(value)))}</text>')
        for index, item in enumerate(items):
            y = margin["top"] + index * row_height + row_height * 0.18
            bar_height = row_height * 0.58
            bar_width = plot_width * float(item[value_key]) / maximum
            label = html.escape(str(item[label_key]))
            parts.append(f'<text class="axis label" x="{left - 12}" y="{y + bar_height * 0.72:.1f}" text-anchor="end">{label}</text>')
            parts.append(f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="4" fill="{color}"/>')
            parts.append(f'<text class="bar-value" x="{min(left + bar_width + 8, width - 48):.1f}" y="{y + bar_height * 0.72:.1f}">{format_money(Decimal(str(item[value_key])))}</text>')
    else:
        for tick in range(5):
            y = margin["top"] + plot_height * tick / 4
            value = maximum * (4 - tick) / 4
            parts.append(f'<line class="grid" x1="{margin["left"]}" y1="{y:.1f}" x2="{width - margin["right"]}" y2="{y:.1f}"/>')
            parts.append(f'<text class="axis" x="{margin["left"] - 10}" y="{y + 4:.1f}" text-anchor="end">{format_money(Decimal(str(value)))}</text>')
        slot_width = plot_width / max(len(items), 1)
        bar_width = slot_width * 0.56
        for index, item in enumerate(items):
            bar_height = plot_height * float(item[value_key]) / maximum
            x = margin["left"] + index * slot_width + (slot_width - bar_width) / 2
            y = margin["top"] + plot_height - bar_height
            label = html.escape(str(item[label_key]))
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="4" fill="{color}"/>')
            parts.append(f'<text class="axis" x="{x + bar_width / 2:.1f}" y="{height - 20}" text-anchor="middle">{label}</text>')

    parts.append("</svg>")
    return "".join(parts)


def svg_line_chart(items, *, value_key, label_key, color="#d46b48"):
    width, height = 760, 340
    left, right, top, bottom = 66, 24, 18, 52
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum = max((item[value_key] for item in items), default=0)
    maximum = maximum * 1.15 if maximum else 1
    points = []
    parts = [
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(label_key)} trend chart">'
    ]

    for tick in range(5):
        y = top + plot_height * tick / 4
        value = maximum * (4 - tick) / 4
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}"/>')
        parts.append(f'<text class="axis" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{value:,.0f}</text>')

    for index, item in enumerate(items):
        x = left + plot_width * index / max(len(items) - 1, 1)
        y = top + plot_height * (1 - item[value_key] / maximum)
        points.append(f"{x:.1f},{y:.1f}")
        label = html.escape(str(item[label_key]))
        parts.append(f'<text class="axis" x="{x:.1f}" y="{height - 20}" text-anchor="middle">{label}</text>')

    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    for point in points:
        x, y = point.split(",")
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="white" stroke="{color}" stroke-width="3"/>')
    parts.append("</svg>")
    return "".join(parts)


def build_dashboard(orders):
    revenue = sum((order["total"] for order in orders), Decimal("0"))
    order_count = len({order["order_id"] for order in orders})
    average_order_value = revenue / order_count
    units_sold = sum(order["quantity"] for order in orders)
    customer_count = len({order["customer_id"] for order in orders})
    date_range = f"{min(order['date'] for order in orders).strftime('%b %Y')} to {max(order['date'] for order in orders).strftime('%b %Y')}"

    monthly = defaultdict(lambda: {"revenue": Decimal("0"), "orders": 0})
    product_revenue = defaultdict(lambda: Decimal("0"))
    country_revenue = defaultdict(lambda: Decimal("0"))
    for order in orders:
        monthly[order["month"]]["revenue"] += order["total"]
        monthly[order["month"]]["orders"] += 1
        product_revenue[order["product"]] += order["total"]
        country_revenue[order["country"]] += order["total"]

    month_rows = [
        {
            "label": date.fromisoformat(f"{month}-01").strftime("%b"),
            "revenue": float(values["revenue"]),
            "orders": values["orders"],
        }
        for month, values in sorted(monthly.items())
    ]
    products = [
        {"label": name, "revenue": float(value)}
        for name, value in sorted(product_revenue.items(), key=lambda item: item[1], reverse=True)
    ]
    countries = [
        {"label": name, "revenue": float(value)}
        for name, value in sorted(country_revenue.items(), key=lambda item: item[1], reverse=True)
    ]

    kpis = [
        ("Total revenue", format_money(revenue), "Sum of the cleaned order totals."),
        ("Orders", f"{order_count:,}", "Count of unique order IDs in the cleaned data."),
        ("Average order value", format_money(average_order_value), "Total revenue divided by unique orders."),
        ("Units sold", f"{units_sold:,}", "Sum of quantities across all kept orders."),
        ("Customers", f"{customer_count:,}", "Count of unique customer IDs with an order."),
    ]
    kpi_cards = "".join(
        f'<article class="kpi"><p>{html.escape(label)}</p><strong>{html.escape(value)}</strong>'
        f'<span>{html.escape(description)}</span></article>'
        for label, value, description in kpis
    )

    charts = [
        ("Revenue by month", "Sum of order totals by order month.", svg_bar_chart(month_rows, value_key="revenue", label_key="label", color="#167c72")),
        ("Orders by month", "Number of cleaned orders placed each month.", svg_line_chart(month_rows, value_key="orders", label_key="label")),
        ("Revenue by product", "Order revenue grouped by product.", svg_bar_chart(products, value_key="revenue", label_key="label", horizontal=True, color="#397aa8")),
        ("Revenue by country", "Order revenue grouped by customer country.", svg_bar_chart(countries, value_key="revenue", label_key="label", horizontal=True, color="#c17a28")),
    ]
    chart_panels = "".join(
        f'<section class="panel"><div class="panel-heading"><h2>{title}</h2>'
        f'<p>{description}</p></div>{chart}</section>'
        for title, description, chart in charts
    )

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Orders KPI Dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink: #17312f; --muted: #647774; --paper: #f2f5f2; --line: #e1e8e3; --teal: #167c72; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--paper); color: var(--ink); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 34px max(24px, calc((100vw - 1240px) / 2)); color: #f8fbf7; background-color: #173d3a; background-image: repeating-linear-gradient(135deg, transparent 0 18px, rgba(255,255,255,.035) 18px 19px); }}
    .eyebrow {{ margin: 0 0 8px; color: #a9d8cc; font: 700 12px/1.4 Arial, sans-serif; text-transform: uppercase; letter-spacing: 1.2px; }}
    h1 {{ margin: 0; font-size: 34px; font-weight: 500; }}
    .subtitle {{ margin: 8px 0 0; color: #d5e4de; font: 15px/1.5 Arial, sans-serif; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }}
    .kpi {{ min-height: 136px; padding: 17px 18px; border: 1px solid var(--line); border-top: 3px solid var(--teal); background: #fff; }}
    .kpi p {{ margin: 0 0 10px; color: var(--muted); font: 700 12px/1.4 Arial, sans-serif; text-transform: uppercase; }}
    .kpi strong {{ display: block; margin-bottom: 9px; font: 500 clamp(23px, 2vw, 30px)/1.1 Georgia, serif; overflow-wrap: anywhere; }}
    .kpi span {{ display: block; color: var(--muted); font: 12px/1.45 Arial, sans-serif; }}
    .charts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .panel {{ min-width: 0; padding: 18px 18px 12px; border: 1px solid var(--line); background: #fff; }}
    .panel-heading h2 {{ margin: 0; font-size: 19px; font-weight: 500; }}
    .panel-heading p {{ margin: 5px 0 2px; color: var(--muted); font: 13px/1.5 Arial, sans-serif; }}
    .chart {{ display: block; width: 100%; height: auto; overflow: visible; font-family: Arial, sans-serif; }}
    .grid {{ stroke: #e8eeea; stroke-width: 1; }}
    .axis {{ fill: #6e7f7b; font-size: 11px; }}
    .label {{ font-size: 12px; }}
    .footer {{ padding: 18px 2px 4px; color: var(--muted); font: 12px/1.5 Arial, sans-serif; }}
    @media (max-width: 900px) {{ .kpis {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
    @media (max-width: 640px) {{ header {{ padding: 26px 20px; }} h1 {{ font-size: 29px; }} main {{ padding: 16px; }} .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }} .kpi {{ min-height: 128px; padding: 14px; }} .charts {{ grid-template-columns: 1fr; gap: 10px; }} .panel {{ padding: 15px 10px 8px; }} }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">Sales overview · cleaned orders</p>
    <h1>Orders KPI Dashboard</h1>
    <p class="subtitle">{len(orders):,} valid orders · {date_range}</p>
  </header>
  <main>
    <section class="kpis" aria-label="Key performance indicators">{kpi_cards}</section>
    <div class="charts">{chart_panels}</div>
    <p class="footer">Revenue is based on the cleaned dataset's calculated order total. Duplicate IDs and invalid source rows were excluded during ETL.</p>
  </main>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description="Create a self-contained HTML KPI dashboard from cleaned orders.")
    parser.add_argument("--input", default="data/cleaned_orders.csv")
    parser.add_argument("--output", default="data/kpi_dashboard.html")
    arguments = parser.parse_args()

    orders = load_orders(arguments.input)
    output_path = Path(arguments.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_dashboard(orders), encoding="utf-8")
    print(f"Created KPI dashboard for {len(orders):,} orders at {output_path}")


if __name__ == "__main__":
    main()