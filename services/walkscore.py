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
from common import UnsupportedCityException, MissingConfigVarException, configvar
import util


# %%
@configvar(type=str)
def walkscore_api_key():
    """API key for walkscore.com.

    Visit https://www.walkscore.com/professional/api-sign-up.php to get a free API key.
    """


@configvar()
def bike_score_estimate():
    """
    Estimated bike score for a location.

    Bike Score only works for some locations (USA and Canada?). For other locations, you can provide an estimate.

    Example config:

        taipei: 70
    """


@configvar()
def transit_score_estimate():
    """
    Estimated transit score for a location.

    Transit Score only works for some locations (USA and Canada?). For other locations, you can provide an estimate.

    Example config:

        taipei: 100
    """


# %%
def fetch_walk_score(loc):
    """Request Walk Score info from Walk Score API"""
    return util.web_get(
        f'https://api.walkscore.com/score?format=json&lat={loc.lat}&lon={loc.lon}&transit=1&bike=1&wsapikey={walkscore_api_key()}'
    ).json()


# %%
def walk_score(loc):
    return fetch_walk_score(loc)['walkscore']


def bike_score(loc):
    try:
        return fetch_walk_score(loc)['bike']['score']
    except KeyError:
        try:
            return bike_score_estimate()[loc.name]
        except (MissingConfigVarException, KeyError):
            raise UnsupportedCityException(
                f'no bike score for {loc}; try creating the bike_score_estimate.yaml config file.'
            )


def transit_score(loc):
    try:
        return fetch_walk_score(loc)['transit']['score']
    except KeyError:
        try:
            return transit_score_estimate()[loc.name]
        except (MissingConfigVarException, KeyError):
            raise UnsupportedCityException(
                f'no transit score for {loc}; try creating the transit_score_estimate.yaml config file.'
            )


# %% tags=["active-ipynb"]
# print(f'{bike_score(NEW_YORK)=}')
# print(f'{bike_score(TAIPEI)=}')
