# -*- coding: utf-8 -*-

#******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora hledání pohřešované osoby
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
#******************************************************************************

import os
import shutil
import csv
import io
from qgis.PyQt import QtWidgets,QtCore, QtGui, uic
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *
import urllib.request, urllib.error, urllib.parse
import socket

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'result.ui'))

class Ui_Result(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(Ui_Result, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.pushButtonNotFound.clicked.connect(self.acceptNotFound)

        self.DATAPATH = ''
        self.searchid = ''

        self.point = None

        date = QDate.currentDate();
        self.dateTimeEditMissing.setDate(date)

        self.comboBoxSex.addItem(_fromUtf8("Muž"))
        self.comboBoxSex.addItem(_fromUtf8("Žena"))

        self.comboBoxTerrain.addItem(_fromUtf8("Ano"))
        self.comboBoxTerrain.addItem(_fromUtf8("Ne"))
        self.comboBoxTerrain.addItem(_fromUtf8("Částečně"))

        self.comboBoxPurpose.addItem(_fromUtf8("Alzheimerova choroba"))
        self.comboBoxPurpose.addItem(_fromUtf8("Demence"))
        self.comboBoxPurpose.addItem(_fromUtf8("Deprese"))
        self.comboBoxPurpose.addItem(_fromUtf8("Retardovaný"))
        self.comboBoxPurpose.addItem(_fromUtf8("Psychická nemoc"))
        self.comboBoxPurpose.addItem(_fromUtf8("Sebevrah"))
        self.comboBoxPurpose.addItem(_fromUtf8("Dopravní nehoda(úraz, šok)"))
        self.comboBoxPurpose.addItem(_fromUtf8("Ǔtěk z domova"))
        self.comboBoxPurpose.addItem(_fromUtf8("Ztráta orientace"))
        self.comboBoxPurpose.addItem(_fromUtf8("Jiné (uveďte v pozn.)"))

        self.comboBoxCondition.addItem(_fromUtf8("Velmi dobrá"))
        self.comboBoxCondition.addItem(_fromUtf8("Dobrá"))
        self.comboBoxCondition.addItem(_fromUtf8("Špatná"))
        self.comboBoxCondition.addItem(_fromUtf8("Velmi špatná"))

        self.comboBoxHealth.addItem(_fromUtf8("Bez zdravotních obtíží"))
        self.comboBoxHealth.addItem(_fromUtf8("Diabetes"))
        self.comboBoxHealth.addItem(_fromUtf8("Epilepsie"))
        self.comboBoxHealth.addItem(_fromUtf8("Pohybově postižený"))
        self.comboBoxHealth.addItem(_fromUtf8("Vysoký krevní tlak"))
        self.comboBoxHealth.addItem(_fromUtf8("Jiné (uveďte v pozn.)"))

        self.comboBoxPlace.addItem(_fromUtf8("Vinice / chmelnice"))
        self.comboBoxPlace.addItem(_fromUtf8("Ovocný sad / zahrada"))
        self.comboBoxPlace.addItem(_fromUtf8("Louka"))
        self.comboBoxPlace.addItem(_fromUtf8("Pole s plodinami"))
        self.comboBoxPlace.addItem(_fromUtf8("Pole sklizené"))
        self.comboBoxPlace.addItem(_fromUtf8("Vodní plocha"))
        self.comboBoxPlace.addItem(_fromUtf8("Vodní tok"))
        self.comboBoxPlace.addItem(_fromUtf8("V obci / městě"))
        self.comboBoxPlace.addItem(_fromUtf8("Jiné (uveďte v pozn.)"))

        self.comboBoxPlace2.addItem(_fromUtf8("U stavebního objektu"))
        self.comboBoxPlace2.addItem(_fromUtf8("Uvnitř stavebního objektu"))
        self.comboBoxPlace2.addItem(_fromUtf8("U cesty (do cca 20 m)"))
        self.comboBoxPlace2.addItem(_fromUtf8("Na rozhraní terénů"))
        self.comboBoxPlace2.addItem(_fromUtf8("Houština"))
        self.comboBoxPlace2.addItem(_fromUtf8("Lom"))
        self.comboBoxPlace2.addItem(_fromUtf8("Skalní útvary"))
        self.comboBoxPlace2.addItem(_fromUtf8("Na cestě"))
        self.comboBoxPlace2.addItem(_fromUtf8("Jiné (uveďte v pozn.)"))

        self.comboBoxHealth2.addItem(_fromUtf8("Bez zdravotních obtíží"))
        self.comboBoxHealth2.addItem(_fromUtf8("Bezvědomí"))
        self.comboBoxHealth2.addItem(_fromUtf8("Krvácení"))
        self.comboBoxHealth2.addItem(_fromUtf8("Mrtvý"))
        self.comboBoxHealth2.addItem(_fromUtf8("Otrava"))
        self.comboBoxHealth2.addItem(_fromUtf8("Otřes mozku"))
        self.comboBoxHealth2.addItem(_fromUtf8("Podchlazení"))
        self.comboBoxHealth2.addItem(_fromUtf8("Fyzické vyčerpání"))
        self.comboBoxHealth2.addItem(_fromUtf8("Zlomeniny"))
        self.comboBoxHealth2.addItem(_fromUtf8("Jiné (uveďte v pozn.)"))

    def setPoint(self, point):
        self.point = point
        self.lineEditCoords.setText(str(round(self.point.x())) + ' ' + str(round(self.point.y())))

    def accept(self):
        self.saveXML()
        self.saveHTML()
        self.closeSearch()
        self.close()

    def acceptNotFound(self):
        self.closeSearch()
        self.close()

    def saveHTML(self):
        html = io.open(self.DATAPATH + "/search/result.html", encoding='utf-8', mode="w")
        html.write('<!DOCTYPE html>\n')
        html.write('<html><head><meta charset = "UTF-8">\n')
        html.write('<title>Report z výsledku pátrání</title>\n')
        html.write('</head>\n')
        html.write('<body>\n')
        html.write("<h1>Výsledek</h1>\n")
        html.write("<p>Souřadnice (S-JTSK): " + self.lineEditCoords.text() + "</p>\n")
        html.write("<p>Pohřešování od: " + self.dateTimeEditMissing.text() + "</p>\n")
        html.write("<p>Oznámení od pohřešování: " + self.spinBoxHourFromMissing.text() + " h</p>\n")
        html.write("<p>Pohlaví: " + self.comboBoxSex.currentText() + "</p>\n")
        html.write("<p>Věk: " + self.spinBoxAge.text() + "</p>\n")
        html.write("<p>Znalost terénu: " + self.comboBoxTerrain.currentText() + "</p>\n")
        html.write("<p>Důvod: " + self.comboBoxPurpose.currentText() + "</p>\n")
        html.write("<p>Kondice: " + self.comboBoxCondition.currentText() + "</p>\n")
        html.write("<p>Zdravotní stav: " + self.comboBoxHealth.currentText() + "</p>\n")
        html.write("<p>Hodin od oznámení: " + self.spinBoxHourFromAnnounce.text() + "</p>\n")
        html.write("<p>Místo: " + self.comboBoxPlace.currentText() + "</p>\n")
        html.write("<p>Upřesnění místa: " + self.comboBoxPlace2.currentText() + "</p>\n")
        html.write("<p>Aktuální zdravotní stav: " + self.comboBoxHealth2.currentText() + "</p>\n")
        html.write("<p>Poznámka: " + self.plainTextEditNote.toPlainText() + "</p>\n")
        html.write("</body>\n")
        html.write("</html>\n")
        html.close()

    def saveXML(self):
        xml = io.open(self.DATAPATH + "/search/result.xml", encoding='utf-8', mode='w')
        xml.write('<?xml version="1.0"?>\n')
        xml.write("<result>\n")
        xml.write("<coords>" + self.lineEditCoords.text() + "</coords>\n")
        xml.write("<datetimemissing>" + self.dateTimeEditMissing.text() + "</datetimemissing>\n")
        xml.write("<hourfrommissing>" + self.spinBoxHourFromMissing.text() + "</hourfrommissing>\n")
        xml.write("<sex>" + str(self.comboBoxSex.currentIndex()) + "</sex>\n")
        xml.write("<!--" + self.comboBoxSex.currentText() + "-->\n")
        xml.write("<age>" + self.spinBoxAge.text() + "</age>\n")
        xml.write("<terrain>" + str(self.comboBoxTerrain.currentIndex()) + "</terrain>\n")
        xml.write("<!--" + self.comboBoxTerrain.currentText() + "-->\n")
        xml.write("<purpose>" + str(self.comboBoxPurpose.currentIndex()) + "</purpose>\n")
        xml.write("<!--" + self.comboBoxPurpose.currentText() + "-->\n")
        xml.write("<condition>" + str(self.comboBoxCondition.currentIndex()) + "</condition>\n")
        xml.write("<!--" + self.comboBoxCondition.currentText() + "-->\n")
        xml.write("<health>" + str(self.comboBoxHealth.currentIndex()) + "</health>\n")
        xml.write("<!--" + self.comboBoxHealth.currentText() + "-->\n")
        xml.write("<hourfromannonce>" + self.spinBoxHourFromAnnounce.text() + "</hourfromannonce>\n")
        xml.write("<place>" + str(self.comboBoxPlace.currentIndex()) + "</place>\n")
        xml.write("<!--" + self.comboBoxPlace.currentText() + "-->\n")
        xml.write("<place2>" + str(self.comboBoxPlace2.currentIndex()) + "</place2>\n")
        xml.write("<!--" + self.comboBoxPlace2.currentText() + "-->\n")
        xml.write("<health2>" + str(self.comboBoxHealth2.currentIndex()) + "</health2>\n")
        xml.write("<!--" + self.comboBoxHealth2.currentText() + "-->\n")
        xml.write("<note>" + self.plainTextEditNote.toPlainText() + "</note>\n")
        xml.write("</result>\n")
        xml.close()

    def setDataPath(self, DATAPATH):
        self.DATAPATH = DATAPATH

    def setSearchid(self, searchid):
        self.searchid = searchid

    def closeSearch(self):
        response = None
        # Connects to the server to close the search
        try:
            url = 'http://gisak.vsb.cz/patrac/search.php?operation=closesearch&id=pcr007&searchid=' + self.searchid
            # print url
            response = urllib.request.urlopen(url, None, 5)
            searchStatus = response.read()
        except urllib.error.URLError:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")
        except socket.timeout:
            QMessageBox.information(None, "INFO:", "Nepodařilo se spojit se serverem.")