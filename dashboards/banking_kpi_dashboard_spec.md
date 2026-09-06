# Banking KPI Dashboard -- Design Specification

Power BI Desktop was not available while building this project, so this is a build
specification rather than a rendered dashboard. It documents the data model, page
layout, and metric definitions the way I would hand them to a BI developer if I
weren't building it myself.

## Data Source

Connects to the analytical tables in `sql/transformations/01_build_analytical_tables.sql`:
`dim_customer`, `dim_account`, `fact_transaction`, `dim_customer_risk_tier`,
`fact_account_balance_monthly`.

## Data Model

Star schema: one fact table (`fact_transaction`) joined to three dimensions
(`dim_customer`, `dim_account`, a date dimension generated from `transaction_date`).
`dim_customer_risk_tier` joins to `dim_customer` on `customer_id` as a role-playing
dimension for risk-based slicing.

## Page 1 -- Executive Summary

- KPI cards: total active customers (current month), net transaction volume,
  average account balance, delinquency rate.
- Trend line: monthly active customers, 13-month rolling window.
- Bar chart: net transaction volume by channel.
- Slicers: date range, customer segment.

## Page 2 -- Customer & Segment Detail

- Table: segment-level account count, average balance, average monthly transactions
  (from `sql/analysis/01_business_questions.sql`, Q2).
- Scatter: credit score vs. total balance, colored by risk tier.
- Drill-down: click a segment to filter the balance trend below.

## Page 3 -- Risk & Delinquency

- Matrix: risk tier x loan type, showing delinquency rate (Q3 in analysis SQL).
- Cohort retention chart: 6-month and 12-month active rate by account-opening
  quarter (Q4 in analysis SQL).

## Page 4 -- Data Quality

- Table sourced from `data/processed/data_quality_exception_report.csv`: rule
  name, failing record count, severity.
- Intent: a stakeholder opening the dashboard should be able to see, at a glance,
  whether the numbers on the other pages should be trusted that day.

## KPI Definitions

| KPI | Definition |
|---|---|
| Active customer | Customer with at least one transaction in the selected period |
| Net transaction volume | Sum of transaction amounts (deposits positive, withdrawals/fees negative) |
| Delinquency rate | (Delinquent + Charged Off loans) / total loans, by risk tier and loan type |
| Churn probability | Model output from `python/churn_model.py`; a ranked risk score, not a certainty |

## Visual Hierarchy Notes

Executive page stays to four KPI cards and two charts max -- a stakeholder should
get the headline in the time it takes to open the tab. Everything else lives one
click deeper on the detail pages.
