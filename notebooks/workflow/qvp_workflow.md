---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
  main_language: python
kernelspec:
  display_name: Python 3
  name: python3
---

::::{grid} 3

:::{grid-item}
```{image} ../../images/logos/radar_datatree_logo.png
:width: 150px
:alt: radar datatree Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/xradar_logo.svg
:width: 150px
:alt: xradar Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/Xarray_Icon_Final.svg
:width: 150px
:alt: xarray Logo
```
:::

::::

(qvp-workflow)=
# Quasi-Vertical Profiles (QVP)

Quasi-Vertical Profiles (QVPs) turn the PPI volumes a radar already collects into a time-height view of the atmosphere above it, without needing dedicated RHI scans. The technique was introduced by Ryzhkov et al. [](https://doi.org/10.1175/JTECH-D-15-0020.1): at a single, sufficiently high and fixed elevation angle, reflectivity and the polarimetric moments are averaged around the full azimuthal sweep into one vertical profile, and stacking these profiles in time reveals how the vertical structure evolves as precipitation passes over the radar.

```{code-cell} ipython3
:tags: [remove-cell]

import cmweather
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import icechunk
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
```

## Prerequisites

| Concepts | Importance | Notes |
| --- | --- | --- |
| Xarray Basics | Necessary | Working with radar DataTrees and azimuthal averaging |
| Polarimetric Radar Variables | Helpful | Interpreting ZDR, KDP, RHOHV |

* **Time to learn**: 15 minutes

## Overview

A QVP is the azimuthal mean of a polarimetric moment {math}`X` at a fixed elevation, evolving in time:

```{math}
:label: eq:qvp
\mathrm{QVP}(r, t) = \frac{1}{N_\theta} \sum_{\theta=1}^{N_\theta} X(r, \theta, t)
```

Ryzhkov et al. [](https://doi.org/10.1175/JTECH-D-15-0020.1) used this technique to track the melting layer and dendritic growth zone (roughly -10 to -15 degrees Celsius) as precipitation evolves. In that layer, ice crystals grow into dendrites and begin to aggregate as they fall and partially melt; in a QVP this shows up as a ZDR increase (up to 1.5-2 dB), a RHOHV decrease, and a strong vertical gradient in Z, sometimes accompanied by a nonzero KDP as the vertical phase gradient responds to the changing hydrometeor population. Because a QVP only needs the routine PPI volumes a radar already collects, it lets researchers examine the time evolution of these microphysical processes continuously, and compare polarimetric radar observations directly against vertically pointing remote sensors.

QVPs assume precipitation is approximately uniform in a ring around the radar, so they are most reliable in widespread, layered precipitation. For an isolated convective cell the azimuthal average mixes in-storm and clear-air rays, but the technique remains a useful way to track how a storm's vertical structure evolves as it approaches, passes over, and recedes from the radar — which is why we apply it here to the Jastrebac dual-polarization convective case ([](#convective-case)) rather than the single-polarization data used for [QPE](#qpe-estimation).

(qvp-claim-data)=
## Claim Data

We use the ARCO data provided in [](#intro-data-access).

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
prefix = "jastrebac_500m"  # dual-pol, 12 × 360 × 500, 2017 + 2026 — convective case

storage = icechunk.s3_storage(
    bucket=BUCKET,
    prefix=prefix,
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
repo = icechunk.Repository.open(storage)
dtree = xr.open_datatree(
    repo.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
).sel(vcp_time="2017")
display(dtree)
root = next(iter(dtree.keys())).split("/")[0]
```

## Select the Highest Elevation

QVPs are computed from the steepest routinely available elevation angle: a steeper beam needs less range to reach a given height, which reduces horizontal drift and keeps the assumption that one azimuthal sweep samples a roughly co-located vertical column.

(qvp-select-sweep)=
```{code-cell} ipython3
sweeps = sorted(dtree[root].children, key=lambda s: int(s.split("_")[-1]))
sweep = sweeps[-1]

swp = dtree[f"{root}/{sweep}"].to_dataset(inherit="all_coords")
elevation_deg = float(swp.sweep_fixed_angle.isel(vcp_time=0))
print(f"Using {sweep} at {elevation_deg:.1f}\N{DEGREE SIGN} elevation")
display(swp)
```

## Quality Control

```{note}
A fraction of ``KDP`` gates carry a "no reliable estimate" sentinel value (\N{ALMOST EQUAL TO} -10 deg/km) rather than a physical value. Together with gates where ``RHOHV`` is below 0.7 — unlikely to be meteorological echo — these are excluded before azimuthal averaging.
```

```{code-cell} ipython3
qc_mask = swp.RHOHV >= 0.7
zdr = swp.ZDR.where(qc_mask)
rhohv = swp.RHOHV.where(qc_mask)
kdp = swp.KDP.where(qc_mask & (swp.KDP > -9))
```

## Compute the QVP

Reflectivity must be averaged in linear units and converted back to dB afterwards — averaging directly in dB would bias the mean low, since dB compresses the dynamic range of the underlying (linear) received power. Height above the radar follows from simple trigonometry on the fixed elevation angle and range: {math}`h = r \sin\theta_e`.

```{seealso}
- [](https://doi.org/10.1175/JTECH-D-15-0020.1) — the original QVP formulation
```

```{code-cell} ipython3
def azimuthal_mean(da, is_db=False):
    lin = 10 ** (da / 10) if is_db else da
    out = lin.mean("azimuth", skipna=True)
    return 10 * np.log10(out.where(out > 0)) if is_db else out

elevation = np.deg2rad(elevation_deg)
height = (swp.range * np.sin(elevation) / 1000).assign_attrs(units="km", long_name="Height above radar")

qvp = xr.Dataset(
    {
        "DBZH": azimuthal_mean(swp.DBZH, is_db=True),
        "ZDR": azimuthal_mean(zdr),
        "RHOHV": azimuthal_mean(rhohv),
        "KDP": azimuthal_mean(kdp),
    }
).assign_coords(height=height)
qvp = qvp.where(qvp.height <= 15, drop=True)
display(qvp)
```

## Visualize the Vertical Structure

```{note}
This archive's raw ``ZDR`` and ``KDP`` are not yet bias-corrected — see [](#system_phidp), [](#delta-phidp) and [](#attenuation-correction-dual-pol) for the phase-calibration steps used elsewhere in this course. The panels below are still worth reading for their time-height *structure* — in particular the ``RHOHV`` dip and enhanced ``DBZH``/``ZDR`` as the storm's melting layer and dendritic growth zone evolve — even though their absolute levels reflect this radar's uncorrected system biases.
```

```{code-cell} ipython3
fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True, sharey=True)

qvp.DBZH.plot(ax=axes[0, 0], x="vcp_time", y="height", cmap="HomeyerRainbow", vmin=0, vmax=60)
axes[0, 0].set_title("QVP - Reflectivity (DBZH)")

qvp.ZDR.plot(ax=axes[0, 1], x="vcp_time", y="height", cmap="HomeyerRainbow", vmin=0, vmax=8)
axes[0, 1].set_title("QVP - Differential Reflectivity (ZDR)")

qvp.RHOHV.plot(ax=axes[1, 0], x="vcp_time", y="height", cmap="plasmidis", vmin=0.7, vmax=1)
axes[1, 0].set_title("QVP - Correlation Coefficient (RHOHV)")

qvp.KDP.plot(ax=axes[1, 1], x="vcp_time", y="height", cmap="seismic", vmin=-2, vmax=2)
axes[1, 1].set_title("QVP - Specific Differential Phase (KDP)")

for ax in axes[0, :]:
    ax.set_xlabel("")
for ax in axes[1, :]:
    ax.set_xlabel("Time (UTC)")
    ax.tick_params(axis="x", rotation=30)
for ax in axes[:, 0]:
    ax.set_ylabel("Height (km)")
for ax in axes[:, 1]:
    ax.set_ylabel("")
fig.tight_layout()
```

## Next Steps

You've computed a QVP for the convective case at the highest available elevation. Return to the [``sweep`` selection step](#qvp-select-sweep) to try a lower elevation angle — you'll need a longer range to reach the same height, trading vertical resolution for a wider footprint around the radar.

```{tip}
For a fully bias-corrected polarimetric QVP, apply the phase processing from [](#system_phidp), [](#delta-phidp) and [](#attenuation-correction-dual-pol) to ``swp`` before running the azimuthal averaging step above.
```
