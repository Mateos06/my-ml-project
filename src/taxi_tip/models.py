"""Explicit feature allowlist and training-only preprocessing."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .config import FEATURE_GROUPS, FORBIDDEN, SEED


class CategoryStrings(TransformerMixin, BaseEstimator):
    """Normalize mixed numeric/missing categories without learning a vocabulary."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.DataFrame(X).astype("string").fillna("Unknown").astype(str).to_numpy()

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


def feature_columns(groups: list[str]) -> tuple[list[str], list[str]]:
    numeric, categorical = [], []
    for group in groups:
        num, cat = FEATURE_GROUPS[group]
        numeric.extend(num)
        categorical.extend(cat)
    if FORBIDDEN.intersection(numeric + categorical):
        raise ValueError("Post-tip information is forbidden in predictors.")
    return numeric, categorical


def make_pipeline(groups: list[str], model: str = "logistic", depth: int = 4, leaf: int = 200) -> Pipeline:
    numeric, categorical = feature_columns(groups)
    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                              ("scale", StandardScaler())]), numeric),
        ("category", Pipeline([("strings", CategoryStrings()),
                               ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=True))]), categorical),
    ], remainder="drop")
    estimator = (LogisticRegression(C=1.0, max_iter=1500, solver="lbfgs", random_state=SEED)
                 if model == "logistic" else DecisionTreeClassifier(max_depth=depth, min_samples_leaf=leaf, random_state=SEED))
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])


def fit_fare_rule(train: pd.DataFrame) -> dict:
    """An interpretable rule: flag the highest-rate May fare band (n >= 200)."""
    grouped = train.groupby("fare_band").generous_tip.agg(["size", "mean"])
    eligible = grouped.loc[grouped["size"] >= 200]
    if eligible.empty:
        eligible = grouped
    return {"band": str(eligible["mean"].idxmax()), "rates": grouped["mean"].to_dict()}


def rule_scores(frame: pd.DataFrame, rule: dict) -> np.ndarray:
    # Binary rule has two ranks, with May rates as its probability scores.
    positive = frame.fare_band.eq(rule["band"])
    high = float(rule["rates"][rule["band"]])
    low = min(float(v) for v in rule["rates"].values())
    return np.where(positive, high, low)
