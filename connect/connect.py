from qgis.PyQt.QtCore import QThread, pyqtSignal
import urllib.request, urllib.error, urllib.parse
import socket, os
import requests, json

class Response():
    status = 200
    data = ""
    filename = None

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

        self.statusChanged.emit(responseToReturn)


class ConnectPost(QThread):
    statusChanged = pyqtSignal(object)
    url = None
    data = None
    filename = None
    timeout = 5

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
        response = None
        try:
            if self.filename is not None:
                if os.path.isfile(self.filename):
                    with open(self.filename, 'rb') as f: r = requests.post(self.url,
                                                               data=self.data,
                                                               files={'fileToUpload': f})
                else:
                    responseToReturn.status = 500
                    responseToReturn.data = ""
            else:
                requests.post(self.url, data=self.data)
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

        self.statusChanged.emit(responseToReturn)
