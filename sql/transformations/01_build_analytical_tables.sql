-- Transformation layer: builds the clean, deduplicated analytical tables that
-- downstream reporting and the Python analysis scripts read from.

-- Deduplicated customer dimension, keeping the first-seen record per customer_id
CREATE TABLE dim_customer AS
SELECT *
FROM (
    SELECT
        c.*,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_since) AS rn
    FROM stg_customers c
    WHERE state IN (
        'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
        'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
        'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
        'VA','WA','WV','WI','WY'
    )
) ranked
WHERE rn = 1;

-- Account dimension restricted to accounts with a valid customer reference
CREATE TABLE dim_account AS
SELECT a.*
FROM stg_accounts a
INNER JOIN dim_customer c ON a.customer_id = c.customer_id;

-- Deduplicated transaction fact table
CREATE TABLE fact_transaction AS
SELECT DISTINCT
    transaction_id, account_id, transaction_date, transaction_type, amount, channel
FROM stg_transactions
WHERE transaction_date IS NOT NULL;

-- Customer credit risk tier, derived from FICO-style bands (620/680/740 cutoffs)
CREATE TABLE dim_customer_risk_tier AS
SELECT
    customer_id,
    credit_score,
    CASE
        WHEN credit_score IS NULL THEN 'Unscored'
        WHEN credit_score < 620 THEN 'Subprime'
        WHEN credit_score < 680 THEN 'Near Prime'
        WHEN credit_score < 740 THEN 'Prime'
        ELSE 'Super Prime'
    END AS risk_tier
FROM dim_customer;

-- Monthly account balance snapshot, rolled forward from transaction activity
CREATE TABLE fact_account_balance_monthly AS
SELECT
    account_id,
    DATE_TRUNC('month', transaction_date) AS balance_month,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY DATE_TRUNC('month', transaction_date)
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance
FROM (
    SELECT account_id, transaction_date, SUM(amount) AS amount
    FROM fact_transaction
    GROUP BY account_id, transaction_date
) daily
GROUP BY account_id, DATE_TRUNC('month', transaction_date), amount;
