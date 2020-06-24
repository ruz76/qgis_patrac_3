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
from . import aboutdialog
from .connect.connect import *

from . import resources_rc

# Debugger
from . import debug

class PatracPlugin(object):

    singleBandStyles = ["paletted",
                        "singlebandgray",
                        "singlebandpseudocolor"
                       ]

    def __init__(self, iface):
        # debug.RemoteDebugger.setup_remote_pydev_debug('localhost',10999)

        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.layer = None
        self.toolBar = None

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

    def checkSettings(self):
        pluginPath = path.dirname(__file__)
        profilePath = pluginPath + "/../../../"
        if not os.path.isdir(profilePath + "qgis_patrac_settings"):
            os.mkdir(profilePath + "qgis_patrac_settings")
            os.mkdir(profilePath + "qgis_patrac_settings/config")
            os.mkdir(profilePath + "qgis_patrac_settings/styles")
            os.mkdir(profilePath + "qgis_patrac_settings/grass")
            copy(pluginPath + "/config/systemid.txt", profilePath + "qgis_patrac_settings/config/")
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
        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'C:/patracdata/'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'D:/patracdata/'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'E:/patracdata/'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/'

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

        self.actionDock = QAction(QIcon(":/icons/patrac.png"), "Patrac", self.iface.mainWindow())
        self.actionDock.setStatusTip(QCoreApplication.translate("Patrac", "Show/hide Patrac dockwidget"))
        self.actionDock.setWhatsThis(QCoreApplication.translate("Patrac", "Show/hide Patrac dockwidget"))
        self.actionDock.triggered.connect(self.showWidget)
        self.iface.addPluginToMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)

        self.dockWidget = patracdockwidget.PatracDockWidget(self)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)

        self.iface.currentLayerChanged.connect(self.layerChanged)
        self.layerChanged()

        self.createToolbar()
        self.hideToolbars()

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
        self.toolbar = self.iface.addToolBar("Patrac Toolbar")
        self.toolbar.setObjectName("Patrac Toolbar")
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
        self.toolbar.addAction(self.iface.actionMeasure())
        self.toolbar.addAction(self.iface.actionMeasureArea())
        self.toolbar.addAction(self.iface.actionAddRasterLayer())
        self.toolbar.addAction(self.iface.actionAddOgrLayer())

    def unload(self):
        self.iface.currentLayerChanged.disconnect(self.layerChanged)

        #self.iface.removePluginToolBarIcon(self.actionDock)
        self.iface.removePluginMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)
        self.iface.removePluginMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionAbout)

        self.dockWidget.close()
        del self.dockWidget
        self.dockWidget = None

    def showWidget(self):
        self.dockWidget.show()

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
