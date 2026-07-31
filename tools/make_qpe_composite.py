#!/usr/bin/env python3
"""Produce gridded, composited Z-R rain-rate fields for the ERAD2026 PySteps day.

The published schedule runs QC -> corrections -> QPE -> gridding on day 1 and feeds
the result into the Sunday PySteps workshop. This script chains the steps that the
course already teaches, so day 2 has a concrete input to nowcast:

    open ARCO store            notebooks/data-access/intro-data-access.md
    georeference onto LAEA     notebooks/workflow/gridding_data.md
    beam-blockage mask         notebooks/workflow/dem_beamblockage.md   (optional)
    attenuation correction     notebooks/workflow/attenuation_single_pol.md
    Z -> R (Marshall-Palmer)   notebooks/workflow/qpe_estimation.md
    grid via KDTree mapping    notebooks/workflow/gridding_data.md
    composite with max()       notebooks/workflow/composite_togrid.md

No new algorithms are introduced. QPE is single-polarisation Z-R throughout, so both
radars take the identical chain and the dual-pol moments are not needed.

Rain rate is computed in *polar* space, before gridding. Under the course's current
`nearest` interpolation and `max()` compositing this is bit-identical to converting
after compositing (both are selections, and Z-R is monotonic, so they commute). It is
done this way so the product stays correct if the interpolator is ever switched to
`inverse_distance`, where averaging dBZ and converting afterwards is wrong by -66%.

Usage
-----
    python tools/make_qpe_composite.py --outdir data/qpe
    python tools/make_qpe_composite.py --cases 2014 --dem-dir . --outdir data/qpe
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import icechunk
import numpy as np
import pyproj
import rioxarray  # noqa: F401  -- registers the .rio accessor used for write_crs
import wradlib as wrl
import xarray as xr
import xradar as xd

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- data source -----------------------------------------------------------------
OSN_ENDPOINT = "https://umn1.osn.mghpcc.org"
BUCKET = "nexrad-arco"

# Jastrebac splits across two stores because 2014 uses 250 m bins and 2017/2026 use
# 500 m bins; merging them would mis-label the 500 m data in physical space.
CASES: dict[str, dict[str, str]] = {
    "2014": {"fgora": "Fgora", "jastrebac": "jastrebac_250m"},
    "2017": {"fgora": "Fgora", "jastrebac": "jastrebac_500m"},
    "2026": {"fgora": "Fgora", "jastrebac": "jastrebac_500m"},
}
SWEEP = "sweep_0"  # lowest elevation (0.5 deg), closest to the ground for QPE

# --- processing constants --------------------------------------------------------
ZR_A, ZR_B = 200.0, 1.6  # Marshall & Palmer (1948), as in qpe_estimation.md
CBB_MAX = 0.5  # drop gates with >50% cumulative beam blockage

# Ceiling on corrected reflectivity before Z-R. The archives contain echo up to 70 dBZ
# (Fgora 2017) and 80 dBZ (Jastrebac 2026) -- hail and clutter rather than rain -- and
# Z-R turns those into physically impossible rates (uncapped, Fgora 2017 peaks at
# 1758 mm/h). 59 dBZ is not a new threshold: it is exactly the ceiling the attenuation
# correction below already enforces through constraint_dbz.
DBZ_CAP = 59.0

# LAEA grid, verbatim from gridding_data.md (EPSG:3035-style, EuCom XL extent).
# Both radars are cut from this one lattice, which is what lets xr.concat align them.
X0, Y0 = 3760756.2464729655, -2656141.3006878751
NX, NY, RES = 6500, 5300, 1000.0
IPOL = "nearest"

# Kept as a literal so it can be published verbatim in the attrs. Round-tripping the
# CRS back through to_proj4() rewrites "+a/+b" as "+ellps=GRS80" and warns about lost
# information, and pysteps wants a proj4 string it can hand straight to pyproj.
PROJ4 = (
    "+proj=laea +lat_0=52 +lon_0=10 "
    f"+x_0={X0} "
    f"+y_0={Y0} "
    "+a=6378137 +b=6356752.3141403701 +units=m +no_defs"
)

# --- time alignment --------------------------------------------------------------
# The inter-radar offset flips sign between cases (+106 s in 2017, -106 s in 2026),
# so composite_togrid.md's floor("5min") pairs them inconsistently. We reindex onto an
# explicit 5-minute axis instead. Tolerance is under half the step, so each slot takes
# at most one scan.
STEP_MIN = 5
TOL_SECONDS = 150


def laea_crs():
    """The shared LAEA projection (gridding_data.md)."""
    return wrl.georef.ensure_crs(pyproj.CRS.from_proj4(PROJ4))


def open_sweep(prefix: str, case: str, crs) -> xr.Dataset:
    """Open one radar's sweep for one case, georeferenced onto the LAEA grid."""
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
    )
    root = next(iter(dtree.keys())).split("/")[0]
    swp = (
        dtree[f"{root}/{SWEEP}"]
        .to_dataset(inherit="all_coords")
        .sel(vcp_time=case)
        .wrl.georef.georeference(crs=crs)
    )
    swp = swp.rename(crs_wkt="spatial_ref")
    # wradlib/wradlib#791: georeference() mislabels z's units as degrees.
    swp.z.attrs = xd.model.get_altitude_attrs()
    return swp.sortby("vcp_time")


def qc_and_qpe(swp: xr.Dataset, dem: xr.Dataset | None = None) -> xr.Dataset:
    """Attenuation-correct reflectivity and convert to rain rate, in polar space."""
    gate_length = float(np.diff(swp.range)[0]) / 1000.0  # km
    dbz = swp.DBZH

    # Modified Kraemer, constrained in both corrected dBZ and total PIA
    # (attenuation_single_pol.md, section 4).
    pia = dbz.wrl.atten.correct_attenuation_constrained(
        a_max=5.0e-5,
        a_min=2.0e-5,
        n_a=100,
        b_max=0.75,
        b_min=0.65,
        n_b=6,
        gate_length=gate_length,
        constraints=[wrl.atten.constraint_dbz, wrl.atten.constraint_pia],
        constraint_args=[[DBZ_CAP], [10.0]],
    )
    # Cap before Z-R so hail/clutter cores cannot become impossible rain rates.
    dbz_corr = (dbz + pia).clip(max=DBZ_CAP)

    # Z -> R, Marshall-Palmer (qpe_estimation.md).
    rain_rate = dbz_corr.wrl.trafo.idecibel().wrl.zr.z_to_r(a=ZR_A, b=ZR_B)

    # Beam blockage is applied *after* attenuation: the correction integrates along
    # each ray, so injecting NaN beforehand would poison every downstream gate.
    if dem is not None and "CBB" in dem:
        rain_rate = rain_rate.where(dem["CBB"] <= CBB_MAX)

    rain_rate.attrs = {
        "units": "mm/h",
        "long_name": "Rain rate (Marshall-Palmer Z-R)",
        "zr_a": ZR_A,
        "zr_b": ZR_B,
    }
    return swp.assign(rain_rate=rain_rate, PIA=pia)


def grid_rain(swp: xr.Dataset, crs) -> xr.Dataset:
    """Interpolate polar rain rate onto the shared LAEA lattice (gridding_data.md)."""
    x = X0 + (np.arange(NX) - NX / 2 + 0.5) * RES
    y = Y0 + (np.arange(NY) - NY / 2 + 0.5) * (-RES)
    cart = xr.Dataset(coords={"x": ("x", x), "y": ("y", y)}).chunk(x=500, y=500)
    cart = cart.rio.write_crs(crs)
    # Crop the global lattice to this radar's footprint. Because every radar is cut
    # from the same x/y arrays, the subsets share exact coordinates.
    cart = cart.sel(
        x=slice(float(swp.x.min()), float(swp.x.max())),
        y=slice(float(swp.y.max()), float(swp.y.min())),  # y decreases north->south
    )

    src = swp[["rain_rate"]]  # only what we need -- gridding all moments is wasted work
    # Geometry is static, so one mapping serves every timestep in the stack.
    mapping = src.wrl.ipol.get_mapping(cart, k=4)
    return src.wrl.ipol.interpolate(mapping, method=IPOL)


def common_time_axis(times_list: list[np.ndarray]) -> np.ndarray:
    """A regular 5-minute axis spanning every radar's scans."""
    t0 = min(t.min() for t in times_list).astype("datetime64[m]")
    t1 = max(t.max() for t in times_list).astype("datetime64[m]")
    # Anchor to a clean 5-minute boundary (the epoch is itself 5-min aligned).
    t0 = t0 - np.timedelta64(int(t0.astype("int64") % STEP_MIN), "m")
    grid = np.arange(
        t0, t1 + np.timedelta64(STEP_MIN, "m"), np.timedelta64(STEP_MIN, "m")
    )
    return grid.astype("datetime64[ns]")


def composite(gridded: dict[str, xr.Dataset], case: str) -> xr.Dataset:
    """Align both radars on the 5-min axis and reduce with max() (composite_togrid.md)."""
    grid_times = common_time_axis(
        [np.asarray(g.vcp_time.values) for g in gridded.values()]
    )
    aligned = {}
    for name, g in gridded.items():
        aligned[name] = (
            g.rain_rate.sortby("vcp_time")
            .reindex(
                vcp_time=grid_times,
                method="nearest",
                tolerance=np.timedelta64(TOL_SECONDS, "s"),
            )
            .rename(vcp_time="time")
        )

    radars = xr.DataArray(list(aligned), dims="radar")
    stack = xr.concat(list(aligned.values()), dim=radars)  # outer join -> union grid
    rain_rate = stack.max("radar")
    n_radars = stack.notnull().sum("radar").astype("uint8")

    ds = xr.Dataset({"rain_rate": rain_rate, "n_radars": n_radars})

    # The 5-minute anchor can overhang the first/last scan, leaving empty edge slots.
    # Trim those, but keep interior gaps -- a slot where one radar is missing is real
    # information (it shows up as n_radars == 1) and must not be silently dropped.
    populated = (ds.n_radars > 0).any(dim=("x", "y")).values
    if populated.any():
        first = int(populated.argmax())
        last = len(populated) - int(populated[::-1].argmax())
        if (first, last) != (0, len(populated)):
            print(
                f"  [{case}] trimming {first} leading / "
                f"{len(populated) - last} trailing empty slot(s)"
            )
            ds = ds.isel(time=slice(first, last))

    ds["rain_rate"] = ds.rain_rate.astype("float32")
    ds["rain_rate"].attrs = {
        "units": "mm/h",
        "long_name": "Composited rain rate (Marshall-Palmer Z-R)",
        "standard_name": "rainfall_rate",
    }
    ds["n_radars"].attrs = {
        "long_name": "Number of radars contributing to this cell",
        "comment": "0 = no data, 1 = single radar, 2 = both radars in the overlap",
    }
    ds["time"].attrs = {"long_name": "Valid time (nominal 5-minute slot)"}
    ds["x"].attrs = {"units": "m", "standard_name": "projection_x_coordinate"}
    ds["y"].attrs = {"units": "m", "standard_name": "projection_y_coordinate"}

    x, y = ds.x.values, ds.y.values
    ds.attrs = {
        "title": f"ERAD2026 gridded Z-R rain-rate composite, {case}",
        "summary": (
            "Fruska Gora + Jastrebac lowest-sweep reflectivity, attenuation-corrected "
            "and converted to rain rate with Marshall-Palmer Z-R, gridded onto a 1 km "
            "LAEA lattice and composited with max(). Produced for the ERAD2026 short "
            "course PySteps session."
        ),
        "source_stores": ", ".join(
            f"{k}={v}" for k, v in CASES[case].items()
        ),
        "sweep": SWEEP,
        "zr_a": ZR_A,
        "zr_b": ZR_B,
        "dbz_cap": DBZ_CAP,
        "qc_steps": (
            f"modified-Kraemer attenuation correction; corrected reflectivity capped at "
            f"{DBZ_CAP} dBZ before Z-R; beam-blockage mask if DEM supplied"
        ),
        "composite_method": f"max over radars, {IPOL} interpolation",
        # --- pysteps-facing metadata ---
        "projection": PROJ4,
        "x1": float(x.min() - RES / 2),
        "x2": float(x.max() + RES / 2),
        "y1": float(y.min() - RES / 2),
        "y2": float(y.max() + RES / 2),
        "xpixelsize": float(RES),
        "ypixelsize": float(RES),
        "yorigin": "upper",
        "unit": "mm/h",
        "transform": "None",
        "accutime": float(STEP_MIN),
        "threshold": 0.1,
        "zerovalue": 0.0,
    }
    return ds


def build_case(case: str, dem_dir: Path | None, crs) -> xr.Dataset:
    gridded = {}
    for radar, prefix in CASES[case].items():
        print(f"  [{case}/{radar}] opening {prefix} ...", flush=True)
        swp = open_sweep(prefix, case, crs)

        dem = None
        if dem_dir is not None:
            dem_path = dem_dir / f"{prefix}_{SWEEP}_dem.nc"
            if dem_path.exists():
                dem = xr.open_dataset(dem_path)
                print(f"  [{case}/{radar}] beam blockage from {dem_path.name}")
            else:
                print(f"  [{case}/{radar}] no DEM at {dem_path.name}, skipping blockage")

        swp = qc_and_qpe(swp, dem=dem)
        print(
            f"  [{case}/{radar}] {swp.sizes['vcp_time']} scans, "
            f"PIA max {float(swp.PIA.max()):.1f} dB, "
            f"R max {float(swp.rain_rate.max()):.1f} mm/h",
            flush=True,
        )
        gridded[radar] = grid_rain(swp, crs).compute()
        print(f"  [{case}/{radar}] gridded -> {dict(gridded[radar].sizes)}", flush=True)

    ds = composite(gridded, case).compute()
    print(
        f"  [{case}] composite {dict(ds.sizes)}  "
        f"both-radar cells {(ds.n_radars == 2).sum().item():,}",
        flush=True,
    )
    return ds


def upload(local: Path, prefix: str) -> None:
    """Publish one store to OSN. Credentials come from the environment only."""
    import os

    import s3fs

    key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if not (key and secret):
        raise SystemExit(
            "refusing to upload: set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        )
    fs = s3fs.S3FileSystem(
        key=key, secret=secret, client_kwargs={"endpoint_url": OSN_ENDPOINT}
    )
    dest = f"{BUCKET}/{prefix}/{local.name}"
    print(f"  uploading -> s3://{dest}", flush=True)
    fs.put(str(local), dest, recursive=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="+", default=sorted(CASES), choices=sorted(CASES))
    ap.add_argument("--outdir", type=Path, default=Path("data/qpe"))
    ap.add_argument(
        "--dem-dir",
        type=Path,
        default=None,
        help="directory holding {prefix}_sweep_0_dem.nc from dem_beamblockage.md",
    )
    ap.add_argument(
        "--upload-prefix",
        default=None,
        help=(
            "publish each store under s3://%s/<prefix>/ on OSN. Requires "
            "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in the environment." % BUCKET
        ),
    )
    args = ap.parse_args()

    crs = laea_crs()
    args.outdir.mkdir(parents=True, exist_ok=True)

    for case in args.cases:
        print(f"=== {case}", flush=True)
        ds = build_case(case, args.dem_dir, crs)
        out = args.outdir / f"qpe_composite_{case}.zarr"
        ds.to_zarr(out, mode="w", zarr_format=3, consolidated=True)
        mb = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1e6
        print(f"=== {case} -> {out}  ({mb:.1f} MB on disk)", flush=True)
        if args.upload_prefix:
            upload(out, args.upload_prefix)
        print(flush=True)


if __name__ == "__main__":
    main()
