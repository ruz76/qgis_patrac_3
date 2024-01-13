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

import csv, io, math, urllib.request, urllib.error, urllib.parse, socket, subprocess, os, sys, uuid, json

from qgis.core import *
from qgis.gui import *

from urllib.parse import quote
from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

import processing

from .. connect.connect import *

class ClipSourceDataTask(QgsTask):
    def __init__(self, widget, params):
        super().__init__("Patrac task", QgsTask.CanCancel)
        self.widget = widget
        self.exception: Optional[Exception] = None
        # self.source_path = "/data/patracdata/kraje/ka/"
        # self.target_path = "/data/patracdata/kraje/ka/projekty/testing/"
        # self.minx = -857031.912000000
        # self.maxx = -849227.571900000
        # self.miny = -1028202.161000000
        # self.maxy = -1021136.837500000
        # self.epsg = 5514
        self.source_path = params["source_path"]
        self.target_path = params["target_path"]
        self.minx = params["minx"]
        self.maxx = params["maxx"]
        self.miny = params["miny"]
        self.maxy = params["maxy"]
        self.epsg = params["epsg"]
        self.type = params["type"]

    def get_proj_win(self):
        return str(self.minx) + ',' + str(self.maxx) + ',' + str(self.miny) + ',' + str(self.maxy) + ' [EPSG:' + str(self.epsg) + ']'

    def run(self):
        try:
            self.setProgress(5)
            processing.run(
                "native:extractbyextent",
                {
                    'INPUT':self.source_path + 'vektor/ZABAGED/vodtok.shp',
                    'EXTENT':self.get_proj_win(),
                    'CLIP':False,
                    'OUTPUT':self.target_path + 'pracovni/vodtok.shp'
                }
            )
            self.setProgress(20)
            processing.run(
                "native:extractbyextent",
                {
                    'INPUT':self.source_path + 'vektor/ZABAGED/cesta.shp',
                    'EXTENT':self.get_proj_win(),
                    'CLIP':False,
                    'OUTPUT':self.target_path + 'pracovni/cesta.shp'
                }
            )
            self.setProgress(40)
            processing.run(
                "native:extractbyextent",
                {
                    'INPUT':self.source_path + 'vektor/ZABAGED/lespru.shp',
                    'EXTENT':self.get_proj_win(),
                    'CLIP':False,
                    'OUTPUT':self.target_path + 'pracovni/lespru.shp'
                }
            )
            self.setProgress(60)
            vector_output_name = 'sektory_group'
            if self.type == 'extend':
                vector_output_name = 'sectors_group_to_append'
            processing.run(
                "native:extractbyextent",
                {
                    'INPUT':self.source_path + 'vektor/ZABAGED/sectors.shp',
                    'EXTENT':self.get_proj_win(),
                    'CLIP':False,
                    'OUTPUT':self.target_path + 'pracovni/' + vector_output_name + '.shp'
                }
            )
            self.setProgress(80)
            layer = QgsVectorLayer(self.target_path + 'pracovni/' + vector_output_name + '.shp', "mylayer", "ogr")
            layer.startEditing()
            QgsMessageLog.logMessage("ADDING fields", "Patrac")
            stavField = QgsField('stav', QVariant.Int)
            prostredkyField = QgsField('prostredky', QVariant.String)
            area_haField = QgsField('area_ha', QVariant.Double)
            poznamkaField = QgsField('poznamka', QVariant.String)
            od_casField = QgsField('od_cas', QVariant.String)
            do_casField = QgsField('do_cas', QVariant.String)
            percentField = QgsField('stats_min', QVariant.Double)
            layer.dataProvider().addAttributes([stavField, prostredkyField, area_haField, poznamkaField, od_casField, do_casField, percentField])
            layer.updateFields()
            layer.commitChanges()
            layer.startEditing()
            features = layer.dataProvider().getFeatures()
            for feature in features:
                area_ha = round(feature.geometry().area() / 10000, 1)
                if area_ha < 1:
                    feature['area_ha'] = area_ha
                else:
                    feature['area_ha'] = round(area_ha)
                layer.updateFeature(feature)
            layer.commitChanges()
            progress = 100
            if self.type == 'extend':
                progress = 95
            self.setProgress(progress)
            return True
        except Exception as e:
            self.exception = e
            QgsMessageLog.logMessage("ERROR in ClipSourceDataTask " + str(e), "Patrac")
            return False

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage("ClipSourceDataTask FINISHED", "Patrac")
            if self.type == 'initial':
                self.widget.finishStep1()
                self.widget.clearMessageBar()
            if self.type == 'extend':
                self.widget.appendSectors()
        else:
            QMessageBox.critical(None, QApplication.translate("Patrac", "CRITICAL ERROR", None),
                                 QApplication.translate("Patrac", "Can not create project. Check the data. Try to update data is Settings.", None))
            self.widget.clearMessageBar()

class Project(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.serverUrl = self.widget.serverUrl
        self.settingsPath = self.pluginPath + "/../../../patrac_settings"
        with open(self.settingsPath + "/config/config.json") as c:
            self.config = json.load(c)

    def copyTemplate(self, NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE):
        if not os.path.isdir(NEW_PROJECT_PATH):
            os.mkdir(NEW_PROJECT_PATH)

            # sets the settings to zero, so no radial and no weight limit is used
            os.mkdir(NEW_PROJECT_PATH + "/config")
            copy(self.settingsPath + "/grass/" + "weightlimit.txt", NEW_PROJECT_PATH + '/config/weightlimit.txt')
            copy(self.settingsPath + "/grass/" + "maxtime.txt", NEW_PROJECT_PATH + '/config/maxtime.txt')
            copy(self.settingsPath + "/grass/" + "radialsettings.txt", NEW_PROJECT_PATH + '/config/radialsettings.txt')

            copy(TEMPLATES_PATH + "/projekt/clean_v3.qgs", NEW_PROJECT_PATH + "/" + NAMESAFE + ".qgs")
            os.mkdir(NEW_PROJECT_PATH + "/pracovni")
            for file in glob(TEMPLATES_PATH + '/projekt/pracovni/*'):
                copy(file, NEW_PROJECT_PATH + "/pracovni/")
            copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.dbf",
                 NEW_PROJECT_PATH + "/pracovni/sektory_group.dbf")
            copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.shp",
                 NEW_PROJECT_PATH + "/pracovni/sektory_group.shp")
            copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.shx",
                 NEW_PROJECT_PATH + "/pracovni/sektory_group.shx")
            copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.qml",
                 NEW_PROJECT_PATH + "/pracovni/sektory_group.qml")
            os.mkdir(NEW_PROJECT_PATH + "/search")
            copy(TEMPLATES_PATH + "/projekt/search/sectors.txt", NEW_PROJECT_PATH + "/search/")
            os.mkdir(NEW_PROJECT_PATH + "/search/gpx")
            os.mkdir(NEW_PROJECT_PATH + "/search/shp")
            copy(TEMPLATES_PATH + "/projekt/search/shp/style.qml", NEW_PROJECT_PATH + "/search/shp/")
            os.mkdir(NEW_PROJECT_PATH + "/search/temp")
            os.mkdir(NEW_PROJECT_PATH + "/sektory")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/gpx")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/shp")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/pdf")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/html")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/styles")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/shp/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/shp/")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/styles/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/styles/")
            os.mkdir(NEW_PROJECT_PATH + "/raster")
            os.mkdir(NEW_PROJECT_PATH + "/vektor")

    def getSafeDirectoryName(self, name):
        name = name.lower()
        replace = ['a', 'c', 'd', 'e', 'e', 'i', 'n', 'o', 'r', 's', 't', 'u', 'u', 'y', 'z', '_', '_', '_', '_', '_', '_']
        position = 0
        for ch in ['á', 'č', 'ď', 'ě', 'é', 'í', 'ň', 'ó', 'ř', 'š', 'ť', 'ú', 'ů', 'ý', 'ž', ' ', '(', ')', '.', ':', ',']:
            if ch in name:
                name = name.replace(ch, replace[position])
            position = position + 1
        return name

    def getSimpleProjectDataPath(self):
        DATAPATH = ''
        letters = "CDEFGHIJKLMNOPQRSTUVWXYZ"
        drives = [letters[i] + ":/" for i in range(len(letters))]
        for drive in drives:
            if os.path.isfile(drive + 'patracdata/cr/projekty/simple/simple.qgs'):
                DATAPATH = drive + 'patracdata/cr/projekty/simple/'
                break
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/cr/projekty/simple/'

        return DATAPATH

    def getRegionDataPath(self):
        DATAPATH = ''
        letters = "CDEFGHIJKLMNOPQRSTUVWXYZ"
        drives = [letters[i] + ":/" for i in range(len(letters))]
        for drive in drives:
            if os.path.isfile(drive + 'patracdata/cr/projekty/simple/simple.qgs'):
                DATAPATH = drive + 'patracdata/cr/projekty/simple/'
                break
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/cr/projekty/simple/'

        return DATAPATH

    def checkRegion(self, region):
        if region is not None:
            region = region.lower()
        else:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Out of Czech Republic. Can not continue.", None))
            return None

        regionOut = None
        QgsMessageLog.logMessage("Region: " + region, "Patrac")
        QgsMessageLog.logMessage("Datapath: " + self.config['data_path'], "Patrac")
        if os.path.isfile(self.config['data_path'] + 'kraje/' + region + '/metadata.json'):
            with open(self.config['data_path'] + 'kraje/' + region + '/metadata.json') as m:
                metadata = json.load(m)
                if metadata['version'] == '2023-09-08':
                    regionOut = region

        return regionOut

    def checkRegionExtent(self):
        if (self.canvas.extent().width() > 10000) or (self.canvas.extent().height() > 10000):
            reply = QMessageBox.question(self, QApplication.translate("Patrac", 'Region', None),
                                                                      QApplication.translate("Patrac", 'The area is large. Computing will be slow. Do you want to continue?', None),
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return True
            else:
                return False
        else:
            return True

    def createProject(self, index, desc, version):
        # Check if the project has okresy_pseudo.shp

        QgsMessageLog.logMessage("CREATING PROJECT", "Patrac")

        name = self.widget.municipalities_names[index]
        region = self.widget.municipalities_regions[index]
        region = self.checkRegion(region)

        if region is None:
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                                                 QApplication.translate("Patrac", "Do not have data for seleted region. Can not continue.", None))
            self.widget.showSettings()
            self.widget.setCursor(Qt.ArrowCursor)
            return

        self.widget.setCursor(Qt.WaitCursor)
        if name == '':
            name = 'noname_' + strftime("%Y-%m-%d_%H-%M-%S", gmtime())
            QgsMessageLog.logMessage("Noname: " + name, "Patrac")
        else:
            name = name + "_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime())

        NAMESAFE = self.getSafeDirectoryName(name)

        items = self.widget.municipalities_coords[index].split(";")
        x = int(items[0])
        y = int(items[1])
        XMIN = str(x - 6000)
        YMIN = str(y - 5000)
        XMAX = str(x + 6000)
        YMAX = str(y + 5000)
        QgsMessageLog.logMessage("g.region e=" + XMAX + " w=" + XMIN + " n=" + YMAX + " s=" + YMIN, "Patrac")
        QgsMessageLog.logMessage("Name: " + NAMESAFE, "Patrac")

        DATAPATH = self.config["data_path"]

        NEW_PROJECT_PATH = DATAPATH + "kraje/" + region + "/projekty/" + NAMESAFE
        # set working dir to new path
        QSettings().setValue("UI/lastProjectDir", DATAPATH + "kraje/" + region + "/projekty/" + NAMESAFE)

        TEMPLATES_PATH = self.pluginPath + "/templates"
        self.copyTemplate(NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE)
        copy(DATAPATH + "kraje/" + region + "/vektor/ZABAGED/lastsectorid.txt", NEW_PROJECT_PATH + '/config/lastsectorid.txt')

        # TODO make it globally
        epsg = 5514

        params = {
            "source_path": DATAPATH + "kraje/" + region + "/",
            "target_path": DATAPATH + "kraje/" + region + "/projekty/" + NAMESAFE + "/",
            "minx": XMIN,
            "maxx": XMAX,
            "miny": YMIN,
            "maxy": YMAX,
            "epsg": epsg,
            "type": "initial"
        }

        self.widget.createProgressBar(QApplication.translate("Patrac", "Loading data: ", None))
        self.widget.clearTasksList()
        self.widget.appendTask(ClipSourceDataTask(self.widget, params))
        self.widget.runTask(0)
        # print("TASK STARTED")

        return {
            "name": name,
            "desc": desc,
            "region": region,
            "version": version,
            "NEW_PROJECT_PATH": NEW_PROJECT_PATH,
            "NAMESAFE": NAMESAFE,
            "XMIN": XMIN,
            "YMIN": YMIN,
            "XMAX": XMAX,
            "YMAX": YMAX,
            "epsg": epsg
        }

    def finishCreateProject(self, params):
        if os.path.exists(params["NEW_PROJECT_PATH"] + '/pracovni/sektory_group.qix'):
            os.remove(params["NEW_PROJECT_PATH"] + '/pracovni/sektory_group.qix')

        project = QgsProject.instance()
        QgsMessageLog.logMessage(params["NEW_PROJECT_PATH"] + '/' + params["NAMESAFE"] + '.qgs', "Patrac")
        project.read(params["NEW_PROJECT_PATH"] + '/' + params["NAMESAFE"] + '.qgs')

        with open(self.pluginPath + "/config/lastprojectpath.txt", "w") as f:
            f.write(params["NEW_PROJECT_PATH"])

        # self.do_msearch()
        self.zoomToExtent(params["XMIN"], params["YMIN"], params["XMAX"], params["YMAX"])

        # self.widget.Sectors.recalculateSectors(True, False)
        self.createNewSearch(params["name"], params["desc"], params["region"], params["version"])
        self.widget.settingsdlg.updateSettings()
        self.saveRegion(params["region"], params["NEW_PROJECT_PATH"])
        self.saveExtent(params["XMIN"], params["YMIN"], params["XMAX"], params["YMAX"], params["NEW_PROJECT_PATH"])

        if os.path.exists(self.config['zpm_path']):
            self.widget.Utils.addRasterLayer(self.config['zpm_path'], 'zpm', 3857, -1)
        else:
            reply = QMessageBox.question(None,
                                         QApplication.translate("Patrac", 'ZPM', None), QApplication.translate("Patrac", 'Can not find ZPM map. Do you wan to find it yourself?', None),
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                options = QFileDialog.Options()
                fileName, _ = QFileDialog.getOpenFileName(self.widget, "ZPM", "", "All Files (*);;MBTiles Files (*.mbtiles)", options=options)
                if fileName:
                    self.widget.Utils.addRasterLayer(fileName, 'zpm', 3857, -1)
                    self.config['zpm_path'] = fileName
                    with open(self.settingsPath + "/config/config.json", "w") as outfile:
                        json.dump(self.config, outfile)

        self.widget.Utils.removeLayer(params["NEW_PROJECT_PATH"] + '/pracovni/distances_costed_cum.tif')

        self.iface.mapCanvas().refresh()
        self.widget.setCursor(Qt.ArrowCursor)

    def saveRegion(self, region, DATAPATH):
        QgsMessageLog.logMessage("Saving region: " + region + " to " + DATAPATH + '/config/region.txt', "Patrac")
        f = open(DATAPATH + '/config/region.txt', 'w')
        f.write(region)
        f.close()

    def saveExtent(self, XMIN, YMIN, XMAX, YMAX, DATAPATH):
        QgsMessageLog.logMessage("Saving extent to " + DATAPATH + '/config/extent.txt', "Patrac")
        f = open(DATAPATH + '/config/extent.txt', 'w')
        f.write(XMIN + " " + YMIN + " " + XMAX + " " + YMAX)
        f.close()

    def zoomToExtent(self, XMIN, YMIN, XMAX, YMAX):
        rect = QgsRectangle(float(XMIN), float(YMIN), float(XMAX), float(YMAX))
        srs = self.canvas.mapSettings().destinationCrs()
        current_crs = srs.authid()
        if current_crs == "EPSG:5514":
            self.canvas.setExtent(rect)
        else:
            srs = self.canvas.mapSettings().destinationCrs()
            crs_src = QgsCoordinateReferenceSystem(5514)
            crs_dest = QgsCoordinateReferenceSystem(srs)
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            extent = xform.transform(rect)
            self.canvas.setExtent(extent)
        self.canvas.refresh()

    def createNewSearch(self, name, desc, region, version):
        QgsMessageLog.logMessage("Vytvářím nové pátrání: " + name + " " + region, "Patrac")
        searchid = self.createSearchId(name)

    def createSearchId(self, name):
        dirname = self.getSafeDirectoryName(name.split(" ")[0])
        start = dirname.replace("_", "").replace("?", "")
        searchid = start + str(uuid.uuid4()).replace("-", "")
        searchid20 = searchid[:20]
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        f = io.open(DATAPATH + '/config/searchid.txt', 'w', encoding='utf-8')
        f.write(searchid20)
        f.close()
        return searchid20

    def extendRegion(self):

        self.widget.Utils.loadRemovedNecessaryLayers()

        # Check if the project has sektory_group_selected.shp
        if not self.widget.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, QApplication.translate("Patrac", "ERROR", None),
                                    QApplication.translate("Patrac", "Wrong project.", None))
            return

        self.widget.setCursor(Qt.WaitCursor)

        with open(self.widget.Utils.getDataPath() + '/config/extent.txt') as e:
            initialExtent = e.read()
        initialExtentItems = initialExtent.split(" ")

        CMINX = self.canvas.extent().xMinimum()
        CMINY = self.canvas.extent().yMinimum()
        CMAXX = self.canvas.extent().xMaximum()
        CMAXY = self.canvas.extent().yMaximum()

        source_crs = self.canvas.mapSettings().destinationCrs()
        current_crs = source_crs.authid()
        if current_crs != "EPSG:5514":
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            minJTSK = transform.transform(float(CMINX), float(CMINY))
            CMINX = minJTSK.x()
            CMINY = minJTSK.y()
            maxJTSK = transform.transform(float(CMAXX), float(CMAXY))
            CMAXX = maxJTSK.x()
            CMAXY = maxJTSK.y()

        XMIN = str(CMINX) \
            if CMINX < float(initialExtentItems[0]) else initialExtentItems[0]
        YMIN = str(CMINY) \
            if CMINY < float(initialExtentItems[1]) else initialExtentItems[1]
        XMAX = str(CMAXX) \
            if CMAXX > float(initialExtentItems[2]) else initialExtentItems[2]
        YMAX = str(CMAXY) \
            if CMAXY > float(initialExtentItems[3]) else initialExtentItems[3]

        with open(self.widget.Utils.getDataPath() + '/config/extent.txt', 'w') as e:
            e.write(str(XMIN) + " " + str(YMIN) + " " + str(XMAX) + " " + str(YMAX))

        project_info = self.widget.Utils.getProjectInfo()
        project_info['minx'] = XMIN
        project_info['miny'] = YMIN
        project_info['maxx'] = XMAX
        project_info['maxy'] = YMAX

        with open(self.widget.Utils.getDataPath() + "/pracovni/project.json", 'w') as outfile:
            json.dump(project_info, outfile)

        DATAPATH = self.config["data_path"]
        # TODO make it globally
        epsg = 5514
        with open(self.widget.Utils.getDataPath() + '/config/region.txt') as r:
            region = r.read()

        params = {
            "source_path": DATAPATH + "kraje/" + region + "/",
            "target_path": self.widget.Utils.getDataPath() + '/',
            "minx": XMIN,
            "maxx": XMAX,
            "miny": YMIN,
            "maxy": YMAX,
            "epsg": epsg,
            "type": "extend"
        }

        self.widget.createProgressBar("Extending area: ")
        self.widget.clearTasksList()
        self.widget.appendTask(ClipSourceDataTask(self.widget, params))
        self.widget.runTask(0)
        QgsMessageLog.logMessage("ClipSourceDataTask STARTED", "Patrac")

