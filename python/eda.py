"""
Exploratory analysis supporting the business questions in sql/analysis/01_business_questions.sql.
Run after cleaning.py has produced the analytical tables.
"""

import pandas as pd
from scipy import stats

from cleaning import clean_customers, clean_accounts, clean_transactions, build_customer_features


def monthly_channel_activity(transactions: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    merged = transactions.merge(accounts[['account_id', 'customer_id']], on='account_id')
    merged['txn_month'] = merged['transaction_date'].dt.to_period('M')
    return merged.groupby(['txn_month', 'channel']).agg(
        active_customers=('customer_id', 'nunique'),
        transaction_count=('transaction_id', 'count'),
        net_amount=('amount', 'sum'),
    ).reset_index()


def segment_profile(customers: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    merged = accounts.merge(customers[['customer_id', 'segment']], on='customer_id')
    return merged.groupby('segment').agg(
        account_count=('account_id', 'count'),
        avg_balance=('current_balance', 'mean'),
        median_balance=('current_balance', 'median'),
    ).reset_index().sort_values('avg_balance', ascending=False)


def credit_score_vs_balance_correlation(features: pd.DataFrame) -> dict:
    """Spearman rather than Pearson since balance is heavily right-skewed."""
    valid = features.dropna(subset=['credit_score', 'total_balance'])
    corr, p_value = stats.spearmanr(valid['credit_score'], valid['total_balance'])
    return {'spearman_corr': round(corr, 3), 'p_value': round(p_value, 4), 'n': len(valid)}


def channel_amount_anova(transactions: pd.DataFrame) -> dict:
    """One-way ANOVA testing whether average transaction amount differs across channels --
    a sanity check before treating channel as a segmentation variable."""
    groups = [g['amount'].values for _, g in transactions.groupby('channel')]
    f_stat, p_value = stats.f_oneway(*groups)
    return {'f_statistic': round(f_stat, 3), 'p_value': round(p_value, 4)}


if __name__ == '__main__':
    customers = pd.read_csv('../data/raw/customers_raw.csv')
    accounts = pd.read_csv('../data/raw/accounts_raw.csv')
    transactions = pd.read_csv('../data/raw/transactions_raw.csv')

    clean_cust = clean_customers(customers)
    clean_acct = clean_accounts(accounts, clean_cust)
    clean_txn = clean_transactions(transactions)
    features = build_customer_features(clean_cust, clean_acct, clean_txn)

    print("Segment profile:")
    print(segment_profile(clean_cust, clean_acct))
    print("\nCredit score vs. balance correlation:")
    print(credit_score_vs_balance_correlation(features))
    print("\nChannel transaction amount ANOVA:")
    print(channel_amount_anova(clean_txn))

    monthly = monthly_channel_activity(clean_txn, clean_acct)
    monthly.to_csv('../data/processed/monthly_channel_activity.csv', index=False)
