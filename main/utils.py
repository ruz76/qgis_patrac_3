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

class Utils(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas

    def checkLayer(self, name):
        layerExists = False
        for lyr in list(QgsProject.instance().mapLayers().values()):
            QgsMessageLog.logMessage("Check layer: " + name + ": " + lyr.source(), "Patrac")
            if name in lyr.source():
                layerExists = True
                break
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
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
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
        # TODO - maybe just copy the style
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

    def transform_xslt_time(self, pluginpath, xml_filename, output, start, end):
        dom = ET.parse(xml_filename)
        xslt = ET.parse(os.path.join(pluginpath, '/xslt/gpx.xsl'))
        transform = ET.XSLT(xslt)
        newdom = transform(dom, start = ET.XSLT.strparam(start), end = ET.XSLT.strparam(end))
        # print(ET.tostring(newdom, pretty_print=True))