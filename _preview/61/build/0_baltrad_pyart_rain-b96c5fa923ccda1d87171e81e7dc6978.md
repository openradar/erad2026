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

# Rain Rate retrieval with Py-ART

In this notebook, an ODIM_H5 file is read using BALTRAD. Then the rain rate is determined from the calculated specific attenuation using Py-ART.
This is a severe flooding case from July 8, 2013 in Toronto, Canada, with radar data from the King City, Ontario, radar.

+++

## retrieve data from s3 bucket

```{code-cell} ipython3
import os
import urllib.request
from pathlib import Path

# Set the URL for the cloud
URL = "https://js2.jetstream-cloud.org:8001/"
path = "pythia/radar/erad2024/baltrad/pyart2baltrad"
!mkdir -p data
files = ["WKR_201307082030.h5"]
for file in files:
    file0 = os.path.join(path, file)
    name = os.path.join("data", Path(file).name)
    if not os.path.exists(name):
        print(f"downloading, {name}")
        urllib.request.urlretrieve(f"{URL}{file0}", name)
```

```{code-cell} ipython3
%matplotlib inline
```

Import the necessary modules.

```{code-cell} ipython3
import numpy as np
import pyart
import baltrad_pyart_bridge as bridge  # routines to pass data from Py-ART and BALTRAD
import _raveio  # BALTRAD's input/output module
import cmweather
```

Read in the data using RAVE (a component of BALTRAD)

+++

# Rain rate retrieval using specific attenuation using BALTRAD and Py-ART

```{code-cell} ipython3
rio = _raveio.open("data/WKR_201307082030.h5")
```

Convert the data to a Py-ART Radar object.

```{code-cell} ipython3
radar = bridge.raveio2radar(rio)
```

Examine some of the radar moments.

```{code-cell} ipython3
display = pyart.graph.RadarDisplay(radar)
```

```{code-cell} ipython3
display.plot_ppi("DBZH", 0, vmin=-15, vmax=60)
display.plot_range_rings([50, 100, 150])
```

```{code-cell} ipython3
display.plot_ppi("PHIDP", 0, vmin=0, vmax=180, cmap="ChaseSpectral")
display.plot_range_rings([50, 100, 150])
```

```{code-cell} ipython3
display.plot_ppi("RHOHV", 0, vmin=0, vmax=1.0, mask_outside=False, cmap="CM_rhohv")
display.plot_range_rings([50, 100, 150])
```

```{code-cell} ipython3
display.plot_ppi("SQIH", 0, vmin=0, vmax=1, mask_outside=False, cmap="ChaseSpectral")
display.plot_range_rings([50, 100, 150])
```

Calculate the specific attenuation and attenuation corrected reflectivity using Py-ART, add these field to the radar object.

```{code-cell} ipython3
radar.info()
```

```{code-cell} ipython3
spec_at, cor_z = pyart.correct.calculate_attenuation(
    radar,
    0,
    doc=0,
    refl_field="DBZH",
    ncp_field="SQIH",
    rhv_field="RHOHV",
    phidp_field="PHIDP",
    fzl=8000,
)
# use the parameter below for a more 'cleanup up' attenuation field
# ncp_min=-1, rhv_min=-1)
```

```{code-cell} ipython3
radar.info()
```

```{code-cell} ipython3
radar.add_field("specific_attenuation", spec_at)
radar.add_field("corrected_reflectivity", cor_z)
```

Examine these two new fields.

```{code-cell} ipython3
display.plot_ppi("specific_attenuation", 0, vmin=0, vmax=0.1)
display.plot_range_rings([50, 100, 150])
```

```{code-cell} ipython3
display.plot_ppi("corrected_reflectivity", 0, vmin=-15, vmax=60)
display.plot_range_rings([50, 100, 150])
```

Calculate the rain rate from the specific attenuation using a power law determined from the ARM Southern Great Plains site.  Mask values where the attenuation is not valid (when the cross correlation ratio or signal quality is low). Add this field to the radar object.

```{code-cell} ipython3
R = 300.0 * (radar.fields["specific_attenuation"]["data"]) ** 0.89
rain_rate_dic = pyart.config.get_metadata("rain_rate")
rain_rate_dic["units"] = "mm/hr"
rate_not_valid = np.logical_or(
    (radar.fields["SQIH"]["data"] < 0.4), (radar.fields["RHOHV"]["data"] < 0.8)
)
rain_rate_dic["data"] = np.ma.masked_where(rate_not_valid, R)
# fill the missing values with 0 for a nicer plot
rain_rate_dic["data"] = np.ma.filled(rain_rate_dic["data"], 0)
```

```{code-cell} ipython3
radar.add_field("RATE", rain_rate_dic)
```

Examine the rain rate

```{code-cell} ipython3
display.plot_ppi("RATE", 0, vmin=0, vmax=50.0)
```

Create a new RaveIO object from the Py-ART radar object and write this out using Rave

```{code-cell} ipython3
rio_out = bridge.radar2raveio(radar)
```

```{code-cell} ipython3
container = _raveio.new()
container.object = rio_out.object
container.save("data/WKR_201307082030_with_rain_rate.h5")

import os

print(
    "ODIM_H5 file is %i bytes large"
    % os.path.getsize("data/WKR_201307082030_with_rain_rate.h5")
)
```
