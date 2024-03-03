# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
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
def value_of_transit():
    """
    Annual dollar value of city's transit infrastructure.

    value_of_transit should be the extra value from living in a location where all errands can be
    accomplished via transit vs living in a location where all errands require a car.

    Internally, we use the formula
        value_of_transit * walkscore_transit_score / 100
    to get the value of transit for a location.

    See https://www.walkscore.com/methodology.shtml for the meaning of Transit Score values from 0 - 100.
    """


# %%
FACTOR_NAME = 'Transit'


def annual_value(loc):
    return value_of_transit() * walkscore.transit_score(loc) / 100


# %% tags=["active-ipynb"]
# annual_value(SEATTLE)
