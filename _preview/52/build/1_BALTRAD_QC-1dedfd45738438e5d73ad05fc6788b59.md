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

# Quality Control

+++

## retriev data from s3 bucket

```{code-cell} ipython3
import os
import urllib.request
from pathlib import Path

# Set the URL for the cloud
URL = "https://js2.jetstream-cloud.org:8001/"
path = "pythia/radar/erad2024/baltrad/baltrad_short_course/"
!mkdir -p data
files = ["201405190715_SUR.h5", "plrze_pvol_20120205T0430Z.h5", "sekir.h5"]
for file in files:
    file0 = os.path.join(path, file)
    name = os.path.join("data", Path(file).name)
    if not os.path.exists(name):
        print(f"downloading, {name}")
        urllib.request.urlretrieve(
            f"{URL}{file0}", os.path.join("data", Path(file).name)
        )
```

##  Import the file I/O module along with the main RAVE module containing useful constants

```{code-cell} ipython3
%matplotlib inline
import matplotlib
import _raveio, _rave
```

## Read an input ODIM_H5 file

```{code-cell} ipython3
rio = _raveio.open("data/201405190715_SUR.h5")
```

## Create a simple plotter for B-scans, elaborating the example from the I/O exercise

```{code-cell} ipython3
# Two color palettes, one used in GoogleMapsPlugin, and the other from RAVE
from GmapColorMap import dbzh as dbzp
from rave_win_colors import continuous_MS as vradp


# Convert a 768-list palette to a matplotlib colorlist
def make_colorlist(pal):
    colorlist = []
    for i in range(0, len(pal), 3):
        colorlist.append([pal[i] / 255.0, pal[i + 1] / 255.0, pal[i + 2] / 255.0])
    return colorlist


# Convert lists to colormaps
dbzcl = make_colorlist(dbzp)
vradcl = make_colorlist(vradp)

# Then create a simple plotter
import matplotlib.pyplot as plt

# from types import StringType
StringType = type("")


def plot(data, colorlist=dbzcl, title="B-scan"):
    mini, maxi = data.shape.index(min(data.shape)), data.shape.index(max(data.shape))
    figsize = (16, 12) if mini == 0 else (12, 8)
    fig = plt.figure(figsize=figsize)
    plt.title(title)
    clist = (
        colorlist
        if type(colorlist) == StringType
        else matplotlib.colors.ListedColormap(colorlist)
    )
    plt.imshow(data, cmap=clist, clim=(0, 255))
    plt.colorbar(shrink=float(data.shape[mini]) / data.shape[maxi])
```

## Access the polar volume and plot VRAD data from the lowest scan

```{code-cell} ipython3
pvol = rio.object
plot(pvol.getScan(0).getParameter("VRADH").getData(), vradcl, "Original VRAD")
```

## Dealias the volume

```{code-cell} ipython3
import _dealias

ret = _dealias.dealias(pvol)
```

### Check whether the first scan's been dealiased

```{code-cell} ipython3
print("This first scan is dealiased: %s" % str(_dealias.dealiased(pvol.getScan(0))))
```

### Replot for comparison

```{code-cell} ipython3
plot(pvol.getScan(0).getParameter("VRADH").getData(), vradcl, "Dealiased VRAD")
```

## Shift gears - back to reflectivity

```{code-cell} ipython3
rio = _raveio.open("data/plrze_pvol_20120205T0430Z.h5")
pvol = rio.object
plot(pvol.getScan(0).getParameter("DBZH").getData(), title="Original DBZH")
```

## Use the bRopo package's quality plugin to identify and remove non-precipitation echoes

```{code-cell} ipython3
import odc_polarQC
import warnings

warnings.filterwarnings("ignore")  # Suppress SyntaxWarning from Python2 code

odc_polarQC.algorithm_ids = ["ropo"]
pvol = odc_polarQC.QC(pvol)
```

### Plot the resulting DBZH

```{code-cell} ipython3
plot(pvol.getScan(0).getParameter("DBZH").getData(), title="DBZH after bRopo")
```

## Topographical beam-blockage QC using the beamb package's quality plugin

```{code-cell} ipython3
import time

odc_polarQC.algorithm_ids = ["beamb"]
before = time.time()
pvol = odc_polarQC.QC(pvol)
after = time.time()
print("beamb runtime = %2.2f seconds" % (after - before))
```

## Probability of overshooting

```{code-cell} ipython3
odc_polarQC.algorithm_ids = ["rave-overshooting"]
pvol = odc_polarQC.QC(pvol)
```

## Accessing and manging data quality fields

```{code-cell} ipython3
scan = pvol.getScan(0)
print("Scan contains %i quality fields" % scan.getNumberOfQualityFields())
```

```{code-cell} ipython3
for i in range(scan.getNumberOfQualityFields()):
    qf = scan.getQualityField(i)
    print("Quality field %i has identifier %s" % (i, qf.getAttribute("how/task")))
```

## Plot quality fields

+++

### Beam blockage

```{code-cell} ipython3
bb = scan.getQualityFieldByHowTask("se.smhi.detector.beamblockage")
plot(bb.getData(), "binary", "Quality indicator for beam blockage")
```

### Probability of non-precipitation

```{code-cell} ipython3
bb = scan.getQualityFieldByHowTask("fi.fmi.ropo.detector.classification")
plot(bb.getData(), "binary", "Quality indicator for ropo")
```

### Probability of overshooting

```{code-cell} ipython3
bb = scan.getQualityFieldByHowTask("se.smhi.detector.poo")
plot(bb.getData(), "binary", "Quality indicator for PoO")
```

## Chaining algorithms - new data

```{code-cell} ipython3
rio = _raveio.open("data/sekir.h5")
pvol = rio.object

odc_polarQC.algorithm_ids = [
    "ropo",
    "beamb",
    "radvol-att",
    "radvol-broad",
    "rave-overshooting",
]
pvol = odc_polarQC.QC(pvol)
```

```{code-cell} ipython3
scan = pvol.getScan(0)
att = scan.getQualityField(2)
plot(att.getData(), "binary", "Attenuation")
```

## "Total Quality"

```{code-cell} ipython3
odc_polarQC.algorithm_ids = ["qi-total"]
pvol = odc_polarQC.QC(pvol)
```

```{code-cell} ipython3
qitot = scan.getQualityField(5)
plot(qitot.getData(), "binary", "Total quality index")
```

```{code-cell} ipython3

```
