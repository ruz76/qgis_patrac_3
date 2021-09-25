# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora pátrání po pohřešované osobě
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
# ******************************************************************************

import os
import sys
import subprocess
import shutil
import csv
import io
from qgis.PyQt import QtWidgets, QtGui, uic
from qgis.core import *
from qgis.gui import *
from qgis import utils
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
import webbrowser
import urllib.request, urllib.error, urllib.parse
import requests, json
from ..connect.connect import *
from string import ascii_uppercase
import urllib3

# import qrcode

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings.ui'))


class Ui_Settings(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for settings"""

    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Settings, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../qgis_patrac_settings"
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.config = None
        self.readConfig()
        self.systemid = self.config["systemid"]
        self.unitsLabels = [self.tr("Handler"), self.tr("Searcher"), self.tr("Rider"), self.tr("Car"), self.tr("Drone"), self.tr("Diver"), self.tr("Other")]

        self.main = parent
        self.iface = self.main.iface
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.comboBoxDistance.addItem(self.tr("LSOM"))
        self.comboBoxDistance.addItem(self.tr("Hill"))
        self.comboBoxDistance.addItem(self.tr("UK"))
        self.comboBoxDistance.addItem(self.tr("User specific"))
        self.comboBoxFriction.addItem(self.tr("Pastorkova"))
        self.comboBoxFriction.addItem(self.tr("User specific"))
        # Fills tables with distances
        self.fillTableWidgetDistance("/grass/distancesLSOM.txt", self.tableWidgetDistancesLSOM, "system")
        self.fillTableWidgetDistance("/grass/distancesHill.txt", self.tableWidgetDistancesHill, "system")
        self.fillTableWidgetDistance("/grass/distancesUK.txt", self.tableWidgetDistancesUK, "system")
        self.fillTableWidgetDistance("/grass/distancesUser.txt", self.tableWidgetDistancesUser, "user")
        # Fills table with friction values
        self.fillTableWidgetFriction("/grass/friction.csv", self.tableWidgetFriction)

        # Fills table with search units
        self.fillTableWidgetUnitsTimes("/grass/units_times.csv", self.tableWidgetUnitsTimes)

        # Fills values for weights of the points
        if os.path.isfile(DATAPATH + "/config/weightlimit.txt"):
            self.fillLineEdit(DATAPATH + "/config/weightlimit.txt", self.lineEditWeightLimit)
        else:
            self.fillLineEdit(self.settingsPath + "/grass/weightlimit.txt", self.lineEditWeightLimit)

        self.drive = "D"
        self.pushButtonHds.clicked.connect(self.testHds)
        self.pushButtonDataHds.clicked.connect(self.testDataHds)
        self.fillDataHdsCmb()
        self.pushButtonUpdateData.clicked.connect(self.updateData)
        self.pushButtonFixData.clicked.connect(self.fixData)

        self.buttonBox.accepted.connect(self.accept)

        self.periodic_scheduler = None
        self.pushButtonShowQrCode.clicked.connect(self.showQrCode)

        self.pushButtonSaveStyle.clicked.connect(self.saveStyle)
        self.pushButtonRecalculateFriction.clicked.connect(self.recalculateFriction)

        self.lineEditAccessKey.editingFinished.connect(self.lineEditAccessKeyEditingFinished)

    def lineEditAccessKeyEditingFinished(self):
        print(self.lineEditAccessKey.text())
        if len(self.lineEditAccessKey.text()) < 24:
            QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("You have to enter valid key of 24 characters."))
            return

        # TODO do it via POST and HTTPS
        url = "http://sarops.info/patrac/kopis.php?"
        url += "ack=" + self.lineEditAccessKey.text()

        self.getemails = Connect()
        self.getemails.setUrl(url)
        self.getemails.statusChanged.connect(self.onGetEmails)
        self.getemails.start()

    def onGetEmails(self, response):
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            emails = json.loads(data)
            if len(emails) < 3:
                QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not find key in the database."))
            else:
                if emails[0] == 'ERROR':
                    QMessageBox.information(self.parent.iface.mainWindow(), self.tr("Error"), self.tr("Can not find key in the database."))
                else:
                    self.lineEditEmailTo1.setText(emails[0])
                    self.lineEditEmailTo2.setText(emails[1])
                    self.config["pcrkrid"] = emails[2]

        else:
            self.parent.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def downloadStats(self):
        # localPath = "/tmp/ka/stats.db"
        localPath = self.drive + ":/patracdata/kraje/" + self.comboBoxDataFix.currentText() + "/vektor/ZABAGED/line_x/stats.db"
        if not os.path.exists(localPath) or (os.path.exists(localPath) and os.path.getsize(localPath) < 1000):
            try:
                if os.path.exists(localPath):
                    os.remove(localPath)
                url = self.serverUrl + "/qgis3/data/stats/" + self.comboBoxDataFix.currentText() + "/stats.db"
                http = urllib3.PoolManager()
                response = http.request('GET', url, preload_content=False)
                content_length = response.headers['Content-Length']
                total_size = int(content_length)
                downloaded = 0
                CHUNK = 256 * 10240
                with open(localPath, 'wb') as fp:
                    while True:
                        chunk = response.read(CHUNK)
                        downloaded += len(chunk)
                        if not chunk:
                            break
                        fp.write(chunk)
                response.release_conn()
            except:
                QMessageBox.information(None, self.tr("ERROR"), self.tr("Can not connect to the server"))

    def fixData(self):
        self.parent.setCursor(Qt.WaitCursor)
        self.setCursor(Qt.WaitCursor)

        if sys.platform.startswith('win'):
            self.downloadStats()
            p = subprocess.Popen((self.pluginPath + "/grass/run_fix_datastore.bat", self.drive + ":/patracdata/kraje/" + self.comboBoxDataFix.currentText(), self.pluginPath))
            p.wait()
            QMessageBox.information(None, self.tr("Fixed"), self.tr("The datastore has been fixed"))
        else:
            # self.downloadStats()
            QMessageBox.information(None, self.tr("Not available"), self.tr("The function is not implemented"))

        self.setCursor(Qt.ArrowCursor)
        self.parent.setCursor(Qt.ArrowCursor)

    def readConfig(self):
        with open(self.settingsPath + "/config/config.json") as json_file:
            self.config = json.load(json_file)

    def writeConfig(self):
        self.config["hsapikey"] = self.lineEditAccessKey.text()
        self.config["emailfrom"] = self.lineEditEmailFrom.text()
        self.config["emailto1"] = self.lineEditEmailTo1.text()
        self.config["emailto2"] = self.lineEditEmailTo2.text()
        with open(self.settingsPath + "/config/config.json", "w") as outfile:
            json.dump(self.config, outfile)

    def fillHSConfig(self):
        self.lineEditAccessKey.setText(self.config["hsapikey"])
        if 'emailfrom' in self.config:
            self.lineEditEmailFrom.setText(self.config["emailfrom"])
        if 'emailto1' in self.config:
            self.lineEditEmailTo1.setText(self.config["emailto1"])
        if 'emailto2' in self.config:
            self.lineEditEmailTo2.setText(self.config["emailto2"])

    def fillDataHdsCmb(self):
        if sys.platform.startswith('win'):
            for i in ascii_uppercase:
                if os.path.exists(i + ":/patracdata"):
                    self.fillDataHdsCmbList(i + ":")
                    self.drive = i
                    break
        else:
            if os.path.exists("/data/patracdata"):
                self.fillDataHdsCmbList("/data")

    def fillDataHdsCmbList(self, disk):
        regions = ["jc", "jm", "ka", "kh", "lb", "ms", "ol", "pa", "pl", "st", "us", "vy", "zl"]
        for region in regions:
            if os.path.exists(disk + "/patracdata/kraje/" + region):
                self.comboBoxDataHds.addItem(region)
                self.comboBoxDataFix.addItem(region)
                self.pushButtonDataHds.setEnabled(True)
                self.pushButtonFixData.setEnabled(True)

    def testDataHds(self):
        self.parent.setCursor(Qt.WaitCursor)
        self.setCursor(Qt.WaitCursor)
        self.main.testHdsData(self.comboBoxDataHds.currentText(), self.textEditHds)
        self.setCursor(Qt.ArrowCursor)
        self.parent.setCursor(Qt.ArrowCursor)

    def saveStyle(self):

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        if layer is not None:
            settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
            name = open(settingsPath + "/styles/sektory_group.txt", 'r').read()
            layer.saveNamedStyle(settingsPath + '/styles/sectors_' + name + '.qml')

    def refreshSystemUsersSetSheduler(self):
        QMessageBox.information(None, self.tr("Not available"), self.tr("The function is not implemented"))

    def incidentEdit(self):
        if self.incidentId is None:
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Wrong input"), self.tr("You have to create incident first"))
            return
        if len(self.lineEditUsername.text()) < 3:
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Wrong input"), self.tr("Enter user"))
            return
        if len(self.lineEditPassword.text()) < 5:
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Wrong input"), self.tr("Enter password"))
            return

        url = "https://api.hscr.cz/cz/hscr-sbook-login?"
        url += "L=" + urllib.parse.quote(self.lineEditUsername.text())
        url += "&H=" + urllib.parse.quote(self.lineEditPassword.text())

        self.sbookaccess = Connect()
        self.sbookaccess.setUrl(url)
        self.sbookaccess.statusChanged.connect(self.onSbookAccess)
        self.sbookaccess.start()

    def onSbookAccess(self, response):
        msg = self.tr("Can not get access")
        if response.status == 200:
            data = response.data.read().decode('utf-8')
            if len(data) > 5:
                hsdata = None
                try:
                    hsdata = json.loads(data)
                except:
                    QMessageBox.information(self.main.iface.mainWindow(), self.tr("Error"), msg)
                    return
                if hsdata["ok"] == 1:
                    urlToOpen = "https://api.hscr.cz/cz/kniha-sluzeb/vyzvy?"
                    urlToOpen += "action=show-record"
                    urlToOpen += "&record_id=" + str(self.incidentId)
                    urlToOpen += "&t=" + hsdata["token"]
                    webbrowser.get().open(urlToOpen)
                else:
                    QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)
            else:
                QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def updateSettings(self):
        self.showSearchId()
        self.showPath()
        self.fillHSConfig()
        # if self.parent.projectname != "":
        #     self.lineEditTitle.setText(self.parent.projectname)
        # if self.parent.projectdesc != "":
        #     self.lineEditText.setText(self.parent.projectdesc)

    def showSearchId(self):
        # Fills textEdit with SearchID
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if DATAPATH != "" and QFileInfo(DATAPATH + "/config/searchid.txt").exists():
            self.searchID = open(DATAPATH + "/config/searchid.txt", 'r').read()
            self.lineEditSearchID.setText(self.searchID)
        else:
            msg = self.tr("Wrong project.")
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Wrong project"), msg)

    def showPath(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        self.labelPath.setText(self.tr("Path to the project") + ": " + prjfi.absolutePath())

    def testHds(self):
        # msg = self.tr("Function is temporarily unavailable. Use data test, please.")
        # QMessageBox.information(self.main.iface.mainWindow(), self.tr("Not available"), msg)
        # return
        self.parent.setCursor(Qt.WaitCursor)
        self.setCursor(Qt.WaitCursor)
        self.main.testHds(self.textEditHds)
        self.setCursor(Qt.ArrowCursor)
        self.parent.setCursor(Qt.ArrowCursor)

    def updateData(self):
        msg = self.tr("Function is not supported")
        QMessageBox.information(self.main.iface.mainWindow(), self.tr("Not available"), msg)
        return

    def getPatracDataPath(self):
        DATAPATH = ''
        letters = "CDEFGHIJKLMNOPQRSTUVWXYZ"
        drives = [letters[i] + ":/" for i in range(len(letters))]
        for drive in drives:
            if os.path.isfile(drive + 'patracdata/cr/projekty/simple/simple.qgs'):
                DATAPATH = drive + 'patracdata/cr/projekty/simple/'
                break
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/cr/projekty/simple/'

        return DATAPATH

    def showHelp(self):
        try:
            DATAPATH = self.getPatracDataPath()
            webbrowser.get().open(
                "file://" + DATAPATH + "doc/index.html")
            # webbrowser.get().open("file://" + DATAPATH + "/sektory/report.html")
            # self.iface.messageBar().pushMessage("Error", "file://" + self.pluginPath + "/doc/index.html", level=Qgis.Critical)
            # webbrowser.get().open("file://" + self.pluginPath + "/doc/index.html")
            # webbrowser.open("file://" + self.pluginPath + "/doc/index.html")
        except (webbrowser.Error):
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not find web browser to open help"), level=Qgis.Critical)

    def fillLineEdit(self, filePath, lineEdit):
        content = open(filePath, 'r').read()
        lineEdit.setText(content)

    def getRegion(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if DATAPATH != "" and QFileInfo(DATAPATH + "/config/region.txt").exists():
            region = open(DATAPATH + "/config/region.txt", 'r').read()
            return region.upper()
        else:
            msg = self.tr("Wrong project.")
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Wrong project"), msg)
            return "KH"

    def getRegionAndSurrounding(self):
        # TODO put to file
        kraj = self.getRegion()
        if kraj == "US":
            return ["US", "LB", "ST", "KA", "PL"]
        if kraj == "ST":
            return ["KH", "PA", "ST", "US"]
        if kraj == "PL":
            return ["PL", "KA", "US", "ST", "JC"]
        if kraj == "KH":
            return ["KH", "PA", "ST", "US"]
        if kraj == "HP":
            return ["HP", "ST"]
        if kraj == "PA":
            return ["PA", "KH", "VY", "OL", "JM"]
        if kraj == "VY":
            return ["VY", "JC", "ST", "JM", "PA"]
        if kraj == "JC":
            return ["JC", "VY", "PL", "ST", "JM"]
        if kraj == "JM":
            return ["JM", "VY", "JC", "ZL", "OL", "PA"]
        if kraj == "ZL":
            return ["ZL", "MS", "OL", "JM"]
        if kraj == "OL":
            return ["OL", "MS", "JM", "ZL", "PA"]
        if kraj == "LB":
            return ["LB", "US", "KH", "ST"]
        if kraj == "MS":
            return ["MS", "ZL", "OL"]
        if kraj == "KA":
            return ["KA", "US", "PL"]

    def callOnDuty(self):
        if hasattr(self, 'searchID') and self.searchID != "":
            self.setStatus("callonduty", self.searchID)

    def callToJoin(self):
        if hasattr(self, 'searchID') and self.searchID != "":
            self.setStatus("calltocome", self.searchID)

    def putToSleep(self):
        self.setStatus("waiting", "")

    def getSelectedSystemUsers(self):
        # indexes = self.selectionModel.selectedIndexes()
        rows = self.tableWidgetSystemUsers.selectionModel().selectedRows()
        # rows = self.tableWidgetSystemUsers.selectionModel().selectedIndexes()
        ids = ""
        first = True
        for row in rows:
            if first:
                ids = ids + self.tableWidgetSystemUsers.item(row.row(), 0).text()
            else:
                ids = ids + ";" + self.tableWidgetSystemUsers.item(row.row(), 0).text()
            first = False
            # ids.append(self.tableWidgetSystemUsers.item(row.row(), 0).text())
            # print(self.tableWidgetSystemUsers.item(row.row(), 0).text());
        return ids

    def getSelectedSystemUsersStatuses(self):
        rows = self.tableWidgetSystemUsers.selectionModel().selectedRows()
        statuses = ""
        first = True
        for row in rows:
            if first:
                statuses = statuses + self.tableWidgetSystemUsers.item(row.row(), 2).text()
            else:
                statuses = statuses + ";" + self.tableWidgetSystemUsers.item(row.row(), 2).text()
            first = False
            # ids.append(self.tableWidgetSystemUsers.item(row.row(), 0).text())
            # print(self.tableWidgetSystemUsers.item(row.row(), 0).text());
        return statuses

    def removeSleepingSystemUsers(self, ids, statuses):
        idsList = ids.split(";")
        statusesList = statuses.split(";")
        idsListOut = []
        for i in range(len(idsList)):
            if statusesList[i] != "sleeping" and statusesList[i] != "released":
                idsListOut.append(idsList[i])

        idsOutput = ""
        first = True
        for id in idsListOut:
            if first:
                idsOutput = idsOutput + id
            else:
                idsOutput = idsOutput + ";" + id
            first = False
        return idsOutput

    def setStatus(self, status, searchid):
        idsSelected = self.getSelectedSystemUsers()
        statuses = self.getSelectedSystemUsersStatuses()
        ids = self.removeSleepingSystemUsers(idsSelected, statuses)
        if len(ids) != len(idsSelected):
            QMessageBox.information(None, self.tr("INFO"),
                                    self.tr("Some of the selected handlersare in sleeping or released state. You have to wait for their wakeup."))
        if ids == "":
            QMessageBox.information(None, self.tr("INFO"), self.tr("You did not select handler that can be called."))
            return

        # Connects to the server to call the selected users on duty
        self.connect = Connect()
        self.connect.setUrl(self.serverUrl + 'users.php?operation=changestatus&id=' + self.systemid + '&status_to=' + status + '&ids=' + ids + "&searchid=" + searchid)
        self.connect.statusChanged.connect(self.onStatusChanged)
        self.connect.start()

    def onStatusChanged(self, response):
        # print(response.status)
        if response.status == 200:
            self.refreshSystemUsers()
            QgsMessageLog.logMessage(str(response.data.read()), "Patrac")
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def refreshSystemUsers(self):
        self.systemusers = Connect()
        self.systemusers.setUrl(self.serverUrl + 'users.php?operation=getsystemusers&id=' + self.systemid)
        self.systemusers.statusChanged.connect(self.onRefreshSystemUsers)
        self.systemusers.start()

    def onRefreshSystemUsers(self, response):
        if response.status == 200:
            list = response.data.read().decode('utf-8')
            if list != "":
                self.fillTableWidgetSystemUsers(list, self.tableWidgetSystemUsers)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def getDataFromUrl(self, url, timeout):
        # self.connect = Connect()
        # self.connect.setUrl(url)
        # self.connect.statusChanged.connect(self.onGetDataFromUrl)
        # self.connect.start()
        return ""

    def fillTableWidgetSystemUsers(self, list, tableWidget):
        """Fills table with units"""
        tableWidget.setHorizontalHeaderLabels([self.tr("Sysid"), self.tr("Name"), self.tr("Status"), self.tr("Search id"), self.tr("Region"), self.tr("Arrive until")])
        tableWidget.setColumnWidth(1, 300);
        # Reads list and populate the table
        lines = list.split("\n")
        lines = self.filterSystemUsers(lines)
        tableWidget.setRowCount(len(lines))
        # tableWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        # Loops via users
        i = 0
        for line in lines:
            if line != "":
                cols = line.split(";")
                j = 0
                for col in cols:
                    if j == 2:
                        col = self.getStatusName(col)
                        tableWidget.setItem(i, j, QTableWidgetItem(col))
                    else:
                        tableWidget.setItem(i, j, QTableWidgetItem(str(col)))
                    j = j + 1
                # tableWidget.selectRow(i)
                i = i + 1

    def filterSystemUsers(self, lines):
        linesFiltered = []
        for line in lines:
            if line != "":
                cols = line.split(";")
                if self.filterSystemUsersByStatus(cols[2]):
                    if self.filterSystemUserByTime(cols[5]):
                        if self.filterSystemUsersByArea(cols[4]):
                            linesFiltered.append(line)
                #         else:
                #             print("Filtered out: " + line)
                #     else:
                #         print("Filtered out: " + line)
                # else:
                #     print("Filtered out: " + line)
        return linesFiltered

    def filterSystemUsersByStatus(self, value):
        if self.comboBoxStatus.currentIndex() == 0:
            return True
        else:
            return self.getStatusCode(self.comboBoxStatus.currentText()) == value

    def filterSystemUserByTime(self, value):
        if self.comboBoxTime.currentIndex() == 0:
            return True
        if self.comboBoxTime.currentIndex() == 1:
            allowedValues = ["60m"]
            return value in allowedValues
        if self.comboBoxTime.currentIndex() == 2:
            allowedValues = ["60m", "120m"]
            return value in allowedValues
        if self.comboBoxTime.currentIndex() == 3:
            allowedValues = ["60m", "120m", "180m"]
            return value in allowedValues
        if self.comboBoxTime.currentIndex() == 4:
            allowedValues = ["60m", "120m", "180m", "240m"]
            return value in allowedValues
        if self.comboBoxTime.currentIndex() == 5:
            allowedValues = ["60m", "120m", "180m", "240m", "300m"]
            return value in allowedValues
        if self.comboBoxTime.currentIndex() == 6:
            allowedValues = ["gt300m"]
            return value in allowedValues

    def filterSystemUsersByArea(self, value):
        if self.comboBoxArea.currentIndex() == 0:
            return True
        if self.comboBoxArea.currentIndex() == 1:
            return value == self.getRegion()
        if self.comboBoxArea.currentIndex() == 2:
            return value in self.getRegionAndSurrounding()

    def fillTableWidgetFriction(self, fileName, tableWidget):
        """Fills table with units"""
        tableWidget.setHorizontalHeaderLabels([self.tr("ID"), self.tr("Time per 10m"), self.tr("KOD"), self.tr("Description"), self.tr("Note")])
        tableWidget.setColumnWidth(3, 300);
        tableWidget.setColumnWidth(4, 300);
        # Reads CSV and populate the table
        with open(self.pluginPath + fileName, "r") as fileInput:
            i = 0
            for row in csv.reader(fileInput, delimiter=';'):
                j = 0
                unicode_row = row
                # yield row.encode('utf-8')
                for field in unicode_row:
                    tableWidget.setItem(i, j, QTableWidgetItem(field))
                    j = j + 1
                i = i + 1

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

    def fillTableWidgetUnitsTimes(self, fileName, tableWidget):
        """Fills table with units"""
        tableWidget.setVerticalHeaderLabels(
            [self.tr("empty easy no cover"),
             self.tr("empty easy with cover"),
             self.tr("empty difficult"),
             self.tr("cover easy to pass"),
             self.tr("cover difficult to pass"),
             self.tr("intravilan"),
             self.tr("parks and playgrounds with people"),
             self.tr("parks and playgrounds without people"),
             self.tr("water body"),
             self.tr("other")])
        tableWidget.setHorizontalHeaderLabels(self.unitsLabels)
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

    def fillTableWidgetDistance(self, fileName, tableWidget, type):
        """Fills table with distances"""
        tableWidget.setHorizontalHeaderLabels(['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '95%'])
        tableWidget.setVerticalHeaderLabels(
            [self.tr("Child 1-3"), self.tr("Child 4-6"), self.tr("Child 7-12"), self.tr("Child 13-15"), self.tr("Despondent"), self.tr("Psychical illness"), self.tr("Retarded"),
             self.tr("Alzheimer"), self.tr("Turist"), self.tr("Demention")])

        currentPath = self.pluginPath
        if type == "user":
            currentPath = self.pluginPath + "/../../../qgis_patrac_settings"

        # Reads CSV and populate the table
        with open(currentPath + fileName, "r") as fileInput:
            i = 0
            for row in csv.reader(fileInput, delimiter=','):
                j = 0
                for field in row:
                    tableWidget.setItem(i, j, QTableWidgetItem(field))
                    j = j + 1
                i = i + 1

    def fillCmbArea(self):
        self.comboBoxArea.addItem(self.tr("All"))
        self.comboBoxArea.addItem(self.tr("Region"))
        self.comboBoxArea.addItem(self.tr("Region and surrounding"))

    def fillCmbTime(self):
        self.comboBoxTime.addItem(self.tr("All"))
        self.comboBoxTime.addItem("< 1h")
        self.comboBoxTime.addItem("< 2h")
        self.comboBoxTime.addItem("< 3h")
        self.comboBoxTime.addItem("< 4h")
        self.comboBoxTime.addItem("< 5h")
        self.comboBoxTime.addItem("> 5h")

    def fillCmbStatus(self):
        self.comboBoxStatus.addItem(self.tr("All"))
        self.comboBoxStatus.addItem(self.tr("waiting"))
        self.comboBoxStatus.addItem(self.tr("call on duty"))
        self.comboBoxStatus.addItem(self.tr("ready to go"))
        self.comboBoxStatus.addItem(self.tr("can not arrive"))
        self.comboBoxStatus.addItem(self.tr("call to come"))
        self.comboBoxStatus.addItem(self.tr("on duty"))

    def getStatusName(self, status):
        if status == "waiting":
            return self.tr("waiting")
        if status == "callonduty":
            return self.tr("call on duty")
        if status == "readytogo":
            return self.tr("ready to go")
        if status == "cannotarrive":
            return self.tr("can not arrive")
        if status == "calltocome":
            return self.tr("call to come")
        if status == "onduty":
            return self.tr("on duty")

    def getStatusCode(self, status):
        if status == self.tr("waiting"):
            return "waiting"
        if status == self.tr("call on duty"):
            return "callonduty"
        if status == self.tr("ready to go"):
            return "readytogo"
        if status == self.tr("can not arrive"):
            return "cannotarrive"
        if status == self.tr("call to come"):
            return "calltocome"
        if status == self.tr("on duty"):
            return "onduty"

    def accept(self):
        """Writes settings to the appropriate files"""

        if not hasattr(self, 'searchID'):
            # Wrong project
            return

        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"

        # Distances are fixed, but the user can change user distances, so only the one table is written
        f = open(settingsPath + '/grass/distancesUser.txt', 'w')
        for i in range(0, 10):
            for j in range(0, 9):
                value = self.tableWidgetDistancesUser.item(i, j).text()
                if value == '':
                    value = '0'
                if j == 0:
                    f.write(value)
                else:
                    f.write("," + value)
            f.write("\n")
        f.close()

        # Units can be changes so the units.txt is written
        # f = io.open(settingsPath + '/grass/units.txt', 'w', encoding='utf-8')
        # for i in range(0, 7):
        #     for j in range(0, 2):
        #         value = self.tableWidgetUnits.item(i, j).text()
        #         if value == '':
        #             value = '0'
        #         unicodeValue = self.getUnicode(value)
        #         if j == 0:
        #             f.write(unicodeValue)
        #         else:
        #             f.write(";" + unicodeValue)
        #     f.write("\n")
        # f.close()

        # Units can be changes so the units.txt is written
        f = io.open(settingsPath + '/grass/units_times.csv', 'w', encoding='utf-8')
        for i in range(0, 10):
            for j in range(0, 7):
                value = self.tableWidgetUnitsTimes.item(i, j).text()
                if value == '':
                    value = '0'
                unicodeValue = self.getUnicode(value)
                if j == 0:
                    f.write(unicodeValue)
                else:
                    f.write(";" + unicodeValue)
            f.write("\n")
        f.close()

        # According to the selected distances combo is copied one of the distances file to the distances.txt
        if self.comboBoxDistance.currentIndex() == 0:
            shutil.copy(self.pluginPath + "/grass/distancesLSOM.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 1:
            shutil.copy(self.pluginPath + "/grass/distancesHill.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 2:
            shutil.copy(self.pluginPath + "/grass/distancesUK.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 3:
            settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
            shutil.copy(settingsPath + "/grass/distancesUser.txt", self.pluginPath + "/grass/distances.txt")

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        f = open(DATAPATH + '/config/searchid.txt', 'w')
        f.write(self.lineEditSearchID.text())
        f.close()

        f = open(DATAPATH + '/config/weightlimit.txt', 'w')
        f.write(self.lineEditWeightLimit.text())
        f.close()

        f = open(self.settingsPath + '/grass/weightlimit.txt', 'w')
        f.write(self.lineEditWeightLimit.text())
        f.close()

        f = open(DATAPATH + '/config/radialsettings.txt', 'w')
        if self.checkBoxRadial.isChecked():
            f.write("1")
        else:
            f.write("0")
        f.close()

        f = open(self.settingsPath + '/grass/radialsettings.txt', 'w')
        if self.checkBoxRadial.isChecked():
            f.write("1")
        else:
            f.write("0")
        f.close()

        self.writeConfig()

        QMessageBox.information(self.main.iface.mainWindow(), self.tr("INFO"), self.tr("Settings has been updated"))

    def ifNumberGetString(self, number):
        """Converts number to string"""
        convertedStr = number
        if isinstance(number, int) or \
                isinstance(number, float):
            convertedStr = str(number)
        return convertedStr

    def getUnicode(self, strOrUnicode, encoding='utf-8'):
        """Converts string to unicode"""
        strOrUnicode = self.ifNumberGetString(strOrUnicode)
        if isinstance(strOrUnicode, str):
            return strOrUnicode
        return str(strOrUnicode, encoding, errors='ignore')

    def getString(self, strOrUnicode, encoding='utf-8'):
        """Converts unicode to string"""
        strOrUnicode = self.ifNumberGetString(strOrUnicode)
        if isinstance(strOrUnicode, str):
            return strOrUnicode.encode(encoding)
        return strOrUnicode

    def showQrCode(self):
        if hasattr(self, 'searchID') and self.searchID != "":
            url = "https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=" + self.searchID
            webbrowser.get().open(url)
            # webbrowser.open(url)

    def recalculateFriction(self):
        QMessageBox.information(None, self.tr("Not available"), self.tr("The function is not implemented"))
        return
        f = open(self.pluginPath + '/grass/friction_user.rules', 'w')
        for i in range(0, 56):
            cat = self.tableWidgetFriction.item(i, 0).text()
            value = self.tableWidgetFriction.item(i, 1).text()
            if value == '':
                value = 'null'
            f.write(cat + " = " + value + "\n")
        f.write("* = null\n")
        f.write("end\n")
        f.close()

        self.parent.setCursor(Qt.WaitCursor)
        self.setCursor(Qt.WaitCursor)

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_friction.bat", DATAPATH, self.pluginPath))
            p.wait()
        else:
            p = subprocess.Popen(
                ('bash', self.pluginPath + "/grass/run_friction.sh", DATAPATH, self.pluginPath))
            p.wait()

        QMessageBox.information(None, self.tr("Recalculated"), self.tr("The friction has been recalculated"))
        self.setCursor(Qt.ArrowCursor)
        self.parent.setCursor(Qt.ArrowCursor)
