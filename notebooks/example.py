# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Example: ISS ground track
#
# Propagates an embedded TLE with SGP4 and plots the ground track.

# %%
import matplotlib.pyplot as plt
import numpy as np
from skyfield.api import EarthSatellite, load, wgs84

# %%
L1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9005"
L2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391 10009"
ts = load.timescale()
sat = EarthSatellite(L1, L2, "ISS", ts)

# %%
t = ts.utc(2024, 1, 1, 12, np.arange(0, 180))
sub = wgs84.subpoint_of(sat.at(t))

# %%
fig, ax = plt.subplots(figsize=(10, 5))
ax.scatter(sub.longitude.degrees, sub.latitude.degrees, s=4)
ax.set(xlim=(-180, 180), ylim=(-90, 90), xlabel="Longitude [deg]", ylabel="Latitude [deg]")
ax.grid(True)
plt.show()
