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
# ******************************************************************************

import os
from qgis.PyQt import QtWidgets, QtGui, uic
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

from .chppatrac import *
import uuid
from shutil import copy

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'chcalculate.ui'))


class Ui_Chcalculate(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for settings"""

    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Chcalculate, self).__init__(parent)
        self.parent = parent
        self.widget = parent
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.settingsPath = pluginPath + "/../../../patrac_settings"

    def accept(self):
        self.plainTextEditResults.clear()
        self.plainTextEditResults.appendPlainText('Computing ...')
        chinesePostmanId = str(uuid.uuid4())
        working_dir = os.path.join('/tmp/', chinesePostmanId)
        os.mkdir(working_dir)
        # copy('/home/jencek/Documents/Projekty/PCR/test_data/test.gpkg', os.path.join(working_dir, 'test.gpkg'))
        copy('/home/jencek/Documents/Projekty/PCR/test_data_eustach/test.gpkg', os.path.join(working_dir, 'test.gpkg'))

        sectors_layer = self.widget.getSectorsLayer()
        selected_sectors = sectors_layer.selectedFeatures()
        ids = []
        for sector in selected_sectors:
            ids.append(sector['id'])
        # print(ids)

        config = {
            "log_level": "debug",
            "gpkg_path": os.path.join(working_dir, 'test.gpkg'),
            "output_dir": working_dir,
            "covers": {
                "handler": 12,
                "pedestrian": 12,
                "rider": 16,
                "quad_bike": 20
            },
            "searchers": {
                "handler": self.spinBoxHandlersCount.value(),
                "pedestrian": self.spinBoxPedestriansCount.value(),
                "rider": self.spinBoxRidersCount.value(),
                "quad_bike": self.spinBoxQuadBikesCount.value()
            },
            "sectors": ids
        }
        solutions = solve_area(config)
        for solution in solutions:
            self.widget.Utils.addVectorLayerWithStyle(os.path.join(config['output_dir'], solution['id'] + ".shp"), solution['id'], "chinese_lines_notime", 'EPSG:4326')
            # self.widget.Utils.addVectorLayerWithStyle(os.path.join(config['output_dir'], solution['id'] + ".shp"), solution['id'], "chinese_lines", 'EPSG:4326')
            print(solution)
            self.plainTextEditResults.appendPlainText(str(solution))

