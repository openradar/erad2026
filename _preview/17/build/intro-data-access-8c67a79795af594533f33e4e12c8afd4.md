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
import matplotlib.pyplot as plt
import xarray as xr
import xradar

OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"
```

```{code-cell} ipython3
def open_arco_store(prefix: str) -> xr.DataTree:
    """Open an icechunk-backed ARCO store from OSN with anonymous access."""
    storage = icechunk.s3_storage(
        bucket=BUCKET,
        prefix=prefix,
        endpoint_url=OSN_ENDPOINT,
        region="us-east-1",
        anonymous=True,
        force_path_style=True,
    )
    repo = icechunk.Repository.open(storage)
    return xr.open_datatree(
        repo.readonly_session("main").store,
        engine="zarr",
        consolidated=False,
        chunks={},
    )
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
sweep0_raw = dtree_raw["/sweep_0"].to_dataset()
moments = [v for v in sweep0_raw.data_vars
           if v not in {"sweep_mode", "sweep_number", "prt_mode", "follow_mode", "sweep_fixed_angle"}]
print(f"Moment: {moments}")
print(f"Dims:   {dict(sweep0_raw.sizes)}")
```

### Download files locally (optional)

```{code-cell} ipython3
from pathlib import Path

download_dir = Path("data/fgora_sample")
download_dir.mkdir(parents=True, exist_ok=True)

sample_ts = "2014051500012000"
for remote in [f for f in fgora_raw if sample_ts in f]:
    local = download_dir / Path(remote).name
    if not local.exists():
        fs.get(remote, str(local))
    print(f"  {local.name} ({'downloaded' if not local.exists() else 'cached'})")
```

+++

## Part 2: ARCO Zarr access

The same data as **Analysis-Ready Cloud-Optimized (ARCO) Zarr stores** — pre-merged, pre-aligned, and indexed along a `vcp_time` dimension spanning all three dates (2014, 2017, 2026). Built with [`raw2zarr`](https://github.com/aladinor/raw2zarr) following the [radar-datatree](https://atmoscale.github.io/radar-datatree/index.html) data model by [Atmoscale](https://atmoscale.ai/).

Each store is an [icechunk](https://icechunk.io/)-versioned Zarr v3 archive. The top-level group is the task name, with 12 sweep children containing CF-compliant moment arrays indexed by `(vcp_time, azimuth, range)`.

```{code-cell} ipython3
fgora_dt = open_arco_store("fgora")
jastrebac_dt = open_arco_store("jastrebac")

for name, dt, task in [
    ("FGora", fgora_dt, "DEJSTVO"),
    ("Jastrebac", jastrebac_dt, "JSTB_250_Dp_leto"),
]:
    ds = dt[f"/{task}/sweep_0"].to_dataset()
    moms = sorted(v for v in ds.data_vars
                  if v not in {"sweep_fixed_angle", "ray_elevation_angle", "sweep_number"})
    print(f"{name:<12s} /{task}  dims={dict(ds.sizes)}  moments={moms}")
```

```{code-cell} ipython3
fgora_dt
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
    x_km = ds["x"].values / 1000
    y_km = ds["y"].values / 1000
    pcm = ax.pcolormesh(x_km, y_km, dbzh.values,
                        cmap="turbo", vmin=-20, vmax=60, shading="auto")
    fig.colorbar(pcm, ax=ax, label="DBZH [dBZ]")
    ax.set_title(f"{site} ({task})\nsweep_0 (0.5 deg) · {str(ds['vcp_time'].values[0])[:19]} UTC")
    ax.set_xlabel("x [km]"); ax.set_ylabel("y [km]")
    ax.set_aspect("equal")

plt.tight_layout()
plt.show()
```

+++

## Jastrebac dual-pol moments

```{code-cell} ipython3
ds_j = jastrebac_dt["/JSTB_250_Dp_leto/sweep_0"].to_dataset()

fig, axes = plt.subplots(1, 3, figsize=(17, 5))
for ax, (mom, cmap, vmin, vmax, label) in zip(axes, [
    ("DBZH",  "turbo",    -20,  60, "Reflectivity [dBZ]"),
    ("ZDR",   "RdYlBu_r",  -2,   5, "ZDR [dB]"),
    ("RHOHV", "viridis",  0.7, 1.0, "RHOHV [-]"),
]):
    da = ds_j[mom].isel(vcp_time=0).load()
    pcm = ax.pcolormesh(ds_j["x"].values / 1000, ds_j["y"].values / 1000,
                        da.values, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
    fig.colorbar(pcm, ax=ax, label=label)
    ax.set_title(f"Jastrebac · sweep_0 · {mom}")
    ax.set_aspect("equal")
plt.tight_layout()
plt.show()
```

+++

## Time-series slice from ARCO

One of the key advantages of the ARCO format: slice across the full time range without touching individual files.

```{code-cell} ipython3
dbzh_all = fgora_dt["/DEJSTVO/sweep_0/DBZH"].load()
max_dbzh = dbzh_all.max(dim=["azimuth", "range"])

fig, ax = plt.subplots(figsize=(12, 3))
ax.plot(max_dbzh["vcp_time"].values, max_dbzh.values, "o-", markersize=3)
ax.set_xlabel("Time")
ax.set_ylabel("Max DBZH [dBZ]")
ax.set_title("FGora (DEJSTVO) — peak reflectivity per volume, sweep_0 (0.5 deg)")
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
