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

import csv, io, math, subprocess, os, sys, uuid, filecmp

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

class Styles(object):
    def __init__(self, widget):
        self.widget = widget
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.Utils = self.widget.Utils
        self.Area = self.widget.Area
        self.Sectors = self.widget.Sectors

    def getSectorsLayer(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break
        return layer

    def setSectorsStyle(self, name):
        layer = self.getSectorsLayer()
        if not layer is None:
            settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
            layer.loadNamedStyle(settingsPath + '/styles/sectors_' + name + '.qml')
            f = io.open(settingsPath + '/styles/sektory_group.txt', 'w', encoding='utf-8')
            f.write(name)
            f.close()

    def setSectorsLabels(self, state):
        layer = self.getSectorsLayer()
        layer.setLabelsEnabled(state)
        layer.triggerRepaint()
