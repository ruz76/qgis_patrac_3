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

import csv, io, math, subprocess, os, sys, uuid

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Printing(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas

    def exportPDF(self, extent, path):
        self.export(extent, path)
        self.exportTiles(extent, path)

    def exportTiles(self, extent, path):
        widthprint = 0.27
        widthmap = extent.width()
        heightmap = extent.height()
        rect = QgsRectangle(extent.xMinimum(), extent.yMinimum(), extent.xMinimum() + widthmap / 2, extent.yMinimum() + heightmap / 2)
        self.export(rect, path + "_1.pdf")
        rect = QgsRectangle(extent.xMinimum(), extent.yMinimum() + heightmap / 2, extent.xMinimum() + widthmap / 2, extent.yMinimum() + heightmap)
        self.export(rect, path + "_2.pdf")
        rect = QgsRectangle(extent.xMinimum() + widthmap / 2, extent.yMinimum() + heightmap / 2, extent.xMinimum() + widthmap, extent.yMinimum() + heightmap)
        self.export(rect, path + "_3.pdf")
        rect = QgsRectangle(extent.xMinimum() + widthmap / 2, extent.yMinimum(), extent.xMinimum() + widthmap, extent.yMinimum() + heightmap / 2)
        self.export(rect, path + "_4.pdf")

    def export(self, extent, path):
        project = QgsProject.instance()
        layout = project.layoutManager().layoutByName("Basic")
        maps = [item for item in list(layout.items()) if
                item.type() == QgsLayoutItemRegistry.LayoutMap and item.scene()]
        composer_map = maps[0]
        extent.scale(1.1)
        composer_map.zoomToExtent(extent)
        layout.updateSettings()
        exporter = QgsLayoutExporter(layout)
        exporter.exportToPdf(path, QgsLayoutExporter.PdfExportSettings())