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

# Attenuation correction comparison with wradlib

Comparison between BALTRAD and wradlib attenuation correction

+++

## Retrieve data from s3 bucket

```{code-cell} ipython3
import os
import urllib.request
from pathlib import Path

# Set the URL for the cloud
URL = "https://js2.jetstream-cloud.org:8001/"
path = "pythia/radar/erad2024/baltrad/baltrad2wradlib/"
!mkdir -p data
!mkdir -p shp
files = [
    "data/201405190715_SUR.h5",
    "shp/europe_countries.dbf",
    "shp/europe_countries.prj",
    "shp/europe_countries.sbn",
    "shp/europe_countries.sbx",
    "shp/europe_countries.shp",
    "shp/europe_countries.shx",
]
for file in files:
    file0 = os.path.join(path, Path(file).name)
    if not os.path.exists(file):
        print(f"downloading, {file}")
        x = urllib.request.urlretrieve(f"{URL}{file0}", file)
```

## Prepare your environment

```{code-cell} ipython3
%matplotlib inline
```

```{code-cell} ipython3
import gc

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import shapefile
import wradlib
import xradar as xd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
```

## Run BALTRAD's odc_toolbox

+++

First, you will process a scan from Suergavere (Estland) by using BALTRAD's odc_toolbox.

From your VM's vagrant directory, navigate to the folder ``/baltrad2wradlib``.

Execute the following command:

``$ odc_toolbox -i data -o out -q ropo,radvol-att``

Check whether a file was created in the folder ``/out``.

**BALTRAD will not create output files if these already exist.** You can check that via ``!ls out``.

```{code-cell} ipython3
!odc_toolbox --help
```

```{code-cell} ipython3
!odc_toolbox -i data -o out -q ropo,radvol-att
```

```{code-cell} ipython3
!ls out
```

## Read and inspect data from Suergavere (Estonia) before and after QC with odc_toolbox

```{code-cell} ipython3
# Before QC
inp = xd.io.open_odim_datatree("data/201405190715_SUR.h5")
# After QC
out = xd.io.open_odim_datatree("out/201405190715_SUR.h5")
```

## Georeference

```{code-cell} ipython3
inp = inp.xradar.georeference()
out = out.xradar.georeference()
```

```{code-cell} ipython3
swp_inp = inp["sweep_0"].ds.set_coords("sweep_mode")
swp_out = out["sweep_0"].ds.set_coords("sweep_mode")
display(swp_inp)
display(swp_out)
```

## Design a plot we will use for all PPIs in this exercise

```{code-cell} ipython3
import cartopy.crs as ccrs
import wradlib as wrl
from cartopy.io.shapereader import Reader

map_proj = ccrs.AzimuthalEquidistant(
    central_latitude=swp_inp.latitude.values, central_longitude=swp_inp.longitude.values
)
osr_proj = wrl.georef.create_osr(
    "aeqd", lat_0=swp_inp.latitude.values, lon_0=swp_inp.longitude.values
)

geometries = list(Reader("shp/europe_countries.shp").geometries())


def plot_ppi_to_ax(ppi, ax, title="", geometries=None, **kwargs):
    pm = ppi.wrl.vis.plot(crs=map_proj, ax=ax, **kwargs)
    ax.set_title(title)
    if geometries is not None:
        ax.add_geometries(
            geometries,
            ccrs.PlateCarree(),
            facecolor="lightgrey",
            edgecolor="k",
            linewidths=1,
            zorder=-1,
        )
    wrl.vis.plot_ppi_crosshair(
        site=(ppi.longitude.values, ppi.latitude.values, ppi.altitude.values),
        ranges=[50000, 100000, 150000, 200000, ppi.range.max().values],
        angles=[0, 90, 180, 270],
        line=dict(color="white"),
        circle={"edgecolor": "white"},
        ax=ax,
        crs=osr_proj,
    )
    return pm
```

## Plot the selected fields into one figure

```{code-cell} ipython3
fig = plt.figure(figsize=(12, 10))

ax = plt.subplot(221, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_inp.DBZH.where(swp_inp.DBZH >= -10),
    ax=ax,
    geometries=geometries,
    title="Before QC",
    add_colorbar=False,
    vmin=-10,
    vmax=65,
)

ax = plt.subplot(222, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_out.DBZH.where(swp_out.DBZH >= -10),
    ax=ax,
    geometries=geometries,
    title="After QC",
    add_colorbar=False,
    vmin=-10,
    vmax=65,
)

ax = plt.subplot(223, projection=map_proj)
qm = plot_ppi_to_ax(
    swp_out.quality1,
    ax=ax,
    geometries=geometries,
    add_colorbar=False,
    title="Quality 1",
)

ax = plt.subplot(224, projection=map_proj)
qm = plot_ppi_to_ax(
    swp_out.QIND, ax=ax, geometries=geometries, add_colorbar=False, title="Quality 2"
)

plt.tight_layout()

# Add colorbars
fig.subplots_adjust(right=0.9)
cax = fig.add_axes((0.9, 0.6, 0.03, 0.3))
cbar = plt.colorbar(pm, cax=cax)
cbar.set_label("Horizontal reflectivity (dBZ)", fontsize="large")

cax = fig.add_axes((0.9, 0.1, 0.03, 0.3))
cbar = plt.colorbar(qm, cax=cax)
cbar.set_label("Quality index", fontsize="large")
```

## Collect and plot the polarimetric moments from the original ODIM_H5 dataset

```{code-cell} ipython3
fig = plt.figure(figsize=(12, 12))

ax = plt.subplot(221, projection=map_proj)
pm = plot_ppi_to_ax(swp_inp.RHOHV, ax=ax, title="RhoHV", geometries=geometries)

ax = plt.subplot(222, projection=map_proj)
pm = plot_ppi_to_ax(swp_inp.PHIDP, ax=ax, title="PhiDP", geometries=geometries)

ax = plt.subplot(223, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_inp.ZDR, ax=ax, title="Differential reflectivity", geometries=geometries
)

ax = plt.subplot(224, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_inp.VRAD, ax=ax, title="Doppler velocity", geometries=geometries
)

plt.tight_layout()
```

## Try some filtering and attenuation correction

```{code-cell} ipython3
# Set ZH to a very low value where we do not expect valid data
zh = swp_inp.DBZH.fillna(-32.0)
# Retrieve PIA by using some constraints (see https://docs.wradlib.org/en/latest/notebooks/attenuation/attenuation.html for help)
pia = zh.wrl.atten.correct_attenuation_constrained(
    constraints=[wradlib.atten.constraint_dbz, wradlib.atten.constraint_pia],
    constraint_args=[[64.0], [20.0]],
)

# Correct reflectivity by PIA
zh_corrected = swp_inp.DBZH + pia
```

## Compare results against QC from odc_toolbox

```{code-cell} ipython3
fig = plt.figure(figsize=(18, 10))

ax = plt.subplot(131, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_inp.DBZH.where(swp_out.DBZH >= -10),
    ax=ax,
    geometries=geometries,
    title="Before QC",
)

ax = plt.subplot(132, projection=map_proj)
pm = plot_ppi_to_ax(
    swp_out.DBZH.where(swp_out.DBZH >= -10),
    ax=ax,
    geometries=geometries,
    title="After QC using BALTRAD Toolbox",
)

ax = plt.subplot(133, projection=map_proj)
pm = plot_ppi_to_ax(
    zh_corrected.where(zh_corrected >= -10),
    ax=ax,
    geometries=geometries,
    title="After QC using wradlib",
)
```
