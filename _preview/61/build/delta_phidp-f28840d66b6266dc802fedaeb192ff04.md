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

::::{grid} 4

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

:::{grid-item}
```{image} ../../images/logos/wradlib_logo.svg.png
:width: 125px
:alt: wradlib Logo
```
:::

::::


(delta-phidp)=
# Total Differential Phase Shift

This notebook focuses on the estimation of the total differential phase shift, {math}`\Delta \Phi_{DP}^{tot}`, from polarimetric radar observations. 

The estimated {math}`\Delta \Phi_{DP}^{tot}` is an important intermediate quantity in several radar processing tasks, including [attenuation correction](#attenuation-correction-dual-pol).

The algorithm is described in detail in [](https://doi.org/10.1175/1520-0426(2000)017%3C0332:TRPAAT%3E2.0.CO;2),  [](https://doi.org/10.1175/JTECH-D-13-00038.1) and [](https://doi.org/10.1175/JHM-D-14-0066.1).



```{code-cell} python
:tags: [remove-cell]

import cmweather
import numpy as np
import matplotlib.pyplot as plt
import wradlib as wrl
import xarray as xr
import xradar as xd
import fsspec
import icechunk
import holoviews as hv
import hvplot
import hvplot.xarray
import warnings
warnings.filterwarnings("ignore")
```

(delta-phidp-select)=
## Claim Data

We use the ARCO data provided in [](#intro-data-access). Please refer to this notebook for details of access.

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
prefix = "jastrebac_250m"  # dual-pol, 12 × 360 × 1000, 2014 only
# prefix = "jastrebac_500m"  # dual-pol, 12 × 360 × 500,  2017 + 2026

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
)
display(dtree)
root = next(iter(dtree.keys())).split("/")[0] 
```

## Get lowest elevation sweep

First we get the lowest sweep and do some georeferencing.

```{seealso}
- [](xref:wradlib#generated/wradlib.georef.polar.georeference)
- [](xref:wradlib#generated/wradlib.georef.projection.get_earth_projection)
```

```{code-cell} ipython3
swp = (
    dtree[f"{root}/sweep_0"]
    .to_dataset()
    .assign_coords(dtree[root].coords)
    .assign_coords(sweep_mode="azimuth_surveillance")
    .wrl.georef.georeference(crs=wrl.georef.get_earth_projection())
).sel(vcp_time="2014")
swp.x.attrs = xd.model.get_longitude_attrs()
swp.y.attrs = xd.model.get_latitude_attrs()
swp.z.attrs = xd.model.get_altitude_attrs()
display(swp)
```

## Mask with RHOHV

First, we mask with {math}`\rho_{HV}` and/or any other moment you trust to remove unwanted signal.

```{code-cell} ipython3
mask = (swp.RHOHV >= 0.9)
mswp = swp.where(mask)
phimask = mswp.uPhiDP
```
## Estimate {math}`\Delta \Phi_{DP}^{tot}`

Second, we estimate total differential phase shift {math}`\Delta \Phi_{DP}^{tot}`. The range window can be selected according to your data.

```{code-cell} ipython3
dphi = phimask.wrl.dp.delta_phidp(5000.)
display(dphi)
```
## Overview Plots

Let's have a look at the results.

+++

(delta-phidp-time)=
### Select vcp_time index

```{code-cell} ipython3
vcp = 0
```

### Phase over Azimuth

```{code-cell} ipython3
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))
dphi.first.isel(vcp_time=vcp).plot(label="first", ax=ax1)
dphi.last.isel(vcp_time=vcp).plot(label="last", ax=ax1)
ax1.grid()
ax1.legend()
dphi.dphi.isel(vcp_time=vcp).plot(ls="-", marker=".", label="delta", ax=ax2)
ax2.grid()
ax2.legend()
plt.tight_layout()
```

### Polar Domain

```{code-cell} ipython3
fig = plt.figure(figsize=(20, 14))
ax1 = plt.subplot(231, projection="polar")
ax2 = plt.subplot(232, projection="polar")
ax3 = plt.subplot(233, projection="polar")
# set the lable go clockwise and start from the top
ax1.set_theta_zero_location("N")
ax2.set_theta_zero_location("N")
ax3.set_theta_zero_location("N")
# clockwise
ax1.set_theta_direction(-1)
ax2.set_theta_direction(-1)
ax3.set_theta_direction(-1)

theta = np.linspace(0, 2 * np.pi, num=360, endpoint=False)
ax1.plot(theta, dphi.first_idx.isel(vcp_time=vcp), color="b", linewidth=3)
_ = ax1.set_title(r"$\Delta \Phi_{DP}$ - First Index")
ax2.plot(theta, dphi.last_idx.isel(vcp_time=vcp), color="r", linewidth=3)
_ = ax2.set_title(r"$\Delta \Phi_{DP}$ - Last Index")
ax3.plot(theta, dphi.dphi.isel(vcp_time=vcp), color="g", linewidth=3)
_ = ax3.set_title(r"$\Delta \Phi_{DP}^{tot}$")
```

### First and last segments

```{code-cell} ipython3
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
dphi.start_range.isel(vcp_time=vcp).plot(ax=ax1, lw=0.8, c="k")
(dphi.start_range.isel(vcp_time=vcp) + dphi.center_span).plot(ax=ax1, lw=0.8, c="r", ls=":")
dphi.stop_range.isel(vcp_time=vcp).plot(ax=ax1, lw=0.8, c="k")
(dphi.stop_range.isel(vcp_time=vcp) - dphi.center_span).plot(ax=ax1, lw=0.8, c="r", ls=":")
phimask.isel(vcp_time=vcp).plot(ax=ax1, x="azimuth", y="range", cmap="turbo", vmin=90, vmax=300)
ax1.set_title(r"$\Phi_{DP}$ - start/stop")

phimask2 = phimask.where(((phimask.range >= dphi.start_range.isel(vcp_time=vcp)) & (phimask.range <= dphi.start_range.isel(vcp_time=vcp) + dphi.center_span)) |
                         ((phimask.range >= dphi.stop_range.isel(vcp_time=vcp) - dphi.center_span) & (phimask.range <= dphi.stop_range.isel(vcp_time=vcp))))
phimask2.isel(vcp_time=vcp).plot(ax=ax2, x="azimuth", y="range", cmap="turbo", vmin=90, vmax=300)
dphi.start_range.isel(vcp_time=vcp).plot(ax=ax2, lw=0.8, c="k", ls=":")
(dphi.start_range.isel(vcp_time=vcp) + dphi.center_span).plot(ax=ax2, lw=0.8, c="k", ls=":")
dphi.stop_range.isel(vcp_time=vcp).plot(ax=ax2, lw=0.8, c="k", ls=":")
(dphi.stop_range.isel(vcp_time=vcp) - dphi.center_span).plot(ax=ax2, lw=0.8, c="k", ls=":")
ax2.set_title(r"$\Phi_{DP}$ - start/stop - masked")
fig.tight_layout()
```

## Next Steps

You've completed the total differential phase workflow for the selected dataset. Return to [](#phidp-select), select the other case study day, and rerun the notebook.

```{tip}
You might also want to have a look at other elevations. Please choose the wanted sweep at [](#delta-phidp-select).

You might also want to have a look at other time steps. Please choose the wanted time at [](#delta-phidp-time).

You might also save your computed data to disk for later processing.
```



