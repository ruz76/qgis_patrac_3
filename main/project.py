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

import csv, io, math, urllib.request, urllib.error, urllib.parse, socket, subprocess, os, sys, uuid

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

class ZPM_Raster():
    def __init__(self, name, distance, xmin, ymin, xmax, ymax):
        self.name = name
        self.distance = distance
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

class Project(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.serverUrl = self.widget.serverUrl

    def addZPMRasters(self, KRAJ_DATA_PATH, Level, Layers_Count, minscaledenominator, maxscaledenominator):
        XCENTER = self.widget.canvas.extent().center().x()
        YCENTER = self.widget.canvas.extent().center().y()
        if not os.path.isfile(KRAJ_DATA_PATH + "/raster/ZPM_" + Level + "tis/metadata.csv"):
            QgsMessageLog.logMessage("ZPM " + Level + " se nepodařilo načíst", "Patrac")
            return
        with open(KRAJ_DATA_PATH + "/raster/ZPM_" + Level + "tis/metadata.csv", "r") as fileInput:
            rasters = list()
            rasters_count = 0
            for row in csv.reader(fileInput, delimiter=';'):
                distance = math.hypot(XCENTER - float(row[1]), YCENTER - float(row[2]))
                raster = ZPM_Raster(row[0], distance, row[3], row[4], row[5], row[6])
                # print "Not ordered " + raster.name + " " + str(raster.distance)
                if rasters_count > 0:
                    counter = 0
                    inserted = False
                    for x in rasters:
                        if x.distance > distance:
                            rasters.insert(counter, raster)
                            inserted = True
                            break
                        counter = counter + 1
                    if not inserted:
                        rasters.append(raster)
                else:
                    rasters.append(raster)
                rasters_count = rasters_count + 1
            for x in range(0, Layers_Count):
                if x < len(rasters):
                    raster = rasters[x]
                    # print "Ordered " + raster.name + " " + str(raster.distance)
                    self.addRasterLayerToGroup(KRAJ_DATA_PATH + "/raster/ZPM_" + Level + "tis/" + raster.name,
                                               raster.name,
                                               "zbg_" + Level + "tis_orig", minscaledenominator, maxscaledenominator)

    def addRasterLayerToGroup(self, path, label, group, minscaledenominator, maxscaledenominator):
        """Adds raster layer to map"""
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            QgsMessageLog.logMessage("Vrstvu " + path + " se nepodařilo načíst", "Patrac")
        else:
            raster.setCrs(QgsCoordinateReferenceSystem(5514, QgsCoordinateReferenceSystem.EpsgCrsId))
            raster.setScaleBasedVisibility(True)
            raster.setMinimumScale(maxscaledenominator)
            raster.setMaximumScale(minscaledenominator)
            QgsProject.instance().addMapLayer(raster, False)
            root = QgsProject.instance().layerTreeRoot()
            mygroup = root.findGroup(group)
            mygroup.addLayer(raster)
            mygroup.setExpanded(False)

    def addAllZPMRasters(self, KRAJ_DATA_PATH):
        if os.path.isfile(KRAJ_DATA_PATH + "/VERSION"):
            self.addZPMRasters(KRAJ_DATA_PATH, "1024", 1, 1000000, 2000000)
            self.addZPMRasters(KRAJ_DATA_PATH, "512", 1, 500000, 1000000)
            self.addZPMRasters(KRAJ_DATA_PATH, "256", 4, 250000, 500000)
            self.addZPMRasters(KRAJ_DATA_PATH, "128", 2, 125000, 250000)
            self.addZPMRasters(KRAJ_DATA_PATH, "64", 4, 60000, 125000)
            self.addZPMRasters(KRAJ_DATA_PATH, "32", 6, 20000, 60000)
            self.addZPMRasters(KRAJ_DATA_PATH, "16", 9, 10000, 20000)
            self.addZPMRasters(KRAJ_DATA_PATH, "8", 9, 5000, 10000)
            self.addZPMRasters(KRAJ_DATA_PATH, "4", 72, 1, 5000)
        else:
            self.addZPMRasters(KRAJ_DATA_PATH, "100", 4, 80000, 1000000)
            self.addZPMRasters(KRAJ_DATA_PATH, "50", 4, 40000, 80000)
            self.addZPMRasters(KRAJ_DATA_PATH, "25", 6, 20000, 40000)
            self.addZPMRasters(KRAJ_DATA_PATH, "16", 9, 10000, 20000)
            self.addZPMRasters(KRAJ_DATA_PATH, "8", 9, 5000, 10000)
            self.addZPMRasters(KRAJ_DATA_PATH, "3", 72, 1, 5000)

        self.widget.iface.messageBar().clearWidgets()

    def copyTemplate(self, NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE):
        if not os.path.isdir(NEW_PROJECT_PATH):
            os.mkdir(NEW_PROJECT_PATH)

            # sets the settings to zero, so no radial and no weight limit is used
            os.mkdir(NEW_PROJECT_PATH + "/config")
            f = open(NEW_PROJECT_PATH + '/config/weightlimit.txt', 'w')
            f.write("0")
            f.close()
            f = open(NEW_PROJECT_PATH + '/config/radialsettings.txt', 'w')
            f.write("0")
            f.close()

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
            # copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.prj",
            #     NEW_PROJECT_PATH + "/pracovni/sektory_group.prj")
            # copy(NEW_PROJECT_PATH + "/pracovni/sektory_group_selected.qpj",
            #     NEW_PROJECT_PATH + "/pracovni/sektory_group.qpj")
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
            os.mkdir(NEW_PROJECT_PATH + "/sektory/styles")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/shp/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/shp/")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/styles/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/styles/")
            # copy(TEMPLATES_PATH + "/projekt/sektory/shp/style.qml", NEW_PROJECT_PATH + "/sektory/shp/")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/jtsk")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/jtsk/PERMANENT")
            # print TEMPLATES_PATH + '/grassdata/jtsk/PERMANENT'
            for file in glob(TEMPLATES_PATH + '/grassdata/jtsk/PERMANENT/*'):
                # print file
                copy(file, NEW_PROJECT_PATH + "/grassdata/jtsk/PERMANENT/")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/wgs84")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/wgs84/PERMANENT")
            for file in glob(TEMPLATES_PATH + '/grassdata/wgs84/PERMANENT/*'):
                copy(file, NEW_PROJECT_PATH + "/grassdata/wgs84/PERMANENT/")

    def getSafeDirectoryName(self, name):
        name = name.lower()
        replace = ['a', 'c', 'd', 'e', 'e', 'i', 'n', 'o', 'r', 's', 't', 'u', 'u', 'y', 'z', '_', '_', '_', '_', '_']
        position = 0
        for ch in ['á', 'č', 'ď', 'ě', 'é', 'í', 'ň', 'ó', 'ř', 'š', 'ť', 'ú', 'ů', 'ý', 'ž', ' ', '(', ')', '.', ':']:
            if ch in name:
                name = name.replace(ch, replace[position])
            position = position + 1
        return name

    def openProjectSimple(self):
        # Tries to open simple project for generating search project
        simpleProjectPath = ''

        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'C:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'D:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'E:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = '/data/patracdata/cr/projekty/simple/simple.qgs'

        if simpleProjectPath == '':
            QMessageBox.information(None, "CHYBA:",
                                    "Nepodařilo se načíst výchozí projekt. Zkuste jej prosím načíst ručně.")
            return False
        else:
            project = QgsProject.instance()
            project.read(QFileInfo(simpleProjectPath))
            #QMessageBox.information(None, "INFO:",
            #                        u"Podařilo se načíst výchozí projekt. Vyhledejte znovu obec a vygenerujte projekt pro hledání.")

            return True

    def getRegion(self):
        layer = None
        for lyr in list(QgsMapLayerRegistry.instance().mapLayers().values()):
            if "okresy_pseudo.shp" in lyr.source():
                layer = lyr
                break

        for feature in layer.getFeatures():
            if (feature.geometry().contains(self.canvas.extent().center())):
                return feature["nk"]

        return None

    def getSimpleProjectDataPath(self):
        DATAPATH = ''
        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'C:/patracdata/cr/projekty/simple/'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'D:/patracdata/cr/projekty/simple/'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'E:/patracdata/cr/projekty/simple/'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/cr/projekty/simple/'

        return DATAPATH

    def checkRegion(self, region):
        if region is not None:
            region = region.lower()
        else:
            QMessageBox.information(None, "CHYBA:",
                                    "Extent mapy je mimo ČR. Nemám data nemohu pokračovat.")
            return None

        DATAPATH = self.getSimpleProjectDataPath()

        if DATAPATH == '':
            QMessageBox.information(None, "KRITICKÁ CHYBA:",
                                    "Nepodařilo se najít adresář s daty. Nemohu pokračovat.")
            return None

        regionOut = None
        QgsMessageLog.logMessage("Region: " + region, "Patrac")
        if os.path.isfile(DATAPATH + '/../../../kraje/' + region + '/vektor/OSM/line_x/merged_polygons_groupped.shp'):
            regionOut = region
        if os.path.isfile(
                DATAPATH + '/../../../kraje/' + region + '/vektor/ZABAGED/line_x/merged_polygons_groupped.shp'):
            regionOut = region

        return regionOut

    def checkRegionExtent(self):
        if (self.canvas.extent().width() > 10000) or (self.canvas.extent().height() > 10000):
            reply = QMessageBox.question(self, 'Region',
                                         'Region je příliš rozsáhlý. Výpočty budou pomalé. Chcete pokračovat?',
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return True
            else:
                return False
        else:
            return True

    def createProject(self, index, desc):
        # Check if the project has okresy_pseudo.shp

        QgsMessageLog.logMessage("CREATING PROJECT", "Patrac")
        #project = QgsProject.instance()
        #project.clear()
        #QgsMapLayerRegistry.instance().mapLayers().clear()

        #if not self.openProjectSimple():
        #    return

        # if not self.checkLayer("okresy_pseudo.shp"):
            #QMessageBox.information(None, "CHYBA:",
            #                        u"Projekt neobsahuje vrstvu okresy. Pokusím se otevřít výchozí projekt.")
            # QgsMessageLog.logMessage("checkLayer(okresy_pseudo.shp)", "Patrac")
            # if not self.openProjectSimple():
            #    return

        # QgsMessageLog.logMessage("openProjectSimple OK", "Patrac")

        name = self.widget.municipalities_names[index]
        region = self.widget.municipalities_regions[index]

        #region = self.getRegion()
        region = self.checkRegion(region)

        if region is None:
            QMessageBox.information(None, "CHYBA:",
                                    "Pro daný kraj nemám k dispozici data. Nemám data nemohu pokračovat.")
            return

        # if not self.checkRegionExtent():
        #     QMessageBox.information(None, "INFO:",
        #                             u"Ukončuji generování.")
        #     return

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
        QgsMessageLog.logMessage("Název: " + NAMESAFE, "Patrac")

        DATAPATH = self.getSimpleProjectDataPath()

        NEW_PROJECT_PATH = DATAPATH + "/../../../kraje/" + region + "/projekty/" + NAMESAFE
        # set working dir to new path
        QSettings().setValue("UI/lastProjectDir", DATAPATH + "/../../../kraje/" + region + "/projekty/" + NAMESAFE)

        TEMPLATES_PATH = DATAPATH + "/../../../kraje/templates"
        KRAJ_DATA_PATH = DATAPATH + "/../../../kraje/" + region
        self.copyTemplate(NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE)

        if sys.platform.startswith('win'):
            p = subprocess.Popen((
                                 self.pluginPath + "/grass/run_export.bat", KRAJ_DATA_PATH, self.pluginPath, XMIN, YMIN,
                                 XMAX, YMAX, NEW_PROJECT_PATH))
            p.wait()
            p = subprocess.Popen((self.pluginPath + "/grass/run_import.bat", NEW_PROJECT_PATH, self.pluginPath, XMIN,
                                  YMIN, XMAX, YMAX, KRAJ_DATA_PATH))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_export.sh", KRAJ_DATA_PATH, self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, NEW_PROJECT_PATH))
            p.wait()
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_import.sh", NEW_PROJECT_PATH, self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, KRAJ_DATA_PATH))
            p.wait()

        # self.copyQGSTemplate(NEW_PROJECT_PATH, TEMPLATES_PATH, KRAJ_DATA_PATH)
        QMessageBox.information(None, "INFO:",
                                "Projekt vytvořen. Pokusím se o jeho načtení, buďte prosím trpěliví. V případě chyby vytvoření zopakujte.");
        project = QgsProject.instance()
        QgsMessageLog.logMessage(NEW_PROJECT_PATH + '/' + NAMESAFE + '.qgs', "Patrac")
        project.read(NEW_PROJECT_PATH + '/' + NAMESAFE + '.qgs')
        # self.do_msearch()
        self.zoomToExtent(XMIN, YMIN, XMAX, YMAX)
        # self.addAllZPMRasters(KRAJ_DATA_PATH)
        self.widget.Sectors.recalculateSectors(True)
        self.createNewSearch(name, desc, region)
        self.widget.settingsdlg.updateSettings()
        self.saveRegion(region, NEW_PROJECT_PATH)
        self.saveExtent(XMIN, YMIN, XMAX, YMAX, NEW_PROJECT_PATH)
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

    def createNewSearch(self, name, desc, region):
        QgsMessageLog.logMessage("Vytvářím nové pátrání: " + name + " " + region, "Patrac")
        searchid = self.createSearchId(name)
        self.createSearchOnServer(searchid, name, desc, region)

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

    def createSearchOnServer(self, searchid, name, desc, region):
        response = None
        # Connects to the server to obtain list of users based on list of locations
        try:
            escaped_name = quote(name.encode('utf-8'))
            escaped_desc = quote(desc.encode('utf-8'))
            url = self.serverUrl + 'search.php?operation=createnewsearch&id=pcr007&searchid='\
                  + searchid + '&name=' + escaped_name + '&desc=' + escaped_desc + '&region=' + region
            response = urllib.request.urlopen(url, None, 5)
            searchStatus = response.read()
        except urllib.error.URLError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
        except socket.timeout:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
        # TODO - if we can not connect to server, we should connect later
        # self.getMessage()
