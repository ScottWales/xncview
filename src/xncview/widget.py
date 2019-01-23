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

import sys
from matplotlib.backends.qt_compat import QtWidgets as QW, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import numpy
import dask.array
from .interpret_cf import *


class DimensionWidget(QW.QWidget):
    """
    Widget to select dimensions
    """

    #: Signal emitted when value is changed
    valueChanged = QtCore.Signal(int)

    def __init__(self, dimension):
        """
        Construct the widget

        Args:
            dimension: xarray.DataArray
        """
        super().__init__()

        main_layout = QW.QHBoxLayout(self)

        #: The dimension represented by this widget
        self.dimension = dimension

        self.title = QW.QLabel(dimension.name)
        self.textbox = QW.QLineEdit()
        self.slider = QW.QSlider(orientation=QtCore.Qt.Horizontal)

        self.slider.setMinimum(0)
        self.slider.setMaximum(dimension.size-1)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._update_from_slider)

        self.textbox.returnPressed.connect(self._update_from_value)

        main_layout.addWidget(self.title)
        main_layout.addWidget(self.textbox)
        main_layout.addWidget(self.slider)



    def _update_from_value(self):
        value = self.textbox.text()
        value = numpy.asscalar(numpy.array(value, dtype=self.dimension.dtype))
        index = self.dimension.to_index().get_loc(value, method='nearest')
        self.slider.setValue(index)


    def _update_from_slider(self, value):
        self.textbox.setText(str(self.dimension[value].values))
        self.valueChanged.emit(value)
    

    def value(self):
        """
        The current slider index
        """
        return self.slider.value()


class Widget(QW.QWidget):
    """
    Base QT Widget for the xncview interface
    """
    def __init__(self, dataset):
        """
        Construct the widget

        Args:
            dataset: xarray.Dataset
        """
        super().__init__()

        main_layout = QW.QVBoxLayout(self)

        self.varlist = QW.QComboBox()
        self.xdim = QW.QComboBox()
        self.ydim = QW.QComboBox()

        header = QW.QGroupBox()
        header_layout = QW.QHBoxLayout(header)
        header_layout.addWidget(self.varlist)
        header_layout.addWidget(self.xdim)
        header_layout.addWidget(self.ydim)

        main_layout.addWidget(header)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axis = self.canvas.figure.subplots()

        main_layout.addWidget(self.canvas)

        #: Dataset being inspected
        self.dataset = dataset

        # Setup list of variables, further setup is done by change_variable()
        classes = classify_vars(dataset)
        variables = [v for v in classes['data'] if dataset[v].ndim >= 2]
        self.varlist.addItems(variables)

        # Connect slots
        self.varlist.currentIndexChanged.connect(self.change_variable)
        self.xdim.activated.connect(self.redraw)
        self.ydim.activated.connect(self.redraw)

        #: Currently active variable
        self.variable = None

        #: Values for non-axis dimensions
        self.dims = {}
        dims_group = QW.QGroupBox()
        dims_layout = QW.QVBoxLayout(dims_group)
        for name in self.dataset.coords:
            self.dims[name] = DimensionWidget(self.dataset[name])
            self.dims[name].valueChanged.connect(self.redraw)
            dims_layout.addWidget(self.dims[name])
        main_layout.addWidget(dims_group)

        if len(variables) > 0:
            self.change_variable()


    def change_variable(self, index=0):
        """
        The active variable has changed
        """
        old_dims = []
        if self.variable is not None:
            old_dims = self.variable.dims

        varname = self.varlist.currentText()
        self.variable = self.dataset[varname]
        print('\nVariable details:')
        print(self.variable)

        self.bounds = dask.array.stack([self.variable.min(), self.variable.max()]).compute()

        if set(self.variable.dims) != set(old_dims):
            self.update_dimensions()

        self.redraw()


    def update_dimensions(self):
        """
        Update dimension lists based on the current variable
        """
        # Refresh dimensions
        self.xdim.clear()
        self.xdim.addItems(self.variable.coords)

        x = 0
        lon = identify_lon(self.variable)
        if lon is not None:
            x = self.xdim.findText(lon)
        self.xdim.setCurrentIndex(x)

        self.ydim.clear()
        self.ydim.addItems(self.variable.coords)

        y = 1
        lat = identify_lat(self.variable)
        if lat is not None:
            y = self.ydim.findText(lat)
        self.ydim.setCurrentIndex(y)

        for d, w in self.dims.items():
            w.setVisible(d in self.variable.coords)


    def redraw(self):
        self.axis.clear()

        x = self.xdim.currentText()
        y = self.ydim.currentText()

        passive_dims = set(self.variable.coords) - set([x,y])
        for d, w in self.dims.items():
            w.setVisible(d in passive_dims)

        if x != y:
            v = self.variable

            # Flatten passive dims
            for d in self.variable.coords:
                if d not in [x,y]:
                    v = v.isel({d:self.dims[d].value()})

            # Plot data
            try:
                v.plot.pcolormesh(x, y, add_colorbar=False, ax=self.axis, clim=self.bounds)
            except Exception as e:
                print(e)

        self.canvas.draw()


    def update_axes(self):
        self.axis.remove()
        self.axis = self.canvas.figure.axes(projection=cartopy.crs.PlateCarree())
        self.axis.coastlines()
