import numpy as np
import pandas as pd

from dashboard import compute_returns


def test_compute_returns_uses_log_returns():
    prices = pd.DataFrame({"TEST": [100.0, 110.0, 121.0]})

    returns = compute_returns(prices)

    np.testing.assert_allclose(returns["TEST"].to_numpy(), np.log([1.1, 1.1]))
