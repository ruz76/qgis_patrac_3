from qgis.PyQt.QtCore import QThread, pyqtSignal
import urllib.request, urllib.error, urllib.parse
import socket, os
import requests, json
import sqlite3
from sqlite3 import Error
import ast
from qgis.core import *
from qgis.gui import *

class Response():
    status = 200
    data = ""
    filename = None

class Database():
    path = ""
    def __init__(self, path):
        self.path = path

    def insertRequest(self, url, data, filename):
        conn = None
        try:
            conn = sqlite3.connect(self.path)
            c = conn.cursor()
            request = (url, data, filename)
            # print(request)
            c.execute('INSERT INTO requests(url, data, filename) VALUES(?,?,?)', request)
            # print(insert_reponse)
            conn.commit()
            conn.close()

        except Error as e:
            print("INSERT: ", e)

class SaveProject(QThread):
    def __init__(self):
        super(SaveProject, self).__init__()

    def run(self):
        while True:
            try:
                project = QgsProject.instance()
                if project is not None:
                    prjfi = QFileInfo(project.fileName())
                    DATAPATH = prjfi.absolutePath()
                    if DATAPATH != "" and QFileInfo(DATAPATH + "/config/region.txt").exists():
                        project.write()
            except:
                a = 100 # Only placeholder, TODO
            self.sleep(300)

class CheckRequests(QThread):
    path = ""
    def __init__(self, path):
        self.path = path
        super(CheckRequests, self).__init__()

    def run(self):
        while True:
            # print("CheckRequests")
            conn = None
            try:
                # print(self.path)
                conn = sqlite3.connect(self.path)
                c = conn.cursor()
                c.execute("SELECT id, url, data, filename FROM requests LIMIT 1")
                row = c.fetchone()
                if row is not None:
                    if row[3] is None:
                        # print("NO FILE")
                        self.rowid = row[0]
                        self.simpleGet = Connect()
                        self.simpleGet.setUrl(row[1])
                        self.simpleGet.statusChanged.connect(self.onResponse)
                        self.simpleGet.start()
                    else:
                        # print("FILE", row[2])
                        self.rowid = row[0]
                        self.postFile = ConnectPost()
                        self.postFile.setUrl(row[1])
                        self.postFile.setFilename(row[3])
                        self.postFile.setData(ast.literal_eval(row[2]))
                        self.postFile.statusChanged.connect(self.onResponsePostFile)
                        self.postFile.start()
                conn.close()

            except Error as e:
                # print("SELECT: ", e)
                a = 100 # Only placeholder, TODO

            self.sleep(60)

    def deleteRow(self):
        try:
            conn = sqlite3.connect(self.path)
            c = conn.cursor()
            sql = "DELETE FROM requests WHERE id = " + str(self.rowid)
            print(sql)
            c.execute(sql)
            conn.commit()
            conn.close()

        except Error as e:
            a = 100 # Only placeholder, TODO
            # print("DELETE: ", e)

    def onResponse(self, response):
        if response.status != 200:
            return
        else:
            self.deleteRow()

    def onResponsePostFile(self, response):
        # print("AA", response.status, response.data)
        if response.status != 200:
            return
        elif response.data is not None:
            if response.data.startswith('E'):
                return
        else:
            self.deleteRow()

class Connect(QThread):
    statusChanged = pyqtSignal(object)
    url = None
    timeout = 5

    def setUrl(self, url):
        self.url = url

    def setTimeout(self, timeout):
        self.timeout = timeout

    def run(self):
        responseToReturn = Response()
        response = None
        try:
            response = urllib.request.urlopen(self.url, None, self.timeout)
            # response = response.read().decode('utf-8') # str(response.read())
            responseToReturn.data = response
            # print(dir(response.status))
            responseToReturn.status = response.status
        except urllib.error.URLError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except urllib.error.HTTPError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except socket.timeout:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except Exception as e:
            responseToReturn.status = 500
            responseToReturn.data = ""

        self.statusChanged.emit(responseToReturn)


class ConnectPost(QThread):
    statusChanged = pyqtSignal(object)
    url = None
    data = None
    filename = None
    timeout = 5
    type = "data"

    def setType(self, type):
        self.type = type

    def setUrl(self, url):
        self.url = url

    def setData(self, data):
        self.data = data

    def setFilename(self, filename):
        self.filename = filename

    def setTimeout(self, timeout):
        self.timeout = timeout

    def run(self):
        responseToReturn = Response()
        # print("SHIT", self.filename)
        try:
            if self.filename is not None:
                if os.path.isfile(self.filename):
                    with open(self.filename, 'rb') as f:
                        if self.type == "data":
                            r = requests.post(self.url, data=self.data, files={'fileToUpload': f})
                        if self.type == "json":
                            r = requests.post(self.url, json=self.data, files={'fileToUpload': f})
                        responseToReturn.status = r.status_code
                        responseToReturn.data = r.text
                else:
                    responseToReturn.status = 500
                    responseToReturn.data = ""
            else:
                if self.type == "data":
                    requests.post(self.url, data=self.data)
                if self.type == "json":
                    requests.post(self.url, json=self.data)
            responseToReturn.status = 200
        except urllib.error.URLError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except urllib.error.HTTPError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except socket.timeout:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except Exception as e:
            responseToReturn.status = 500
            responseToReturn.data = ""
            # print("RTR EEE", str(e))

        # print("RTR", responseToReturn)
        self.statusChanged.emit(responseToReturn)


class ConnectFile(QThread):
    statusChanged = pyqtSignal(object)
    url = None
    filename = None
    timeout = 5

    def setUrl(self, url):
        self.url = url

    def setFilename(self, filename):
        self.filename = filename

    def setTimeout(self, timeout):
        self.timeout = timeout

    def run(self):
        responseToReturn = Response()
        response = None
        try:
            response = requests.get(self.url)
            responseToReturn.data = response
            responseToReturn.filename = self.filename
            responseToReturn.status = response.status_code
        except urllib.error.URLError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except urllib.error.HTTPError:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except socket.timeout:
            responseToReturn.status = 500
            responseToReturn.data = ""
        except Exception as e:
            responseToReturn.status = 500
            responseToReturn.data = ""

        self.statusChanged.emit(responseToReturn)
