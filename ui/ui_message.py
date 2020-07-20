# -*- coding: utf-8 -*-

# ******************************************************************************
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
# ******************************************************************************

import os
import shutil
import csv

from qgis.PyQt import QtWidgets, QtGui, uic
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.gui import *
import urllib.request, urllib.error, urllib.parse
import socket
import requests, json
import io
import datetime
import webbrowser

from ..connect.connect import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'message.ui'))


class Ui_Message(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for sending the messages
    """

    def __init__(self, pluginPath, DATAPATH, parent=None):
        """Constructor."""
        super(Ui_Message, self).__init__(parent)
        self.main = parent
        self.iface = self.main.iface
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.DATAPATH = DATAPATH
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.browseButton.clicked.connect(self.showBrowse)
        self.btnCheckAll.clicked.connect(self.checkAll)
        self.btnCheckNone.clicked.connect(self.checkNone)
        self.btnRefresh.clicked.connect(self.fillSearchersList)
        self.pushButtonGpx.clicked.connect(self.addGpx)
        self.fillSearchersList()
        self.listWidgetHistory.setWordWrap(True)
        self.fillMessagesList()
        self.listWidgetHistory.scrollToBottom()
        self.listWidgetMessages.itemDoubleClicked.connect(self.messagesDoubleClick)

    def addGpx(self):
        self.lineEditPath.setText(self.DATAPATH + "/sektory/gpx/all.gpx")

    def messagesDoubleClick(self, item):
        # print item.text()
        items = item.text().split("@")
        if (len(items) == 2):
            attachment = str(items[1]).strip()
            if len(attachment) > 2:
                if "/" in attachment or "\\" in attachment:
                    webbrowser.open("file://" + attachment)
                else:
                    webbrowser.open("file://" + self.DATAPATH + "/pracovni/" + attachment)

    def fillMessagesList(self):
        # read file with messages and
        if os.path.exists(self.DATAPATH + "/pracovni/zpravy.txt"):
            # print self.DATAPATH + "/pracovni/zpravy.txt"
            with io.open(self.DATAPATH + "/pracovni/zpravy.txt", encoding='utf-8') as f:
                item = ""
                for line in f:
                    if item != "" and line.startswith("---"):
                        self.listWidgetHistory.addItem(item)
                        item = ""
                    else:
                        item += line

    def fillSearchersList(self):
        self.filllist = Connect()
        self.filllist.setUrl(self.serverUrl + 'loc.php?searchid=' + self.getSearchID())
        self.filllist.statusChanged.connect(self.onFillSearchersList)
        self.filllist.start()

    def onFillSearchersList(self, response):
        if response.status == 200:
            self.listViewModel = QStandardItemModel()
            locations = str(response.data.read().decode("utf-8"))
            lines = locations.split("\n")
            lineid = 0
            # Loops via locations
            for line in lines:
                if line != "" and lineid > 0:
                    cols = line.split(";")
                    if cols != None:
                        # Adds name of the user and session id to the list
                        # self.comboBoxUsers.addItem(str(cols[3]).decode('utf8') + ' (' + str(cols[0]) + ')')
                        item = QStandardItem(str(cols[3]) + ' (' + str(cols[0]) + ')')
                        # item = QStandardItem(str(cols[3]).decode('utf8'))
                        item.setCheckable(True)
                        self.listViewModel.appendRow(item)
                lineid += 1
            self.listViewSearchers.setModel(self.listViewModel)
            self.getMessage()
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def getSearchID(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        searchid = open(DATAPATH + "/config/searchid.txt", 'r').read()
        return searchid.strip()

    def showBrowse(self):
        """Opens file dialog for browsing"""
        filename = QFileDialog.getOpenFileName()
        self.lineEditPath.setText(filename)

    def checkAll(self):
        i = 0
        while self.listViewModel.item(i):
            # print i
            self.listViewModel.item(i).setCheckState(Qt.Checked)
            i += 1

    def checkNone(self):
        i = 0
        while self.listViewModel.item(i):
            self.listViewModel.item(i).setCheckState(Qt.Unchecked)
            i += 1

    def getSearchersIDS(self):
        i = 0
        added = 0
        ids = ""
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                id = self.listViewModel.item(i).text().split("(")[1][:-1]
                if added > 0:
                    ids = ids + ";" + id
                else:
                    ids = id
                added += 1
            i += 1
        return ids

    def getSearchersNames(self):
        i = 0
        added = 0
        names = ""
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                name = self.listViewModel.item(i).text().split("(")[0][:-1]
                if added > 0:
                    names = names + ";" + name
                else:
                    names = name
                added += 1
            i += 1
        return names

    def accept(self):
        """Sends the message"""
        # Gets the filename
        filename1 = self.lineEditPath.text()
        # Gets the sessionid from combobox
        # id = str(self.comboBoxUsers.currentText()).split("(")[1][:-1]
        ids = self.getSearchersIDS()
        QgsMessageLog.logMessage("Recipients: " + ids, "Patrac")
        if ids == "":
            QMessageBox.information(None, self.tr("ERROR"), self.tr("No recipient."))
            return

        # Gets the message as plain text
        message = self.plainTextEditMessage.toPlainText()
        searchid = self.getSearchID()
        now = datetime.datetime.now().strftime("%d.%m. %H:%M")

        self.sendmessage = ConnectPost()
        self.sendmessage.setUrl(self.serverUrl + "message.php")
        self.sendmessage.statusChanged.connect(self.onSendMessageResponse)

        if filename1:
            if os.path.isfile(filename1):
                # If the file exists
                self.listWidgetHistory.addItem(now + "\n" + self.getSearchersNames() + "\n" + message + "\n@ " + filename1)
                # Stores message sinto file for archiving
                with io.open(self.DATAPATH + "/pracovni/zpravy.txt", encoding='utf-8', mode="a") as messages:
                    messages.write(now + "\n" + self.getSearchersNames() + "\n" + message + "\n@ " + filename1 + "\n--------------------\n")
                self.sendmessage.setFilename(filename1)
                self.sendmessage.setData({'message': message, 'ids': ids,
                 'operation': 'insertmessages',
                 'searchid': searchid,
                 'from_id': 'coordinator' + searchid})
        else:
            # If file is not specified then send without file
            self.listWidgetHistory.addItem(now + "\n" + self.getSearchersNames() + "\n" + message)
            # Stores message sinto file for archiving
            with io.open(self.DATAPATH + "/pracovni/zpravy.txt", encoding='utf-8', mode="a") as messages:
                messages.write(now + "\n" + self.getSearchersNames() + "\n" + message + "\n--------------------\n")

            self.sendmessage.setData({'message': message, 'ids': ids, 'operation': 'insertmessages',
                                    'searchid': searchid, 'from_id': 'coordinator' + searchid})

        self.listWidgetHistory.item(0).setForeground(QColor(255, 0, 0, 255))
        self.listWidgetHistory.scrollToBottom()
        self.sendmessage.start()

    def onSendMessageResponse(self, response):
        if response.status != 200:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def markMessageAsReaded(self, sysid):
        self.markmessage = Connect()
        self.markmessage.setUrl(self.serverUrl + 'message.php?operation=markmessage&searchid='
                                + self.getSearchID() + '&id=coordinator' + self.getSearchID()
                                + '&sysid=' + sysid)
        self.markmessage.statusChanged.connect(self.onMarkMessageAsReadedResponse)
        self.markmessage.start()

    def onMarkMessageAsReadedResponse(self, response):
        if response.status == 200:
            message = response.data.read()
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)

    def getMessage(self):
        self.getmessage = Connect()
        self.getmessage.setUrl(self.serverUrl + 'message.php?operation=getmessages&lastereceivedmessageid=0&searchid=' + self.getSearchID() + '&sessionid=coordinator' + self.getSearchID())
        self.getmessage.statusChanged.connect(self.onGetMessageResponse)
        self.getmessage.start()

    def onGetMessageResponse(self, response):
        if response.status == 200:
            message = response.data.read()
            self.listWidgetMessages.clear()
            data = json.loads(message.decode('utf8'))
            for message in data["messages"]:
                if message["file"] != "":
                    self.getAttachment(message["file"], message["shared"])
                messageForView = message["dt_created"] + ": " + message["fromid"] + "\n" + message["message"]
                if message["file"] != "":
                    messageForView += " @ " + message["file"]
                self.listWidgetMessages.addItem("\n" + messageForView)
                self.listWidgetMessages.scrollToBottom()
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)


    def getAttachment(self, filename, shared):
        response = None
        fileplacement = None
        if shared == "1":
            fileplacement = "shared"
        else:
            fileplacement = 'coordinator' + self.getSearchID()

        self.getfile = ConnectFile()
        self.getfile.setUrl(self.serverUrl + 'message.php?operation=getfile&searchid=' + self.getSearchID() + '&id=' + fileplacement + '&filename=' + filename)
        self.getfile.setFilename(filename)
        self.getfile.statusChanged.connect(self.onGetFileResponse)
        self.getfile.start()


    def onGetFileResponse(self, response):
        if response.status == 200:
            with io.open(self.DATAPATH + "/pracovni/" + response.filename, "wb") as code:
                code.write(response.content)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Can not connect to the server."), level=Qgis.Warning)
