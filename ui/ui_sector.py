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
        self.type = None
        self.unit = 0
        self.accepted = False
        self.sectorsProgressType.addItem(self.tr("Handler"))
        self.sectorsProgressType.addItem(self.tr("Person"))
        self.sectorsProgressType.addItem(self.tr("Drone"))
        self.sectorsProgressType.addItem(self.tr("Other"))

    def setFeature(self, feature):
        self.feature = feature
        if isinstance(feature.attributes()[1], str):
            self.labelSectorId.setText(self.tr("SECTOR") + ": " + feature.attributes()[1])
        self.mDateTimeEditChange.setDateTime(QDateTime.currentDateTime())
        if isinstance(feature.attributes()[6], str):
            self.lineEditComment.setText(feature.attributes()[6])
        else:
            self.lineEditComment.setText("")
        if not isinstance(feature.attributes()[3], int):
            self.sectorsProgressType.setCurrentIndex(self.unit)
            if self.type is not None:
                if self.type == 0:
                    self.sectorsProgressStateRisk.setChecked(True)
                if self.type == 1:
                    self.sectorsProgressStateStarted.setChecked(True)
                if self.type == 2:
                    self.sectorsProgressStateFinished.setChecked(True)
        if isinstance(feature.attributes()[3], int):
            if isinstance(feature.attributes()[4], str):
                self.sectorsProgressType.setCurrentIndex(int(feature.attributes()[4]))
            if feature.attributes()[3] == 0:
                self.sectorsProgressStateStarted.setChecked(True)
            if feature.attributes()[3] == 1:
                self.sectorsProgressStateFinished.setChecked(True)
            if feature.attributes()[3] == 2:
                self.sectorsProgressStateRisk.setChecked(True)
        self.accepted = False

    def getAccepted(self):
        return self.accepted

    def accept(self):
        # TODO fix based on new structure
        if self.feature is not None:
            self.feature.setAttribute(6, self.lineEditComment.text())
            # Attribute position in the list
            attribute = 3
            if self.sectorsProgressStateNotStarted.isChecked() == True:
                type = None
            if self.sectorsProgressStateStarted.isChecked() == True:
                type = 1
                unit = self.sectorsProgressType.currentIndex()
                self.unit = unit
            if self.sectorsProgressStateFinished.isChecked() == True:
                type = 2
            if self.sectorsProgressStateRisk.isChecked() == True:
                type = 0
            self.type = type
            self.feature.setAttribute(attribute, type)
            if type is None:
                self.feature.setAttribute(attribute + 1, None)
                self.feature.setAttribute(7, None)
                self.feature.setAttribute(8, None)
            if type == 1:
                self.feature.setAttribute(attribute + 1, unit)
            if type == 1 or type == 0:
                self.feature.setAttribute(7, self.mDateTimeEditChange.dateTime().toString('dd.MM.yyyy hh:mm:ss'))
            if type == 2:
                self.feature.setAttribute(8, self.mDateTimeEditChange.dateTime().toString('dd.MM.yyyy hh:mm:ss'))
            self.accepted = True
        self.close()
