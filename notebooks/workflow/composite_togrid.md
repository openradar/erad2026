---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3
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

(composite-to-grid)=
# Composite To Grid

In this notebook we show the production of a maximum reflectivity composite from [Fruška_Gora](wiki:Fruška_Gora) Radar and [](wiki:Jastrebac) Radar to a common cartesian grid.

```{code-cell} ipython3
import tempfile
import warnings

import cmweather
import numpy as np
import pyproj
import xarray as xr
import matplotlib.pyplot as plt

import wradlib as wrl
import wradlib_data

warnings.filterwarnings("ignore")
```

```{code-cell} ipython3
import cmweather
import numpy as np
import wradlib as wrl
import matplotlib.pyplot as plt
import xarray as xr
import xradar as xd
import fsspec
import icechunk
import holoviews as hv
import hvplot
import hvplot.xarray
```

## Claim Data

We use the preprocess data from [](gridding_data.md).


```{code-cell} ipython3
# prefix = "Fgora"  # single-pol, 12 sweeps × 360 az × 250 range, 2014 + 2017 + 2026
prefix = "jastrebac_250m"  # dual-pol, 12 × 360 × 1000, 2014 only
# prefix = "jastrebac_500m"  # dual-pol, 12 × 360 × 500,  2017 + 2026
```

## Get Lowest Sweep

```{code-cell} ipython3
outname_nearest = f"{prefix}_nearest.nc"
filenames = {"jastrebac": "jastrebac_500m_nearest.nc", "fgora": "Fgora_nearest.nc"}
ctree = xr.DataTree()
for radar, filename in filenames.items():
    ds = xr.open_dataset(filename, chunks={}).sel(vcp_time="2017")
    ds = ds.assign_coords(vcp_time=ds.vcp_time.dt.floor("5min")).sortby("vcp_time")
    ctree[radar] = ds
display(ctree)
```

## Plot Overview

```{code-cell} ipython3
fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
ax = axs.flat[1]
ctree["jastrebac"].ds.DBZH[0].wrl.vis.plot(ax=ax, vmin=0, vmax=60)
ax.set_title("Radar Jastrebac")
ax.set_xlim(min(ctree["fgora"].ds.x.min(), ctree["jastrebac"].ds.x.min()), max(ctree["fgora"].ds.x.max(), ctree["jastrebac"].ds.x.max())) 
ax.set_ylim(min(ctree["fgora"].ds.y.min(), ctree["jastrebac"].ds.y.min()), max(ctree["fgora"].ds.y.max(), ctree["jastrebac"].ds.y.max()))
ax = axs.flat[0]
ctree["fgora"].ds.DBZH[0].wrl.vis.plot(ax=ax, vmin=0, vmax=60)
ax.set_title("Radar Fruŝka Gora")
ax.set_xlim(min(ctree["fgora"].ds.x.min(), ctree["jastrebac"].ds.x.min()), max(ctree["fgora"].ds.x.max(), ctree["jastrebac"].ds.x.max())) 
ax.set_ylim(min(ctree["fgora"].ds.y.min(), ctree["jastrebac"].ds.y.min()), max(ctree["fgora"].ds.y.max(), ctree["jastrebac"].ds.y.max()))
```

## Compositing

Before compositing we combine the two radar grids into one Dataset.

```{code-cell} ipython3
radars = xr.DataArray(ctree.children, dims="radar")
radargrids = xr.concat([ctree[radar].ds.DBZH for radar in ctree.children], dim=radars)

display(radargrids)
```

Then we finally reduce over the ``radar`` dimension to create the final output.

```{code-cell} ipython3
composite = radargrids.max("radar")
display(composite)
```

## Plot Result

```{code-cell} ipython3
csel = composite.isel(vcp_time=0)
csel.where(csel>0.1).plot(cmap="HomeyerRainbow", vmin=0, vmax=60)
```

```{code-cell} ipython3
csel = composite.isel(vcp_time=1)
csel.where(csel>0.1).plot(cmap="HomeyerRainbow", vmin=0, vmax=60)
```

## Write Composite

```{code-cell} ipython3
outname_composite = f"composite1.nc"
composite.to_netcdf(outname_composite)
```