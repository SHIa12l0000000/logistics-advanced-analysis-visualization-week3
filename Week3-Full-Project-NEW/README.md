# Week 3 — Advanced Data Analysis and Visualization in Logistics

**Internship assignment:** Exploratory data analysis, performance KPIs, and Python visualization of a hypothetical last-mile delivery operation.

**Status:** Completed reproducible demonstration | **Data:** 100% synthetic, not a real company dataset.

## Executive overview

Using a seeded simulator, this repository generates 960 fictional parcel shipments over May–July 2026 in six distribution zones, then computes central-tendency and spread statistics, delivery performance KPIs, group comparisons and Pearson correlations. Eight charts are exported as PNGs and included in the accompanying professional Word report.

### Demonstration results (seed = 2026)

| KPI | Value |
| --- | ---: |
| Shipments | 960 |
| On-time delivery rate | 93.44% |
| Average delivery time | 4.23 h |
| 90th-percentile delivery time | 6.63 h |
| Average transport cost per shipment | ₹161.67 |
| Distance vs transport cost Pearson r | +0.941 |
| Low traffic on-time rate | 98.92% |
| High traffic on-time rate | 80.00% |

**Caution:** Patterns are deliberately embedded in the simulator, so these numbers are *not* independently discovered facts, business forecasts, causal estimates or proof of savings. Any real recommendations need validation on real dispatch data.

## Project files

```text
week3-logistics-advanced-analysis-visualization/
├── README.md
├── requirements.txt
├── data_dictionary.md
├── scripts/
│   ├── generate_data.py
│   └── analyze_logistics.py
├── tests/
│   └── test_pipeline.py
├── data/raw/
│   └── simulated_shipments.csv
├── outputs/
│   ├── figures/  (8 .png visualizations)
│   └── tables/   (descriptive stats, daily volume, KPIs, correlations, JSON metrics)
└── report/
    └── Week3_Logistics_Advanced_Analysis_Visualization.docx
```

## Run locally

Requires **Python 3.10+**.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python scripts/generate_data.py --n 960 --seed 2026 --output data/raw/simulated_shipments.csv
python scripts/analyze_logistics.py --input data/raw/simulated_shipments.csv --output-dir outputs
python -m unittest discover -s tests -v
```

Outputs are deterministically created in `outputs/figures/` and `outputs/tables/`. The Word report is a snapshot of the packaged data; run the generator with the supplied seed and sample size for matching statistics. The figure appearance can vary slightly with local Matplotlib versions.

## Visualizations

1. `01_daily_volume.png`: daily shipment trends and seven-day average (line chart)
2. `02_delivery_time_distribution.png`: delivery-time distribution and mean/median (histogram)
3. `03_zone_on_time.png`: reliability by delivery zone (horizontal bar chart)
4. `04_distance_cost.png`: distance vs cost and least-squares trend (scatter chart)
5. `05_traffic_sla_boxplot.png`: SLA margin by traffic conditions (box plot)
6. `06_correlation_matrix.png`: Pearson correlations between numeric measures (heatmap)
7. `07_zone_mean_cost.png`: average cost per shipment by zone (bar chart)
8. `08_service_sla.png`: reliability by standard/priority SLA (bar chart)

## Metric definitions

- **On-time rate:** 100 × number of shipments with actual hours ≤ promised hours / completed shipments.
- **SLA margin (hours):** actual hours − promised hours; positive = late, negative = early.
- **Mean cost per shipment:** total modeled transportation costs / number of shipments.
- **Transport cost correlation:** Pearson r between delivery distance and transportation cost. Association alone does not establish causation.
- **Average daily volume:** total shipments / number of calendar days represented (including days with zero shipments).

## Assumptions and limitations

All shipments are treated as completed. Transport costs are generated synthetic values in INR, not carrier invoices. Transit times are synthetic elapsed hours (not GPS or traffic-API results). There is no fleet capacity, driver-level assignment, vehicle routing, profit, customer identity, geolocation, emission estimate, or real weather feed. The constructed relationships explain why correlations can be strong; they cannot establish real operational effectiveness. The dataset supports EDA illustration only.

## References

- [pandas DataFrame.corr](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html)
- [Matplotlib plot types](https://matplotlib.org/stable/plot_types/index)
- [NumPy random Generator](https://numpy.org/doc/stable/reference/random/generator.html)

**Prepared for:** Week 3 internship submission. **Author:** Bedi Shivam Jagjeet.
