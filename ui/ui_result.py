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
import shutil
import csv
import io
from qgis.PyQt import QtWidgets,QtCore, QtGui, uic
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *
import urllib.request, urllib.error, urllib.parse
import socket
import zipfile
from time import gmtime, strftime
from ..connect.connect import *
from .. main.utils import Utils

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'result.ui'))

class Ui_Result(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, widget):
        """Constructor."""
        super(Ui_Result, self).__init__()

        self.widget = widget
        self.Utils = Utils(self.widget)
        self.serverUrl = self.widget.serverUrl
        self.systemid = self.widget.systemid

        self.setupUi(self)
        self.pushButtonNotFound.clicked.connect(self.acceptNotFound)

        self.DATAPATH = ''
        self.searchid = ''

        self.point = None

        date = QDate.currentDate();
        self.dateTimeEditMissing.setDate(date)

        self.comboBoxSex.addItem(self.tr("Male"))
        self.comboBoxSex.addItem(self.tr("Female"))

        self.comboBoxTerrain.addItem(self.tr("Yes"))
        self.comboBoxTerrain.addItem(self.tr("No"))
        self.comboBoxTerrain.addItem(self.tr("Partly"))

        self.comboBoxPurpose.addItem(self.tr("Alzheimer"))
        self.comboBoxPurpose.addItem(self.tr("Demention"))
        self.comboBoxPurpose.addItem(self.tr("Despondent"))
        self.comboBoxPurpose.addItem(self.tr("Retarded"))
        self.comboBoxPurpose.addItem(self.tr("Psychical ilness"))
        self.comboBoxPurpose.addItem(self.tr("Suicider"))
        self.comboBoxPurpose.addItem(self.tr("Accident"))
        self.comboBoxPurpose.addItem(self.tr("Home escape"))
        self.comboBoxPurpose.addItem(self.tr("Desorientation"))
        self.comboBoxPurpose.addItem(self.tr("Other"))

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

        self.comboBoxPlace.addItem(self.tr("Vineyard / Hop garden"))
        self.comboBoxPlace.addItem(self.tr("Garden"))
        self.comboBoxPlace.addItem(self.tr("Meadow"))
        self.comboBoxPlace.addItem(self.tr("Forest"))
        self.comboBoxPlace.addItem(self.tr("Field with plants"))
        self.comboBoxPlace.addItem(self.tr("Field without plants"))
        self.comboBoxPlace.addItem(self.tr("Water body"))
        self.comboBoxPlace.addItem(self.tr("Water creek"))
        self.comboBoxPlace.addItem(self.tr("Intravilan"))
        self.comboBoxPlace.addItem(self.tr("Other"))

        self.comboBoxPlace2.addItem(self.tr("Next to building"))
        self.comboBoxPlace2.addItem(self.tr("Inside building"))
        self.comboBoxPlace2.addItem(self.tr("Next to path"))
        self.comboBoxPlace2.addItem(self.tr("On interface of different landtypes"))
        self.comboBoxPlace2.addItem(self.tr("Bush"))
        self.comboBoxPlace2.addItem(self.tr("Mine"))
        self.comboBoxPlace2.addItem(self.tr("Rocks"))
        self.comboBoxPlace2.addItem(self.tr("On road"))
        self.comboBoxPlace2.addItem(self.tr("Other"))

        self.comboBoxHealth2.addItem(self.tr("No health problems"))
        self.comboBoxHealth2.addItem(self.tr("Unconsciousness"))
        self.comboBoxHealth2.addItem(self.tr("Bleeding"))
        self.comboBoxHealth2.addItem(self.tr("Dead"))
        self.comboBoxHealth2.addItem(self.tr("Poison"))
        self.comboBoxHealth2.addItem(self.tr("Concussion"))
        self.comboBoxHealth2.addItem(self.tr("Hypothermia"))
        self.comboBoxHealth2.addItem(self.tr("Physical exhaustion"))
        self.comboBoxHealth2.addItem(self.tr("Fractures"))
        self.comboBoxHealth2.addItem(self.tr("Other"))

    def setPoint(self, point):
        self.point = point
        self.lineEditCoords.setText(str(round(self.point.x())) + ' ' + str(round(self.point.y())))

    def accept(self):
        self.saveXML()
        self.saveHTML()
        self.acceptNoDiff()

    def acceptNotFound(self):
        self.saveXMLNoResult()
        self.acceptNoDiff()

    def acceptNoDiff(self):
        self.closeHSSearch()
        self.removePersonInfo()
        self.clearUsersInCall()
        self.zipDir()
        self.zipForServer()
        self.close()

    def clearUsersInCall(self):
        path = self.Utils.getDataPath() + "/pracovni/users_in_call.json"
        with open(path, "w") as outfile:
            json.dump([], outfile)

    def saveHTML(self):
        html = io.open(self.DATAPATH + "/search/result.html", encoding='utf-8', mode="w")
        html.write('<!DOCTYPE html>\n')
        html.write('<html><head><meta charset = "UTF-8">\n')
        html.write('<title>' + self.tr("Result") + '</title>\n')
        html.write('</head>\n')
        html.write('<body>\n')
        html.write("<h1>" + self.tr("Result") + "</h1>\n")
        html.write("<p>" + self.tr("Position from map (S-JTSK)") + ": " + self.lineEditCoords.text() + "</p>\n")
        html.write("<p>" + self.tr("Missing from") + ": " + self.dateTimeEditMissing.text() + "</p>\n")
        html.write("<p>" + self.tr("Reported after missing (h)") + ": " + self.spinBoxHourFromMissing.text() + " h</p>\n")
        html.write("<p>" + self.tr("Sex") + ": " + self.comboBoxSex.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Age") + ": " + self.spinBoxAge.text() + "</p>\n")
        html.write("<p>" + self.tr("Known terrain") + ": " + self.comboBoxTerrain.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Purpose") + ": " + self.comboBoxPurpose.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Condition") + ": " + self.comboBoxCondition.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Known health state") + ": " + self.comboBoxHealth.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Hours from report") + ": " + self.spinBoxHourFromAnnounce.text() + "</p>\n")
        html.write("<p>" + self.tr("Place") + ": " + self.comboBoxPlace.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Detail information about place") + ": " + self.comboBoxPlace2.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Current health state") + ": " + self.comboBoxHealth2.currentText() + "</p>\n")
        html.write("<p>" + self.tr("Note") + ": " + self.plainTextEditNote.toPlainText() + "</p>\n")
        html.write("</body>\n")
        html.write("</html>\n")
        html.close()

    def getPersonType(self):
        project_settings = self.Utils.getProjectInfo()
        person_types_text = [self.tr("Child 1-3"), self.tr("Child 3-6"), self.tr("Child 7-12"), self.tr("Child 13-15"), self.tr("Despondent"), self.tr("Psychical ilness"), self.tr("Retarded"), self.tr("Alzheimer"), self.tr("Turist"), self.tr("Demention")]
        return [project_settings["persontype"], person_types_text[project_settings["persontype"] - 1]]

    def saveXMLNoResult(self):
        person_type = self.getPersonType()
        xml = io.open(self.DATAPATH + "/search/result.xml", encoding='utf-8', mode='w')
        xml.write('<?xml version="1.0"?>\n')
        xml.write("<result>\n")
        xml.write("<person_type>" + str(person_type[0]) + "</person_type>\n")
        xml.write("<!--" + person_type[1] + "-->\n")
        xml.write("</result>\n")
        xml.close()

    def saveXML(self):
        person_type = self.getPersonType()
        xml = io.open(self.DATAPATH + "/search/result.xml", encoding='utf-8', mode='w')
        xml.write('<?xml version="1.0"?>\n')
        xml.write("<result>\n")
        xml.write("<coords>" + self.lineEditCoords.text() + "</coords>\n")
        xml.write("<datetimemissing>" + self.dateTimeEditMissing.text() + "</datetimemissing>\n")
        xml.write("<hourfrommissing>" + self.spinBoxHourFromMissing.text() + "</hourfrommissing>\n")
        xml.write("<sex>" + str(self.comboBoxSex.currentIndex()) + "</sex>\n")
        xml.write("<!--" + self.comboBoxSex.currentText() + "-->\n")
        xml.write("<age>" + self.spinBoxAge.text() + "</age>\n")
        xml.write("<terrain>" + str(self.comboBoxTerrain.currentIndex()) + "</terrain>\n")
        xml.write("<!--" + self.comboBoxTerrain.currentText() + "-->\n")
        xml.write("<purpose>" + str(self.comboBoxPurpose.currentIndex()) + "</purpose>\n")
        xml.write("<!--" + self.comboBoxPurpose.currentText() + "-->\n")
        xml.write("<condition>" + str(self.comboBoxCondition.currentIndex()) + "</condition>\n")
        xml.write("<!--" + self.comboBoxCondition.currentText() + "-->\n")
        xml.write("<health>" + str(self.comboBoxHealth.currentIndex()) + "</health>\n")
        xml.write("<!--" + self.comboBoxHealth.currentText() + "-->\n")
        xml.write("<hourfromannonce>" + self.spinBoxHourFromAnnounce.text() + "</hourfromannonce>\n")
        xml.write("<place>" + str(self.comboBoxPlace.currentIndex()) + "</place>\n")
        xml.write("<!--" + self.comboBoxPlace.currentText() + "-->\n")
        xml.write("<place2>" + str(self.comboBoxPlace2.currentIndex()) + "</place2>\n")
        xml.write("<!--" + self.comboBoxPlace2.currentText() + "-->\n")
        xml.write("<health2>" + str(self.comboBoxHealth2.currentIndex()) + "</health2>\n")
        xml.write("<!--" + self.comboBoxHealth2.currentText() + "-->\n")
        xml.write("<note>" + self.plainTextEditNote.toPlainText() + "</note>\n")
        xml.write("<person_type>" + str(person_type[0]) + "</person_type>\n")
        xml.write("<!--" + person_type[1] + "-->\n")
        xml.write("</result>\n")
        xml.close()

    def zipDir(self):
        self.setCursor(Qt.WaitCursor)
        parts = self.DATAPATH.split('/')
        filename = parts[len(parts)-1] + "_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + ".zip"
        zipf = zipfile.ZipFile(self.DATAPATH + '/../' + filename, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.DATAPATH):
            for file in files:
                zipf.write(os.path.join(root, file))
        zipf.close()
        self.setCursor(Qt.ArrowCursor)

    def zipForServer(self):
        self.setCursor(Qt.WaitCursor)
        project_settings = self.Utils.getProjectInfo()
        parts = self.DATAPATH.split('/')
        filename = parts[len(parts)-1] + "_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + "_export.zip"
        if project_settings["projectversion"] == 0:
            filename = "TEST_" + filename
        zipf = zipfile.ZipFile(self.DATAPATH + '/../' + filename, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.DATAPATH + '/search/gpx'):
            for file in files:
                zipf.write(os.path.join(root, file))
        zipf.write(self.DATAPATH + '/search/result.xml')
        zipf.write(self.DATAPATH + '/pracovni/mista.shp')
        zipf.write(self.DATAPATH + '/pracovni/mista.shx')
        zipf.write(self.DATAPATH + '/pracovni/mista.dbf')
        zipf.write(self.DATAPATH + '/pracovni/sektory_group.shp')
        zipf.write(self.DATAPATH + '/pracovni/sektory_group.shx')
        zipf.write(self.DATAPATH + '/pracovni/sektory_group.dbf')
        zipf.write(self.DATAPATH + '/pracovni/patraci_lines.shp')
        zipf.write(self.DATAPATH + '/pracovni/patraci_lines.shx')
        zipf.write(self.DATAPATH + '/pracovni/patraci_lines.dbf')
        zipf.close()

        self.archivefile = ConnectPost()
        self.archivefile.setUrl(self.serverUrl + "archive.php")
        self.archivefile.statusChanged.connect(self.onArchiveFileResponse)
        self.archivefile.setFilename(self.DATAPATH + '/../' + filename)
        self.archivefile.setData({'operation': 'archive'})
        self.archivefile.start()

        self.setCursor(Qt.ArrowCursor)

    def onArchiveFileResponseError(self):
        self.database = Database(self.widget.pluginPath + "/settings.db")
        self.database.insertRequest(self.archivefile.url, str(self.archivefile.data), self.archivefile.filename)

    def onArchiveFileResponse(self, response):
        if response.status != 200:
            self.widget.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)
            self.onArchiveFileResponseError()
            return
        if response.data.startswith('E'):
            self.widget.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not upload result to the server."), level=Qgis.Warning)
            self.onArchiveFileResponseError()
            return

        self.widget.iface.messageBar().pushMessage(self.tr("Success"), self.tr("Result uploaded to the server."), level=Qgis.Info)

    def setDataPath(self, DATAPATH):
        self.DATAPATH = DATAPATH

    def setSearchid(self, searchid):
        self.searchid = searchid

    def closeHSSearch(self):
        GinaGUID = self.Utils.getProjectInfo()['gina_guid']
        accessKey = self.getAccessKey()

        url = 'https://api.hscr.cz/cz/app-patrac-close-incident?accessKey=' + accessKey + '&GinaGUID=' + GinaGUID
        self.closeHSSearchConnect = Connect()
        self.closeHSSearchConnect.setUrl(url)
        self.closeHSSearchConnect.statusChanged.connect(self.onCloseHSSearchServerResponse)
        self.closeHSSearchConnect.start()

    def removePersonInfo(self):
        self.Utils.updateProjectInfo("lost_name", "")
        self.Utils.updateProjectInfo("lost_age", 0)
        self.Utils.updateProjectInfo("lost_sex", 0)
        self.Utils.updateProjectInfo("lost_from_date_time", "")
        self.Utils.updateProjectInfo("lost_time_from_info", "")
        self.Utils.updateProjectInfo("lost_physical_condition", 0)
        self.Utils.updateProjectInfo("lost_health", 0)
        self.Utils.updateProjectInfo("lost_height", 0)
        self.Utils.updateProjectInfo("lost_body_type", 0)
        self.Utils.updateProjectInfo("lost_hair_color", 0)
        self.Utils.updateProjectInfo("lost_clothes", "")

    def getAccessKey(self):
        with open(self.widget.getPluginPath() + "/../../../qgis_patrac_settings" + "/config/config.json") as json_file:
            config = json.load(json_file)
            accessKey = config['hsapikey']
        return accessKey

    def onCloseHSSearchServerResponse(self, response):
        if response.status == 200:
            searchStatus = response.data.read()
        else:
            self.database = Database(self.widget.pluginPath + "/settings.db")
            self.database.insertRequest(self.closeHSSearchConnect.url, None, None)
            self.widget.iface.messageBar().pushMessage(QApplication.translate("Patrac", "ERROR", None), QApplication.translate("Patrac", "Can not connect to the server.", None), level=Qgis.Warning)
