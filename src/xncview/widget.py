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
import matplotlib.pyplot as plt
import numpy
import dask.array
import xarray
import cartopy.crs
import cartopy.mpl.geoaxes
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

        self.slider.valueChanged.connect(self._update_from_slider)
        self.textbox.returnPressed.connect(self._update_from_value)

        self.slider.setValue(0)

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


class ColorBarWidget(QW.QWidget):
    """
    Contains the colour bar and controls to change bounds
    """

    valueChanged = QtCore.Signal(float, float)

    def __init__(self):
        super().__init__()

        main_layout = QW.QVBoxLayout(self)

        figure = Figure()
        figure.set_frameon(False)
        self.canvas = FigureCanvas(figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.axis = self.canvas.figure.add_axes([0, 0.05, 0.2, 0.9])

        self.upperTextBox = QW.QLineEdit()
        self.lowerTextBox = QW.QLineEdit()

        main_layout.addWidget(self.upperTextBox)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.lowerTextBox)

        #: Colour bar limits
        self.bounds = [numpy.nan, numpy.nan]

        self.setFixedWidth(80)

    def setBounds(self, bounds):
        self.bounds = bounds

        self.lowerTextBox.setText("%.2e"%bounds[0])
        self.upperTextBox.setText("%.2e"%bounds[1])

    def redraw(self, plot):
        """
        Redraw the colour bar
        """
        self.axis.clear()
        if plot is not None:
            plt.colorbar(plot, cax=self.axis)

        self.canvas.draw()

    def get_plot_args(self):
        kwargs = {}
        if self.bounds[0] < 0 < self.bounds[1]:
            kwargs['vmax'] = numpy.abs(self.bounds).max()
        else:
            kwargs['vmin'] = self.bounds[0]
            kwargs['vmax'] = self.bounds[1]
        return kwargs


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

        figure_group = QW.QGroupBox()
        figure_layout = QW.QHBoxLayout(figure_group)

        figure = Figure(tight_layout=True)
        figure.set_frameon(False)
        self.canvas = FigureCanvas(figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.axis = self.canvas.figure.subplots()

        self.colorbar = ColorBarWidget()

        figure_layout.addWidget(self.canvas)
        figure_layout.addWidget(self.colorbar)

        main_layout.addWidget(figure_group)

        #: Dataset being inspected
        self.dataset = dataset

        # Setup list of variables, further setup is done by change_variable()
        classes = classify_vars(dataset)
        variables = sorted([v for v in classes['data'] if dataset[v].ndim >= 2])
        self.varlist.addItems(variables)

        # Connect slots
        self.varlist.currentIndexChanged.connect(self.change_variable)
        self.xdim.activated.connect(self.change_axes)
        self.ydim.activated.connect(self.change_axes)

        #: Currently active variable
        self.variable = None

        #: Values for non-axis dimensions
        self.dims = {}
        dims_group = QW.QGroupBox()
        dims_layout = QW.QVBoxLayout(dims_group)

        # Create widgets for coordinates
        for name in self.dataset.coords:
            self.dims[name] = DimensionWidget(self.dataset[name])
            self.dims[name].valueChanged.connect(self.redraw)
            dims_layout.addWidget(self.dims[name])

        # Create widgets for bare dims
        for name in self.dataset.dims:
            if name not in self.dims:
                da = xarray.DataArray(range(self.dataset.dims[name]))
                self.dims[name] = DimensionWidget(da)
                self.dims[name].valueChanged.connect(self.redraw)
                dims_layout.addWidget(self.dims[name])

        main_layout.addWidget(dims_group)

        if len(variables) > 0:
            self.change_variable()


    def _get_variable_dims(self):
        """
        Get the available dimensions for the current variable
        """
        return set(self.variable.coords.keys()).union(self.variable.dims)


    def change_variable(self, index=0):
        """
        The active variable has changed
        """
        old_dims = []
        if self.variable is not None:
            old_dims = self._get_variable_dims()

        varname = self.varlist.currentText()
        self.variable = self.dataset[varname]
        print('\nVariable details:')
        print(self.variable)

        self.colorbar.setBounds(dask.array.stack([self.variable.min(), self.variable.max()]).compute())

        if self._get_variable_dims() != old_dims:
            self.update_dimensions()

        self.redraw()


    def update_dimensions(self):
        """
        Update dimension lists based on the current variable
        """
        # Refresh dimensions
        newdims = sorted(self._get_variable_dims())

        self.xdim.clear()
        self.xdim.addItems(newdims)

        x = 0
        lon = identify_lon(self.variable)
        if lon is not None:
            x = self.xdim.findText(lon)
        self.xdim.setCurrentIndex(x)

        self.ydim.clear()
        self.ydim.addItems(newdims)

        y = 1
        lat = identify_lat(self.variable)
        if lat is not None:
            y = self.ydim.findText(lat)
        self.ydim.setCurrentIndex(y)

        self.change_axes()



    def change_axes(self):
        """
        The selected plotting axes have changed
        """
        x = self.xdim.currentText()
        y = self.ydim.currentText()

        variable_dims = self._get_variable_dims()
        for d, w in self.dims.items():
            w.setVisible(d in variable_dims)

        for d in [x, y, *self.variable[x].dims, *self.variable[y].dims]:
            self.dims[d].setVisible(False)

        lon = identify_lon(self.variable)
        lat = identify_lat(self.variable)

        if not isinstance(self.axis, cartopy.mpl.geoaxes.GeoAxes) and (x == lon and y == lat):
            # Convert from standard axes to cartopy
            self.axis.remove()
            self.axis = self.canvas.figure.subplots(subplot_kw={
                'projection': cartopy.crs.PlateCarree(central_longitude=180.0)})
        elif isinstance(self.axis, cartopy.mpl.geoaxes.GeoAxes) and (x != lon or y != lat):
            # Convert from cartopy to standard axes
            self.axis.remove()
            self.axis = self.canvas.figure.subplots()

        self.redraw()


    def redraw(self):
        self.axis.clear()

        x = self.xdim.currentText()
        y = self.ydim.currentText()

        plot = None
        if x != y:
            v = self.variable

            plot_args = {}
            if isinstance(self.axis, cartopy.mpl.geoaxes.GeoAxes):
                plot_args['transform'] = cartopy.crs.PlateCarree()
                self.axis.coastlines(alpha=0.2)

            # # Flatten passive dims
            # for d in self.variable.coords:
            #     if d not in [x,y]:
            #         v = v.isel({d:self.dims[d].value()})

            # Plot data
            try:
                plot = v.plot.pcolormesh(x, y, ax=self.axis,
                        add_colorbar=False,
                        **plot_args,
                        **self.colorbar.get_plot_args(),
                        )
            except Exception as e:
                print(e)

        self.canvas.draw()
        self.colorbar.redraw(plot)
