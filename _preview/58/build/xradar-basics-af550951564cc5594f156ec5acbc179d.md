---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '1.3'
    jupytext_version: 1.19.1
kernelspec:
  name: python3  
  display_name: Python 3
---

```{image} ../../images/logos/xradar_logo.svg
:width: 250px
:alt: xradar Logo
```

# Xradar Basics



***


## Overview

1. Xradar general overview
1. Radar data IO
2. Radar data georeferencing
3. Data visualization
   


## Prerequisites
| Concepts | Importance | Notes |
| --- | --- | --- |
| [Intro to Xarray](https://foundations.projectpythia.org/core/xarray.html) | Necessary |  Basic features |
| [Radar Cookbook](https://projectpythia.org/radar-cookbook/README.html) | Necessary |  Radar basics |
| [Matplotlib](https://foundations.projectpythia.org/core/matplotlib.html) | Necessary |  Plotting basic features |
- **Time to learn**: 30 minutes
***


## Imports

```{code-cell} ipython3
import xradar as xd
import pyart
import wradlib as wrl

import fsspec
import numpy as np
import xarray as xr

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
```

## Xradar


`Xradar` is a `Python` package developed to streamline the **reading** and **writing** of radar data across various formats, with exports aligned to standards like ODIM_H5 and CfRadial. Born from the **Open Radar Science Community's** collaboration at **ERAD2022**, `Xradar` uses an `xarray-based` data model, compatible with the upcoming **CfRadial2.1/FM301** standard. This ensures seamless integration with other xarray-based software and existing open-source radar processing tools.


### Xradar data model
Xradar leverages the upcoming FM301 standard, a subset of CfRadial2.0, using Xarray to efficiently manage radar data.


#### DataTree Structure (CfRadial2.1/FM301 standard)
Xradar employs `xarray.DataTree` objects to organize radar sweeps within a single structure, where each sweep is an `xarray.Dataset` containing relevant metadata and variables.


```{image} ../../images/CfRadial2.1.svg
:width: 500px
:alt: xradar cfradial
```

## Xradar importers


Xradar supports several importers to handle different radar data formats. These importers typically include:

- **ODIM_H5**: For reading radar data in the ODIM_H5 format, which is widely used in Europe and supported by the EUMETNET OPERA program.

- **CfRadial**: For importing data in the CfRadial format, which is commonly used in the atmospheric sciences community.

- **SIGMET/IRIS**: For ingesting radar data from SIGMET/IRIS formats, which are used by various weather radar systems globally.

- **GAMIC**: For reading data from GAMIC radars, which use their proprietary format.

For more importers check [here](https://docs.openradarscience.org/projects/xradar/en/stable/importers.html)


Let's find some Serrbian radar data.

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
fs = fsspec.filesystem(
    "s3", anon=True, client_kwargs={"endpoint_url": OSN_ENDPOINT},
)

for site, prefix in [("FGora", "fgora_vol"), ("Jastrebac", "jastrebac_vol")]:
    files = sorted(fs.glob(f"{BUCKET}/{prefix}/**/*.vol"))
    print(f"{site} raw files: {len(files)}")
    for f in files[:4]:
        print(f"  {f.split('/')[-1]}")
    print()
```

```{code-cell} ipython3
fgora_raw = sorted(fs.glob(f"{BUCKET}/fgora_vol/**/*.vol"))
sample_file = fgora_raw[2]  # a dBZ file
print(f"File: {sample_file.split('/')[-1]}")

local_path = fsspec.open_local(
    f"simplecache::s3://{sample_file}",
    s3={"anon": True, "client_kwargs": {"endpoint_url": OSN_ENDPOINT}},
)
dtree = xd.io.open_rainbow_datatree(local_path, optional_groups=True)
dtree
```

In this `Xarray.Datatree` object, the first two nodes contains radar metadata and the others contains `Xarray.Datasets` for each sweeps.

```{code-cell} ipython3
for sweep in dtree.children:
    try:
        print(f"{sweep} - elevation {np.round(dtree[sweep]['sweep_fixed_angle'].values[...], 1)}")
    except KeyError:
        print (sweep)
```

Let's explore the `0.5` degrees elevation ('sweep_0')

```{code-cell} ipython3
ds_sw0 = dtree["sweep_0"].ds.assign_coords(dtree["/"].coords)
display(ds_sw0)
```

## Xradar visualization

We can make a plot using [`xarray.plot`](https://docs.xarray.dev/en/latest/user-guide/plotting.html) functionality.

```{code-cell} ipython3
ds_sw0.DBZH.plot(
    cmap="ChaseSpectral",
    vmax=60,
    vmin=-10, 
)
```

The radar data in the `Xarray.Dataset` object includes range and azimuth as coordinates. To create a radial plot, apply the [`xradar.georeference`](https://docs.openradarscience.org/projects/xradar/en/stable/georeference.html) method. This method will generate x, y, and z coordinates for the plot.

```{code-cell} ipython3
ds_sw0 = ds_sw0.xradar.georeference()
display(ds_sw0)
```

We can now create a radial plot passing `x` and `y` coordinates

```{code-cell} ipython3
ds_sw0.DBZH.plot(
    x="x", 
    y= "y",
    cmap="ChaseSpectral",
    vmax=60,
    vmin=-10, 
)
```

## Data slicing

We can use the power of `Xarray` to acces data within the first 50 kilometers by [slicing](https://foundations.projectpythia.org/core/xarray/xarray-intro.html#slicing-along-coordinates) along coordinates.

```{code-cell} ipython3
ds_sw0.sel(range=slice(0, 5e4)).DBZH.plot(
    x="x", 
    y= "y",
    cmap="ChaseSpectral",
    vmax=60,
    vmin=-10, 
)
```

Let's suppose we want to subset between 90 and 180 degrees angle in azimuth.

```{code-cell} ipython3
ds_sw0.sel(azimuth=slice(90, 180), range=slice(0, 5e4)).DBZH.plot(
    x="x", 
    y= "y",
    cmap="ChaseSpectral",
    vmax=60,
    vmin=-10, 
)
```

Perhaps, we just want to see radar reflectivity along the 100 degrees angle in azimuth.

```{code-cell} ipython3
ds_sw0 = ds_sw0.pipe(xd.util.remove_duplicate_rays)
```

```{code-cell} ipython3
ds_sw0.sel(azimuth=143, method="nearest").DBZH.plot()
```

## DataTree operations

```{code-cell} ipython3
def filter_data(ds):
    ds = ds.where(ds.DBZH > 0)
    return ds
```

```{code-cell} ipython3
dtree_filt = dtree.xradar.map_over_sweeps(filter_data)
```

```{code-cell} ipython3
dtree_filt["sweep_0"].ds.xradar.georeference()["DBZH"].plot(
    x="x",
    y="y",
    cmap="ChaseSpectral",
    vmax=60,
    vmin=-10,
)
```

## Xradar integration

### Py-Art

`Xradar` datatree objects can be ported to `Py-ART` radar objects using the pyart.xradar.Xradar method.

```{code-cell} ipython3
radar = pyart.xradar.Xradar(dtree)
fig = plt.figure(figsize=[10, 8])
pyart_display = pyart.graph.RadarMapDisplay(radar)
pyart_display.plot_ppi_map('DBZH', sweep=0)
```

```{code-cell} ipython3
del pyart_display
```

### Wradlib

`Wradlib` functionality can also be applied to `Xarray.Datatree` objects. For example, the [`wradlib.georef`](https://docs.wradlib.org/en/latest/georef.html) module can be used to enrich data by adding geographical coordinates.

```{code-cell} ipython3
for key in list(dtree.children):
    if "sweep" in key:
        dtree[key].ds = dtree[key].ds.assign_coords(dtree["/"].coords).wrl.georef.georeference(
            crs=wrl.georef.get_default_projection()
        ).drop_vars(["altitude", "latitude", "longitude"])
```

```{code-cell} ipython3
dtree["sweep_0"].ds
```

```{code-cell} ipython3
swp = dtree["sweep_0"].ds.set_coords("sweep_mode")
swp.DBZH.wrl.vis.plot(vmax=60, vmin=-10)
plt.gca().set_title(f"Fruška Gora - {swp.time.min().values.astype("<M8[s]")} - {swp.sweep_fixed_angle.values:.1f} deg");
```

## Xradar Transform

```{code-cell} ipython3
ds_cf1 = dtree.xradar.to_cf1()
```

```{code-cell} ipython3
ds_cf1["DBZH"].where(ds_cf1["DBZH"] > 0).plot()
```

```{code-cell} ipython3
# ds_cf1.to_netcdf("cf1.nc")
```

```{code-cell} ipython3
dtree_cf2 = ds_cf1.xradar.to_cf2()
# dtree_cf2.to_netcdf("cf2.nc")
```

## Xradar exporters


In xradar, exporters convert radar data into various formats for analysis or integration. Exporting is supported for recognized standards, including:

- CfRadial1
- CfRadial2
- ODIM
- Zarr

Although [`Zarr`](https://zarr.readthedocs.io/en/stable/getting_started.html) is not a traditional standard format, it provides an analysis-ready, cloud-optimized format that enhances data accessibility and performance.

```{code-cell} ipython3
dtree.to_zarr("tree.zarr", consolidated=True, mode="w")
```

```{code-cell} ipython3
dt_back = xr.open_datatree("tree.zarr", engine="zarr",chunks={})
```

```{code-cell} ipython3
display(dt_back)
```

***

## Summary

`Xradar` is a Python library designed for working with radar data. It extends xarray to include radar-specific functionality, such as purpose-based accessors and georeferencing methods. It supports exporting data in various formats, including CfRadial1, CfRadial2, ODIM, and Zarr. xradar facilitates the analysis, visualization, and integration of radar data with other tools and systems.


## Resources and references
 - [Xradar](https://docs.openradarscience.org/projects/xradar/en/stable/index.html)
 - [Radar cookbook](https://github.com/ProjectPythia/radar-cookbook)
 - [Py-Art landing page](https://arm-doe.github.io/pyart/)
 - [Wradlib landing page](https://docs.wradlib.org/en/latest/index.html)
