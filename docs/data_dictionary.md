# Data Dictionary -- Banking Transaction & Risk Analytics

## customers_raw.csv

| Column | Type | Description |
|---|---|---|
| customer_id | string | Unique customer identifier |
| segment | string | Retail, Small Business, Premier, Private Banking |
| state | string | 2-letter US state code (some records contain invalid codes -- see data quality checks) |
| customer_since | date | Date the customer relationship began |
| age | int | Customer age |
| credit_score | int | FICO-style score, 300-850 (some records are null) |

## accounts_raw.csv

| Column | Type | Description |
|---|---|---|
| account_id | string | Unique account identifier |
| customer_id | string | Foreign key to customers (a small number of records reference a non-existent customer) |
| account_type | string | Checking, Savings, Money Market, CD |
| open_date | date | Account opening date |
| status | string | Active, Closed, Dormant |
| current_balance | float | Reported current balance |

## transactions_raw.csv

| Column | Type | Description |
|---|---|---|
| transaction_id | string | Unique transaction identifier (a small number are duplicated -- see validation) |
| account_id | string | Foreign key to accounts |
| transaction_date | date | Date of transaction (a small number are null) |
| transaction_type | string | Deposit, Withdrawal, Transfer, POS Purchase, ACH, Fee |
| amount | float | Signed amount; deposits positive, withdrawals/fees negative |
| channel | string | Branch, Online, Mobile, ATM, Call Center |

Note: the committed file is a sampled subset of a larger generated dataset,
kept smaller so the repository stays lightweight. Generation logic (with the
original row count and injected data quality issues) is described in the README.

## loans_raw.csv

| Column | Type | Description |
|---|---|---|
| loan_id | string | Unique loan identifier |
| customer_id | string | Foreign key to customers |
| loan_type | string | Auto, Mortgage, Personal, Home Equity, Credit Card |
| principal_amount | float | Original loan principal |
| origination_date | date | Loan origination date |
| term_months | int | Loan term in months |
| interest_rate_pct | float | Annual interest rate |
| loan_status | string | Current, Delinquent, Charged Off, Paid Off |

## Known data quality issues (intentionally present, used to test the validation layer)

- Duplicate customer records
- Missing credit scores
- Invalid state codes ("XX")
- Accounts referencing a customer_id that does not exist
- Duplicate transaction records
- Transactions with a missing date
- Transaction amount outliers (100-500x normal magnitude)
