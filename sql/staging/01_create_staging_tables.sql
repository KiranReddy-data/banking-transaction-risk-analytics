-- Staging: raw table definitions matching source file structure
-- These mirror what would come from a nightly extract off core banking / loan servicing systems.

CREATE TABLE stg_customers (
    customer_id      VARCHAR(20),
    segment          VARCHAR(30),
    state            VARCHAR(2),
    customer_since   DATE,
    age              INT,
    credit_score     INT
);

CREATE TABLE stg_accounts (
    account_id        VARCHAR(20),
    customer_id       VARCHAR(20),
    account_type      VARCHAR(20),
    open_date         DATE,
    status            VARCHAR(10),
    current_balance   NUMERIC(14,2)
);

CREATE TABLE stg_transactions (
    transaction_id     VARCHAR(20),
    account_id         VARCHAR(20),
    transaction_date   DATE,
    transaction_type   VARCHAR(20),
    amount             NUMERIC(14,2),
    channel            VARCHAR(20)
);

CREATE TABLE stg_loans (
    loan_id            VARCHAR(20),
    customer_id        VARCHAR(20),
    loan_type          VARCHAR(20),
    principal_amount   NUMERIC(14,2),
    origination_date   DATE,
    term_months        INT,
    interest_rate_pct  NUMERIC(5,2),
    loan_status        VARCHAR(20)
);
