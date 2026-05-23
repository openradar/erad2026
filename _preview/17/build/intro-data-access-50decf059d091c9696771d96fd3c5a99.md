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

This notebook shows how to access the ERAD 2026 Serbian radar dataset hosted on the [NSF Open Storage Network (OSN)](https://www.openstoragenetwork.org/), part of the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) initiative by [Atmoscale](https://atmoscale.ai/). Two complementary access patterns are demonstrated:

| Access pattern | What you get | When to use |
|---|---|---|
| **Raw `.vol` files** | Per-moment Rainbow binary files, streamed or downloaded | When you need the original vendor format (e.g., for vendor-specific QC, re-processing with different parameters) |
| **ARCO Zarr stores** | Analysis-Ready Cloud-Optimized xarray DataTrees (icechunk-versioned) | When you want instant slicing by time, elevation, or variable — no file-level I/O |

**Two sites, three dates each (2014, 2017, 2026):**

| Site | Radar | Type | Task (scan program) | Moments |
|---|---|---|---|---|
| Fruska Gora (FGora) | Selex/Leonardo | Single-pol | `DEJSTVO` | DBZH, DBTH, VRADH, WRADH |
| Jastrebac | Selex/Leonardo | Dual-pol | `JSTB_250_Dp_leto` | + ZDR, KDP, PHIDP, RHOHV, uPhiDP |

+++

## Setup

```{code-cell} ipython3
import fsspec
import xarray as xr
import xradar
import matplotlib.pyplot as plt
import numpy as np

# OSN endpoint — public read access, no credentials needed.
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

+++

## Part 1: Raw `.vol` file access

Rainbow `.vol` files are stored per-moment: each file holds one radar variable (e.g., reflectivity `dBZ`, velocity `V`) across all 12 elevation sweeps for one timestamp. A complete volume scan is reconstructed from the 4 (single-pol) or 9 (dual-pol) per-moment files sharing the same `YYYYMMDDHHMMSSss` filename prefix.

### Browse available files

```{code-cell} ipython3
# Anonymous access to the OSN bucket via fsspec's S3 backend.
fs = fsspec.filesystem(
    "s3",
    anon=True,
    client_kwargs={"endpoint_url": OSN_ENDPOINT},
)

# List all raw .vol files for FGora (single-pol)
fgora_raw = sorted(fs.glob(f"{BUCKET}/fgora_vol/**/*.vol"))
print(f"FGora raw files: {len(fgora_raw)}")
for f in fgora_raw[:8]:
    print(f"  {f}")
print(f"  ... ({len(fgora_raw) - 8} more)")
```

```{code-cell} ipython3
# List Jastrebac (dual-pol) — 9 moments per timestamp
jastrebac_raw = sorted(fs.glob(f"{BUCKET}/jastrebac_vol/**/*.vol"))
print(f"Jastrebac raw files: {len(jastrebac_raw)}")
```

### Stream and open a single `.vol` file

No download needed — `xradar` reads directly from the remote file via `fsspec`'s `simplecache` protocol.

```{code-cell} ipython3
# Pick the first FGora reflectivity file
sample_file = fgora_raw[2]  # dBZ file
print(f"Streaming: {sample_file}")

# Open via simplecache (caches locally on first read, then reuses)
with fsspec.open(
    f"simplecache::s3://{sample_file}",
    s3={"anon": True, "client_kwargs": {"endpoint_url": OSN_ENDPOINT}},
) as f:
    dtree = xradar.io.open_rainbow_datatree(f)
    print(dtree)
```

```{code-cell} ipython3
# Each .vol file contains one moment across all 12 sweeps.
sweep0 = dtree["/sweep_0"].to_dataset()
print(f"Moment in sweep_0: {[v for v in sweep0.data_vars if v not in {'sweep_mode','sweep_number','prt_mode','follow_mode','sweep_fixed_angle'}]}")
print(f"Dims: {dict(sweep0.sizes)}")
```

### Download files locally (optional fallback)

```{code-cell} ipython3
from pathlib import Path

download_dir = Path("data/fgora_sample")
download_dir.mkdir(parents=True, exist_ok=True)

# Download one timestamp's worth of files (4 moments for FGora)
sample_ts = "2014051500012000"
sample_files = [f for f in fgora_raw if sample_ts in f]
print(f"Downloading {len(sample_files)} files for timestamp {sample_ts}:")
for remote in sample_files:
    local = download_dir / Path(remote).name
    if not local.exists():
        fs.get(remote, str(local))
        print(f"  -> {local.name}")
    else:
        print(f"  (cached) {local.name}")
```

+++

## Part 2: ARCO Zarr access

The same data is also available as **Analysis-Ready Cloud-Optimized (ARCO) Zarr stores** — pre-merged, pre-aligned, and indexed along a `vcp_time` dimension spanning all three dates (2014, 2017, 2026). Built with [`raw2zarr`](https://github.com/aladinor/raw2zarr) using the `layout="per_moment"` pipeline, following the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) data model developed by [Atmoscale](https://atmoscale.ai/).

Each store is an [icechunk](https://icechunk.io/)-versioned Zarr v3 archive following the radar-datatree hierarchical convention: the top-level group is the task name (`DEJSTVO` for FGora, `JSTB_250_Dp_leto` for Jastrebac), with 12 sweep children containing CF-compliant moment arrays indexed by `(vcp_time, azimuth, range)`.

### Open the FGora ARCO store

```{code-cell} ipython3
import icechunk

# Open the icechunk repo with anonymous S3 credentials
storage = icechunk.s3_storage(
    bucket=BUCKET,
    prefix="fgora",
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
repo = icechunk.Repository.open(storage)
fgora_dt = xr.open_datatree(
    repo.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
)
fgora_dt
```

```{code-cell} ipython3
# The lowest-elevation sweep — all 100 timestamps, all 4 moments, ready to slice.
sweep0 = fgora_dt["/DEJSTVO/sweep_0"].to_dataset()
print(f"Dims: {dict(sweep0.sizes)}")
print(f"Time range: {str(sweep0['vcp_time'].values[0])[:10]} to {str(sweep0['vcp_time'].values[-1])[:10]}")
print(f"Moments: {sorted(v for v in sweep0.data_vars if v not in {'sweep_fixed_angle','ray_elevation_angle','sweep_number'})}")
```

### Open the Jastrebac ARCO store

```{code-cell} ipython3
storage_j = icechunk.s3_storage(
    bucket=BUCKET,
    prefix="jastrebac",
    endpoint_url=OSN_ENDPOINT,
    region="us-east-1",
    anonymous=True,
    force_path_style=True,
)
repo_j = icechunk.Repository.open_existing(storage_j)
jastrebac_dt = xr.open_datatree(
    repo_j.readonly_session("main").store,
    engine="zarr",
    consolidated=False,
    chunks={},
)
sweep0_j = jastrebac_dt["/JSTB_250_Dp_leto/sweep_0"].to_dataset()
print(f"Jastrebac sweep_0 dims: {dict(sweep0_j.sizes)}")
print(f"Moments: {sorted(v for v in sweep0_j.data_vars if v not in {'sweep_fixed_angle','ray_elevation_angle','sweep_number'})}")
```

+++

## Visualization — side-by-side PPI

```{code-cell} ipython3
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

for ax, (dt, task, site) in zip(axes, [
    (fgora_dt, "DEJSTVO", "FGora"),
    (jastrebac_dt, "JSTB_250_Dp_leto", "Jastrebac"),
]):
    ds = dt[f"/{task}/sweep_0"].to_dataset()
    dbzh = ds["DBZH"].isel(vcp_time=0).load()

    # Use x/y Cartesian coords if present, otherwise azimuth/range
    if "x" in ds.coords or "x" in ds.data_vars:
        x_km = ds["x"].values / 1000
        y_km = ds["y"].values / 1000
        pcm = ax.pcolormesh(x_km, y_km, dbzh.values, cmap="turbo", vmin=-20, vmax=60, shading="auto")
        ax.set_xlabel("x [km]"); ax.set_ylabel("y [km]")
    else:
        pcm = ax.pcolormesh(dbzh.values, cmap="turbo", vmin=-20, vmax=60, shading="auto")
        ax.set_xlabel("range bin"); ax.set_ylabel("azimuth")

    fig.colorbar(pcm, ax=ax, label="DBZH [dBZ]")
    ts = str(ds["vcp_time"].values[0])[:19]
    ax.set_title(f"{site} ({task}) · sweep_0 (0.5deg)\n{ts} UTC")
    ax.set_aspect("equal")

plt.tight_layout()
plt.show()
```

+++

## Jastrebac dual-pol moments

```{code-cell} ipython3
ds_j = jastrebac_dt["/JSTB_250_Dp_leto/sweep_0"].to_dataset()

panels = [
    ("DBZH",  "turbo",     -20,  60, "Reflectivity [dBZ]"),
    ("ZDR",   "RdYlBu_r",  -2,   5, "ZDR [dB]"),
    ("RHOHV", "viridis",   0.7, 1.0, "RHOHV [-]"),
]

fig, axes = plt.subplots(1, 3, figsize=(17, 5))
for ax, (mom, cmap, vmin, vmax, label) in zip(axes, panels):
    da = ds_j[mom].isel(vcp_time=0).load()
    if "x" in ds_j.coords or "x" in ds_j.data_vars:
        pcm = ax.pcolormesh(ds_j["x"].values/1000, ds_j["y"].values/1000, da.values,
                           cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
    else:
        pcm = ax.pcolormesh(da.values, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
    fig.colorbar(pcm, ax=ax, label=label)
    ax.set_title(f"Jastrebac · sweep_0 · {mom}")
    ax.set_aspect("equal")
plt.tight_layout()
plt.show()
```

+++

## Time-series slice from ARCO

One of the key advantages of the ARCO format: slice across the full 12-year time range without touching individual files.

```{code-cell} ipython3
# Extract the maximum reflectivity per timestamp across the lowest sweep
dbzh_all = fgora_dt["/DEJSTVO/sweep_0/DBZH"].load()
max_dbzh = dbzh_all.max(dim=["azimuth", "range"])

fig, ax = plt.subplots(figsize=(12, 3))
ax.plot(max_dbzh["vcp_time"].values, max_dbzh.values, "o-", markersize=3)
ax.set_xlabel("Time")
ax.set_ylabel("Max DBZH [dBZ]")
ax.set_title("FGora (DEJSTVO) — peak reflectivity per volume scan, sweep_0 (0.5 deg)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

+++

## Summary

| | Raw `.vol` files | ARCO Zarr (icechunk) |
|---|---|---|
| **Location** | `s3://nexrad-arco/{site}_vol/{date}/*.vol` | `s3://nexrad-arco/{site}/` |
| **Format** | Rainbow binary (one moment per file) | Zarr v3, chunked, CF-compliant |
| **Access** | Stream via fsspec + xradar | Open directly as xarray DataTree |
| **Time indexing** | Manual (parse filenames) | Built-in `vcp_time` dimension |
| **Best for** | Re-processing, format-specific QC | Analysis, visualization, ML training |
| **Coverage** | 3 dates × 2 sites (1188 files) | 3 dates × 2 sites (196 volumes) |

Both patterns access the same underlying observations — choose based on your workflow.

### References

- [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) — the hierarchical data model for ARCO radar archives
- [Atmoscale](https://atmoscale.ai/) — cloud-native weather radar infrastructure
- [raw2zarr](https://github.com/aladinor/raw2zarr) — the conversion pipeline that produced these stores
- [icechunk](https://icechunk.io/) — version-controlled Zarr storage
- [xradar](https://docs.openradarscience.org/projects/xradar/) — the xarray-based radar I/O library
