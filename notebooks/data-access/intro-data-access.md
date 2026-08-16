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

(intro-data-access)=
# Data Access — Serbian Rainbow Radar

![radar-datatree](https://atmoscale.github.io/radar-datatree/_images/logo-banner1.png)

This notebook shows how to access the ERAD 2026 Serbian radar dataset hosted on the [NSF Open Storage Network (OSN)](https://www.openstoragenetwork.org/), part of the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) initiative by [Atmoscale](https://atmoscale.ai/). Two access patterns are demonstrated:

| Access pattern | What you get | When to use |
|---|---|---|
| **Raw `.vol` files** | Per-moment Rainbow binary files | Original vendor format (QC, re-processing) |
| **ARCO Zarr stores** | Analysis-Ready Cloud-Optimized xarray DataTrees | Instant slicing by time, elevation, or variable |

**Two sites, three dates each (2014, 2017, 2026):**

| Site | Radar | Type | Task | Moments |
|---|---|---|---|---|
| Fruska Gora (FGora) | Selex/Leonardo | Single-pol | `DEJSTVO` | DBZH, DBTH, VRADH, WRADH |
| Jastrebac | Selex/Leonardo | Dual-pol | `JSTB_250_Dp_leto` | + ZDR, KDP, PHIDP, RHOHV, uPhiDP |

+++

## Setup

```{code-cell} ipython3
import cmweather  # noqa: F401 -- registers the HomeyerRainbow colormap
import fsspec
import icechunk
import rioxarray  # noqa: F401 -- registers the .rio accessor used for the composite CRS
import xarray as xr
import xradar

OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

***

## Part 1: Raw `.vol` file access

Rainbow `.vol` files are stored per-moment: each file holds one radar variable (e.g., reflectivity `dBZ`, velocity `V`) across all 12 elevation sweeps for one timestamp. A complete volume is reconstructed from the 4 (single-pol) or 9 (dual-pol) per-moment files sharing the same `YYYYMMDDHHMMSSss` filename prefix.

### Browse available files

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

### Open a single `.vol` file

xradar's Rainbow reader uses memory-mapped I/O, so it needs a local path. `fsspec.open_local` with `simplecache` downloads on first access and caches locally.

```{code-cell} ipython3
fgora_raw = sorted(fs.glob(f"{BUCKET}/fgora_vol/**/*.vol"))
sample_file = fgora_raw[2]  # a dBZ file
print(f"File: {sample_file.split('/')[-1]}")

local_path = fsspec.open_local(
    f"simplecache::s3://{sample_file}",
    s3={"anon": True, "client_kwargs": {"endpoint_url": OSN_ENDPOINT}},
)
dtree_raw = xradar.io.open_rainbow_datatree(local_path)
dtree_raw
```

```{code-cell} ipython3
sweep0_raw = dtree_raw["/sweep_0"].to_dataset(inherit="all_coords")
```

### Download files locally (optional)

If you prefer working with local files, you can download a single timestamp's worth of per-moment files:

```{code-cell} ipython3
from pathlib import Path

download_dir = Path("data/fgora_sample")
download_dir.mkdir(parents=True, exist_ok=True)

sample_ts = "2014051500012000"
for remote in [f for f in fgora_raw if sample_ts in f]:
    local = download_dir / Path(remote).name
    if not local.exists():
        fs.get(remote, str(local))
    print(f"  {local.name}")
```

***

## Part 2: ARCO Zarr access

The same data as **Analysis-Ready Cloud-Optimized (ARCO) Zarr stores** — pre-merged, pre-aligned, and indexed along a `vcp_time` dimension. Each store is an [icechunk](https://icechunk.io/)-versioned Zarr v3 archive following the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) data model by [Atmoscale](https://atmoscale.ai/). The top-level group is the task name, with 12 sweep children containing CF-compliant moment arrays indexed by `(vcp_time, azimuth, range)`.

**Three stores** are published to keep `range` axes physically consistent — Jastrebac splits across two stores because the 2014 dataset uses 250 m bins (1000 bins → 250 km range) while the 2017 and 2026 datasets use 500 m bins (~500 bins → 250 km range). Merging them into a single `range` axis would mis-label the 500 m data in physical space.

| Store prefix | Coverage | Bin width × count |
|---|---|---|
| `Fgora/` | FGora, 2014 + 2017 + 2026 | 1000 m × 250 |
| `jastrebac_250m/` | Jastrebac, 2014 | 250 m × 1000 |
| `jastrebac_500m/` | Jastrebac, 2017 + 2026 | 500 m × 500 |

### Open one store

Below opens **FGora** (single-pol, spans all three dates). To open one of the Jastrebac stores instead, swap the commented-out `prefix=` line in.

```{code-cell} ipython3
prefix = "Fgora"  # single-pol, 12 sweeps × 360 az × 250 range, 2014 + 2017 + 2026
# prefix = "jastrebac_250m"  # dual-pol, 12 × 360 × 1000, 2014 only
# prefix = "jastrebac_500m"  # dual-pol, 12 × 360 × 500,  2017 + 2026

storage = icechunk.s3_storage(
    bucket=BUCKET,
    prefix=prefix,
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
repo = icechunk.Repository.open(storage)
dt = xr.open_datatree(
    repo.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
)
dt
```

### Inspect dimensions, range axis, and moments

```{code-cell} ipython3
task = next(iter(dt.children))  # "DEJSTVO" or "JSTB_250_Dp_leto"
ds = dt[f"/{task}/sweep_0"].to_dataset()
rng = ds["range"]
moms = sorted(
    v for v in ds.data_vars
    if v not in {"sweep_fixed_angle", "ray_elevation_angle", "sweep_number"}
)
print(f"Task    : /{task}")
print(f"Dims    : {dict(ds.sizes)}")
print(
    f"Range   : {int(rng.size)} bins @ {float(rng[1] - rng[0]):.0f} m"
    f"  (first gate {float(rng[0]):.0f} m, last {float(rng[-1]):.0f} m)"
)
print(f"Moments : {moms}")
```

***

## Part 3: Gridded QPE composite

The two stores above are **polar** data, one radar each. The course workflow turns them into a
single **Cartesian composite** — quality-controlled, attenuation-corrected, converted to rain
rate and merged across both radars onto a 1 km grid. See [](#composite-to-grid-qc) for how it
is produced.

Unlike the ARCO stores, this product is a **plain Zarr v3 store**, so no `icechunk` session is
needed — `xr.open_zarr` opens it directly.

```{code-cell} ipython3
composite_url = f"s3://{BUCKET}/composite.zarr"
```

```{important}
Two arguments matter here:

* `consolidated=False` — this is a **Zarr v3** store, and consolidated metadata is not part of
  the v3 specification. Requesting it raises `ValueError: Consolidated metadata requested ...
  but not found`. Zarr v3 discovers metadata efficiently without it.
* `decode_coords="all"` — this tells `xarray` to honour the CF `grid_mapping` attribute and
  restore `spatial_ref` as a coordinate. Without it the projection is still in the store but
  arrives as a plain data variable, and `.rio.crs` returns `None`.
```

```{code-cell} ipython3
comp = xr.open_zarr(
    composite_url,
    storage_options={"anon": True, "client_kwargs": {"endpoint_url": OSN_ENDPOINT}},
    consolidated=False,
    decode_coords="all",
)
comp
```

The store is self-describing — CF standard names, units and the projection travel with it:

```{code-cell} ipython3
print(f"Conventions : {comp.attrs['Conventions']}")
print(f"CRS         : {comp.rio.crs.to_string() if comp.rio.crs else 'not decoded'}")
print(f"Grid        : {comp.sizes['y']} × {comp.sizes['x']} @ 1 km")
print(f"Times       : {comp.sizes['vcp_time']} steps, "
      f"{str(comp.vcp_time.values[0])[:16]} → {str(comp.vcp_time.values[-1])[:16]}")
for v in comp.data_vars:
    a = comp[v].attrs
    print(f"  {v:10} [{a.get('units', '-'):7}] {a.get('long_name', '')}")
```

| Variable | Units | Meaning |
|---|---|---|
| `DBZH` | dBZ | Attenuation-corrected reflectivity composite |
| `rain_rate` | mm h⁻¹ | Rain rate from Marshall-Palmer Z-R |
| `n_radars` | 1 | How many radars saw each cell (0, 1 or 2) |

```{code-cell} ipython3
rr = comp.rain_rate.isel(vcp_time=comp.sizes["vcp_time"] // 2)
rr.where(rr > 0.1).plot(cmap="HomeyerRainbow", vmin=0, vmax=30, figsize=(8, 7),
                        cbar_kwargs=dict(label="rain rate (mm h$^{-1}$)"))
```

***

## Summary

| | Raw `.vol` files | ARCO Zarr (icechunk) | QPE composite (Zarr) |
|---|---|---|---|
| **Location** | `s3://nexrad-arco/{site}_vol/{date}/*.vol` | `s3://nexrad-arco/{Fgora, jastrebac_250m, jastrebac_500m}/` | `s3://nexrad-arco/composite.zarr` |
| **Format** | Rainbow binary (one moment per file) | Zarr v3, chunked, CF-compliant | Zarr v3, CF-1.10, self-describing |
| **Geometry** | Polar, per radar | Polar, per radar | Cartesian 1 km LAEA, both radars merged |
| **Access** | `fsspec.open_local` + `xradar` | `icechunk` + `xr.open_datatree` | `xr.open_zarr(..., decode_coords="all")` |
| **Time indexing** | Manual (parse filenames) | Built-in `vcp_time` dimension | Regular 5-minute `vcp_time` |
| **Best for** | Re-processing, format-specific QC | Analysis, visualization, ML | Nowcasting, hydrology, verification |
| **Coverage** | 3 dates × 2 sites (1188 files) | FGora 3 dates + Jastrebac 2014 (250 m grid) + Jastrebac 2017/2026 (500 m grid) — 3 stores, 196 volumes total | Lowest sweep (0.5°), one case per store |

### References

- [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) — hierarchical data model for ARCO radar archives
- [Atmoscale](https://atmoscale.ai/) — cloud-native weather radar infrastructure
- [icechunk](https://icechunk.io/) — version-controlled Zarr storage
- [xradar](https://docs.openradarscience.org/projects/xradar/) — xarray-based radar I/O library
