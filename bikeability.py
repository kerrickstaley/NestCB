# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from common import configvar
from services import walkscore


# %%
@configvar(type=float)
def value_of_bikeability():
    """
    Annual dollar value of city's bike-friendliness.

    value_of_bikeability should be the extra value from living in a location that is extremely
    bike friendly vs living in a location that is not at all bikeable.

    Internally, we use the formula
        value_of_bikeability * walkscore_bikeability_score / 100
    to get the value of bikeability for a location.

    See https://www.walkscore.com/methodology.shtml for the meaning of Bike Score values from 0 - 100.
    """


# %%
FACTOR_NAME = 'Bikeability'


def annual_value(loc):
    return value_of_bikeability() * walkscore.bike_score(loc) / 100


# %% tags=["active-ipynb"]
# annual_value(locs.seattle)
