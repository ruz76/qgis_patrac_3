    def getLength(self):
        li = self.iface.legendInterface()
        sl = li.selectedLayers(True)
        info = ""
        for lyr in sl:
            line_length = 0
            for feature in lyr.getFeatures():
                sourceCrs = QgsCoordinateReferenceSystem(4326)
                destCrs = QgsCoordinateReferenceSystem(2154)
                tr = QgsCoordinateTransform(sourceCrs, destCrs)
                geom = feature.geometry()
                geom.transform(tr)
                line_length += geom.length()
            str_line_length = str(round(line_length))
            index = len(str_line_length) - 5
            info += lyr.name() + ": " + str_line_length[:index] + " km " + str_line_length[index:][:-2] + " m\n"
        QMessageBox.information(None, "DELKY:", info)

    def pomAddRasters(self):
        KRAJ_DATA_PATH = "/data/patracdata/kraje/vy"
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "100", 2, 80000, 1000000)
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "50", 2, 40000, 80000)
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "25", 2, 20000, 40000)
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "16", 9, 10000, 20000)
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "8", 9, 5000, 10000)
        self.Project.addZPMRasters(KRAJ_DATA_PATH, "3", 81, 1, 5000)
