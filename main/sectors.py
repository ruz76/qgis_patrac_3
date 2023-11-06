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
import collections
import json

from qgis.core import *
from qgis.gui import *

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

import processing, time

from shutil import copy

overrideLocale = bool(QSettings().value("locale/overrideFlag", False))
if not overrideLocale:
    localeFullName = QLocale.system().name()
else:
    localeFullName = QSettings().value("locale/userLocale", "")

if localeFullName == "cs":
    from .report_export_cs import *
else:
    if localeFullName == "uk":
        from .report_export_uk import *
    else:
        from .report_export_en import *

def get_label(f):
    if len(f['label']) >= 5:
        return f['label']
    if len(f['label']) == 4:
        return f['label'][:2] + "0" + f['label'][2:4]
    if len(f['label']) == 3:
        return f['label'][:2] + "00" + f['label'][2:3]
    if len(f['label']) == 2:
        return f['label'][:1] + "000" + f['label'][1:2]
    if len(f['label']) == 1:
        return f['label'] + "0000"

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

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        # Adds newly created layer with sectors to map
        self.Utils.addVectorLayer(DATAPATH + '/pracovni/sectors_zoned.shp', 'sektory zoned', 5514)

        #layer.dataProvider().forceReload()
        # layer.triggerRepaint()
        self.filterSectors(min, max)
        self.widget.setCursor(Qt.ArrowCursor)
        # self.recalculateSectors(False)
        return

    def filterSectors(self, min, max):
        QgsMessageLog.logMessage("Filtruji pro " + str(min) + " " + str(max), "Patrac")

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sectors_zoned.shp" in lyr.source():
                layer = lyr
                break

        provider = layer.dataProvider()
        features = provider.getFeatures()
        # save ids of selected sectors into file for future usage
        f = open(self.Utils.getDataPath() + '/pracovni/selectedSectors.txt', 'w')
        filter = "id IN ("
        try:
            for feature in features:
                if min == 0 and max > 80:
                    f.write(str(feature['id']) + "\n")
                    filter += "'" + str(feature['id']) + "', "
                else:
                    if str(feature['stats_min']) != 'NULL':
                        # QgsMessageLog.logMessage("Filtruji pro " + str(feature['stats_min']) + " " + str(feature['id']), "Patrac")
                        if min <= feature['stats_min'] and max >= feature['stats_min']:
                            # QgsMessageLog.logMessage("Filtruji pro " + str(feature['stats_min']) + " " + str(feature['id']), "Patrac")
                            f.write(str(feature['id']) + "\n")
                            filter += "'" + str(feature['id']) + "', "
        except Exception as e:
            print(e)
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                             QApplication.translate("Patrac", "Wrong installation. Call you administrator.", None))
            return

        filter = filter[:-2] + ")"
        f.close()

        self.Utils.removeLayer(self.Utils.getDataPath() + "/pracovni/sectors_zoned.shp")
        self.Utils.removeLayer(self.Utils.getDataPath() + "/pracovni/sektory_group.shp")
        self.Utils.addVectorLayerWithStyle(self.Utils.getDataPath() + "/pracovni/sektory_group.shp", "sektory", "sectors_single", 5514)

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        # Filter the layer
        layer.setSubsetString('')
        QgsMessageLog.logMessage("Filtruji " + filter, "Patrac")
        layer.setSubsetString(filter)
        layer.triggerRepaint()

    def getRegionDataPath(self):
        region = open(self.Utils.getDataPath() + '/config/region.txt', 'r').read()
        return self.Utils.getDataPath() + "/../../../" + region

    def getDuplicities(self, features):
        all = []
        for feature in features:
            all.append(feature['id'])
        duplicities = [item for item, count in collections.Counter(all).items() if count > 1]
        duplicities_dict = {}
        for d in duplicities:
            duplicities_dict.update({d:'A'})

        return duplicities_dict

    def increaseIdSize(self, layer):
        fields = layer.fields()
        for field in fields:
            if field.name() == 'id':
                field.setLength(25)

    def recalculateSectors(self, setLabels, setIds):
        """Recalculate areas of sectors and identifiers"""

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
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
        layer.commitChanges()
        duplicities = {}
        if setIds:
            duplicities = self.getDuplicities(features)

        sectorid = 0
        f = None
        if setLabels:
            f = open(DATAPATH + '/pracovni/listOfIds.txt', 'w')

        layer.startEditing()
        self.increaseIdSize(layer)
        layer.commitChanges()
        layer.triggerRepaint()

        layer.startEditing()
        features = provider.getFeatures()
        newIds = ""
        try:
            for feature in features:
                sectorid = sectorid + 1
                # Label is set to A and sequential number
                # Labels must be stable for whole search area, so only at the beginning are sectors labeled
                if setLabels:
                    #feature['label'] = 'A' + str(sectorid)
                    feature['label'] = str(feature['id'])

                # print("SET IDS" + str(setIds))
                if setIds:
                    if feature['id'] in duplicities:
                        current_duplicity = feature['id']
                        feature['id'] = str(feature['id']) + "_" + str(duplicities[feature['id']])
                        newIds += "'" + str(feature['id']) + "', "
                        feature['label'] = str(feature['id'])
                        order = duplicities[current_duplicity]
                        order = chr(ord(str(order)) + 1)
                        duplicities.update({current_duplicity:order})
                        print(str(feature['id']))

                # Area in hectares
                feature['area_ha'] = round(feature.geometry().area() / 10000)
                #print(str(feature['id']))
                if setLabels:
                    f.write(str(feature['id']) + "\n")
                layer.updateFeature(feature)
        except:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                    QApplication.translate("Patrac", "Wrong installation. Call you administrator.", None))
        layer.commitChanges()
        if layer.subsetString() != "" and newIds != "":
            layer.setSubsetString(layer.subsetString()[:-1] + ", " + newIds[:-2] + ")")
        layer.triggerRepaint()
        if setLabels:
            f.close()

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

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        sectorid = self.recalculateSectors(False, False)
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
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + str(feature['label']) + "_" + str(feature['id']) + ".gpx",
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

    def transformTrack(self, layer):
        params = {
            'INPUT' : layer,
            'TARGET_CRS': 'EPSG:5514',
            'OUTPUT': 'memory:transformed'
        }
        res = processing.run('qgis:reprojectlayer', params)
        return res['OUTPUT']

    def transformLine(self, line, source_crs):
        crs_src = QgsCoordinateReferenceSystem(source_crs)
        crs_dest = QgsCoordinateReferenceSystem(5514)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        return xform.transform(line)

    def getSectorsLayer(self):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break
        if layer is None:
            return None
        return layer

    def checkBeforeSplit(self, selected_sectors, selectedLayers):
        if selected_sectors is None or len(selected_sectors) < 1:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "You have to select at least one sector to split.", None))
            return
        if len(selectedLayers) < 1:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "You have to select line layer.", None))
            return
        if len(selectedLayers) > 1:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "You have to select line layer.", None))
            return
        if selectedLayers[0].type() != QgsMapLayerType.VectorLayer or selectedLayers[0].geometryType() != 1:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "Selected layer is not line layer.", None))
            return
        return "OK"

    def setAttributesAfterSplit(self, feature_source, feature_target, id, label):
        feature_target['id'] = id
        feature_target['label'] = label
        feature_target['area_ha'] = round(feature_target.geometry().area() / 10000)
        feature_target['typ'] = feature_source['typ']
        feature_target['stav'] = feature_source['stav']
        feature_target['prostredky'] = feature_source['prostredky']

    def getDistanceToExtend(self, pointxy, sector_geometry):
        point_geometry = QgsGeometry.fromPointXY(pointxy)
        if point_geometry.within(sector_geometry):
            return 1000
        else:
            return 0

    def getExtendedLineGeometry(self, line, sector_geometry):
        line_geometry = line.geometry()
        line_geometry.convertToSingleType()
        polylineXY = line_geometry.asPolyline()
        polyline = []
        for ptXY in polylineXY:
            pt = QgsPoint(ptXY)
            polyline.append(pt)
        ls = QgsLineString(polyline)
        ls.extend(self.getDistanceToExtend(polylineXY[0], sector_geometry), self.getDistanceToExtend(polylineXY[len(polylineXY) - 1], sector_geometry))
        polylineXY = []
        for pt in ls:
            ptXY = QgsPointXY(pt)
            polylineXY.append(ptXY)
        return polylineXY

    def splitByLine(self):
        self.widget.setCursor(Qt.WaitCursor)
        sectors_layer = self.getSectorsLayer()
        selected_sectors = sectors_layer.selectedFeatures()
        selectedLayers = self.iface.layerTreeView().selectedLayers()
        if self.checkBeforeSplit(selected_sectors, selectedLayers) is None:
            return
        layer_line = selectedLayers[0]
        features = layer_line.selectedFeatures()
        if len(features) != 1:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "You have to select just one line.", None))
            return
        selectid = [features[0].id()]
        if selectedLayers[0].crs().authid() != "EPSG:5514":
            layer_line = self.transformTrack(layer_line)
            layer_line.select(selectid)
        features = layer_line.selectedFeatures()
        provider_sectors_layer = sectors_layer.dataProvider()
        sectors_layer.startEditing()
        newIds = ""
        lastsectorid = self.Utils.getLastSectorId()
        for sector in selected_sectors:
            sector_geometry = sector.geometry()
            for line in features:
                ls = self.getExtendedLineGeometry(line, sector_geometry)
                output = sector_geometry.splitGeometry(ls, False)
                if len(output[1]) > 0:
                    sector.setGeometry(sector_geometry)
                    id = lastsectorid + 1
                    label = sector['label']
                    newIds += "'" + str(id) + '_A' + "', "
                    self.setAttributesAfterSplit(sector, sector, id, label + '_A')
                    sectors_layer.updateFeature(sector)
                    cur_sub_id = 'B'
                    for o in output[1]:
                        feature = QgsFeature(sector)
                        feature.setGeometry(o)
                        id += 1
                        self.setAttributesAfterSplit(sector, feature, id, label + '_' + cur_sub_id)
                        newIds += "'" + str(id) + '_' + cur_sub_id + "', "
                        provider_sectors_layer.addFeatures([feature])
                        cur_sub_id = chr(ord(cur_sub_id) + 1)
                    self.Utils.writeLastSectorId(id)
                else:
                    QMessageBox.information(None, QApplication.translate("Patrac", "ERROR:", None), QApplication.translate("Patrac", "Can not split.", None))
        sectors_layer.commitChanges()
        if sectors_layer.subsetString() != "" and newIds != "":
            sectors_layer.setSubsetString(sectors_layer.subsetString()[:-1] + "," + newIds[:-2] + ")")
        sectors_layer.triggerRepaint()
        self.widget.setCursor(Qt.ArrowCursor)

    def createCregion(self, extentItems):
        DATA_PATH = self.Utils.getDataPath()
        data = {
            "type": "FeatureCollection",
            "name": "region",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::5514" } },
            "features": [
                { "type": "Feature", "properties": { "name": "null" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ int(extentItems[0]), int(extentItems[1]) ], [ int(extentItems[2]), int(extentItems[1]) ], [ int(extentItems[2]), int(extentItems[3]) ], [ int(extentItems[0]), int(extentItems[3]) ], [ int(extentItems[0]), int(extentItems[1]) ] ] ] } }
            ]
        }
        with open(DATA_PATH + "/pracovni/cregion.geojson", "w+") as f:
            json.dump(data, f)

    def addVectorLayerForSplitByLine(self, name, label):
        DATA_PATH = self.Utils.getDataPath()
        if os.path.exists(DATA_PATH + "/pracovni/" + name + ".prj"):
            os.remove(DATA_PATH + "/pracovni/" + name + ".prj")
        self.Utils.addVectorLayerWithStyle(DATA_PATH + "/pracovni/" + name + ".shp", label, name, 5514)

    def addVectorsForSplitByLine(self):
        self.widget.setCursor(Qt.WaitCursor)
        self.addVectorLayerForSplitByLine("vodtok", "Vodní toky")
        self.addVectorLayerForSplitByLine("cesta", "Cesty")
        self.addVectorLayerForSplitByLine("lespru", "Průseky")
        self.widget.setCursor(Qt.ArrowCursor)

    def rewriteSelectedSectors(self):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break
        crs = QgsCoordinateReferenceSystem("EPSG:5514")
        QgsVectorFileWriter.writeAsVectorFormat(layer, self.Utils.getDataPath() + "/pracovni/sektory_group_selected.shp",
                                                "utf-8", crs, "ESRI Shapefile")

    def writeSectorHtml(self, report, feature, extent_5514):
        srs = self.canvas.mapSettings().destinationCrs()
        crs_src = QgsCoordinateReferenceSystem(5514)
        crs_dest = QgsCoordinateReferenceSystem(srs)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        extent = xform.transform(extent_5514)
        project = QgsProject.instance()
        layout = project.layoutManager().layoutByName("Basic")
        maps = [item for item in list(layout.items()) if
                item.type() == QgsLayoutItemRegistry.LayoutMap and item.scene()]
        composer_map = maps[0]
        extent.scale(1.1)
        composer_map.zoomToExtent(extent)
        extent = composer_map.extent()
        scale = 10
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        with open(DATAPATH + '/sektory/html/' + str(feature['id']) + '.html', 'w+') as f:
            # print('*****' + feature['id'] + '*****')
            f.write('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"></head><body>')
            f.write("<h1>" + QApplication.translate("Patrac", "SECTOR", None) + " " + feature['label'] + " (" + str(feature['area_ha']) + " ha)</h1>" + "\n")
            f.write("<h2>" + QApplication.translate("Patrac", "Map lists where the sector is present", None) + "</h2>")
            widthmax = (271.816 * scale) / 0.64
            heightmax = (177.272 * scale) / 0.64
            widthmap = extent.width()
            heightmap = extent.height()
            cols = int(widthmap / widthmax) + 1 # we need to handle round - may use roundup ot increase number of cols by 1
            rows = int(heightmap / heightmax) + 1 # we need to handle round - may use roundup ot increase number of cols by 1
            for row in range(rows):
                for col in range(cols):
                    rect = QgsRectangle(extent.xMinimum() + (col * widthmax),
                                        extent.yMaximum() - (row * heightmax),
                                        extent.xMinimum() + (col * widthmax) + widthmax,
                                        extent.yMaximum() - (row * heightmax) - heightmax)
                    geom = feature.geometry()
                    geom.transform(xform)
                    if geom.intersects(rect):
                        f.write('<a href="../' + str(scale) + '_report_' + str(row) + '_' + str(col) + '.pdf">' + str(row) + '-' + str(col) + '.pdf</a>\n')

            f.write("<h2>" + QApplication.translate("Patrac", "GPS file with drawn sector", None) + "</h2>")
            f.write('<a href="../gpx/' + str(feature['label']) + "_" + str(feature['id']) + '.gpx">' + str(feature['label']) + '.gpx</a>\n')
            f.write("</body></html>")

    def fixUt(self, ut):
        if ut == 0:
            print("The unit speed value is set to 0, this is not correct. Returning 1.")
            return 1
        else:
            return ut

    def getReportItems(self, feature):
        # Returns type of the search landuse based on landuse type
        # 1 volný schůdný bez porostu
        # 2 volný schůdný s porostem
        # 3 volný obtížně schůdný
        # 4 porost lehce průchozí
        # 5 porost obtížně průchozí
        # 6 zastavěné území měst a obcí
        # 7 městské parky a hřiště s pohybem osob
        # 8 městské parky a hřiště bez osob
        # 9 vodní plocha
        # 10 ostatní plochy
        types = [
            ['ODPOCI', 'OSPLSI', 'TRTRPO'],
            ['ORNAPU', 'SADZAH'],
            ['KOLEJI', 'POTELO', 'SKLADK'],
            ['LPSTROM', 'VINICE', 'CHMELN'],
            ['LPKOSO', 'LPKROV', 'MAZCHU'],
            ['AREZAS', 'ARUCZA', 'HRBITO', 'PRSTPR', 'ROZTRA', 'ROZZRI', 'ULOMIS', 'USNAOD', 'INTRAV'],
            ['ZAHPAR'],
            [],
            ['VODPLO'],
            ['ELEKTR', 'LETISTE', 'OTHER'],
        ]
        selected_type = 10
        id = 1
        for type in types:
            if feature['typ'] in type:
                selected_type = id
            id += 1
        stats = str(selected_type) + '||' + str(feature['area_ha'] * 10000) + '|100%'
        return [stats]

    def getMostCommonType(self, types):
        selected_type = 0
        selected_value = 0
        id = 0
        for type in types:
            if type > selected_value:
                selected_type = id
                selected_value = type
            id += 1
        return selected_type

    def calculateFeaturesReport(self, features):
        # Sets area of areas to zero
        SUM_P1 = 0
        SUM_P2 = 0
        SUM_P3 = 0
        SUM_P4 = 0
        SUM_P5 = 0
        SUM_P6 = 0
        SUM_P7 = 0
        SUM_P8 = 0
        SUM_P9 = 0
        SUM_P10 = 0
        i = 1
        DATAPATH = self.Utils.getDataPath()
        PLUGIN_PATH = self.Utils.getPluginPath()
        system = "win"
        if sys.platform.startswith('linux'):
            system = 'linux'
        for feature in features:
            f = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='w')
            # Sets areas of types of areas to zero
            # TODO - vyjasnit zarazeni typu + mozna pouzit i letecke snimky - nejaká jednoduchá automaticka rizena klasifikace
            P1 = 0  # volny schudny bez porostu (louky, pole ) - nejsem schopen zatim z dat identifikovat, mozna dle data patrani, v zime bude pole bez porostu a louka asi taky
            P2 = 0  # volny schudny s porostem (louky, pole ) - zatim tedy bude vse s porostem
            P3 = 0  # volny obtizne schudny (hory, skaly, lomy) - v prostoru mam lomy, skaly asi taky nejsem zatim schopen identifikovat
            P4 = 0  # porost lehce pruchozi (les bez prekazek) - asi vsechn les, kde neni krovi
            P5 = 0  # porost obtizne pruchozi (houstiny, skaly) - asi les s krovinami
            P6 = 0  # zastavene uzemi mest a obci
            P7 = 0  # mestske parky a hriste s pohybem osob - pohyb osob nejsem schopen posoudit, tedy asi co je zahrada bude bez pohybu a co je park bude s pohybem
            P8 = 0  # mestske parky a hriste bez osob
            P9 = 0  # vodni plocha
            P10 = 0  # ostatni

            REPORTITEMS = self.getReportItems(feature)

            # Decides for each type of area from REPORT in which category belongs
            try:
                for REPORTITEM in REPORTITEMS:
                    REPORTITEMVALUES = REPORTITEM.split('|')
                    if REPORTITEMVALUES[0] == '1':
                        P1 = P1 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P1 = SUM_P1 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '2':
                        P2 = P2 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P2 = SUM_P2 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '3':
                        P3 = P3 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P3 = SUM_P3 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '4':
                        P4 = P4 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P4 = SUM_P4 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '5':
                        P5 = P5 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P5 = SUM_P5 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '6':
                        P6 = P6 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P6 = SUM_P6 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '7':
                        P7 = P7 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P7 = SUM_P7 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '8':
                        P8 = P8 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P8 = SUM_P8 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '9':
                        P9 = P9 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P9 = SUM_P9 + float(REPORTITEMVALUES[2])
                    if REPORTITEMVALUES[0] == '10':
                        P10 = P10 + float(REPORTITEMVALUES[3].split('%')[0])
                        SUM_P10 = SUM_P10 + float(REPORTITEMVALUES[2])
            except ValueError:
                print("The statistic for current sector is invalid, can not compute.")

            # Corect 100%
            if P1 > 100:
                P1 = 100
            if P2 > 100:
                P2 = 100
            if P3 > 100:
                P3 = 100
            if P4 > 100:
                P4 = 100
            if P5 > 100:
                P5 = 100
            if P6 > 100:
                P6 = 100
            if P7 > 100:
                P7 = 100
            if P8 > 100:
                P8 = 100
            if P9 > 100:
                P9 = 100
            if P10 > 100:
                P10 = 100

            # Writes output to the report
            # f.write(u'<div id="a' + str(i) + 's">\n')
            # f.write(u"<ul>\n")
            # f.write(u"<li>" + p1label + ": " + str(P1) + u" %</li>\n")
            # f.write(u"<li>" + p2label + ": " + str(P2) + u" %</li>\n")
            # f.write(u"<li>" + p3label + ": " + str(P3) + u" %</li>\n")
            # f.write(u"<li>" + p4label + ": " + str(P4) + u" %</li>\n")
            # f.write(u"<li>" + p5label + ": " + str(P5) + u" %</li>\n")
            # f.write(u"<li>" + p6label + ": " + str(P6) + u" %</li>\n")
            # f.write(u"<li>" + p7label + ": " + str(P7) + u" %</li>\n")
            # f.write(u"<li>" + p8label + ": " + str(P8) + u" %</li>\n")
            # f.write(u"<li>" + p9label + ": " + str(P9) + u" %</li>\n")
            # f.write(u"<li>" + p10label + ": " + str(P10) + u" %</li>\n")
            # f.write(u"</ul>\n")
            # f.write(u"</div>\n")

            p_labels = [p1label, p2label, p3label, p4label, p5label, p6label, p7label, p8label, p9label, p10label]
            p_values = [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10]
            most_common_type = self.getMostCommonType(p_values)
            f.write(u'<tr><td>' + feature['label'] + '</td><td>' + str(feature['area_ha']) + '</td><td>' + p_labels[most_common_type] + '</td>\n')
            f.write(u'<td><a href="gpx/' + str(feature['label']) + "_" + str(feature['id']) + '.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></td>\n')
            f.write(u'</tr>\n')
            f.close()

            i += 1

        # Sets area to ha
        SUM_P1 = SUM_P1 / float(10000)
        SUM_P2 = SUM_P2 / float(10000)
        SUM_P3 = SUM_P3 / float(10000)
        SUM_P4 = SUM_P4 / float(10000)
        SUM_P5 = SUM_P5 / float(10000)
        SUM_P6 = SUM_P6 / float(10000)
        SUM_P7 = SUM_P7 / float(10000)
        SUM_P8 = SUM_P8 / float(10000)
        SUM_P9 = SUM_P9 / float(10000)
        SUM_P10 = SUM_P10 / float(10000)

        f = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='w')

        # Reads numbers for existing search units from units.txt
        CUR_KPT = 0
        CUR_PT = 0
        CUR_VPT = 0

        fileInput = None
        settingsPath = PLUGIN_PATH + "/../../../patrac_settings"
        if system == 'win':
            fileInput = open(settingsPath + "/grass/units.txt", encoding='utf-8', mode="r")
        elif system == 'linux':
            fileInput = open(settingsPath + "/grass/units.txt", mode="r")

        i = 0
        for row in csv.reader(fileInput, delimiter=';'):
            # unicode_row = [x.decode('utf8') for x in row]
            unicode_row = row
            cur_count = int(unicode_row[0])
            if i == 0:  # Pes
                CUR_KPT = cur_count
            if i == 1:  # Rpjnice
                CUR_PT = cur_count
            if i == 5:  # Potápěč
                CUR_VPT = cur_count
            i = i + 1

        fileInput.close()


        f.write(u'<div id="areas" class="fixed400">\n')
        f.write(u"\n<h2>" + typesOfLanduse + "</h2>\n");
        f.write(u"<table>\n")
        if int(math.ceil(SUM_P1)) > 0:
            f.write(u"<tr><td>" + p1label + "</td><td>" + str(int(math.ceil(SUM_P1))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P2)) > 0:
            f.write(u"<tr><td>" + p2label + "</td><td>" + str(int(math.ceil(SUM_P2))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P3)) > 0:
            f.write(u"<tr><td>" + p3label + "</td><td>" + str(int(math.ceil(SUM_P3))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P4)) > 0:
            f.write(u"<tr><td>" + p4label + "</td><td>" + str(int(math.ceil(SUM_P4))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P5)) > 0:
            f.write(u"<tr><td>" + p5label + "</td><td>" + str(int(math.ceil(SUM_P5))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P6)) > 0:
            f.write(u"<tr><td>" + p6label + "</td><td>" + str(int(math.ceil(SUM_P6))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P7)) > 0:
            f.write(u"<tr><td>" + p7label + "</td><td>" + str(int(math.ceil(SUM_P7))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P8)) > 0:
            f.write(u"<tr><td>" + p8label + "</td><td>" + str(int(math.ceil(SUM_P8))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P9)) > 0:
            f.write(u"<tr><td>" + p9label + "</td><td>" + str(int(math.ceil(SUM_P9))) + u" ha</td></tr>\n")
        if int(math.ceil(SUM_P10)) > 0:
            f.write(u"<tr><td>" + p10label + "</td><td>" + str(int(math.ceil(SUM_P10))) + u" ha</td></tr>\n")
        f.write(u"</table>\n")
        f.write(u"</div>\n")

        fileInput = None
        unitsTimesPath = PLUGIN_PATH + "/../../../patrac_settings/grass/units_times.csv"
        if system == 'win':
            fileInput = open(unitsTimesPath, encoding='utf-8', mode="r")
        elif system == 'linux':
            fileInput = open(unitsTimesPath, mode="r")

        # Reads CSV and populates the array
        unitsTimes = []
        for row in csv.reader(fileInput, delimiter=';'):
            row_out = []
            for field in row:
                row_out.append(float(field))
            unitsTimes.append(row_out)

        KPT = SUM_P2 + SUM_P3 + SUM_P5
        KPT_PT = SUM_P1 + SUM_P4 + SUM_P8
        f.write(u'<div id="teams" class="fixed400">\n')
        f.write(u"<h2>" + handlersLabel + "</h2>\n")
        f.write(u"<p>" + areaForhandlersLabel + " " + str(int(math.ceil(KPT + KPT_PT))) + u" ha.\n")
        f.write(u"<p>" + availableLabel + " " + str(CUR_KPT) + u" " + handlersLabel2 + ".\n")
        P2_P3_P5_KPT = float(SUM_P2) / self.fixUt(unitsTimes[1][0]) + float(SUM_P3) / self.fixUt(unitsTimes[2][0]) + float(SUM_P5) / self.fixUt(unitsTimes[4][0])
        P1_P4_P8_KPT = float(SUM_P1) / self.fixUt(unitsTimes[0][0]) + float(SUM_P4) / self.fixUt(unitsTimes[3][0]) + float(SUM_P8) / self.fixUt(unitsTimes[7][0])
        if CUR_KPT > 0:
            f.write(u"<p>" + searchingForTime + " " + str(
                int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(CUR_KPT)))) + u" h.\n")

        if KPT_PT > 0:
            P1_P4_P8_PT = float(SUM_P1) / self.fixUt(unitsTimes[0][1]) + float(SUM_P4) / self.fixUt(unitsTimes[3][1]) + float(SUM_P8) / self.fixUt(unitsTimes[7][1])
            f.write(
                u"<p>" + handlersSubstitute + " " + str(int(math.ceil(KPT_PT))) + u" ha.\n")
        if (SUM_P2 + SUM_P1) > 0:
            f.write(u"<p>" + dronArea + " " + str(
                int(math.ceil(SUM_P2 + SUM_P1))) + u" ha.\n")

        PT = SUM_P6 + SUM_P7 + SUM_P10
        f.write(u"<h2>" + searchersLabel + "</h2>\n")
        f.write(u"<p>" + searchersArea + " " + str(round(PT)) + u" ha.\n")
        f.write(u"<p>" + availableLabel + " " + str(CUR_PT) + u" " + searchersLabel2 + ".\n")
        P6_P7_P10_PT = float(SUM_P6) / self.fixUt(unitsTimes[5][1]) + float(SUM_P7) / self.fixUt(unitsTimes[6][1]) + float(SUM_P10) / self.fixUt(unitsTimes[9][1])
        if CUR_PT > 0:
            f.write(u"<p>" + searchingForTime + " " + str(int(math.ceil(P6_P7_P10_PT / float(CUR_PT)))) + u" h.\n")
        else:
            f.write(u"<p>" + noSearchers + ".\n")

        if SUM_P9 > 0:
            f.write(u"<h2>" + diverLabel + "</h2>\n")
            f.write(u"<p>" + waterArea + " " + str(int(math.ceil(SUM_P9))) + u" ha.\n")
            if CUR_VPT > 0:
                P9_VPT = float(SUM_P9) / self.fixUt(unitsTimes[8][4])
                f.write(u"<p>" + availableLabel + " " + str(CUR_VPT) + u" " + diverLabel2 + ".\n")
                f.write(u"<p>" + searchingForTime + " " + str(int(math.ceil(P9_VPT / float(CUR_VPT)))) + u" h.\n")
            else:
                f.write(u"<p>" + noDivers + ".\n")

        f.write(u"</div>\n")

        maxtime = 3
        if os.path.isfile(settingsPath + "/grass/maxtime.txt"):
            try:
                maxtime = int(open(settingsPath + "/grass/maxtime.txt", 'r').read())
            except ValueError:
                maxtime = 3

        if maxtime <= 0:
            maxtime = 3

        f.write(u'<div id="time" class="fixed400">\n')
        f.write(u"<h2>" + timeLabel + "</h2>\n")
        f.write(u"\n<p>" + searchUntil + " " + str(int(maxtime)) + u" " + unitsNeeded + ":</p>\n")
        f.write(u"\n<ul>\n")
        f.write(u"\n<li>" + str(int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(maxtime)))) + u" " + handlersLabel2 + "</li>\n")
        f.write(u"\n<li>" + str(int(math.ceil((P6_P7_P10_PT) / float(maxtime)))) + u" " + searchersLabel2 + "</li>\n")
        if SUM_P9 > 0:
            f.write(u"\n<li>" + atLeastOneDiver + "</li>\n")
        if (SUM_P2 + SUM_P1) > 0:
            f.write(u"\n<li>" + atLeastOneDrone + "</li>\n")
        f.write(u"\n</ul>\n")
        f.write(u"</div>\n")

        f.close()

    def reportExportSectors(self, openReport, exportPDF):
        """Creates report and exports sectors to SHP and GPX"""

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        # print("Before recalculateSectors")
        # time.sleep(30)

        sectorid = self.recalculateSectors(False, False)

        self.widget.setCursor(Qt.WaitCursor)
        # exports curent layer to selected layer for GRASS GIS import

        # print("Before rewriteSelectedSectors")
        # time.sleep(30)
        self.rewriteSelectedSectors()

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        provider = layer.dataProvider()
        features = provider.getFeatures()

        LABELS = ""
        featuresCount = 0
        for feature in features:
            LABELS = LABELS + "!" + str(feature['label'])
            featuresCount += 1

        # Loop via features in sektory_group_selected
        features = provider.getFeatures()
        features = sorted(features, key=get_label)

        self.calculateFeaturesReport(features)

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
        # f.write('<p><a href="report.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a>&nbsp;<a href="gpx/all.gpx">'
        #         '<img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
        f.write('<a href="gpx/all.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
        f.write('<p>' + QApplication.translate("Patrac", "Overall view", None) + '</p>')
        # f.write('<p><a href="report.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a></p>\n')
        f.write('<!--tilemapall-->')
        f.write('<p>1:25 000</p>')
        f.write('<!--tilemap25-->')
        f.write('<p>1:10 000</p>')
        f.write('<!--tilemap10-->')
        f.write('<p>' + QApplication.translate("Patrac", "If you do not see links to PDF files for print, the files were not generated. Please use checkbox on last card in the guide and show report again.", None) + '</p>')
        f.write('</div>\n')

        # Reads units report
        try:
            report_units = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='r').read()
            f.write(report_units)
        except:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "Wrong installation. Call you administrator.", None))
            return

        # crs for GPX
        crs = QgsCoordinateReferenceSystem("EPSG:4326")

        i = 1
        copy(self.pluginPath + "/templates/projekt/sektory/shp/sectors.gpkg", DATAPATH + "/sektory/shp/sectors.gpkg")

        f.write('<div class="fixed500">')
        f.write("<h2>" + QApplication.translate("Patrac", "SECTOR", None) + "</h2>")
        f.write("<table border><tr><th>" + QApplication.translate("Patrac", "SECTOR", None) + "</th><th>ha</th><th>" + QApplication.translate("Patrac", "Types of terrain", None) + '</th><th>GPS</th></th>' + "\n")

        self.widget.createProgressBar(QApplication.translate("Patrac", 'Exporting GPX for each sector', None))
        step = 100 / featuresCount
        progress = 0
        self.widget.setProgress(0)
        for feature in features:

            # Reads sector report
            report = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='r').read()
            f.write(report)
            self.writeSectorHtml(report, feature, layer.extent())

            sector = QgsVectorLayer("LineString?crs=epsg:5514", feature['label'], "memory")

            # self.Utils.copyLayer(DATAPATH, feature['label'])
            # sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()

            nameField = QgsField('name', QVariant.String)
            descField = QgsField('desc', QVariant.String)
            sector.dataProvider().addAttributes([nameField, descField])
            sector.updateFields()

            fet.setAttributes([feature['label'], str(feature['area_ha']) + ' ha '])

            polygon = feature.geometry()
            line = QgsGeometry.fromPolylineXY(polygon.asMultiPolygon()[0][0])
            fet.setGeometry(line)
            providerSector.addFeatures([fet])
            providerLayerLines.addFeatures([fet])
            sector.commitChanges()

            if not sector.isValid():
                QgsMessageLog.logMessage("Can not read sector " + feature['label'], "Patrac")
            else:
                # Export do GPX
                # QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                #                                         "utf-8", crs, "GPX",
                #                                         datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                #                                         layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + str(feature['label']) + "_" + str(feature['id']) + ".gpx",
                                                        "utf-8", crs, "GPX",
                                                        layerOptions=['FORCE_GPX_TRACK=YES'])


                gpkgPath = DATAPATH + "/sektory/shp/sectors.gpkg"
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                options.layerName = feature['label']
                options.fileEncoding="UTF-8"
                options.destCRS=sector.crs()
                options.driverName="GPKG"
                QgsVectorFileWriter.writeAsVectorFormat(sector, gpkgPath, options)
                sector_from_gpkg = QgsVectorLayer(DATAPATH + "/sektory/shp/sectors.gpkg|layername=" + feature['label'], feature['label'], "ogr")
                sector_from_gpkg.loadNamedStyle(self.pluginPath + "/templates/projekt/sektory/shp/style.qml")
                # TODO - from settings
                crs = QgsCoordinateReferenceSystem(5514)
                sector_from_gpkg.setCrs(crs)

                QgsProject.instance().addMapLayer(sector_from_gpkg, False)
                root = QgsProject.instance().layerTreeRoot()
                sektorygroup = root.findGroup("sektory")
                if sektorygroup is None:
                    sektorygroup = root.insertGroup(0, "sektory")
                sektorygroup.addLayer(sector_from_gpkg)
                sektorygroup.setExpanded(False)
            progress += step
            self.widget.setProgress(round(progress))
            i += 1

        self.widget.setProgress(99)

        f.write("</table></div>")

        # writes all sectors to one file
        layerLines.commitChanges()
        # QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
        #                                         "utf-8", crs, "GPX",
        #                                         datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
        #                                         layerOptions=['FORCE_GPX_TRACK=YES'])
        QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
                                                "utf-8", crs, "GPX",
                                                layerOptions=['FORCE_GPX_TRACK=YES'])

        # Writes footer
        with open(DATAPATH + '/pracovni/report_footer.html', encoding='utf-8', mode='r') as foot:
            footer = foot.read()
        f.write(footer)
        f.close()

        self.widget.setProgress(100)
        self.widget.clearMessageBar()

        # exports overall map with all sectors to PDF
        if exportPDF:
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

        self.widget.setCursor(Qt.ArrowCursor)
        # Opens report in default browser
        if openReport:
            webbrowser.open("file://" + DATAPATH + "/sektory/report.html")
        return

    def createIndividualSectorPdf(self):

        DATAPATH = self.Utils.getDataPath()

        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        provider = layer.dataProvider()
        features = provider.getFeatures()

        featuresCount = 0
        for feature in features:
            featuresCount += 1

        # TODO change to something interesting
        if featuresCount > 0:
            reply = QMessageBox.question(None,
                                         QApplication.translate("Patrac", 'Step', None), QApplication.translate("Patrac", 'Generating of PDFs for individual sectors can take about 10 seconds for each sector. Do you want to continue? Number of sectors: ' + str(featuresCount), None),
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.No:
                return

        self.widget.createProgressBar(QApplication.translate("Patrac", 'Exporting PDFs for each sector', None))
        step = 100 / featuresCount
        progress = 0
        self.widget.setProgress(round(progress))
        features = provider.getFeatures()
        srs = self.canvas.mapSettings().destinationCrs()
        current_crs = srs.authid()
        needsToBeTransformed = True
        if current_crs == "EPSG:5514":
            needsToBeTransformed = False
        else:
            srs = self.canvas.mapSettings().destinationCrs()
            crs_src = QgsCoordinateReferenceSystem(5514)
            crs_dest = QgsCoordinateReferenceSystem(srs)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())

            # extent = xform.transform(layer.extent())
            # self.Printing.exportPDF(extent, DATAPATH + "/sektory/")

        for feature in features:
            bbox = feature.geometry().boundingBox()
            # print(str(bbox))
            if needsToBeTransformed:
                extent = xform.transform(bbox)
            else:
                extent = bbox
            scale = 1.2
            if feature.geometry().area() < 100000:
                scale = (100000 / feature.geometry().area()) + 0.2
            self.Printing.export(extent, DATAPATH + "/sektory/pdf/" + feature['label'] + "_" + str(feature['id']) + ".pdf", scale)
            progress += step
            self.widget.setProgress(round(progress))

        self.widget.setProgress(100)
        self.widget.clearMessageBar()
        webbrowser.open("file://" + DATAPATH + "/sektory/pdf/")
