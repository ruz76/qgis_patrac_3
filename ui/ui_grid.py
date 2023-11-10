# -*- coding: utf-8 -*-

#******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora hledání pohřešované osoby
#
# Copyright (C) 2017-2019 Jan Růžička (jan.ruzicka.vsb@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
#******************************************************************************

import os
from qgis.PyQt import QtWidgets,QtCore, QtGui, uic
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from PyQt5.QtCore import QDateTime

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'grid.ui'))

class Ui_Grid(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self):
        """Constructor."""
        super(Ui_Grid, self).__init__()
        self.setupUi(self)
        self.parent = None
        self.method = 'full'

    def setParent(self, parent):
        self.parent = parent

    def setMethod(self, method):
        self.method = method
        if self.method == 'full':
            self.radioButtonGridSize10m.setEnabled(False)
        else:
            self.radioButtonGridSize10m.setEnabled(True)

    def accept(self):
        try:
            gridsize = 100
            if self.radioButtonGridSize10m.isChecked():
                gridsize = 10
            if self.radioButtonGridSize1000m.isChecked():
                gridsize = 1000
            self.parent.setGridSize(gridsize)
            self.close()
        except:
            QMessageBox.information(None, self.tr("ERROR"), self.tr("You have to insert integer."))
