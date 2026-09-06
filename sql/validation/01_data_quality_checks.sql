-- Data validation checks run against staging before data is promoted to the analytical layer.
-- Each query returns rows that FAIL the rule. An empty result set means the rule passed.

-- 1. Duplicate customer records
SELECT customer_id, COUNT(*) AS record_count
FROM stg_customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- 2. Orphaned accounts: account references a customer_id that does not exist
SELECT a.account_id, a.customer_id
FROM stg_accounts a
LEFT JOIN stg_customers c ON a.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 3. Invalid state codes
SELECT customer_id, state
FROM stg_customers
WHERE state NOT IN (
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY'
);

-- 4. Missing credit score
SELECT customer_id
FROM stg_customers
WHERE credit_score IS NULL;

-- 5. Duplicate transaction records (double-post issue)
SELECT transaction_id, COUNT(*) AS occurrences
FROM stg_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 6. Transactions with a missing transaction_date
SELECT transaction_id, account_id
FROM stg_transactions
WHERE transaction_date IS NULL;

-- 7. Transaction amount outliers -- IQR method rather than a fixed threshold,
--    since a fixed dollar cutoff doesn't hold across account/transaction types.
WITH bounds AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) AS q3
    FROM stg_transactions
)
SELECT t.transaction_id, t.account_id, t.amount
FROM stg_transactions t, bounds b
WHERE t.amount < b.q1 - 3 * (b.q3 - b.q1)
   OR t.amount > b.q3 + 3 * (b.q3 - b.q1);

-- 8. Loans with a term/type mismatch
SELECT loan_id, loan_type, term_months
FROM stg_loans
WHERE (loan_type = 'Mortgage' AND term_months < 60)
   OR (loan_type = 'Auto' AND term_months > 96);
