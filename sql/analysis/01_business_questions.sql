-- Analytical queries answering the business questions this project is scoped around.

-- Q1: Monthly active customer count and net transaction volume by channel
SELECT
    DATE_TRUNC('month', t.transaction_date) AS txn_month,
    t.channel,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    COUNT(*) AS transaction_count,
    ROUND(SUM(t.amount), 2) AS net_amount
FROM fact_transaction t
JOIN dim_account a ON t.account_id = a.account_id
GROUP BY DATE_TRUNC('month', t.transaction_date), t.channel
ORDER BY txn_month, t.channel;

-- Q2: Customer segment profile -- average balance and transaction frequency
SELECT
    c.segment,
    COUNT(DISTINCT a.account_id) AS account_count,
    ROUND(AVG(a.current_balance), 2) AS avg_balance,
    ROUND(AVG(txn_freq.txn_count), 1) AS avg_monthly_transactions
FROM dim_customer c
JOIN dim_account a ON c.customer_id = a.customer_id
LEFT JOIN (
    SELECT account_id, COUNT(*) / 20.0 AS txn_count
    FROM fact_transaction
    GROUP BY account_id
) txn_freq ON a.account_id = txn_freq.account_id
GROUP BY c.segment
ORDER BY avg_balance DESC;

-- Q3: Delinquency rate by risk tier and loan type
SELECT
    rt.risk_tier,
    l.loan_type,
    COUNT(*) AS total_loans,
    SUM(CASE WHEN l.loan_status IN ('Delinquent','Charged Off') THEN 1 ELSE 0 END) AS at_risk_loans,
    ROUND(
        100.0 * SUM(CASE WHEN l.loan_status IN ('Delinquent','Charged Off') THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ) AS delinquency_rate_pct
FROM stg_loans l
JOIN dim_customer_risk_tier rt ON l.customer_id = rt.customer_id
GROUP BY rt.risk_tier, l.loan_type
ORDER BY delinquency_rate_pct DESC;

-- Q4: New-customer cohort retention -- active 6 / 12 months after first account opened
WITH first_account AS (
    SELECT customer_id, MIN(open_date) AS first_open_date
    FROM dim_account
    GROUP BY customer_id
),
cohort AS (
    SELECT customer_id, DATE_TRUNC('quarter', first_open_date) AS cohort_quarter
    FROM first_account
),
activity AS (
    SELECT a.customer_id, DATE_TRUNC('month', t.transaction_date) AS active_month
    FROM fact_transaction t
    JOIN dim_account a ON t.account_id = a.account_id
    GROUP BY a.customer_id, DATE_TRUNC('month', t.transaction_date)
)
SELECT
    c.cohort_quarter,
    COUNT(DISTINCT c.customer_id) AS cohort_size,
    COUNT(DISTINCT CASE WHEN act.active_month >= c.cohort_quarter + INTERVAL '6 months' THEN c.customer_id END) AS active_after_6mo,
    COUNT(DISTINCT CASE WHEN act.active_month >= c.cohort_quarter + INTERVAL '12 months' THEN c.customer_id END) AS active_after_12mo
FROM cohort c
LEFT JOIN activity act ON c.customer_id = act.customer_id
GROUP BY c.cohort_quarter
ORDER BY c.cohort_quarter;

-- Q5: Reconciliation -- transaction-derived balance vs. reported account balance
SELECT
    a.account_id,
    a.current_balance AS reported_balance,
    ROUND(COALESCE(SUM(t.amount), 0), 2) AS transaction_derived_balance,
    ROUND(a.current_balance - COALESCE(SUM(t.amount), 0), 2) AS variance
FROM dim_account a
LEFT JOIN fact_transaction t ON a.account_id = t.account_id
GROUP BY a.account_id, a.current_balance
HAVING ABS(a.current_balance - COALESCE(SUM(t.amount), 0)) > 50
ORDER BY ABS(variance) DESC;
