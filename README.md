# Practise_set
Practising skills here. Just for fun.

## Sample ETL Pipeline

This project uses a deterministic, synthetic e-commerce orders dataset with 2,500 rows. It includes mixed date formats, inconsistent text casing and whitespace, invalid values, missing fields, and duplicate order IDs.

Generate or regenerate the input dataset, then run the pipeline:

```bash
python3 generate_dataset.py
python3 etl_pipeline.py
```

The pipeline writes `data/cleaned_orders.csv` and `data/quality_report.json`. It trims and standardizes text, normalizes known country names, parses dates to `YYYY-MM-DD`, validates required fields and numeric values, removes duplicate order IDs, and adds a calculated `total` column. Invalid and duplicate rows are excluded and counted in the report.

Input and output paths can be overridden with `--input`, `--output`, and `--report`.

Create a self-contained KPI dashboard from the cleaned dataset:

```bash
python3 visualize_kpis.py
```

The dashboard is written to `data/kpi_dashboard.html`. It shows revenue, order count, average order value, units sold, and unique customers, with monthly and product/country breakdown charts. It uses only Python's standard library; open the generated HTML file in a browser to view it.
