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
from matplotlib.backends.qt_compat import QtWidgets as QW
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
    

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
        variables = [d.name for d in dataset.data_vars.values() if d.ndim >= 2]
        self.varlist.addItems(variables)

        # Connect slots
        self.varlist.currentIndexChanged.connect(self.change_variable)
        self.xdim.activated.connect(self.redraw)
        self.ydim.activated.connect(self.redraw)

        #: Currently active variable
        self.variable = None

        #: Values for non-axis dimensions
        self.passive_dims = {}

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

        if set(self.variable.dims) != set(old_dims):
            # Refresh dimensions
            self.passive_dims = {d:0 for d in self.variable.dims}

            self.xdim.clear()
            self.xdim.addItems(self.variable.dims)
            self.xdim.setCurrentIndex(1)

            self.ydim.clear()
            self.ydim.addItems(self.variable.dims)
            self.ydim.setCurrentIndex(0)

        self.redraw()


    def redraw(self):
        self.axis.clear()

        x = self.xdim.currentText()
        y = self.ydim.currentText()

        if x != y:
            v = self.variable

            # Flatten passive dims
            for d, i in self.passive_dims.items():
                if d not in [x,y]:
                    v = v.isel({d:i})

            # Plot data
            v.plot.pcolormesh(x, y, add_colorbar=False, ax=self.axis)

        self.canvas.draw()
