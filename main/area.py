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

class CalculateDistance(QgsTask):
    # This is a lite version of the calculation that does not need GRASS GIS, but it is not so accurate
    def __init__(self, widget, parent, params):
        super().__init__("Calculate Distance Task", QgsTask.CanCancel)
        self.widget = widget
        self.parent = parent
        self.persontype = params["persontype"]
        self.data_path = params["data_path"]
        self.finish_steps = params["finish_steps"]
        self.exception: Optional[Exception] = None

    def run(self):
        try:
            progress = 10
            self.setProgress(progress)

            layer = None
            for lyr in list(QgsProject.instance().mapLayers().values()):
                if self.data_path + "pracovni/sektory_group.shp" in lyr.source():
                    layer = lyr
                    break

            points_layer = None
            for lyr in list(QgsProject.instance().mapLayers().values()):
                if self.data_path + "pracovni/mista.shp" in lyr.source():
                    points_layer = lyr
                    break

            # print(self.data_path)
            # print(layer)
            # print(points_layer)
            layer.setSubsetString('')
            provider = layer.dataProvider()
            points_provider = points_layer.dataProvider()

            features = provider.getFeatures()
            layer.startEditing()
            distances = self.get_distances()
            for feature in features:
                points_features = points_provider.getFeatures()
                dist = 1000000
                for point_feature in points_features:
                    cur_dist = feature.geometry().distance(point_feature.geometry())
                    if cur_dist < dist:
                        dist = cur_dist
                feature['stats_min'] = self.get_percent(distances, dist)
                # feature['percent'] = cur_dist
                layer.updateFeature(feature)
            layer.commitChanges()

            progress = 100
            self.setProgress(progress)

            return True
        except Exception as e:
            # print(str(e))
            QgsMessageLog.logMessage("Error in CalculateDistanceCostedCumulativeTask: " + str(e), "Patrac")
            self.exception = e
            return False

    def finished(self, result):
        QgsMessageLog.logMessage("Task Calculate Distance Task FINISHED", "Patrac")
        if result:
            if self.finish_steps:
                self.widget.finishRecalculateAll()
            else:
                self.widget.finishStep3()

            self.widget.clearMessageBar()
        else:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "Can not compute. Try again, please. Check the position of last seen person. Move the point inside sector that is not a water body. DO not place it on building or encapsulated area, such as power station.", None))
            self.widget.clearMessageBar()

    def get_distances(self):
        with open(self.parent.pluginPath + "/grass/distances.txt") as d:
            lines = d.readlines()
            items = lines[self.persontype].rstrip().split(',')
            return items

    def get_percent(self, distances, cur_distance):
        variables = [10, 20, 30, 40, 50, 60, 70, 80, 95]
        pos = 0
        for distance in distances:
            if cur_distance < float(distance):
                return variables[pos]
            pos += 1
        return 95

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

    def checkPointsIfAreInsideTheArea(self, features):
        result = True
        for feature in features:
            QgsMessageLog.logMessage("Feature: " + str(feature.geometry().asWkt()), "Patrac")
            point = feature.geometry().asPoint()
            if point.x() < (int(self.params['minx']) + 100) \
                    or point.x() > (int(self.params['maxx']) - 100) \
                    or point.y() < (int(self.params['miny']) + 100) \
                    or point.y() > (int(self.params['maxy']) - 100):
                result = False
        return result

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
        result = self.checkPointsIfAreInsideTheArea(features)
        if not result:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "Can not compute. One of the points is out of the project area.", None))
            self.widget.clearMessageBar()
            return

        self.calculatedPoints = []
        self.cumulativeEquationInputs = []
        self.widget.clearTasksList()

        # If there is just one point - impossible to define direction
        # TODO - think more about this check - should be more than two, probably and in some shape as well
        if len(features) > 1:
            azimuth = self.getRadial(features)
            useAzimuth = self.Utils.getProcessRadial()
            QgsMessageLog.logMessage("Masking for azimuth: " + str(azimuth) + " " + str(useAzimuth), "Patrac")
            if azimuth <= 360 and useAzimuth:
                self.findAreaWithRadial(finish_steps, azimuth)
            else:
                self.findAreaWithRadial(finish_steps, 0)
        else:
            self.findAreaWithRadial(finish_steps, 0)

        self.widget.runTask(0)
        self.widget.setCursor(Qt.ArrowCursor)
        return "CALCULATED"

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
        center_map = self.plugin.canvas.center()
        srs = self.canvas.mapSettings().destinationCrs()
        crs_src = QgsCoordinateReferenceSystem(srs)
        crs_dest = QgsCoordinateReferenceSystem(5514)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        center = xform.transform(center_map)
        fet.setGeometry(QgsGeometry.fromPointXY(center))
        fet.setAttributes(
            [1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        provider.addFeatures([fet])
        layer.commitChanges()

    def findAreaWithRadial(self, finish_steps, azimuth):
        DATAPATH = self.Utils.getDataPath()
        params = {
            "data_path": DATAPATH + "/",
            "persontype": self.params["persontype"],
            "minx": self.params["minx"],
            "maxx": self.params["maxx"],
            "miny": self.params["miny"],
            "maxy": self.params["maxy"],
            "epsg": self.params["epsg"],
            "finish_steps": finish_steps,
            "azimuth": azimuth
        }

        self.widget.appendTask(CalculateDistance(self.widget, self, params))

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
