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
    os.path.dirname(__file__), 'sector.ui'))

class Ui_Sector(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self):
        """Constructor."""
        super(Ui_Sector, self).__init__()
        self.setupUi(self)
        self.feature = None
        self.type = 0

    def setFeature(self, feature, type):
        self.feature = feature
        self.type = type
        self.mDateTimeEditChange.setDateTime(QDateTime.currentDateTime())
        if isinstance(feature.attributes()[7], str):
            self.lineEditComment.setText(feature.attributes()[7])

    def accept(self):
        if self.feature is not None:
            self.feature.setAttribute(7, self.lineEditComment.text())
            print(str(self.mDateTimeEditChange.dateTime()))
            if self.type == 1 or self.type == 0:
                self.feature.setAttribute(8, self.mDateTimeEditChange.dateTime().toString('dd.MM.yyyy hh:mm:ss'))
            if self.type == 2:
                self.feature.setAttribute(9, self.mDateTimeEditChange.dateTime().toString('dd.MM.yyyy hh:mm:ss'))
        self.close()
