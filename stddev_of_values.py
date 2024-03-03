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
from main import compute_results_pd

# %%
df = compute_results_pd()
df

# %%
df.std().sort_values(ascending=False)
