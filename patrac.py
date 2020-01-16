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
import configparser

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from qgis.core import *
from qgis.gui import *

from . import patracdockwidget
from . import aboutdialog

from . import resources_rc

class PatracPlugin(object):

    singleBandStyles = ["paletted",
                        "singlebandgray",
                        "singlebandpseudocolor"
                       ]

    def __init__(self, iface):
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
            translationPath = userPluginPath + "/i18n/patrac_" + localeFullName + ".qm"
        else:
            translationPath = systemPluginPath + "/i18n/patrac_" + localeFullName + ".qm"

        self.localePath = translationPath
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            QCoreApplication.installTranslator(self.translator)

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
        self.actionDock.setCheckable(True)

        self.actionAbout = QAction(QIcon(":/icons/about.png"), "About", self.iface.mainWindow())
        self.actionAbout.setStatusTip(QCoreApplication.translate("Patrac", "About Patrac"))
        self.actionAbout.setWhatsThis(QCoreApplication.translate("Patrac", "About Patrac"))

        self.actionDock.triggered.connect(self.showHideDockWidget)
        self.actionAbout.triggered.connect(self.about)

        #self.iface.addPluginToolBarIcon(self.actionDock)
        self.iface.addPluginToMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)
        self.iface.addPluginToMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionAbout)

        self.dockWidget = patracdockwidget.PatracDockWidget(self)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)
        self.dockWidget.visibilityChanged.connect(self.__dockVisibilityChanged)

        self.iface.currentLayerChanged.connect(self.layerChanged)
        self.layerChanged()

    def unload(self):
        self.iface.currentLayerChanged.disconnect(self.layerChanged)

        #self.iface.removePluginToolBarIcon(self.actionDock)
        self.iface.removePluginMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionDock)
        self.iface.removePluginMenu(QCoreApplication.translate("Patrac", "Patrac"), self.actionAbout)

        self.dockWidget.close()
        del self.dockWidget
        self.dockWidget = None

    def showHideDockWidget(self):
        if self.dockWidget.isVisible():
            self.dockWidget.hide()
        else:
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

    def about(self):
        d = aboutdialog.AboutDialog()
        d.exec_()

    def __dockVisibilityChanged(self):
        if self.dockWidget.isVisible():
            self.actionDock.setChecked(True)
        else:
            self.actionDock.setChecked(False)
