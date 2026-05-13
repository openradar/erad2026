#!/usr/bin/env bash
# show commands before execution
set -x

# do not fail GHA on nonzero exit status
set +e

# needed to find dependencies
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$CONDA_PREFIX/hlhdf/lib

# download
cd $BALTRAD_INSTALL_ROOT/tmp
git clone --depth=1 https://github.com/baltrad/rave.git
cd rave

make distclean || true
rm -f config.cache

# build, test and install
./configure --prefix=$CONDA_PREFIX/rave \
            --with-hlhdf=$CONDA_PREFIX/hlhdf \
            --with-proj=$CONDA_PREFIX/include,$CONDA_PREFIX/lib \
            --with-expat=$CONDA_PREFIX/include,$CONDA_PREFIX/lib \
            --with-numpy=$CONDA_PREFIX/lib/python3.13/site-packages/numpy/core/include/numpy/ \
            --with-netcdf=$CONDA_PREFIX/include,$CONDA_PREFIX/lib \
            --with-python-makefile=$CONDA_PREFIX/lib/python3.13/config-3.13-x86_64-linux-gnu/Makefile

sed -i 's/\<_FillValue\>/"_FillValue"/g' librave/toolbox/cartesian_cf_io.c
sed -i '/def rave_pgf_syslog_client/a\
    if address == "/dev/log" and not os.path.exists(address):\
        return rave_pgf_stdout_client(name=name, level=level)\
' rave/Lib/rave_pgf_logger.py
make
make test
make install
# Copy files that need (temporary) monkeying to transition to Py3
# kmuehlbauer: not sure, if this is needed any more, disabling for now
# cp -r ~/binder/baltrad/opt/baltrad/rave/Lib/* $CONDA_PREFIX/rave/Lib/

# activation script
grep -l rave ${CONDA_PREFIX}/etc/conda/activate.d/baltrad.sh
if [[ $? == 1 ]]; then
    echo "export RAVEROOT=$CONDA_PREFIX/rave" >> ${CONDA_PREFIX}/etc/conda/activate.d/baltrad.sh
    echo "export PATH=\"\$PATH:$CONDA_PREFIX/rave/bin\"" >> ${CONDA_PREFIX}/etc/conda/activate.d/baltrad.sh
    echo "export LD_LIBRARY_PATH=\"\$LD_LIBRARY_PATH:$CONDA_PREFIX/rave/lib\"" >> ${CONDA_PREFIX}/etc/conda/activate.d/baltrad.sh
fi
