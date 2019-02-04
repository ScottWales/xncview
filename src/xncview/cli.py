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
import textwrap


class Preprocessor:
    description = """
    Visualise a climate and weather data file

    See `xncview --preprocessor FOO --help` for help with a specific pre-processor
    """

    def __init__(self, top_parser, argv):
        parser = argparse.ArgumentParser(parents=[top_parser],
                description=textwrap.dedent(self.description),
                formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('input', nargs='*', help='Input files')
        parser = self._init_parser(parser)

        #: Command-line arguments
        self.args = parser.parse_args(argv)

    def _init_parser(self, parser):
        """
        Add arguments to the parser (extension point)
        """
        return parser

    def _open_dataset(self):
        """
        Open the input files provided by self.args.input (extension point)

        Default implementation sets up chunking
        """
        dataset = xarray.open_mfdataset(self.args.input, chunks={})
        if 'time' in dataset.dims.keys():
            dataset.chunk({'time':1})

        return dataset

    def _do_preprocess(self, dataset):
        """
        Run any preprocessing steps (extension point) 
        """
        return dataset

    def __call__(self):
        """
        Do the pre-processing
        """
        ds = self._open_dataset()
        return self._do_preprocess(ds)


class PreprocessorOasis(Preprocessor):
    description = """
    Visualise an Oasis restart file
    """

    def _init_parser(self, parser):
        parser.add_argument('--rundir', default=None, help="Oasis run directory, containing namcouple, grids.nc, masks.nc (default parent directory of first input)")
        parser.add_argument('--grid', '-g', required=True, help="Oasis grid input files are defined on")
        return parser

    def _do_preprocess(self, dataset):
        if self.args.rundir is None:
            self.args.rundir = os.path.dirname(self.args.input[0])

        masks = xarray.open_dataset(os.path.join(self.args.rundir, 'masks.nc'))
        grids = xarray.open_dataset(os.path.join(self.args.rundir, 'grids.nc'))

        lat = grids[f'{args.grid}.lat']
        lon = grids[f'{args.grid}.lon']
        mask = masks[f'{args.grid}.msk']

        lat.attrs['axis'] = 'Y'
        lat.attrs['bounds'] = f'{args.grid}.cla'
        lon.attrs['axis'] = 'X'
        lon.attrs['bounds'] = f'{args.grid}.clo'

        new_vars = {
            f'{args.grid}.cla': grids[f'{args.grid}.cla'],        
            f'{args.grid}.clo': grids[f'{args.grid}.clo'],        
        }
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

        return ds_out


preprocessors = {
    'none': Preprocessor,
    'oasis': PreprocessorOasis,
    }


def main():
    """
    Preview a NetCDF file
    """
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False)
    parser.add_argument('--preprocessor', '-P', choices=preprocessors, default='none', help='Input file pre-processor')

    args, pp_args = parser.parse_known_args()

    # Hand over to the pre-processor
    dataset = preprocessors[args.preprocessor](parser, pp_args)()

    xncview(dataset)


if __name__ == '__main__':
    main()
