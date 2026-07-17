---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.3
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

<img src="../../images/logos/arm_logo.png" width=500 alt="ARM Logo"></img>

+++

# Py-ART Gridding 
---

+++

## Overview
   
Within this notebook, we will cover:

1. What is gridding and why is it important?
1. An overview of gridding with Py-ART  
1. Test out a different gridding routine
1. Apply Gridding to a Selection of Files

+++

## Prerequisites
| Concepts | Importance | Notes |
| --- | --- | --- |
| [Py-ART Basics](pyart-basics) | Helpful | Basic features |
| [Intro to Cartopy](https://foundations.projectpythia.org/core/cartopy/cartopy.html) | Helpful | Basic features |
| [Matplotlib Basics](https://foundations.projectpythia.org/core/matplotlib/matplotlib-basics.html) | Helpful | Basic plotting |
| [NumPy Basics](https://foundations.projectpythia.org/core/numpy/numpy-basics.html) | Helpful | Basic arrays |

- **Time to learn**: 15 minutes
---

+++

## Imports

```{code-cell} ipython3
import os
from pathlib import Path
import glob
import warnings

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import fsspec
import re
import pyart
from pyart.testing import get_test_data
from datetime import datetime
import xarray as xr

OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
warnings.filterwarnings('ignore')
```

## What is gridding and why is it important?

+++

### Antenna vs. Cartesian Coordinates

Radar data, by default, is stored in a **polar (or antenna) coordinate system**, with the data coordinates stored as an angle (ranging from 0 to 360 degrees with 0 == North), and a radius from the radar, and an elevation which is the angle between the ground and the ground.

This format can be challenging to plot, since it is scan/radar specific. Also, it can make comparing with model data, which is on a lat/lon grid, challenging since one would need to **transform** the model daa cartesian coordinates to polar/antenna coordiantes.

Fortunately, PyART has a variety of gridding routines, which can be used to **grid your data to a Cartesian grid**. Once it is in this new grid, one can easily slice/dice the dataset, and compare to other data sources.

### Why is Gridding Important?

Gridding is essential to combining multiple data sources (ex. multiple radars), and comparing to other data sources (ex. model data). There are also decisions that are made during the gridding process that have a large impact on the regridded data - for example:
- What resolution should my grid be?
- Which interpolation routine should I use?
- How smooth should my interpolated data be?

While there is not always a right or wrong answer, it is important to understand the options available, and document which routine you used with your data! Also - experiment with different options and choose the best for your use case!

+++

## An overview of gridding with Py-ART
Let's dig into the regridding process with PyART!

+++

## Read in the Data and Plot the Data

+++

### Read in a sample file from the Fruska Gora (FGora) radar
Our data is formatted as a Rainbow file used by Leonardo radars. We will download the data locally so that Py-ART's Rainbow reader can read the files.

```{code-cell} ipython3
from pathlib import Path
fs = fsspec.filesystem(
    "s3", anon=True, client_kwargs={"endpoint_url": OSN_ENDPOINT},
)
fgora_raw = sorted(fs.glob(f"{BUCKET}/fgora_vol/**/*.vol"))
download_dir = Path("data/fgora_sample")
download_dir.mkdir(parents=True, exist_ok=True)

sample_ts = "2014051500012000"
for remote in [f for f in fgora_raw if sample_ts in f]:
    local = download_dir / Path(remote).name
    if not local.exists():
        fs.get(remote, str(local))
    print(f"  {local.name}")
```

```{code-cell} ipython3
radar = pyart.aux_io.read_rainbow_wrl('data/fgora_sample/2014051500012000dBZ.vol')
```

Let's plot up quick look of reflectivity, at the lowest elevation scan (closest to the ground)

```{code-cell} ipython3
fig = plt.figure(figsize=[6, 6])
display = pyart.graph.RadarDisplay(radar)
display.plot_ppi('reflectivity', 
                 cmap='HomeyerRainbow')
```

As mentioned before, the dataset is currently in the **antenna coordinate system** measured as distance from the radar

+++

### Setup our Gridding Routine with `pyart.map.grid_from_radars()`

Py-ART has the [Grid object](https://arm-doe.github.io/pyart/API/generated/pyart.core.Grid.html#pyart.core.Grid) which has characteristics similar to that of the [Radar object](https://arm-doe.github.io/pyart/API/generated/pyart.core.Radar.html), except that the data are stored in Cartesian coordinates instead of the radar's antenna coordinates.

```{code-cell} ipython3
pyart.core.Grid?
```

We can **transform our data** into this grid object, from the radars, using `pyart.map.grid_from_radars()`.

Beforing gridding our data, we need to make a decision about the desired grid resolution and extent. For example, one might imagine a grid configuration of:
- Grid extent/limits
    - 20 km in the x-direction (north/south)
    - 20 km in the y-direction (west/east)
    - 15 km in the z-direction (vertical)
- 500 m spatial resolution

The `pyart.map.grid_from_radars()` function takes the grid shape and grid limits as input, with the order `(z, y, x)`.

Let's setup our configuration, setting our grid extent **first**, with the distance measured in **meters**

```{code-cell} ipython3
z_grid_limits = (0.,15_000.)
y_grid_limits = (-150_000.,150_000.)
x_grid_limits = (-150_000.,150_000.)
```

Now that we have our grid limits, we can set our desired resolution (again, in meters)

```{code-cell} ipython3
grid_resolution = 500
```

Let's compute our grid shape - using the extent and resolution to compute the number of grid points in each direction.

```{code-cell} ipython3
def compute_number_of_points(extent, resolution):
    return int((extent[1] - extent[0])/resolution)
```

Now that we have a helper function to compute this, let's apply it to our vertical dimension

```{code-cell} ipython3
z_grid_points = compute_number_of_points(z_grid_limits, grid_resolution)
z_grid_points
```

We can apply this to the horizontal (x, y) dimensions as well.

```{code-cell} ipython3
x_grid_points = compute_number_of_points(x_grid_limits, grid_resolution)
y_grid_points = compute_number_of_points(y_grid_limits, grid_resolution)

print(z_grid_points,
      y_grid_points,
      x_grid_points)
```

#### Use our configuration to grid the data!
Now that we have the grid shape and grid limits, let's grid up our radar!

```{code-cell} ipython3
grid = pyart.map.grid_from_radars(radar,
                                  grid_shape=(z_grid_points,
                                              y_grid_points,
                                              x_grid_points),
                                  grid_limits=(z_grid_limits,
                                               y_grid_limits,
                                               x_grid_limits),
                                  fields=['reflectivity'],
                                  min_radius=500.
                                 )
grid
```

We now have a `pyart.core.Grid` object!

+++

### Plot up the Grid Object

#### Plot a horizontal view of the data
We can use the `GridMapDisplay` from `pyart.graph` to visualize our regridded data, starting with a horizontal view (slice along a single vertical level)

```{code-cell} ipython3
display = pyart.graph.GridMapDisplay(grid)
display.plot_grid('reflectivity',
                  level=3,
                  vmin=-20,
                  vmax=60,
                  cmap='HomeyerRainbow')
```

#### Plot a Latitudinal Slice

+++

We can also slice through a single latitude or longitude!

```{code-cell} ipython3
display.plot_latitude_slice('reflectivity',
                            lat=45.15,
                            vmin=-20,
                            vmax=60,
                            cmap='HomeyerRainbow')
plt.xlim([-20, 20]);
```

#### Plot with Xarray

+++

Another neat feature of the `Grid` object is that we can transform it to an `xarray.Dataset`!

```{code-cell} ipython3
ds = grid.to_xarray()
ds
```

Now, our plotting routine is a **one-liner**, starting with the horizontal slice:

```{code-cell} ipython3
ds.isel(z=2).reflectivity.plot(cmap='HomeyerRainbow',
                               vmin=-20,
                               vmax=60);
```

And a vertical slice at a given y dimension (latitude)

```{code-cell} ipython3
ds.sel(y=-3000,
       method='nearest').reflectivity.plot(cmap='HomeyerRainbow',
                                           vmin=-20,
                                           vmax=60);
```

### Try a Different Gridding Technique

In the previous section, we used the Barnes interpolation technique for interpolating the radar data to Cartesian coordinates. Such an interpolation, while producing smoother grids, can blur out mesoscale phenomena that occur on the scale of the grid resolution such as gust fronts and hail cores. Therefore, to capture these more extreme events, a nearest neighbor interpolation is desired to capture these events at the expense of a noisier grid.

```{code-cell} ipython3
nearest_grid = pyart.map.grid_from_radars(radar,
                                  grid_shape=(z_grid_points,
                                              y_grid_points,
                                              x_grid_points),
                                  grid_limits=(z_grid_limits,
                                               y_grid_limits,
                                               x_grid_limits),
                                  fields=['reflectivity'],
                                  weighting_function='Nearest',
                                  min_radius=500.
                                 )
```

```{code-cell} ipython3
display.plot_latitude_slice('reflectivity',
                            lat=45.1,
                            vmin=-20,
                            vmax=60,
                            cmap='HomeyerRainbow')
plt.xlim([-20, 20]);
```

## Apply Gridding to a Selection of Files

We would like to apply our gridding transformation to an entire list of files, that will enable tracking in future notebooks (ex. tobac). We need to:
- Setup a function to grid our data (including saving it to disk)
- Provide a list of files to grid

```{code-cell} ipython3
def grid_radar_data(infile, outdir, grid_resolution=500):
    """
    Parameters
    ==========
    infile: string, path to file to be gridded
    outdir: string, path to directory to save to
    grid_resolution: int, desired resolution of field in meters
    
    Returns
    =======
    print statement with saved file
    """

    # Read the data
    radar = pyart.aux_io.read_rainbow_wrl(infile)
    
    # Configure the bounds + compute points
    z_grid_limits = (0.,15_000.)
    y_grid_limits = (-150_000.,150_000.)
    x_grid_limits = (-150_000.,150_000.)
    x_grid_points = compute_number_of_points(x_grid_limits, grid_resolution)
    y_grid_points = compute_number_of_points(y_grid_limits, grid_resolution)
    z_grid_points = compute_number_of_points(z_grid_limits, grid_resolution)
    
    
    # Grid the radar data
    grid = pyart.map.grid_from_radars(radar,
                                  grid_shape=(z_grid_points,
                                              y_grid_points,
                                              x_grid_points),
                                  grid_limits=(z_grid_limits,
                                               y_grid_limits,
                                               x_grid_limits),
                                  fields=['reflectivity'],
                                  weighting_function='Nearest',
                                  min_radius=grid_resolution
                                 )
    
    infile_path = Path(infile)
    os.makedirs(outdir, exist_ok=True)
    outfile = f"{outdir}/{infile_path.stem}.nc"
    
    # Save to disk
    grid.to_xarray().to_netcdf(outfile, mode='w')
    print(f"Done gridding + saving {outfile}")
    return outfile
```

```{code-cell} ipython3
fs = fsspec.filesystem(
    "s3", anon=True, client_kwargs={"endpoint_url": OSN_ENDPOINT},
)

# Can replace this prefix to jastrebac_vol get the Jastrebac radar
prefix = "fgora_vol"
files = sorted(fs.glob(f"{BUCKET}/{prefix}/**/*.vol"))
pat = re.compile(r'/(\d{14})\d{2}[A-Za-z]+\.vol$')
times = sorted({m.group(1) for f in files if (m := pat.search(f))})
dBz_files = [x for x in files if "dBZ" in x]
```

```{code-cell} ipython3
def download_file(remote, download_dir=Path("data/fgora_sample")):
    local = download_dir / Path(remote).name
    if not local.exists():
        fs.get(remote, str(local))
    return str(local)
```

```{code-cell} ipython3
downloaded_files = [download_file(file) for file in dBz_files]
# Let's just target a single date. We have 2014-05-15, 2017-08-12, and 2026-05-12
data_date = "20140515"
downloaded_files = [x for x in downloaded_files if data_date in x]
```

```{code-cell} ipython3
gridded_data = [grid_radar_data(file,
                                "../../data/fgora/gridded_dBZ/") for file in downloaded_files]
```

### Read in the Gridded Data and Plot It
Now that we have our output, we can read all of it into the same `xarray.Dataset`, and visualize our data!

```{code-cell} ipython3
ds = xr.open_mfdataset(gridded_data).squeeze()
```

```{code-cell} ipython3
ds.reflectivity.isel(z=2).plot(x='x',
                               y='y',
                               col='time',
                               vmin=-20,
                               vmax=70,
                               cmap='ChaseSpectral',
                               col_wrap=5);
```

---
## Summary
Within this notebook, we covered the basics of gridding radar data using `pyart`, including:
- What we mean by gridding and why is it matters
- Configuring your gridding routine
- Visualize gridded radar data

### What's Next
In the next few notebooks, we walk through applying data cleaning methods, and advanced visualization methods!

+++

## Resources and References
Py-ART essentials links:

* [Landing page](arm-doe.github.io/pyart/)
* [Examples](https://arm-doe.github.io/pyart/examples/index.html)
* [Source Code](github.com/ARM-DOE/pyart)
* [Mailing list](groups.google.com/group/pyart-users/)
* [Issue Tracker](github.com/ARM-DOE/pyart/issues)
