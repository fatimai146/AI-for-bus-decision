"""Small fixed-effects OLS helper (within transformation + cluster-robust SEs)."""
import numpy as np
import pandas as pd


def demean(df, cols, group):
    return df[cols] - df.groupby(group, sort=False)[cols].transform("mean")


def fe_ols(df, y, xs, fe=None, cluster=None):
    """OLS of y on xs, absorbing one set of fixed effects by demeaning.

    Returns a DataFrame with coef, se, and 95% CI for each x. Standard errors
    are clustered on `cluster` (defaults to the fixed-effect group).
    """
    cols = [y] + xs
    if fe is not None:
        d = demean(df, cols, df[fe])
    else:
        d = df[cols] - df[cols].mean()
    Y = d[y].to_numpy()
    X = d[xs].to_numpy(dtype=float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    resid = Y - X @ beta

    cl = df[cluster or fe] if (cluster or fe) is not None else pd.Series(np.arange(len(df)))
    codes, _ = pd.factorize(cl)
    G = codes.max() + 1
    scores = np.zeros((G, X.shape[1]))
    np.add.at(scores, codes, X * resid[:, None])
    n, k = X.shape
    adj = G / (G - 1) * (n - 1) / max(n - k, 1)
    V = adj * XtX_inv @ (scores.T @ scores) @ XtX_inv
    se = np.sqrt(np.diag(V))
    return pd.DataFrame({
        "term": xs, "coef": beta, "se": se,
        "ci_low": beta - 1.96 * se, "ci_high": beta + 1.96 * se,
    })


def pct(b):
    """Log-point coefficient -> percent difference."""
    return (np.exp(b) - 1) * 100
