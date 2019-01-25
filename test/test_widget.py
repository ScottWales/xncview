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

import xarray
import xncview
import numpy

def test_variable_names(qtbot):
    ds = xarray.Dataset({
        'a': (['x'], numpy.zeros((2,))),
        'b': (['x','y'], numpy.zeros((2,2,))),
        'c': (['x','y','z'], numpy.zeros((2,2,2))),
        })

    # 'a' should be ignored as it's 1D
    widget = xncview.Widget(ds)
    assert widget.varlist.count() == 2


def test_variable_dims(qtbot):
    ds = xarray.Dataset({
        'a': (['x'], numpy.zeros((2,))),
        'b': (['x','y'], numpy.zeros((2,2,))),
        'c': (['x','y','z'], numpy.zeros((2,2,2))),
        })

    # Select 'c', should have 3 dims
    widget = xncview.Widget(ds)
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

    widget = xncview.Widget(ds)
    widget.varlist.setCurrentIndex(widget.varlist.findText('a'))

    assert widget.xdim.currentText() == 'lon'
    assert widget.ydim.currentText() == 'lat'

    assert widget.dims['t'].isVisibleTo(widget)
    assert not widget.dims['x'].isVisibleTo(widget)
    assert not widget.dims['y'].isVisibleTo(widget)

