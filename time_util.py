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
import datetime as dt


# %%
@configvar(default=dt.date.today())
def today():
    """
    Today's date.

    We fix this value so that generated values don't unexpectedly change. You can remove the file (rm config/today.yaml) in order to update it. It's recommended that you don't check this file in.
    """
