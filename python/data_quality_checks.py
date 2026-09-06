"""
Data quality checks for the banking analytics pipeline.

Mirrors the SQL validation rules in sql/validation/, but runs in Python so it can be
scheduled as part of ingestion and produce a structured exception report instead of
just a pass/fail query result.
"""

import pandas as pd

VALID_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY'
}


def check_duplicate_ids(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    counts = df[id_col].value_counts()
    dup_ids = counts[counts > 1].index
    return df[df[id_col].isin(dup_ids)].sort_values(id_col)


def check_referential_integrity(child_df: pd.DataFrame, parent_df: pd.DataFrame, key: str) -> pd.DataFrame:
    valid_keys = set(parent_df[key])
    return child_df[~child_df[key].isin(valid_keys)]


def check_invalid_states(df: pd.DataFrame, state_col: str = 'state') -> pd.DataFrame:
    return df[~df[state_col].isin(VALID_STATES)]


def check_nulls(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df[df[col].isna()]


def check_amount_outliers_iqr(df: pd.DataFrame, amount_col: str = 'amount', multiplier: float = 3.0) -> pd.DataFrame:
    """IQR-based outlier bound rather than a fixed dollar cutoff, since a fixed threshold
    doesn't generalize across account types or transaction types."""
    q1, q3 = df[amount_col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    return df[(df[amount_col] < lower) | (df[amount_col] > upper)]


def build_exception_report(customers: pd.DataFrame, accounts: pd.DataFrame,
                            transactions: pd.DataFrame) -> pd.DataFrame:
    """Consolidate all validation checks into a single exception summary -- the kind
    of output that would get emailed to a data owner each morning."""
    exceptions = []
    exceptions.append(('duplicate_customer_id', len(check_duplicate_ids(customers, 'customer_id'))))
    exceptions.append(('orphaned_account_customer_ref', len(check_referential_integrity(accounts, customers, 'customer_id'))))
    exceptions.append(('invalid_state_code', len(check_invalid_states(customers))))
    exceptions.append(('missing_credit_score', len(check_nulls(customers, 'credit_score'))))
    exceptions.append(('duplicate_transaction_id', len(check_duplicate_ids(transactions, 'transaction_id'))))
    exceptions.append(('missing_transaction_date', len(check_nulls(transactions, 'transaction_date'))))
    exceptions.append(('transaction_amount_outlier', len(check_amount_outliers_iqr(transactions.dropna(subset=['amount'])))))

    report = pd.DataFrame(exceptions, columns=['rule', 'failing_records'])
    report['severity'] = report['failing_records'].apply(
        lambda n: 'high' if n > 30 else ('medium' if n > 5 else 'low')
    )
    return report


if __name__ == '__main__':
    customers = pd.read_csv('../data/raw/customers_raw.csv')
    accounts = pd.read_csv('../data/raw/accounts_raw.csv')
    transactions = pd.read_csv('../data/raw/transactions_raw.csv')

    report = build_exception_report(customers, accounts, transactions)
    print(report.to_string(index=False))
    report.to_csv('../data/processed/data_quality_exception_report.csv', index=False)
