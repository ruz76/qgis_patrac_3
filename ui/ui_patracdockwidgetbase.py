# -*- coding: utf-8 -*-

from qgis.PyQt import QtWidgets,QtCore, QtGui
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
import os.path
import csv

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PatracDockWidget(object):
    def setupUi(self, PatracDockWidget):
        PatracDockWidget.setObjectName(_fromUtf8("PatracDockWidget"))
        PatracDockWidget.resize(302, 182)

        self.pluginPath = PatracDockWidget.pluginPath

        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))

        self.tabLayout = QVBoxLayout(self.dockWidgetContents)
        self.tabLayout.setObjectName(_fromUtf8("tabLayout"))

        self.tabWidget = QTabWidget()
        self.tabGuide = QWidget()
        self.tabWidget.addTab(self.tabGuide, QApplication.translate("PatracDockWidget", "Plan", None))

        self.tabManagement = QWidget()
        self.tabWidget.addTab(self.tabManagement, QApplication.translate("PatracDockWidget", "Management", None))

        self.verticalLayoutManagement = QVBoxLayout(self.tabManagement)
        self.verticalLayoutManagement.setObjectName(_fromUtf8("verticalLayoutManagement"))
        self.tabManagement.setLayout(self.verticalLayoutManagement)
        self.setUpStyles()
        self.setUpProgress()

        self.tabAction = QWidget()
        self.tabWidget.addTab(self.tabAction, QApplication.translate("PatracDockWidget", "Action", None))
        self.verticalLayoutAction = QVBoxLayout(self.tabAction)
        self.verticalLayoutAction.setObjectName(_fromUtf8("verticalLayoutAction"))
        self.tabAction.setLayout(self.verticalLayoutAction)
        self.setUpAction()

        self.tabAnalyze = QWidget()
        self.tabWidget.addTab(self.tabAnalyze, QApplication.translate("PatracDockWidget", "Analyze", None))
        self.verticalLayoutAnalyze = QVBoxLayout(self.tabAnalyze)
        self.verticalLayoutAnalyze.setObjectName(_fromUtf8("verticalLayoutAnalyze"))
        self.tabAnalyze.setLayout(self.verticalLayoutAnalyze)
        self.setUpAnalyse()

        self.tabExpert = QWidget()
        # self.tabWidget.addTab(self.tabExpert, QApplication.translate("PatracDockWidget", "Expert", None))

        self.verticalLayout = QVBoxLayout(self.tabExpert)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabExpert.setLayout(self.verticalLayout)

        # self.tabHelp = QWidget()
        # self.tabWidget.addTab(self.tabHelp, u"Nápověda")
        # self.setHelpTab()

        self.verticalGuideLayout = QVBoxLayout(self.tabGuide)
        self.verticalGuideLayout.setObjectName(_fromUtf8("verticalGuideLayout"))
        self.tabGuide.setLayout(self.verticalGuideLayout)

        self.horizontalLayoutToolbar = QHBoxLayout()
        self.horizontalLayoutToolbar.setObjectName(_fromUtf8("horizontalLayoutToolbar"))

        self.tbtnGetSectors = QPushButton(self.dockWidgetContents)
        self.tbtnGetSectors.setObjectName(_fromUtf8("tbtnGetSectors"))  
        self.tbtnGetSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "select_sectors.png")));
        self.tbtnGetSectors.setIconSize(QSize(32,32))
        self.tbtnGetSectors.setFixedSize(QSize(42,42))
        self.horizontalLayoutToolbar.addWidget(self.tbtnGetSectors)
        self.tbtnGetSectors.setToolTip(QApplication.translate("PatracDockWidget", "Select sectors", None))

        self.tbtnRecalculateSectors = QPushButton(self.dockWidgetContents)
        self.tbtnRecalculateSectors.setObjectName(_fromUtf8("tbtnRecalculateSectors"))  
        self.tbtnRecalculateSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "number_sectors.png")));
        self.tbtnRecalculateSectors.setIconSize(QSize(32,32))
        self.tbtnRecalculateSectors.setFixedSize(QSize(42,42))
        self.horizontalLayoutToolbar.addWidget(self.tbtnRecalculateSectors)
        self.tbtnRecalculateSectors.setToolTip(QApplication.translate("PatracDockWidget", "Renumber sectors", None))

        self.tbtnExportSectors = QPushButton(self.dockWidgetContents)
        self.tbtnExportSectors.setObjectName(_fromUtf8("tbtnExportSectors"))  
        self.tbtnExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "export_sectors.png")));
        self.tbtnExportSectors.setIconSize(QSize(32,32))
        self.tbtnExportSectors.setFixedSize(QSize(42,42))
        self.horizontalLayoutToolbar.addWidget(self.tbtnExportSectors)
        self.tbtnExportSectors.setToolTip(QApplication.translate("PatracDockWidget", "Export sectors", None))

        self.tbtnReportExportSectors = QPushButton(self.dockWidgetContents)
        self.tbtnReportExportSectors.setObjectName(_fromUtf8("tbtnReportExportSectors"))
        self.tbtnReportExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "report_export_sectors.png")));
        self.tbtnReportExportSectors.setIconSize(QSize(32, 32))
        self.tbtnReportExportSectors.setFixedSize(QSize(42, 42))
        self.horizontalLayoutToolbar.addWidget(self.tbtnReportExportSectors)
        self.tbtnReportExportSectors.setToolTip(QApplication.translate("PatracDockWidget", "Create report", None))

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar) 

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        
        #self.horizontalLayout_6 = QHBoxLayout()
        #self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.comboPerson = QComboBox(self.dockWidgetContents)
        self.comboPerson.setObjectName(_fromUtf8("comboPerson"))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 1-3", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 4-6", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 7-12", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 13-15", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Despondent", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Psychical ilness", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Retarded", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Alzheimer", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Turist", None))
        self.comboPerson.addItem(QApplication.translate("PatracDockWidget", "Demention", None))
        self.horizontalLayout_4.addWidget(self.comboPerson)
        #self.verticalLayout.addLayout(self.horizontalLayout_6)
        
        self.btnGetArea = QPushButton(self.dockWidgetContents)
        self.btnGetArea.setObjectName(_fromUtf8("btnGetArea"))
        self.horizontalLayout_4.addWidget(self.btnGetArea)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.label = QLabel(self.dockWidgetContents)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.sliderStart = QSlider(self.dockWidgetContents)
        self.sliderStart.setProperty("value", 0)
        self.sliderStart.setOrientation(QtCore.Qt.Horizontal)
        self.sliderStart.setTickPosition(QSlider.TicksBelow)
        self.sliderStart.setObjectName(_fromUtf8("sliderStart"))
        self.horizontalLayout.addWidget(self.sliderStart)
        self.spinStart = QSpinBox(self.dockWidgetContents)
        self.spinStart.setMaximum(100)
        self.spinStart.setObjectName(_fromUtf8("spinStart"))
        self.horizontalLayout.addWidget(self.spinStart)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label_2 = QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.sliderEnd = QSlider(self.dockWidgetContents)
        self.sliderEnd.setOrientation(QtCore.Qt.Horizontal)
        self.sliderEnd.setTickPosition(QSlider.TicksBelow)
        self.sliderEnd.setObjectName(_fromUtf8("sliderEnd"))
        self.horizontalLayout_2.addWidget(self.sliderEnd)
        self.spinEnd = QSpinBox(self.dockWidgetContents)
        self.spinEnd.setObjectName(_fromUtf8("spinEnd"))
        self.horizontalLayout_2.addWidget(self.spinEnd)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayoutToolbar_5 = QHBoxLayout()
        self.horizontalLayoutToolbar_5.setObjectName(_fromUtf8("horizontalLayoutToolbar_5"))

        self.tbtnShowMessage = QPushButton(self.dockWidgetContents)
        self.tbtnShowMessage.setObjectName(_fromUtf8("tbtnShowMessage"))
        self.tbtnShowMessage.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "message.png")))
        self.tbtnShowMessage.setIconSize(QSize(32, 32))
        self.tbtnShowMessage.setFixedSize(QSize(42, 42))
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowMessage)
        self.tbtnShowMessage.setToolTip(
            QApplication.translate("PatracDockWidget", "Messages", None))

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar_5)

        self.setGuideSteps()

        self.horizontalGeneralToolbarLayout = QHBoxLayout()
        self.horizontalGeneralToolbarLayout.setObjectName(_fromUtf8("horizontalGeneralToolbarLayout"))

        self.showHandlers = QPushButton(self.dockWidgetContents)
        self.showHandlers.setObjectName(_fromUtf8("helpShow"))
        self.showHandlers.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "handlers.png")))
        self.showHandlers.setIconSize(QSize(32, 32))
        self.showHandlers.setFixedSize(QSize(42, 42))
        self.showHandlers.setToolTip(
            QApplication.translate("PatracDockWidget", "Handlers", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.showHandlers)

        self.tbtnInsertFinal = QPushButton(self.dockWidgetContents)
        self.tbtnInsertFinal.setObjectName(_fromUtf8("tbtnInsertFinal"))
        self.tbtnInsertFinal.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "set_result.png")))
        self.tbtnInsertFinal.setIconSize(QSize(32, 32))
        self.tbtnInsertFinal.setFixedSize(QSize(42, 42))
        self.tbtnInsertFinal.setToolTip(QApplication.translate(
            "PatracDockWidget", "Result", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.tbtnInsertFinal)

        self.tbtnShowSettings = QPushButton(self.dockWidgetContents)
        self.tbtnShowSettings.setObjectName(_fromUtf8("tbtnShowSettings"))
        self.tbtnShowSettings.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "settings.png")))
        self.tbtnShowSettings.setIconSize(QSize(32, 32))
        self.tbtnShowSettings.setFixedSize(QSize(42, 42))
        self.tbtnShowSettings.setToolTip(
            QApplication.translate("PatracDockWidget", "Settings", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.tbtnShowSettings)

        self.helpShow = QPushButton(self.dockWidgetContents)
        self.helpShow.setObjectName(_fromUtf8("helpShow"))
        self.helpShow.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "help.png")))
        self.helpShow.setIconSize(QSize(32, 32))
        self.helpShow.setFixedSize(QSize(42, 42))
        self.helpShow.setToolTip(
            QApplication.translate("PatracDockWidget", "Help", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.helpShow)

        self.tabLayout.addWidget(self.tabWidget)
        self.tabLayout.addLayout(self.horizontalGeneralToolbarLayout)

        PatracDockWidget.setWidget(self.dockWidgetContents)
        self.retranslateUi(PatracDockWidget)
        QtCore.QMetaObject.connectSlotsByName(PatracDockWidget)

    def setUpStyles(self):

        self.horizontalLayoutStyles = QHBoxLayout()
        self.horizontalLayoutStyles.setObjectName(_fromUtf8("horizontalLayoutStyles"))

        self.sectorsUnitsRecommendedStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUnitsRecommendedStyle.setObjectName(_fromUtf8("sectorsUnitsRecommendedStyle"))
        self.sectorsUnitsRecommendedStyle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sectors_units_recommended.png")));
        self.sectorsUnitsRecommendedStyle.setIconSize(QSize(24,24));
        self.sectorsUnitsRecommendedStyle.setFixedSize(QSize(32,32));
        self.sectorsUnitsRecommendedStyle.setToolTip(QApplication.translate("PatracDockWidget", "Sectors by recommended units", None))
        self.horizontalLayoutStyles.addWidget(self.sectorsUnitsRecommendedStyle)

        self.sectorsUnitsStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUnitsStyle.setObjectName(_fromUtf8("sectorsUnitsStyle"))
        self.sectorsUnitsStyle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sectors_units.png")));
        self.sectorsUnitsStyle.setIconSize(QSize(24,24));
        self.sectorsUnitsStyle.setFixedSize(QSize(32,32));
        self.sectorsUnitsStyle.setToolTip(QApplication.translate("PatracDockWidget", "Sectors by units", None))
        self.horizontalLayoutStyles.addWidget(self.sectorsUnitsStyle)

        self.sectorsProgressStyle = QPushButton(self.dockWidgetContents)
        self.sectorsProgressStyle.setObjectName(_fromUtf8("sectorsProgressStyle"))
        self.sectorsProgressStyle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sectors_stav.png")));
        self.sectorsProgressStyle.setIconSize(QSize(24,24));
        self.sectorsProgressStyle.setFixedSize(QSize(32,32));
        self.sectorsProgressStyle.setToolTip(QApplication.translate("PatracDockWidget", "Sectors by state", None))
        self.horizontalLayoutStyles.addWidget(self.sectorsProgressStyle)

        self.sectorsUniqueStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUniqueStyle.setObjectName(_fromUtf8("sectorsUniqueStyle"))
        self.sectorsUniqueStyle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sectors_unique.png")));
        self.sectorsUniqueStyle.setIconSize(QSize(24,24));
        self.sectorsUniqueStyle.setFixedSize(QSize(32,32));
        self.sectorsUniqueStyle.setToolTip(QApplication.translate("PatracDockWidget", "Sectors by type", None))
        self.horizontalLayoutStyles.addWidget(self.sectorsUniqueStyle)

        self.sectorsSingleStyle = QPushButton(self.dockWidgetContents)
        self.sectorsSingleStyle.setObjectName(_fromUtf8("sectorsSingleStyle"))
        self.sectorsSingleStyle.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sectors_single.png")));
        self.sectorsSingleStyle.setIconSize(QSize(24,24));
        self.sectorsSingleStyle.setFixedSize(QSize(32,32));
        self.sectorsSingleStyle.setToolTip(QApplication.translate("PatracDockWidget", "Remove colors", None))
        self.horizontalLayoutStyles.addWidget(self.sectorsSingleStyle)

        self.printPrepared = QPushButton(self.dockWidgetContents)
        self.printPrepared.setObjectName(_fromUtf8("printPrepared"))
        self.printPrepared.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "print_prepared.png")));
        self.printPrepared.setIconSize(QSize(24,24));
        self.printPrepared.setFixedSize(QSize(32,32));
        self.printPrepared.setToolTip(QApplication.translate("PatracDockWidget", "PDF from report", None))
        self.horizontalLayoutStyles.addWidget(self.printPrepared)

        self.printUserDefined = QPushButton(self.dockWidgetContents)
        self.printUserDefined.setObjectName(_fromUtf8("printUserDefined"))
        self.printUserDefined.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "print_user.png")));
        self.printUserDefined.setIconSize(QSize(24,24));
        self.printUserDefined.setFixedSize(QSize(32,32));
        self.printUserDefined.setToolTip(QApplication.translate("PatracDockWidget", "Create own map", None))
        self.horizontalLayoutStyles.addWidget(self.printUserDefined)

        self.exportToCSV = QPushButton(self.dockWidgetContents)
        self.exportToCSV.setObjectName(_fromUtf8("exportToCSV"))
        self.exportToCSV.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "export_to_csv.png")));
        self.exportToCSV.setIconSize(QSize(24,24));
        self.exportToCSV.setFixedSize(QSize(32,32));
        self.exportToCSV.setToolTip(QApplication.translate("PatracDockWidget", "Export to CSV", None))
        self.horizontalLayoutStyles.addWidget(self.exportToCSV)

        self.verticalLayoutManagement.addLayout(self.horizontalLayoutStyles)

        self.chkShowLabels = QCheckBox(self.dockWidgetContents)
        self.chkShowLabels.setText(QApplication.translate("PatracDockWidget", "Show labels", None))
        self.chkShowLabels.setChecked(True)
        self.verticalLayoutManagement.addWidget(self.chkShowLabels)

    def setUpProgress(self):
        self.sectorsProgressStateLabel = QLabel(self.dockWidgetContents)
        self.sectorsProgressStateLabel.setObjectName(_fromUtf8("sectorsProgressStateLabel"))
        self.sectorsProgressStateLabel.setText(QApplication.translate("PatracDockWidget", "Click with right mouse button into the sector to set it state or analyze. For search analyze select the track.", None))
        self.sectorsProgressStateLabel.setWordWrap(True)
        self.verticalLayoutManagement.addWidget(self.sectorsProgressStateLabel)

        self.setUpTracks()

    def setUpTracks(self):
        self.horizontalLayoutTracks = QHBoxLayout()
        self.horizontalLayoutStyles.setObjectName(_fromUtf8("horizontalLayoutStyles"))

        self.guideCopyGpx = QPushButton(self.dockWidgetContents)
        self.guideCopyGpx.setObjectName(_fromUtf8("guideCopyGpx"))
        self.guideCopyGpx.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "gpx_export.png")));
        self.guideCopyGpx.setIconSize(QSize(24,24));
        self.guideCopyGpx.setFixedSize(QSize(32,32));
        self.guideCopyGpx.setToolTip(QApplication.translate("PatracDockWidget", "Save sectors to GPS", None))
        self.horizontalLayoutTracks.addWidget(self.guideCopyGpx)

        self.tbtnImportPaths = QPushButton(self.dockWidgetContents)
        self.tbtnImportPaths.setObjectName(_fromUtf8("tbtnImportPaths"))
        self.tbtnImportPaths.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "gpx_import.png")))
        self.tbtnImportPaths.setIconSize(QSize(24, 24))
        self.tbtnImportPaths.setFixedSize(QSize(32, 32))
        self.tbtnImportPaths.setToolTip(QApplication.translate("PatracDockWidget", "Import from GPS", None))
        self.horizontalLayoutTracks.addWidget(self.tbtnImportPaths)

        # self.tbtnShowSearchers = QPushButton(self.dockWidgetContents)
        # self.tbtnShowSearchers.setObjectName(_fromUtf8("tbtnShowSearchers"))
        # self.tbtnShowSearchers.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers.png")))
        # self.tbtnShowSearchers.setIconSize(QSize(24, 24))
        # self.tbtnShowSearchers.setFixedSize(QSize(32, 32))
        # self.horizontalLayoutTracks.addWidget(self.tbtnShowSearchers)
        # self.tbtnShowSearchers.setToolTip(
        #     QApplication.translate("PatracDockWidget", "Show searchers (points)", None))

        self.tbtnShowSearchersTracks = QPushButton(self.dockWidgetContents)
        self.tbtnShowSearchersTracks.setObjectName(_fromUtf8("tbtnShowSearchersTracks"))
        self.tbtnShowSearchersTracks.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers_tracks.png")))
        self.tbtnShowSearchersTracks.setIconSize(QSize(24, 24))
        self.tbtnShowSearchersTracks.setFixedSize(QSize(32, 32))
        self.horizontalLayoutTracks.addWidget(self.tbtnShowSearchersTracks)
        self.tbtnShowSearchersTracks.setToolTip(
            QApplication.translate("PatracDockWidget", "Show searchers (lines)", None))

        self.verticalLayoutManagement.addLayout(self.horizontalLayoutTracks)

        self.sectorsTracksStateLabel = QLabel(self.dockWidgetContents)
        self.sectorsTracksStateLabel.setObjectName(_fromUtf8("sectorsTracksStateLabel"))
        self.sectorsTracksStateLabel.setText(QApplication.translate("PatracDockWidget", "Tracks Note", None))
        self.sectorsTracksStateLabel.setWordWrap(True)
        self.verticalLayoutManagement.addWidget(self.sectorsTracksStateLabel)

    def setUpAction(self):

        self.horizontalLostAction = QHBoxLayout()
        self.horizontalLostAction.setObjectName(_fromUtf8("horizontalLostAction"))
        self.lostActionLabel = QLabel(self.dockWidgetContents)
        self.lostActionLabel.setObjectName(_fromUtf8("sectorsAnalyzeStateLabel"))
        self.lostActionLabel.setText(QApplication.translate("PatracDockWidget", "Lost person description", None))
        self.lostActionLabel.setWordWrap(True)
        self.horizontalLostAction.addWidget(self.lostActionLabel)
        self.tbtnSetLostPerson = QPushButton(self.dockWidgetContents)
        self.tbtnSetLostPerson.setObjectName(_fromUtf8("tbtnSetLostPerson"))
        self.tbtnSetLostPerson.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "person.png")))
        self.tbtnSetLostPerson.setIconSize(QSize(24, 24))
        self.tbtnSetLostPerson.setFixedSize(QSize(30, 30))
        self.tbtnSetLostPerson.setToolTip(QApplication.translate(
            "PatracDockWidget", "Edit lost person description", None))
        self.horizontalLostAction.addWidget(self.tbtnSetLostPerson)
        self.verticalLayoutAction.addLayout(self.horizontalLostAction)

        self.horizontalCoordinatorAction = QHBoxLayout()
        self.horizontalCoordinatorAction.setObjectName(_fromUtf8("horizontalCoordinatorAction"))
        self.coordinatorActionLabel = QLabel(self.dockWidgetContents)
        self.coordinatorActionLabel.setObjectName(_fromUtf8("sectorsAnalyzeStateLabel"))
        self.coordinatorActionLabel.setText(QApplication.translate("PatracDockWidget", "Name of the commander", None))
        self.coordinatorActionLabel.setWordWrap(True)
        self.coordinatorActionLabel.setFixedWidth(200)
        self.horizontalCoordinatorAction.addWidget(self.coordinatorActionLabel)
        self.coordinatorActionLineEdit = QLineEdit()
        self.horizontalCoordinatorAction.addWidget(self.coordinatorActionLineEdit)
        self.verticalLayoutAction.addLayout(self.horizontalCoordinatorAction)

        self.horizontalCoordinatorTelAction = QHBoxLayout()
        self.horizontalCoordinatorTelAction.setObjectName(_fromUtf8("horizontalCoordinatorTelAction"))
        self.coordinatorTelActionLabel = QLabel(self.dockWidgetContents)
        self.coordinatorTelActionLabel.setObjectName(_fromUtf8("coordinatorTelActionLabel"))
        self.coordinatorTelActionLabel.setText(QApplication.translate("PatracDockWidget", "Telephone of the commander", None))
        self.coordinatorTelActionLabel.setWordWrap(True)
        self.coordinatorTelActionLabel.setFixedWidth(200)
        self.horizontalCoordinatorTelAction.addWidget(self.coordinatorTelActionLabel)
        self.coordinatorTelActionLineEdit = QLineEdit()
        self.horizontalCoordinatorTelAction.addWidget(self.coordinatorTelActionLineEdit)
        self.verticalLayoutAction.addLayout(self.horizontalCoordinatorTelAction)

        self.horizontalPlaceHandlersAction = QHBoxLayout()
        self.horizontalPlaceHandlersAction.setObjectName(_fromUtf8("horizontalPlaceHandlersAction"))
        self.placeHandlersActionLabel = QLabel(self.dockWidgetContents)
        self.placeHandlersActionLabel.setObjectName(_fromUtf8("placeHandlersActionLabel"))
        self.placeHandlersActionLabel.setText(QApplication.translate("PatracDockWidget", "Place of meeting of handlers", None))
        self.placeHandlersActionLabel.setWordWrap(True)
        self.placeHandlersActionLabel.setFixedWidth(200)
        self.horizontalPlaceHandlersAction.addWidget(self.placeHandlersActionLabel)
        self.placeHandlersActionLineEdit = QLineEdit()
        self.horizontalPlaceHandlersAction.addWidget(self.placeHandlersActionLineEdit)
        self.tbtnSetPlaceHandlers = QPushButton(self.dockWidgetContents)
        self.tbtnSetPlaceHandlers.setObjectName(_fromUtf8("tbtnSetPlaceHandlers"))
        self.tbtnSetPlaceHandlers.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "pointer.png")))
        self.tbtnSetPlaceHandlers.setIconSize(QSize(24, 24))
        self.tbtnSetPlaceHandlers.setFixedSize(QSize(30, 30))
        self.tbtnSetPlaceHandlers.setToolTip(QApplication.translate(
            "PatracDockWidget", "Select from map", None))
        self.horizontalPlaceHandlersAction.addWidget(self.tbtnSetPlaceHandlers)
        self.verticalLayoutAction.addLayout(self.horizontalPlaceHandlersAction)

        self.horizontalPlaceOtherAction = QHBoxLayout()
        self.horizontalPlaceOtherAction.setObjectName(_fromUtf8("horizontalPlaceOtherAction"))
        self.placeOtherActionLabel = QLabel(self.dockWidgetContents)
        self.placeOtherActionLabel.setObjectName(_fromUtf8("placeOtherActionLabel"))
        self.placeOtherActionLabel.setText(QApplication.translate("PatracDockWidget", "Place of meeting of others", None))
        self.placeOtherActionLabel.setWordWrap(True)
        self.placeOtherActionLabel.setFixedWidth(200)
        self.horizontalPlaceOtherAction.addWidget(self.placeOtherActionLabel)
        self.placeOtherActionLineEdit = QLineEdit()
        self.horizontalPlaceOtherAction.addWidget(self.placeOtherActionLineEdit)
        self.tbtnSetPlaceOther = QPushButton(self.dockWidgetContents)
        self.tbtnSetPlaceOther.setObjectName(_fromUtf8("tbtnSetPlaceOther"))
        self.tbtnSetPlaceOther.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "pointer.png")))
        self.tbtnSetPlaceOther.setIconSize(QSize(24, 24))
        self.tbtnSetPlaceOther.setFixedSize(QSize(30, 30))
        self.tbtnSetPlaceOther.setToolTip(QApplication.translate(
            "PatracDockWidget", "Select from map", None))
        self.horizontalPlaceOtherAction.addWidget(self.tbtnSetPlaceOther)
        self.verticalLayoutAction.addLayout(self.horizontalPlaceOtherAction)

        self.tbtnUpdateAction = QPushButton(self.dockWidgetContents)
        self.tbtnUpdateAction.setObjectName(_fromUtf8("tbtnUpdateAction"))
        self.tbtnUpdateAction.setText(QApplication.translate(
            "PatracDockWidget", "Update action", None))
        self.tbtnUpdateAction.setToolTip(QApplication.translate(
            "PatracDockWidget", "Update action settings", None))
        self.verticalLayoutAction.addWidget(self.tbtnUpdateAction)

    def setUpAnalyse(self):

        self.sectorsAnalyzeStateLabel = QLabel(self.dockWidgetContents)
        self.sectorsAnalyzeStateLabel.setObjectName(_fromUtf8("sectorsAnalyzeStateLabel"))
        self.sectorsAnalyzeStateLabel.setText(QApplication.translate("PatracDockWidget", "Analyze Note", None))
        self.sectorsAnalyzeStateLabel.setWordWrap(True)
        self.verticalLayoutAnalyze.addWidget(self.sectorsAnalyzeStateLabel)

        self.sectorsProgressAnalyzeType = QComboBox(self.dockWidgetContents)
        self.sectorsProgressAnalyzeType.setObjectName(_fromUtf8("sectorsProgressAnalyzeType"))
        self.horizontalSectorsAnalyzeTrack = QHBoxLayout()
        self.horizontalSectorsAnalyzeTrack.setObjectName(_fromUtf8("horizontalSectorsAnalyzeTrack"))

        self.horizontalSectorsAnalyzeTrack.addWidget(self.sectorsProgressAnalyzeType)
        self.verticalLayoutAnalyze.addLayout(self.horizontalSectorsAnalyzeTrack)

        self.horizontalSectorsAnalyzeTrackValue = QHBoxLayout()
        self.horizontalSectorsAnalyzeTrackValue.setObjectName(_fromUtf8("horizontalSectorsAnalyzeTrackValue"))
        self.sectorsAnalyzeTrackValueLabel = QLabel(self.dockWidgetContents)
        self.sectorsAnalyzeTrackValueLabel.setObjectName(_fromUtf8("sectorsAnalyzeTrackValueLabel"))
        self.sectorsAnalyzeTrackValueLabel.setText(QApplication.translate("PatracDockWidget", "Buffer in m", None))
        self.horizontalSectorsAnalyzeTrackValue.addWidget(self.sectorsAnalyzeTrackValueLabel)
        self.sectorsProgressAnalyzeValue = QLineEdit()
        self.onlyInt = QIntValidator()
        self.sectorsProgressAnalyzeValue.setValidator(self.onlyInt)
        self.horizontalSectorsAnalyzeTrackValue.addWidget(self.sectorsProgressAnalyzeValue)
        self.verticalLayoutAnalyze.addLayout(self.horizontalSectorsAnalyzeTrackValue)

        self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer = QWidget()
        self.horizontalSectorsAnalyzeTrackNumberOfPersons = QHBoxLayout(self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer)
        self.horizontalSectorsAnalyzeTrackNumberOfPersons.setObjectName(_fromUtf8("horizontalSectorsAnalyzeTrackNumberOfPersons"))
        self.sectorsAnalyzeTrackNumberOfPersons = QLabel(self.dockWidgetContents)
        self.sectorsAnalyzeTrackNumberOfPersons.setObjectName(_fromUtf8("sectorsAnalyzeTrackValueLabel"))
        self.sectorsAnalyzeTrackNumberOfPersons.setText(QApplication.translate("PatracDockWidget", "Number of persons", None))
        self.horizontalSectorsAnalyzeTrackNumberOfPersons.addWidget(self.sectorsAnalyzeTrackNumberOfPersons)
        self.sectorsProgressAnalyzeNumberOfPersons = QLineEdit()
        self.onlyInt = QIntValidator()
        self.sectorsProgressAnalyzeNumberOfPersons.setValidator(self.onlyInt)
        self.horizontalSectorsAnalyzeTrackNumberOfPersons.addWidget(self.sectorsProgressAnalyzeNumberOfPersons)
        self.verticalLayoutAnalyze.addWidget(self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer)
        self.horizontalSectorsAnalyzeTrackNumberOfPersonsContainer.setEnabled(False)

    def setGuideSteps(self):
        self.tabGuideSteps = QTabWidget()
        self.tabGuideStep1 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep1, "1")
        self.setGuideLayoutStep1()
        self.tabGuideStep2 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep2, "2")
        self.setGuideLayoutStep2()
        self.tabGuideStep3 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep3, "3")
        self.setGuideLayoutStep3()
        self.tabGuideStep4 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep4, "4")
        self.setGuideLayoutStep4()
        self.tabGuideStep5 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep5, "5")
        self.setGuideLayoutStep5()
        self.tabGuideStep6 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep6, "6")
        self.setGuideLayoutStep6()
        self.tabGuideStep7 = QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep7, QApplication.translate("PatracDockWidget", "Changes in the plan", None))
        self.setGuideLayoutStep7()
        self.verticalGuideLayout.addWidget(self.tabGuideSteps)
        self.tabGuideSteps.setCurrentIndex(0)

    def setGuideLayoutStep1(self):
        self.verticalGuideLayoutStep1 = QVBoxLayout(self.tabGuideStep1)
        self.verticalGuideLayoutStep1.setObjectName(_fromUtf8("verticalGuideLayoutStep1"))
        self.guideTestSearch = QRadioButton(self.tabGuideStep1)
        self.guideTestSearch.setText(QApplication.translate("PatracDockWidget", "Education and testing", None))
        self.verticalGuideLayoutStep1.addWidget(self.guideTestSearch)
        self.guideRealSearch = QRadioButton(self.tabGuideStep1)
        self.guideRealSearch.setText(QApplication.translate("PatracDockWidget", "Real action", None))
        self.verticalGuideLayoutStep1.addWidget(self.guideRealSearch)
        self.guideLabelStep1 = QLabel(self.dockWidgetContents)
        self.guideLabelStep1.setObjectName(_fromUtf8("guideLabelStep1"))
        self.guideLabelStep1.setText(QApplication.translate("PatracDockWidget", "Enter name and description", None))
        self.guideLabelStep1.setWordWrap(True)
        self.verticalGuideLayoutStep1.addWidget(self.guideLabelStep1)
        self.guideMunicipalitySearch = QLineEdit()
        self.guideMunicipalitySearch.setMaximumWidth(280)
        self.guideMunicipalitySearch.setAlignment(Qt.AlignLeft)
        self.guideMunicipalitySearch.setPlaceholderText(QApplication.translate("PatracDockWidget", "Enter name", None))
        self.verticalGuideLayoutStep1.addWidget(self.guideMunicipalitySearch)
        self.guideSearchDescription = QLineEdit()
        self.guideSearchDescription.setMaximumWidth(280)
        self.guideSearchDescription.setAlignment(Qt.AlignLeft)
        self.guideSearchDescription.setPlaceholderText(QApplication.translate("PatracDockWidget", "Brief description", None))
        self.verticalGuideLayoutStep1.addWidget(self.guideSearchDescription)
        self.guideStep1Next = QPushButton(self.dockWidgetContents)
        self.guideStep1Next.setObjectName(_fromUtf8("guideStep1Next"))
        self.guideStep1Next.setText(QApplication.translate("PatracDockWidget", "Next", None))
        self.verticalGuideLayoutStep1.addWidget(self.guideStep1Next)
        self.tabGuideStep1.setLayout(self.verticalGuideLayoutStep1)

    def setGuideLayoutStep2(self):
        self.verticalGuideLayoutStep2 = QVBoxLayout(self.tabGuideStep2)
        self.verticalGuideLayoutStep2.setObjectName(_fromUtf8("verticalGuideLayoutStep2"))
        self.guideLabelStep2 = QLabel(self.dockWidgetContents)
        self.guideLabelStep2.setObjectName(_fromUtf8("guideLabelStep2"))
        self.guideLabelStep2.setText(QApplication.translate("PatracDockWidget", "Select type of the person", None))
        self.guideLabelStep2.setWordWrap(True)
        self.verticalGuideLayoutStep2.addWidget(self.guideLabelStep2)
        self.guideComboPerson = QComboBox(self.dockWidgetContents)
        self.guideComboPerson.setObjectName(_fromUtf8("guideComboPerson"))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 1-3", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 3-6", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 7-12", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Child 13-15", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Despondent", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Psychical ilness", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Retarded", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Alzheimer", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Turist", None))
        self.guideComboPerson.addItem(QApplication.translate("PatracDockWidget", "Demention", None))
        self.verticalGuideLayoutStep2.addWidget(self.guideComboPerson)
        self.guideLabel2Step2 = QLabel(self.dockWidgetContents)
        self.guideLabel2Step2.setObjectName(_fromUtf8("guideLabel2Step2"))
        self.guideLabel2Step2.setText(QApplication.translate("PatracDockWidget", "Guide Step 2 Note", None))
        self.guideLabel2Step2.setWordWrap(True)
        self.verticalGuideLayoutStep2.addWidget(self.guideLabel2Step2)
        self.guideStep2Next = QPushButton(self.dockWidgetContents)
        self.guideStep2Next.setObjectName(_fromUtf8("guideStep2Next"))
        self.guideStep2Next.setText(QApplication.translate("PatracDockWidget", "Next", None))
        self.verticalGuideLayoutStep2.addWidget(self.guideStep2Next)
        self.tabGuideStep2.setLayout(self.verticalGuideLayoutStep2)

    def setGuideLayoutStep3(self):
        self.verticalGuideLayoutStep3 = QVBoxLayout(self.tabGuideStep3)
        self.verticalGuideLayoutStep3.setObjectName(_fromUtf8("verticalGuideLayoutStep3"))
        self.guideLabelStep3 = QLabel(self.dockWidgetContents)
        self.guideLabelStep3.setObjectName(_fromUtf8("guideLabelStep3"))
        self.guideLabelStep3.setText(QApplication.translate("PatracDockWidget", "Click into the map for report of the last seen.", None))
        self.guideLabelStep3.setWordWrap(True)
        self.verticalGuideLayoutStep3.addWidget(self.guideLabelStep3)
        self.guideLabel2Step3 = QLabel(self.dockWidgetContents)
        self.guideLabel2Step3.setObjectName(_fromUtf8("guideLabel2Step3"))
        self.guideLabel2Step3.setText(QApplication.translate("PatracDockWidget", "If you know the time you may specify it.", None))
        self.guideLabel2Step3.setWordWrap(True)
        self.verticalGuideLayoutStep3.addWidget(self.guideLabel2Step3)
        self.guideLabel3Step3 = QLabel(self.dockWidgetContents)
        self.guideLabel3Step3.setObjectName(_fromUtf8("guideLabel3Step3"))
        self.guideLabel3Step3.setText(QApplication.translate("PatracDockWidget", "Guide Step 3 Note.", None))
        self.guideLabel3Step3.setWordWrap(True)
        self.verticalGuideLayoutStep3.addWidget(self.guideLabel3Step3)
        self.horizontalGuideStep3AddFeature = QHBoxLayout()
        self.horizontalGuideStep3AddFeature.setObjectName(_fromUtf8("horizontalGuideStep3AddFeature"))
        self.guideLabel4Step3 = QLabel(self.dockWidgetContents)
        self.guideLabel4Step3.setObjectName(_fromUtf8("guideLabel4Step3"))
        self.guideLabel4Step3.setText(QApplication.translate("PatracDockWidget", "Return to point add.", None))
        self.guideLabel4Step3.setWordWrap(True)
        self.horizontalGuideStep3AddFeature.addWidget(self.guideLabel4Step3)
        self.tbtnReturnToAddfeature = QPushButton(self.dockWidgetContents)
        self.tbtnReturnToAddfeature.setObjectName(_fromUtf8("tbtnReturnToAddfeature"))
        self.tbtnReturnToAddfeature.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "pointer.png")))
        self.tbtnReturnToAddfeature.setIconSize(QSize(24, 24))
        self.tbtnReturnToAddfeature.setFixedSize(QSize(30, 30))
        self.tbtnReturnToAddfeature.setToolTip(QApplication.translate(
            "PatracDockWidget", "Return to point add", None))
        self.horizontalGuideStep3AddFeature.addWidget(self.tbtnReturnToAddfeature)
        self.verticalGuideLayoutStep3.addLayout(self.horizontalGuideStep3AddFeature)
        self.guideStep3Next = QPushButton(self.dockWidgetContents)
        self.guideStep3Next.setObjectName(_fromUtf8("guideStep3Next"))
        self.guideStep3Next.setText(QApplication.translate("PatracDockWidget", "Next", None))
        self.verticalGuideLayoutStep3.addWidget(self.guideStep3Next)
        self.tabGuideStep3.setLayout(self.verticalGuideLayoutStep3)

    def setGuideLayoutStep4(self):
        self.verticalGuideLayoutStep4 = QVBoxLayout(self.tabGuideStep4)
        self.verticalGuideLayoutStep4.setObjectName(_fromUtf8("verticalGuideLayoutStep4"))
        self.guideLabelStep4 = QLabel(self.dockWidgetContents)
        self.guideLabelStep4.setObjectName(_fromUtf8("guideLabelStep4"))
        self.guideLabelStep4.setText(QApplication.translate("PatracDockWidget", "The search area is set to 70%", None))
        self.guideLabelStep4.setWordWrap(True)
        self.verticalGuideLayoutStep4.addWidget(self.guideLabelStep4)
        self.guideLabel2Step4 = QLabel(self.dockWidgetContents)
        self.guideLabel2Step4.setObjectName(_fromUtf8("guideLabel2Step4"))
        self.guideLabel2Step4.setText(QApplication.translate("PatracDockWidget", "Guide Step 4 Note.", None))
        self.guideLabel2Step4.setWordWrap(True)
        self.verticalGuideLayoutStep4.addWidget(self.guideLabel2Step4)
        self.guideSpinEnd = QSpinBox(self.dockWidgetContents)
        self.guideSpinEnd.setMaximum(100)
        self.guideSpinEnd.setObjectName(_fromUtf8("guideSpinEnd"))
        self.guideSpinEnd.setValue(70)
        self.verticalGuideLayoutStep4.addWidget(self.guideSpinEnd)
        self.guideStep4Next = QPushButton(self.dockWidgetContents)
        self.guideStep4Next.setObjectName(_fromUtf8("guideStep4Next"))
        self.guideStep4Next.setText(QApplication.translate("PatracDockWidget", "Next", None))
        self.verticalGuideLayoutStep4.addWidget(self.guideStep4Next)
        self.tabGuideStep4.setLayout(self.verticalGuideLayoutStep4)

    def setGuideLayoutStep5(self):
        self.verticalGuideLayoutStep5 = QVBoxLayout(self.tabGuideStep5)
        self.verticalGuideLayoutStep5.setObjectName(_fromUtf8("verticalGuideLayoutStep5"))
        self.guideLabelStep5 = QLabel(self.dockWidgetContents)
        self.guideLabelStep5.setObjectName(_fromUtf8("guideLabelStep5"))
        self.guideLabelStep5.setText(QApplication.translate("PatracDockWidget", "Number of units", None))
        self.guideLabelStep5.setWordWrap(True)
        self.verticalGuideLayoutStep5.addWidget(self.guideLabelStep5)
        self.loadAvailableUnits()
        self.guideStep5OtherUnits = QPushButton(self.dockWidgetContents)
        self.guideStep5OtherUnits.setObjectName(_fromUtf8("guideStep5OtherUnits"))
        self.guideStep5OtherUnits.setText(QApplication.translate("PatracDockWidget", "Other units", None))
        self.verticalGuideLayoutStep5.addWidget(self.guideStep5OtherUnits)
        self.guideMaxTimeLabel = QLabel(self.dockWidgetContents)
        self.guideMaxTimeLabel.setText(QApplication.translate("PatracDockWidget", "Maximum time for search", None))
        self.guideMaxTime = QLineEdit()
        self.guideMaxTime.setText("3")
        self.horizontalMaxTimeLayout = QHBoxLayout(self.tabGuideStep5)
        self.horizontalMaxTimeLayout.addWidget(self.guideMaxTimeLabel)
        self.horizontalMaxTimeLayout.addWidget(self.guideMaxTime)
        self.verticalGuideLayoutStep5.addLayout(self.horizontalMaxTimeLayout)
        self.guideLabelStep5b = QLabel(self.dockWidgetContents)
        self.guideLabelStep5b.setObjectName(_fromUtf8("guideLabelStep5b"))
        self.guideLabelStep5b.setText(QApplication.translate("PatracDockWidget", "Or maximum time for search", None))
        self.guideLabelStep5b.setWordWrap(True)
        self.verticalGuideLayoutStep5.addWidget(self.guideLabelStep5b)
        self.tabGuideStep5.setLayout(self.verticalGuideLayoutStep5)
        self.guideStep5Next = QPushButton(self.dockWidgetContents)
        self.guideStep5Next.setObjectName(_fromUtf8("guideStep5Next"))
        self.guideStep5Next.setText(QApplication.translate("PatracDockWidget", "Next", None))
        self.verticalGuideLayoutStep5.addWidget(self.guideStep5Next)
        self.tabGuideStep5.setLayout(self.verticalGuideLayoutStep5)

    def setGuideLayoutStep6(self):
        self.verticalGuideLayoutStep6 = QVBoxLayout(self.tabGuideStep6)
        self.verticalGuideLayoutStep6.setObjectName(_fromUtf8("verticalGuideLayoutStep6"))
        self.chkGenerateOverallPDF = QCheckBox(self.dockWidgetContents)
        self.chkGenerateOverallPDF.setText(QApplication.translate("PatracDockWidget", "Generate PDF", None))
        self.verticalGuideLayoutStep6.addWidget(self.chkGenerateOverallPDF)

        self.guideLabelStep6 = QLabel(self.dockWidgetContents)
        self.guideLabelStep6.setObjectName(_fromUtf8("guideLabelStep6"))
        self.guideLabelStep6.setText(QApplication.translate("PatracDockWidget", "Almost finished. You may generate PDF and then show the report.", None))
        self.guideLabelStep6.setWordWrap(True)
        self.verticalGuideLayoutStep6.addWidget(self.guideLabelStep6)

        self.guideShowReport = QPushButton(self.dockWidgetContents)
        self.guideShowReport.setObjectName(_fromUtf8("guideShowReport"))
        self.guideShowReport.setText(QApplication.translate("PatracDockWidget", "Show report", None))
        self.verticalGuideLayoutStep6.addWidget(self.guideShowReport)

        self.guideStep6ShowSectorsByType = QPushButton(self.dockWidgetContents)
        self.guideStep6ShowSectorsByType.setObjectName(_fromUtf8("guideStep6ShowSectorsByType"))
        self.guideStep6ShowSectorsByType.setText(QApplication.translate("PatracDockWidget", "Show sectors by type", None))
        self.verticalGuideLayoutStep6.addWidget(self.guideStep6ShowSectorsByType)

        self.guideStep6ShowSectorsBySuggestedUnits = QPushButton(self.dockWidgetContents)
        self.guideStep6ShowSectorsBySuggestedUnits.setObjectName(_fromUtf8("guideStep6ShowSectorsBySuggestedUnits"))
        self.guideStep6ShowSectorsBySuggestedUnits.setText(QApplication.translate("PatracDockWidget", "Show sectors by recomended units", None))
        self.verticalGuideLayoutStep6.addWidget(self.guideStep6ShowSectorsBySuggestedUnits)

        self.guideLabel2Step6 = QLabel(self.dockWidgetContents)
        self.guideLabel2Step6.setObjectName(_fromUtf8("guideLabel2Step6"))
        self.guideLabel2Step6.setText(QApplication.translate("PatracDockWidget", "Guide Step 2 Note 2.", None))
        self.guideLabel2Step6.setWordWrap(True)
        self.verticalGuideLayoutStep6.addWidget(self.guideLabel2Step6)

        self.horizontalLayoutToolbarGuide6 = QHBoxLayout()
        self.horizontalLayoutToolbarGuide6.setObjectName(_fromUtf8("horizontalLayoutToolbarGuide6"))

        self.verticalGuideLayoutStep6.addLayout(self.horizontalLayoutToolbarGuide6)
        self.tabGuideStep6.setLayout(self.verticalGuideLayoutStep6)

    def setGuideLayoutStep7(self):
        self.verticalGuideLayoutStep7 = QVBoxLayout(self.tabGuideStep7)

        self.horizontalLayoutToolbarGuideLayoutStep7 = QHBoxLayout()
        self.horizontalLayoutToolbarGuideLayoutStep7.setObjectName(_fromUtf8("horizontalLayoutToolbarGuideLayoutStep7"))

        self.tbtnExtendRegion = QPushButton(self.dockWidgetContents)
        self.tbtnExtendRegion.setObjectName(_fromUtf8("tbtnExtendRegion"))
        self.tbtnExtendRegion.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "extend_region.png")))
        self.tbtnExtendRegion.setIconSize(QSize(24, 24))
        self.tbtnExtendRegion.setFixedSize(QSize(32, 32))
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnExtendRegion)
        self.tbtnExtendRegion.setToolTip(QApplication.translate("PatracDockWidget", "Extend area", None))

        self.tbtnDefinePlaces = QPushButton(self.dockWidgetContents)
        self.tbtnDefinePlaces.setObjectName(_fromUtf8("tbtnDefinePlaces"))
        self.tbtnDefinePlaces.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "define_places.png")));
        self.tbtnDefinePlaces.setIconSize(QSize(24,24));
        self.tbtnDefinePlaces.setFixedSize(QSize(32,32));
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnDefinePlaces)
        self.tbtnDefinePlaces.setToolTip(QApplication.translate("PatracDockWidget", "Places management", None))

        self.tbtnAddPlaces = QPushButton(self.dockWidgetContents)
        self.tbtnAddPlaces.setObjectName(_fromUtf8("tbtnDefinePlaces"))
        self.tbtnAddPlaces.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "add_places.png")));
        self.tbtnAddPlaces.setIconSize(QSize(24,24));
        self.tbtnAddPlaces.setFixedSize(QSize(32,32));
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnAddPlaces)
        self.tbtnAddPlaces.setToolTip(QApplication.translate("PatracDockWidget", "Append places", None))

        self.tbtnPercent = QPushButton(self.dockWidgetContents)
        self.tbtnPercent.setObjectName(_fromUtf8("tbtnPercent"))
        self.tbtnPercent.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "percent.png")));
        self.tbtnPercent.setIconSize(QSize(24,24));
        self.tbtnPercent.setFixedSize(QSize(32,32));
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnPercent)
        self.tbtnPercent.setToolTip(QApplication.translate("PatracDockWidget", "Set percent", None))

        self.tbtnUnits = QPushButton(self.dockWidgetContents)
        self.tbtnUnits.setObjectName(_fromUtf8("tbtnUnits"))
        self.tbtnUnits.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "sap.png")));
        self.tbtnUnits.setIconSize(QSize(24,24));
        self.tbtnUnits.setFixedSize(QSize(32,32));
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnUnits)
        self.tbtnUnits.setToolTip(QApplication.translate("PatracDockWidget", "Set units", None))

        self.tbtnSwitchSectorsType = QPushButton(self.dockWidgetContents)
        self.tbtnSwitchSectorsType.setObjectName(_fromUtf8("tbtnSwitchSectorsType"))
        self.tbtnSwitchSectorsType.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "switch_sectors_type.png")));
        self.tbtnSwitchSectorsType.setIconSize(QSize(24,24));
        self.tbtnSwitchSectorsType.setFixedSize(QSize(32,32));
        self.horizontalLayoutToolbarGuideLayoutStep7.addWidget(self.tbtnSwitchSectorsType)
        self.tbtnSwitchSectorsType.setToolTip(QApplication.translate("PatracDockWidget", "Switch sectors type", None))

        self.verticalGuideLayoutStep7.addLayout(self.horizontalLayoutToolbarGuideLayoutStep7)

        self.tbtnRecalculate = QPushButton(self.dockWidgetContents)
        self.tbtnRecalculate.setObjectName(_fromUtf8("tbtnRecalculate"))
        self.tbtnRecalculate.setText(QApplication.translate("PatracDockWidget", "Recalculate", None))
        self.verticalGuideLayoutStep7.addWidget(self.tbtnRecalculate)
        self.tbtnRecalculate.setToolTip(QApplication.translate("PatracDockWidget", "Recalculate", None))

        self.tabGuideStep7.setLayout(self.verticalGuideLayoutStep7)

    def setAvailableUnitsItems(self):
        self.guideDogCountLabel = QLabel(self.dockWidgetContents)
        self.guideDogCountLabel.setText(QApplication.translate("PatracDockWidget", "Handler", None))
        self.guideDogCountLabel.setFixedWidth(100)
        self.guideDogCount = QLineEdit()
        self.horizontalDogCountLayout = QHBoxLayout(self.tabGuideStep5)
        self.horizontalDogCountLayout.addWidget(self.guideDogCountLabel)
        self.horizontalDogCountLayout.addWidget(self.guideDogCount)
        self.verticalGuideLayoutStep5.addLayout(self.horizontalDogCountLayout)

        self.guidePersonCountLabel = QLabel(self.dockWidgetContents)
        self.guidePersonCountLabel.setText(QApplication.translate("PatracDockWidget", "Person", None))
        self.guidePersonCountLabel.setFixedWidth(100)
        self.guidePersonCount = QLineEdit()
        self.horizontalPersonCountLayout = QHBoxLayout(self.tabGuideStep5)
        self.horizontalPersonCountLayout.addWidget(self.guidePersonCountLabel)
        self.horizontalPersonCountLayout.addWidget(self.guidePersonCount)
        self.verticalGuideLayoutStep5.addLayout(self.horizontalPersonCountLayout)

        self.guideDroneCountLabel = QLabel(self.dockWidgetContents)
        self.guideDroneCountLabel.setText(QApplication.translate("PatracDockWidget", "Drone", None))
        self.guideDroneCountLabel.setFixedWidth(100)
        self.guideDroneCount = QLineEdit()
        self.horizontalDroneCountLayout = QHBoxLayout(self.tabGuideStep5)
        self.horizontalDroneCountLayout.addWidget(self.guideDroneCountLabel)
        self.horizontalDroneCountLayout.addWidget(self.guideDroneCount)
        self.verticalGuideLayoutStep5.addLayout(self.horizontalDroneCountLayout)

    def loadAvailableUnits(self):
        self.setAvailableUnitsItems()
        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        with open(settingsPath + "/grass/units.txt", "r") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = row
                # dog
                if i == 0:
                    self.guideDogCount.setText(unicode_row[0])
                # person
                if i == 1:
                    self.guidePersonCount.setText(unicode_row[0])
                # diver
                if i == 5:
                    self.guideDroneCount.setText(unicode_row[0])
                i=i+1

    def retranslateUi(self, PatracDockWidget):
        PatracDockWidget.setWindowTitle(QApplication.translate(
            "PatracDockWidget", "Searcher", None))
        self.btnGetArea.setText(QApplication.translate(
            "PatracDockWidget", "Determine area", None))
        self.label.setText(QApplication.translate(
            "PatracDockWidget", "Values min/max", None))
        self.label_2.setText(QApplication.translate(
            "PatracDockWidget", "Values max/min", None))
