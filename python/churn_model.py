"""
Churn risk model for retail/small-business banking customers.

Scope note: "churn" here is defined as no observed transaction activity in the 90 days
before the reference date (see cleaning.build_customer_features). A meaningful share of
customers in this synthetic sample have no transactions recorded at all during the
window, which pushes the churn rate higher than a real portfolio would typically show --
that's an artifact of how the sample was generated, not a claim about actual bank
attrition, and is called out explicitly rather than hidden.

Model choice: logistic regression as an interpretable baseline, gradient boosting as
the comparison model. Given class imbalance, accuracy alone isn't a meaningful metric,
so this reports precision, recall, and ROC-AUC.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

from cleaning import clean_customers, clean_accounts, clean_transactions, build_customer_features

NUMERIC_FEATURES = [
    'age', 'credit_score', 'total_transactions', 'avg_transaction_amount',
    'distinct_channels_used', 'total_balance', 'account_count'
]
CATEGORICAL_FEATURES = ['segment', 'risk_tier']


def prepare_dataset(features: pd.DataFrame):
    features = features.dropna(subset=['credit_score']).copy()
    return features[NUMERIC_FEATURES + CATEGORICAL_FEATURES], features['churned']


def build_pipeline(model) -> Pipeline:
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), NUMERIC_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
    ])
    return Pipeline([('preprocess', preprocessor), ('model', model)])


def evaluate(name, pipeline, X_test, y_test):
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]
    print(f"--- {name} ---")
    print(classification_report(y_test, preds, digits=3))
    print(f"ROC-AUC: {roc_auc_score(y_test, probs):.3f}")
    print("Confusion matrix:\n", confusion_matrix(y_test, preds))


def main():
    customers = pd.read_csv('../data/raw/customers_raw.csv')
    accounts = pd.read_csv('../data/raw/accounts_raw.csv')
    transactions = pd.read_csv('../data/raw/transactions_raw.csv')

    clean_cust = clean_customers(customers)
    clean_acct = clean_accounts(accounts, clean_cust)
    clean_txn = clean_transactions(transactions)
    features = build_customer_features(clean_cust, clean_acct, clean_txn)

    X, y = prepare_dataset(features)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    logit = build_pipeline(LogisticRegression(max_iter=1000, class_weight='balanced'))
    logit.fit(X_train, y_train)
    evaluate('Logistic Regression (baseline)', logit, X_test, y_test)

    gbm = build_pipeline(GradientBoostingClassifier(random_state=42))
    gbm.fit(X_train, y_train)
    evaluate('Gradient Boosting', gbm, X_test, y_test)

    scored = features.dropna(subset=['credit_score']).copy()
    scored['churn_probability'] = gbm.predict_proba(scored[NUMERIC_FEATURES + CATEGORICAL_FEATURES])[:, 1]
    scored[['customer_id', 'segment', 'risk_tier', 'churn_probability']] \
        .sort_values('churn_probability', ascending=False) \
        .to_csv('../data/processed/customer_churn_scores.csv', index=False)


if __name__ == '__main__':
    main()
