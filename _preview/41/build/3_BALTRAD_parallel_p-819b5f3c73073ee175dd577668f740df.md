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

# Parallel processing

+++

The default VM setup is to use a single CPU core. In order to demonstrate the power of parallel processing, you must first determine whether your physical hardware has more than a single core.

On Linux this is done in the terminal with the 'nproc' command.

On Mac this is done in the terminal with the 'sysctl -n hw.ncpu' command.

On Windows this is done graphically using the Task Manager's Performance tab.

We want tune our VM to harness the power of several CPUs. Follow the following steps:

1. Shut down the IPython notebook Server (Ctrl-C, answer yes)
2. Shutdown the VM (click the X button in the VM window, choose power down the machine)
3. Select the VM in the VirtualBox Manager Window, from the menu choose Machine->Setting
4. Choose the System Tab, then Processor, use the slider to set the number of Processor to 2, 4, or 8 depending on your system resources.  
5. Click Ok, and then start the machine
6. Login, use the start_notebook.sh script to start the IPython server, start the notebook and you should have multiple processors!

RELOAD THIS PAGE!

+++

## retrieve data from s3 bucket

```{code-cell} ipython3
import os
import urllib.request
from pathlib import Path

# Set the URL for the cloud
URL = "https://js2.jetstream-cloud.org:8001/"
path = "pythia/radar/erad2024/baltrad/baltrad_short_course/"
!mkdir -p data
files = [
    "seang.h5",
    "searl.h5",
    "sease.h5",
    "sehud.h5",
    "sekir.h5",
    "sekkr.h5",
    "selek.h5",
    "selul.h5",
    "seosu.h5",
    "sevar.h5",
    "sevil.h5",
]
for file in files:
    file0 = os.path.join(path, file)
    name = os.path.join("data", Path(file).name)
    if not os.path.exists(name):
        print(f"downloading, {name}")
        urllib.request.urlretrieve(
            f"{URL}{file0}", os.path.join("data", Path(file).name)
        )
```

## Verify from Python the number of CPU cores at our disposal

```{code-cell} ipython3
import multiprocessing

print("We have %i cores to play with!" % multiprocessing.cpu_count())
```

Yay! Now we're going to set up some rudimentary functionality that will allow us to distribute a processing load among our cores.

+++

## Define a generator

```{code-cell} ipython3
import os
import _raveio, odc_polarQC

# Specify the processing chain
odc_polarQC.algorithm_ids = [
    "ropo",
    "beamb",
    "radvol-att",
    "radvol-broad",
    "rave-overshooting",
    "qi-total",
]


# Run processing chain on a single file. Return an output file string.
def generate(file_string):
    rio = _raveio.open(file_string)

    pvol = rio.object
    pvol = odc_polarQC.QC(pvol)
    rio.object = pvol

    # Derive an output file name
    path, fstr = os.path.split(file_string)
    ofstr = os.path.join(path, "qc_" + fstr)

    rio.save(ofstr)
    return ofstr
```

## Feed the generator, sequentially

```{code-cell} ipython3
import glob, time

ifstrs = glob.glob("data/se*.h5")
before = time.time()
for fstr in ifstrs:
    print(fstr, generate(fstr))
after = time.time()

print("Processing time: %3.2f seconds" % (after - before))
```

Mental note: repeat once!

+++

## Multiprocess the generator

```{code-cell} ipython3
# Both input and output are a list of file strings
def multi_generate(fstrs, procs=None):
    pool = multiprocessing.Pool(
        procs
    )  # Pool of processors. Defaults to all available logical cores

    results = []
    # chunksize=1 means feed a process a new job as soon as the process is idle.
    # In our case, this restricts the queue to one "dispatcher" which is faster.
    r = pool.map_async(generate, fstrs, chunksize=1, callback=results.append)
    r.wait()

    return results[0]
```

## Feed the monster, asynchronously!

```{code-cell} ipython3
before = time.time()
ofstrs = multi_generate(ifstrs)
after = time.time()

print("Processing time: %3.2f seconds" % (after - before))
```

```{code-cell} ipython3

```
