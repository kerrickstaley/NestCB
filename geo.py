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
"""Geography and geometry."""

import pytz
import functools
import geopy
import geopandas
import shapely
import util


# %%
@functools.cache
def _census_block_api(loc):
    return util.web_get(
        f'https://geo.fcc.gov/api/census/block/find?latitude={loc.lat}&longitude={loc.lon}&censusYear=2020&showall=false&format=json'
    ).json()


# %%
def city_to_state_code(city):
    return _census_block_api(city)['State']['code']


# %%
def city_to_county(city):
    """
    Note: Raises KeyError if city is not in the USA.

    Return:
        Name of the county including the word "County", e.g. "San Francisco County".
    """
    return _census_block_api(city)['County']['name']


# %%
@functools.cache
def _timezones_df():
    with util.web_get_to_file(
        'https://github.com/evansiroky/timezone-boundary-builder/releases/download/2023d/timezones.shapefile.zip',
        suffix='.zip',
    ) as f:
        return geopandas.read_file('zip://' + str(f.name))


@util.cache_on_disk
def city_timezone(loc):
    rows = _timezones_df()[lambda df: df.geometry.contains(shapely.Point(loc.lonlat))]
    if not len(rows):
        raise RuntimeError(f'Could not find timezone for {loc}')

    return pytz.timezone(rows.iloc[0].tzid)


# %% tags=["active-ipynb"]
# city_timezone(locs.berkeley)


# %%
@util.cache_on_disk
def _nominatim_reverse(latlon):
    # We cache to comply with Nominatim's terms of service
    # https://operations.osmfoundation.org/policies/nominatim/
    geolocator = geopy.Nominatim(user_agent='NestCB')
    return geolocator.reverse(latlon)


# %%
def get_country_code(latlon):
    return _nominatim_reverse(latlon).raw['address']['country_code']


# %%
class NoStateException(Exception):
    pass


def get_state(latlon):
    addr = _nominatim_reverse(latlon).raw['address']
    if addr['country_code'] != 'us':
        raise NoStateException(f'{latlon=} is not in the USA')
    return addr['state']


# %% tags=["active-ipynb"]
# get_state((37.85353813271663, -122.29008828881683))


# %%
@functools.cache
def _zipcodes_df():
    with util.web_get_to_file(
        'https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip',
        suffix='.zip',
    ) as f:
        return geopandas.read_file('zip://' + str(f.name))


class NoZipCodeException(Exception):
    pass


_NO_ZIP_CODE = '_NO_ZIP_CODE'


@util.cache_on_disk
def _get_zipcode(latlon):
    lat, lon = latlon
    rows = _zipcodes_df()[lambda df: df.geometry.contains(shapely.Point(lon, lat))]

    # Note: We can't directly raise an exception from here because it won't be cached. Instead, we
    # return a special value and have a wrapper function that can raise an exception.
    if not len(rows):
        return _NO_ZIP_CODE

    return rows.iloc[0]['NAME20']


def get_zipcode(latlon):
    ret = _get_zipcode(latlon)
    if ret == _NO_ZIP_CODE:
        raise NoZipCodeException(f'Failed to find ZIP code for {latlon}')
    return ret


# %% tags=["active-ipynb"]
# get_zipcode((37.8, -122.4))

# %% tags=["active-ipynb"]
# get_zipcode((37.85353813271663, -122.29008828881683))
