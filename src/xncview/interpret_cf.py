#!/usr/bin/env python
#
# Copyright 2019 Scott Wales
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


lat_units = set((
        'degrees_north',
        'degrees_N',
        'degreesN',
        'degree_north',
        'degree_N',
        'degreeN',
        ))
lon_units = set((
        'degrees_east',
        'degrees_E',
        'degreesE',
        'degree_east',
        'degree_E',
        'degreeE',
        ))


def identify_lat(variable):
    lat_dims = []

    for d, dim in variable.coords.items():

        if (dim.attrs.get('axis', None) == 'Y' or 
            dim.attrs.get('standard_name', None) == 'latitude' or
            dim.attrs.get('units', None) in lat_units):
            
            lat_dims.append(d)

    if len(lat_dims) > 1:
        raise Exception("Multiple potential latitude dimensions")
    elif len(lat_dims) < 1:
        return None
    else:
        return lat_dims[0]


def identify_lon(variable):
    lon_dims = []

    for d, dim in variable.coords.items():

        if (dim.attrs.get('axis', None) == 'X' or 
            dim.attrs.get('standard_name', None) == 'longitude' or
            dim.attrs.get('units', None) in lon_units):
            
            lon_dims.append(d)

    if len(lon_dims) > 1:
        raise Exception("Multiple potential longitude dimensions")
    elif len(lon_dims) < 1:
        return None
    else:
        return lon_dims[0]


def classify_vars(dataset):
    bounds = set()
    coords = set()

    for name, var in dataset.variables.items():
        if 'bounds' in var.attrs:
            bounds.add(var.attrs['bounds'])

        if 'coordinates' in var.attrs:
            coords.update(var.attrs['coordinates'].split())

    data = set(dataset.variables.keys()) - bounds - coords
    return {'bounds': bounds, 'coords': coords, 'data': data}

