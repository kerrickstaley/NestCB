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
from typing import NamedTuple
from util import DefaultReprMixin


class Location(NamedTuple):
    name: str
    lat: float
    lon: float

    def _repr_html_(self):
        import folium

        my_map = folium.Map(location=self.latlon, zoom_start=14)
        folium.Marker(self.latlon, popup=self.name).add_to(my_map)
        return my_map._repr_html_()

    @property
    def latlon(self):
        # TODO we don't really need this, can deprecate
        return self.lat, self.lon

    @property
    def lonlat(self):
        return self.lon, self.lat

    def __iter__(self):
        yield self.lat
        yield self.lon

    def __getitem__(self, idx):
        return [self.lat, self.lon][idx]

    def __len__(self):
        return 2

    def __str__(self):
        return self.name


class Polygon(DefaultReprMixin):
    def __init__(self, locs):
        self.locs = locs

    def __eq__(self, other):
        return self.locs == other.locs
