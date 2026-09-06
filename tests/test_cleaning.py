"""
Tests for the banking analytics cleaning logic. Run with: pytest tests/
"""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
from cleaning import clean_customers, clean_accounts, clean_transactions, assign_risk_tier


@pytest.fixture
def sample_customers():
    return pd.DataFrame({
        'customer_id': ['C1', 'C1', 'C2', 'C3'],
        'segment': ['Retail', 'Retail', 'Premier', 'Retail'],
        'state': ['GA', 'GA', 'NY', 'XX'],
        'customer_since': ['2020-01-01', '2020-01-01', '2019-06-01', '2021-03-01'],
        'age': [30, 30, 45, 28],
        'credit_score': [680.0, 680.0, 740.0, 600.0],
    })


def test_clean_customers_removes_duplicates(sample_customers):
    result = clean_customers(sample_customers)
    assert result['customer_id'].is_unique


def test_clean_customers_removes_invalid_state(sample_customers):
    result = clean_customers(sample_customers)
    assert 'C3' not in result['customer_id'].values
    assert set(result['state']) <= {'GA', 'NY'}


def test_clean_accounts_drops_orphaned_customer_ref(sample_customers):
    clean_cust = clean_customers(sample_customers)
    accounts = pd.DataFrame({
        'account_id': ['A1', 'A2'],
        'customer_id': ['C1', 'C99'],
        'account_type': ['Checking', 'Savings'],
        'open_date': ['2020-02-01', '2020-02-01'],
        'status': ['Active', 'Active'],
        'current_balance': [1000.0, 500.0],
    })
    result = clean_accounts(accounts, clean_cust)
    assert 'C99' not in result['customer_id'].values
    assert len(result) == 1


def test_clean_transactions_drops_nulls_and_duplicates():
    transactions = pd.DataFrame({
        'transaction_id': ['T1', 'T1', 'T2'],
        'account_id': ['A1', 'A1', 'A1'],
        'transaction_date': ['2024-01-01', '2024-01-01', None],
        'transaction_type': ['Deposit', 'Deposit', 'Fee'],
        'amount': [100.0, 100.0, -5.0],
        'channel': ['Online', 'Online', 'Mobile'],
    })
    result = clean_transactions(transactions)
    assert len(result) == 1
    assert result.iloc[0]['transaction_id'] == 'T1'


def test_assign_risk_tier_bands():
    assert assign_risk_tier(600) == 'Subprime'
    assert assign_risk_tier(650) == 'Near Prime'
    assert assign_risk_tier(700) == 'Prime'
    assert assign_risk_tier(780) == 'Super Prime'
    assert assign_risk_tier(None) == 'Unscored'
