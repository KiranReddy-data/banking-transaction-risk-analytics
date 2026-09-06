# Banking Transaction & Credit Risk Analytics

## Overview

A retail/small-business banking analytics project covering customer, account, transaction, and loan data. It mirrors the kind of work involved in a Senior Data Analyst banking role -- validating source data, building a clean analytical layer, answering specific business questions in SQL, and building a churn risk model in Python.

**Data**: fully synthetic, generated in Python with NumPy/Pandas. No real customer, account, or transaction data is used or referenced anywhere in this repository.

## Business Problem

A bank's operations, risk, and technology teams pull from the same underlying transaction and account data but ask different questions of it: operations wants channel usage trends, risk wants delinquency signals, and technology wants to know whether the reporting layer can be trusted. This project builds one validated analytical layer that can answer all three.

## Business Questions

1. How does transaction volume and active-customer count trend by channel over time?
2. Which customer segments hold the most value, and how often do they transact?
3. Do the credit risk tiers assigned to customers actually predict loan delinquency?
4. How does customer engagement decay after account opening (cohort retention)?
5. Does the transaction-derived balance reconcile with the reported account balance?
6. Which customers show early signals of going inactive (churn risk)?

## Dataset

Four tables, generated with realistic distributions and intentional data quality issues (duplicates, orphaned foreign keys, nulls, outliers) so the validation layer has something real to catch. Full column definitions are in `docs/data_dictionary.md`. The transaction file committed here is a 9,000-row sample of a larger 45,000-row generated dataset, kept smaller to avoid bloating the repository.

| Table | Rows |
|---|---|
| customers | 2,500 |
| accounts | 3,200 |
| transactions (sampled) | 9,000 |
| loans | 1,400 |

## Data Quality Checks

Every table is validated before being trusted for analysis. Checks are implemented twice -- once in SQL (`sql/validation/01_data_quality_checks.sql`) for a warehouse context, and once in Python (`python/data_quality_checks.py`) for a pipeline context -- and both produce the same categories of exceptions: duplicate IDs, orphaned foreign keys, invalid state codes, missing credit scores, missing transaction dates, and IQR-based amount outliers. These issues are injected on purpose so the checks have something to catch, the same way a real source system hands you imperfect data.

## Data Model

Star schema built in `sql/transformations/`: `fact_transaction` joined to `dim_customer`, `dim_account`, and `dim_customer_risk_tier`. Full layout is described in the dashboard spec.

## SQL Analysis

`sql/analysis/01_business_questions.sql` answers the six business questions above directly, using CTEs, window functions, and a reconciliation query comparing transaction-derived balances against reported balances.

## Python Analysis

- `python/cleaning.py` -- dedup, referential integrity enforcement, feature engineering
- `python/eda.py` -- segment profiling, a Spearman correlation test (credit score vs. balance), and a one-way ANOVA on transaction amount by channel
- `python/churn_model.py` -- logistic regression baseline and gradient boosting comparison for churn risk

## Predictive Model

Churn is defined as no observed transaction activity in the 90 days before the latest date in the sample. On held-out data, gradient boosting outperforms the logistic regression baseline on ROC-AUC. A meaningful share of customers in this synthetic sample never received a randomly-assigned transaction at all, which inflates the apparent churn rate and makes the classification problem easier than it would be with denser real transaction history -- that limitation is noted here rather than left out of the discussion.

## Key Findings

- Private Banking and Premier segments carry meaningfully higher average balances than Retail, as expected, but show lower transaction frequency -- consistent with fewer, larger-value relationships rather than high-volume day-to-day banking.
- Delinquency rate is highest among Subprime-tier personal and auto loans, directionally what the risk tiering is supposed to predict -- a reasonable validation that the tiering logic is doing its job.
- The channel-amount ANOVA shows a statistically significant difference in average transaction size across channels, supporting channel as a real segmentation variable rather than incidental metadata.
- Reconciliation between reported and transaction-derived balances flags a set of accounts with variance over $50 -- in a real system this is the kind of gap that needs a root-cause conversation with the source system owner before a balance-based KPI ships to stakeholders.

## Business Recommendations

- Route reconciliation exceptions to whoever owns the account balance feed before publishing balance-based KPIs on the executive dashboard.
- Treat the churn score as a ranking tool for outreach prioritization, not a hard cutoff -- the 90-day inactivity definition is a starting point that should be reviewed with the retention team.
- Use the delinquency-by-tier breakdown to sanity-check whether current risk tiering thresholds still hold, since Prime-tier delinquency is not negligible in this sample.

## Dashboard

Power BI Desktop wasn't available while building this project, so the dashboard is documented as a build specification rather than a rendered file -- see `dashboards/banking_kpi_dashboard_spec.md` for the full page layout, data model, and KPI definitions.

## Project Structure

```
banking-transaction-risk-analytics/
├── README.md
├── data/
│   ├── raw/                  # synthetic source files
│   └── processed/            # outputs from python scripts (gitignored, regenerate locally)
├── sql/
│   ├── staging/              # raw table DDL
│   ├── transformations/      # star schema build
│   ├── analysis/             # business question queries
│   └── validation/           # data quality SQL checks
├── python/
│   ├── data_quality_checks.py
│   ├── cleaning.py
│   ├── eda.py
│   └── churn_model.py
├── dashboards/
│   └── banking_kpi_dashboard_spec.md
├── docs/
│   └── data_dictionary.md
├── requirements.txt
└── .gitignore
```

## How to Run

```bash
pip install -r requirements.txt
cd python
python data_quality_checks.py   # produces the exception report
python eda.py                   # segment profile, correlation test, ANOVA
python churn_model.py           # trains and evaluates the churn model
```

SQL scripts are written for a Postgres-style dialect (window functions, `DATE_TRUNC`, `PERCENTILE_CONT`) and are meant to be run against a warehouse loaded with the same CSVs -- there's no bundled database in this repo.

## Limitations

- All data is synthetic; findings describe patterns in this generated sample, not real banking behavior.
- The churn label is a simplifying definition for this project, not a validated business definition.
- The dashboard is a specification, not a working file, due to no Power BI Desktop access while building this.

## Future Improvements

- Add a fraud-signal model using transaction sequence features (time between transactions, channel switching) rather than only point-in-time attributes.
- Extend reconciliation logic to handle partial-period balances instead of a single point-in-time comparison.
- Build the dashboard spec out in Power BI once desktop access is available, and replace this document with the actual .pbix file.
