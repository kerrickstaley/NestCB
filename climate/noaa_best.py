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
"""
Finds the best NOAA stations for a given location.

Code to find the NOAA stations that are closest to a given location
while also having good data availability/quality.
"""

# %%
from common import logger
from climate.noaa import (
    noaa_df as orig_noaa_df,
    closest_noaa_stations,
    NoNoaaStationData,
    annual_rainfall as orig_annual_rainfall,
)
import functools
import requests
from typing import Optional, Union
import location
from time_util import today
from haversine import haversine
import datetime as dt
from climate._util import parse_since_until_n
import geo
import util

# %%
# This dumb hack seems necessary when tethering on my phone.
# https://stackoverflow.com/a/46972341/785404
requests.packages.urllib3.util.connection.HAS_IPV6 = False

# %%
today().year


# %%
@util.cache_on_disk
def get_best_stations(loc):
    """
    Get best stations near a location.

    Currently just returns the single best station that meets all criteria, or raises if none found.
    """

    begin_year = today().year - 5
    end_year = today().year - 1
    for require_precip_1hr in [True, False]:
        for station in closest_noaa_stations(loc, n=40):
            station_id = f'{station["USAF"]}-{station["WBAN"]}'
            try:
                df = orig_noaa_df(station_id, begin_year=begin_year, end_year=end_year)
            except NoNoaaStationData:
                continue

            checks = [
                {
                    'name': 'dist_km',
                    'value': haversine(
                        loc, (float(station['LAT']), float(station['LON']))
                    ),
                    'limit': 50,
                },
                {
                    'name': 'frac_rows_missing',
                    'value': 1 - len(df) / (365.25 * 24 * (end_year - begin_year + 1)),
                    'limit': 0.03,
                },
                {
                    'name': 'frac_temp_missing',
                    'value': df.temp.isna().mean(),
                    'limit': 0.05,
                },
            ]

            if require_precip_1hr:
                checks.append(
                    {
                        'name': 'frac_precip_1hr_missing',
                        'value': df.precip_1hr.isna().mean(),
                        'limit': 0.05,
                    }
                )
            else:
                checks.append(
                    {
                        'name': 'frac_relative_humidity_missing',
                        'value': df.relative_humidity.isna().mean(),
                        'limit': 0.05,
                    }
                )

            checks_passed = True
            for check in checks:
                if check['value'] > check['limit']:
                    logger.debug(
                        f'skipping station "{station["STATION NAME"]}" ({station_id=} latlon=({station["LAT"]}, {station["LON"]})) because {check["name"]}={check["value"]} > {check["limit"]}'
                    )
                    checks_passed = False
                    break

            if not checks_passed:
                continue

            logger.debug(
                f'selected station "{station["STATION NAME"]}" ({station_id=} latlon=({station["LAT"]}, {station["LON"]}))'
            )
            return [station_id]

    raise RuntimeError("Didn't find any good stations")


# %% tags=["active-ipynb"]
# with util.LoggingContext(logger, 'DEBUG'):
#     print(get_best_stations.__wrapped__(locs.squamish))


# %%
def _wrap_to_take_location(f):
    @functools.wraps(f)
    def ret(
        loc_or_station_ids: Union[location.Location, list[str], str], *args, **kwargs
    ):
        if isinstance(loc_or_station_ids, location.Location):
            station_ids = get_best_stations(loc_or_station_ids)
        else:
            station_ids = loc_or_station_ids

        return f(station_ids, *args, **kwargs)

    return ret


noaa_df = _wrap_to_take_location(orig_noaa_df)
annual_rainfall = _wrap_to_take_location(orig_annual_rainfall)


# %%
def daily_noaa_dfs(
    loc: location.Location,
    since: Optional[dt.date] = None,
    until: Optional[dt.date] = None,
    n: Optional[int] = None,
):
    # n_buffer = 3 because the last few days of data may be partially missing
    since, until = parse_since_until_n(since, until, n, n_buffer=3)

    timezone = geo.city_timezone(loc)

    @functools.cache
    def get_df(begin_year, end_year):
        return noaa_df(loc, begin_year, end_year)

    ret = []
    date = since
    while date <= until:
        # Python's datetime library continues to disappoint in so many ways
        # c.f. https://news.ycombinator.com/item?id=20018827
        begin_dt = timezone.localize(dt.datetime.combine(date, dt.time())).astimezone(
            dt.timezone.utc
        )
        end_dt = timezone.localize(
            dt.datetime.combine(date + dt.timedelta(days=1), dt.time())
        ).astimezone(dt.timezone.utc)

        df = get_df(begin_dt.year, end_dt.year)

        ret.append(df[(begin_dt <= df.dt_utc) & (df.dt_utc < end_dt)])

        date += dt.timedelta(days=1)

    if n is not None:
        ret = ret[:n]

    return ret


# %% tags=["active-ipynb"]
# noaa_df(locs.berkeley, 2018, 2021)

# %% tags=["active-ipynb"]
# annual_rainfall(locs.berkeley, 2018, 2021)
