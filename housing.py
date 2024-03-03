# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from common import logger, UnsupportedCityException, configvar
import functools
import pandas as pd
import geopandas
import shapely
import geo
import numpy as np
import finance
import util


# %%
@configvar(type=lambda x: x)
def housing_marginal_utility_per_month():
    """
    The relative value of different housing configurations.

    Each key in the config gives the relative monthly utility of living in a home with N bedrooms.

    Example config:

        1: -200
        2: 0
        3: 150
        4: 240
        5: 300

    In this example, a 2-bedroom home is the baseline. A 1-bed home has a marginal utility of $-100 / month, which means that you would be indifferent to living in a 2-bedroom apartment with a $800 / mo rent and a 1-bedroom apartment with a $700 / mo rent. Similarly this example config says you would be indifferent between a $800 / mo 2-bed and a $875 / mo 3-bed.

    It doesn't matter what number of bedrooms you use as a baseline; all that matters is the relative values.

    The dataset that this module uses is the Zillow Home Value Index, which only has data for 1, 2, 3, 4, and 5+ bedrooms, so the results will be slightly wrong if your optimal home in a region is a studio or has 5+ bedrooms.
    """


# %% tags=["active-ipynb"]
# housing_marginal_utility_per_month()


# %%
def download_zillow_data(fname):
    with util.web_get_to_file(
        f'https://files.zillowstatic.com/research/public_csvs/zhvi/{fname}'
    ) as f:
        yield f.name


# %%
@functools.cache
def load_zillow_df(aggregation, type):
    """
    Load dataframe for Zillow Home Value Index.

    :param aggregation: One of "City", "Zip", "Neighborhood".
    :param type: e.g. "bdrmcnt_4" for 4-bedroom.
    """
    fname = f'{aggregation}_zhvi_{type}_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
    url = f'https://files.zillowstatic.com/research/public_csvs/zhvi/{fname}'
    with util.web_get_to_file(url) as f:
        return pd.read_csv(f.name)


# %%
load_zillow_df('Zip', 'bdrmcnt_1')


# %%
@functools.cache
def zillow_neighborhoods_df():
    with util.web_get_to_file(
        'https://edg.epa.gov/data/PUBLIC/OEI/ZILLOW_NEIGHBORHOODS/Zillow_Neighborhoods.zip',
        suffix='.zip',
    ) as f:
        return geopandas.read_file('zip://' + str(f.name) + '!ZillowNeighborhoods.gdb')


# %% tags=["active-ipynb"]
# zillow_neighborhoods_df()[lambda df: df.City == 'San Francisco'][lambda df: df.geometry.contains(shapely.Point(-122.4, 37.8))].geometry.iloc[0]


# %%
@util.cache_on_disk
def zillow_neighborhood(latlon):
    lat, lon = latlon
    rows = zillow_neighborhoods_df()[
        lambda df: df.geometry.contains(shapely.Point(lon, lat))
    ]
    if len(rows):
        return rows.iloc[0]
    else:
        return None


# %% tags=["active-ipynb"]
# print(zillow_neighborhood(locs.minneapolis))
# zillow_neighborhood(locs.minneapolis).geometry


# %%
def home_prices(loc):
    nb = zillow_neighborhood(loc)

    try:
        zipcode = geo.get_zipcode(loc.latlon)
    except geo.NoZipCodeException:
        raise UnsupportedCityException('Not in USA')

    ret = {}
    for nbed in range(1, 6):
        df = load_zillow_df('Neighborhood', f'bdrmcnt_{nbed}')
        if nb is not None and len(
            rows := df[lambda df: df.RegionID == int(nb.RegionID)]
        ):
            logger.debug(
                f'loc {loc.name} {nbed}-bed was priced using neighborhood {nb}'
            )
            ret[nbed] = round(rows.iloc[0].iloc[-1])
            continue

        df = load_zillow_df('Zip', f'bdrmcnt_{nbed}')
        rows = df[lambda df: df.RegionName == int(zipcode)]
        if len(rows):
            logger.debug(f'loc {loc.name} {nbed}-bed was priced using ZIP {zipcode}')
            ret[nbed] = round(rows.iloc[0].iloc[-1])
            continue

        ret[nbed] = np.nan

    return ret


# %% tags=["active-ipynb"]
# logger.setLevel('DEBUG')
# print(home_prices(locs.minneapolis))

# %%
tweak = {
    i: finance.annual_dollars_to_capital(12 * housing_marginal_utility_per_month()[i])
    for i in range(1, 6)
}


def home_shadow_prices(loc):
    hp = home_prices(loc)
    return {i: hp[i] - tweak[i] for i in range(1, 6)}


# %% tags=["active-ipynb"]
# home_shadow_prices(locs.san_francisco)

# %% tags=["active-ipynb"]
# home_shadow_prices(locs.berkeley)

# %% tags=["active-ipynb"]
# home_shadow_prices(locs.seattle)

# %%
FACTOR_NAME = 'Housing'


def annual_value(loc):
    shadow_prices = home_shadow_prices(loc)
    non_nan = [p for p in shadow_prices.values() if not np.isnan(p)]

    if not non_nan:
        raise UnsupportedCityException('Not able to compute any house prices')

    return -finance.capital_to_annual_dollars(min(non_nan))
