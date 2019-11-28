# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

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

    def setAttribute(self, attribute):
        self.attribute = attribute

    def canvasPressEvent(self, e):
        self.point = self.toMapCoordinates(e.pos())

    def analyzeTrack(self, sector):
        currentLayer = self.canvas.currentLayer()
        # TODO check also vector and line
        if currentLayer.crs().authid() != "EPSG:4326":
            QMessageBox.information(None, "CHYBA:", "Vybraná vrstva není stopou. Vyberte správnou vrstvu.")
            return
        provider = currentLayer.dataProvider()
        features = provider.getFeatures()
        crs_src = QgsCoordinateReferenceSystem(4326)
        crs_dest = QgsCoordinateReferenceSystem(5514)
        xform = QgsCoordinateTransform(crs_src, crs_dest)
        buffer_union = None
        for feature in features:
            geom = feature.geometry()
            geom.transform(xform)
            geom = geom.buffer(50,2)
            if buffer_union is None:
                buffer_union = geom
            else:
                buffer_union = buffer_union.combine(geom)
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
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        # root = QgsProject.instance().layerTreeRoot()
        # mygroup = root.findGroup(u"nepropátráno")
        # if mygroup is None:
        #     mygroup = root.addGroup(u"nepropátráno")
        # mygroup.addLayer(layer)
        # mygroup.setExpanded(False)
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