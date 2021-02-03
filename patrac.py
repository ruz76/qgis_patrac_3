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


import os, subprocess, sys
from os import path
from shutil import copy
from glob import glob
import configparser

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from qgis.core import *
from qgis.gui import *

from . import patracdockwidget
from .connect.connect import *

# Debugger
from . import debug

class NoClose(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def ok_to_close(self):
        self.pluginPath = path.dirname(__file__)
        if path.exists(self.pluginPath + "/config/lastprojectpath.txt"):
            with open(self.pluginPath + "/config/lastprojectpath.txt", "r") as f:
                projectPath = f.read()
                print(projectPath + "/search/result.xml")
                # TODO stop QGIS from exiting
                if not path.exists(projectPath + "/search/result.xml"):
                    return False
                else:
                    return True
        else:
            return True

    def eventFilter(self, object, event):
        # print("CLOSE FILTER")
        if isinstance(event, QCloseEvent):
            if not self.ok_to_close():
                QMessageBox.warning(None, QApplication.translate("Patrac", "ERROR", None), QApplication.translate("Patrac", "You did not enter the result of the search. Use smile button, please.", None))
                event.ignore()
                return True

        return super().eventFilter( object, event )

class PatracPlugin(object):

    singleBandStyles = ["paletted",
                        "singlebandgray",
                        "singlebandpseudocolor"
                       ]

    def __init__(self, iface):
        # debug.RemoteDebugger.setup_remote_pydev_debug('localhost',10999)

        #QgsApplication.setQuitOnLastWindowClosed(False)
        #QgsApplication.lastWindowClosed.connect(self.exiting)

        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.no_close = NoClose()
        self.iface.mainWindow().installEventFilter(self.no_close)

        self.layer = None
        self.toolBar = None
        self.toolbar = self.iface.addToolBar("Patrac Toolbar")
        self.toolbar.setObjectName("Patrac Toolbar")

        # self.qgsVersion = str(QGis.QGIS_VERSION_INT)

        userPluginPath = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/qgis_patrac"

        overrideLocale = bool(QSettings().value("locale/overrideFlag", False))
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        if QFileInfo(userPluginPath).exists():
            translationPath = userPluginPath + "/i18n/qgis_patrac_" + localeFullName + ".qm"
        else:
            translationPath = systemPluginPath + "/i18n/qgis_patrac_" + localeFullName + ".qm"

        self.localePath = translationPath
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            QCoreApplication.installTranslator(self.translator)

        self.checkSettings()
        self.copyDoc()
        self.checkRequests = CheckRequests(userPluginPath + "/settings.db")
        self.checkRequests.start()

        self.saveProject = SaveProject()
        self.saveProject.start()
        self.iface.actionMapTips().setChecked(True)

    def checkSettings(self):
        pluginPath = path.dirname(__file__)
        profilePath = pluginPath + "/../../../"
        if not os.path.isdir(profilePath + "qgis_patrac_settings"):
            os.mkdir(profilePath + "qgis_patrac_settings")
            os.mkdir(profilePath + "qgis_patrac_settings/config")
            os.mkdir(profilePath + "qgis_patrac_settings/styles")
            os.mkdir(profilePath + "qgis_patrac_settings/grass")
            copy(pluginPath + "/config/systemid.txt", profilePath + "qgis_patrac_settings/config/")
            copy(pluginPath + "/config/config.json", profilePath + "qgis_patrac_settings/config/")
            copy(pluginPath + "/config/paths.txt", profilePath + "qgis_patrac_settings/config/")
            copy(pluginPath + "/grass/maxtime.txt", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/units.txt", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/weightlimit.txt", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/radialsettings.txt", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/distancesUser.txt", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/buffer.csv", profilePath + "qgis_patrac_settings/grass/")
            copy(pluginPath + "/grass/units_times.csv", profilePath + "qgis_patrac_settings/grass/")
            for file in glob(pluginPath + "/styles/*"):
                copy(file, profilePath + "qgis_patrac_settings/styles/")
        else:
            if not os.path.isfile(profilePath + "qgis_patrac_settings/grass/buffer.csv"):
                copy(pluginPath + "/grass/buffer.csv", profilePath + "qgis_patrac_settings/grass/")
            if not os.path.isfile(profilePath + "qgis_patrac_settings/grass/units_times.csv"):
                copy(pluginPath + "/grass/units_times.csv", profilePath + "qgis_patrac_settings/grass/")
            if not os.path.isfile(profilePath + "qgis_patrac_settings/config/config.json"):
                copy(pluginPath + "/config/config.json", profilePath + "qgis_patrac_settings/config/")
            for file in glob(pluginPath + "/styles/*"):
                copy(file, profilePath + "qgis_patrac_settings/styles/")

    def copyDocDir(self, DATAPATH, pluginPath, name):
        if not os.path.isdir(DATAPATH + "doc/" + name):
            os.mkdir(DATAPATH + "doc/" + name)
        for file in glob(pluginPath + "/doc/" + name + "/*"):
            copy(file, DATAPATH + "doc/" + name + "/")

    def copyDoc(self):
        pluginPath = path.dirname(__file__)
        DATAPATH = self.getPatracDataPath()
        if not os.path.isdir(DATAPATH + "doc"):
            os.mkdir(DATAPATH + "doc")
        copy(pluginPath + "/doc/index.html", DATAPATH + "doc/")
        self.copyDocDir(DATAPATH, pluginPath, "css")
        self.copyDocDir(DATAPATH, pluginPath, "fonts")
        self.copyDocDir(DATAPATH, pluginPath, "images")
        self.copyDocDir(DATAPATH, pluginPath, "js")

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


    def initGui(self):
        # if int(self.qgsVersion) < 10900:
        #     qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
        #     QMessageBox.warning(self.iface.mainWindow(),
        #                         "Patrac",
        #                         QCoreApplication.translate("Patrac", "QGIS version detected: ") + qgisVersion +
        #                         QCoreApplication.translate("Patrac", "Je potřeba minimálně verze 2.0.\nPlugin nebude fungovat."))
        #     return None

        self.dockWidget = None
        pluginPath = path.dirname(__file__)

        self.actionDock = QAction(QIcon(pluginPath + "/icons/patrac.png"), "Patrac", self.iface.mainWindow())
        self.actionDock.setStatusTip(QCoreApplication.translate("Patrac", "Show/hide Patrac dockwidget"))
        self.actionDock.setWhatsThis(QCoreApplication.translate("Patrac", "Show/hide Patrac dockwidget"))
        self.actionDock.triggered.connect(self.showWidget)
        self.iface.addPluginToMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)

        self.dockWidget = patracdockwidget.PatracDockWidget(self)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)

        self.iface.currentLayerChanged.connect(self.layerChanged)
        self.iface.initializationCompleted.connect(self.hideToolbars)
        self.layerChanged()

        self.createToolbar()
        self.hideToolbars()

    def runHDS(self):
        self.dockWidget.testHds(None)

    def exiting(self):
        print("EXITING")

    def hideToolbars(self):
        self.iface.advancedDigitizeToolBar().setVisible(False)
        self.iface.attributesToolBar().setVisible(False)
        self.iface.databaseToolBar().setVisible(False)
        self.iface.dataSourceManagerToolBar().setVisible(False)
        self.iface.digitizeToolBar().setVisible(False)
        self.iface.fileToolBar().setVisible(False)
        self.iface.helpToolBar().setVisible(False)
        self.iface.layerToolBar().setVisible(False)
        self.iface.mapNavToolToolBar().setVisible(False)
        self.iface.pluginToolBar().setVisible(False)
        self.iface.rasterToolBar().setVisible(False)
        self.iface.vectorToolBar().setVisible(False)
        self.iface.webToolBar().setVisible(False)

    def createToolbar(self):
        self.toolbar.addAction(self.actionDock)
        self.toolbar.addAction(self.iface.actionOpenProject())
        self.toolbar.addAction(self.iface.actionSaveProject())
        self.toolbar.addAction(self.iface.actionShowLayoutManager())
        self.toolbar.addAction(self.iface.actionPan())
        self.toolbar.addAction(self.iface.actionZoomIn())
        self.toolbar.addAction(self.iface.actionZoomOut())
        self.toolbar.addAction(self.iface.actionZoomToLayer())
        self.toolbar.addAction(self.iface.actionZoomToSelected())
        self.toolbar.addAction(self.iface.actionIdentify())
        self.toolbar.addAction(self.iface.actionOpenTable())
        self.toolbar.addAction(self.iface.actionOpenFieldCalculator())
        self.toolbar.addAction(self.iface.actionSelect())
        self.toolbar.addAction(self.iface.actionToggleEditing())
        self.toolbar.addAction(self.iface.actionAddFeature())
        self.toolbar.addAction(self.iface.actionMoveFeature())
        self.toolbar.addAction(self.iface.actionDeleteSelected())
        self.toolbar.addAction(self.iface.actionSplitFeatures())
        self.toolbar.addAction(self.iface.actionSaveEdits())
        self.addRecalculateButton()
        self.toolbar.addAction(self.iface.actionMeasure())
        self.toolbar.addAction(self.iface.actionMeasureArea())
        self.toolbar.addAction(self.iface.actionAddRasterLayer())
        self.toolbar.addAction(self.iface.actionAddOgrLayer())
        self.addVectorsForSplitByLineButton()
        self.addSplitByLineButton()

    def addRecalculateButton(self):
        pluginPath = path.dirname(__file__)
        self.recalculateSectorsAction = QAction(QIcon(pluginPath + "/icons/number_sectors.png"), "Patrac", self.iface.mainWindow())
        self.recalculateSectorsAction.setStatusTip(QCoreApplication.translate("Patrac", "Recalculate sectors"))
        self.recalculateSectorsAction.setWhatsThis(QCoreApplication.translate("Patrac", "Recalculate sectors"))
        self.recalculateSectorsAction.triggered.connect(self.dockWidget.recalculateSectorsExpert)
        self.toolbar.addAction(self.recalculateSectorsAction)

    def addSplitByLineButton(self):
        pluginPath = path.dirname(__file__)
        self.splitByLineAction = QAction(QIcon(pluginPath + "/icons/split_by_line.png"), "Patrac", self.iface.mainWindow())
        self.splitByLineAction.setStatusTip(QCoreApplication.translate("Patrac", "Split by line"))
        self.splitByLineAction.setWhatsThis(QCoreApplication.translate("Patrac", "Split by line"))
        self.splitByLineAction.triggered.connect(self.dockWidget.splitByLine)
        self.toolbar.addAction(self.splitByLineAction)

    def addVectorsForSplitByLineButton(self):
        pluginPath = path.dirname(__file__)
        self.addVectorsForSplitByLineAction = QAction(QIcon(pluginPath + "/icons/add_vectors_for_split_by_line.png"), "Patrac", self.iface.mainWindow())
        self.addVectorsForSplitByLineAction.setStatusTip(QCoreApplication.translate("Patrac", "Add vectors for Split by line"))
        self.addVectorsForSplitByLineAction.setWhatsThis(QCoreApplication.translate("Patrac", "Add vectors for Split by line"))
        self.addVectorsForSplitByLineAction.triggered.connect(self.dockWidget.addVectorsForSplitByLine)
        self.toolbar.addAction(self.addVectorsForSplitByLineAction)

    def createShowWidgetAction(self):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

    def unload(self):
        # if not self.no_close.ok_to_close():
        #     if sys.platform.startswith('win'):
        #         try:
        #             subprocess.Popen(("C:/OSGeo4W64/bin/qgis.bat"))
        #         except:
        #             print("CAN NOT FIND QGIS TO RELOAD")
        #     else:
        #         try:
        #             subprocess.Popen(("qgis", "--profiles-path", "/home/jencek/qgis3_profiles", "--profile", "default"))
        #         except:
        #             print("CAN NOT FIND QGIS TO RELOAD")

        self.iface.currentLayerChanged.disconnect(self.layerChanged)
        self.iface.removePluginMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)
        self.dockWidget.close()
        del self.dockWidget
        self.dockWidget = None

    def showWidget(self):
        self.dockWidget.show()
        self.hideToolbars()
        for x in self.iface.mainWindow().findChildren(QDockWidget):
            if x.objectName() == 'Layers' or x.objectName() == 'PatracDockWidget':
                x.setVisible(True)
                x.setFloating(False)

    def layerChanged(self):
        self.layer = self.iface.activeLayer()

        if self.layer is None:
            return

        if self.layer.type() != QgsMapLayer.RasterLayer:
            self.dockWidget.disableOrEnableControls(False)
            return

        if self.layer.providerType() not in ["gdal", "grass"]:
            self.dockWidget.disableOrEnableControls(False)
            return

        if self.layer.bandCount() > 1 and self.layer.renderer().type() not in self.singleBandStyles:
            self.dockWidget.disableOrEnableControls(False)
            return

        band = self.layer.renderer().usesBands()[0]
        stat = self.layer.dataProvider().bandStatistics(band)
        maxValue = int(stat.maximumValue)
        minValue = int(stat.minimumValue)
        self.dockWidget.updateSliders(maxValue, minValue)

        self.dockWidget.disableOrEnableControls(True)
