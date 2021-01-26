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

import csv, io, math, subprocess, os, sys, uuid, json

from qgis.core import *
from qgis.gui import *
from shutil import copy

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Utils(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas

    def loadRemovedNecessaryLayers(self):
        layers = ["patraci.shp", "sektory_group.shp", "mista.shp", "mista_linie.shp", "mista_polygon.shp"]
        layers_titles = ["patraci", "sektory", "mista", "mista_linie", "mista_polygon"]
        id = 0
        for layer in layers:
            layerExists = self.checkLayer(layer)
            if not layerExists:
                self.addVectorLayer(self.getDataPath() + "/pracovni/" + layer, layers_titles[id])
            id += 1

        layer = "distances_costed_cum.tif"
        layerExists = self.checkLayer(layer)
        if not layerExists:
            self.addRasterLayer(self.getDataPath() + "/pracovni/" + layer, "procenta")

        layer = "zpm.mbtiles"
        layerExists = self.checkLayer(layer)
        if not layerExists:
            self.addRasterLayer(self.getDataPath() + "/../../../" + layer, "zpm")

    def checkLayer(self, name):
        layerExists = False
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if name in lyr.source():
                layerExists = True
                break
        if not layerExists:
            QgsMessageLog.logMessage("Check layer: " + name, "Patrac")
        return layerExists

    def removeLayer(self, path):
        """Removes layer based on path to file"""
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == path:
                layer = lyr
                break
        if layer is not None:
            if layer.isValid():
                QgsProject.instance().removeMapLayer(layer)
        return

    def copyOnlineTrackLayer(self, DATAPATH, name):
        copy(DATAPATH + "/pracovni/patraci_lines.shp", DATAPATH + "/search/shp/" + name + ".shp")
        copy(DATAPATH + "/pracovni/patraci_lines.shx", DATAPATH + "/search/shp/" + name + ".shx")
        copy(DATAPATH + "/pracovni/patraci_lines.dbf", DATAPATH + "/search/shp/" + name + ".dbf")

    def copyLayer(self, DATAPATH, name):
        copy(DATAPATH + "/sektory/shp/template.shp", DATAPATH + "/sektory/shp/" + name + ".shp")
        copy(DATAPATH + "/sektory/shp/template.shx", DATAPATH + "/sektory/shp/" + name + ".shx")
        copy(DATAPATH + "/sektory/shp/template.dbf", DATAPATH + "/sektory/shp/" + name + ".dbf")
        # copy(DATAPATH + "/sektory/shp/template.prj", DATAPATH + "/sektory/shp/" + name + ".prj")
        copy(DATAPATH + "/sektory/shp/template.qml", DATAPATH + "/sektory/shp/" + name + ".qml")
        # copy(DATAPATH + "/sektory/shp/template.qpj", DATAPATH + "/sektory/shp/" + name + ".qpj")

    def addRasterLayer(self, path, label):
        """Adds raster layer to map"""
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            QgsMessageLog.logMessage("Can not read layer: " + path, "Patrac")
        else:
            ##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsProject.instance().addMapLayer(raster)

    def addVectorLayer(self, path, label):
        """Adds raster layer to map"""
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            ##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsProject.instance().addMapLayer(vector)

    def addVectorLayerWithStyle(self, path, label, style):
        """Adds raster layer to map"""
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            vector.loadNamedStyle(self.pluginPath + '/styles/' + style + '.qml')
            QgsProject.instance().addMapLayer(vector)

    def getProcessRadial(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        processRadial = open(DATAPATH + '/config/radialsettings.txt', 'r').read()
        processRadial = processRadial.strip()
        if (processRadial == "0"):
            return False
        else:
            return True

    def getWeightLimit(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        weightLimit = open(DATAPATH + '/config/weightlimit.txt', 'r').read()
        weightLimit = weightLimit.strip()
        if weightLimit.isdigit():
            return int(weightLimit)
        else:
            return 1

    def setStyle(self, path, name):
        """Copies style and replaces some definitions"""
        qml = open(path + 'style.qml', 'r').read()
        f = open(path + name + '.qml', 'w')
        qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

    def dump(self, obj):
        for attr in dir(obj):
            if hasattr(obj, attr):
                print(("obj.%s = %s" % (attr, getattr(obj, attr))))

    def featureIntersects(self, featureToCheck, geometries):
        # does not work, and if it works it will be slow
        # print("START INTERSECT")
        for geometry in geometries:
            # print("FEATURE:" + geometry.exportToWkt())
            # print("featureToCheck:" + featureToCheck.geometry().exportToWkt())
            if geometry.intersects(featureToCheck.geometry()):
                return True
        return False

    def getDataPath(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        return prjfi.absolutePath()

    def creation_date(self, path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if sys.platform.startswith('win'):
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def getDrivesList(self):
        letters = "CDEFGHIJKLMNOPQRSTUVWXYZ"
        return [letters[i] + ":/" for i in range(len(letters))]

    def createProjectInfo(self, projectname, projectdesc, version):
        project_info = {
            "projectname": projectname,
            "projectdesc": projectdesc,
            "projectversion": version,
            "coordinatorname": "",
            "coordinatortel": "",
            "placehandlers": "",
            "placehandlers_lat": 0.0,
            "placehandlers_lon": 0.0,
            "placeother": "",
            "placeother_lat": 0.0,
            "placeother_lon": 0.0,
            "lost_name": "",
            "lost_sex": 0,
            "lost_age": 0,
            "lost_from_date_time": "",
            "lost_time_from_info": "",
            "lost_physical_condition": 0,
            "lost_health": 0,
            "lost_height": 0,
            "lost_body_type": 0,
            "lost_hair_color": 0,
            "lost_clothes": "",
            "hs_incidentid": "0",
            "gina_guid": ""
        }

        with open(self.getDataPath() + "/pracovni/project.json", 'w') as outfile:
            json.dump(project_info, outfile)

    def getProjectInfo(self):
        if os.path.exists(self.getDataPath() + "/pracovni/project.json"):
            with open(self.getDataPath() + "/pracovni/project.json") as json_file:
                return json.load(json_file)
        else:
            return None

    def updateProjectInfo(self, key, value):
        project_info = self.getProjectInfo()
        if project_info is None:
            # TODO get name form filename QgsProject.instance().fileName()
            self.createProjectInfo("Noname testing", "Noname description", 0)
            project_info = self.getProjectInfo()

        project_info[key] = value

        with open(self.getDataPath() + "/pracovni/project.json", 'w') as outfile:
            json.dump(project_info, outfile)
