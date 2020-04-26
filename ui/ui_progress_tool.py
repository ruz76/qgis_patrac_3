# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import QSettings

from qgis.core import *
from qgis.gui import *

from .ui_result import Ui_Result


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
        self.pluginPath = ''
        self.iface = iface

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
        self.value = value

    def setAttribute(self, attribute):
        self.attribute = attribute

    def canvasPressEvent(self, e):
        self.point = self.toMapCoordinates(e.pos())
        srs = self.canvas.mapSettings().destinationCrs()
        current_crs = srs.authid()
        if current_crs != "EPSG:5514":
            srs = self.canvas.mapSettings().destinationCrs()
            crs_src = QgsCoordinateReferenceSystem(srs)
            crs_dest = QgsCoordinateReferenceSystem(5514)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            self.point = xform.transform(self.point)

    def analyzeTrackDouble(self, features, sector):
        # TODO
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
                geom = geom.buffer(int(self.value),2)
                if buffer_union is None:
                    buffer_union = geom
                else:
                    buffer_union = buffer_union.combine(geom)
        return buffer_union

    def analyzeTrack(self, sector):
        # TODO Rojnice - krajníci
        currentLayer = self.canvas.currentLayer()
        # TODO check also vector and line
        if currentLayer != None and currentLayer.crs().authid() != "EPSG:4326":
            QMessageBox.information(None, "CHYBA:", "Vybraná vrstva není stopou. Vyberte správnou vrstvu.")
            return
        provider = currentLayer.dataProvider()
        features = provider.getFeatures()

        buffer_union = None
        if self.unit == 2:
            buffer_union = self.analyzeTrackDouble(features, sector)
            QMessageBox.information(None, "CHYBA:", "Tato funkce není zatím implementována.")
            return
        else:
            buffer_union = self.analyzeTrackSingle(features, sector)
            if buffer_union == None:
                QMessageBox.information(None, "CHYBA:", "Vybraná vrstva neobsahuje stopy pro analýzu. Vyberte správnou vrstvu nebo jiný pátrací prostředek.")
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
        self.iface.setActiveLayer(currentLayer)

    def canvasReleaseEvent(self, e):
        if self.point is not None and self.layer is not None:
            provider = self.layer.dataProvider()
            features = provider.getFeatures()
            if self.attribute > -1:
                subsetString = self.layer.subsetString()
                self.layer.setSubsetString("")
                self.layer.startEditing()
            try:
                for feature in features:
                    if feature.geometry().contains(self.point):
                        QgsMessageLog.logMessage("RE 5", "Patrac")
                        if self.attribute > -1:
                            # print(self.type)
                            feature.setAttribute(self.attribute, self.type)
                            if self.type == 1:
                                feature.setAttribute(self.attribute + 1, self.unit)
                            self.layer.updateFeature(feature)
                            self.layer.commitChanges()
                            self.layer.setSubsetString(subsetString)
                        else:
                            self.analyzeTrack(feature)
                        break
            except Exception as e:
                self.layer.setSubsetString(subsetString)
                QgsMessageLog.logMessage("canvasReleaseEvent crash " + str(e), "Patrac")