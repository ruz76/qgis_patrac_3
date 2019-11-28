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
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.main = parent
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.comboBoxDistance.addItem("LSOM")
        self.comboBoxDistance.addItem("Hill")
        self.comboBoxDistance.addItem("UK")
        self.comboBoxDistance.addItem("Vlastní")
        self.comboBoxFriction.addItem("Pastorková")
        self.comboBoxFriction.addItem("Vlastní")
        # Fills tables with distances
        self.fillTableWidgetDistance("/grass/distancesLSOM.txt", self.tableWidgetDistancesLSOM)
        self.fillTableWidgetDistance("/grass/distancesHill.txt", self.tableWidgetDistancesHill)
        self.fillTableWidgetDistance("/grass/distancesUK.txt", self.tableWidgetDistancesUK)
        self.fillTableWidgetDistance("/grass/distancesUser.txt", self.tableWidgetDistancesUser)
        # Fills table with friction values
        self.fillTableWidgetFriction("/grass/friction.csv", self.tableWidgetFriction)
        # Fills table with search units
        self.fillTableWidgetUnits("/grass/units.txt", self.tableWidgetUnits)
        # Fills values for weights of the points
        self.fillLineEdit("/grass/weightlimit.txt", self.lineEditWeightLimit)
        self.pushButtonHds.clicked.connect(self.testHds)
        self.pushButtonUpdatePlugin.clicked.connect(self.updatePlugin)
        self.pushButtonUpdateData.clicked.connect(self.updateData)
        self.pushButtonGetRasters.clicked.connect(self.getRasters)
        self.pushButtonGetSystemUsers.clicked.connect(self.refreshSystemUsers)
        self.comboBoxArea.currentIndexChanged.connect(self.refreshSystemUsers)
        self.comboBoxTime.currentIndexChanged.connect(self.refreshSystemUsers)
        self.comboBoxStatus.currentIndexChanged.connect(self.refreshSystemUsers)
        self.pushButtonCallOnDuty.clicked.connect(self.callOnDuty)
        self.pushButtonJoinSearch.clicked.connect(self.callToJoin)
        self.pushButtonPutToSleep.clicked.connect(self.putToSleep)
        self.pushButtonShowHelp.clicked.connect(self.showHelp)
        self.buttonBox.accepted.connect(self.accept)

        # set up empty sheduler
        self.pushButtonGetSystemUsersShedule.clicked.connect(self.refreshSystemUsersSetSheduler)
        self.periodic_scheduler = None

        self.pushButtonShowQrCode.clicked.connect(self.showQrCode)

        # fill filtering combos
        self.fillCmbArea()
        self.fillCmbTime()
        self.fillCmbStatus()

    def refreshSystemUsersSetSheduler(self):
        QMessageBox.information(None, "NOT IMPLEMENTED", "Tato funkce není zatím implementována")
        # if self.periodic_scheduler is None:
        #    INTERVAL = 5  # every second
        #    periodic_scheduler = PeriodicScheduler()
        #    periodic_scheduler.setup(INTERVAL, self.refreshSystemUsers)  # it executes the event just once
        #    periodic_scheduler.run()  # it starts the scheduler

    def updateSettings(self):
        self.showSearchId()
        self.showPath()

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
        self.main.testHds()

    def updatePlugin(self):
        currentVersion = self.getCurrentVersion()
        installedVersion = self.getInstalledVersion()
        if currentVersion != "" and currentVersion != installedVersion:
            msg = "K dispozici je nová verze. Chcete ji instalovat?"
            install = QMessageBox.question(self.main.iface.mainWindow(), "Nová verze", msg, QMessageBox.Yes,
                                           QMessageBox.No)
            if install == QMessageBox.Yes:
                self.downloadPlugin(currentVersion)
                msg = "Nová verze byla nainstalována. Dojde k obnovení pluginu do výchozí pozice."
                QMessageBox.information(self.main.iface.mainWindow(), "Nová verze", msg)
                utils.reloadPlugin('qgis_patrac');
                self.done(0)
        else:
            msg = "Máte aktuální verzi: " + currentVersion
            QMessageBox.information(self.main.iface.mainWindow(), "Nová verze", msg)
        # shutil.copy("/tmp/aboutdialog.py", self.pluginPath + "/aboutdialog.py")

    def getCurrentVersion(self):
        content = self.getDataFromUrl("https://raw.githubusercontent.com/ruz76/qgis_patrac/master/RELEASE", 5)
        return content.strip()

    def getInstalledVersion(self):
        fname = self.pluginPath + "/RELEASE"
        with open(fname) as f:
            content = f.readline().strip()
            return content

    def downloadZip(self, url, path):
        os.umask(0o002)
        try:
            req = urllib.request.urlopen(url)
            totalSize = 16800000
            if req.info().getheader('Content-Length') is not None:
                totalSize = int(req.info().getheader('Content-Length').strip())
            downloaded = 0
            CHUNK = 256 * 1024
            self.progressBarUpdatePlugin.setMinimum(0)
            self.progressBarUpdatePlugin.setMaximum(totalSize)
            zipTemp = tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False)
            zipTempName = zipTemp.name
            zipTemp.seek(0)
            with open(zipTempName, 'wb') as fp:
                while True:
                    chunk = req.read(CHUNK)
                    downloaded += len(chunk)
                    self.show()
                    self.progressBarUpdatePlugin.setValue(downloaded)
                    if not chunk:
                        break
                    fp.write(chunk)
            pluginZip = zipfile.ZipFile(zipTemp)
            pluginZip.extractall(path)
            zipTemp.close()
        except urllib.error.HTTPError:
            QMessageBox.information(self.main.iface.mainWindow(), "HTTP Error", "Nemohu stáhnout plugin z: " + url)
        except urllib.error.URLError:
            QMessageBox.information(self.main.iface.mainWindow(), "HTTP Error", "Nemohu stáhnout plugin z: " + url)

    def downloadPlugin(self, release):
        pluginPath = self.pluginPath
        pluginsPath = os.path.abspath(os.path.join(pluginPath, ".."))
        # url = "https://github.com/ruz76/qgis_patrac/archive/" + release + ".zip"
        url = "http://gisak.vsb.cz/patrac/qgis/" + release + ".zip"
        self.downloadZip(url, pluginsPath)
        self.copySettingsFiles(pluginPath, pluginsPath + "/qgis_patrac-" + release[1:])
        qgisPath = os.path.abspath(os.path.join(pluginsPath, "../.."))
        shutil.move(pluginPath, qgisPath + "/cache/qgis_patrac_" + str(time.time()))
        shutil.move(pluginsPath + "/qgis_patrac-" + release[1:], pluginPath)

    def copySettingsFiles(self, sourceDirectory, targetDirectory):
        copy(sourceDirectory + "/config/systemid.txt", targetDirectory + "/config/systemid.txt")
        copy(sourceDirectory + "/grass/distances.txt", targetDirectory + "/grass/distances.txt")
        copy(sourceDirectory + "/grass/radialsettings.txt", targetDirectory + "/grass/radialsettings.txt")
        copy(sourceDirectory + "/grass/units.txt", targetDirectory + "/grass/units.txt")
        copy(sourceDirectory + "/grass/weightlimit.txt", targetDirectory + "/grass/weightlimit.txt")
        copy(sourceDirectory + "/xslt/saxon9he.jar", targetDirectory + "/xslt/saxon9he.jar")

    def downloadTemplate(self, release):
        patracdata = ""
        if sys.platform.startswith('win'):
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            for drive in drives:
                if os.path.exists(os.path.join(drive, "patracdata")):
                    patracdata = os.path.join(drive, "patracdata")
        else:
            if os.path.exists("/data/patracdata/"):
                patracdata = "/data/patracdata/"

        if patracdata == "":
            QMessageBox.information(self.main.iface.mainWindow(), "Data Error",
                                    "Nemohu najít adresář patracdata. Aktualizace se nezdařila. Kontaktujte podporu.")

        url = "http://gisak.vsb.cz/patrac/qgis/templates." + release + ".zip"
        self.downloadZip(url, os.path.join(patracdata, "kraje"))

        if not os.path.exists(os.path.join(patracdata, 'archives')):
            os.makedirs(os.path.join(patracdata, 'archives'))

        shutil.move(os.path.join(patracdata, "kraje", "templates"),
                    os.path.join(patracdata, 'archives') + "/templates_" + str(time.time()))
        shutil.move(os.path.join(patracdata, "kraje") + "/templates-" + release[1:],
                    os.path.join(patracdata, "kraje", "templates"))

        self.fixDatastore(patracdata)

    def fixDatastore(self, patracdata):
        kraje = ("us", "st", "pl", "kh", "hp", "pa", "vy", "jc", "jm", "zl", "ol", "lb", "ms", "ka")
        for kraj in kraje:
            if os.path.exists(os.path.join(patracdata, "kraje",  kraj)):
                if sys.platform.startswith('win'):
                    QMessageBox.information(None, "INFO", "Upravuji datový sklad: " + os.path.join(patracdata, "kraje", kraj))
                    p = subprocess.Popen((
                        self.pluginPath + "/grass/run_fix_datastore.bat", os.path.join(patracdata, "kraje", kraj),
                        self.pluginPath))
                    p.wait()
                else:
                    p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_fix_datastore.sh",
                                          os.path.join(patracdata, "kraje", kraj), self.pluginPath))
                    p.wait()

    def updateData(self):
        QMessageBox.information(None, "INFO", "Tato funkce není zatím implementována plně. Aktualizuji šablonu a fixuji sklady.")
        currentVersion = self.getCurrentVersion()
        self.downloadTemplate(currentVersion)

    def showHelp(self):
        webbrowser.open("file://" + self.pluginPath + "/doc/index.html")

    def getQrCode(self):
        img = qrcode.make('Some data here')

    def fillLineEdit(self, fileName, lineEdit):
        content = open(self.pluginPath + fileName, 'r').read()
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
            # TODO change hardcoded value for id
            response = urllib.request.urlopen(
                self.serverUrl + 'users.php?operation=changestatus&id=pcr007&status_to=' + status + '&ids=' + ids + "&searchid=" + searchid,
                None, 5)
            changed = response.read()
            self.refreshSystemUsers()
            QgsMessageLog.logMessage(changed, "Patrac")
            return changed
        except urllib.error.URLError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except urllib.error.HTTPError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except socket.timeout:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""

    def refreshSystemUsers(self):
        list = self.getSystemUsers()
        #if list != "":
            #self.fillTableWidgetSystemUsers(list, self.tableWidgetSystemUsers)

    def getSystemUsers(self):
        # TODO change hardcoded value for id to value from configuration
        return self.getDataFromUrl(self.serverUrl + 'users.php?operation=getsystemusers&id=pcr007', 5)

    def getDataFromUrl(self, url, timeout):
        response = None
        # Connects to the server to obtain list of users based on list of locations
        try:
            response = urllib.request.urlopen(url, None, timeout)
            system_users = response.read()
            return system_users
        except urllib.error.URLError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except urllib.error.HTTPError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
            return ""
        except socket.timeout:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
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
                        tableWidget.setItem(i, j, QTableWidgetItem(str(col).decode('utf8')))
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
        tableWidget.setColumnWidth(1, 600);
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

    def fillTableWidgetDistance(self, fileName, tableWidget):
        """Fills table with distances"""
        tableWidget.setHorizontalHeaderLabels(['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '95%'])
        tableWidget.setVerticalHeaderLabels(
            ["Dítě 1-3", "Dítě 4-6", "Dítě 7-12", "Dítě 13-15", "Deprese", "Psychická nemoc", "Retardovaný",
             "Alzheimer", "Turista", "Demence"])
        # Reads CSV and populate the table
        with open(self.pluginPath + fileName, "r") as fileInput:
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
        # Distances are fixed, but the user can change user distances, so only the one table is written
        f = open(self.pluginPath + '/grass/distancesUser.txt', 'w')
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
        f = io.open(self.pluginPath + '/grass/units.txt', 'w', encoding='utf-8')
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
            shutil.copy(self.pluginPath + "/grass/distancesUser.txt", self.pluginPath + "/grass/distances.txt")

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        f = open(DATAPATH + '/config/searchid.txt', 'w')
        f.write(self.lineEditSearchID.text())
        f.close()

        f = open(DATAPATH + '/config/weightlimit.txt', 'w')
        f.write(self.lineEditWeightLimit.text())
        f.close()

        f = open(DATAPATH + '/config/radialsettings.txt', 'w')
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

    def getRasters(self):
        self.copyRasters("128")
        self.copyRasters("64")
        self.copyRasters("32")
        self.copyRasters("16")
        self.copyRasters("8")
        self.copyRasters("4")

    def copyRasters(self, level):
        path_to = self.lineEditZpmTo.text()
        path_from = self.lineEditZpmFrom.text()
        copy(path_from + level + "K/metadata.csv", path_to + "ZPM_" + level + "tis/")
        with open(path_to + level + ".name") as fp:
            line = fp.readline()
            while line:
                line = line.rstrip()
                copy(path_from + level + "K/" + line.upper() + ".tif", path_to + "ZPM_" + level + "tis/")
                copy(path_from + level + "K/" + line.upper() + ".wld", path_to + "ZPM_" + level + "tis/")
                line = fp.readline()

    def showQrCode(self):
        url = "https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=" + self.searchID
        webbrowser.open(url)

