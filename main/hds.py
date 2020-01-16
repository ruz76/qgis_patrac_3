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

import csv, io, math, subprocess, os, sys, uuid, filecmp

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Hds(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.Utils = self.widget.Utils
        self.Area = self.widget.Area
        self.Sectors = self.widget.Sectors

    # Tests
    def loadTestProject(self):
        project = QgsProject.instance()
        project.read(QFileInfo(self.pluginPath + '/tests/data/zahradka__plzen-sever_/clean.qgs'))

    def compareFiles(self, file1, file2, datetimefile1_orig):
        # we test just the binary content
        datetimefile1 = self.Utils.creation_date(file1)
        if (filecmp.cmp(file1, file2)) and (datetimefile1 != datetimefile1_orig):
            return True
        else:
            return False

    # Happy day scenario test
    def testHds(self):
        # prepare

        # load project
        self.loadTestProject()

        # get area
        datetimefile1_orig = self.Utils.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/distances_costed_cum.tif')
        self.Area.getArea()
        # the tiff should be the same as matrice

        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/distances_costed_cum.tif',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/distances_costed_cum.tif',
                             datetimefile1_orig):
            QgsMessageLog.logMessage("INFO: Area test skončil dobře (výstupní tif odpovídá očekávanému stavu)",
                                     "Patrac")
        else:
            QgsMessageLog.logMessage("ERROR: Area test skončil chybou (výstupní tif neodpovídá očekávanému stavu)",
                                     "Patrac")

        # get sectors
        datetimefile1_orig = self.Utils.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/sektory_group_selected.shp')
        self.widget.sliderEnd.setValue(60)
        self.Sectors.getSectors(0,60)
        # the shp should be same as matrice
        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/sektory_group_selected.shp',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/sektory_group_selected.shp',
                             datetimefile1_orig):
            QgsMessageLog.logMessage("INFO: Sectors test skončil dobře (výstupní SHP odpovídá očekávanému stavu)",
                                     "Patrac")
        else:
            QgsMessageLog.logMessage("ERROR: Sectors test skončil chybou (výstupní SHP neodpovídá očekávanému stavu)",
                                     "Patrac")

        # repost export
        datetimefile1_orig = self.Utils.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/sektory/report.html')
        self.Sectors.reportExportSectors(True, True)
        # the html should be same as matrice
        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/sektory/report.html',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/report.html',
                             datetimefile1_orig):
            QgsMessageLog.logMessage(
                "INFO: Report_Export test skončil dobře (výstupní HTML odpovídá očekávanému stavu)", "Patrac")
        else:
            QgsMessageLog.logMessage(
                "ERROR: Report_Export test skončil chybou (výstupní HTML neodpovídá očekávanému stavu)", "Patrac")

