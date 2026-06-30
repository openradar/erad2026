---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.3
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

<img src="../../images/logos/arm_logo.png" width=500 alt="ARM Logo"></img>

+++

# Py-ART Corrections
---

+++

## Overview
   
Within this notebook, we will cover:

1. Intro to radar aliasing.
1. Calculation of velocity texture using Py-ART
1. Dealiasing the velocity field

## Prerequisites
| Concepts | Importance | Notes |
| --- | --- | --- |
| [Py-ART Basics](pyart-basics) | Helpful | Basic features |
| [Matplotlib Basics](https://foundations.projectpythia.org/core/matplotlib/matplotlib-basics.html) | Helpful | Basic plotting |
| [NumPy Basics](https://foundations.projectpythia.org/core/numpy/numpy-basics.html) | Helpful | Basic arrays |

- **Time to learn**: 15 minutes
---

+++

## Imports

```{code-cell} ipython3
import os
import warnings
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pyart
import fsspec
import icechunk
import xarray as xr

OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"

warnings.filterwarnings('ignore')
```

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
radar_vel = pyart.aux_io.read_rainbow_wrl('data/fgora_sample/2014051500012000V.vol')
radar = pyart.aux_io.read_rainbow_wrl('data/fgora_sample/2014051500012000dBZ.vol')
radar.fields["velocity"] = radar_vel.fields["velocity"].copy()
```

### Plot a quick-look of reflectivity and velocity
We can start by taking a quick look at the reflectivity and velocity fields. Notice how the velocity field is **rather messy**, indicated by the speckles and high/low values directly next to each other

```{code-cell} ipython3
fig = plt.figure(figsize=[8, 10])
ax = plt.subplot(211, projection=ccrs.PlateCarree())
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('reflectivity',
                     ax=ax,
                     sweep=0,
                     resolution='50m',
                     vmin=0,
                     vmax=60, 
                     lat_lines=[43, 44, 45, 46, 47],
                     projection=ccrs.PlateCarree(),
                     cmap='HomeyerRainbow')

ax2 = plt.subplot(2,1,2,projection=ccrs.PlateCarree())
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('velocity',
                     ax=ax2,
                     sweep=0,
                     resolution='50m',
                     lat_lines=[43, 44, 45, 46, 47],
                     lon_lines=[16, 17, 18, 19, 20, 21, 22, 23],
                     vmin=-10,
                     vmax=10, 
                     projection=ccrs.PlateCarree(),
                     cmap='balance')
plt.show()
```

## Dealiasing our Velocity

### An Overview of Aliasing

+++

The radial velocity measured by the radar is mesasured by detecing the phase shift between the transmitted pulse and the pulse recieved by the radar. However, using this methodology, it is only possible to detect phase shifts within $\pm 2\pi$ due to the periodicity of the transmitted wave. Therefore, for example, a phase shift of $3\pi$ would erroneously be detected as a phase shift of $-\pi$ and give an incorrect value of velocity when retrieved by the radar. This phenomena is called aliasing. The maximium unambious velocity that can be detected by the radar before aliasing occurs is called the Nyquist velocity.

In the next example, you will see an example of aliasing occurring, where the values of +10 m/s abruptly transition into a region of -10 m/s, with -5 m/s in the middle of the region around 45 N, 21 E.

+++

### Calculate Velocity Texture

First, for dealiasing to work efficiently, we need to use a GateFilter. Notice that, this time, the data shown does not give us a nice gate_id. This is what raw data looks like, and we need to do some preprocessing on the data to remove noise and clutter. Thankfully, Py-ART gives us the capability to do this. As a simple filter in this example, we will first calculate the velocity texture using Py-ART's [`calculate_velocity_texture`](https://arm-doe.github.io/pyart/API/generated/pyart.retrieve.calculate_velocity_texture.html) function. The velocity texture is the standard deviation of velocity surrounding a gate. This will be higher in the presence of noise.

Let's investigate this function first...

```{code-cell} ipython3
pyart.retrieve.calculate_velocity_texture?
```

### Determining the Right Parameters
You'll notice that we need:
- Our radar object
- The name of our velocity field
- The number of gates within our window to use to calculate the texture
- The nyquist velocity

PyART normally supports the retrieval of the nyquist velocity through its `instrument_parameters` attribute of the `Radar` object. However, the Nyquist velocity is not stored in these files. Therefore, we will have to find the maximum of the velocity field in order to tease out the Nyquist velocity.

```{code-cell} ipython3
nyquist_velocity = radar.fields["velocity"]["data"].max()
nyquist_velocity
```

While the nyquist velocity is stored as an array, we see that these are all the same value...

+++

### Calculate Velocity Texture and Filter our Data
Now that we have an ide?a of which parameters to pass in, let's calculate velocity texture!

```{code-cell} ipython3
vel_texture = pyart.retrieve.calculate_velocity_texture(radar,
                                                        vel_field='velocity',
                                                        nyq=nyquist_velocity)
vel_texture
```

The `pyart.retrieve.calculate_velocity_texture` function results in a data dictionary, including the actual data, as well as metadata. We can add this to our `radar` object, by using the `radar.add_field` method, passing the name of our new field (`"texture"`), the data dictionary (`vel_texture`), and a clarification that we want to replace the existing velocity texture field if it already exists in our radar object (`replace_existing=True`)

```{code-cell} ipython3
radar.add_field('texture', vel_texture, replace_existing=True)
```

#### Plot our Velocity Texture Field

+++

Now that we have our velocity texture field added to our radar object, let's plot it!

```{code-cell} ipython3
fig = plt.figure(figsize=[8, 8])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('texture',
                     sweep=0,
                     resolution='50m',
                     vmin=0,
                     vmax=10, 
                     projection=ccrs.PlateCarree(),
                     cmap='balance')
plt.show()
```

#### Determine a Suitable Velocity Texture Threshold

+++

Plot a histogram of velocity texture to get a better idea of what values correspond to hydrometeors and what values of texture correspond to artifacts.

In the below example, a threshold of 3 would eliminate most of the peak corresponding to noise around 6 while preserving most of the values in the peak of ~0.5 corresponding to hydrometeors.

```{code-cell} ipython3
hist, bins = np.histogram(radar.fields['texture']['data'][np.isfinite(radar.fields['texture']['data'])],
                          bins=150)
bins = (bins[1:]+bins[:-1])/2.0

plt.plot(bins,
         hist,
         label='Velocity Texture Frequency')
plt.axvline(3,
            color='r',
            label='Proposed Velocity Texture Threshold')

plt.xlabel('Velocity texture')
plt.ylabel('Count')
plt.legend()
```

In this example, we only see a unimodal distribution of velocity texture. This is because the Rainbow files already have noise filtering applied by the radar's internal processing. However, if the default processing does not remove enough noise and clutter, then it can further be refined by following the steps in this notebook.

+++

#### Setup a Gatefilter Object and Apply our Threshold

+++

Now we can set up our GateFilter ([`pyart.filters.GateFilter`](https://arm-doe.github.io/pyart/API/generated/pyart.filters.GateFilter.html#pyart.filters.GateFilter)), which allows us to easily apply masks and filters to our radar object.

```{code-cell} ipython3
gatefilter = pyart.filters.GateFilter(radar)
gatefilter
```

We discovered that a velocity texture threshold of **only including values below 3** would be suitable for this dataset, we use the `.exclude_above` method, specifying we want to exclude `texture` values above 3.

```{code-cell} ipython3
gatefilter.exclude_above('texture', 3)
```

#### Plot our Filtered Data

+++

Now that we have created a gatefilter, filtering our data using the velocity texture, let's plot our data!

We need to pass our gatefilter to the `plot_ppi_map` to apply it to our plot.

```{code-cell} ipython3
# Plot our Unfiltered Data
fig = plt.figure(figsize=[8, 10])
ax = plt.subplot(211, projection=ccrs.PlateCarree())
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('velocity',
                     title='Raw Radial Velocity (no filter)',
                     ax=ax,
                     sweep=0,
                     resolution='50m',
                     vmin=-17,
                     vmax=17,
                     projection=ccrs.PlateCarree(),
                     colorbar_label='Radial Velocity (m/s)',
                     cmap='balance')

ax2 = plt.subplot(2,1,2,projection=ccrs.PlateCarree())

# Plot our filtered data
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('velocity',
                     title='Radial Velocity with Velocity Texture Filter',
                     ax=ax2,
                     sweep=0,
                     resolution='50m',
                     vmin=-17,
                     vmax=17, 
                     projection=ccrs.PlateCarree(),
                     colorbar_label='Radial Velocity (m/s)',
                     gatefilter=gatefilter,
                     cmap='balance')
plt.show()
```

### Dealias the Velocity Using the Region-Based Method

+++

At this point, we can use the [`dealias_region_based`](https://arm-doe.github.io/pyart/API/generated/pyart.correct.dealias_region_based.html) to dealias the velocities and then add the new field to the radar!

```{code-cell} ipython3
velocity_dealiased = pyart.correct.dealias_region_based(radar,
                                                        vel_field='velocity',
                                                        nyquist_vel=nyquist_velocity,
                                                        centered=True,
                                                        gatefilter=gatefilter)

# Add our data dictionary to the radar object
radar.add_field('corrected_velocity', velocity_dealiased, replace_existing=True)
```

#### Plot our Cleaned, Dealiased Velocities

+++

Plot the new velocities, which now look much more realistic.

```{code-cell} ipython3
fig = plt.figure(figsize=[8, 8])
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('corrected_velocity',
                     sweep=0,
                     resolution='50m',
                     vmin=-40,
                     vmax=40, 
                     projection=ccrs.PlateCarree(),
                     colorbar_label='Radial Velocity (m/s)',
                     cmap='balance',
                     gatefilter=gatefilter)
plt.show()
```

## Compare our Raw Velocity Field to our Dealiased, Cleaned Velocity Field
As a last comparison, let's compare our raw, uncorrected velocities with our cleaned velocities, after applying the velocity texture threshold and dealiasing algorithm

```{code-cell} ipython3
# Plot our Unfiltered Data
fig = plt.figure(figsize=[8, 10])
ax = plt.subplot(211, projection=ccrs.PlateCarree())
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('velocity',
                     title='Raw Radial Velocity (no filter)',
                     ax=ax,
                     sweep=0,
                     resolution='50m',
                     vmin=-30,
                     vmax=30,
                     projection=ccrs.PlateCarree(),
                     colorbar_label='Radial Velocity (m/s)',
                     cmap='balance')

ax2 = plt.subplot(2,1,2,projection=ccrs.PlateCarree())

# Plot our filtered, dealiased data
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('corrected_velocity',
                     title='Radial Velocity with Velocity Texture Filter and Dealiasing',
                     ax=ax2,
                     sweep=0,
                     resolution='50m',
                     vmin=-30,
                     vmax=30, 
                     projection=ccrs.PlateCarree(),
                     gatefilter=gatefilter,
                     colorbar_label='Radial Velocity (m/s)',
                     cmap='balance')
plt.show()
```

## Conclusions
Within this lesson, we walked through how to apply radial velocity corrections to a dataset, filtering based on the velocity texture and using a regional dealiasing algorithm.

### What's Next
In the next few notebooks, we walk through gridding radar data and advanced visualization methods!

+++

## Resources and References
Py-ART essentials links:

* [Landing page](arm-doe.github.io/pyart/)
* [Examples](https://arm-doe.github.io/pyart/examples/index.html)
* [Source Code](github.com/ARM-DOE/pyart)
* [Mailing list](groups.google.com/group/pyart-users/)
* [Issue Tracker](github.com/ARM-DOE/pyart/issues)

```{code-cell} ipython3

```
