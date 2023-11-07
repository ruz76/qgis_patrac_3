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

from os import path

from datetime import datetime

class Utils(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.layers = {
            "mista.shp": {
                "cs": "Místa",
                "en": "Places",
                "uk": "Місця"
            },
            "mista_linie.shp": {
                "cs": "Místa (linie)",
                "en": "Places (lines)",
                "uk": "Місця (лінія)"
            },
            "mista_polygon.shp": {
                "cs": "Místa (plocha)",
                "en": "Places (area)",
                "uk": "Місця (область)"
            },
            "patraci.shp": {
                "cs": "Pátrači",
                "en": "Searchers",
                "uk": "Пошуковці"
            },
            "sektory_group.shp": {
                "cs": "Sektory",
                "en": "Sectors",
                "uk": "Сектори"
            },
            "distances_costed_cum.tif": {
                "cs": "Procenta",
                "en": "Percent",
                "uk": "Відсоток"
            },
            "zpm.mbtiles": {
                "cs": "zpm",
                "en": "zpm",
                "uk": "zpm"
            }
        }

    def getPluginPath(self):
        return path.dirname(__file__) + "/.."

    def getSettingsPath(self):
        pluginPath = self.getPluginPath()
        return pluginPath + "/../../../patrac_settings"

    def setUTFToAllLayers(self):
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                layer.setProviderEncoding(u'UTF-8')
                layer.dataProvider().setEncoding(u'UTF-8')

    def loadRemovedNecessaryLayers(self):
        layers = ["patraci.shp", "sektory_group.shp", "mista.shp", "mista_linie.shp", "mista_polygon.shp"]
        id = 0
        for layer in layers:
            layerExists = self.checkLayer(layer)
            if not layerExists:
                self.addVectorLayer(self.getDataPath() + "/pracovni/" + layer, self.getLayerName(layers[id]), 5514)
            id += 1

        layer = "distances_costed_cum.tif"
        layerExists = self.checkLayer(layer)
        if not layerExists:
            self.addRasterLayer(self.getDataPath() + "/pracovni/" + layer, self.getLayerName(layer), 5514)

        layer = "zpm.mbtiles"
        layerExists = self.checkLayer(layer)
        if not layerExists:
            self.addRasterLayer(self.getDataPath() + "/../../../" + layer, self.getLayerName(layer), 5514)

    def getLayer(self, name):
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if name in lyr.source():
                layer = lyr
                return layer
        return layer

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
            if path in lyr.source():
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

    def addRasterLayer(self, path, label, crs_code, placement=0):
        """Adds raster layer to map"""
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            QgsMessageLog.logMessage("Can not read layer: " + path, "Patrac")
        else:
            crs = QgsCoordinateReferenceSystem(crs_code)
            raster.setCrs(crs)
            if placement < 0:
                root = QgsProject.instance().layerTreeRoot()
                QgsProject.instance().addMapLayer(raster, False)
                root.insertLayer(len(root.children()) + placement, raster)
            else:
                QgsProject.instance().addMapLayer(raster)

    def addVectorLayer(self, path, label, crs_code):
        """Adds raster layer to map"""
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            crs = QgsCoordinateReferenceSystem(crs_code)
            vector.setCrs(crs)
            vector.setProviderEncoding(u'UTF-8')
            vector.dataProvider().setEncoding(u'UTF-8')
            QgsProject.instance().addMapLayer(vector)

    def addVectorLayerWithStyle(self, path, label, style, crs_code):
        """Adds raster layer to map"""
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            crs = QgsCoordinateReferenceSystem(crs_code)
            vector.setCrs(crs)
            vector.setProviderEncoding(u'UTF-8')
            vector.dataProvider().setEncoding(u'UTF-8')
            vector.loadNamedStyle(self.pluginPath + '/styles/' + style + '.qml')
            QgsProject.instance().addMapLayer(vector)

    def setLayerCrs(self, path, code):
        crs = QgsCoordinateReferenceSystem(code)
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.source() == path:
                layer = lyr
                break
        if layer is not None:
            if layer.isValid():
                layer.setCrs(crs)

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

    def createProjectInfo(self, projectname, projectdesc, version, minx, maxx, miny, maxy, epsg):
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
            "gina_guid": "",
            "sectors_type": 0,
            "epsg": epsg,
            "minx": minx,
            "maxx": maxx,
            "miny": miny,
            "maxy": maxy
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

    def backupSectors(self, type):
        copy(self.getDataPath() + "/pracovni/sektory_group.shp", self.getDataPath() + "/pracovni/sektory_group_" + type + ".shp")
        copy(self.getDataPath() + "/pracovni/sektory_group.shx", self.getDataPath() + "/pracovni/sektory_group_" + type + ".shx")
        copy(self.getDataPath() + "/pracovni/sektory_group.dbf", self.getDataPath() + "/pracovni/sektory_group_" + type + ".dbf")
        copy(self.getDataPath() + "/pracovni/sektory_group.prj", self.getDataPath() + "/pracovni/sektory_group_" + type + ".prj")

    def restoreSectors(self, type):
        if not os.path.exists(self.getDataPath() + "/pracovni/sektory_group_" + type + ".shp"):
            QgsMessageLog.logMessage("Vrstvu " + self.getDataPath() + "/pracovni/sektory_group_" + type + ".shp" + " se nepodařilo najít", "Patrac")
            return
        self.removeLayer(self.getDataPath() + "/pracovni/sektory_group.shp")
        copy(self.getDataPath() + "/pracovni/sektory_group_" + type + ".shp", self.getDataPath() + "/pracovni/sektory_group.shp")
        copy(self.getDataPath() + "/pracovni/sektory_group_" + type + ".shx", self.getDataPath() + "/pracovni/sektory_group.shx")
        copy(self.getDataPath() + "/pracovni/sektory_group_" + type + ".dbf", self.getDataPath() + "/pracovni/sektory_group.dbf")
        copy(self.getDataPath() + "/pracovni/sektory_group_" + type + ".prj", self.getDataPath() + "/pracovni/sektory_group.prj")
        self.addVectorLayerWithStyle(self.getDataPath() + "/pracovni/sektory_group.shp", self.getLayerName("sektory_group.shp"), "sectors_single", 5514)

    def createUTMSectors(self, cellsize):
        with open(self.getDataPath() + '/config/extent.txt') as f:
            lines = f.readlines()
            parts = lines[0].split(' ')

        source_crs = QgsCoordinateReferenceSystem(5514)
        dest_crs = QgsCoordinateReferenceSystem(32633)
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        minXY_UTM = transform.transform(int(parts[0]), int(parts[1]))
        maxXY_UTM = transform.transform(int(parts[2]), int(parts[3]))

        # cellsize = 1000
        # print(minXY_UTM)
        # print(maxXY_UTM)

        minx = int(minXY_UTM.x() / cellsize) * cellsize - cellsize
        miny = int(minXY_UTM.y() / cellsize) * cellsize - cellsize
        maxx = int(maxXY_UTM.x() / cellsize) * cellsize + cellsize
        maxy = int(maxXY_UTM.y() / cellsize) * cellsize + cellsize

        print(minx, miny, maxx, maxy)

        self.createUTMSectorsGrid([minx, miny, maxx, maxy], cellsize)

    def importSwitchedSectorsToDatastore(self):
        if sys.platform.startswith('win'):
            p = subprocess.Popen(
                (self.pluginPath + "/grass/run_import_after_switch_type.bat", self.getDataPath(), self.pluginPath))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_import_after_switch_type.sh", self.getDataPath(), self.pluginPath))
            p.wait()

    def getGridSectorLabel(self, minx, miny, cellsize):
        kmstrx = str(minx)[-5:]
        kmstry = str(miny)[-5:]
        x = kmstrx[0:3]
        y = kmstry[0:3]
        if cellsize == 10:
            x = kmstrx[0:4]
            y = kmstry[0:4]
        if cellsize == 1000:
            x = kmstrx[0:2]
            y = kmstry[0:2]
        return x + "-" + y

    def createUTMSectorsGrid(self, extent, cellsize):
        self.removeLayer(self.getDataPath() + "/pracovni/sektory_group.shp")

        layer = QgsVectorLayer(self.getDataPath() + "/pracovni/sektory_group.shp", "sektory", "ogr")
        if layer is not None:
            layer.setSubsetString("")
            provider = layer.dataProvider()
            listOfIds = [feat.id() for feat in layer.getFeatures()]
            # Deletes all features in layer patraci.shp
            layer.startEditing()
            layer.deleteFeatures(listOfIds)
            layer.commitChanges()
        else:
            return

        cols = int((extent[2] - extent[0]) / cellsize)
        rows = int((extent[3] - extent[1]) / cellsize)
        minx = extent[0]
        miny = extent[1]
        # ch = 'A'
        id = 0
        for col in range(cols):
            for row in range(rows):
                geom = self.getUTMGridPolygon(minx, miny, cellsize)
                label = self.getGridSectorLabel(minx, miny, cellsize)
                cols = [id, label, 'MIX', None, None, (cellsize * cellsize) / 10000, None, None, None]
                self.saveUTMGridPolygon(provider, geom, cols)
                miny = miny + cellsize
                id += 1
            minx = minx + cellsize
            miny = extent[1]
            # ch = chr(ord(ch) + 1)

        layer.commitChanges()

        self.addVectorLayerWithStyle(self.getDataPath() + "/pracovni/sektory_group.shp", self.getLayerName("sektory_group.shp"), "sectors_single", 5514)

    def getUTMGridPolygon(self, minx, miny, cellsize):
        maxx = minx + cellsize
        maxy = miny + cellsize
        wkt = "POLYGON((" + str(minx) + " " + str(miny)\
              + ", " + str(maxx) + " " + str(miny)\
              + ", " + str(maxx) + " " + str(maxy)\
              + ", " + str(minx) + " " + str(maxy)\
              + ", " + str(minx) + " " + str(miny) + "))"

        source_crs = QgsCoordinateReferenceSystem(32633)
        dest_crs = QgsCoordinateReferenceSystem(5514)
        tr = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        geom = QgsGeometry.fromWkt(wkt)
        geom.transform(tr)
        # print(geom.asWkt())
        return geom

    def saveUTMGridPolygon(self, provider, geom, cols):
        fet = QgsFeature()
        # Name and sessionid are on first and second place
        fet.setAttributes(cols)
        fet.setGeometry(geom)
        provider.addFeatures([fet])

    def getLostInfo(self, project_settings):
        lost_info = "Pohřešovaná osoba: "
        if project_settings["lost_name"] != "":
            lost_info += project_settings["lost_name"]
            if project_settings["lost_sex"] == 0:
                lost_info += ", Muž"
            if project_settings["lost_sex"] == 1:
                lost_info += ", Žena"
            lost_info += ", Věk: " + str(project_settings["lost_age"])
            if project_settings["lost_clothes"] != "":
                lost_info += ", Oblečení: " + project_settings["lost_clothes"]

        if lost_info == "Pohřešovaná osoba: ":
            lost_info += "neuvedeno"

        return lost_info

    def getDateTimeFromTimestamp(self, ts):
        try:
            dt_object = datetime.fromtimestamp(int(ts))
            return str(dt_object)
        except:
            return ""

    def getDiffOfTimestampFromNow(self, ts):
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        try:
            diff = timestamp - int(ts)
            return diff
        except:
            return 100000

    def savePointFeaturesToFile(self, features, epsg, file_path):
        # Create layer with result
        uri = "Point?crs=epsg:" + str(epsg) + "&index=yes"

        mem_layer = QgsVectorLayer(uri,
                                   'points',
                                   'memory')

        prov = mem_layer.dataProvider()

        # feats = [ QgsFeature() for i in range(len(features)) ]
        #
        # for i, feat in enumerate(feats):
        #     feat.setAttributes([i])
        #     feat.setGeometry(features[i])

        prov.addFeatures(features)

        crs = QgsCoordinateReferenceSystem("EPSG:" + str(epsg))
        QgsVectorFileWriter.writeAsVectorFormat(mem_layer, file_path,
                                                "utf-8", crs, "ESRI Shapefile")


    def saveMistaModificationTime(self):
        DATAPATH = self.getDataPath()
        with open(DATAPATH + '/pracovni/data_modified.json', 'w') as out:
            mod = {
                "mista_shp": os.path.getmtime(DATAPATH + '/pracovni/mista.shp'),
                "mista_dbf": os.path.getmtime(DATAPATH + '/pracovni/mista.dbf'),
                "sectors_shp": os.path.getmtime(DATAPATH + '/pracovni/sektory_group.shp'),
                "sectors_dbf": os.path.getmtime(DATAPATH + '/pracovni/sektory_group.dbf'),
                "weightlimit": os.path.getmtime(DATAPATH + '/config/weightlimit.txt'),
                "radialsettings": os.path.getmtime(DATAPATH + '/config/radialsettings.txt'),
            }
            out.write(json.dumps(mod))

    def hasBeenDataModified(self):
        DATAPATH = self.getDataPath()
        if os.path.exists(DATAPATH + '/pracovni/data_modified.json'):
            with open(DATAPATH + '/pracovni/data_modified.json') as modfile:
                mod = json.load(modfile)
                mista_shp = os.path.getmtime(DATAPATH + '/pracovni/mista.shp')
                mista_dbf = os.path.getmtime(DATAPATH + '/pracovni/mista.dbf')
                sectors_shp = os.path.getmtime(DATAPATH + '/pracovni/sektory_group.shp')
                sectors_dbf = os.path.getmtime(DATAPATH + '/pracovni/sektory_group.dbf')
                weightlimit = os.path.getmtime(DATAPATH + '/config/weightlimit.txt')
                radialsettings = os.path.getmtime(DATAPATH + '/config/radialsettings.txt')
                if mod['mista_shp'] != mista_shp \
                        or mod['mista_dbf'] != mista_dbf \
                        or mod['sectors_shp'] != sectors_shp \
                        or mod['sectors_dbf'] != sectors_dbf \
                        or mod['weightlimit'] != weightlimit \
                        or mod["radialsettings"] != radialsettings:
                    return True
                else:
                    return False
        else:
            return True

    def getLastSectorId(self):
        DATAPATH = self.getDataPath()
        if os.path.exists(DATAPATH + '/config/lastsectorid.txt'):
            with open(DATAPATH + '/config/lastsectorid.txt') as lastsectorid_file:
                try:
                    lastsectorid = int(lastsectorid_file.read())
                    return lastsectorid
                except ValueError:
                    return 1000000
        else:
            return 1000000

    def writeLastSectorId(self, value):
        DATAPATH = self.getDataPath()
        with open(DATAPATH + '/config/lastsectorid.txt', "w") as out:
            out.write(str(value))

    def renameLayers(self):
        locale = self.getLocale()

        for key in self.layers:
            layer = self.getLayer(key)
            if layer is not None:
                layer.setName(self.layers[key][locale])

    def setGlobalVariables(self):
        zpm_update = '2022-01-01'
        sectors_update = '2023-09-08'
        variables = {
            "zpm_update": {
                "cs": "ZPM aktualizace: " + zpm_update,
                "en": "ZPM update: " + zpm_update,
                "uk": "ЗПМ оновлення: " + zpm_update
            },
            "sectors_update": {
                "cs": "Sektory aktualizace: " + sectors_update,
                "en": "Sectors update: " + sectors_update,
                "uk": "Сектори оновлення: " + sectors_update
            },
            "print_label": {
                "cs": "Tisk",
                "en": "Print",
                "uk": "Друк"
            },
            "contour_line_label": {
                "cs": "Vrstevnice",
                "en": "Contour lines",
                "uk": "Контурна лінія"
            },
        }

        locale = self.getLocale()

        for key in variables:
            QgsExpressionContextUtils.setGlobalVariable(key, variables[key][locale])

    def getLocale(self):
        overrideLocale = bool(QSettings().value("locale/overrideFlag", False))
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")
        locale = localeFullName[:2]
        if locale in ['cs', 'en', 'uk']:
            return locale
        else:
            return 'en'

    def getLayerName(self, key):
        locale = self.getLocale()
        if key in self.layers:
            return self.layers[key][locale]
        else:
            return "Unknown"
