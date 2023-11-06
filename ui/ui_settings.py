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
import tempfile
from zipfile import ZipFile
from time import gmtime, strftime

# import qrcode

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings.ui'))


class Ui_Settings(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for settings"""

    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Settings, self).__init__(parent)
        self.parent = parent
        self.widget = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../patrac_settings"
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.config = None
        self.readConfig()
        self.unitsLabels = [self.tr("Handler"), self.tr("Searcher"), self.tr("Rider"), self.tr("Car"), self.tr("Drone"), self.tr("Diver"), self.tr("Other")]

        self.main = parent
        self.iface = self.main.iface
        self.serverUrl = 'http://sarops.info/patrac/'
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

        try:
            if os.path.isfile(DATAPATH + "/config/radialsettings.txt"):
                with open(DATAPATH + "/config/radialsettings.txt") as rs:
                    if rs.read().rstrip() == '1':
                        self.checkBoxRadial.setChecked(True)
                    else:
                        self.checkBoxRadial.setChecked(False)
            else:
                with open(self.settingsPath + "/grass/radialsettings.txt") as rs:
                    if rs.read().rstrip() == '1':
                        self.checkBoxRadial.setChecked(True)
                    else:
                        self.checkBoxRadial.setChecked(False)
        except:
            print("ERROR CHBX")
            self.checkBoxRadial.setChecked(False)

        self.pushButtonUpdateData.clicked.connect(self.updateData)
        # self.buttonBox.accepted.connect(self.accept)
        self.periodic_scheduler = None
        self.pushButtonSaveStyle.clicked.connect(self.saveStyle)
        self.lineEditAccessKey.editingFinished.connect(self.lineEditAccessKeyEditingFinished)

        self.fillDataCmbList()

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

    def fillDataCmbList(self):
        regions = ["jc", "jm", "ka", "kh", "lb", "ms", "ol", "pa", "pl", "st", "us", "vy", "zl"]
        for region in regions:
            self.comboBoxData.addItem(region)

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
            name = open(self.settingsPath + "/styles/sektory_group.txt", 'r').read()
            layer.saveNamedStyle(self.settingsPath + '/styles/sectors_' + name + '.qml')

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
        self.showPath()
        self.fillHSConfig()


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


    def downloadResource(self, source, target, start, end):
        print(source)
        print(target)
        self.progressBar.setValue(start)
        try:
            if os.path.exists(target):
                os.remove(target)
            url = source
            http = urllib3.PoolManager()
            response = http.request('GET', url, preload_content=False)
            content_length = response.headers['Content-Length']
            total_size = int(content_length)
            downloaded = 0
            CHUNK = 256 * 10240
            with open(target, 'wb') as fp:
                while True:
                    chunk = response.read(CHUNK)
                    downloaded += len(chunk)
                    if not chunk:
                        break
                    fp.write(chunk)
            response.release_conn()
            self.progressBar.setValue(end)
        except Exception as e:
            print(e)
            QMessageBox.information(None, self.tr("ERROR"), self.tr("Can not connect to the server"))

    def downloadData(self, start, end):
        try:
            self.textEditHds.append(QApplication.translate("Patrac", 'Downloading data ...', None))
            QtWidgets.QApplication.processEvents()
            tmpdirname = tempfile.mkdtemp()
            self.downloadResource(self.serverUrl + "qgis3/data/" + self.comboBoxData.currentText() + "/list.json", os.path.join(tmpdirname, 'list.json'), 30, 31)
            if os.path.exists(os.path.join(tmpdirname, 'list.json')):
                with open(os.path.join(tmpdirname, 'list.json')) as l:
                    data = json.load(l)
                    count = len(data)
                    size = round((end - start) / count)
                    i = 1
                    for item in data:
                        res = list(item.keys())[0]
                        self.downloadResource(self.serverUrl + "qgis3/data/" + self.comboBoxData.currentText() + "/" + res, os.path.join(tmpdirname, res), start, start + size)
                        self.textEditHds.append(QApplication.translate("Patrac", 'Downloaded chunk ', None) + str(i) + '/' + str(count))
                        QtWidgets.QApplication.processEvents()
                        start += size
                        i += 1
                return [tmpdirname, data]
            else:
                return None
        except:
            return None

    def mergeDownloaded(self, items, source, target):
        self.textEditHds.append(QApplication.translate("Patrac", 'Merging chunks ...', None))
        QtWidgets.QApplication.processEvents()
        for item in items:
            with open(os.path.join(source, item), 'rb') as input:
                data = input.read()
            with open(target, 'ab') as output:
                output.write(data)

    def backupData(self, source, target, start, end):
        try:
            self.textEditHds.append(QApplication.translate("Patrac", 'Backing up the data ...', None))
            self.textEditHds.append(QApplication.translate("Patrac", 'Calculating files ...', None))
            # shutil.make_archive(target, 'zip', source)
            count = 0
            for dirname, subdirs, files in os.walk(source):
                for filename in files:
                    count += 1

            step = (end - start) / count
            progress = start
            zf = ZipFile(target, "w")
            for dirname, subdirs, files in os.walk(source):
                zf.write(dirname)
                for filename in files:
                    self.textEditHds.append(QApplication.translate("Patrac", 'Archiving ', None) + filename + ' ...')
                    QtWidgets.QApplication.processEvents()
                    zf.write(os.path.join(dirname, filename))
                    progress += step
                    self.progressBar.setValue(round(progress))
            zf.close()

            self.progressBar.setValue(end)
            return True
        except:
            self.textEditHds.append(QApplication.translate("Patrac", '!!! ERROR in update of the data. Exiting. !!!', None))
            return False

    def unzipData(self, source, target):
        self.textEditHds.append(QApplication.translate("Patrac", 'Unzipping data ...', None))
        QtWidgets.QApplication.processEvents()
        try:
            kraj_zip = ZipFile(source)
            kraj_zip.extractall(target)
        except:
            QMessageBox.information(self.main.iface.mainWindow(), self.tr("Can not extract"), self.tr("Can not extract"))

    def updateData(self):
        # msg = self.tr("Function is not supported")
        # QMessageBox.information(self.main.iface.mainWindow(), self.tr("Not available"), msg)
        self.progressBar.setValue(5)
        if not os.path.exists(self.config['data_path'] + 'kraje/backups'):
            os.makedirs(self.config['data_path'] + 'kraje/backups', exist_ok=True)
        dir_path = self.config['data_path'] + 'kraje/' + self.comboBoxData.currentText()
        zip_file_name = os.path.join(self.config['data_path'] + 'kraje/backups', self.comboBoxData.currentText() + '_' + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + '.zip')
        if os.path.exists(dir_path):
            backupResults = self.backupData(dir_path, zip_file_name, 5, 30)
        if os.path.exists(dir_path) and (not backupResults or not os.path.exists(zip_file_name)):
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "The backup of the data was not created. Can not continue with data update.", None))
            return
        self.progressBar.setValue(30)
        resources = self.downloadData(30, 70)
        if resources is None:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "The data was not downloaded. Can not continue with data update.", None))
            return
        self.progressBar.setValue(70)
        self.mergeDownloaded(resources[1], resources[0], os.path.join(resources[0], 'data.zip'))
        self.progressBar.setValue(85)
        try:
            self.unzipData(os.path.join(resources[0], 'data.zip'), self.config['data_path'] + 'kraje/' + self.comboBoxData.currentText() + '/')
        except:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "The data were corrupted. Can not continue with data update.", None))
            return
        self.progressBar.setValue(100)
        self.textEditHds.append(QApplication.translate("Patrac", 'Finished. The data has been updated.', None))
        QtWidgets.QApplication.processEvents()
        return

    def showHelp(self):
        try:
            webbrowser.get().open(
                "file://" + self.config['data_path'] + "doc/index.html")
        except (webbrowser.Error):
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not find web browser to open help"), level=Qgis.Critical)

    def fillLineEdit(self, filePath, lineEdit):
        content = open(filePath, 'r').read()
        lineEdit.setText(content)


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
        # Reads CSV and populate the table
        with open(self.settingsPath + fileName, "r") as fileInput:
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
        # Reads CSV and populate the table
        with open(self.settingsPath + fileName, "r") as fileInput:
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
            currentPath = self.pluginPath + "/../../../patrac_settings"

        # Reads CSV and populate the table
        with open(currentPath + fileName, "r") as fileInput:
            i = 0
            for row in csv.reader(fileInput, delimiter=','):
                j = 0
                for field in row:
                    tableWidget.setItem(i, j, QTableWidgetItem(field))
                    j = j + 1
                i = i + 1

    # def copySettingsInfoProject(self):
    #     prjfi = QFileInfo(QgsProject.instance().fileName())
    #     DATAPATH = prjfi.absolutePath()
    #     if os.path.exists(DATAPATH + "/pracovni/sektory_group.shp"):
    #         shutil.copy(self.settingsPath + "/grass/" + "weightlimit.txt", DATAPATH + '/config/weightlimit.txt')
    #         shutil.copy(self.settingsPath + "/grass/" + "radialsettings.txt", DATAPATH + '/config/radialsettings.txt')

    def accept(self):
        """Writes settings to the appropriate files"""

        # Distances are fixed, but the user can change user distances, so only the one table is written
        f = open(self.settingsPath + '/grass/distancesUser.txt', 'w')
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
        f = io.open(self.settingsPath + '/grass/units_times.csv', 'w', encoding='utf-8')
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
            shutil.copy(self.settingsPath + "/grass/distancesUser.txt", self.pluginPath + "/grass/distances.txt")

        DATAPATH = self.widget.Utils.getDataPath()
        if os.path.exists(DATAPATH + '/config/'):
            with open(self.widget.Utils.getDataPath() + '/config/weightlimit.txt', 'w') as f:
                f.write(self.lineEditWeightLimit.text())

            with open(DATAPATH + '/config/radialsettings.txt', 'w') as f:
                if self.checkBoxRadial.isChecked():
                    f.write("1")
                else:
                    f.write("0")

        self.writeConfig()
        # self.copySettingsInfoProject()

        QMessageBox.information(self.main.iface.mainWindow(), self.tr("INFO"), self.tr("Settings has been updated"))

        self.close()

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
