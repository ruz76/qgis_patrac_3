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
from qgis.PyQt import QtWidgets,QtGui, uic
from qgis.core import *
from qgis.gui import *
from qgis import utils
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
import webbrowser
import urllib.request, urllib.error, urllib.parse
import socket
import requests, json
import tempfile
import zipfile
from shutil import copy
import sched, time

#If on windows
try:
    import win32api
except:
    QgsMessageLog.logMessage("Linux - no win api", "Patrac")


# import qrcode

class PeriodicScheduler(object):
    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def setup(self, interval, action, actionargs=()):
        action(*actionargs)
        self.scheduler.enter(interval, 1, self.setup,
                             (interval, action, actionargs))

    def run(self):
        self.scheduler.run()


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
        self.systemid = open(self.settingsPath + "/config/systemid.txt", 'r').read()

        self.main = parent
        self.iface = self.main.iface
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.comboBoxDistance.addItem("LSOM")
        self.comboBoxDistance.addItem("Hill")
        self.comboBoxDistance.addItem("UK")
        self.comboBoxDistance.addItem("Vlastní")
        self.comboBoxFriction.addItem("Pastorková")
        self.comboBoxFriction.addItem("Vlastní")
        # Fills tables with distances
        self.fillTableWidgetDistance("/grass/distancesLSOM.txt", self.tableWidgetDistancesLSOM, "system")
        self.fillTableWidgetDistance("/grass/distancesHill.txt", self.tableWidgetDistancesHill, "system")
        self.fillTableWidgetDistance("/grass/distancesUK.txt", self.tableWidgetDistancesUK, "system")
        self.fillTableWidgetDistance("/grass/distancesUser.txt", self.tableWidgetDistancesUser, "user")
        # Fills table with friction values
        self.fillTableWidgetFriction("/grass/friction.csv", self.tableWidgetFriction)

        # Fills table with search units
        self.fillTableWidgetUnits("/grass/units.txt", self.tableWidgetUnits)

        # Fills values for weights of the points
        if os.path.isfile(DATAPATH + "/config/weightlimit.txt"):
            self.fillLineEdit(DATAPATH + "/config/weightlimit.txt", self.lineEditWeightLimit)
        else:
            self.fillLineEdit(self.settingsPath + "/grass/weightlimit.txt", self.lineEditWeightLimit)

        self.pushButtonHds.clicked.connect(self.testHds)
        self.pushButtonUpdatePlugin.clicked.connect(self.updatePlugin)
        self.pushButtonUpdateData.clicked.connect(self.updateData)

        self.pushButtonGetSystemUsers.clicked.connect(self.refreshSystemUsers)
        self.comboBoxArea.currentIndexChanged.connect(self.refreshSystemUsers)
        self.comboBoxTime.currentIndexChanged.connect(self.refreshSystemUsers)
        self.comboBoxStatus.currentIndexChanged.connect(self.refreshSystemUsers)
        self.pushButtonCallOnDuty.clicked.connect(self.callOnDuty)
        self.pushButtonJoinSearch.clicked.connect(self.callToJoin)
        self.pushButtonPutToSleep.clicked.connect(self.putToSleep)
        self.pushButtonShowHelp.clicked.connect(self.showHelp)
        self.buttonBox.accepted.connect(self.accept)

        # Psovodi HS
        self.pushButtonCreateIncident.clicked.connect(self.createIncident)
        self.pushButtonIncidentEdit.clicked.connect(self.incidentEdit)
        self.incidentId = None

        # set up empty sheduler
        self.pushButtonGetSystemUsersShedule.clicked.connect(self.refreshSystemUsersSetSheduler)
        self.periodic_scheduler = None

        self.pushButtonShowQrCode.clicked.connect(self.showQrCode)

        self.pushButtonSaveStyle.clicked.connect(self.saveStyle)

        # fill filtering combos
        self.fillCmbArea()
        self.fillCmbTime()
        self.fillCmbStatus()
        self.fillCentroid()

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
        QMessageBox.information(None, "NOT IMPLEMENTED", "Tato funkce není zatím implementována")
        # if self.periodic_scheduler is None:
        #    INTERVAL = 5  # every second
        #    periodic_scheduler = PeriodicScheduler()
        #    periodic_scheduler.setup(INTERVAL, self.refreshSystemUsers)  # it executes the event just once
        #    periodic_scheduler.run()  # it starts the scheduler

    def fillCentroid(self):
        lon, lat = self.getCentroid()
        if lon == 0 and lat == 0:
            return
        else:
            self.lineEditLongitude.setText(str(lon))
            self.lineEditLattitude.setText(str(lat))

    def getCentroid(self):
        center = self.iface.mapCanvas().center()
        srs = self.iface.mapCanvas().mapSettings().destinationCrs()
        source_crs = QgsCoordinateReferenceSystem(srs)
        dest_crs = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        xyWGS = transform.transform(center.x(), center.y())
        return xyWGS

    def createIncident(self):
        if len(self.lineEditTitle.text()) < 5:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte Název")
            return
        if len(self.lineEditText.text()) < 5:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte Popis")
            return
        if len(self.lineEditAccessKey.text()) < 24:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte API Key")
            return
        if len(self.lineEditServerUrl.text()) < 50:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte URL serveru")
            return
        if len(self.lineEditPhone.text()) < 9:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte váš telefon")
            return

        distance = 500
        try:
            distance = int(self.lineEditDistance.text())
        except ValueError:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte vzdálenost v kilometrech")
            return
        lon = 0
        try:
            lon = float(self.lineEditLongitude.text())
        except ValueError:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte longitute ve formátu 18.14556")
            return
        lat = 0
        try:
            lat = float(self.lineEditLattitude.text())
        except ValueError:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte lattitude ve formátu 48.54556")
            return

        url = self.lineEditServerUrl.text() + "?"
        url += "accessKey=" + self.lineEditAccessKey.text()
        url += "&lat=" + str(lat)
        url += "&lng=" + str(lon)
        url += "&title=" + urllib.parse.quote(self.lineEditTitle.text())
        url += "&text=" + urllib.parse.quote(self.lineEditText.text())
        url += "&searchRadius=" + str(distance)
        url += "&userPhone=" + str(self.lineEditPhone.text())
        url += "&createIncident=1"
        data = self.getDataFromUrl(url, 5)
        if len(data) > 20:
            self.fillSystemUsersHS(data)
        else:
            QMessageBox.information(self.main.iface.mainWindow(), "Chyba", "Nepodařilo se založit incident")

    def fillSystemUsersHS(self, data):
        msg = "Nepodařilo se načíst data o psovodech"
        hsdata = None
        try:
            hsdata = json.loads(data)
        except:
            QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)
            return

        if hsdata["ok"] == 1:
            # print(hsdata["users"])
            self.incidentId = hsdata["IncidentId"]
            self.tableWidgetSystemUsersHS.setHorizontalHeaderLabels(["Jméno", "Telefon"])
            self.tableWidgetSystemUsersHS.setColumnWidth(1, 300);
            self.tableWidgetSystemUsersHS.setRowCount(len(hsdata["users"]))
            i = 0
            for user in hsdata["users"]:
                self.tableWidgetSystemUsersHS.setItem(i, 0, QTableWidgetItem(user["name"]))
                self.tableWidgetSystemUsersHS.setItem(i, 1, QTableWidgetItem(user["phone"]))
                i += 1
        else:
            QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)

    def incidentEdit(self):
        msg = "Nepodařilo se získat přístup"
        if len(self.lineEditUsername.text()) < 3:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte uživatele")
            return
        if len(self.lineEditPassword.text()) < 5:
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný vstup", "Zadejte heslo")
            return

        url = "https://www.horskasluzba.cz/cz/hscr-sbook-login?"
        url += "L=" + urllib.parse.quote(self.lineEditUsername.text())
        url += "H=" + urllib.parse.quote(self.lineEditPassword.text())
        data = self.getDataFromUrl(url, 5)
        if len(data) > 5:
            hsdata = None
            try:
                hsdata = json.loads(data)
            except:
                QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)
                return
            if hsdata["ok"] == 1:
                urlToOpen = "https://www.horskasluzba.cz/cz/kniha-sluzeb/vyzvy?"
                urlToOpen += "action=show-record"
                urlToOpen += "&record_id=" + str(self.incidentId)
                urlToOpen += "&t=" + hsdata["token"]
                webbrowser.get().open(urlToOpen)
            else:
                QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)
        else:
            QMessageBox.information(self.main.iface.mainWindow(), "Chyba", msg)

    def updateSettings(self):
        self.showSearchId()
        self.showPath()
        self.fillCentroid()
        if self.parent.projectname != "":
            self.lineEditTitle.setText(self.parent.projectname)
        if self.parent.projectdesc != "":
            self.lineEditText.setText(self.parent.projectdesc)

    def showSearchId(self):
        # Fills textEdit with SearchID
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if DATAPATH != "" and QFileInfo(DATAPATH + "/config/searchid.txt").exists():
            self.searchID = open(DATAPATH + "/config/searchid.txt", 'r').read()
            self.lineEditSearchID.setText(self.searchID)
        else:
            msg = "Nemohu najít konfigurační soubor s identifikátorem pátrání. Některé funkce nebudou dostupné."
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný projekt", msg)

    def showPath(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        self.labelPath.setText("Cesta k projektu: " + prjfi.absolutePath())

    def testHds(self):
        self.parent.setCursor(Qt.WaitCursor)
        self.main.testHds()
        self.parent.setCursor(Qt.ArrowCursor)

    def updatePlugin(self):
        msg = "Aktualizace se nově provádí přes menu Zásuvné moduly"
        QMessageBox.information(self.main.iface.mainWindow(), "Nová verze", msg)
        return

    def updateData(self):
        msg = "Funkce není v této verzi podporována"
        QMessageBox.information(self.main.iface.mainWindow(), "Nedostupné", msg)
        return
        QMessageBox.information(None, "INFO", "Tato funkce není zatím implementována plně. Aktualizuji šablonu a fixuji sklady.")
        currentVersion = self.getCurrentVersion()
        self.downloadTemplate(currentVersion)

    def getPatracDataPath(self):
        DATAPATH = ''
        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'C:/patracdata/'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'D:/patracdata/'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'E:/patracdata/'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/'

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
            self.iface.messageBar().pushMessage("Error", "Can not find web browser to open help", level=Qgis.Critical)

    def getQrCode(self):
        img = qrcode.make('Some data here')

    def fillLineEdit(self, filePath, lineEdit):
        content = open(filePath, 'r').read()
        lineEdit.setText(content)

    def getRegion(self):
        # TODO
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if DATAPATH != "" and QFileInfo(DATAPATH + "/config/region.txt").exists():
            region = open(DATAPATH + "/config/region.txt", 'r').read()
            return region.upper()
        else:
            msg = "Nemohu najít konfigurační soubor s regionem pátrání. Některé funkce nebudou dostupné."
            QMessageBox.information(self.main.iface.mainWindow(), "Chybný projekt", msg)
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
        self.setStatus("callonduty", self.searchID)

    def callToJoin(self):
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
        response = None
        idsSelected = self.getSelectedSystemUsers()
        statuses = self.getSelectedSystemUsersStatuses()
        ids = self.removeSleepingSystemUsers(idsSelected, statuses)
        if len(ids) != len(idsSelected):
            QMessageBox.information(None, "INFO:",
                                    "Někteří vybraní uživatelé jsou ve stavu sleeping nebo released. Je nutné počkat až se sami probudí.")
        if ids == "":
            QMessageBox.information(None, "INFO:", "Nevybrali jste žádného uživatele, kterého by šlo oslovit.")
            return
        # Connects to the server to call the selected users on duty
        try:
            response = urllib.request.urlopen(
                self.serverUrl + 'users.php?operation=changestatus&id=' + self.systemid + '&status_to=' + status + '&ids=' + ids + "&searchid=" + searchid,
                None, 5)
            changed = str(response.read())
            self.refreshSystemUsers()
            QgsMessageLog.logMessage(changed, "Patrac")
            return changed
        except urllib.error.URLError:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except urllib.error.HTTPError:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except socket.timeout:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""

    def refreshSystemUsers(self):
        list = self.getSystemUsers()
        if list != "":
            self.fillTableWidgetSystemUsers(list, self.tableWidgetSystemUsers)

    def getSystemUsers(self):
        return self.getDataFromUrl(self.serverUrl + 'users.php?operation=getsystemusers&id=' + self.systemid, 5)

    def getDataFromUrl(self, url, timeout):
        response = None
        # Connects to the server to obtain list of users based on list of locations
        try:
            response = urllib.request.urlopen(url, None, timeout)
            system_users = response.read().decode('utf-8')
            return system_users
        except urllib.error.URLError:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except urllib.error.HTTPError:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except socket.timeout:
            self.iface.messageBar().pushMessage("Error", "Nepodařilo se spojit se serverem.", level=Qgis.Warning)
            # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""

    def fillTableWidgetSystemUsers(self, list, tableWidget):
        """Fills table with units"""
        tableWidget.setHorizontalHeaderLabels(["Sysid", "Jméno", "Status", "Id pátrání", "Kraj", "Příjezd do"])
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
        tableWidget.setHorizontalHeaderLabels(["ID", "Čas (10m)", "KOD", "Popis", "Poznámka"])
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
        tableWidget.setHorizontalHeaderLabels(["Počet", "Poznámka"])
        tableWidget.setVerticalHeaderLabels(
            ["Pes", "Člověk do rojnice", "Kůň", "Čtyřkolka", "Vrtulník", "Potápěč", "Jiné"])
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

    def fillTableWidgetDistance(self, fileName, tableWidget, type):
        """Fills table with distances"""
        tableWidget.setHorizontalHeaderLabels(['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '95%'])
        tableWidget.setVerticalHeaderLabels(
            ["Dítě 1-3", "Dítě 4-6", "Dítě 7-12", "Dítě 13-15", "Deprese", "Psychická nemoc", "Retardovaný",
             "Alzheimer", "Turista", "Demence"])

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
        self.comboBoxArea.addItem("Všichni")
        self.comboBoxArea.addItem("Kraj")
        self.comboBoxArea.addItem("Kraj a okolí")

    def fillCmbTime(self):
        self.comboBoxTime.addItem("Všichni")
        self.comboBoxTime.addItem("< 1h")
        self.comboBoxTime.addItem("< 2h")
        self.comboBoxTime.addItem("< 3h")
        self.comboBoxTime.addItem("< 4h")
        self.comboBoxTime.addItem("< 5h")
        self.comboBoxTime.addItem("> 5h")

    def fillCmbStatus(self):
        self.comboBoxStatus.addItem("Všichni")
        self.comboBoxStatus.addItem("čeká")
        self.comboBoxStatus.addItem("pozván")
        self.comboBoxStatus.addItem("k dispozici")
        self.comboBoxStatus.addItem("nemohu přijet")
        self.comboBoxStatus.addItem("vyzván k příjezdu")
        self.comboBoxStatus.addItem("na cestě nebo v pátrání")

    def getStatusName(self, status):
        if status == "waiting":
            return "čeká"
        if status == "callonduty":
            return "pozván"
        if status == "readytogo":
            return "k dispozici"
        if status == "cannotarrive":
            return "nemohu přijet"
        if status == "calltocome":
            return "vyzván k příjezdu"
        if status == "onduty":
            return "na cestě nebo v pátrání"

    def getStatusCode(self, status):
        if status == "čeká":
            return "waiting"
        if status == "pozván":
            return "callonduty"
        if status == "k dispozici":
            return "readytogo"
        if status == "nemohu přijet":
            return "cannotarrive"
        if status == "vyzván k příjezdu":
            return "calltocome"
        if status == "na cestě nebo v pátrání":
            return "onduty"

    def accept(self):
        """Writes settings to the appropriate files"""
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
        f = io.open(settingsPath + '/grass/units.txt', 'w', encoding='utf-8')
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
        url = "https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=" + self.searchID
        webbrowser.get().open(url)
        #webbrowser.open(url)

