from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from qgis.core import *
from qgis.gui import *

from .ui_result import Ui_Result

class PointMapTool(QgsMapTool):
  """Map tool for click in the map"""
  def __init__(self, canvas):
      self.canvas = canvas
      QgsMapTool.__init__(self, self.canvas)
      self.reset()
      #Dialog for setting result output
      self.dialog = Ui_Result()
      self.DATAPATH = ''
      self.searchid = ''

  def reset(self):
      self.point = None

  def setDataPath(self, DATAPATH):
      self.DATAPATH = DATAPATH

  def setSearchid(self, searchid):
      self.searchid = searchid

  def canvasPressEvent(self, e):
      self.point = self.toMapCoordinates(e.pos())

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