from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsVectorLayer, QgsWkbTypes, QgsProject, QgsField, QgsMessageLog
from qgis.gui import QgsMapTool, QgsMapToolEmitPoint, QgsRubberBand
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QVariant

class LineMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, widget):
        super(LineMapTool, self).__init__(canvas)
        self.canvas = canvas
        self.points = []
        self.widget = widget
        self.rubberBand = None
        self.layer = None

    def createLayer(self):
        self.layer = QgsVectorLayer("LineString?crs=epsg:3857", "Line", "memory")
        pr = self.layer.dataProvider()
        pr.addAttributes([QgsField("id", QVariant.Int)])
        self.layer.updateFields()
        QgsProject.instance().addMapLayer(self.layer)

    def canvasPressEvent(self, event):
        if event.button() == 2:
            self.makeSplit()
        else:
            point = self.toMapCoordinates(event.pos())
            self.points.append(QgsPoint(point))

            if self.layer is None:
                self.createLayer()

            if len(self.points) == 1:
                self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
                self.rubberBand.setColor(QColor(255, 0, 0, 100))
                self.rubberBand.setWidth(2)

            self.rubberBand.addPoint(point)

    def canvasMoveEvent(self, event):
        if len(self.points) > 0:
            self.rubberBand.movePoint(self.rubberBand.numberOfVertices() - 1, self.toMapCoordinates(event.pos()))

    def canvasReleaseEvent(self, event):
        if len(self.points) > 1:
            # Vytvoření liniové geometrie
            line_geometry = QgsGeometry.fromPolyline(self.points)

            if self.layer is not None:
                self.layer.startEditing()
                listOfIds = [feat.id() for feat in self.layer.getFeatures()]
                self.layer.deleteFeatures(listOfIds)
                feature = QgsFeature()
                feature.setGeometry(line_geometry)
                feature.setAttributes([1])
                self.layer.addFeature(feature)
                self.layer.commitChanges()

        # self.reset()

    def reset(self):
        self.points = []
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer = None

    def activate(self):
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberBand.setColor(QColor(255, 0, 0, 100))
        self.rubberBand.setWidth(2)
        QgsMapTool.activate(self)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.reset()

    def makeSplit(self):
        line_geometry = QgsGeometry.fromPolyline(self.points)
        QgsMessageLog.logMessage(line_geometry.asWkt(), "Patrac")
        listOfIds = [feat.id() for feat in self.layer.getFeatures()]
        self.layer.select(listOfIds)
        self.widget.splitByDrawnLine(self.layer)
        QgsProject.instance().removeMapLayer(self.layer)
        self.deactivate()
