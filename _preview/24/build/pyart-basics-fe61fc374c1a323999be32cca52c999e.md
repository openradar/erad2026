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

```{image} ../../images/logos/arm_logo.png
:width: 500px
:alt: ARM Logo
```

# Py-ART Basics with Xradar
---


## Overview
   
Within this notebook, we will cover:

1. General overview of Py-ART and its functionality
1. Reading data using Py-ART
1. An overview of the `pyart.Radar` object
1. Create a Plot of our Radar Data



## Prerequisites
| Concepts | Importance | Notes |
| --- | --- | --- |
| [Intro to Cartopy](https://foundations.projectpythia.org/core/cartopy/cartopy.html) | Helpful | Basic features |
| [Matplotlib Basics](https://foundations.projectpythia.org/core/matplotlib/matplotlib-basics.html) | Helpful | Basic plotting |
| [NumPy Basics](https://foundations.projectpythia.org/core/numpy/numpy-basics.html) | Helpful | Basic arrays |

- **Time to learn**: 45 minutes
---


## Imports

```{code-cell} ipython3
import os
import warnings

import cartopy.crs as ccrs
import matplotlib.pyplot as plt


import pyart
from pyart.testing import get_test_data
import xradar as xd

warnings.filterwarnings("ignore")
```

## An Overview of Py-ART


### History of the Py-ART

 * Development began to address the needs of ARM with the acquisition of a number of
   new scanning cloud and precipitation radar as part of the American Recovery Act.
 * The project has since expanded to work with a variety of weather radars and a wider user
   base including radar researchers and climate modelers.
 * The software has been released on GitHub as open source software under a BSD license.
   Runs on Linux, OS X. It also runs on Windows with more limited functionality.

### What can PyART Do?

Py-ART can be used for a variety of tasks from basic plotting to more complex
processing pipelines. Specific uses for Py-ART include:

 * Reading radar data in a variety of file formats.
 * Creating plots and visualization of radar data.
 * Correcting radar moments while in antenna coordinates, such as:
    * Doppler unfolding/de-aliasing.
    * Attenuation correction.
    * Phase processing using a Linear Programming method.
 * Mapping data from one or multiple radars onto a Cartesian grid.
 * Performing retrievals.
 * Writing radial and Cartesian data to NetCDF files.


## Reading in Data Using Py-ART


### Reading data in using `xradar.io.open_`


When reading in a radar file, we use the `pyart.io.read` module.

`pyart.io.read` can read a variety of different radar formats, such as Cf/Radial, ODIM_H5, etc.
The documentation on what formats can be read by xradar can be found here:

* [xradar readers Documentation](https://docs.openradarscience.org/projects/xradar/en/stable/importers.html)

Let's take a look at one of these readers:

```{code-cell} ipython3
?xd.io.open_cfradial1_datatree
```

Let's use a sample data file from `pyart` - which is [**cfradial** format](https://github.com/NCAR/CfRadial).

When we read this in, we get a [`pyart.Radar` object](https://arm-doe.github.io/pyart/API/generated/pyart.core.Radar.html#pyart.core.Radar)!

```{code-cell} ipython3
file = get_test_data("swx_20120520_0641.nc")
dt = xd.io.open_cfradial1_datatree(file)
dt
```

### Investigate the [`xradar` object](https://docs.openradarscience.org/projects/xradar/en/stable/notebooks/CfRadial1.html)


Within this [`xradar` object](https://docs.openradarscience.org/projects/xradar/en/stable/notebooks/CfRadial1.html) object are the actual data fields, each stored in a different group, mimicking the FM301/cfradial2 data standard.

This is where data such as reflectivity and velocity are stored.

To see what fields are present we can add the fields and keys additions to the variable where the radar object is stored.

```{code-cell} ipython3
dt["sweep_0"]
```

#### Extract a sample data field


The fields are stored in a dictionary, each containing coordinates, units and more.
All can be accessed by just adding the fields addition to the radar object variable.

For an individual field, we add a string in brackets after the fields addition to see
the contents of that field.

Let's take a look at `'corrected_reflectivity_horizontal'`, which is a common field to investigate.

```{code-cell} ipython3
print(dt["sweep_0"]["corrected_reflectivity_horizontal"])
```

We can go even further in the dictionary and access the actual reflectivity data.

We use add `.data` at the end, which will extract the **data array** (which is a numpy array) from the dictionary.

```{code-cell} ipython3
reflectivity = dt["sweep_0"]["corrected_reflectivity_horizontal"].data
print(type(reflectivity), reflectivity)
```

Lets' check the size of this array...

```{code-cell} ipython3
reflectivity.shape
```

This reflectivity data array, numpy array, is a two-dimensional array with dimensions:
- Range (distance away from the radar)
- Azimuth (direction around the radar)

```{code-cell} ipython3
dt["sweep_0"].dims
```

If we wanted to look the 300th ray, at the second gate, we would use something like the following:

```{code-cell} ipython3
print(reflectivity[300, 2])
```

We can also select a specific azimuth if desired, using the xarray syntax:

```{code-cell} ipython3
dt["sweep_0"].sel(azimuth=180, method="nearest")
```

## Plotting our Radar Data

<!-- #region -->
### An Overview of Py-ART Plotting Utilities

Now that we have loaded the data and inspected it, the next logical thing to do is to visualize the data! Py-ART's visualization functionality is done through the objects in the [pyart.graph](https://arm-doe.github.io/pyart/API/generated/pyart.graph.html) module.

In Py-ART there are 4 primary visualization classes in pyart.graph:

* [RadarDisplay](https://arm-doe.github.io/pyart/API/generated/pyart.graph.RadarDisplay.html)
* [RadarMapDisplay](https://arm-doe.github.io/pyart/API/generated/pyart.graph.RadarMapDisplay.html)
* [AirborneRadarDisplay](https://arm-doe.github.io/pyart/API/generated/pyart.graph.AirborneRadarDisplay.html)

Plotting grid data
* [GridMapDisplay](https://arm-doe.github.io/pyart/API/generated/pyart.graph.GridMapDisplay.html)

### Use the [RadarMapDisplay](https://arm-doe.github.io/pyart/API/generated/pyart.graph.RadarMapDisplay.html) with our data

For the this example, we will be using `RadarMapDisplay`, using Cartopy to deal with geographic coordinates.


We start by creating a figure first, and adding our traditional radar methods to the xradar object.
<!-- #endregion -->

```{code-cell} ipython3
fig = plt.figure(figsize=[10, 10])
radar = pyart.xradar.Xradar(dt)
```

Once we have a figure, let's add our `RadarMapDisplay`

```{code-cell} ipython3
fig = plt.figure(figsize=[10, 10])
display = pyart.graph.RadarMapDisplay(radar)
```

Adding our map display without specifying a field to plot **won't do anything** we need to specifically add a field to field using `.plot_ppi_map()`

```{code-cell} ipython3
display.plot_ppi_map("corrected_reflectivity_horizontal")
```

By default, it will plot the elevation scan, the the default colormap from `Matplotlib`... let's customize!

We add the following arguements:
- `sweep=3` - The fourth elevation scan (since we are using Python indexing)
- `vmin=-20` - Minimum value for our plotted field/colorbar
- `vmax=60` - Maximum value for our plotted field/colorbar
- `projection=ccrs.PlateCarree()` - Cartopy latitude/longitude coordinate system
- `cmap='pyart_HomeyerRainbow'` - Colormap to use, selecting one provided by PyART

```{code-cell} ipython3
fig = plt.figure(figsize=[12, 12])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map(
    "corrected_reflectivity_horizontal",
    sweep=3,
    vmin=-20,
    vmax=60,
    projection=ccrs.PlateCarree(),
    cmap="HomeyerRainbow",
)
plt.show()
```

You can change many parameters in the graph by changing the arguments to plot_ppi_map. As you can recall from earlier. simply view these arguments in a Jupyter notebook by typing:

```{code-cell} ipython3
?display.plot_ppi_map
```

For example, let's change the colormap to something different

```{code-cell} ipython3
fig = plt.figure(figsize=[12, 12])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map(
    "corrected_reflectivity_horizontal",
    sweep=3,
    vmin=-20,
    vmax=60,
    projection=ccrs.PlateCarree(),
    cmap="Carbone42",
)
plt.show()
```

Or, let's view a different elevation scan! To do this, change the sweep parameter in the plot_ppi_map function.

```{code-cell} ipython3
fig = plt.figure(figsize=[12, 12])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map(
    "corrected_reflectivity_horizontal",
    sweep=0,
    vmin=-20,
    vmax=60,
    projection=ccrs.PlateCarree(),
    cmap="Carbone42",
)
plt.show()
```

Let's take a look at a different field - for example, correlation coefficient (`corr_coeff`)

```{code-cell} ipython3
fig = plt.figure(figsize=[12, 12])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map(
    "copol_coeff",
    sweep=0,
    vmin=0.8,
    vmax=1.0,
    projection=ccrs.PlateCarree(),
    cmap="Carbone42",
)
plt.show()
```

***
## Summary
Within this notebook, we covered the basics of working with radar data using `pyart`, including:
- Reading in a file using `xradar.io`
- Investigating the `xradar` object
- Visualizing radar data using the `RadarMapDisplay`

### What's Next
In the next few notebooks, we walk through gridding radar data, applying data cleaning methods, and advanced visualization methods!


## Resources and References
Py-ART essentials links:

* [Landing page](https://arm-doe.github.io/pyart/)
* [Examples](https://arm-doe.github.io/pyart/examples/index.html)
* [Source Code](https://github.com/ARM-DOE/pyart)
* [Mailing list](https://groups.google.com/group/pyart-users/)
* [Issue Tracker](https://github.com/ARM-DOE/pyart/issues)
