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
        if current_crs != "EPSG:4326":
            srs = self.canvas.mapSettings().destinationCrs()
            crs_src = QgsCoordinateReferenceSystem(srs)
            crs_dest = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            self.point = xform.transform(self.point)
            self.widget.setPointLatLon(self.point, self.type)
            self.widget.setPointLatLonHumanReadable(self.covertToHumanReadable(), self.type)
