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
import math
from common import configvar
import pandas as pd
import io
import functools
import util


# %%
@configvar(type=float)
def annual_income():
    """
    Total annual income for the group of people in the analysis.
    """


# %%
# TODO this is really naive; can get this from 30-year bond yields instead
DISCOUNT_RATE_PCT = 4.0


# %%
def money_to_utility(m):
    return math.log(m)


def utility_to_money(u):
    return math.exp(u)


# TODO should this hardcoded 25 be 100 / DISCOUNT_RATE_PCT ?
def annual_dollars_to_capital(d):
    return d * 25


def capital_to_annual_dollars(c):
    return c / 25


# %%
def _gdp_growth_df_raw():
    return pd.read_csv(
        io.StringIO(
            util.web_get('https://a.usafacts.org/api/v4/Metrics/csv/116290').text
        )
    )


@functools.cache
def _gdp_growth_df():
    df = _gdp_growth_df_raw()[:1].set_index('Years').T
    df.index = df.index.astype('int')
    df['Annual percent change in real GDP (%)'] = df[
        'Annual percent change in real GDP (%)'
    ].astype('float')
    return df


@functools.cache
def annual_us_real_gdp_growth():
    """
    Compute the average annual US real GDP growth, where e.g. 0.03 means 3% annual growth.
    """
    return (
        _gdp_growth_df()['Annual percent change in real GDP (%)'] + 1
    ).product() ** (1 / len(_gdp_growth_df())) - 1


# %%
def _inflation_df_raw():
    return pd.read_csv(
        io.StringIO(
            util.web_get('https://a.usafacts.org/api/v4/Metrics/csv/27246').text
        )
    )


@functools.cache
def _inflation_df():
    df = _inflation_df_raw()[:1].set_index('Years').T
    df.index = df.index.astype('int')
    df['Average inflation rate (%)'] = df['Average inflation rate (%)'].astype('float')
    return df


@functools.cache
def annual_us_inflation_rate():
    """
    Compute the average annual US inflation rate, where e.g. 0.02 means 2% inflation rate.
    """
    return (_inflation_df()['Average inflation rate (%)'] + 1).product() ** (
        1 / len(_gdp_growth_df())
    ) - 1


# %%
def _population_df_raw():
    return pd.read_csv(
        io.StringIO(
            util.web_get('https://a.usafacts.org/api/v4/Metrics/csv/12818').text
        )
    )


@functools.cache
def _population_df():
    df = _population_df_raw()[:1].set_index('Years').T
    df.index = df.index.astype('int')
    df['Resident Population (People)'] = df['Resident Population (People)'].astype(
        'int'
    )
    return df


@functools.cache
def annual_us_pop_growth_rate():
    """
    Compute the average annual US population growth rate, where e.g. 0.01 means 1% growth rate.
    """
    start_year = _gdp_growth_df().iloc[0].name
    end_year = _gdp_growth_df().iloc[-1].name
    return (
        _population_df().loc[end_year, 'Resident Population (People)']
        / _population_df().loc[start_year, 'Resident Population (People)']
    ) ** (1 / (end_year - start_year)) - 1


@functools.cache
def annual_us_real_gdp_per_capita_growth():
    return (1 + annual_us_real_gdp_growth()) / (1 + annual_us_pop_growth_rate()) - 1


# %% tags=["active-ipynb"]
# print(f'{annual_us_real_gdp_growth()=:.4f}')
# print(f'{annual_us_inflation_rate()=:.4f}')
# print(f'{annual_us_pop_growth_rate()=:.4f}')
# print(f'{annual_us_real_gdp_per_capita_growth()=:.4f}')
