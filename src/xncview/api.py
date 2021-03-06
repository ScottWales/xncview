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

from .widget import Widget

import sys
from matplotlib.backends.qt_compat import QtWidgets as QW


def xncview(dataset):
    """
    Starts a QT window to display the data

    Args:
        dataset: xarray.Dataset
    """
    QApp = QW.QApplication.instance()
    if QApp is None:
        QApp = QW.QApplication(sys.argv)

    widget = Widget(dataset)
    widget.resize(1200,800)
    widget.show()

    return QApp.exec_()
