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
import urllib.request, urllib.error, urllib.parse
import requests, json
from .. connect.connect import *
from .. main.utils import Utils

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'handlers.ui'))

class Ui_Handlers(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Handlers, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../qgis_patrac_settings"
        self.Utils = Utils(self.parent)

        # Psovodi HS
        self.hsCallType = 0
        self.pushButtonCheckAvailability.clicked.connect(self.checkIncidentHandlers)
        self.pushButtonCreateIncident.clicked.connect(self.callHandlers)
        self.pushButtonShowInAction.clicked.connect(self.showInAction)
        self.pushButtonMessages.clicked.connect(self.showMessages)
        self.incidentId = None
        self.readConfig()
        # self.fillHSConfig()

    def readConfig(self):
        with open(self.settingsPath + "/config/config.json") as json_file:
            self.config = json.load(json_file)

    def updateSettings(self):
        self.project_settings = self.Utils.getProjectInfo()

    def accept(self):
        self.close()

    def showInAction(self):
        QMessageBox.information(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Not yet implemented"))

    def showMessages(self):
        QMessageBox.information(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Not yet implemented"))

    def checkIncidentHandlers(self):
        self.hsCallType = 0
        self.createIncident("https://www.horskasluzba.cz/cz/app-patrac-new-incident-test")

    def callHandlers(self):
        self.hsCallType = 1
        self.createIncident("https://www.horskasluzba.cz/cz/app-patrac-new-incident")

    def createIncident(self, urlInput):
        if self.project_settings is None:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong project"), self.tr("This function is avaialble from projects created in at least version 3.12.22"))
            return
        if len(self.project_settings['projectname']) < 5:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing Title"))
            return
        if len(self.project_settings['projectdesc']) < 5:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing Description"))
            return
        if len(self.config["hsapikey"]) < 24:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing API Key"))
            return
        if len(self.project_settings['coordinatortel']) < 9:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing Phone"))
            return

        distance = 500
        try:
            distance = int(self.lineEditDistance.text())
        except ValueError:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Enter distance in km"))
            return

        if self.project_settings['placehandlers_lon'] == 0.0 or self.project_settings['placehandlers_lat'] == 0.0:
            centroid = self.getCentroid()
            lon = centroid.x()
            lat = centroid.y()
        else:
            lon = self.project_settings['placehandlers_lon']
            lat = self.project_settings['placehandlers_lat']

        url = urlInput + "?"
        url += "accessKey=" + self.config["hsapikey"]
        url += "&lat=" + str(lat)
        url += "&lng=" + str(lon)
        url += "&title=" + urllib.parse.quote(self.project_settings['projectname'])
        url += "&text=" + urllib.parse.quote(self.project_settings['projectdesc'])
        url += "&searchRadius=" + str(distance)
        url += "&userPhone=" + urllib.parse.quote(self.project_settings['coordinatortel'])
        url += "&createIncident=1"

        self.incident = Connect()
        self.incident.setUrl(url)
        self.incident.statusChanged.connect(self.onIncidentResponse)
        self.incident.start()

    def onIncidentResponse(self, response):
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            if len(data) > 20:
                self.fillSystemUsersHS(data)
            else:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not create incident"))
        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def fillSystemUsersHS(self, data):
        msg = self.tr("Can not read data")
        hsdata = None
        hsusersids = ""
        try:
            hsdata = json.loads(data)
        except:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), msg)
            return

        if hsdata["ok"] == 1:
            self.parent.iface.messageBar().pushMessage(self.tr("Success"), self.tr("Connected"), level=Qgis.Info)
            # print(hsdata["users"])
            self.incidentId = hsdata["IncidentId"]
            self.tableWidgetSystemUsersHS.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Phone"), self.tr("Distance")])
            self.tableWidgetSystemUsersHS.setColumnWidth(1, 300);
            self.tableWidgetSystemUsersHS.setRowCount(len(hsdata["users"]))
            i = 0
            for user in hsdata["users"]:
                self.tableWidgetSystemUsersHS.setItem(i, 0, QTableWidgetItem(user["name"]))
                self.tableWidgetSystemUsersHS.setItem(i, 1, QTableWidgetItem(user["phone"]))
                self.tableWidgetSystemUsersHS.setItem(i, 2, QTableWidgetItem(str(round(float(user["distance"])))))
                hsusersids += "hs" + user["id"] + ";"
                i += 1
            if self.hsCallType == 1 or self.config["debug_level"] > 0:
                self.setSystemUsersHSStatus(hsusersids, "onduty")
            self.tableWidgetSystemUsersHS.sortItems(2, QtCore.Qt.AscendingOrder)
        else:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), msg)

    def setSystemUsersHSStatus(self, hsusersids, status):
        # print(hsusersids)
        # Connects to the server to call the selected users on duty
        if hasattr(self, 'searchID') and self.searchID != "":
            self.connect = Connect()
            self.connect.setUrl(self.serverUrl + 'users.php?operation=changestatushs&id=' + self.systemid + '&status_to=' + status + '&ids=' + hsusersids + "hs0" + "&searchid=" + self.searchID)
            self.connect.statusChanged.connect(self.onStatusChanged)
            self.connect.start()

    def getCentroid(self):
        center = self.parent.iface.mapCanvas().center()
        srs = self.parent.iface.mapCanvas().mapSettings().destinationCrs()
        source_crs = QgsCoordinateReferenceSystem(srs)
        dest_crs = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        xyWGS = transform.transform(center.x(), center.y())
        return xyWGS
