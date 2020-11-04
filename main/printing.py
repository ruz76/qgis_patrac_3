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
import fileinput

from qgis.core import *
from qgis.gui import *

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Printing(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas

    def exportPDF(self, extent, path):
        self.exportAll(extent, path, 1.1)
        with open(path + "report.html", 'r') as file :
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("<!--tilemapall-->", '<p><a href="report.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')

        # Write the file out again
        with open(path + "report.html", 'w') as file:
            file.write(filedata)

    def exportTiles(self, extent, path, scale):
        widthmax = (271.816 * scale) / 0.64
        heightmax = (177.272 * scale) / 0.64
        widthmap = extent.width()
        heightmap = extent.height()
        cols = int(widthmap / widthmax) + 1 # we need to handle round - may use roundup ot increase number of cols by 1
        rows = int(heightmap / heightmax) + 1 # we need to handle round - may use roundup ot increase number of cols by 1
        tilemap = ""
        tilemap += '<table style="width: 400px; height: 250px">\n'
        for row in range(rows):
            tilemap += '<tr>\n'
            for col in range(cols):
                rect = QgsRectangle(extent.xMinimum() + (col * widthmax),
                                    extent.yMaximum() - (row * heightmax),
                                    extent.xMinimum() + (col * widthmax) + widthmax,
                                    extent.yMaximum() - (row * heightmax) - heightmax)
                tilemap += '<td style="border: 1px solid; width: 100px; height: 50px; text-align: center"><a href="' + str(scale) + '_report_' + str(row) + '_' + str(col) + '.pdf">' + str(row) + '-' + str(col) + '&nbsp;<img src="styles/pdf.png" alt="PDF" width="40"></a></a></td>\n'
                self.export(rect, path + str(scale) + "_report_" + str(row) + "_" + str(col) + ".pdf", 1.0)
            tilemap += '</tr>\n'
        tilemap += '</table>\n'

        # Read in the file
        with open(path + "report.html", 'r') as file :
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("<!--tilemap" + str(scale) + "-->", tilemap)

        # Write the file out again
        with open(path + "report.html", 'w') as file:
            file.write(filedata)

    def export(self, extent, path, scale):
        project = QgsProject.instance()
        layout = project.layoutManager().layoutByName("Basic")
        maps = [item for item in list(layout.items()) if
                item.type() == QgsLayoutItemRegistry.LayoutMap and item.scene()]
        composer_map = maps[0]
        extent.scale(scale)
        composer_map.zoomToExtent(extent)
        layout.updateSettings()
        exporter = QgsLayoutExporter(layout)
        exporter.exportToPdf(path, QgsLayoutExporter.PdfExportSettings())

    def exportAll(self, extent, path, scale):
        project = QgsProject.instance()
        layout = project.layoutManager().layoutByName("Basic")
        maps = [item for item in list(layout.items()) if
                item.type() == QgsLayoutItemRegistry.LayoutMap and item.scene()]
        composer_map = maps[0]
        extent.scale(scale)
        composer_map.zoomToExtent(extent)
        layout.updateSettings()
        exporter = QgsLayoutExporter(layout)
        exporter.exportToPdf(path + "report.pdf", QgsLayoutExporter.PdfExportSettings())
        #self.exportTiles(composer_map.extent(), path, 50)
        composer_map.zoomToExtent(extent)
        self.exportTiles(composer_map.extent(), path, 25)
        composer_map.zoomToExtent(extent)
        self.exportTiles(composer_map.extent(), path, 10)
