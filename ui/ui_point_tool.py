from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from qgis.core import *
from qgis.gui import *

from .ui_result import Ui_Result

class PointMapTool(QgsMapTool):
  """Map tool for click in the map"""
  def __init__(self, canvas, widget):
      self.canvas = canvas
      self.widget = widget
      QgsMapTool.__init__(self, self.canvas)
      self.reset()
      #Dialog for setting result output
      self.dialog = Ui_Result(self.widget)
      self.DATAPATH = ''
      self.searchid = ''
      self.Utils = self.widget.Utils

  def reset(self):
      self.point = None

  def setDataPath(self, DATAPATH):
      self.DATAPATH = DATAPATH

  def setSearchid(self, searchid):
      self.searchid = searchid

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

      self.addToCanvas(self.point)
      self.widget.iface.messageBar().clearWidgets()

  def addToCanvas(self, point):
      layer = QgsVectorLayer("Point", "result", "memory")
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
      self.saveLayer(layer)

  def saveLayer(self, layer):
      crs = QgsCoordinateReferenceSystem("EPSG:5514")
      QgsVectorFileWriter.writeAsVectorFormat(layer, self.Utils.getDataPath() + "/pracovni/result.shp",
                                              "utf-8", crs, "ESRI Shapefile")

      vector = QgsVectorLayer(self.Utils.getDataPath() + "/pracovni/result.shp", "Nález", "ogr")
      if not vector.isValid():
          QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
      else:
          settingsPath = self.widget.pluginPath + "/../../../qgis_patrac_settings"
          vector.loadNamedStyle(settingsPath + '/styles/result.qml')
          QgsProject.instance().addMapLayer(vector)

  def canvasReleaseEvent(self, e):
      if self.point is not None:
          #print "Point: ", self.point.x()
          self.dialog.setPoint(self.point)
          self.dialog.setDataPath(self.DATAPATH)
          self.dialog.setSearchid(self.searchid)
          self.dialog.show()

  #def deactivate(self):
  #    super(PointMapTool, self).deactivate()
  #    self.emit(SIGNAL("deactivated()"))
