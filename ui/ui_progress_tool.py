# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import QSettings

from qgis.core import *
from qgis.gui import *

import processing
import sys

from .ui_sector import Ui_Sector

class ProgressMapTool(QgsMapTool):
    """Map tool for click in the map"""

    def __init__(self, canvas, iface):
        self.canvas = canvas
        QgsMapTool.__init__(self, self.canvas)
        self.reset()
        self.DATAPATH = ''
        self.unit = 0
        self.type = ''
        self.attribute = 3
        self.layer = None
        self.value = 50
        self.numberOfSearchers = 10
        self.pluginPath = ''
        self.iface = iface
        self.dialog = Ui_Sector()

    def reset(self):
        self.point = None

    def setPluginPath(self, pluginPath):
        self.pluginPath = pluginPath

    def setDataPath(self, DATAPATH):
        self.DATAPATH = DATAPATH

    def setUnit(self, unit):
        self.unit = unit

    def setType(self, type):
        self.type = type

    def setLayer(self, layer):
        self.layer = layer

    def setValue(self, value):
        try:
            self.value = int(value)
        except:
            self.value = 50

    def setNumberOfSearchers(self, numberOfSearchers):
        try:
            self.numberOfSearchers = int(numberOfSearchers)
        except:
            self.numberOfSearchers = 0

    def setAttribute(self, attribute):
        self.attribute = attribute

    def canvasPressEvent(self, e):
        # Right click
        if e.button() == 2:
            self.point = self.toMapCoordinates(e.pos())
            srs = self.canvas.mapSettings().destinationCrs()
            current_crs = srs.authid()
            if current_crs != "EPSG:5514":
                srs = self.canvas.mapSettings().destinationCrs()
                crs_src = QgsCoordinateReferenceSystem(srs)
                crs_dest = QgsCoordinateReferenceSystem(5514)
                xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
                self.point = xform.transform(self.point)

    def transformTrack(self, layer):
        params = {
            'INPUT' : layer,
            'TARGET_CRS': 'EPSG:5514',
            'OUTPUT': 'memory:transformed'
        }
        res = processing.run('qgis:reprojectlayer', params)
        return res['OUTPUT']

    def getLayerFeatures(self, layer):
        provider = layer.dataProvider()
        return provider.getFeatures()

    def getClosestSegment(self, features, geom):
        currentGeom = None
        currentDistance = sys.float_info.max
        for feature in features:
            geom2 = feature.geometry()
            dist = geom2.distance(geom)
            if dist < currentDistance:
                currentDistance = dist
                currentGeom = geom2

        currentGeom.convertToSingleType()
        polyline = currentGeom.asPolyline()
        line = QgsLineString(QgsPoint(polyline[0]), QgsPoint(polyline[1]))
        line.extend(200, 200)
        line = QgsGeometry.fromWkt(line.asWkt())
        return line

    def getSideBuffer(self, layer, side, distance):
        params = {
            'INPUT' : layer,
            'DISTANCE': distance,
            'SIDE': side,
            'JOIN_STYLE': 0,
            'OUTPUT': 'memory:sidebuffer'
        }
        res = processing.run('qgis:singlesidedbuffer', params)
        return res['OUTPUT']

    def unionLayers(self, layer1, layer2):
        params = {
            'INPUT' : layer1,
            'OVERLAY': layer2,
            'OUTPUT': 'memory:union'
        }
        res = processing.run('qgis:union', params)
        return res['OUTPUT']

    def dissolveLayer(self, layer):
        params = {
            'INPUT' : layer,
            'OUTPUT': 'memory:dissolve'
        }
        res = processing.run('qgis:dissolve', params)
        return res['OUTPUT']

    def getUnionBuffer(self, layer1, layer2, dir1, dir2, dist1, dist2):
        buffer1_A = self.getSideBuffer(layer1, dir1, dist2)
        buffer2_A = self.getSideBuffer(layer1, dir2, dist1)
        buffer1_B = self.getSideBuffer(layer2, dir2, dist2)
        buffer2_B = self.getSideBuffer(layer2, dir1, dist1)
        tmp_layer = self.unionLayers(buffer1_A, buffer2_A)
        tmp_layer = self.unionLayers(tmp_layer, buffer1_B)
        tmp_layer = self.unionLayers(tmp_layer, buffer2_B)
        tmp_layer = self.dissolveLayer(tmp_layer)
        features = self.getLayerFeatures(tmp_layer)
        geom = None
        for feature in features:
            geom = feature.geometry()
        return geom
        # QgsProject.instance().addMapLayer(tmp_layer)
        # QgsProject.instance().addMapLayer(right_buffer2)

    def analyzeTrackDouble(self, layers, sector):
        layer1 = self.transformTrack(layers[0])
        layer2 = self.transformTrack(layers[1])
        features1 = self.getLayerFeatures(layer1)
        features2 = self.getLayerFeatures(layer2)
        for feature in features1:
            geom = feature.geometry()
            if geom.intersects(sector.geometry()):
                # we are inside sector
                geom.convertToSingleType()
                polyline = geom.asPolyline()
                if len(polyline) > 1:
                    # print(polyline)
                    line = QgsLineString(QgsPoint(polyline[0]), QgsPoint(polyline[1]))
                    # print(line)
                    line.extend(0, 200)
                    # print(line)
                    line = QgsGeometry.fromWkt(line.asWkt())
                    line.rotate(90, polyline[4])
                    # print(line)
                    line2 = self.getClosestSegment(features2, line)
                    buffer_size = float((self.numberOfSearchers * self.value * 2) - (self.value * 2)) / float(2)
                    if line.intersects(line2):
                        return self.getUnionBuffer(layer1, layer2, 1, 0, self.value, buffer_size)
                    else:
                        return self.getUnionBuffer(layer1, layer2, 0, 1, buffer_size, self.value)
                else:
                    # can not determine the order of tracks
                    return None
        return None

    def analyzeTrackSingle(self, features, sector):
        crs_src = QgsCoordinateReferenceSystem(4326)
        crs_dest = QgsCoordinateReferenceSystem(5514)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        buffer_union = None
        for feature in features:
            geom = feature.geometry()
            geom.transform(xform)
            if geom.intersects(sector.geometry()):
                geom = geom.buffer(self.value, 2)
                if buffer_union is None:
                    buffer_union = geom
                else:
                    buffer_union = buffer_union.combine(geom)
        return buffer_union

    def analyzeTrack(self, sector):
        selectedLayers = self.iface.layerTreeView().selectedLayers()
        if len(selectedLayers) < 1:
            QMessageBox.information(None, self.tr("CHYBA:"), self.tr("You have to select track."))
            return
        buffer_union = None
        if self.unit == 2:
            if int(self.numberOfSearchers) < 3:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("You have to enter number of persons including siders."))
                return
            if len(selectedLayers) != 2:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("You have to select two tracks."))
                return
            if selectedLayers[0] != None and selectedLayers[0].crs().authid() != "EPSG:4326" and selectedLayers[1] != None and selectedLayers[1].crs().authid() != "EPSG:4326":
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Selected layers are not tracks."))
                return
            if selectedLayers[0].type() != QgsMapLayerType.VectorLayer or selectedLayers[0].geometryType() != 1 or selectedLayers[1].type() != QgsMapLayerType.VectorLayer or selectedLayers[1].geometryType() != 1:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Selected layers are not tracks."))
                return
            buffer_union = self.analyzeTrackDouble(selectedLayers, sector)
        else:
            # print(selectedLayers[0].geometryType())
            # print(selectedLayers[0].crs().authid())
            # print(selectedLayers[0].type())
            if len(selectedLayers) != 1:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Yout have to select just one layer."))
                return
            if selectedLayers[0] != None and selectedLayers[0].crs().authid() != "EPSG:4326":
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Selected layer is not track."))
                return
            if selectedLayers[0].type() != QgsMapLayerType.VectorLayer or selectedLayers[0].geometryType() != 1:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Selected layer is not track."))
                return
            provider = selectedLayers[0].dataProvider()
            features = provider.getFeatures()
            buffer_union = self.analyzeTrackSingle(features, sector)
            if buffer_union == None:
                QMessageBox.information(None, self.tr("CHYBA:"), self.tr("Select track does not have data to analyze. Select another track or unit."))
                return

        difference = sector.geometry().difference(buffer_union)
        uri = "multipolygon?crs=epsg:5514"
        layer = QgsVectorLayer(uri, sector['label'], "memory")
        layer.startEditing()
        provider = layer.dataProvider()
        fet = QgsFeature()
        fet.setGeometry(difference)
        provider.addFeatures([fet])
        layer.commitChanges()
        layer.updateExtents()
        layer.loadNamedStyle(self.pluginPath + '/styles/not_searched.qml')
        layer.triggerRepaint()
        QgsProject.instance().addMapLayer(layer)

    def canvasReleaseEvent(self, e):
        # Right click
        print(e.button())
        print(self.point)
        print(self.layer)
        print(self.attribute)
        if e.button() == 2 and self.point is not None and self.layer is not None:
            provider = self.layer.dataProvider()
            features = provider.getFeatures()
            if self.attribute > -1:
                subsetString = self.layer.subsetString()
                self.layer.setSubsetString("")
                self.layer.startEditing()
            try:
                for feature in features:
                    # print(feature.geometry())
                    if feature.geometry().contains(self.point):
                        QgsMessageLog.logMessage("RE 5", "Patrac")
                        if self.attribute > -1:
                            # print(self.type)
                            # feature.setAttribute(self.attribute, self.type)
                            # if self.type == 1:
                            #     feature.setAttribute(self.attribute + 1, self.unit)
                            self.dialog.setFeature(feature)
                            self.dialog.exec_()
                            if self.dialog.getAccepted():
                                self.layer.updateFeature(feature)
                                self.layer.commitChanges()
                                self.layer.setSubsetString(subsetString)
                        else:
                            self.analyzeTrack(feature)
                        break
            except Exception as e:
                self.layer.setSubsetString(subsetString)
                QgsMessageLog.logMessage(self.tr("canvasReleaseEvent crash") + ": " + str(e), "Patrac")
