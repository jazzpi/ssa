# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Closest approach analysis between COSMOS-2612 and ICEYE-X36
#
# Around early-mid October 2026, COSMOS-2612 performed a series of maneuvers to line up a close
# approach to ICEYE-X36 (see [Marco Langbroek's blog](
# https://sattrackcam.blogspot.com/2026/10/kosmos-2612-and-iceye-x36-worrisome-cat.html)).
#
# This notebook investigates the closest approach of the two satellites on 2026-10-18.
#
# ## Elsets
#
# I queried the elsets between 2026-10-17 and 2026-10-19 with this Space-Track query:
#
# [`https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/59103,68762/EPOCH/>now-3/orderby/NORAD_CAT_ID asc/emptyresult/show/format/csv`](https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/59103,68762/EPOCH/>now-3/orderby/NORAD_CAT_ID%20asc/emptyresult/show/format/csv)
#
# We can then read this file and find the time spans where each `(iceye, cosmos)` elset pair is the latest one available:

# %%
import numpy as np
import pandas as pd

START = pd.to_datetime("2026-10-17 00:00:00")
DURATION = pd.Timedelta(days=3)
END = START + DURATION
ICEYE_ID = 59103
COSMOS_ID = 68762
# Elsets from Space-Track
ELSET_PATH = "../data/cosmos-2612-iceye-x36.csv"

# Read & separate the elsets
elsets = pd.read_csv(ELSET_PATH)
iceye_elsets = elsets[elsets["NORAD_CAT_ID"] == ICEYE_ID]
iceye_elsets.reset_index(drop=True, inplace=True)
cosmos_elsets = elsets[elsets["NORAD_CAT_ID"] == COSMOS_ID]
cosmos_elsets.reset_index(drop=True, inplace=True)
iceye_epochs = pd.to_datetime(iceye_elsets["EPOCH"])
cosmos_epochs = pd.to_datetime(cosmos_elsets["EPOCH"])
iceye_epochs = iceye_epochs.sort_values()
cosmos_epochs = cosmos_epochs.sort_values()

# Find ranges where each (iceye, cosmos) elset pair is the latest one available
def latest_elset(epochs: pd.Series, times: pd.Series) -> np.ndarray:
    """Index label of the newest elset with epoch <= each time, or -1 if none yet."""
    pos = np.searchsorted(epochs.to_numpy(), times.to_numpy(), side="right") - 1
    labels = epochs.index.to_numpy()
    return np.where(pos >= 0, labels[np.maximum(pos, 0)], -1)


edges = np.unique(
    np.concatenate(
        [
            [START.to_datetime64(), END.to_datetime64()],
            iceye_epochs.to_numpy(),
            cosmos_epochs.to_numpy(),
        ]
    )
)
edges = edges[(edges >= START.to_datetime64()) & (edges <= END.to_datetime64())]

ranges = pd.DataFrame({"start": edges[:-1], "end": edges[1:]})
ranges["iceye"] = latest_elset(iceye_epochs, ranges["start"])
ranges["cosmos"] = latest_elset(cosmos_epochs, ranges["start"])
# Ranges before either satellite's first elset can't be propagated
ranges = ranges[(ranges["iceye"] >= 0) & (ranges["cosmos"] >= 0)].reset_index(drop=True)
# %% [markdown]
# ## Propagation
#
# Now, we can propagate the elements for the whole three-day range at 10s intervals and calculate the distance / velocity between the two satellites at each time.

# %%
from skyfield.api import EarthSatellite, load

# Build the time series for each elset pair
STEP_S = 10
ts = load.timescale()
range_times = []
for r in ranges.itertuples():
    secs = np.arange(0, (r.end - r.start).total_seconds(), STEP_S)
    s = pd.Timestamp(r.start)
    range_times.append(ts.utc(s.year, s.month, s.day, s.hour, s.minute, s.second + secs))

# Build skyfield objects for each elset
iceye = [EarthSatellite.from_omm(ts, iceye_elsets.loc[i]) for i in iceye_elsets.index]
cosmos = [EarthSatellite.from_omm(ts, cosmos_elsets.loc[i]) for i in cosmos_elsets.index]

all_t = []
all_dist = []
all_vel = []

for r, tt in zip(ranges.itertuples(), range_times):
    all_t.append(tt.utc_datetime())
    # Propagate both satellites
    range = (iceye[r.iceye] - cosmos[r.cosmos]).at(tt)
    # Let skyfield calculate the relative distance
    all_dist.append(range.distance().m)
    # Let skyfield calculate the relative velocity
    all_vel.append(np.linalg.norm(range.velocity.m_per_s, axis=0))

# Merge the results for each elset pair time range into single arrays
all_t = np.concatenate(all_t)
all_dist = np.concatenate(all_dist)
all_vel = np.concatenate(all_vel)

# %% [markdown]
# ## Results
#
# Now we can find the minimum distance and what time it occured:

# %%
min_dist_idx = np.argmin(all_dist)
min_dist_time = all_t[min_dist_idx]
min_dist_value = all_dist[min_dist_idx]
min_dist_vel = all_vel[min_dist_idx]

print(f"Minimum distance occurs at {min_dist_time}")
print(f"Minimum distance value: {min_dist_value:.1f} m")
print(f"Relative velocity at minimum distance: {min_dist_vel:.3f} m/s")

# Find elsets at the time of minimum distance
range_ends = np.cumsum([len(tt) for tt in range_times])
min_dist_range = ranges.iloc[np.searchsorted(range_ends, min_dist_idx, side="right")]
for name, elset in [
    ("ICEYE-X36", iceye_elsets.loc[min_dist_range["iceye"]]),
    ("COSMOS-2612", cosmos_elsets.loc[min_dist_range["cosmos"]]),
]:
    print(f"\n{name} elset (epoch {elset['EPOCH']}):")
    print(elset["TLE_LINE1"])
    print(elset["TLE_LINE2"])

# %% [markdown]
# ## Plots
#
# And of course, we can plot separation/velocity over time:

# %%
import matplotlib.pyplot as plt

fig, (dist, ep) = plt.subplots(2, 1, figsize=(10, 10), sharex=True, height_ratios=[8, 2])
fig.suptitle(
    "Close approach between COSMOS-2612 vs ICEYE-X36"
)

(l_dist,) = dist.plot(all_t, all_dist / 1e3, color="tab:blue")
dist.set_ylabel("Distance [km]", color=l_dist.get_color())
dist.grid(True)

vel = dist.twinx()
(l_vel,) = vel.plot(all_t, all_vel, color="tab:orange")
vel.set_ylabel("Relative velocity [m/s]", color=l_vel.get_color())

# Draw distance over velocity
dist.set_zorder(vel.get_zorder() + 1)
dist.patch.set_visible(False)
dist.set_axisbelow(True)

epoch_rows = [
    ("ICEYE-X36", iceye_epochs.dt.tz_localize("UTC").dt.to_pydatetime()),
    ("COSMOS-2612", cosmos_epochs.dt.tz_localize("UTC").dt.to_pydatetime()),
]
ep.eventplot([e for _, e in epoch_rows], lineoffsets=[0, 1], linelengths=0.8)
ep.set_yticks([0, 1], [name for name, _ in epoch_rows])
ep.set_xlim(all_t[0], all_t[-1])
ep.set_xlabel("Time")
ep.grid(True, axis="x")
ep.set_title("Elset updates")
plt.show()

# %% [markdown]
# We can see discrete jumps in the separation when the elsets update. But the large separation on 2026-10-19 hides the interesting part. Let's plot only up to 2026-10-18T08:00 (when the first big jump in separation occurs):

# %%
PLOT_END = pd.Timestamp("2026-10-18T08:00", tz="UTC")
mask = all_t <= PLOT_END

fig, (dist, ep) = plt.subplots(2, 1, figsize=(10, 10), sharex=True, height_ratios=[8, 2])
fig.suptitle(
    "Close approach between COSMOS-2612 vs ICEYE-X36"
)

(l_dist,) = dist.plot(all_t[mask], all_dist[mask], color="tab:blue")
dist.set_ylim(0, 2000)
dist.set_ylabel("Distance [m]", color=l_dist.get_color())
dist.grid(True)

vel = dist.twinx()
(l_vel,) = vel.plot(all_t[mask], all_vel[mask], color="tab:orange")
vel.set_ylim(0, 2)
vel.set_ylabel("Relative velocity [m/s]", color=l_vel.get_color())

# Draw distance over velocity
dist.set_zorder(vel.get_zorder() + 1)
dist.patch.set_visible(False)
dist.set_axisbelow(True)

ep.eventplot([e for _, e in epoch_rows], lineoffsets=[0, 1], linelengths=0.8)
ep.set_yticks([0, 1], [name for name, _ in epoch_rows])
ep.set_xlim(all_t[0], all_t[-1])
ep.set_xlabel("Time")
ep.grid(True, axis="x")
ep.set_title("Elset updates")

dist.set_xlim(all_t[0], PLOT_END)
plt.show()

# %% [markdown]
# The elsets don't tell us when COSMOS-2612 performed its maneuver(s) to increase the separation, but clearly it was some time before the first large jump in separation ~2026-10-18 08:00. Still, it is interesting to note that the jump to the very low separation (~2026-10-18 04:30) happened due to an update in the ICEYE-X36 elset, not the COSMOS-2612 ones.
