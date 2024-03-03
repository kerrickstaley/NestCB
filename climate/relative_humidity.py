import numpy as np


def relative_humidity(temp: float, dew_point: float) -> float:
    rh = 100 * (
        np.exp((17.625 * dew_point) / (243.04 + dew_point))
        / np.exp((17.625 * temp) / (243.04 + temp))
    )
    return rh
