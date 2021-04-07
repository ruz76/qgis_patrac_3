from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from qgis.core import *
from qgis.gui import *

import math

class PointMapToolLatLon(QgsMapTool):
    """Map tool for click in the map"""

    def __init__(self, canvas, widget):
        self.canvas = canvas
        self.widget = widget
        self.point = None
        self.type = 0
        QgsMapTool.__init__(self, self.canvas)
        self.reset()
        self.Utils = self.widget.Utils

    def reset(self):
        self.point = None

    def setType(self, type):
        self.type = type

    def toDegreesMinutesAndSeconds(self, coordinate):
        # Used from https://stackoverflow.com/questions/37893131/how-to-convert-lat-long-from-decimal-degrees-to-dms-format
        print(coordinate)
        absolute = abs(coordinate)
        degrees = math.floor(absolute)
        minutesNotTruncated = (absolute - degrees) * 60
        minutes = math.floor(minutesNotTruncated)
        seconds = math.floor((minutesNotTruncated - minutes) * 60)
        return str(degrees) + "° " + str(minutes) + "' " + str(seconds) + "''"

    def covertToHumanReadable(self):
        latitude = self.toDegreesMinutesAndSeconds(self.point.y())
        if self.point.y() >= 0:
            latitudeCardinal = "N"
        else:
            latitudeCardinal = "S"

        longitude = self.toDegreesMinutesAndSeconds(self.point.x())
        if self.point.x() >= 0:
            longitudeCardinal = "E"
        else:
            longitudeCardinal = "W"

        return latitudeCardinal + "" + latitude + " " + longitudeCardinal + "" + longitude

    def canvasPressEvent(self, e):
        self.point = self.toMapCoordinates(e.pos())
        srs = self.canvas.mapSettings().destinationCrs()
        current_crs = srs.authid()

        if current_crs != "EPSG:5514":
            crs_src = QgsCoordinateReferenceSystem(srs)
            crs_dest = QgsCoordinateReferenceSystem(5514)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            point_5514 = xform.transform(self.point)
            self.addToCanvas(point_5514, self.type)
        else:
            self.addToCanvas(self.point, self.type)

        if current_crs != "EPSG:4326":
            srs = self.canvas.mapSettings().destinationCrs()
            crs_src = QgsCoordinateReferenceSystem(srs)
            crs_dest = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            self.point = xform.transform(self.point)
            self.widget.setPointLatLon(self.point, self.type)
            self.widget.setPointLatLonHumanReadable(self.covertToHumanReadable(), self.type)
        else:
            self.widget.setPointLatLon(self.point, self.type)
            self.widget.setPointLatLonHumanReadable(self.covertToHumanReadable(), self.type)


    def addToCanvas(self, point, type):
        layer_name = 'handlers_placement'
        layer_title = 'Místo pro psovody'
        if type == 1:
            layer_name = 'others_placement'
            layer_title = 'Místo pro ostatní prostředky'

        layer = QgsVectorLayer("Point", layer_name, "memory")
        crs = QgsCoordinateReferenceSystem("EPSG:5514")
        layer.setCrs(crs)
        pr = layer.dataProvider()
        field = QgsField("note", QVariant.String)
        field.setLength(50)
        pr.addAttributes([field])
        layer.updateFields()
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(point))
        f.setAttributes(["NOP"])
        pr.addFeature(f)
        layer.updateExtents()
        self.saveLayer(layer, layer_name, layer_title)

    def saveLayer(self, layer, layer_name, layer_title):
        crs = QgsCoordinateReferenceSystem("EPSG:5514")
        QgsVectorFileWriter.writeAsVectorFormat(layer, self.Utils.getDataPath() + "/pracovni/" + layer_name + ".shp",
                                                "utf-8", crs, "ESRI Shapefile")

        vector = QgsVectorLayer(self.Utils.getDataPath() + "/pracovni/" + layer_name + ".shp", layer_title, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            settingsPath = self.widget.pluginPath + "/../../../qgis_patrac_settings"
            vector.loadNamedStyle(settingsPath + '/styles/' + layer_name + '.qml')
            QgsProject.instance().addMapLayer(vector)
