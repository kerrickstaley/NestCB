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
from climate.relative_humidity import relative_humidity
import csv
import io
import gzip
from haversine import haversine
import numpy as np
import pandas as pd
import re
import requests
from typing import Optional, Union
import functools
import util

# %%
# This dumb hack seems necessary when tethering on my phone.
# https://stackoverflow.com/a/46972341/785404
requests.packages.urllib3.util.connection.HAS_IPV6 = False


# %%
class NoNoaaStationData(RuntimeError):
    pass


def _parse_isd_latlon(s):
    """Parse a lat/lon value from the isd-history.csv file from NOAA."""
    s = s.strip()
    if s == '':
        return None

    if re.search(r'^(\+|-)0*\.0*$', s):
        return None

    # strip leading zeroes
    s = re.sub(r'^(\+|-)0+', r'\1', s)
    return float(s)


@functools.cache
def noaa_isd_history_csv_parsed():
    with util.web_get_to_file(
        'https://noaa-isd-pds.s3.amazonaws.com/isd-history.csv'
    ) as f:
        with open(f.name, 'r') as h:
            return list(csv.DictReader(h))


def closest_noaa_stations(loc, n=1):
    dist_lines = []
    for line in noaa_isd_history_csv_parsed():
        isd_lat = _parse_isd_latlon(line['LAT'])
        isd_lon = _parse_isd_latlon(line['LON'])
        if isd_lat is None or isd_lon is None:
            continue
        dist = haversine(loc, (isd_lat, isd_lon))
        dist_lines.append((dist, line))

    # We could reduce time complexity slightly by using sortedcontainers.SortedList but want to avoid the dep
    dist_lines.sort(key=lambda pair: pair[0])

    return [line for dist, line in dist_lines[:n]]


# %% tags=["active-ipynb"]
# closest_noaa_stations(locs.seattle, n=5)


# %%
def _combine_noaa_dfs(dfa, dfb):
    """
    Combine the data from multiple NOAA ISD dataframes from the same city.
    """
    _a = '_a'
    _b = '_b'
    df = dfa.merge(dfb, suffixes=[_a, _b], on='dt_utc', how='outer')
    fields = [
        'temp',
        'dew_point',
        'precip_1hr',
        'relative_humidity',
    ]

    for field in fields:
        df[field] = (df[field + _a] + df[field + _b]) / 2
        ana = df[field + _a].isna()
        bna = df[field + _b].isna()
        df.loc[ana, field] = df.loc[ana, field + _b]
        df.loc[bna, field] = df.loc[bna, field + _a]

    drop_fields = [field for field in df if field.endswith(_a) or field.endswith(_b)]
    return df.drop(columns=drop_fields).sort_values(by='dt_utc').reset_index(drop=True)


# %%
def _noaa_df_for_year(station_id: str, year: int):
    """
    Internal routine to download NOAA data for a single station and year.

    Params:
    - city_or_stations: e.g. ['997271-99999'] for Manhattan - Battery Park or NEW_YORK to average
      all stations configured for New York.
    """
    UNKNOWN = -9999
    # We use this S3 mirror of https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite because the original site
    # has reliability problems.
    url = f'https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/{year}/{station_id}-{year}.gz'
    # The field widths in the documentation at https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.pdf are wrong :(
    # They sometimes include the extra space and sometimes don't
    names_widths = [
        ('year', 4),
        ('month', 3),
        ('day', 3),
        ('hour', 3),
        ('temp', 6),
        ('dew_point', 6),
        ('pressure', 6),
        ('wind_dir', 6),
        ('wind_speed', 6),
        ('sky_coverage', 6),
        ('precip_1hr', 6),
        ('precip_6hr', 6),
    ]
    # Pandas can directly open url (which is pretty neat!). But in order to get caching we load it through requests.
    resp = util.web_get(url)
    if resp.status_code == 404:
        raise NoNoaaStationData(f'Got 404 for {url}!')

    df = pd.read_fwf(
        io.StringIO(gzip.decompress(resp.content).decode('utf8')),
        names=[name for name, width in names_widths],
        widths=[width for name, width in names_widths],
    )

    for name, _ in names_widths[4:]:
        df.loc[df[name] == UNKNOWN, name] = np.nan

    for col in [
        'temp',
        'dew_point',
        'pressure',
        'wind_speed',
        'precip_1hr',
        'precip_6hr',
    ]:
        df[col] /= 10

    df['relative_humidity'] = relative_humidity(df['temp'], df['dew_point'])

    df['dt_utc'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']], utc=True)

    return df


# %%
def noaa_df(
    station_ids: Union[list[str], str], begin_year: int, end_year: Optional[int] = None
):
    """
    Download NOAA data for a single year or range of years.

    Year range is inclusive.

    Params:
    - station_ids: e.g. '997271-99999' for Manhattan - Battery Park or NEW_YORK for Central Park
    - begin_year: First year to download data for.
    - end_year: Last year to download data for (inclusive). If None, only data for begin_year will be returned.
    """
    if isinstance(station_ids, str):
        station_ids = [station_ids]

    if end_year is None:
        end_year = begin_year

    merged_df = None
    for station_id in station_ids:
        yearly_dfs = []
        for year in range(begin_year, end_year + 1):
            try:
                yearly_dfs.append(_noaa_df_for_year(station_id, year))
            except NoNoaaStationData:
                continue

        if not yearly_dfs:
            raise NoNoaaStationData('Did not find data for any of the requested years')

        station_df = pd.concat(yearly_dfs)

        if merged_df is None:
            merged_df = station_df
        else:
            merged_df = _combine_noaa_dfs(merged_df, station_df)

    return merged_df


# %%
def annual_rainfall(station_ids, start_year, end_year=None):
    # Note: If you set end_year to the current year you will get wrong results.
    if end_year is None:
        end_year = start_year

    df = noaa_df(station_ids, start_year, end_year)
    # TODO figure out if we can tighten this 0.1 threshold for NYC
    assert df.precip_1hr.isna().mean() < 0.1

    return df[~df.precip_1hr.isna()].precip_1hr.sum() / (end_year - start_year + 1)
