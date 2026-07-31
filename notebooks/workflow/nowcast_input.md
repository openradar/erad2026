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

::::{grid} 3

:::{grid-item}
```{image} ../../images/logos/radar_datatree_logo.png
:width: 150px
:alt: radar datatree Logo
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

(nowcast-input)=
# Gridded QPE Composite — Input for Nowcasting

The workflow you have just followed — quality control, attenuation correction, QPE, and
gridding — ends with a rainfall field on a regular Cartesian grid. This notebook opens the
**published product** of that chain: composited rain rate from both Serbian radars, on a
1 km grid at a strictly regular 5-minute cadence.

This is the dataset used as input in the **PySteps nowcasting session**. Nowcasting needs a
sequence of precipitation fields that are evenly spaced in time, on a fixed grid, in physical
units — which is precisely what the day-1 workflow produces.

```{code-cell} ipython3
:tags: [remove-cell]

import warnings

import cmweather  # noqa: F401 -- registers HomeyerRainbow
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

warnings.filterwarnings("ignore")
```

## Prerequisites

| Concepts | Importance | Notes |
| --- | --- | --- |
| [Gridding Polar Data](#gridding-polar-data) | Necessary | How the Cartesian grid is built |
| [Composite To Grid](#composite-to-grid) | Necessary | How the two radars are merged |
| [QPE](#qpe-estimation) | Necessary | The Z-R relationship used here |

* **Time to learn**: 10 minutes

## How this product was made

Every step is one you have already seen in this course, applied to both radars and to all
timesteps of a case rather than to a single scan:

| Step | Notebook |
| --- | --- |
| Open the ARCO store | [](#intro-data-access) |
| Georeference onto the LAEA grid | [](#gridding-polar-data) |
| Attenuation correction (modified Krämer) | [](#attenuation-correction-single-pol) |
| Reflectivity → rain rate (Marshall-Palmer) | [](#qpe-estimation) |
| Interpolate to the Cartesian grid | [](#gridding-polar-data) |
| Merge both radars | [](#composite-to-grid) |

Rain rate is computed in **polar space, before gridding**. With `nearest` interpolation and a
`max` composite this is mathematically identical to converting afterwards, because both
operations select an existing value and the Z-R relation is monotonic. Doing it in polar keeps
the product correct if the interpolator is ever changed to an averaging scheme, where
converting after averaging would be badly biased.

The production script lives at `tools/make_qpe_composite.py`.

## Claim Data

```{code-cell} ipython3
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
QPE_PREFIX = "erad2026-qpe"
```

(nowcast-select-case)=
```{code-cell} ipython3
case = "2017"  # "2014" stratiform | "2017" convective | "2026" clear air
```

```{code-cell} ipython3
:tags: [remove-cell]

import os
case = os.environ.get("ERAD2026_CASE", case)
```

Unlike the source radar archives, this product is a **plain Zarr v3 store**, so it opens with
`xr.open_zarr` directly — no `icechunk` session needed.

```{code-cell} ipython3
ds = xr.open_zarr(
    f"s3://{BUCKET}/{QPE_PREFIX}/qpe_composite_{case}.zarr",
    storage_options={
        "anon": True,
        "client_kwargs": {"endpoint_url": OSN_ENDPOINT},
    },
    consolidated=True,
)
display(ds)
```

The `time` axis is regular by construction — each scan is snapped to its nearest 5-minute
slot. The two radars do not scan simultaneously (their offset is around ±2 minutes and its
sign differs between cases), so snapping to a shared axis is what makes them comparable.

```{code-cell} ipython3
dt = np.unique(np.diff(ds.time.values) / np.timedelta64(1, "m"))
print(f"Case      : {case}")
print(f"Timesteps : {ds.sizes['time']}  ({str(ds.time.values[0])[:16]} → {str(ds.time.values[-1])[:16]})")
print(f"Spacing   : {dt} minutes")
print(f"Grid      : {ds.sizes['y']} × {ds.sizes['x']} @ {ds.attrs['xpixelsize']:.0f} m")
```

## Plot a Single Frame

```{code-cell} ipython3
frame = ds.rain_rate.isel(time=ds.sizes["time"] // 2)

fig, ax = plt.subplots(figsize=(9, 8))
frame.where(frame > 0.1).plot(
    ax=ax, cmap="HomeyerRainbow", vmin=0, vmax=20,
    cbar_kwargs=dict(label="rain rate (mm h$^{-1}$)"),
)
ax.set_title(f"{str(frame.time.values)[:16]} — composited rain rate")
ax.set_aspect("equal")
fig.tight_layout()
```

## Radar Coverage

`n_radars` records how many radars contributed to each cell. The lens where it equals 2 is the
overlap region; cells at 1 are seen by a single radar. This also exposes timesteps where one
radar is missing a scan.

```{code-cell} ipython3
fig, ax = plt.subplots(figsize=(9, 8))
ds.n_radars.isel(time=ds.sizes["time"] // 2).plot(
    ax=ax, levels=[0, 1, 2, 3], cmap="viridis",
    cbar_kwargs=dict(label="contributing radars"),
)
ax.set_title("Radar coverage")
ax.set_aspect("equal")
fig.tight_layout()
```

## Evolution Over the Case

```{code-cell} ipython3
wet = ds.rain_rate.where(ds.rain_rate > 0.1)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
wet.mean(dim=("x", "y")).plot(ax=ax1, marker="o", ms=3)
ax1.set_ylabel("mean rain rate\n(mm h$^{-1}$)")
ax1.set_xlabel("")
ax1.grid(alpha=0.4)

(wet.notnull().sum(dim=("x", "y")) * 1e-3).plot(ax=ax2, marker="o", ms=3, color="tab:orange")
ax2.set_ylabel("wet area\n(10³ km²)")
ax2.grid(alpha=0.4)
fig.suptitle(f"{case} — domain evolution")
fig.tight_layout()
```

## Handing This to PySteps

Nowcasting libraries want the field plus a metadata dictionary describing the grid. Everything
needed is carried in the store's attributes, so the handoff is mechanical:

```{code-cell} ipython3
metadata = {
    "projection": ds.attrs["projection"],
    "x1": ds.attrs["x1"], "x2": ds.attrs["x2"],
    "y1": ds.attrs["y1"], "y2": ds.attrs["y2"],
    "xpixelsize": ds.attrs["xpixelsize"],
    "ypixelsize": ds.attrs["ypixelsize"],
    "yorigin": ds.attrs["yorigin"],
    "unit": ds.attrs["unit"],
    "transform": None,
    "accutime": ds.attrs["accutime"],
    "threshold": ds.attrs["threshold"],
    "zerovalue": ds.attrs["zerovalue"],
}
metadata
```

The rain-rate stack itself is a plain `(time, y, x)` array. Nowcasting schemes generally work
in dBR and expect no-data as `NaN`:

```{code-cell} ipython3
R = ds.rain_rate.values  # (time, y, x), mm/h
print(f"stack shape : {R.shape}")
print(f"finite      : {np.isfinite(R).mean() * 100:.1f}%")
print(f"wet (>0.1)  : {np.nanmean(R > 0.1) * 100:.1f}% of finite cells")
```

## Caveats

```{warning}
**The 2026 case is clear-air dominated.** Only about a third of its echo above 10 dBZ is
cleanly meteorological — much of the rest is ground clutter and biological scatter, which a
Z-R relationship happily converts into non-existent rainfall. It is published for
completeness and makes an instructive *hard* case, but it is not a clean precipitation
event. Prefer 2017 (convective) or 2014 (stratiform) for evaluating nowcast skill.
```

Three further limitations are worth stating plainly:

- **A single Z-R relation is used everywhere.** Marshall-Palmer ({math}`a=200`, {math}`b=1.6`)
  was fitted to stratiform rain, so it is best justified for 2014 and least justified in the
  convective cores of 2017. No dual-polarization estimator is applied — see
  [](#attenuation-correction-dual-pol) for why R(KDP) would be the more robust choice in heavy
  rain.
- **Corrected reflectivity is capped at 59 dBZ** before the Z-R conversion. The archives
  contain echo up to 70 dBZ (Fruška Gora, 2017) and 80 dBZ (Jastrebac, 2026) — hail and
  clutter rather than rain — and an uncapped Z-R turns those into rates above
  1700 mm h{sup}`-1`. The ceiling is the same one the attenuation correction already applies
  through `constraint_dbz`, so it introduces no new tuning, but it does mean the most intense
  convective cores are truncated rather than faithfully estimated.
- **The composite takes the maximum** where both radars see a cell. This is the course's
  existing compositing rule and it is simple to reason about, but it biases rainfall high in
  the overlap region relative to a quality-weighted blend.
- **Only the lowest sweep is used**, so the field is subject to beam broadening and increasing
  beam height with range — the far edges of the domain sample precipitation well above ground.

## Next Steps

Return to the [``case`` selection step](#nowcast-select-case) and rerun with a different event
to compare a stratiform, a convective, and a clear-air field.
