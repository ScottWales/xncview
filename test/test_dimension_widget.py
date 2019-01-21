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

from xncview.widget import DimensionWidget
import xarray


def test_update_value(qtbot):
    """
    Updating the value text should update the slider
    """
    da = xarray.DataArray([1,2,3],name='test', coords=[('x',[1,2,3])])

    widget = DimensionWidget(da.x)
    assert widget.value() == 0

    widget.textbox.setText('2')
    assert widget.value() == 1


def test_update_slider(qtbot):
    """
    Updating the slider should update the value text
    """
    da = xarray.DataArray([1,2,3],name='test', coords=[('x',[1,2,3])])

    widget = DimensionWidget(da.x)
    assert widget.value() == 0

    widget.slider.setValue(1)
    assert widget.textbox.text() == '2'
