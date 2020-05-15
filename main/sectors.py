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

import csv, io, math, subprocess, os, sys, uuid, webbrowser

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Sectors(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.Utils = self.widget.Utils
        self.Printing = self.widget.Printing

    def getSectors(self, min, max):
        """Selects sectors from grass database based on filtered raster"""

        # Check if the project has sektory_group.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Removes layer
        # self.removeLayer(DATAPATH + '/pracovni/sektory_group.shp')

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/sectors.py", "Patrac")
        self.widget.setCursor(Qt.WaitCursor)
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_sectors.bat", DATAPATH, self.pluginPath,
                                  str(min), str(max)))
            p.wait()
            # os.system(self.pluginPath + "/grass/run_sectors.bat " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_sectors.sh", DATAPATH, self.pluginPath,
                                  str(min), str(max)))
            p.wait()
            # os.system("bash " + self.pluginPath + "/grass/run_sectors.sh " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))

        # Adds newly created layer with sectors to map
        self.Utils.addVectorLayer(DATAPATH + '/pracovni/sektory_group_selected.shp', 'sektory vybrané')

        #layer.dataProvider().forceReload()
        # layer.triggerRepaint()
        self.filterSectors()
        self.widget.setCursor(Qt.ArrowCursor)
        # self.recalculateSectors(False)
        return

    def filterSectors(self):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group_selected.shp" in lyr.source():
                layer = lyr
                break

        provider = layer.dataProvider()
        features = provider.getFeatures()
        # save ids of selected sectors into file for future usage
        f = open(self.Utils.getDataPath() + '/pracovni/selectedSectors.txt', 'w')
        filter = "id IN ("
        for feature in features:
            f.write(str(feature['id']) + "\n")
            filter += "'" + str(feature['id']) + "', "
        filter = filter[:-2] + ")"
        f.close()

        # remove layer we do not need it
        # Removes first two attrbutes from added layer
        # Attributes are something like cat_
        # Attributes cat and cat_ are identical
        fList = list()
        fList.append(0)
        fList.append(1)
        layer.startEditing()
        layer.dataProvider().deleteAttributes(fList)
        layer.commitChanges()

        self.Utils.removeLayer(self.Utils.getDataPath() + "/pracovni/sektory_group_selected.shp")

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        # Filter the layer
        QgsMessageLog.logMessage("Filtruji " + filter, "Patrac")
        layer.setSubsetString(filter)

    def extendRegion(self):
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/export.py", "Patrac")
        self.widget.setCursor(Qt.WaitCursor)

        initialExtent = open(self.Utils.getDataPath() + '/config/extent.txt', 'r').read()
        initialExtentItems = initialExtent.split(" ")

        XMIN = str(self.canvas.extent().xMinimum()) \
            if self.canvas.extent().xMinimum() < float(initialExtentItems[0]) else initialExtentItems[0]
        YMIN = str(self.canvas.extent().yMinimum()) \
            if self.canvas.extent().yMinimum() < float(initialExtentItems[1]) else initialExtentItems[1]
        XMAX = str(self.canvas.extent().xMaximum()) \
            if self.canvas.extent().xMaximum() > float(initialExtentItems[2]) else initialExtentItems[2]
        YMAX = str(self.canvas.extent().yMaximum()) \
            if self.canvas.extent().yMaximum() > float(initialExtentItems[3]) else initialExtentItems[3]

        # XMIN = str(self.canvas.extent().xMinimum())
        # YMIN = str(self.canvas.extent().yMinimum())
        # XMAX = str(self.canvas.extent().xMaximum())
        # YMAX = str(self.canvas.extent().yMaximum())

        if sys.platform.startswith('win'):
            p = subprocess.Popen((
                self.pluginPath + "/grass/run_export.bat", self.getRegionDataPath(), self.pluginPath, XMIN, YMIN,
                XMAX, YMAX, self.Utils.getDataPath()))
            p.wait()
            p = subprocess.Popen((self.pluginPath + "/grass/run_import_for_extend.bat", self.Utils.getDataPath(), self.pluginPath, XMIN,
                                  YMIN, XMAX, YMAX, self.getRegionDataPath()))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_export.sh", self.getRegionDataPath(), self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, self.Utils.getDataPath()))
            p.wait()
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_import_for_extend.sh", self.Utils.getDataPath(), self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, self.getRegionDataPath()))
            p.wait()

        self.appendSectors()
        self.widget.setCursor(Qt.ArrowCursor)

    def getRegionDataPath(self):
        region = open(self.Utils.getDataPath() + '/config/region.txt', 'r').read()
        return self.Utils.getDataPath() + "/../../../" + region

    def getSectorsIds(self):
        with open(self.Utils.getDataPath() + '/pracovni/listOfIds.txt') as f:
            return f.read().splitlines()

    def appendSectors(self):
        self.Utils.addVectorLayer(self.Utils.getDataPath() + "/pracovni/sektory_group_to_append.shp", "Sektory k přidání")

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        layerToAdd = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group_to_append.shp" in lyr.source():
                layerToAdd = lyr
                break

        if layerToAdd == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        # we remove the subset if it is set
        layer.setSubsetString("")

        # we save the edits before the process (if there are any)
        layer.commitChanges()

        # we create list of ids of existing layer
        startingLetter = 'B'
        featureIds = self.getSectorsIds()
        #print(featureIds)
        #geometries = []
        provider = layer.dataProvider()
        features = provider.getFeatures()
        # for feature in features:
        #     #featureIds.append(feature['id'])
        #     #geometries.append(feature.geometry())
        #     if ord(feature['label'][0:1]) >= ord(startingLetter):
        #         startingLetter = chr(ord(feature['label'][0:1]) + 1)

        # we open layer again to add new sectors
        layer.startEditing()

        f = open(self.Utils.getDataPath() + '/pracovni/listOfIds.txt', 'a')
        providerToAdd = layerToAdd.dataProvider()
        featuresToAdd = providerToAdd.getFeatures()
        sectorid = 0
        for feature in featuresToAdd:
            if str(feature['id']) not in featureIds:
                # print("ADD " + str(feature['id']))
                f.write(str(feature['id']) + "\n")
                sectorid = sectorid + 1
                # feature['label'] = str(startingLetter) + str(sectorid)
                feature['label'] = feature['id']
                feature['area_ha'] = round(feature.geometry().area() / 10000)
                layer.addFeature(feature)

        f.close()
        layer.commitChanges()
        layer.triggerRepaint()

        self.Utils.removeLayer(self.Utils.getDataPath() + "/pracovni/sektory_group_to_append.shp")

    def recalculateSectors(self, setLabels):
        """Recalculate areas of sectors and identifiers"""

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR",
                                    "Wrong project.", None))
            return

        self.widget.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        f = None
        if setLabels:
            f = open(DATAPATH + '/pracovni/listOfIds.txt', 'w')
        layer.startEditing()
        for feature in features:
            sectorid = sectorid + 1
            # Label is set to A and sequential number
            # Labels must be stable for whole search area, so only at the beginning are sectors labeled
            if setLabels:
            	#feature['label'] = 'A' + str(sectorid)
            	feature['label'] = str(feature['id'])
            # Area in hectares
            feature['area_ha'] = round(feature.geometry().area() / 10000)
            #print(str(feature['id']))
            if setLabels:
                f.write(str(feature['id']) + "\n")
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        if setLabels:
            f.close()

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/store_sectors.py", "Patrac")
        self.widget.setCursor(Qt.WaitCursor)
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_store_sectors.bat", DATAPATH, self.pluginPath))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_store_sectors.sh", DATAPATH, self.pluginPath))
            p.wait()

        self.widget.setCursor(Qt.ArrowCursor)
        return sectorid

    def removeExportedSectors(self):
        self.widget.setCursor(Qt.WaitCursor)
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if "sektory/shp" in lyr.source():
                if lyr.isValid():
                    QgsProject.instance().removeMapLayer(lyr)
        self.widget.setCursor(Qt.ArrowCursor)
        return

    def exportSectors(self):
        """Exports sectors to SHP and GPX without creating report. It is much faster and allows to use only selected sectors."""

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        sectorid = self.recalculateSectors(False)
        self.widget.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break
        provider = layer.dataProvider()
        features = layer.selectedFeatures()
        if len(features) < 1:
            features = provider.getFeatures()
            QgsMessageLog.logMessage("Není vybrán žádný sektor. Exportuji všechny", "Patrac")

        self.removeExportedSectors()

        # prepare all sectors to one file
        self.Utils.copyLayer(DATAPATH, "all")
        layerLines = QgsVectorLayer(DATAPATH + "/sektory/shp/all.shp", "sektory linie", "ogr")
        providerLayerLines = layerLines.dataProvider()
        layerLines.startEditing()
        fList = list()
        fList.append(0)
        layerLines.dataProvider().deleteAttributes(fList)
        layerLines.renameAttribute(0, 'name')
        layerLines.renameAttribute(1, 'desc')

        i = 1
        for feature in features:
            # Removes existing layer according to label in features
            # TODO - if the number of sectors is higher than in previous step, some of the layers are not removed
            # self.removeLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp")
            self.Utils.copyLayer(DATAPATH, feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()
            fet.setAttributes([feature['label'], str(feature['area_ha']) + ' ha '])

            polygon = feature.geometry()
            line = QgsGeometry.fromPolylineXY(polygon.asMultiPolygon()[0][0])
            fet.setGeometry(line)
            providerSector.addFeatures([fet])
            providerLayerLines.addFeatures([fet])
            sector.commitChanges()

            if not sector.isValid():
                QgsMessageLog.logMessage("Sector " + feature['label'] + " se nepodařilo načíst", "Patrac")
            else:
                # Export do GPX
                crs = QgsCoordinateReferenceSystem("EPSG:4326")
                # QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                #                                         "utf-8", crs, "GPX",
                #                                         datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                #                                         layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                                                        "utf-8", crs, "GPX",
                                                        datasourceOptions=['NameField=label'],
                                                        layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsProject.instance().addMapLayer(sector, False)
                root = QgsProject.instance().layerTreeRoot()
                sektorygroup = root.findGroup("sektory")
                if sektorygroup is None:
                    sektorygroup = root.insertGroup(0, "sektory")
                sektorygroup.addLayer(sector)
                sektorygroup.setExpanded(False)

            i += 1

        # writes all sectors to one file
        layerLines.commitChanges()
        QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
                                                    "utf-8", crs, "GPX",
                                                    layerOptions=['FORCE_GPX_TRACK=YES'])

        self.widget.setCursor(Qt.ArrowCursor)
        return

    def rewriteSelectedSectors(self):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break
        crs = QgsCoordinateReferenceSystem("EPSG:5514")
        QgsVectorFileWriter.writeAsVectorFormat(layer, self.Utils.getDataPath() + "/pracovni/sektory_group_selected.shp",
                                                "utf-8", crs, "ESRI Shapefile")

    def reportExportSectors(self, openReport, exportPDF):
        """Creates report and exports sectors to SHP and GPX"""

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        sectorid = self.recalculateSectors(False)

        self.widget.setCursor(Qt.WaitCursor)
        # exports curent layer to selected layer for GRASS GIS import
        self.rewriteSelectedSectors()

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        # exports overall map with all sectors to PDF
        if exportPDF:
            self.Printing.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")

        provider = layer.dataProvider()
        features = provider.getFeatures()

        LABELS = ""
        for feature in features:
            LABELS = LABELS + "!" + str(feature['label'])

        overrideLocale = bool(QSettings().value("locale/overrideFlag", False))
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        # GRASS exports to SHP
        if sys.platform.startswith('win'):
            p = subprocess.Popen(
                (self.pluginPath + "/grass/run_report_export.bat", DATAPATH, self.pluginPath, str(sectorid), LABELS, localeFullName))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_report_export.sh", DATAPATH, self.pluginPath,
                                  str(sectorid), LABELS, localeFullName))
            p.wait()

        # prepare all sectors to one file
        self.Utils.copyLayer(DATAPATH, "all")
        layerLines = QgsVectorLayer(DATAPATH + "/sektory/shp/all.shp", "sektory linie", "ogr")
        providerLayerLines = layerLines.dataProvider()
        layerLines.startEditing()
        fList = list()
        fList.append(0)
        layerLines.dataProvider().deleteAttributes(fList)
        layerLines.renameAttribute(0, 'name')
        layerLines.renameAttribute(1, 'desc')

        # Reads header of report
        header = io.open(DATAPATH + '/pracovni/report_header.html', encoding='utf-8', mode='r').read()
        # Writes header to report
        f = io.open(DATAPATH + '/sektory/report.html', encoding='utf-8', mode='w')
        f.write(header)
        f.write('<h1>REPORT</h1>\n')
        f.write('<div class="flex-container">\n')

        self.removeExportedSectors()

        # Header for search time
        f.write('<div id="pdf" class="fixed400">\n')
        # f.write(u"\n<h2>Doba pro pátrání</h2>\n");
        # f.write(u"\n<p>Pro propátrání se počítá 3 hodiny jedním týmem</p>\n");
        f.write("\n<h2>" + QApplication.translate("Patrac", "GPX and PDF for search", None) + "</h2>\n");
        # f.write(u"\n<p>Pro propátrání referenční plochy (cca 30 ha) se počítá 3 hodiny jedním týmem.</p>\n");
        f.write('<p><a href="report.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a>&nbsp;<a href="gpx/all.gpx">'
                '<img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
        f.write('<p><a href="report.pdf_1.pdf">Detail ' + QApplication.translate("Patrac", 'S-W', None) + '&nbsp;<img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')
        f.write('<p><a href="report.pdf_2.pdf">Detail ' + QApplication.translate("Patrac", 'N-W', None) + '&nbsp;<img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')
        f.write('<p><a href="report.pdf_3.pdf">Detail ' + QApplication.translate("Patrac", 'N-E', None) + '&nbsp;<img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')
        f.write('<p><a href="report.pdf_4.pdf">Detail ' + QApplication.translate("Patrac", 'S-E', None) + '&nbsp;<img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')
        f.write('</div>\n')

        # Reads units report
        report_units = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='r').read()
        f.write(report_units)

        #styles
        styles = ""

        # crs for GPX
        crs = QgsCoordinateReferenceSystem("EPSG:4326")

        # Loop via features in sektory_group_selected
        features = provider.getFeatures()
        i = 1
        for feature in features:

            styles += "#a" + str(i) + "s {display: none;}\n"
            styles += "#a" + str(i) + "n {display: none;}\n"
            styles += "#a" + str(i) + "sc:checked ~ #a" + str(i) + "s {display: block;}\n"
            styles += "#a" + str(i) + "nc:checked ~ #a" + str(i) + "n {display: block;}\n"

            f.write('<div id="a' + str(i) + '" class="fixed400">\n')
            # Prints previously obtained area and label of the sector
            f.write("<p>" + QApplication.translate("Patrac", "SECTOR", None) + " " + feature['label'] + " (" + str(feature['area_ha']) + " ha)"
                    + '<label class="rolldown" for="a' + str(i) + 'sc">' + QApplication.translate("Patrac", "Types of terrain", None) + '</label></p>' + "\n")
            f.write('<input id="a' + str(i) + 'sc" type="checkbox" style="display: none">\n')

            # Reads sector report
            report = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='r').read()
            f.write(report)

            # Removes existing layer according to label in features
            # TODO - if the number of sectors is higher than in previous step, some of the layers are not removed
            # self.removeLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp")
            # self.setStyle(DATAPATH + "/sektory/shp/", feature['label'])
            # crs = QgsCoordinateReferenceSystem("EPSG:5514")
            # QgsVectorFileWriter.writeAsVectorFormat(layer, DATAPATH + "/sektory/shp/" + feature['label'] + ".shp",
            #                                        "utf-8", crs, "ESRI Shapefile")
            self.Utils.copyLayer(DATAPATH, feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()

            # report_units = io.open(DATAPATH + '/pracovni/report.html.units.' + str(i), encoding='utf-8',
            #                        mode='r').read()

            fList = list()
            fList.append(0)
            sector.dataProvider().deleteAttributes(fList)
            sector.renameAttribute(0, 'name')
            sector.renameAttribute(1, 'desc')
            fet.setAttributes([feature['label'], str(feature['area_ha']) + ' ha '])

            polygon = feature.geometry()
            line = QgsGeometry.fromPolylineXY(polygon.asMultiPolygon()[0][0])
            fet.setGeometry(line)
            providerSector.addFeatures([fet])
            providerLayerLines.addFeatures([fet])
            sector.commitChanges()

            if not sector.isValid():
                QgsMessageLog.logMessage("Sector " + feature['label'] + " se nepodařilo načíst", "Patrac")
            else:
                # Export do GPX
                # QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                #                                         "utf-8", crs, "GPX",
                #                                         datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                #                                         layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                                                        "utf-8", crs, "GPX",
                                                        layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsProject.instance().addMapLayer(sector, False)
                root = QgsProject.instance().layerTreeRoot()
                sektorygroup = root.findGroup("sektory")
                if sektorygroup is None:
                    sektorygroup = root.insertGroup(0, "sektory")
                sektorygroup.addLayer(sector)
                sektorygroup.setExpanded(False)

            # Writes link to PDF and GPX
            #f.write(u'<p><a href="pdf/' + feature['label'] + '.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a>&nbsp;<a href="gpx/'+ feature['label'] +'.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
            f.write('<p><a href="gpx/' + feature[
                        'label'] + '.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
            f.write("</div>\n")

            i += 1

        # writes all sectors to one file
        layerLines.commitChanges()
        # QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
        #                                         "utf-8", crs, "GPX",
        #                                         datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
        #                                         layerOptions=['FORCE_GPX_TRACK=YES'])
        QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
                                                "utf-8", crs, "GPX",
                                                layerOptions=['FORCE_GPX_TRACK=YES'])

        #Writes styles
        f.write("<style>")
        f.write(styles)
        f.write("</style>")

        # Writes footer
        footer = io.open(DATAPATH + '/pracovni/report_footer.html', encoding='utf-8', mode='r').read()
        f.write(footer)
        f.close()

        self.widget.setCursor(Qt.ArrowCursor)
        # Opens report in default browser
        if openReport:
            webbrowser.open("file://" + DATAPATH + "/sektory/report.html")
        return