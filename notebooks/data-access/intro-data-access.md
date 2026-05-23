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
import fsspec
import icechunk
import xarray as xr
import xradar

OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```


+++

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

```python
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

+++

## Part 2: ARCO Zarr access

The same data as **Analysis-Ready Cloud-Optimized (ARCO) Zarr stores** — pre-merged, pre-aligned, and indexed along a `vcp_time` dimension spanning all three dates (2014, 2017, 2026). Built with [`raw2zarr`](https://github.com/aladinor/raw2zarr) following the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) data model by [Atmoscale](https://atmoscale.ai/).

Each store is an [icechunk](https://icechunk.io/)-versioned Zarr v3 archive. The top-level group is the task name, with 12 sweep children containing CF-compliant moment arrays indexed by `(vcp_time, azimuth, range)`.

### Open the FGora ARCO store

```{code-cell} ipython3
fgora_storage = icechunk.s3_storage(
    bucket=BUCKET,
    prefix="fgora",
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
fgora_repo = icechunk.Repository.open(fgora_storage)
fgora_dt = xr.open_datatree(
    fgora_repo.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
)
fgora_dt
```

### Open the Jastrebac ARCO store

```{code-cell} ipython3
jastrebac_storage = icechunk.s3_storage(
    bucket=BUCKET,
    prefix="jastrebac",
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
jastrebac_repo = icechunk.Repository.open(jastrebac_storage)
jastrebac_dt = xr.open_datatree(
    jastrebac_repo.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
)
jastrebac_dt
```

### Inspect sweep dimensions and moments

```{code-cell} ipython3
for name, dt, task in [
    ("FGora", fgora_dt, "DEJSTVO"),
    ("Jastrebac", jastrebac_dt, "JSTB_250_Dp_leto"),
]:
    ds = dt[f"/{task}/sweep_0"].to_dataset()
    moms = sorted(v for v in ds.data_vars
                  if v not in {"sweep_fixed_angle", "ray_elevation_angle", "sweep_number"})
    print(f"{name:<12s} /{task}  dims={dict(ds.sizes)}  moments={moms}")
```

+++

## Summary

| | Raw `.vol` files | ARCO Zarr (icechunk) |
|---|---|---|
| **Location** | `s3://nexrad-arco/{site}_vol/{date}/*.vol` | `s3://nexrad-arco/{site}/` |
| **Format** | Rainbow binary (one moment per file) | Zarr v3, chunked, CF-compliant |
| **Access** | `fsspec.open_local` + `xradar` | `icechunk` + `xr.open_datatree` |
| **Time indexing** | Manual (parse filenames) | Built-in `vcp_time` dimension |
| **Best for** | Re-processing, format-specific QC | Analysis, visualization, ML |
| **Coverage** | 3 dates × 2 sites (1188 files) | 3 dates × 2 sites (196 volumes) |

### References

- [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) — hierarchical data model for ARCO radar archives
- [Atmoscale](https://atmoscale.ai/) — cloud-native weather radar infrastructure
- [raw2zarr](https://github.com/aladinor/raw2zarr) — the conversion pipeline that produced these stores
- [icechunk](https://icechunk.io/) — version-controlled Zarr storage
- [xradar](https://docs.openradarscience.org/projects/xradar/) — xarray-based radar I/O library
