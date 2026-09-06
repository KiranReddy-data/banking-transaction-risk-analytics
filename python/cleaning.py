"""
Cleaning and transformation logic producing the analytical tables used by the modeling
and EDA scripts. Python equivalent of sql/transformations/, kept independent of a live
database connection so the rest of the pipeline can run without a warehouse.
"""

import pandas as pd
from data_quality_checks import VALID_STATES


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df['state'].isin(VALID_STATES)]
    df = df.sort_values('customer_since').drop_duplicates(subset='customer_id', keep='first')
    return df.reset_index(drop=True)


def clean_accounts(df: pd.DataFrame, valid_customers: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    valid_ids = set(valid_customers['customer_id'])
    return df[df['customer_id'].isin(valid_ids)].reset_index(drop=True)


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(subset=['transaction_date'])
    df = df.drop_duplicates(subset='transaction_id', keep='first')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df.reset_index(drop=True)


def assign_risk_tier(credit_score: float) -> str:
    """FICO-style tiering; matches common industry cutoffs rather than an arbitrary scale."""
    if pd.isna(credit_score):
        return 'Unscored'
    if credit_score < 620:
        return 'Subprime'
    if credit_score < 680:
        return 'Near Prime'
    if credit_score < 740:
        return 'Prime'
    return 'Super Prime'


def build_customer_features(customers: pd.DataFrame, accounts: pd.DataFrame,
                             transactions: pd.DataFrame) -> pd.DataFrame:
    """Roll transaction and account activity up to one row per customer -- the feature
    table the churn model trains on."""
    txn_with_cust = transactions.merge(accounts[['account_id', 'customer_id']], on='account_id', how='inner')

    activity = txn_with_cust.groupby('customer_id').agg(
        total_transactions=('transaction_id', 'count'),
        avg_transaction_amount=('amount', 'mean'),
        last_transaction_date=('transaction_date', 'max'),
        distinct_channels_used=('channel', 'nunique'),
    ).reset_index()

    balances = accounts.groupby('customer_id').agg(
        total_balance=('current_balance', 'sum'),
        account_count=('account_id', 'count'),
    ).reset_index()

    features = customers.merge(activity, on='customer_id', how='left').merge(balances, on='customer_id', how='left')
    features['risk_tier'] = features['credit_score'].apply(assign_risk_tier)

    reference_date = transactions['transaction_date'].max()
    features['days_since_last_transaction'] = (
        pd.to_datetime(reference_date) - pd.to_datetime(features['last_transaction_date'])
    ).dt.days

    # Target definition: a customer is labeled "churned" if there has been no transaction
    # activity in the 90 days before the reference date, or no observed activity at all in
    # the sample window. This is a simplifying definition for this project, not a
    # bank-approved churn definition -- a real deployment would need business sign-off here.
    features['days_since_last_transaction'] = features['days_since_last_transaction'].fillna(999)
    features['churned'] = (features['days_since_last_transaction'] > 90).astype(int)

    features['total_transactions'] = features['total_transactions'].fillna(0)
    features['distinct_channels_used'] = features['distinct_channels_used'].fillna(0)
    features['account_count'] = features['account_count'].fillna(0)
    features['total_balance'] = features['total_balance'].fillna(0)
    features['avg_transaction_amount'] = features['avg_transaction_amount'].fillna(0)

    return features
