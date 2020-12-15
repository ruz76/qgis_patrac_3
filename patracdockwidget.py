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
# The sliders and layer transparency are based on https://github.com/alexbruy/raster-transparency
# ******************************************************************************

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import QSettings

from qgis.core import *
from qgis.gui import *

from .ui.ui_patracdockwidgetbase import Ui_PatracDockWidget
from .ui.ui_settings import Ui_Settings
from .ui.ui_gpx import Ui_Gpx
from .ui.ui_message import Ui_Message
from .ui.ui_coords import Ui_Coords
from .ui.ui_point_tool import PointMapTool
from .ui.ui_point_tool_lat_lon import PointMapToolLatLon
from .ui.ui_progress_tool import ProgressMapTool
from .ui.ui_percent import Ui_Percent
from .ui.ui_units import Ui_Units
from .ui.ui_handlers import Ui_Handlers
from .ui.ui_person import Ui_Person

from .main.printing import Printing
from .main.project import ZPM_Raster, Project
from .main.area import Area
from .main.utils import Utils
from .main.sectors import Sectors
from .main.hds import Hds
from .main.styles import Styles

from os import path

import os, sys, subprocess, time, math, socket
import urllib.parse

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime

import csv, io, webbrowser, filecmp, uuid, random, getpass, json

from .connect.connect import *

win32api_exists = False

# If on windows
try:
    import win32api
    win32api_exists = True
except:
    if sys.platform.startswith('win'):
        QgsMessageLog.logMessage("Windows with no win api", "Patrac")
    else:
        QgsMessageLog.logMessage("Linux - no win api", "Patrac")


class PatracDockWidget(QDockWidget, Ui_PatracDockWidget, object):
    def __init__(self, plugin):

        self.plugin = plugin
        self.iface = self.plugin.iface
        self.canvas = self.plugin.iface.mapCanvas()
        self.maxVal = 100
        self.minVal = 0
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.currentStep = 1
        self.projectname = ""
        self.projectdesc = ""

        userPluginPath = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/qgis_patrac"

        if QFileInfo(userPluginPath).exists():
            self.pluginPath = userPluginPath
        else:
            self.pluginPath = systemPluginPath

        # QUICKFIX:
        # self.pluginPath = "/usr/share/qgis/python/plugins/qgis_patrac"
        self.pluginPath = path.dirname(__file__)
        self.settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        self.systemid = open(self.settingsPath + "/config/systemid.txt", 'r').read().rstrip("\n")

        QDockWidget.__init__(self, None)
        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Button GetArea
        self.btnGetArea.clicked.connect(self.runExpertGetArea)

        # Sliders
        self.sliderStart.valueChanged.connect(self.__updateSpinStart)
        self.spinStart.valueChanged.connect(self.__updateSliderStart)
        self.sliderEnd.valueChanged.connect(self.__updateSpinEnd)
        self.spinEnd.valueChanged.connect(self.__updateSliderEnd)

        # Button of places management
        self.tbtnDefinePlaces.clicked.connect(self.definePlaces)
        self.tbtnAddPlaces.clicked.connect(self.setAddFeatureForPlaces)
        # Button of GetSectors
        self.tbtnGetSectors.clicked.connect(self.runExpertGetSectors)

        self.tbtnRecalculateSectors.clicked.connect(self.recalculateSectorsExpert)
        self.tbtnExportSectors.clicked.connect(self.exportSectors)
        self.tbtnReportExportSectors.clicked.connect(self.runExpertReportExportSectors)
        self.tbtnShowSettings.clicked.connect(self.showSettings)
        self.tbtnExtendRegion.clicked.connect(self.extendRegion)
        self.tbtnImportPaths.clicked.connect(self.showImportGpx)
        # self.tbtnShowSearchers.clicked.connect(self.showPeopleSimulation)
        self.tbtnShowSearchers.clicked.connect(self.showPeople)
        self.tbtnShowSearchersTracks.clicked.connect(self.showPeopleTracks)
        self.tbtnShowMessage.clicked.connect(self.showMessage)

        self.tbtnInsertFinal.clicked.connect(self.insertFinal)

        self.setStepsConnection()

        # Help show
        self.helpShow.clicked.connect(self.showHelp)

        self.currentTool = self.iface.mapCanvas().mapTool()
        self.personType = 1

        self.Utils = Utils(self)
        self.Project = Project(self)
        self.Printing = Printing(self)
        self.Area = Area(self)
        self.Sectors = Sectors(self)
        self.Hds = Hds(self)

        # Dialogs and tools are defined here
        self.settingsdlg = Ui_Settings(self.pluginPath, self)
        self.coordsdlg = Ui_Coords(self.plugin.iface.mapCanvas())
        self.pointtool = PointMapTool(self.plugin.iface.mapCanvas(), self)
        self.pointtoollatlon = PointMapToolLatLon(self.plugin.iface.mapCanvas(), self)
        self.progresstool = ProgressMapTool(self.plugin.iface.mapCanvas(), self.plugin.iface)
        self.percentdlg = Ui_Percent()
        self.unitsdlg = Ui_Units(self.pluginPath, self)
        self.handlersdlg = Ui_Handlers(self.pluginPath, self)
        self.persondlg = Ui_Person(self.pluginPath, self)

        self.Styles = Styles(self)
        self.sectorsUniqueStyle.clicked.connect(self.setSectorsUniqueValuesStyle)
        self.guideStep6ShowSectorsByType.clicked.connect(self.setSectorsUniqueValuesStyle)
        self.sectorsSingleStyle.clicked.connect(self.setSectorsSingleValuesStyle)
        self.chkShowLabels.clicked.connect(self.setSectorsShowLabels)
        self.sectorsProgressStyle.clicked.connect(self.setSectorsProgressStyle)
        self.sectorsUnitsStyle.clicked.connect(self.setSectorsUnitsStyle)
        self.sectorsUnitsRecommendedStyle.clicked.connect(self.setSectorsUnitsRecommendedStyle)
        self.guideStep6ShowSectorsBySuggestedUnits.clicked.connect(self.setSectorsUnitsRecommendedStyle)

        # self.sectorsProgress.clicked.connect(self.setSectorsProgress)
        self.sectorsProgressStateNotStarted.clicked.connect(self.setSectorsProgress)
        self.sectorsProgressStateStarted.clicked.connect(self.setSectorsProgress)
        self.sectorsProgressType.activated.connect(self.setSectorsProgress)
        self.sectorsProgressStateFinished.clicked.connect(self.setSectorsProgress)
        self.sectorsProgressStateRisk.clicked.connect(self.setSectorsProgress)

        self.sectorsProgressAnalyzeType.currentIndexChanged.connect(self.sectorsProgressAnalyzeTypeChanged)
        self.sectorsProgressAnalyzeValue.textChanged.connect(self.sectorsProgressAnalyzeValueChanged)
        self.sectorsProgressAnalyzeNumberOfPersons.textChanged.connect(self.sectorsProgressAnalyzeNumberOfPersonsChanged)
        self.loadBuffers()
        self.sectorsProgressAnalyzeNumberOfPersons.setText("10")

        self.tabWidget.currentChanged.connect(self.onTabChanged)
        # self.setMouseHandler()

        self.tbtnReturnToAddfeature.clicked.connect(self.actionAddFeature)
        self.guideStep5OtherUnits.clicked.connect(self.showUnitsDialog)

        self.tbtnPercent.clicked.connect(self.showPercentDialog)
        self.tbtnUnits.clicked.connect(self.showUnitsDialog)
        self.showHandlers.clicked.connect(self.showHandlersDialog)
        self.tbtnRecalculate.clicked.connect(self.recalculateAll)
        self.printPrepared.clicked.connect(self.showReport)
        self.printUserDefined.clicked.connect(self.actionShowLayoutManager)

        self.tbtnSetPlaceHandlers.clicked.connect(self.insertPlaceHandlers)
        self.tbtnSetPlaceOther.clicked.connect(self.insertPlaceOther)
        self.tbtnUpdateAction.clicked.connect(self.updateActionSettings)
        self.tbtnSetLostPerson.clicked.connect(self.showPersonInfo)

        project = QgsProject.instance()
        project.readProject.connect(self.on_project_change)

        self.loadActionSettings()

    def on_project_change(self):
        # print("PROJECT CHANGE")
        self.loadActionSettings()

    def sayHello(self):
        print("HELLO")

    def setMouseHandler(self):
        self.emitPoint = QgsMapToolEmitPoint(self.canvas)
        QObject.connect(self.emitPoint, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.clickedOnMap)

    def clickedOnMap(self):
        print("JOOO")

    def onTabChanged(self, index):
        # If the tab is activated we activate the tool
        if index == 2:
            self.setSectorsProgress()
        if index == 4:
            self.switchToAnalyse()

    def sectorsProgressAnalyzeNumberOfPersonsChanged(self):
        self.progresstool.setNumberOfSearchers(self.sectorsProgressAnalyzeNumberOfPersons.text())

    def sectorsProgressAnalyzeValueChanged(self):
        self.buffers[self.sectorsProgressAnalyzeType.currentIndex()] = self.sectorsProgressAnalyzeValue.text()
        self.progresstool.setAttribute(-1)
        self.progresstool.setUnit(self.sectorsProgressAnalyzeType.currentIndex())
        self.progresstool.setType(0)
        self.progresstool.setValue(self.sectorsProgressAnalyzeValue.text())

    def sectorsProgressAnalyzeTypeChanged(self):
        self.sectorsProgressAnalyzeValue.setText(self.buffers[self.sectorsProgressAnalyzeType.currentIndex()])
        if self.sectorsProgressAnalyzeType.currentIndex() == 2:
            self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer.setEnabled(True)
        else:
            self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer.setEnabled(False)

    def loadBuffers(self):
        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        self.buffers = []
        with open(settingsPath + "/grass/buffer.csv", "r") as fileInput:
            for row in csv.reader(fileInput, delimiter=';'):
                self.buffers.append(row[1])
                self.sectorsProgressAnalyzeType.addItem(row[0])

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
            self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Can not find web browser to open help", None), level=Qgis.Critical)

    def getPluginPath(self):
        return self.pluginPath

    def setStepsConnection(self):
        # Autocompleter fro search of municipalities
        self.setCompleter(self.guideMunicipalitySearch)
        # self.guideMunicipalitySearch.returnPressed.connect(self.runGuideMunicipalitySearch)

        # Step 1 Next
        self.guideStep1Next.clicked.connect(self.runGuideMunicipalitySearch)

        # Step 2 Next
        self.guideStep2Next.clicked.connect(self.runGuideStep2Next)

        # Step 3 Next
        self.guideStep3Next.clicked.connect(self.runGuideStep3Next)

        # Step 4 Next
        self.guideStep4Next.clicked.connect(self.runGuideStep4Next)

        # Step 5 Next
        self.guideStep5Next.clicked.connect(self.runGuideStep5Next)

        # Step 6 Show Report
        self.guideShowReport.clicked.connect(self.showReport)
        self.guideCopyGpx.clicked.connect(self.copyGpx)

    def runCreateProject(self):
        self.projectname = self.msearch.text()
        self.Project.createProject(self.projectname)

    def runCreateProjectGuide(self, index, version):
        self.projectname = self.municipalities_names[index]
        self.projectdesc = self.guideSearchDescription.text()
        self.Project.createProject(index, self.projectdesc, version)
        self.Utils.createProjectInfo(self.projectname, self.projectdesc, version)

    def updateActionSettings(self):
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                            QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.Utils.updateProjectInfo("coordinatorname", self.coordinatorActionLineEdit.text())
        self.Utils.updateProjectInfo("coordinatortel", self.coordinatorTelActionLineEdit.text())
        self.Utils.updateProjectInfo("placehandlers", self.placeHandlersActionLineEdit.text())
        self.Utils.updateProjectInfo("placeother", self.placeOtherActionLineEdit.text())
        self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Info", None), QApplication.translate("Patrac", "Information updated", None), level=Qgis.Info)

    def loadActionSettings(self):
        project_info = self.Utils.getProjectInfo()
        # print(project_info)
        if project_info is not None:
            self.coordinatorActionLineEdit.setText(project_info["coordinatorname"])
            self.coordinatorTelActionLineEdit.setText(project_info["coordinatortel"])
            self.placeHandlersActionLineEdit.setText(project_info["placehandlers"])
            self.placeOtherActionLineEdit.setText(project_info["placeother"])

    def municipalitySearch(self, textBox):
        """Tries to find municipallity in list and zoom to coordinates of it."""
        try:
            input_name = textBox.text()
            i = 0
            # -1 for just test if the municipality was found
            x = -1
            # loop via list of municipalities
            for m in self.municipalities_names:
                # if the municipality is in the list
                if m == input_name:
                    # get the coords from string
                    items = self.municipalities_coords[i].split(";")
                    x = items[0]
                    y = items[1]
                    break
                i = i + 1
            # if the municipality is not found
            if x == -1:
                QMessageBox.information(self.iface.mainWindow(), QApplication.translate("Patrac", "Wrong municipality", None), QApplication.translate("Patrac", "The municipality has not been found", None))
                return -1
            else:
                # if the municipality has coords
                # self.zoomto(x, y)
                return i
        except (KeyError, IOError):
            QMessageBox.information(self.iface.mainWindow(), QApplication.translate("Patrac", "Wrong municipality", None), QApplication.translate("Patrac", "The municipality has not been found", None))
            return -1
        except IndexError:
            return -1

    def runExpertMunicipalitySearch(self):
        self.municipalitySearch(self.msearch)

    def runGuideMunicipalitySearch(self):
        if not self.guideTestSearch.isChecked() and not self.guideRealSearch.isChecked():
            QMessageBox.information(self.iface.mainWindow(), QApplication.translate("Patrac", "Missing input", None), QApplication.translate("Patrac", "You have to select type of the search", None))
            return

        municipalityindex = self.municipalitySearch(self.guideMunicipalitySearch)

        if municipalityindex < 0:
            return

        # generate project
        version = 0
        if self.guideRealSearch.isChecked():
            version = 1
        self.runCreateProjectGuide(municipalityindex, version)

        self.tabGuideSteps.setCurrentIndex(1)
        self.currentStep = 2
        self.iface.actionPan().trigger()

        self.Styles.setSectorsStyle('single')

    def checkStep(self, nextStep):
        if self.currentStep == nextStep - 1:
            return True
        else:
            reply = QMessageBox.question(self, QApplication.translate("Patrac", 'Step', None),
                                         QApplication.translate("Patrac", 'You skipped the step. Do you want to continue?', None),
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return True
            else:
                return False

    def setAddFeatureForPlaces(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break

        if layer is not None:
            self.iface.setActiveLayer(layer)
            layer.startEditing()

            # set tool to add feature
            self.iface.actionAddFeature().trigger()

    def runGuideStep2Next(self):
        if not self.checkStep(3):
            return

        # run area determination computation
        self.personType = self.guideComboPerson.currentIndex() + 1

        # set mista to editing mode
        self.currentTool = self.iface.mapCanvas().mapTool()

        self.setAddFeatureForPlaces()

        # move to next tab (tab 3)
        self.tabGuideSteps.setCurrentIndex(2)
        self.currentStep = 3

    def saveMistaLayer(self):
        # set tool to save edits
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break

        if not layer is None:
            layer.commitChanges()
            self.iface.actionToggleEditing().trigger()

        return layer

    def runGuideStep3Next(self):
        if not self.checkStep(4):
            return

        layer = self.saveMistaLayer()

        if not layer is None:

            self.Area.getArea()

            # set spin to 70%
            self.__updateSliderEnd(70)

            # move to next tab (tab 4)
            self.tabGuideSteps.setCurrentIndex(3)
            self.currentStep = 4

    def runGuideStep4Next(self):
        if not self.checkStep(5):
            return

        # set percent of visibility
        self.spinStart.setValue(0)
        self.spinEnd.setValue(self.guideSpinEnd.value())
        self.updatePatrac()

        # move to next tab (tab 5)
        self.tabGuideSteps.setCurrentIndex(4)
        self.currentStep = 5

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        if os.path.exists(DATAPATH + "/config/maxtime.txt"):
            self.guideMaxTime.setText(open(DATAPATH + "/config/maxtime.txt", 'r').read())

    def runGuideStep5Next(self):
        if not self.checkStep(6):
            return

        # saves information about available resources
        self.saveUnitsInformation()

        # saves maxtime information
        self.saveMaxTimeInformation()

        # select sectors
        self.runGuideGetSectors()

        # run sectors selection and exports
        self.Sectors.reportExportSectors(False, False)

        # move to next tab (tab 6)
        self.tabGuideSteps.setCurrentIndex(5)
        self.currentStep = 6

    def updateUnitsGuide(self):
        with open(self.settingsPath + "/grass/units.txt", "r") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = row
                # dog
                if i == 0:
                    self.guideDogCount.setText(unicode_row[0])
                # person
                if i == 1:
                    self.guidePersonCount.setText(unicode_row[0])
                # diver
                if i == 5:
                    self.guideDiverCount.setText(unicode_row[0])
                i=i+1

    def recalculateAll(self):
        layer = self.saveMistaLayer()
        if not layer is None:
            self.updateUnitsGuide()
            self.Area.getArea()
            self.runGuideGetSectors()
            self.Sectors.reportExportSectors(False, False)
            self.showReport()
            self.updatePatrac()

    def setPercent(self, percent):
        self.spinStart.setValue(0)
        self.spinEnd.setValue(percent)
        self.guideSpinEnd.setValue(percent)
        self.updatePatrac()

    def showPercentDialog(self):
        self.percentdlg.setParent(self)
        self.percentdlg.exec_()

    def showUnitsDialog(self):
        self.unitsdlg.updateTable()
        self.unitsdlg.exec_()

    def exportSectors(self):
        self.Sectors.exportSectors()

    def showReport(self):
        self.setCursor(Qt.WaitCursor)

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "No probability layer. Can not continue.", None));
            return

        transparencyList = []
        transparencyList.extend(self.generateTransparencyList(0, 100))
        # layer.setCacheImage(None)
        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
        self.plugin.iface.mapCanvas().refresh()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "No probability layer. Can not continue.", None));
            return

        # exports overall map with all sectors to PDF
        if self.chkGenerateOverallPDF.isChecked():
            srs = self.canvas.mapSettings().destinationCrs()
            current_crs = srs.authid()
            if current_crs == "EPSG:5514":
                self.Printing.exportPDF(layer.extent(), DATAPATH + "/sektory/")
            else:
                srs = self.canvas.mapSettings().destinationCrs()
                crs_src = QgsCoordinateReferenceSystem(5514)
                crs_dest = QgsCoordinateReferenceSystem(srs)
                xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
                extent = xform.transform(layer.extent())
                self.Printing.exportPDF(extent, DATAPATH + "/sektory/")

        # exports map of sectors to PDF
        # if self.chkGeneratePDF.isChecked():
        #    self.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")

        #    provider = layer.dataProvider()
        #    features = provider.getFeatures()
        #    for feature in features:
        #        self.exportPDF(feature.geometry().boundingBox(), DATAPATH + "/sektory/pdf/" + feature['label'] + ".pdf")

        try:
            webbrowser.get().open("file://" + DATAPATH + "/sektory/report.html")
            # webbrowser.get().open("file://" + DATAPATH + "/sektory/report.html")
        except (webbrowser.Error):
            self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Can not find web browser to open report", None), level=Qgis.Critical)

        self.setCursor(Qt.ArrowCursor)

    def copyGpx(self):
        self.Sectors.exportSectors()
        drives = None
        if sys.platform.startswith('win'):
            if win32api_exists:
                drives = win32api.GetLogicalDriveStrings()
                drives = drives.split('\000')[:-1]
            else:
                drives = self.Utils.getDrivesList()
        else:
            username = getpass.getuser()
            drives = []
            for dirname in os.listdir('/media/' + username + '/'):
                drives.append('/media/' + username + '/' + dirname + '/')

        drives_gpx = []
        for drive in drives:
            if os.path.isdir(drive + 'Garmin/GPX'):
                drives_gpx.append(drive)

        if len(drives_gpx) == 1:
            # nice, only one GPX dir is available
            self.copyGpxToPath(drives_gpx[0] + 'Garmin/GPX')

        if len(drives_gpx) == 0:
            # Not Garmin. TODO
            QMessageBox.information(None, QApplication.translate("Patrac", "INFO", None), QApplication.translate("Patrac", "Did not find GPS. You have to copy GPX manually from the report.", None))

        if len(drives_gpx) > 1:
            # We have more than one place with garmin/GPX
            item, ok = QInputDialog.getItem(self, QApplication.translate("Patrac", "select input dialog", None), QApplication.translate("Patrac", "list of drives", None), drives_gpx, 0, False)
            if ok and item:
                self.copyGpxToPath(item + 'Garmin/GPX')

    def copyGpxToPath(self, path):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        time = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
        try:
            copy(DATAPATH + '/sektory/gpx/all.gpx', path + "/sektory_" + time + ".gpx")
        except:
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Can not copy. You have copy it manually from the path" + ": ", None) + DATAPATH + '/sektory/gpx/all.gpx')
        if os.path.isfile(path + "/sektory_" + time + ".gpx"):
            QMessageBox.information(None, QApplication.translate("Patrac", "INFO", None), QApplication.translate("Patrac", "The sectors has been copied into the device" + ": ", None) + path + "/sektory_" + time + ".gpx")
        else:
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Can not copy. You have copy it manually from the path" + ": ", None) + DATAPATH + '/sektory/gpx/all.gpx')

    def saveUnitsInformation(self):
        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        f = io.open(settingsPath + '/grass/units.txt.tmp', 'w', encoding='utf-8')

        with open(settingsPath + "/grass/units.txt", "r") as fileInput:
            i = 0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = row
                # dog
                if i == 0:
                    unicode_row[0] = self.guideDogCount.text()
                # person
                if i == 1:
                    unicode_row[0] = self.guidePersonCount.text()
                # diver
                if i == 5:
                    unicode_row[0] = self.guideDiverCount.text()
                j = 0
                for field in unicode_row:
                    if j == 0:
                        f.write(field)
                    else:
                        f.write(";" + field)
                    j = j + 1
                i = i + 1
                f.write("\n")
        f.close()

        copy(settingsPath + '/grass/units.txt.tmp', settingsPath + "/grass/units.txt")

    def saveMaxTimeInformation(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        if os.path.exists(DATAPATH + '/config'):
            f = io.open(DATAPATH + '/config/maxtime.txt', 'w', encoding='utf-8')
            f.write(self.guideMaxTime.text())
            f.close()

        if os.path.exists(self.pluginPath + "/../../../qgis_patrac_settings/grass"):
            f = io.open(self.pluginPath + "/../../../qgis_patrac_settings/grass/" + 'maxtime.txt', 'w', encoding='utf-8')
            f.write(self.guideMaxTime.text())
            f.close()

    def setCompleter(self, textBox):
        """Sets the autocompleter for municipalitities."""
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        textBox.setCompleter(completer)
        model = QStringListModel()
        completer.setModel(model)
        # sets arrays of municipalities names and coords
        self.municipalities_names = []
        self.municipalities_coords = []
        self.municipalities_regions = []
        # reads list of municipalities from CSV
        with open(self.pluginPath + "/ui/obce_okr_kr_utf8_20180131.csv", "r") as fileInput:
            # with open(self.pluginPath + "/ui/sk_obce_okr_kr_utf8.csv", "r") as fileInput:
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = row
                # sets the name (and province in brackets for iunique identification)
                self.municipalities_names.append(unicode_row[3] + " (" + unicode_row[5] + ")")
                self.municipalities_coords.append(unicode_row[0] + ";" + unicode_row[1])
                self.municipalities_regions.append(unicode_row[6])
        # Sets list of names to model for autocompleter
        model.setStringList(self.municipalities_names)

    def transform(self, cor):
        """Transforms coords to S-JTSK (EPSG:5514)."""
        map_renderer = self.canvas.mapRenderer()
        srs = map_renderer.destinationCrs()
        crs_src = QgsCoordinateReferenceSystem(5514)
        crs_dest = QgsCoordinateReferenceSystem(srs)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        x = int(cor[0])
        y = int(cor[1])
        t_point = xform.transform(QgsPointXY(x, y))
        return t_point

    def check_crs(self):
        """Check if a transformation needs to take place"""
        map_renderer = self.canvas.mapRenderer()
        srs = map_renderer.destinationCrs()
        current_crs = srs.authid()
        return current_crs

    def zoomto(self, x, y):
        """Zooms to coordinates"""
        current_crs = self.check_crs()
        # If the current CRS is not S-JTSK
        if current_crs != "EPSG:5514":
            cor = (x, y)
            # Do the transformation
            point = self.transform(cor)
            self.update_canvas(point)
        else:
            point = (x, y)
            self.update_canvas(point)

    def update_canvas(self, point):
        # Update the canvas and add vertex marker
        x = point[0]
        y = point[1]
        # TODO change scale according to srid
        # This condition is just quick hack for some srids with deegrees and meters
        if y > 100:
            scale = 2500
        else:
            scale = 0.07
        rect = QgsRectangle(float(x) - scale, float(y) - scale, float(x) + scale, float(y) + scale)
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def updatePatrac(self):
        """Changes the transfṕarency of raster"""
        # print("updatePatrac")
        transparencyList = []
        if self.sliderStart.value() != 0:
            transparencyList.extend(self.generateTransparencyList(0, self.sliderStart.value()))

        if self.sliderEnd.value() != self.maxVal:
            transparencyList.extend(self.generateTransparencyList(self.sliderEnd.value(), self.maxVal))

        # update layer transparency
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/distances_costed_cum.tif" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "No probability layer. Please try step 3 again.", None))
            return

        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
        layer.renderer().setOpacity(0.5)
        layer.triggerRepaint()
        self.plugin.iface.mapCanvas().refresh()

    def __updateSpinStart(self, value):
        endValue = self.sliderEnd.value()
        if value >= endValue:
            self.spinStart.setValue(endValue - 1)
            self.sliderStart.setValue(endValue - 1)
            return
        self.spinStart.setValue(value)

        # if not self.chkManualUpdate.isChecked():
        self.updatePatrac()

    def __updateSliderStart(self, value):
        endValue = self.spinEnd.value()
        if value >= endValue:
            self.spinStart.setValue(endValue - 1)
            self.sliderStart.setValue(endValue - 1)
            return
        self.sliderStart.setValue(value)

    def __updateSpinEnd(self, value):
        startValue = self.sliderStart.value()
        if value <= startValue:
            self.spinEnd.setValue(startValue + 1)
            self.sliderEnd.setValue(startValue + 1)
            return
        self.spinEnd.setValue(value)

        # if not self.chkManualUpdate.isChecked():
        self.updatePatrac()

    def __updateSliderEnd(self, value):
        startValue = self.sliderStart.value()
        if value <= startValue:
            self.spinEnd.setValue(startValue + 1)
            self.sliderEnd.setValue(startValue + 1)
            return
        self.sliderEnd.setValue(value)

    def __toggleRefresh(self):
        settings = QSettings("patrac", "Patrac")
        settings.setValue("manualUpdate", self.chkManualUpdate.isChecked())

        if self.chkManualUpdate.isChecked():
            self.btnRefresh.setEnabled(True)
            try:
                self.sliderStart.sliderReleased.disconnect(self.updatePatrac)
                self.sliderEnd.sliderReleased.disconnect(self.updatePatrac)
            except:
                pass
        else:
            self.btnRefresh.setEnabled(False)
            self.sliderStart.sliderReleased.connect(self.updatePatrac)
            self.sliderEnd.sliderReleased.connect(self.updatePatrac)

    def disableOrEnableControls(self, disable):
        self.label.setEnabled(disable)
        self.sliderStart.setEnabled(disable)
        self.spinStart.setEnabled(disable)
        self.label_2.setEnabled(disable)
        self.sliderEnd.setEnabled(disable)
        self.spinEnd.setEnabled(disable)

    def updateSliders(self, maxValue, minValue):
        # self.maxVal = int(maxValue)
        # self.minVal = int(minValue)

        self.maxVal = 100
        self.minVal = 0

        self.spinStart.setMaximum(int(self.maxVal))
        self.spinStart.setMinimum(int(self.minVal))
        self.spinStart.setValue(int(self.minVal))

        self.spinEnd.setMaximum(int(self.maxVal))
        self.spinEnd.setMinimum(int(self.minVal))
        self.spinEnd.setValue(int(self.guideSpinEnd.value()))

        self.sliderStart.setMinimum(int(self.minVal))
        self.sliderStart.setMaximum(int(self.maxVal))
        self.sliderStart.setValue(int(self.minVal))

        self.sliderEnd.setMinimum(int(self.minVal))
        self.sliderEnd.setMaximum(int(self.maxVal))
        self.sliderEnd.setValue(int(self.guideSpinEnd.value()))

    def generateTransparencyList(self, minVal, maxVal):
        trList = []
        tr = QgsRasterTransparency.TransparentSingleValuePixel()
        tr.min = minVal
        tr.max = maxVal
        tr.percentTransparent = 100
        trList.append(tr)
        return trList

    def runExpertGetArea(self):
        self.personType = self.comboPerson.currentIndex() + 1
        self.Area.getArea()

    def runExpertGetSectors(self):
        self.Sectors.getSectors(self.sliderStart.value(), self.sliderEnd.value())

    def runExpertReportExportSectors(self):
        self.Sectors.reportExportSectors(True, True)

    def runGuideGetSectors(self):
        self.Sectors.getSectors(0, self.guideSpinEnd.value())

    def recalculateSectorsExpert(self):
        self.Sectors.recalculateSectors(False, True)

    def splitByLine(self):
        self.Sectors.splitByLine()

    def addVectorsForSplitByLine(self):
        self.Sectors.addVectorsForSplitByLine()

    def extendRegion(self):
        # msg = QApplication.translate("Patrac", "The function is not available. Please create new project.", None)
        # QMessageBox.information(None, QApplication.translate("Patrac", "Not available", None), msg)
        # return
        self.Sectors.extendRegion()

    def showSettings(self):
        """Shows the settings dialog"""
        self.settingsdlg.updateSettings()
        self.settingsdlg.show()

    def showPersonInfo(self):
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return
        """Shows the person info dialog"""
        self.persondlg.setItems()
        self.persondlg.show()

    def showHandlersDialog(self):
        """Shows the settings dialog"""
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.handlersdlg.updateSettings()
        self.handlersdlg.show()

    def showMessage(self):
        """Show the dialog for sending messages"""
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.setCursor(Qt.WaitCursor)
        self.messagedlg = Ui_Message(self.pluginPath, DATAPATH, self)
        self.messagedlg.show()
        self.setCursor(Qt.ArrowCursor)

    def showImportGpx(self):
        """Shows the dialog for import of GPX tracks"""
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.importgpxdlg = Ui_Gpx(self.pluginPath)
        self.importgpxdlg.show()

    def setPointLatLon(self, point, type):
        if type == 0:
            self.Utils.updateProjectInfo("placehandlers_lon", point.x())
            self.Utils.updateProjectInfo("placehandlers_lat", point.y())
        if type == 1:
            self.Utils.updateProjectInfo("placeother_lon", point.x())
            self.Utils.updateProjectInfo("placeother_lat", point.y())

    def setPointLatLonHumanReadable(self, point, type):
        if type == 0:
            self.placeHandlersActionLineEdit.setText(str(point))
        if type == 1:
            self.placeOtherActionLineEdit.setText(str(point))

    def insertPlaceHandlers(self):
        self.pointtoollatlon.setType(0)
        self.plugin.iface.mapCanvas().setMapTool(self.pointtoollatlon)

    def insertPlaceOther(self):
        self.pointtoollatlon.setType(1)
        self.plugin.iface.mapCanvas().setMapTool(self.pointtoollatlon)

    def insertFinal(self):
        """Sets tool to pointtool to be able handle from click to map.
            It is used at the time when the search is finished.
        """
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        with open(self.pluginPath + "/config/lastprojectpath.txt", "w") as f:
            f.write(DATAPATH)

        self.pointtool.setDataPath(DATAPATH)
        self.pointtool.setSearchid(self.getSearchID())
        self.plugin.iface.mapCanvas().setMapTool(self.pointtool)

        self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Info", None), QApplication.translate("Patrac", "Click into the map at the place of finding. If you finishing without finding, click anywhere into map.", None), level=Qgis.Warning, duration=-1)

    def setSectorsProgress(self):
        layer = self.setSectorsProgressPrepare()
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return

        attribute = 3
        type = 1
        unit = 0
        value = 50
        numberOfSearchers = 10
        if self.sectorsProgressStateNotStarted.isChecked() == True:
            attribute = 3
            type = None
        if self.sectorsProgressStateStarted.isChecked() == True:
            attribute = 3
            type = 1
            unit = self.sectorsProgressType.currentIndex()
        if self.sectorsProgressStateFinished.isChecked() == True:
            attribute = 3
            type = 2
        if self.sectorsProgressStateRisk.isChecked() == True:
            attribute = 3
            type = 0

        self.progresstool.setAttribute(attribute)
        self.progresstool.setUnit(unit)
        self.progresstool.setType(type)
        self.progresstool.setLayer(layer)
        self.progresstool.setValue(value)
        self.progresstool.setNumberOfSearchers(numberOfSearchers)
        self.plugin.iface.mapCanvas().setMapTool(self.progresstool)

    def setSectorsProgressPrepare(self):
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.progresstool.setDataPath(DATAPATH)
        self.progresstool.setPluginPath(self.pluginPath)

        return layer

    def switchToAnalyse(self):
        layer = self.setSectorsProgressPrepare()
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return

        attribute = -1
        type = 0
        unit = self.sectorsProgressAnalyzeType.currentIndex()
        value = self.sectorsProgressAnalyzeValue.text()
        numberOfSearchers = self.sectorsProgressAnalyzeNumberOfPersons.text()

        self.progresstool.setAttribute(attribute)
        self.progresstool.setUnit(unit)
        self.progresstool.setType(type)
        self.progresstool.setLayer(layer)
        self.progresstool.setValue(value)
        self.progresstool.setNumberOfSearchers(numberOfSearchers)
        self.plugin.iface.mapCanvas().setMapTool(self.progresstool)

    def actionShowLayoutManager(self):
        self.iface.actionShowLayoutManager().trigger()

    def actionAddFeature(self):
        self.iface.actionAddFeature().trigger()

    def definePlaces(self):
        """Moves the selected point to specified coordinates
            Or converts lines to points
            Or converts polygons to points
        """
        # Check if the project has mista.shp
        if not self.Utils.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        # Get center of the map
        center = self.plugin.canvas.center()
        self.coordsdlg.setCenter(center)
        self.coordsdlg.setWidget(self)
        # self.coordsdlg.setLayer(layer)
        self.coordsdlg.setModal(True)
        # Show dialog with coordinates of the center
        self.coordsdlg.exec_()
        x = None
        y = None

        # If S-JTSk then simply read
        if self.coordsdlg.radioButtonJTSK.isChecked() == True:
            x = self.coordsdlg.lineEditX.text()
            y = self.coordsdlg.lineEditY.text()

        # If WGS then transformation
        if self.coordsdlg.radioButtonWGS.isChecked() == True:
            x = self.coordsdlg.lineEditLon.text()
            y = self.coordsdlg.lineEditLat.text()
            source_crs = QgsCoordinateReferenceSystem(4326)
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            xyJTSK = transform.transform(float(x), float(y))
            x = xyJTSK.x()
            y = xyJTSK.y()

        # If UTM then transformation
        if self.coordsdlg.radioButtonUTM.isChecked() == True:
            x = self.coordsdlg.lineEditUTMX.text()
            y = self.coordsdlg.lineEditUTMY.text()
            source_crs = QgsCoordinateReferenceSystem(32633)
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            xyJTSK = transform.transform(float(x), float(y))
            x = xyJTSK.x()
            y = xyJTSK.y()

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/mista.shp" in lyr.source():
                layer = lyr
                break
        # If we would like to switch to all features
        # provider = layer.dataProvider()
        # provider.getFeatures()
        # Work only with selected features
        features = layer.selectedFeatures()
        layer.startEditing()
        for fet in features:
            geom = fet.geometry()
            pt = geom.asPoint()
            # print str(pt)
            # Moves point to specified coordinates
            fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(x), float(y))))
            layer.updateFeature(fet)
        layer.commitChanges()
        layer.triggerRepaint()

        # Converts lines to points
        if self.coordsdlg.checkBoxLine.isChecked() == True:
            self.convertLinesToPoints()

        # Converts polygons to points
        if self.coordsdlg.checkBoxPolygon.isChecked() == True:
            self.convertPolygonsToPoints()

    def getLinePoints(self, line):
        """Returns point in the center of the line or two points
            First point is center of the line and second is end of the line.
            Two points are returned in a case that line has smer attribuet equal to 1.
        """
        geom = line.geometry()
        lineLength = geom.length()
        point = geom.interpolate(lineLength / 2)
        if line["smer"] == 1:
            points = geom.asPolyline()
            return [point, QgsGeometry.fromPointXY(points[len(points) - 1])]
        else:
            return [point]

    def convertLinesToPoints(self):
        """Converts lines to points
        """
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layerPoint = None
        layerLine = None
        # Reads lines from mista_line layer
        # Writes centroid to mista
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista_linie.shp":
                layerLine = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerLine = layerLine.dataProvider()
        providerPoint = layerPoint.dataProvider()
        # features = layer.selectedFeatures()
        features = providerLine.getFeatures()
        for fet in features:
            points = self.getLinePoints(fet)
            fetPoint = QgsFeature()
            fetPoint.setGeometry(points[0])
            featureid = fet["id"] + 1000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"], fet["vaha"]])
            if len(points) == 2:
                fetPoint2 = QgsFeature()
                fetPoint2.setGeometry(points[1])
                featureid = fet["id"] + 1000
                cas_od_datetime = datetime.strptime(fet["cas_od"], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
                cas_do_datetime = datetime.strptime(fet["cas_do"], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
                fetPoint2.setAttributes([featureid, format(cas_od_datetime, '%Y-%m-%d %H:%M:%S'),
                                         format(cas_do_datetime, '%Y-%m-%d %H:%M:%S'), fet["vaha"]])
                providerPoint.addFeatures([fetPoint, fetPoint2])
            else:
                providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    def convertPolygonsToPoints(self):
        """Converts polygons to points
           Simply creates centroid of polygon.
        """
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layerPoint = None
        layerPolygon = None
        # Reads lines from mista_polygon layer
        # Writes centroid to mista
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista_polygon.shp":
                layerPolygon = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerPolygon = layerPolygon.dataProvider()
        providerPoint = layerPoint.dataProvider()
        # features = layer.selectedFeatures()
        features = providerPolygon.getFeatures()
        for fet in features:
            fetPoint = QgsFeature()
            fetPoint.setGeometry(fet.geometry().centroid())
            featureid = fet["id"] + 2000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"], fet["vaha"]])
            providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    # It does not work
    # I do not know why it does not work
    def movePointJTSK(self, x, y):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        layer.startEditing()
        for fet in features:
            geom = fet.geometry()
            pt = geom.asPoint()
            # print str(pt)
            # print str(x) + " " + str(y)

    def getSearchID(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        searchid = "NONE"
        with open(DATAPATH + '/config/searchid.txt', 'r') as f:
            searchid = f.read()
        return searchid

    def addFeaturePolyLineFromPoints(self, points, cols, end_time, provider):
        fet = QgsFeature()
        # Name and sessionid are on first and second place
        fet.setAttributes([str(cols[0]), str(end_time), str(cols[2]), str(cols[3])])
        # Geometry is on third and fourth places
        if len(points) > 1:
            line = QgsGeometry.fromPolylineXY(points)
            fet.setGeometry(line)
            provider.addFeatures([fet])

    def showPeopleTracks(self):
        """Shows tracks of logged positions in map"""
        # Check if the project has patraci_lines.shp
        if not self.Utils.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        url = self.serverUrl + 'track.php?searchid=' + self.getSearchID()
        if os.path.exists(DATAPATH + "/pracovni/lasttrackcheck.txt"):
            with open(DATAPATH + "/pracovni/lasttrackcheck.txt", "r") as f:
                start_from = f.read()
                url += "&start_from=" + urllib.parse.quote(start_from)

        self.tracks = Connect()
        self.tracks.setUrl(url)
        self.tracks.setTimeout(20)
        self.tracks.statusChanged.connect(self.onShowPeopleTractResponse)
        self.tracks.start()

    def getProviderAndLayerForTrack(self, DATAPATH, sessionid, username):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/search/shp/" + sessionid + ".shp" in lyr.source():
                layer = lyr
                break
        if layer is None:
            self.Utils.copyOnlineTrackLayer(DATAPATH, sessionid)
            layer = QgsVectorLayer(DATAPATH + "/search/shp/" + sessionid + ".shp", 'ogr')
            if not layer.isValid():
                QgsMessageLog.logMessage("Layer " + DATAPATH + "/search/shp/" + sessionid + ".shp" + " failed to load!", "Patrac")
                return []
            else:
                layer.setName(username)
                crs = QgsCoordinateReferenceSystem("EPSG:4326")
                layer.setCrs(crs)
                QgsProject.instance().addMapLayer(layer, False)
                layer.loadNamedStyle(DATAPATH + '/search/shp/style.qml')
                root = QgsProject.instance().layerTreeRoot()
                group_name = QApplication.translate("Patrac", "Online tracks", None)
                sektory_current_gpx = root.findGroup(group_name)
                if sektory_current_gpx is None:
                    sektory_current_gpx = root.insertGroup(0, group_name)
                sektory_current_gpx.addLayer(layer)
                sektory_current_gpx.setExpanded(False)

        if layer is not None:
            provider = layer.dataProvider()
            return [provider, layer]
        else:
            return []

    def onShowPeopleTractResponse(self, response):
        if response.status == 200:
            locations = response.data.read().decode("utf-8")
            prjfi = QFileInfo(QgsProject.instance().fileName())
            DATAPATH = prjfi.absolutePath()
            # print(locations)
            if "Error" in locations:
                self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Can not connect to the server.", None), level=Qgis.Warning)
                # QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
                return
            # listOfIds = [feat.id() for feat in layer.getFeatures()]
            # Splits to lines
            lines = locations.split("\n")
            if len(lines) < 2 or len(lines[1]) < 10:
                # Wrong response
                self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Tracks are empty.", None), level=Qgis.Warning)
                return
            # Deletes all features in layer patraci.shp
            # layer.deleteFeatures(listOfIds)
            # layer.commitChanges()
            # Loops the lines
            firstLine = True
            end_time = ""
            for line in lines:
                if firstLine and len(line) > 18:
                    with open(DATAPATH + "/pracovni/lasttrackcheck.txt", "w") as f:
                        f.write(line[:19])
                        end_time = line[:19]
                    firstLine = False
                if line != "":  # add other needed checks to skip titles
                    # Splits based on semicolon
                    # TODO - add time
                    cols = line.split(";")
                    if len(cols) < 5:
                        # Wrong line, skip it
                        continue
                    points = []
                    position = 0
                    # print "COLS: " + str(len(cols))
                    for col in cols:
                        if position > 3:
                            try:
                                xy = str(col).split(" ")
                                point = QgsPointXY(float(xy[0]), float(xy[1]))
                                points.append(point)
                            except:
                                QgsMessageLog.logMessage(QApplication.translate("Patrac", "Problem to read data from" + ": ", None) + line, "Patrac")
                                pass
                        position = position + 1
                    if len(points) > 1:
                        print("*****" + cols[0])
                        print(points)
                        provider_layer = self.getProviderAndLayerForTrack(DATAPATH, cols[0], cols[3])
                        if len(provider_layer) < 2:
                            # some error occured
                            continue
                        provider = provider_layer[0]
                        layer = provider_layer[1]
                        layer.startEditing()
                        self.addFeaturePolyLineFromPoints(points, cols, end_time, provider)
                        layer.commitChanges()
                        layer.triggerRepaint()
        else:
            self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Can not connect to the server.", None), level=Qgis.Warning)

    def showPeople(self):
        """Shows location of logged positions in map"""

        # Check if the project has patraci.shp
        if not self.Utils.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "Error", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.positions = Connect()
        self.positions.setUrl(self.serverUrl + 'loc.php?searchid=' + self.getSearchID())
        self.positions.statusChanged.connect(self.onShowPeopleResponse)
        self.positions.start()

    def onShowPeopleResponse(self, response):
        if response.status == 200:
            prjfi = QFileInfo(QgsProject.instance().fileName())
            DATAPATH = prjfi.absolutePath()
            layer = None
            for lyr in list(QgsProject.instance().mapLayers().values()):
                if DATAPATH + "/pracovni/patraci.shp" in lyr.source():
                    layer = lyr
                    break
            provider = layer.dataProvider()
            features = provider.getFeatures()
            sectorid = 0
            listOfIds = [feat.id() for feat in layer.getFeatures()]
            # Deletes all features in layer patraci.shp
            layer.startEditing()
            layer.deleteFeatures(listOfIds)
            layer.commitChanges()
            # Reads locations from response
            locations = response.data.read().decode("utf-8")
            # locations = locations.decode("utf-8")
            # print("LOCATIONS: " + locations)
            # Splits to lines
            lines = locations.split("\n")
            if len(lines) < 2 or len(lines[1]) < 20:
                self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Positions are empty.", None), level=Qgis.Warning)
                return
            # Loops the lines
            i = 0
            for line in lines:
                if line != "" and i > 0:  # add other needed checks to skip titles
                    # Splits based on semicolon
                    # TODO - add time
                    # print(line)
                    cols = line.split(";")
                    fet = QgsFeature()
                    # Geometry is on last place
                    try:
                        xy = str(cols[4]).split(" ")
                        fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(xy[0]), float(xy[1]))))
                        # Name and sessionid are on first and second place
                        fet.setAttributes([str(cols[0]), str(cols[1]), str(cols[2]), str(cols[3])])
                        provider.addFeatures([fet])
                    except Exception as e:
                        self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Problem to read data from" + ": ", None) + line, level=Qgis.Warning)
                        # print(e)
                        pass
                i+=1
            layer.commitChanges()
            layer.triggerRepaint()
        else:
            self.iface.messageBar().pushMessage(QApplication.translate("Patrac", "Error", None), QApplication.translate("Patrac", "Can not connect to the server.", None), level=Qgis.Warning)

    def showPeopleSimulation(self):
        """Shows location of logged positions in map"""

        # Check if the project has patraci.shp
        if not self.Utils.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "CHYBA:", None), QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/patraci.shp" in lyr.source():
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        listOfIds = [feat.id() for feat in layer.getFeatures()]
        # Deletes all features in layer patraci.shp
        layer.deleteFeatures(listOfIds)
        center = self.plugin.canvas.center()
        hh = int(self.plugin.canvas.height() / 2)
        for i in range(0, 10):
            fet = QgsFeature()
            rand = random.randint(-1 * hh, hh)
            rand2 = random.randint(-1 * hh, hh)
            crs_src = QgsCoordinateReferenceSystem(5514)
            crs_dest = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(crs_src, crs_dest)
            point_5514 = QgsPointXY(center.x() + rand, center.y() + rand2)
            point_4326 = xform.transform(point_5514)
            fet.setGeometry(QgsGeometry.fromPointXY(point_4326))
            fet.setAttributes(['idpatrani', '2019-09-03T13:00:00', 'A', 'Karel ' + str(i)])
            provider.addFeatures([fet])
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)

    def testHds(self, textEdit):
        self.Hds.testHds(textEdit)

    def testHdsData(self, region, textEdit):
        self.Hds.testHdsData(region, textEdit)

    def setSectorsUniqueValuesStyle(self):
        self.Styles.setSectorsStyle('unique')
        self.setSectorsShowLabels()

    def setSectorsSingleValuesStyle(self):
        self.Styles.setSectorsStyle('single')
        self.setSectorsShowLabels()

    def setSectorsShowLabels(self):
        if self.chkShowLabels.isChecked():
            self.Styles.setSectorsLabels(True)
        else:
            self.Styles.setSectorsLabels(False)

    def setSectorsProgressStyle(self):
        self.Styles.setSectorsStyle('stav')
        self.setSectorsShowLabels()

    def setSectorsUnitsStyle(self):
        self.Styles.setSectorsStyle('units')
        self.setSectorsShowLabels()

    def setSectorsUnitsRecommendedStyle(self):
        self.Styles.setSectorsStyle('units_recommended')
        self.setSectorsShowLabels()
