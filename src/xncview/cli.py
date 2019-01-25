#!/usr/bin/env python
#
# Copyright 2019 
# 
# Author: Scott Wales <scott.wales@unimelb.edu.au>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import xncview

import argparse
import sys
import xarray
import os
import pandas


def main():
    """
    Preview a NetCDF file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='*')

    args = parser.parse_args()

    dataset = xarray.open_mfdataset(args.input, chunks={})

    if 'time' in dataset.dims.keys():
        dataset.chunk({'time':1})

    xncview(dataset)


def main_oasis():
    """
    Preview an Oasis dump file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='*')
    parser.add_argument('--rundir', default=None)
    parser.add_argument('--grid', '-g', required=True)

    args = parser.parse_args()
    if args.rundir is None:
        args.rundir = os.path.dirname(args.input[0])

    dataset = xarray.open_mfdataset(args.input, chunks={})
    if 'time' in dataset.dims.keys():
        dataset.chunk({'time':1})

    masks = xarray.open_dataset(os.path.join(args.rundir, 'masks.nc'))
    grids = xarray.open_dataset(os.path.join(args.rundir, 'grids.nc'))

    lat = grids[f'{args.grid}.lat']
    lon = grids[f'{args.grid}.lon']
    mask = masks[f'{args.grid}.msk']

    lat.attrs['axis'] = 'Y'
    lon.attrs['axis'] = 'X'

    new_vars = {}
    for v, da in dataset.data_vars.items():
        reshaped = xarray.DataArray(
                da.values.reshape(dataset.time.size, mask.shape[0], mask.shape[1]),
                dims=['time', mask.dims[0], mask.dims[1]])
        reshaped = reshaped.where(mask == 0)

        reshaped.coords['time'] = dataset.time
        reshaped.coords['lat'] = lat
        reshaped.coords['lon'] = lon

        new_vars[v] = reshaped

    ds_out = xarray.Dataset(new_vars)
    ds_out.set_coords(['lat','lon'])

    xncview(ds_out)


def main_iris():
    import iris
    from iris.fileformats.um import structured_um_loading
    parser = argparse.ArgumentParser()
    parser.add_argument('input')

    args = parser.parse_args()

    print("Loading...")
    with structured_um_loading():
        cubes = iris.load(args.input)
    print("Loaded")
        
    das = {}
    for c in cubes:
        name = c.name()
        das[name] = xarray.DataArray.from_iris(c)

        if name == 'air_potential_temperature':
            das[name] = das[name].rename(level_height='level_height_1', sigma='sigma_1')

    print(das)
    dataset = xarray.Dataset(das)
    xncview(dataset)


if __name__ == '__main__':
    main()
