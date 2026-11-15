"""Synthetic demonstration, not a market forecast or backtest."""
import json
import numpy as np
import pandas as pd
import statistical_jump_model as models

if __name__ == "__main__":
    rng = np.random.default_rng(137)
    index = pd.bdate_range("2000-01-03", periods=3000)
    excess = pd.Series(rng.normal(.0003, .012, len(index)), index=index)
    excess.iloc[0] = -.01
    features = models.jump_features(excess)
    fit = models.fit_jump_features(features, excess, penalty=10.)
    state = models.jump_rolling_states(features, fit, np.array([2999]))
    result = {"scope": "one calibration, not full monthly policy", "bull": bool(state.iloc[-1]), "penalty": fit["penalty"]}
    print(json.dumps(result, indent=2, allow_nan=False))
