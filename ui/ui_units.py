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
import csv, io

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'units.ui'))

class Ui_Units(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Units, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../qgis_patrac_settings"
        self.unitsLabels = [self.tr("Handler"), self.tr("Searcher"), self.tr("Rider"), self.tr("Car"), self.tr("Drone"), self.tr("Diver"), self.tr("Other")]

    def accept(self):
        self.writeUnits()
        self.close()

    def updateTable(self):
        self.fillTableWidgetUnits("/grass/units.txt", self.tableWidgetUnits)

    def writeUnits(self):
        # Units can be changes so the units.txt is written
        f = io.open(self.settingsPath + '/grass/units.txt', 'w', encoding='utf-8')
        for i in range(0, 7):
            for j in range(0, 2):
                value = self.tableWidgetUnits.item(i, j).text()
                if value == '':
                    value = '0'
                unicodeValue = self.getUnicode(value)
                if j == 0:
                    f.write(unicodeValue)
                else:
                    f.write(";" + unicodeValue)
            f.write("\n")
        f.close()

    def fillTableWidgetUnits(self, fileName, tableWidget):
        """Fills table with units"""
        tableWidget.setHorizontalHeaderLabels([self.tr("Count"), self.tr("Note")])
        tableWidget.setVerticalHeaderLabels(self.unitsLabels)
        tableWidget.setColumnWidth(1, 600)
        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        # Reads CSV and populate the table
        with open(settingsPath + fileName, "r") as fileInput:
            i = 0
            for row in csv.reader(fileInput, delimiter=';'):
                j = 0
                unicode_row = row
                # yield row.encode('utf-8')
                for field in unicode_row:
                    tableWidget.setItem(i, j, QTableWidgetItem(field))
                    j = j + 1
                i = i + 1

    def getUnicode(self, strOrUnicode, encoding='utf-8'):
        """Converts string to unicode"""
        strOrUnicode = self.ifNumberGetString(strOrUnicode)
        if isinstance(strOrUnicode, str):
            return strOrUnicode
        return str(strOrUnicode, encoding, errors='ignore')

    def ifNumberGetString(self, number):
        """Converts number to string"""
        convertedStr = number
        if isinstance(number, int) or \
                isinstance(number, float):
            convertedStr = str(number)
        return convertedStr
