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

import processing

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

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/export.py", "Patrac")
        self.widget.setCursor(Qt.WaitCursor)

        initialExtent = open(self.Utils.getDataPath() + '/config/extent.txt', 'r').read()
        initialExtentItems = initialExtent.split(" ")

        CMINX = self.canvas.extent().xMinimum()
        CMINY = self.canvas.extent().yMinimum()
        CMAXX = self.canvas.extent().xMaximum()
        CMAXY = self.canvas.extent().yMaximum()

        source_crs = self.canvas.mapSettings().destinationCrs()
        current_crs = source_crs.authid()
        if current_crs != "EPSG:5514":
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            minJTSK = transform.transform(float(CMINX), float(CMINY))
            CMINX = minJTSK.x()
            CMINY = minJTSK.y()
            maxJTSK = transform.transform(float(CMAXX), float(CMAXY))
            CMAXX = maxJTSK.x()
            CMAXY = maxJTSK.y()

        XMIN = str(CMINX) \
            if CMINX < float(initialExtentItems[0]) else initialExtentItems[0]
        YMIN = str(CMINY) \
            if CMINY < float(initialExtentItems[1]) else initialExtentItems[1]
        XMAX = str(CMAXX) \
            if CMAXX > float(initialExtentItems[2]) else initialExtentItems[2]
        YMAX = str(CMAXY) \
            if CMAXY > float(initialExtentItems[3]) else initialExtentItems[3]

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
        print(self.Utils.getDataPath() + "/pracovni/sektory_group_to_append.shp")
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
                print("ADD " + str(feature['id']))
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
                    newIds += "'" + feature['id'] + "', "
                    feature['label'] = str(feature['id'])
                    order = duplicities[current_duplicity]
                    order = chr(ord(str(order)) + 1)
                    duplicities.update({current_duplicity:order})
                    print(feature['id'])

            # Area in hectares
            feature['area_ha'] = round(feature.geometry().area() / 10000)
            #print(str(feature['id']))
            if setLabels:
                f.write(str(feature['id']) + "\n")
            layer.updateFeature(feature)
        layer.commitChanges()
        if layer.subsetString() != "" and newIds != "":
            layer.setSubsetString(layer.subsetString()[:-1] + ", " + newIds[:-2] + ")")
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

    def setAttributesAfterSplit(self, feature_source, feature_target, id):
        feature_target['id'] = id
        feature_target['label'] = id
        feature_target['area_ha'] = round(feature_target.geometry().area() / 10000)
        feature_target['cat'] = feature_source['cat']
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
        for sector in selected_sectors:
            sector_geometry = sector.geometry()
            for line in features:
                ls = self.getExtendedLineGeometry(line, sector_geometry)
                output = sector_geometry.splitGeometry(ls, False)
                if len(output[1]) > 0:
                    sector.setGeometry(sector_geometry)
                    id = sector['id']
                    newIds += "'" + id + '_A' + "', "
                    self.setAttributesAfterSplit(sector, sector, id + '_A')
                    sectors_layer.updateFeature(sector)
                    cur_sub_id = 'B'
                    for o in output[1]:
                        feature = QgsFeature(sector)
                        feature.setGeometry(o)
                        self.setAttributesAfterSplit(sector, feature, id + '_' + cur_sub_id)
                        newIds += "'" + id + '_' + cur_sub_id + "', "
                        provider_sectors_layer.addFeatures([feature])
                        cur_sub_id = chr(ord(cur_sub_id) + 1)
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
        self.Utils.addVectorLayerWithStyle(DATA_PATH + "/pracovni/" + name + ".shp", label, name)

    def addVectorsForSplitByLine(self):
        self.widget.setCursor(Qt.WaitCursor)
        DATA_PATH = self.Utils.getDataPath()
        KRAJ_DATA_PATH = DATA_PATH + "/../../"
        initialExtent = open(self.Utils.getDataPath() + '/config/extent.txt', 'r').read()
        initialExtentItems = initialExtent.split(" ")
        self.createCregion(initialExtentItems)
        XMIN = initialExtentItems[0]
        YMIN = initialExtentItems[1]
        XMAX = initialExtentItems[2]
        YMAX = initialExtentItems[3]
        # GRASS exports to SHP
        if sys.platform.startswith('win'):
            p = subprocess.Popen(
                (self.pluginPath + "/grass/run_export_vectors.bat", KRAJ_DATA_PATH, self.pluginPath, XMIN, YMIN,
                 XMAX, YMAX, DATA_PATH))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_export_vectors.sh", KRAJ_DATA_PATH, self.pluginPath, XMIN, YMIN,
                                  XMAX, YMAX, DATA_PATH))
            p.wait()

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
            f.write(report)
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
            f.write('<a href="../gpx/' + feature['id'] + '.gpx">' + feature['id'] + '.gpx</a>\n')
            f.write("</body></html>")

    def reportExportSectors(self, openReport, exportPDF):
        """Creates report and exports sectors to SHP and GPX"""

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Wrong project.", None))
            return

        sectorid = self.recalculateSectors(False, False)

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
            self.writeSectorHtml(report, feature, layer.extent())

            self.Utils.copyLayer(DATAPATH, feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()

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
                QgsMessageLog.logMessage("Can not read sector " + feature['label'], "Patrac")
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
