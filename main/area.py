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

import csv, io, math, subprocess, os, sys, uuid

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

import processing

class CalculateDistanceCostedCumulativeTask(QgsTask):
    def __init__(self, widget, parent, params):
        super().__init__("Calculate DistanceCostedCumulative Task", QgsTask.CanCancel)
        self.widget = widget
        self.parent = parent
        self.data_path = params["data_path"]
        self.finish_steps = params["finish_steps"]
        self.exception: Optional[Exception] = None

    def run(self):
        try:
            progress = 85
            self.setProgress(progress)

            params = {
                'a': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[0] + '.tif' if len(self.parent.cumulativeEquationInputs) > 0 else None,
                'b': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[1] + '.tif' if len(self.parent.cumulativeEquationInputs) > 1 else None,
                'c': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[2] + '.tif' if len(self.parent.cumulativeEquationInputs) > 2 else None,
                'd': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[3] + '.tif' if len(self.parent.cumulativeEquationInputs) > 3 else None,
                'e': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[4] + '.tif' if len(self.parent.cumulativeEquationInputs) > 4 else None,
                'f': self.data_path + 'pracovni/' + self.parent.cumulativeEquationInputs[5] + '.tif' if len(self.parent.cumulativeEquationInputs) > 5 else None,
                'expression':'distances_costed_cum = ' + self.parent.cumulativeEquation,
                'output':self.data_path + 'pracovni/distances_costed_cum.tif',
                'GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''
            }

            print(params)

            processing.run("grass7:r.mapcalc.simple", params)
            progress = 90
            self.setProgress(progress)

            processing.run("native:zonalstatisticsfb", {'INPUT':self.data_path + 'pracovni/sektory_group.shp','INPUT_RASTER':self.data_path + 'pracovni/distances_costed_cum.tif','RASTER_BAND':1,'COLUMN_PREFIX':'stats_','STATISTICS':[5],'OUTPUT':self.data_path + 'pracovni/sectors_zoned.shp'})
            progress = 100
            self.setProgress(progress)

            return True
        except Exception as e:
            QgsMessageLog.logMessage("Error in CalculateDistanceCostedCumulativeTask: " + str(e), "Patrac")
            self.exception = e
            return False

    def finished(self, result):
        print("FINISHED")
        DATAPATH = self.parent.Utils.getDataPath()
        self.parent.Utils.addRasterLayer(DATAPATH + '/pracovni/distances_costed_cum.tif', 'procenta', 5514, -2)
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break
        if layer is not None:
            layer.triggerRepaint()
            # Sets the added layer as sctive
            self.parent.plugin.iface.setActiveLayer(layer)
        else:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "Wrong installation. Call you administrator.", None))

        if self.finish_steps:
            self.widget.finishRecalculateAll()
        else:
            self.widget.finishStep3()

        self.widget.clearMessageBar()

class CalculateCostDistanceTask(QgsTask):
    def __init__(self, widget, parent, params):
        super().__init__("Calculate CostDistance Task", QgsTask.CanCancel)
        self.widget = widget
        self.parent = parent
        self.data_path = params["data_path"]
        self.pointid = params["pointid"]
        self.persontype = params["persontype"]
        self.minx = params["minx"]
        self.maxx = params["maxx"]
        self.miny = params["miny"]
        self.maxy = params["maxy"]
        self.epsg = params["epsg"]
        self.x = params["x"]
        self.y = params["y"]
        self.finish_steps = params["finish_steps"]
        self.azimuth = params['azimuth']
        self.tolerance = params['tolerance']
        self.friction = params['friction']
        self.exception: Optional[Exception] = None

    def run(self):
        try:
            self.setProgress(5)
            processing.run("gdal:rasterize", {'INPUT':self.data_path + 'pracovni/coords_vector_' + str(self.pointid) + '.shp','FIELD':'','BURN':1,'USE_Z':False,'UNITS':1,'WIDTH':5,'HEIGHT':5,'EXTENT': self.get_proj_win(),'NODATA':0,'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9','DATA_TYPE':0,'INIT':None,'INVERT':False,'EXTRA':'','OUTPUT':self.data_path + 'pracovni/coords_rast_' + str(self.pointid) + '.tif'})
            check_null_result = self.check_null()
            if len(check_null_result) == 0:
                # Error in moving point
                QgsMessageLog.logMessage("Can not move point from null place " + str(self.pointid), "Patrac")
                return False
            else:
                if self.x == check_null_result[0] and self.y == check_null_result[1]:
                    # We do not move the point
                    QgsMessageLog.logMessage("Point is outside null. Normal processing " + str(self.pointid), "Patrac")
                else:
                    # We move the point
                    QgsMessageLog.logMessage("Point is inside null. Moving from it to " + str(self.pointid) + " " + str(self.x) + " " + str(self.y), "Patrac")
                    self.x = check_null_result[0]
                    self.y = check_null_result[1]
                    processing.run("gdal:rasterize", {'INPUT': self.data_path + 'pracovni/friction_flat_cost_buf_coords' + str(self.pointid) + '.shp','FIELD':'','BURN':1,'USE_Z':False,'UNITS':1,'WIDTH':5,'HEIGHT':5,'EXTENT': self.get_proj_win(),'NODATA':0,'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9','DATA_TYPE':0,'INIT':None,'INVERT':False,'EXTRA':'','OUTPUT':self.data_path + 'pracovni/coords_rast_' + str(self.pointid) + '.tif'})
            self.generateRadialOnPoint(self.x, self.y, self.pointid)
            self.writeAzimuthReclass(self.azimuth, self.tolerance, self.friction, self.pointid)
            # QgsMessageLog.logMessage("CWD " + str(os.getcwd()), "Patrac Info")
            processing.run("gdal:rasterize", {'INPUT': self.data_path + 'pracovni/radial' + str(self.pointid) + '.csv','FIELD':'id','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':5,'HEIGHT':5,'EXTENT': self.get_proj_win(),'NODATA':0,'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9','DATA_TYPE':5,'INIT':None,'INVERT':False,'EXTRA':'','OUTPUT': self.data_path + 'pracovni/radial' + str(self.pointid) + '.tif'})
            self.setProgress(10)
            processing.run("grass7:r.reclass", {'input': self.data_path + 'pracovni/radial' + str(self.pointid) + '.tif','rules': self.data_path + 'pracovni/azimuth_reclass_' + str(self.pointid) + '.rules','txtrules': '','output': self.data_path + 'pracovni/radial_reclassed_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            self.setProgress(15)
            processing.run("grass7:r.mapcalc.simple", {'a': self.data_path + 'raster/friction.tif','b':self.data_path + 'pracovni/radial_reclassed_' + str(self.pointid) + '.tif','c':None,'d':None,'e':None,'f':None,'expression':'A+B','output':self.data_path + 'pracovni/friction_radial_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            self.setProgress(20)
            processing.run("grass7:r.walk.coords", {'elevation': self.data_path + 'raster/dem.tif','friction':self.data_path + 'pracovni/friction_radial_' + str(self.pointid) + '.tif','start_coordinates': str(self.x) + ',' + str(self.y),'stop_coordinates':'','walk_coeff':'0.72,6.0,1.9998,-1.9998','lambda':1,'slope_factor':-0.2125,'max_cost':0,'null_cost':None,'memory':300,'-k':False,'-n':False,'output':self.data_path + 'pracovni/cost_' + str(self.pointid) + '.tif','outdir':'TEMPORARY_OUTPUT','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            self.setProgress(25)
            self.setProgress(30)
            processing.run("grass7:r.buffer", {'input': self.data_path + 'pracovni/coords_rast_' + str(self.pointid) + '.tif','distances': self.get_distances(),'units':0,'-z':False,'output': self.data_path + 'pracovni/buffers_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            self.setProgress(35)
            # we have to start on cat 3, so on min of the ring for 20%
            cat=3
            variables = [10, 20, 30, 40, 50, 60, 70, 80]
            rules_global = ''
            PREVMIN = 0
            progress = 35
            for i in variables:
                rules = str(cat) + ' = 1\n'
                rules += 'end'
                processing.run("grass7:r.reclass", {'input': self.data_path + 'pracovni/buffers_' + str(self.pointid) + '.tif','rules':'','txtrules': rules,'output': self.data_path + 'pracovni/distances_' + str(self.pointid) + '_' + str(i) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
                processing.run("grass7:r.mapcalc.simple", {'a': self.data_path + 'pracovni/distances_' + str(self.pointid) + '_' + str(i) + '.tif','b':self.data_path + 'pracovni/cost_' + str(self.pointid) + '.tif','c':None,'d':None,'e':None,'f':None,'expression':'A*B','output':self.data_path + 'pracovni/cost_' + str(self.pointid) + '_distances_' + str(i) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
                stats = processing.run("native:rasterlayerstatistics", {'INPUT':self.data_path + 'pracovni/cost_' + str(self.pointid) + '_distances_' + str(i) + '.tif','BAND':1,'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT'})
                print(stats)
                if stats['MIN'] is not None and stats['MAX'] is not None:
                    try:
                        #Reads min value
                        MIN = float(stats['MIN'])
                        print(str(MIN))
                        #Reads max value
                        MAX = float(stats['MAX'])
                        print(str(MAX))
                        #Minimum value and maximum value is used as extent for relass of the whole cost layer
                        #rules_percentage_f.write(str(MIN) + ' thru ' + str(MAX) + ' = ' + str(i) + '\n')
                        if str(PREVMIN) != 'nan' and str(MIN) != 'nan':
                            rules_global += str(PREVMIN) + ' thru ' + str(MIN) + ' = ' + str(i) + '\n'
                        PREVMIN = MIN
                    except:
                        print("Problem with category " + str(cat) + " " + str(i) + "%")
                cat += 1
                progress += 5
                self.setProgress(progress)
            rules_global += '* = 95\n'
            processing.run("grass7:r.reclass", {'input':self.data_path + 'pracovni/cost_' + str(self.pointid) + '.tif','rules':'','txtrules': rules_global,'output':self.data_path + 'pracovni/distances_' + str(self.pointid) + '_costed.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            progress = 80
            self.setProgress(progress)
            return True
        except Exception as e:
            QgsMessageLog.logMessage("Error in CalculateCostDistanceTask " + str(self.pointid) + ": " + str(e), "Patrac")
            self.exception = e
            return False

    def finished(self, result):
        QgsMessageLog.logMessage("FINISHED Calculate CostDistance Task for Point: " + str(self.pointid), "Patrac")
        self.parent.finishedCalculateCostDistanceTask(self.pointid, self.finish_steps)

    def get_proj_win(self):
        return str(self.minx) + ',' + str(self.maxx) + ',' + str(self.miny) + ',' + str(self.maxy) + ' [EPSG:' + str(self.epsg) + ']'

    def get_distances(self):
        with open(self.parent.pluginPath + "/grass/distances.txt") as d:
            lines = d.readlines()
            return lines[self.persontype].rstrip()

    def check_null(self):
        try:
            processing.run("grass7:r.mapcalc.simple", {'a': self.data_path + 'raster/friction.tif','b': self.data_path + 'pracovni/coords_rast_' + str(self.pointid) + '.tif','c':None,'d':None,'e':None,'f':None,'expression':'A*B','output':self.data_path + 'pracovni/coords_friction_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
            stats = processing.run("native:rasterlayerstatistics", {'INPUT':self.data_path + 'pracovni/coords_friction_' + str(self.pointid) + '.tif','BAND':1,'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT'})
            QgsMessageLog.logMessage("Checking null null place: " + str(stats), "Patrac")
            # Reads min value
            if stats['MIN'] is not None:
                MIN = float(stats['MIN'])
                MEAN = float(stats['MEAN'])
                if str(MIN) == "nan" or str(MEAN) == "nan":
                    return self.move_from_null()
                else:
                    return [self.x, self.y]
            else:
                return self.move_from_null()
        except:
            return self.move_from_null()

    def move_from_null(self):
        print("Moving from null")
        processing.run("grass7:r.mapcalc.simple", {'a': self.data_path + 'raster/friction.tif','b': None,'c':None,'d':None,'e':None,'f':None,'expression':'if(isnull(A), 1, null())','output':self.data_path + 'pracovni/friction_null_rec_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
        processing.run("grass7:r.buffer", {'input': self.data_path + 'pracovni/friction_null_rec_' + str(self.pointid) + '.tif','distances': '10','units':0,'-z':False,'output': self.data_path + 'pracovni/friction_null_rec_buf_10_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
        processing.run("grass7:r.null", {'map':self.data_path + 'pracovni/friction_null_rec_buf_10_' + str(self.pointid) + '.tif','setnull':'1','null':None,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,'output': self.data_path + 'pracovni/friction_null_rec_buf_10_null' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
        with open(self.data_path + 'pracovni/friction_flat_reclass_' + str(self.pointid) + '.rules', 'w') as rec:
            rec.write('* = 1\n')
            rec.write('end\n')
        processing.run("grass7:r.reclass", {'input': self.data_path + 'pracovni/radial' + str(self.pointid) + '.tif','rules': self.data_path + 'pracovni/friction_flat_reclass_' + str(self.pointid) + '.rules','txtrules': '','output': self.data_path + 'pracovni/friction_flat_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
        processing.run("grass7:r.cost", {'input': self.data_path + 'pracovni/friction_flat_' + str(self.pointid) + '.tif','start_coordinates': str(self.x) + ',' + str(self.y) + ' [EPSG:' + str(self.epsg) + ']','stop_coordinates':None,'-k':False,'-n':True,'start_points':None,'stop_points':None,'start_raster':None,'max_cost':0,'null_cost':None,'memory':300,'output': self.data_path + 'pracovni/friction_flat_cost_' + str(self.pointid) + '.tif','nearest':'TEMPORARY_OUTPUT','outdir':'TEMPORARY_OUTPUT','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':'','GRASS_SNAP_TOLERANCE_PARAMETER':-1,'GRASS_MIN_AREA_PARAMETER':0.0001})
        processing.run("grass7:r.mapcalc.simple", {'a': self.data_path + 'pracovni/friction_flat_cost_' + str(self.pointid) + '.tif','b': self.data_path + 'pracovni/friction_null_rec_buf_10_null' + str(self.pointid) + '.tif','c':None,'d':None,'e':None,'f':None,'expression':'A*B','output':self.data_path + 'pracovni/friction_flat_cost_buf_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})

        try:
            stats = processing.run("native:rasterlayerstatistics", {'INPUT':self.data_path + 'pracovni/friction_flat_cost_buf_' + str(self.pointid) + '.tif','BAND':1,'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT'})
            # Reads min value
            if stats['MIN'] is not None:
                MIN = float(stats['MIN'])
                print("MINIMUM: " + str(MIN))
                if str(MIN) == "nan":
                    return []
                # Reads min value
                with open(self.data_path + 'pracovni/move_' + str(self.pointid) + '.rules', 'w') as rec:
                    rec.write(str(MIN) + ' = 1\n')
                    rec.write('* = null\n')
                    rec.write('end')
                processing.run("grass7:r.reclass", {'input': self.data_path + 'pracovni/friction_flat_cost_buf_' + str(self.pointid) + '.tif','rules': self.data_path + 'pracovni/move_' + str(self.pointid) + '.rules','txtrules': '','output': self.data_path + 'pracovni/friction_flat_cost_buf_coords_' + str(self.pointid) + '.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})
                processing.run("native:pixelstopoints", {'INPUT_RASTER':self.data_path + 'pracovni/friction_flat_cost_buf_coords_' + str(self.pointid) + '.tif','RASTER_BAND':1,'FIELD_NAME':'VALUE','OUTPUT':self.data_path + 'pracovni/friction_flat_cost_buf_coords_' + str(self.pointid) + '.shp'})
                return self.get_moved_coordinates()
            else:
                return []
        except:
            return []

    def get_moved_coordinates(self):
        layer = QgsVectorLayer(self.data_path + 'pracovni/friction_flat_cost_buf_coords_' + str(self.pointid) + '.shp', "mylayer", "ogr")
        features = layer.dataProvider().getFeatures()
        for feature in features:
            pt = feature.geometry().asPoint()
            return [pt.x(), pt.y()]
        else:
            return []

    def getRadialAlpha(self, i, KVADRANT):
        """Returns angle based on quandrante"""
        alpha = (math.pi / float(2)) - ((math.pi / float(180)) * i)
        if KVADRANT == 2:
            alpha = ((math.pi / float(180)) * i) - (math.pi / float(2))
        if KVADRANT == 3:
            alpha = (3 * (math.pi / float(2))) - ((math.pi / float(180)) * i)
        if KVADRANT == 4:
            alpha = ((math.pi / float(180)) * i) - (3 * (math.pi / float(2)))
        return alpha

    def getRadialTriangleX(self, alpha, CENTERX, xdir, RADIUS):
        """Gets X coordinate of the triangle"""
        dx = xdir * math.cos(alpha) * RADIUS
        x = CENTERX + dx
        return x

    def getRadialTriangleY(self, alpha, CENTERY, ydir, RADIUS):
        """Gets Y coordinate of the triangle"""
        dy = ydir * math.sin(alpha) * RADIUS
        y = CENTERY + dy
        return y

    def generateRadialOnPoint(self, x, y, id):
        """Generates triangles from defined point in step one degree"""
        CENTERX = x
        CENTERY = y
        # Radius is set ot 20000 meters to be sure that whole area is covered
        RADIUS = 20000;
        # Writes output to radial.csv
        csv = open(self.parent.Utils.getDataPath() + "/pracovni/radial" + str(id) + ".csv", "w")
        # Writes in WKT format
        csv.write("id;wkt\n")
        self.generateRadial(CENTERX, CENTERY, RADIUS, 1, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 2, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 3, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 4, csv)
        csv.close()

    def generateRadial(self, CENTERX, CENTERY, RADIUS, KVADRANT, csv):
        """Generates triangles in defined quadrante"""
        # First quadrante is from 0 to 90 degrees
        # In both axes is coordinates increased
        from_deg = 0
        to_deg = 90
        xdir = 1
        ydir = 1
        # Second quadrante is from 90 to 180 degrees
        # In axe X is coordinate increased
        # In axe Y is coordinate decreased
        if KVADRANT == 2:
            from_deg = 90
            to_deg = 180
            xdir = 1
            ydir = -1
        # Second quadrante is from 180 to 270 degrees
        # In axe X is coordinate decreased
        # In axe Y is coordinate decreased
        if KVADRANT == 3:
            from_deg = 180
            to_deg = 270
            xdir = -1
            ydir = -1
        # Second quadrante is from 270 to 360 degrees
        # In axe X is coordinate decreased
        # In axe Y is coordinate increased
        if KVADRANT == 4:
            from_deg = 270
            to_deg = 361
            xdir = -1
            ydir = 1
        for i in range(from_deg, to_deg):
            alpha = self.getRadialAlpha(i, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
            # Special condtions where one of the axes is on zero direction
            if i == 0:
                x = CENTERX
                y = CENTERY + RADIUS
            if i == 90:
                x = CENTERX + RADIUS
                y = CENTERY
            if i == 180:
                x = CENTERX
                y = CENTERY - RADIUS
            if i == 270:
                x = CENTERX - RADIUS
                y = CENTERY
            # Triangle is written as Polygon
            wkt_polygon = "POLYGON((" + str(CENTERX) + " " + str(CENTERY) + ", " + str(x) + " " + str(y)
            alpha = self.getRadialAlpha(i + 1, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
            # Special condtions where one of the axes is on zero direction
            if i == 89:
                x = CENTERX + RADIUS
                y = CENTERY
            if i == 179:
                x = CENTERX
                y = CENTERY - RADIUS
            if i == 269:
                x = CENTERX - RADIUS
                y = CENTERY
            if i == 359:
                x = CENTERX
                y = CENTERY + RADIUS
            wkt_polygon = wkt_polygon + ", " + str(x) + " " + str(y) + ", " + str(CENTERX) + " " + str(CENTERY) + "))"
            csv.write(str(i) + ";" + wkt_polygon + "\n")

    def writeAzimuthReclass(self, azimuth, tolerance, friction, id):
        """Creates reclass rules for direction
            Tolerance is for example 30 degrees
            Friction is how frict is the direction
        """
        DATAPATH = self.parent.Utils.getDataPath()
        reclass = open(DATAPATH + "/pracovni/azimuth_reclass_" + str(id) + ".rules", "w")
        tolerance_half = tolerance / 2
        astart = int(azimuth) - tolerance_half
        aend = int(azimuth) + tolerance_half
        if astart < 0:
            astart = 360 + astart
            reclass.write(str(astart) + " thru 360 = 0\n")
            reclass.write("0 thru " + str(aend) + " = 0\n")
            reclass.write("* = " + str(friction) + "\n")
            reclass.write("end\n")
        else:
            if aend > 360:
                aend = aend - 360
                reclass.write(str(astart) + " thru 360 = 0\n")
                reclass.write("0 thru " + str(aend) + " = 0\n")
                reclass.write("* = " + str(friction) + "\n")
                reclass.write("end\n")
            else:
                reclass.write(str(astart) + " thru " + str(aend) + "= 0\n")
                reclass.write("* = " + str(friction) + "\n")
                reclass.write("end\n")
        # reclass.write(str(azimuth) + " " + str(tolerance) + " " + str(friction) + "\n")
        reclass.close()

class Area(object):
    def __init__(self, widget):
        self.widget = widget
        self.plugin = self.widget.plugin
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.Utils = self.widget.Utils
        self.calculatedPoints = []
        self.pointsToCalculate = []
        self.cumulativeEquation = ''
        self.cumulativeEquationInputs = []
        self.params = None

    def setParams(self, params):
        self.params = params

    def finishedCalculateCostDistanceTask(self, pointid, finish_steps):
        self.calculatedPoints.append(pointid)
        if len(self.calculatedPoints) == len(self.pointsToCalculate):
            QgsMessageLog.logMessage("Start Cumulative using self.cumulativeEquation", "Patrac")
            # Start Cumulative using self.cumulativeEquation
            DATAPATH = self.Utils.getDataPath()
            params = {
                "data_path": DATAPATH + "/",
                "finish_steps": finish_steps
            }
            self.widget.clearTasksList()
            self.widget.appendTask(CalculateDistanceCostedCumulativeTask(self.widget, self, params))
            self.widget.runTask(0)
        else:
            self.widget.runTask(pointid + 1)

    def getArea(self, finish_steps=False):
        """Runs main search for suitable area"""

        self.widget.createProgressBar(QApplication.translate("Patrac", "Calculating area: ", None))

        if self.params is None:
            projectinfo = self.Utils.getProjectInfo()
            params = {
                "persontype": projectinfo['persontype'],
                "minx": projectinfo['minx'],
                "maxx": projectinfo['maxx'],
                "miny": projectinfo['miny'],
                "maxy": projectinfo['maxy'],
                "epsg": projectinfo['epsg']
            }
            self.params = params

        self.Utils.loadRemovedNecessaryLayers()

        # Check if the project has mista.shp
        if not self.Utils.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None) + ":",
                                    QApplication.translate("Patrac", "Wrong project", None))
            return

        # Vybrana vrstva
        # qgis.utils.iface.setActiveLayer(QgsMapLayer)
        self.widget.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Removes existing loaded layer with area for search
        # This is necessary on Windows - based on lock of files
        self.Utils.removeLayer(DATAPATH + '/pracovni/distances_costed_cum.tif')

        # Tests if layer mista exists
        # TODO should be done tests for attributes as well
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        if layer == None:
            QMessageBox.information(None, QApplication.translate("Patrac", "INFO", None), QApplication.translate("Patrac", "Can not find places layer. Can not compute.", None))
            self.widget.setCursor(Qt.ArrowCursor)
            return

        features = self.filterAndSortFeatures(layer.getFeatures())

        if len(features) == 0:
            # There is not any place defined
            # Place the place to the center of the map
            QMessageBox.information(None, QApplication.translate("Patrac", "INFO:", None),
                                                                 QApplication.translate("Patrac", "Layer with places is empty. Placing point in the center of the map.", None))
            self.addPlaceToTheCenter()
            features = self.filterAndSortFeatures(layer.getFeatures())

        self.pointsToCalculate = features
        self.calculatedPoints = []
        self.cumulativeEquationInputs = []
        self.widget.clearTasksList()

        # If there is just one point - impossible to define direction
        # TODO - think more about this check - should be more than two, probably and in some shape as well
        if len(features) > 1:
            azimuth = self.getRadial(features)
            useAzimuth = self.Utils.getProcessRadial()
            # difficult to set azimuth (for example wrong shape of the path (e.q. close to  circle))
            QgsMessageLog.logMessage("Masking for azimuth: " + str(azimuth) + " " + str(useAzimuth), "Patrac")
            if azimuth <= 360 and useAzimuth:
                self.pointsToCalculate = [features[len(features) - 1]]
                self.findAreaWithRadial(features[len(features) - 1], 0, finish_steps, azimuth, 30, 100)
                # cats_status = self.checkCats()
                # if not cats_status:
                #     self.widget.setCursor(Qt.ArrowCursor)
                #     return
                self.cumulativeEquation = "A"
                self.cumulativeEquationInputs = ['distances_0_costed']
                # self.createCumulativeArea()
            else:
                i = 0
                distances_costed_cum = ""
                max_weight = 1
                for feature in features:
                    self.findAreaWithRadial(feature, i, finish_steps, 0, 0, 0)
                    # cats_status = self.checkCats()
                    # if not cats_status:
                    #     self.widget.setCursor(Qt.ArrowCursor)
                    #     return
                    cur_weight = "1"
                    if str(feature["vaha"]) != "NULL":
                        cur_weight = str(feature["vaha"])
                    if str(feature["vaha"]) != "NULL" and feature["vaha"] > max_weight:
                        max_weight = feature["vaha"]
                    if i == 0:
                        distances_costed_cum = "(" + str(chr(65 + i)) + "/" + cur_weight + ")"
                        self.cumulativeEquationInputs.append('distances_0_costed')
                    else:
                        distances_costed_cum = distances_costed_cum + ",(" + str(chr(65 + i)) + "/" + cur_weight + ")"
                        self.cumulativeEquationInputs.append("distances_" + str(i) + "_costed")
                    i += 1
                # print "DC: min(" + distances_costed_cum + ")*" + str(max_weight)
                self.cumulativeEquation = ("min(" + distances_costed_cum + ")*" + str(max_weight))
                # self.createCumulativeArea()
        else:
            self.findAreaWithRadial(features[0], 0, finish_steps, 0, 0, 0)
            self.cumulativeEquation = "A"
            self.cumulativeEquationInputs = ['distances_0_costed']

        self.widget.runTask(0)
        self.widget.setCursor(Qt.ArrowCursor)
        return "CALCULATED"

    def saveDistancesCostedEquation(self, distances_costed_cum):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        f = open(DATAPATH + '/pracovni/distancesCostedEquation.txt', 'w')
        f.write(distances_costed_cum)
        f.close()

    def addPlaceToTheCenter(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        layer.startEditing()
        fet = QgsFeature()
        center = self.plugin.canvas.center()
        fet.setGeometry(QgsGeometry.fromPointXY(center))
        fet.setAttributes(
            [1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        provider.addFeatures([fet])
        layer.commitChanges()

    def findAreaWithRadial(self, feature, id, finish_steps, azimuth, tolerance, friction):
        DATAPATH = self.Utils.getDataPath()
        geom = feature.geometry()
        pt = geom.asPoint()
        coords = str(pt.x()) + ',' + str(pt.y())
        # writes coord to file
        self.Utils.savePointFeaturesToFile([feature], self.params["epsg"], DATAPATH + "/pracovni/coords_vector_" + str(id) + ".shp")
        QgsMessageLog.logMessage("Coordinates of point " + str(id) + ": " + coords, "Patrac")
        params = {
            "data_path": DATAPATH + "/",
            "pointid": id,
            "persontype": self.params["persontype"],
            "minx": self.params["minx"],
            "maxx": self.params["maxx"],
            "miny": self.params["miny"],
            "maxy": self.params["maxy"],
            "epsg": self.params["epsg"],
            "x": pt.x(),
            "y": pt.y(),
            "finish_steps": finish_steps,
            "azimuth": azimuth,
            "tolerance": tolerance,
            "friction": friction
        }

        self.widget.appendTask(CalculateCostDistanceTask(self.widget, self, params))

    def checkCats(self):
        rules_percentage_path = self.pluginPath + "/grass/rules_percentage.txt"
        if os.path.exists(rules_percentage_path):
            try:
                cats = ["= 10", "= 20", "= 30", "= 40", "= 50", "= 60", "= 70", "= 80", "= 95"]
                cats_count = 0
                with open(rules_percentage_path) as f:
                    lines = f.readlines()
                    for line in lines:
                        for cat in cats:
                            if cat in line:
                                cats_count += 1
                if cats_count != len(cats):
                    return False
                else:
                    return True
            except:
                return False
        else:
            return False

    def azimuth(self, point1, point2):
        '''azimuth between 2 QGIS points ->must be adapted to 0-360°'''
        angle = math.atan2(point2.x() - point1.x(), point2.y() - point1.y())
        angle = math.degrees(angle)
        if angle < 0:
            angle = 360 + angle
        return angle

    def avg_time(self, datetimes):
        """Returns average datetime from two datetimes"""
        epoch = datetime.utcfromtimestamp(0)
        dt1 = (datetimes[0] - epoch).total_seconds()
        dt2 = (datetimes[1] - epoch).total_seconds()
        dt1_dt2 = (dt1 + dt2) / 2
        dt1_dt2_datetime = datetime.utcfromtimestamp(dt1_dt2)
        return dt1_dt2_datetime
        # return datetimes[0]

    def feature_agv_time(self, feature):
        cas_od = feature["cas_od"]
        cas_od_datetime = datetime.strptime(cas_od, '%Y-%m-%d %H:%M:%S')
        cas_do = feature["cas_do"]
        cas_do_datetime = datetime.strptime(cas_do, '%Y-%m-%d %H:%M:%S')
        cas_datetime = self.avg_time([cas_od_datetime, cas_do_datetime])
        return cas_datetime

    def filterAndSortFeatures(self, features):
        items = []
        featuresIndex = 0
        weightLimit = self.Utils.getWeightLimit()
        for feature in features:
            # print("VAHA: " + str(feature["vaha"]))
            if str(feature["vaha"]) == 'NULL' or feature["vaha"] > weightLimit:
                featuresIndex += 1
                index = 0
                for item in items:
                    feature_cas = self.feature_agv_time(feature)
                    item_cas = self.feature_agv_time(item)
                    if feature_cas < item_cas:
                        items.insert(index, feature)
                        break
                    index += 1
                if len(items) < featuresIndex:
                    items.append(feature)
        return items

    def getRadial(self, features):
        """Computes direction of movement"""
        from_geom = None
        to_geom = None
        geom = features[len(features) - 2].geometry()
        from_geom = geom.asPoint()
        geom = features[len(features) - 1].geometry()
        to_geom = geom.asPoint()
        # Computes azimuth from two last points of collection
        azimuth = self.azimuth(from_geom, to_geom)
        QgsMessageLog.logMessage("Azimuth " + str(azimuth), "Patrac")
        # QgsMessageLog.logMessage(u"Čas " + str(cas_datetime_max1) + " Id " + str(id_max1), "Patrac")
        # QgsMessageLog.logMessage(u"Čas " + str(cas_datetime_max2) + " Id " + str(id_max2), "Patrac")
        # cas_diff = cas_datetime_max2 - cas_datetime_max1
        # cas_diff_seconds = cas_diff.total_seconds()
        # QgsMessageLog.logMessage(u"Doba " + str(cas_diff_seconds), "Patrac")
        distance = QgsDistanceArea()
        distance_m = distance.measureLine(from_geom, to_geom)
        QgsMessageLog.logMessage("Distance " + str(distance_m), "Patrac")
        # speed_m_s = distance_m / cas_diff_seconds
        # QgsMessageLog.logMessage(u"Rychlost " + str(speed_m_s), "Patrac")
        return azimuth
