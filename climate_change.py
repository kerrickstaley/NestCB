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
from common import UnsupportedCityException
from finance import (
    annual_income,
    DISCOUNT_RATE_PCT,
    capital_to_annual_dollars,
    annual_us_real_gdp_per_capita_growth,
)
import geo
import pandas as pd
from io import StringIO
import functools
import itertools
from time_util import today
import util


# %%
@functools.cache
def _get_hsiang_impactlab_df_inner(path):
    """Get estimated economic impact of climate change.

    Get a dataframe corresponding to graphic 2i in the 2017 paper "Estimating economic damage from climate change in the United States" by Hsiang et al.
    """
    data = util.web_get(f'http://impactlab.org/wp-content/uploads/{path}').text
    # strip some weird garbage off the start of the file
    for i, c in enumerate(data):
        if c.encode('ascii', errors='ignore').decode() == c:
            break
    data = data[i:]
    return pd.read_csv(StringIO(data))


get_hsiang_total_damage_dist_df = functools.partial(
    _get_hsiang_impactlab_df_inner, '2022/09/county_total_damages_by_likelihood.csv'
)
get_hsiang_sector_damage_df = functools.partial(
    _get_hsiang_impactlab_df_inner, '2023/03/county_damages_by_sector.csv'
)
get_hsiang_decile_damage_df = functools.partial(
    _get_hsiang_impactlab_df_inner, '2022/09/decile_total_damages_distribution.csv'
)


@functools.cache
def get_hsiang_regional_weights_df():
    record_id = 581238
    filename = 'allweights.csv'
    data = util.web_get(
        f'https://zenodo.org/record/{record_id}/files/{filename}?download=1'
    ).text
    data = 'Region' + data
    return pd.read_csv(StringIO(data))


# %%
def _get_hsiang_sector_damage_row(loc):
    state_code = geo.city_to_state_code(loc)
    county_name = geo.city_to_county(loc)
    df = get_hsiang_sector_damage_df()
    rows = df[(df['State Code'] == state_code) & (df['County Name'] == county_name)]
    if not len(rows):
        raise ValueError(
            f"Didn't find {state_code=} {county_name=} in the Hsiang dataset"
        )

    if len(rows) > 1:
        raise ValueError(
            f'Found multiple matches for {state_code=} {county_name=} in the Hsiang dataset'
        )

    return rows.iloc[0]


def median_climate_damage_2090_pct(loc):
    """
    Get estimated GDP damage % from climate change in 2090.

    Get the median damage estimate from the 2017 paper "Estimating economic damage from climate change in the United States" by Hsiang et. al. This can roughly be interpreted as the expected percent reduction in GDP due to climate change effects in 2090, but see the paper for a more precise interpretation.

    Return: A float, where 1.0 means 1%.
    """
    return _get_hsiang_sector_damage_row(loc)['Total damages (% county income)']


def gdp_per_capita_2012(loc):
    """
    Get city's approximate GDP per capita in 2012 from the Hsiang paper.

    N.B. This actually returns the GDP per capita of the *county* that the city is in,
    but this is the number we want to use anyway to pair with median_climate_damage_2090_pct.
    """
    return _get_hsiang_sector_damage_row(loc)['County Income (in 2012)']


# %%
@functools.cache
def _scale_factor():
    current_year = today().year
    pv_tot = 0
    for year in itertools.count(current_year):
        dy = year - current_year
        pv = annual_income()
        # Damage is quadratic in time, per Hsiang
        pv *= ((year - current_year) / (2090 - current_year)) ** 2
        # Adjust for future growth
        pv *= (1 + annual_us_real_gdp_per_capita_growth()) ** dy
        # Discount to present
        pv *= (1 - DISCOUNT_RATE_PCT / 100) ** dy
        # We are going to multiply this by a percent on a scale from 1-100
        pv *= 1 / 100

        pv_tot += pv

        if year > current_year + 100 and pv < 1:
            break

    return capital_to_annual_dollars(pv_tot)


# %%
FACTOR_NAME = 'Climate Change'


# TODO this is pretty bad in many ways
# - not taking into account optionality of moving
# - assuming damages are directly proportional to your personal income
#   - most of the damages are mortality, and the value you assign to your life is proportional to
#     income, so this is not bad, but we could improve by using some config var for microlife or compute it somehow
# - probably shoddy finance math, should double-check by picking coworkers' brains
# - lots of uncertainty (need to build a mechanism for sensitivity analysis)
#
# One specific weird thing that this does is assign a value of -1.6k / year to SF and -6.3k / year to Berkeley;
# it seems like their values should be more similar.
def annual_value(loc):
    try:
        return -median_climate_damage_2090_pct(loc) * _scale_factor()
    except ValueError:
        # TODO: This ValueError catch is kinda broad
        raise UnsupportedCityException(f"Can't compute climate change value for {loc}")


# %% tags=["active-ipynb"]
# print(f'{annual_value(locs.des_moines)=}')
# print(f'{annual_value(locs.new_york)=}')
# print(f'{annual_value(locs.seattle)=}')
# print(f'{annual_value(locs.portland)=}')


# %%
def get_elevation(loc):
    """
    Returns the elevation, in meters, of the city.

    Specifically, returns the elevation of the point specified in geo.CITY_LATLONS. This lat/lon is
    supposed to be a representative lat/lon for that city.
    """
    resp = util.web_get(
        f'https://api.open-elevation.com/api/v1/lookup?locations={loc.lat},{loc.lon}'
    )
    return float(resp.json()['results'][0]['elevation'])


# %% tags=["active-ipynb"]
# get_elevation(locs.seattle)
