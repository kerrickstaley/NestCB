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
from common import configvar
from climate import joggability
import requests

# %%
# This dumb hack seems necessary when tethering on my phone.
# https://stackoverflow.com/a/46972341/785404
requests.packages.urllib3.util.connection.HAS_IPV6 = False


# %%
@configvar(return_doc=True)
def value_of_good_weather_day():
    return f"""
    Value of having a day with good weather.

    The dollar value you would pay to experience a day where
    the weather is good enough to do activities outdoors (e.g. jogging) for a
    few hours, as compared to a day with bad weather.

    Example config:

        20

    Currently, our annual value for the climate of a location is based solely
    on how many "joggable" days there are in a year, defined as days where
    there is a window of at least {joggability.MIN_CONSEC_HOURS} hours
    during the daytime where the temperature is between {joggability.MIN_TEMP_C}C
    and {joggability.MAX_TEMP_C}C and there is less than {joggability.MAX_PRECIP_1HR_MM}mm
    of rainfall per hour.

    A location gets value_of_good_weather_day credit for each such day out of the
    365 in the year.

    If you're doing this analysis for mutiple people, sum their values.
    """


def annual_value(loc):
    """Returns annualized dollar value of the city's climate."""
    summary = joggability.can_jog_summary(loc, n=(365 * 5))
    return value_of_good_weather_day() * 365 * summary.normalized().num_yes


FACTOR_NAME = 'Climate'
