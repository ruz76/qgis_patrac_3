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

import os, sys
import subprocess
from glob import glob
from glob import iglob
import shutil
from shutil import copyfile
import csv
from qgis.PyQt import QtWidgets,QtGui, uic

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.core import *
from qgis.gui import *

from random import randint
from datetime import datetime
from datetime import timedelta
from dateutil import tz
from dateutil import parser
from dateutil.tz import tzutc, tzlocal
import fnmatch
from array import array
import getpass
from osgeo import ogr

win32api_exists = False
#If on windows
try:
    import win32api
    win32api_exists = True
except:
    if sys.platform.startswith('win'):
        QgsMessageLog.logMessage("Windows with no win api", "Patrac")
    else:
        QgsMessageLog.logMessage("Linux - no win api", "Patrac")

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpx.ui'))

class Ui_Gpx(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Gpx, self).__init__(parent)
        self.setupUi(self)
        self.pluginPath = pluginPath
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.path = '/tmp/GARMIN'
        self.DATAPATH = DATAPATH
        self.buttonBoxAll.accepted.connect(self.acceptAll)
        self.buttonBoxLast.accepted.connect(self.acceptLast)
        self.buttonBoxAll.rejected.connect(self.rejectAll)
        self.buttonBoxLast.rejected.connect(self.rejectLast)
        self.status = 'EMPTY'
        self.fillListViewTracks()
        today = datetime.today()
        #Set name for output file when groupped GPX together
        #name is based on day and time
        self.lineEditNameAll.setText(today.strftime('den%d_cas%H_%M'))
        self.lineEditNameLast.setText(today.strftime('den%d_cas%H_%M'))
        self.Utils = parent.Utils

    def fillTableWidgetSectors(self, fileName, tableWidget):
        """Fills table with search sectors
           The table is used for cut of GPX according to time.
        """
        tableWidget.setHorizontalHeaderLabels(['ID', self.tr('From'), self.tr('To')])
        with open(self.DATAPATH + fileName, "r") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=','):    
                j=0
                tableWidget.insertRow(tableWidget.rowCount())
                for field in row:
                    tableWidget.setItem(i, j, QTableWidgetItem(field))
                    j=j+1
                i=i+1
        #tableWidget.rowCount = 3

    def checkDrives(self, drives):
        drives_out = []
        for drive in drives:
            if os.path.exists(drive + "Garmin/GPX"):
                drives_out.append(drive)
        return drives_out

    def getDrive(self):
        """Shows list of Windows drives"""
        if win32api_exists:
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
        else:
            letters = "DEFGHIJKLMNOPQRSTUVWXYZ"
            drives = [letters[i] + ":/" for i in range(len(letters))]
        drives = self.checkDrives(drives)
        item, ok = QInputDialog.getItem(self, self.tr("select input dialog"),
                                        self.tr("list of drives"), drives, 0, False)
        if ok and item:
            return item
        else:
            return None

    def getDriveLinux(self):
        """Shows list of user drives"""
        username = getpass.getuser()
        drives = []
        if not os.path.isdir('/media/' + username + '/'):
            QgsMessageLog.logMessage(self.tr("Not found ") + '/media/' + username + '/. ' + self.tr('Necessary for test.'), "Patrac")
            return None
        for dirname in os.listdir('/media/' + username + '/'):
            drives.append('/media/' + username + '/' + dirname + '/')
        item, ok = QInputDialog.getItem(self, self.tr("select input dialog"),
                                        self.tr("list of drives"), drives, 0, False)
        if ok and item:
            return item
        else:
            return None

    def fillListViewTracks(self):
        """Fills list with tracks"""
        files = glob(self.DATAPATH + '/search/temp/*')
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        #If Windows
        if sys.platform.startswith('win'):
            #Get drive from user select
            drive = self.getDrive()
            #If not selected than C:, that should be always present
            if drive is None:
                QgsMessageLog.logMessage(self.tr("Not found any disk. Will not search for data."), "Patrac")
                return
            self.path = drive[:-1] + '/'
        else:
            drive = self.getDriveLinux()
            if drive is None:
                QgsMessageLog.logMessage(self.tr("Not found any disk. Will not search for data."), "Patrac")
                return
            self.path = drive

        i = 0
        for root, dirnames, filenames in os.walk(self.path):
            for f in fnmatch.filter(filenames, '*.gpx'):
                shutil.copyfile(os.path.join(root, f), self.DATAPATH + '/search/temp/' + str(i) + '.gpx')
                ds = ogr.Open(self.DATAPATH + '/search/temp/' + str(i) + '.gpx')
                with open(self.DATAPATH + '/search/temp/list.csv', "a") as listFile:
                    if not ds is None:
                        layer = ds.GetLayer(4)
                        QgsMessageLog.logMessage(str(layer.GetFeatureCount()), "Patrac")
                        if layer.GetFeatureCount() > 0:
                            feature = layer.GetFeature(0)
                            if feature.GetField('time') is not None:
                                listFile.write(feature.GetField('time') + ";")
                            else:
                                listFile.write("TNK" + ";")
                            feature = layer.GetFeature(layer.GetFeatureCount() - 1)
                            if feature.GetField('time') is not None:
                                listFile.write(feature.GetField('time') + ";")
                            else:
                                listFile.write("TNK" + ";")
                            listFile.write(f + "\n")
                        else:
                            listFile.write(";\n")
                        ds.Destroy()
                    else:
                        listFile.write(";\n")
                i=i+1

        self.fillGpxTracksList()
        self.status = 'FILLED'

    def fillGpxTracksList(self):
        #if some GPX were found
        if os.path.isfile(self.DATAPATH + '/search/temp/list.csv'):
            self.listViewModelAll = QStandardItemModel()
            self.listViewModelLast = QStandardItemModel()
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            #Loop via GPX tracks
            with open(self.DATAPATH + '/search/temp/list.csv') as fp:
                for cnt, line in enumerate(fp):
                    track = 'Track ' + str(cnt) + ': '
                    items = line.split(';')
                    start = ''
                    end = ''
                    #This is some workatound, becaouse the list can contain more than one time information for each track
                    if len(items[0]) > 30:
                        items2 = items[0].split(' ')
                        start = items2[0]
                    else:
                        start = items[0]

                    if len(items[1]) > 30:
                        items2 = items[1].split(' ')
                        end = items2[len(items2) - 1]
                    else:
                        end = items[1]

                    if len(start) > 10 and len(end) > 10:
                        #Convert to local time zone from UTC
                        start_local = self.iso_time_to_local(start)
                        end_local = self.iso_time_to_local(end)
                        end_date = datetime.strptime(end_local, "%Y-%m-%d %H:%M")
                        track += '(' + start_local + ' <-> ' + end_local + ') (' + items[2].rstrip("\n") + ')'
                        item = QStandardItem(track)
                        item.setCheckable(True)
                        self.listViewModelAll.appendRow(item)
                        past_date = datetime.now()-timedelta(hours=24)
                        if end_date > past_date:
                            item_last = QStandardItem(track)
                            item_last.setCheckable(True)
                            self.listViewModelLast.appendRow(item_last)
                    elif start == 'TNK' or end == "TNK":
                        track += self.tr("No Time Information") + ' (' + items[2].rstrip("\n") + ')'
                        item = QStandardItem(track)
                        item.setCheckable(True)
                        self.listViewModelAll.appendRow(item)
                    else:
                        # We do not show everything
                        item = QStandardItem(self.tr("Another Type of GPX"))
                        item.setCheckable(False)
                        self.listViewModelAll.appendRow(item)

            self.listViewTracksAll.setModel(self.listViewModelAll)
            self.listViewTracksLast.setModel(self.listViewModelLast)
        else:
            QgsMessageLog.logMessage(self.tr("No records found") + ":", "Patrac")

    def iso_time_to_local(self, iso):
        """COnverts UTC to local time zone"""
        try:
            when = parser.parse(iso)
            local = when.astimezone(tzlocal())
            local_str = local.strftime("%Y-%m-%d %H:%M")
            return local_str
        except:
            return self.tr("TNK")

    def processTracks(self, lineEditCurrent, listViewModelCurrent):
        SECTOR = lineEditCurrent.text()
        if not os.path.exists(self.DATAPATH + '/search/gpx/' + SECTOR):
            os.makedirs(self.DATAPATH + '/search/gpx/' + SECTOR)

        i = 0
        while listViewModelCurrent.item(i):
            if listViewModelCurrent.item(i).checkState() == Qt.Checked:
                track_id = listViewModelCurrent.item(i).text().split(":")[0][6:]
                result = self.loadTrack(track_id, SECTOR)
                if result:
                    listViewModelCurrent.item(i).setText(listViewModelCurrent.item(i).text() + " -> " +  self.tr("Track loaded"))
                else:
                    listViewModelCurrent.item(i).setText(listViewModelCurrent.item(i).text() + " -> !!!" + self.tr("Problem with loading track") + "!!!")
            i += 1

        QMessageBox.information(None, self.tr("INFO"), self.tr("Loading tracks finished."))

    def loadTrack(self, track_id, dir_name):
        shutil.copyfile(self.DATAPATH + '/search/temp/' + track_id + '.gpx', self.DATAPATH + '/search/gpx/' + dir_name + '/' + track_id + '.gpx')
        vector = QgsVectorLayer(self.DATAPATH + '/search/gpx/' + dir_name + '/' + track_id + '.gpx' + '|layername=tracks', dir_name + '_track_' + track_id, 'ogr')
        if not vector.isValid():
            QgsMessageLog.logMessage("Layer " + self.DATAPATH + '/search/gpx/' + dir_name + '/' + track_id + '.gpx' + '|layername=tracks' + " failed to load!", "Patrac")
            return False
        else:
            if vector.featureCount() > 0:
                print(self.Utils.getSettingsPath())
                vector.loadNamedStyle(self.Utils.getSettingsPath() + '/styles/patraci_lines.qml')
                QgsProject.instance().addMapLayer(vector, False)
                root = QgsProject.instance().layerTreeRoot()
                sektory_current_gpx = root.findGroup(dir_name)
                if sektory_current_gpx is None:
                    sektory_current_gpx = root.insertGroup(0, dir_name)
                sektory_current_gpx.addLayer(vector)
                sektory_current_gpx.setExpanded(False)
                return True
            else:
                QMessageBox.information(None, self.tr("INFO"), self.tr("There are not any tracks in the GPX."))
                return False

    def acceptAll(self):
        if not hasattr(self, 'listViewModelAll'):
            return
        self.processTracks(self.lineEditNameAll, self.listViewModelAll)

    def acceptLast(self):
        if not hasattr(self, 'listViewModelLast'):
            return
        self.processTracks(self.lineEditNameLast, self.listViewModelLast)

    def rejectAll(self):
        self.close()

    def rejectLast(self):
        self.close()
