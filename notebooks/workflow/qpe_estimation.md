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

(qpe-estimation)=
# Quantitative Precipitation Estimation (QPE)

Quantitative Precipitation Estimation converts radar reflectivity into rain rate and, by integrating over time, rainfall accumulation. The Marshall & Palmer [](https://doi.org/10.1175/1520-0469(1948)005%3C0165:TDORWS%3E2.0.CO;2) power-law Z-R relationship is the simplest and most widely used approach, and performs best in widespread, layered (stratiform) precipitation where drop-size distributions are relatively uniform — the case used here.

```{code-cell} ipython3
:tags: [remove-cell]

import numpy as np
import wradlib as wrl
import matplotlib.pyplot as plt
import xarray as xr
import xradar as xd
import icechunk
import cmweather
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
```

## Prerequisites

| Concepts | Importance | Notes |
| --- | --- | --- |
| Xarray Basics | Necessary | Working with radar DataTrees |
| Weather Radar Fundamentals | Helpful | Reflectivity and Z-R relationships |

* **Time to learn**: 15 minutes

## Overview

Marshall & Palmer [](https://doi.org/10.1175/1520-0469(1948)005%3C0165:TDORWS%3E2.0.CO;2) measured raindrop size distributions in stratiform rain at McGill University and found they closely follow an exponential form,

```{math}
:label: eq:dsd
N(D) = N_0\,e^{-\Lambda D}
```

with {math}`N_0 \approx 8000\ \mathrm{m}^{-3}\,\mathrm{mm}^{-1}` roughly constant and {math}`\Lambda` decreasing as rain rate {math}`R` increases. Integrating this drop-size distribution to get the radar reflectivity factor {math}`Z` (the sixth moment of {math}`D`) and the rain rate {math}`R` (related to the third moment and fall speed) separately, then eliminating {math}`\Lambda`, yields a power-law relationship between the two:

```{math}
:label: eq:zr
Z = a R^b \quad\Longleftrightarrow\quad R = \left(\frac{Z}{a}\right)^{1/b}
```

with their now-classic coefficients {math}`a=200`, {math}`b=1.6` ({math}`Z` in {math}`\mathrm{mm}^6\,\mathrm{m}^{-3}`, {math}`R` in {math}`\mathrm{mm\,h}^{-1}`). Because these coefficients were fit to a stratiform-rain drop-size distribution, they shouldn't be assumed to hold in convective rain or snow, where the particle-size distribution differs substantially — other {math}`a`, {math}`b` pairs exist for those regimes, and dual-polarization estimators such as R(KDP) are more robust in heavy rain since they are insensitive to attenuation and less sensitive to drop-size assumptions — see [](#attenuation-correction-dual-pol).

We use the single-polarization Fruška Gora data here (rather than the dual-polarization Jastrebac data used for the convective [QVP](#qvp-workflow)) paired with the stratiform case ([](#stratiform-case)): a single Z-R relationship is best justified over a widespread, more uniform rain event than a convective one.

(qpe-select-prefix)=
## Claim Data

We use the ARCO data provided in [](#intro-data-access).

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
prefix = "Fgora"  # single-pol, 12 sweeps × 360 az × 250 range, 2014 + 2017 + 2026 — stratiform case

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
).sel(vcp_time="2014")
display(dtree)
root = next(iter(dtree.keys())).split("/")[0]
```

## Get the Lowest Elevation Sweep

QPE conventionally uses the lowest available elevation, closest to the ground, to minimize the vertical distance between the radar beam and the surface.

```{seealso}
- [](xref:wradlib#generated/wradlib.georef.polar.georeference)
- [](xref:wradlib#generated/wradlib.georef.projection.get_earth_projection)
```

```{note}
The ``z.attrs`` fix below works around [wradlib/wradlib#791](https://github.com/wradlib/wradlib/issues/791): ``georeference()`` currently mislabels ``z``'s units as degrees instead of meters.
```

```{code-cell} ipython3
swp = (
    dtree[f"{root}/sweep_0"]
    .to_dataset(inherit="all_coords")
    .wrl.georef.georeference(crs=wrl.georef.get_earth_projection())
)
swp.z.attrs = xd.model.get_altitude_attrs()
display(swp)
```

## Convert Reflectivity to Rain Rate

```{seealso}
- [](xref:wradlib#generated/wradlib.trafo.idecibel)
- [](xref:wradlib#generated/wradlib.zr.z_to_r)
```

```{code-cell} ipython3
z_linear = swp.DBZH.wrl.trafo.idecibel()
rain_rate = z_linear.wrl.zr.z_to_r(a=200.0, b=1.6)
rain_rate.attrs.update(units="mm/h", long_name="Rain rate (Marshall-Palmer)")
display(rain_rate)
```

## Accumulate Rainfall

We convert each scan's instantaneous rain rate into a rainfall depth using the volume's median scan interval, then sum over the full period to get total accumulation.

```{code-cell} ipython3
dt_minutes = float(np.median(np.diff(swp.vcp_time.values)) / np.timedelta64(1, "m"))
print(f"Median scan interval: {dt_minutes:.1f} minutes")

accumulation = (rain_rate * dt_minutes / 60.0).sum("vcp_time", skipna=True)
accumulation.name = "accum"
accumulation.attrs.update(units="mm", long_name="Rainfall accumulation")
display(accumulation)
```

## Visualize Accumulated Rainfall

```{code-cell} ipython3
fig = plt.figure(figsize=(8, 7))
accumulation.wrl.vis.plot(cmap="HomeyerRainbow", vmin=0, vmax=15)
plt.gca().set_title(f"{prefix} - Rainfall Accumulation")
fig.tight_layout()
```

## Next Steps

You've computed a single Z-R rainfall accumulation for the stratiform case. Return to the [``prefix`` selection step](#qpe-select-prefix) to try one of the other Fruška Gora dates.

```{tip}
Try re-running with the Jastrebac dual-polarization store used in the [QVP notebook](#qvp-workflow) and compare this single-pol R(Z) estimate against a dual-pol R(KDP) estimate for the same convective case.
```
