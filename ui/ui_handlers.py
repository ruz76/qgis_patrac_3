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
        self.hs_users_in_call = []
        self.pushButtonCheckAvailability.clicked.connect(self.checkIncidentHandlers)
        self.pushButtonCreateIncident.clicked.connect(self.callHandlers)
        self.pushButtonShowInAction.clicked.connect(self.showInAction)
        self.pushButtonMessages.clicked.connect(self.showMessages)
        self.readConfig()
        self.readUsersInCall()

    def readUsersInCall(self):
        path = self.Utils.getDataPath() + "/pracovni/users_in_call.json"
        if os.path.exists(path):
            with open(path, "r") as json_file:
                self.hs_users_in_call = json.load(json_file)

    def saveUsersInCall(self):
        path = self.Utils.getDataPath() + "/pracovni/users_in_call.json"
        with open(path, "w") as outfile:
            json.dump(self.hs_users_in_call, outfile)

    def readConfig(self):
        with open(self.settingsPath + "/config/config.json") as json_file:
            self.config = json.load(json_file)

    def updateSettings(self):
        self.project_settings = self.Utils.getProjectInfo()
        self.readConfig()
        self.readUsersInCall()

    def accept(self):
        self.close()

    def showInAction(self):
        self.getUsersStatus()
        # QMessageBox.information(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Not yet implemented"))

    def showMessages(self):
        QMessageBox.information(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Not yet implemented"))

    def getHsUsersInActionForEmail(self):
        users_ids = []
        users = ""
        for user in self.hs_users_in_call:
            if not user["id"] in users_ids:
                users += user["name"] + " " + user["phone"] + "\n"
                users_ids.append(user["id"])
        return users

    def sendEmail(self):
        if self.config["emailfrom"] == "" or self.config["emailto1"] == "" and self.config["emailto2"] == "":
            QMessageBox.infor-mation(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Emails in settings has to be set. Go to the settings dialog."))
            return

        url = "http://sarops.info/smpatrac.php?"
        url += "apikey=" + self.config["hsapikey"]
        url += "&from=" + self.config["emailfrom"]
        url += "&to1=" + self.config["emailto1"]
        url += "&to2=" + self.config["emailto2"]
        url += "&subject=Patraci+akce"
        body = "Pátrací akce: " + self.project_settings['projectname'] + "\n"
        body += "Popis: " + self.project_settings['projectdesc'] + "\n"
        body += "Kontaktní osoba: " + self.project_settings['coordinatorname'] + "\n"
        body += "Telefon na kontaktní osobu: " + self.project_settings['coordinatortel'] + "\n"
        body += "Atestovaní psovodi:\n" + self.getHsUsersInActionForEmail()
        url += "&body=" + urllib.parse.quote(body)

        self.sendemail = Connect()
        self.sendemail.setUrl(url)
        self.sendemail.statusChanged.connect(self.onSendEmailResponse)
        self.sendemail.start()

    def onSendEmailResponse(self, response):
        if response.status == 200:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("INFO"), self.tr("Email with list of selected handlers has been sent"))
        else:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("ERROR"), self.tr("Email with list of selected handlers can not be sent"))

    def checkIncidentHandlers(self):
        self.hsCallType = 0
        self.createIncident("https://www.horskasluzba.cz/cz/app-patrac-new-incident-test")

    def callHandlers(self):
        self.hsCallType = 1
        if self.project_settings["gina_guid"] == "":
            self.createIncident("https://www.horskasluzba.cz/cz/app-patrac-new-incident")
        else:
            self.addUsersIntoCall()

    def createIncident(self, urlInput):
        if self.project_settings is None:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong project"), self.tr("This function is avaialble from projects created in at least version 3.12.22"))
            return
        if len(self.project_settings['projectname']) < 5:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing Title"))
            return
        if len(self.project_settings['projectdesc']) < 5:
            self.project_settings['projectdesc'] = self.tr("No description")
            # QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Wrong input"), self.tr("Missing Description"))
            # return
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
        if self.hsCallType == 0:
            url += "&searchRadius=" + str(distance)
        else:
            url += "&searchRadius=0"
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
                if self.hsCallType == 0:
                    self.pushButtonCreateIncident.setEnabled(True)
            else:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not create incident"))
        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def addUsersIntoCall(self):
        if self.project_settings["gina_guid"] == "":
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not call handlers. Some error occured."))
            return
        hsusersids = ""
        i = 0
        for checkbox in self.hs_users_available_checkboxes:
            if checkbox.isChecked():
                user = self.hs_users_available[i]
                hsusersids += user["id"] + ","
                user["state"] = self.tr("Notified")
                self.hs_users_in_call.append(user)
            i += 1

        if hsusersids != "":
            url = "https://www.horskasluzba.cz/cz/app-patrac-add-users-to-incident?"
            url += "accessKey=" + self.config["hsapikey"]
            url += "&GinaGUID=" + self.project_settings["gina_guid"]
            url += "&users=" + hsusersids[:-1]

            self.adduserstocall = Connect()
            self.adduserstocall.setUrl(url)
            self.adduserstocall.statusChanged.connect(self.onAddUsersIntoCallResponse)
            self.adduserstocall.start()

            self.sendNotification(hsusersids[:-1])
            self.sendEmail()

        else:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("You have to check the handlers."))

    def onAddUsersIntoCallResponse(self, response):
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            if len(data) < 20:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not call handlers. Some error occured."))
            else:
                self.getUsersStatus()
                self.saveUsersInCall()
        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def getUsersStatus(self):
        if self.project_settings["gina_guid"] == "":
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not show handlers in action. Action was not created yet."))
            return

        url = "https://www.horskasluzba.cz/cz/app-patrac-incident-info?"
        url += "accessKey=" + self.config["hsapikey"]
        url += "&GinaGUID=" + self.project_settings["gina_guid"]

        self.getusersstatus = Connect()
        self.getusersstatus.setUrl(url)
        self.getusersstatus.statusChanged.connect(self.onGetUsersStatusResponse)
        self.getusersstatus.start()

    def onGetUsersStatusResponse(self, response):
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            if len(data) < 20:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not connect to the server."))
            else:
                self.fillUsersInAction(data)
                self.pushButtonCreateIncident.setEnabled(False)
        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def sendNotification(self, users):
        if self.project_settings["gina_guid"] == "":
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not notify handlers. Action was not created yet."))
            return

        url = "https://www.horskasluzba.cz/cz/app-patrac-send-notifications?"
        url += "accessKey=" + self.config["hsapikey"]
        url += "&GinaGUID=" + self.project_settings["gina_guid"]
        url += "&notifyUsersType=list"
        url += "&users=" + users

        self.notifyusers = Connect()
        self.notifyusers.setUrl(url)
        self.notifyusers.statusChanged.connect(self.onSendNotificationResponse)
        self.notifyusers.start()

    def onSendNotificationResponse(self, response):
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            if len(data) < 20:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not connect to the server."))
        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def getUserFromCalls(self, user_in_action):
        print(user_in_action)
        print(self.hs_users_in_call)
        for user in self.hs_users_in_call:
            if user["id"] == str(user_in_action["userId"]):
                return user
        return None

    def fillUsersInAction(self, data):
        print("fillUsersInAction")
        print(data)
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
            self.tableWidgetSystemUsersHS.setColumnCount(4)
            self.tableWidgetSystemUsersHS.setHorizontalHeaderLabels([self.tr("Selected"), self.tr("Name"), self.tr("Phone"), self.tr("State")])
            self.tableWidgetSystemUsersHS.setColumnWidth(1, 300);
            self.tableWidgetSystemUsersHS.setRowCount(len(hsdata["incident"]["users"]))
            hs_users = hsdata["incident"]["users"]
            hs_users.sort(key = lambda json : json['userId'])
            self.hs_users_in_action_checkboxes = []
            i = 0
            for user in hs_users:
                row_checkbox = QCheckBox()
                self.hs_users_in_action_checkboxes.append(row_checkbox)
                self.tableWidgetSystemUsersHS.setCellWidget(i, 0, row_checkbox)
                user_from_calls = self.getUserFromCalls(user)
                if user_from_calls is not None:
                    self.tableWidgetSystemUsersHS.setItem(i, 1, QTableWidgetItem(str(user_from_calls["name"])))
                    self.tableWidgetSystemUsersHS.setItem(i, 2, QTableWidgetItem(str(user_from_calls["phone"])))
                    if user["vyzvaPotvrzena"]:
                        if user["lastReactionType"] == "accepted":
                            user_from_calls["state"] = self.tr("Accepted")
                        else:
                            user_from_calls["state"] = self.tr("Not accepted")
                    self.tableWidgetSystemUsersHS.setItem(i, 3, QTableWidgetItem(str(user_from_calls["state"])))
                else:
                    # print("TADY")
                    QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), msg)
                i += 1
                hsusersids += "hs" + str(user["userId"]) + ";"
            self.setSystemUsersHSStatus(hsusersids, "onduty")
        else:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), msg)

    def fillSystemUsersHS(self, data):
        print("fillSystemUsersHS")
        print(data)
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
            if self.hsCallType == 1:
                self.project_settings["hs_incidentid"] = hsdata["IncidentId"]
                self.project_settings["gina_guid"] = hsdata["GinaGUID"]
                self.Utils.updateProjectInfo("hs_incidentid", self.project_settings["hs_incidentid"])
                self.Utils.updateProjectInfo("gina_guid", self.project_settings["gina_guid"])
                self.addUsersIntoCall()
            if self.hsCallType == 0:
                self.tableWidgetSystemUsersHS.setColumnCount(5)
                self.tableWidgetSystemUsersHS.setHorizontalHeaderLabels([self.tr("Selected"), self.tr("Distance"), self.tr("Name"), self.tr("Phone"), self.tr("State")])
                self.tableWidgetSystemUsersHS.setColumnWidth(2, 300);
                self.tableWidgetSystemUsersHS.setRowCount(len(hsdata["users"]))
                self.hs_users_available = []
                self.hs_users_available_checkboxes = []
                hs_users = hsdata["users"]
                hs_users.sort(key = lambda json : json['distance'])
                i = 0
                for user in hs_users:
                    row_checkbox = QCheckBox()
                    self.hs_users_available_checkboxes.append(row_checkbox)
                    self.tableWidgetSystemUsersHS.setCellWidget(i, 0, row_checkbox)
                    self.tableWidgetSystemUsersHS.setItem(i, 1, QTableWidgetItem(str(round(float(user["distance"])))))
                    self.tableWidgetSystemUsersHS.setItem(i, 2, QTableWidgetItem(user["name"]))
                    self.tableWidgetSystemUsersHS.setItem(i, 3, QTableWidgetItem(user["phone"]))
                    user["state"] = self.tr("Available")
                    self.tableWidgetSystemUsersHS.setItem(i, 4, QTableWidgetItem(user["state"]))
                    self.hs_users_available.append(user)
                    i += 1
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
