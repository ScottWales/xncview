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

from xncview.widget import Widget, _get_variable_dims, _get_bounds

import xarray
import numpy

def test_variable_names(qtbot):
    ds = xarray.Dataset({
        'a': (['x'], numpy.zeros((2,))),
        'b': (['x','y'], numpy.zeros((2,2,))),
        'c': (['x','y','z'], numpy.zeros((2,2,2))),
        })

    # 'a' should be ignored as it's 1D
    widget = Widget(ds)
    assert widget.varlist.count() == 2


def test_variable_dims(qtbot):
    ds = xarray.Dataset({
        'a': (['x'], numpy.zeros((2,))),
        'b': (['x','y'], numpy.zeros((2,2,))),
        'c': (['x','y','z'], numpy.zeros((2,2,2))),
        })

    # Select 'c', should have 3 dims
    widget = Widget(ds)
    widget.varlist.setCurrentIndex(widget.varlist.findText('c'))

    assert widget.xdim.count() == 3
    assert widget.ydim.count() == 3


def test_multi_axis(qtbot):
    ds = xarray.Dataset({
            'a': (['x','y','t'], numpy.zeros((2,2,2,))),
        },
        coords = {
            'lat': (['x','y'], numpy.zeros((2,2,))),
            'lon': (['x','y'], numpy.zeros((2,2,))),
            't': (['t'], [1,2]),
        })
    ds.lat.attrs['axis'] = 'Y'
    ds.lon.attrs['axis'] = 'X'
    ds.t.attrs['axis'] = 'T'

    widget = Widget(ds)
    widget.varlist.setCurrentIndex(widget.varlist.findText('a'))

    assert widget.xdim.currentText() == 'lon'
    assert widget.ydim.currentText() == 'lat'

    assert widget.dims['t'].isVisibleTo(widget)
    assert not widget.dims['x'].isVisibleTo(widget)
    assert not widget.dims['y'].isVisibleTo(widget)


def test_get_dims(qtbot):
    ds = xarray.Dataset({
            'a': (['x','y','z','t'], numpy.zeros((2,2,1,2,))),
        },
        coords = {
            'lat': (['x','y'], numpy.zeros((2,2,))),
            'lon': (['x','y'], numpy.zeros((2,2,))),
            't': (['t'], [1,2]),
            'z': (['z'], [1]),
        })
    ds.lat.attrs['axis'] = 'Y'
    ds.lon.attrs['axis'] = 'X'
    ds.t.attrs['axis'] = 'T'

    dims = _get_variable_dims(ds.a)

    assert 'lat' in dims
    assert 'x' in dims
    assert 't' in dims
    assert 'z' not in dims

def test_get_bounds():
    ds = xarray.Dataset({
        'a': (['x','y'], numpy.zeros((2,2))),
        'x': (['x'], [1,2], {'bounds': 'x_b'}),
        'x_b': (['x','b'], [[0.5,1.5], [1.5,2.5]]),

        'c': (['x','y'], [[1, 2], [1, 2]], {'bounds': 'c_b'}), 
        })
    ds['c_b'] = (['cn','x','y'],numpy.stack([ds.c - 0.5, ds.c + 0.5, ds.c + 0.5, ds.c - 0.5]))

    b = _get_bounds(ds, 'x')
    numpy.testing.assert_equal(b, [0.5,1.5,2.5])

    b = _get_bounds(ds, 'c')
    numpy.testing.assert_equal(b, [[0.5,1.5,2.5],[0.5,1.5,2.5],[0.5,1.5,2.5]])
