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
import requests, json
from .. main.utils import Utils

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'person.ui'))

class Ui_Person(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Person, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../qgis_patrac_settings"
        self.Utils = Utils(self.parent)
        self.fillBoxes()

    def fillBoxes(self):
        self.comboBoxSex.addItem(self.tr("Male"))
        self.comboBoxSex.addItem(self.tr("Female"))

        self.comboBoxCondition.addItem(self.tr("Very good"))
        self.comboBoxCondition.addItem(self.tr("Good"))
        self.comboBoxCondition.addItem(self.tr("Bad"))
        self.comboBoxCondition.addItem(self.tr("Very bad"))

        self.comboBoxHealth.addItem(self.tr("No health problems"))
        self.comboBoxHealth.addItem(self.tr("Diabetes"))
        self.comboBoxHealth.addItem(self.tr("Epilepsie"))
        self.comboBoxHealth.addItem(self.tr("Movement problems"))
        self.comboBoxHealth.addItem(self.tr("Hypertension"))
        self.comboBoxHealth.addItem(self.tr("Other"))

        self.comboBoxBodyType.addItem(self.tr("Thin"))
        self.comboBoxBodyType.addItem(self.tr("Middle"))
        self.comboBoxBodyType.addItem(self.tr("Thick"))
        self.comboBoxBodyType.addItem(self.tr("Obese"))

        self.comboBoxHairColor.addItem(self.tr("Blonde"))
        self.comboBoxHairColor.addItem(self.tr("Brunette"))
        self.comboBoxHairColor.addItem(self.tr("Reddish"))

    def setItems(self):
        self.project_settings = self.Utils.getProjectInfo()
        self.lineEditName.setText(self.project_settings["lost_name"])
        self.comboBoxSex.setCurrentIndex(self.project_settings["lost_sex"])
        self.spinBoxAge.setValue(self.project_settings["lost_age"])
        date = QDate.currentDate();
        if (self.project_settings["lost_from_date_time"]) == "":
            self.dateTimeEditMissingFrom.setDate(date)
        else:
            # TODO set from config
            self.dateTimeEditMissingFrom.setDate(date)
        if (self.project_settings["lost_time_from_info"]) == "":
            self.dateTimeEditMissingReported.setDate(date)
        else:
            # TODO set from config
            self.dateTimeEditMissingReported.setDate(date)
        self.comboBoxCondition.setCurrentIndex(self.project_settings["lost_physical_condition"])
        self.comboBoxHealth.setCurrentIndex(self.project_settings["lost_health"])
        self.spinBoxHeight.setValue(self.project_settings["lost_height"])
        self.comboBoxBodyType.setCurrentIndex(self.project_settings["lost_body_type"])
        self.comboBoxHairColor.setCurrentIndex(self.project_settings["lost_hair_color"])
        self.lineEditClothes.setText(self.project_settings["lost_clothes"])

    def updateInfo(self):
        self.Utils.updateProjectInfo("lost_name", self.lineEditName.text())
        self.Utils.updateProjectInfo("lost_age", self.spinBoxAge.value())
        self.Utils.updateProjectInfo("lost_sex", self.comboBoxSex.currentIndex())
        self.Utils.updateProjectInfo("lost_from_date_time", self.dateTimeEditMissingFrom.text())
        self.Utils.updateProjectInfo("lost_time_from_info", self.dateTimeEditMissingReported.text())
        self.Utils.updateProjectInfo("lost_physical_condition", self.comboBoxCondition.currentIndex())
        self.Utils.updateProjectInfo("lost_health", self.comboBoxHealth.currentIndex())
        self.Utils.updateProjectInfo("lost_height", self.spinBoxHeight.value())
        self.Utils.updateProjectInfo("lost_body_type", self.comboBoxBodyType.currentIndex())
        self.Utils.updateProjectInfo("lost_hair_color", self.comboBoxHairColor.currentIndex())
        self.Utils.updateProjectInfo("lost_clothes", self.lineEditClothes.text())

    def accept(self):
        self.updateInfo()
        self.close()

