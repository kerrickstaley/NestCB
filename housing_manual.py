# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
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
"""
Module allowing you to manually assign housing costs.

If you enable both this module and housing.py, the results from the two modules will be averaged.

Methodology: We can define an "ideal" home as one which would excel at all functions that we want the home to do, and yet would be affordable in a low-cost-of-living area. Then, we could look at the cost of this home in all the cities under consideration. However, for high cost of living areas, this will overestimate the true cost of housing, because realistically in HCOL areas we would choose to live in a cheaper home and sacrifice some of the features of the ideal home.

The true cost of housing in a HCOL is the cost of that cheaper home plus the disutility of not living in the ideal home. This disutility is not quantifiable, but it is by definition greater than zero and also less than (cost of ideal home) - (cost of cheaper home) (if it exceeded this difference we would choose to live in the ideal home). Therefore the true cost of housing is bounded on the low end by the cost of the realistic home and on the high end by the cost of the ideal home.

To estimate the true cost of housing we average the cost of the cheaper home and the cost of the realistic home. We do this average in utility (i.e. logarithmic) space to minimize the expected error in utility units. In other words, we take the geometric mean instead of the arithmetic mean of the prices.
"""

from common import UnsupportedCityException, configvar, locs
import finance
from typing import NamedTuple, Any


# %%
class IdealRealistic(NamedTuple):
    ideal: Any
    realistic: Any


# %%
@configvar(
    type=lambda x: x,
    globals={loc.name: loc.name.upper() for loc in locs.__dict__.values()},
)
def ideal_realistic_home_prices():
    """
    The prices of ideal and realistic homes in each city.

    An "ideal" home is one which would excel at all functions that you want the home to do, and yet would be affordable in a low-cost-of-living area. A realistic home is the home that you would likely buy given the cost constraints of a city. These two prices are used to come up with an overall estimate of the cost of housing of the city (see the module docstring in housing_manual.py for more info).

    To use this module you need to manually determine these prices using e.g. Zillow.

    This configvar is a dict of {city: (ideal_home_price, realistic_home_price)} values. You must define it in a .py file and not a YAML file.

    Example config value:

        {
            seattle: (1_400_000, 800_000),
            des_moines: (600_000, 600_000),
        }

    TODO: Get rid of this weird requirement to make it a .py file and just make it a plain dict that can be defined in YAML.
    """


# %%
def avg_cost(city):
    try:
        prices = ideal_realistic_home_prices()[city]
    except KeyError:
        raise UnsupportedCityException(
            f'{city} is not in ideal_realistic_home_prices()'
        )
    utils = [finance.money_to_utility(m) for m in prices]
    avg_util = sum(utils) / len(utils)
    avg_price = finance.utility_to_money(avg_util)
    return avg_price


# %%
FACTOR_NAME = 'Housing'


# %%
def annual_value(loc):
    city = loc.name.upper()
    # TODO take into account property taxes
    # Property taxes can be as high as 1/2 of the cost of the house itself.
    return -finance.capital_to_annual_dollars(avg_cost(city))
