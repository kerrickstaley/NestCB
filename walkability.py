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
def value_of_walkability():
    """
    Annual dollar value of location's walkability.

    value_of_walkability should be the extra value from living in a location that is extremely
    walkable vs living in a location that is not at all walkable.

    Internally, we use the formula
        value_of_walkability * walkscore / 100
    to get the value of walkability for a location.

    See https://www.walkscore.com/methodology.shtml for the meaning of Walk Score values from 0 - 100.
    """


# %%
FACTOR_NAME = 'Walkability'


def annual_value(loc):
    return value_of_walkability() * walkscore.walk_score(loc) / 100


# %% tags=["active-ipynb"]
# annual_value(SEATTLE)
