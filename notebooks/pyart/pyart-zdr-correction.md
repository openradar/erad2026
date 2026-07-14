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

 Calculating ZDR offsets with xradar and Py-ART
---


## Overview
   
Within this notebook, we will cover:

1. Reading data into Py-ART
1. A little on dual pol and using correlation co-efficient and reflectivity factor to find areas of spherical droplets.
1. Statistal calculations
1. Adding the new adjusted ZDR field



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

## Claim Data

We use the ARCO data provided in [](#intro-data-access). Please refer to this notebook for details of access.

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
# prefix = "Fgora"  # single-pol, 12 sweeps × 360 az × 250 range, 2014 + 2017 + 2026
# prefix = "jastrebac_250m"  # dual-pol, 12 × 360 × 1000, 2014 only
prefix = "jastrebac_500m"  # dual-pol, 12 × 360 × 500,  2017 + 2026

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