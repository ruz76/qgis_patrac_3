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

        # for i in inspect.getmembers(PatracDockWidget):
        #     # Ignores anything starting with underscore
        #     # (that is, private and protected attributes)
        #     if not i[0].startswith('_'):
        #         # Ignores methods
        #         if not inspect.ismethod(i[1]):
        #             print(i)

        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))

        self.tabLayout = QVBoxLayout(self.dockWidgetContents)
        self.tabLayout.setObjectName(_fromUtf8("tabLayout"))

        self.tabWidget = QTabWidget()
        self.tabGuide = QWidget()
        self.tabWidget.addTab(self.tabGuide, QApplication.translate("tabGuide", "Průvodce", None))

        self.tabStyle = QWidget()
        self.tabWidget.addTab(self.tabStyle, "Zobrazení")

        self.verticalLayoutStyle = QVBoxLayout(self.tabStyle)
        self.verticalLayoutStyle.setObjectName(_fromUtf8("verticalLayoutStyle"))
        self.tabStyle.setLayout(self.verticalLayoutStyle)
        self.setUpStyles()

        self.tabProgress = QWidget()
        self.tabWidget.addTab(self.tabProgress, "Průběh")

        self.verticalLayoutProgress = QVBoxLayout(self.tabProgress)
        self.verticalLayoutProgress.setObjectName(_fromUtf8("verticalLayoutProgress"))
        self.tabProgress.setLayout(self.verticalLayoutProgress)
        self.setUpProgress()


        self.tabExpert = QWidget()
        self.tabWidget.addTab(self.tabExpert, "Expert")

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

        self.tbtnDefinePlaces = QPushButton(self.dockWidgetContents)
        self.tbtnDefinePlaces.setObjectName(_fromUtf8("tbtnDefinePlaces"))  
        self.tbtnDefinePlaces.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "define_places.png")));
        self.tbtnDefinePlaces.setIconSize(QSize(32,32));
        self.tbtnDefinePlaces.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnDefinePlaces)
        self.tbtnDefinePlaces.setToolTip(QApplication.translate("PatracDockWidget", "Správa míst", None)) 

        self.tbtnGetSectors = QPushButton(self.dockWidgetContents)
        self.tbtnGetSectors.setObjectName(_fromUtf8("tbtnGetSectors"))  
        self.tbtnGetSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "select_sectors.png")));
        self.tbtnGetSectors.setIconSize(QSize(32,32));
        self.tbtnGetSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnGetSectors)
        self.tbtnGetSectors.setToolTip(QApplication.translate("PatracDockWidget", "Vybrat sektory", None)) 

        self.tbtnRecalculateSectors = QPushButton(self.dockWidgetContents)
        self.tbtnRecalculateSectors.setObjectName(_fromUtf8("tbtnRecalculateSectors"))  
        self.tbtnRecalculateSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "number_sectors.png")));
        self.tbtnRecalculateSectors.setIconSize(QSize(32,32));
        self.tbtnRecalculateSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnRecalculateSectors)
        self.tbtnRecalculateSectors.setToolTip(QApplication.translate("PatracDockWidget", "Přečíslovat sektory", None)) 

        self.tbtnExportSectors = QPushButton(self.dockWidgetContents)
        self.tbtnExportSectors.setObjectName(_fromUtf8("tbtnExportSectors"))  
        self.tbtnExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "export_sectors.png")));
        self.tbtnExportSectors.setIconSize(QSize(32,32));
        self.tbtnExportSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnExportSectors)
        self.tbtnExportSectors.setToolTip(QApplication.translate("PatracDockWidget", "Exportovat sektory", None))

        self.tbtnReportExportSectors = QPushButton(self.dockWidgetContents)
        self.tbtnReportExportSectors.setObjectName(_fromUtf8("tbtnReportExportSectors"))
        self.tbtnReportExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "report_export_sectors.png")));
        self.tbtnReportExportSectors.setIconSize(QSize(32, 32));
        self.tbtnReportExportSectors.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnReportExportSectors)
        self.tbtnReportExportSectors.setToolTip(QApplication.translate("PatracDockWidget", "Vytvořit report", None))

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar) 

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        
        #self.horizontalLayout_6 = QHBoxLayout()
        #self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.comboPerson = QComboBox(self.dockWidgetContents)
        self.comboPerson.setObjectName(_fromUtf8("comboPerson"))
        self.comboPerson.addItem(_fromUtf8("Dítě 1-3"))
        self.comboPerson.addItem(_fromUtf8("Dítě 4-6"))
        self.comboPerson.addItem(_fromUtf8("Dítě 7-12"))
        self.comboPerson.addItem(_fromUtf8("Dítě 13-15"))
        self.comboPerson.addItem(_fromUtf8("Deprese"))
        self.comboPerson.addItem(_fromUtf8("Psychická nemoc"))
        self.comboPerson.addItem(_fromUtf8("Retardovaný"))
        self.comboPerson.addItem(_fromUtf8("Alzheimer"))
        self.comboPerson.addItem(_fromUtf8("Turista"))
        self.comboPerson.addItem(_fromUtf8("Demence"))
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

        self.tbtnExtendRegion = QPushButton(self.dockWidgetContents)
        self.tbtnExtendRegion.setObjectName(_fromUtf8("tbtnImportPaths"))
        self.tbtnExtendRegion.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "extend_region.png")));
        self.tbtnExtendRegion.setIconSize(QSize(32, 32));
        self.tbtnExtendRegion.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnExtendRegion)
        self.tbtnExtendRegion.setToolTip(QApplication.translate("PatracDockWidget", "Roszšířit oblast", None))

        self.tbtnShowSearchers = QPushButton(self.dockWidgetContents)
        self.tbtnShowSearchers.setObjectName(_fromUtf8("tbtnShowSearchers"))
        self.tbtnShowSearchers.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers.png")));
        self.tbtnShowSearchers.setIconSize(QSize(32, 32));
        self.tbtnShowSearchers.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowSearchers)
        self.tbtnShowSearchers.setToolTip(
            QApplication.translate("PatracDockWidget", "Ukázat pátrače (body)", None))

        self.tbtnShowSearchersTracks = QPushButton(self.dockWidgetContents)
        self.tbtnShowSearchersTracks.setObjectName(_fromUtf8("tbtnShowSearchersTracks"))
        self.tbtnShowSearchersTracks.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers_tracks.png")));
        self.tbtnShowSearchersTracks.setIconSize(QSize(32, 32));
        self.tbtnShowSearchersTracks.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowSearchersTracks)
        self.tbtnShowSearchersTracks.setToolTip(
            QApplication.translate("PatracDockWidget", "Ukázat pátrače (linie)", None))

        self.tbtnShowMessage = QPushButton(self.dockWidgetContents)
        self.tbtnShowMessage.setObjectName(_fromUtf8("tbtnShowMessage"))
        self.tbtnShowMessage.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "message.png")));
        self.tbtnShowMessage.setIconSize(QSize(32, 32));
        self.tbtnShowMessage.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowMessage)
        self.tbtnShowMessage.setToolTip(
            QApplication.translate("PatracDockWidget", "Zprávy", None))

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar_5)

        self.setGuideSteps()

        self.horizontalGeneralToolbarLayout = QHBoxLayout()
        self.horizontalGeneralToolbarLayout.setObjectName(_fromUtf8("horizontalGeneralToolbarLayout"))

        self.helpShow = QPushButton(self.dockWidgetContents)
        self.helpShow.setObjectName(_fromUtf8("helpShow"))
        self.helpShow.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "help.png")));
        self.helpShow.setIconSize(QSize(32, 32));
        self.helpShow.setFixedSize(QSize(42, 42));
        self.helpShow.setToolTip(
            QApplication.translate("PatracDockWidget", "Nápověda", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.helpShow)

        self.tbtnImportPaths = QPushButton(self.dockWidgetContents)
        self.tbtnImportPaths.setObjectName(_fromUtf8("tbtnImportPaths"))
        self.tbtnImportPaths.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "import_paths.png")));
        self.tbtnImportPaths.setIconSize(QSize(32, 32));
        self.tbtnImportPaths.setFixedSize(QSize(42, 42));
        self.tbtnImportPaths.setToolTip(QApplication.translate("PatracDockWidget", "Importovat cesty z GPS", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.tbtnImportPaths)

        self.tbtnShowSettings = QPushButton(self.dockWidgetContents)
        self.tbtnShowSettings.setObjectName(_fromUtf8("tbtnShowSettings"))
        self.tbtnShowSettings.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "settings.png")));
        self.tbtnShowSettings.setIconSize(QSize(32, 32));
        self.tbtnShowSettings.setFixedSize(QSize(42, 42));
        self.tbtnShowSettings.setToolTip(
            QApplication.translate("PatracDockWidget", "Nastavení", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.tbtnShowSettings)

        self.tbtnInsertFinal = QPushButton(self.dockWidgetContents)
        self.tbtnInsertFinal.setObjectName(_fromUtf8("tbtnInsertFinal"))
        self.tbtnInsertFinal.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "set_result.png")));
        self.tbtnInsertFinal.setIconSize(QSize(32, 32));
        self.tbtnInsertFinal.setFixedSize(QSize(42, 42));
        self.tbtnInsertFinal.setToolTip(QApplication.translate(
            "PatracDockWidget", "Zadat výsledek", None))
        self.horizontalGeneralToolbarLayout.addWidget(self.tbtnInsertFinal)

        self.tabLayout.addWidget(self.tabWidget)
        self.tabLayout.addLayout(self.horizontalGeneralToolbarLayout)

        PatracDockWidget.setWidget(self.dockWidgetContents)
        self.retranslateUi(PatracDockWidget)
        QtCore.QMetaObject.connectSlotsByName(PatracDockWidget)

    def setUpStyles(self):
        self.sectorsUniqueStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUniqueStyle.setObjectName(_fromUtf8("sectorsUniqueStyle"))
        self.sectorsUniqueStyle.setText("Sektory dle typu")
        self.verticalLayoutStyle.addWidget(self.sectorsUniqueStyle)

        self.sectorsUnitsRecommendedStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUnitsRecommendedStyle.setObjectName(_fromUtf8("sectorsUnitsRecommendedStyle"))
        self.sectorsUnitsRecommendedStyle.setText("Sektory dle doporučených prostředků")
        self.verticalLayoutStyle.addWidget(self.sectorsUnitsRecommendedStyle)

        self.sectorsProgressStyle = QPushButton(self.dockWidgetContents)
        self.sectorsProgressStyle.setObjectName(_fromUtf8("sectorsProgressStyle"))
        self.sectorsProgressStyle.setText("Sektory dle stavu")
        self.verticalLayoutStyle.addWidget(self.sectorsProgressStyle)

        self.sectorsUnitsStyle = QPushButton(self.dockWidgetContents)
        self.sectorsUnitsStyle.setObjectName(_fromUtf8("sectorsUnitsStyle"))
        self.sectorsUnitsStyle.setText("Sektory dle prostředků")
        self.verticalLayoutStyle.addWidget(self.sectorsUnitsStyle)

        self.sectorsSingleStyle = QPushButton(self.dockWidgetContents)
        self.sectorsSingleStyle.setObjectName(_fromUtf8("sectorsSingleStyle"))
        self.sectorsSingleStyle.setText("Odbarvit sektory")
        self.verticalLayoutStyle.addWidget(self.sectorsSingleStyle)

        self.sectorsLabelsOn = QPushButton(self.dockWidgetContents)
        self.sectorsLabelsOn.setObjectName(_fromUtf8("sectorsLabelsOn"))
        self.sectorsLabelsOn.setText("Zapnout popisky sektorů")
        self.verticalLayoutStyle.addWidget(self.sectorsLabelsOn)

        self.sectorsLabelsOff = QPushButton(self.dockWidgetContents)
        self.sectorsLabelsOff.setObjectName(_fromUtf8("sectorsLabelsOff"))
        self.sectorsLabelsOff.setText("Vypnout popisky sektorů")
        self.verticalLayoutStyle.addWidget(self.sectorsLabelsOff)

    def setUpProgress(self):
        self.sectorsProgressStateLabel = QLabel(self.dockWidgetContents)
        self.sectorsProgressStateLabel.setObjectName(_fromUtf8("sectorsProgressStateLabel"))
        self.sectorsProgressStateLabel.setText("Vyberte typ operace. Aktivujte nástroj. Klikněte do sektoru pro změnu stavu. Pokud chcete analyzovat propátrání, vyberte nejdříve vrstvu se stopou v seznamu vrstev.")
        self.sectorsProgressStateLabel.setWordWrap(True)
        self.verticalLayoutProgress.addWidget(self.sectorsProgressStateLabel)
        self.sectorsProgressStateNotStarted = QRadioButton(self.dockWidgetContents)
        self.sectorsProgressStateNotStarted.setObjectName(_fromUtf8("sectorsProgressStateNotStarted"))
        self.sectorsProgressStateNotStarted.setText("Pátrání nezahájeno")
        self.verticalLayoutProgress.addWidget(self.sectorsProgressStateNotStarted)

        self.horizontalSectorsProgressStateStarted = QHBoxLayout()
        self.horizontalSectorsProgressStateStarted.setObjectName(_fromUtf8("horizontalSectorsProgressStateStarted"))

        self.sectorsProgressStateStarted = QRadioButton(self.dockWidgetContents)
        self.sectorsProgressStateStarted.setObjectName(_fromUtf8("sectorsProgressStateStarted"))
        self.sectorsProgressStateStarted.setChecked(True)
        self.sectorsProgressStateStarted.setText("Pátrání zahájeno")
        self.sectorsProgressType = QComboBox(self.dockWidgetContents)
        self.sectorsProgressType.setObjectName(_fromUtf8("sectorsProgressType"))
        self.sectorsProgressType.addItem(_fromUtf8("KPT"))
        self.sectorsProgressType.addItem(_fromUtf8("PT"))
        self.sectorsProgressType.addItem(_fromUtf8("APT"))
        self.sectorsProgressType.addItem(_fromUtf8("JPT"))

        self.horizontalSectorsProgressStateStarted.addWidget(self.sectorsProgressStateStarted)
        self.horizontalSectorsProgressStateStarted.addWidget(self.sectorsProgressType)
        self.verticalLayoutProgress.addLayout(self.horizontalSectorsProgressStateStarted)

        self.sectorsProgressStateFinished = QRadioButton(self.dockWidgetContents)
        self.sectorsProgressStateFinished.setObjectName(_fromUtf8("sectorsProgressStateFinished"))
        self.sectorsProgressStateFinished.setText("Pátrání dokončeno")
        self.verticalLayoutProgress.addWidget(self.sectorsProgressStateFinished)
        self.sectorsProgressAnalyzeTrack = QRadioButton(self.dockWidgetContents)
        self.sectorsProgressAnalyzeTrack.setObjectName(_fromUtf8("sectorsProgressStateFinished"))
        self.sectorsProgressAnalyzeTrack.setText("Analýza propátrání")
        self.verticalLayoutProgress.addWidget(self.sectorsProgressAnalyzeTrack)
        self.sectorsProgress = QPushButton(self.dockWidgetContents)
        self.sectorsProgress.setObjectName(_fromUtf8("sectorsProgress"))
        self.sectorsProgress.setText("Aktivovat")
        self.verticalLayoutProgress.addWidget(self.sectorsProgress)

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
        self.verticalGuideLayout.addWidget(self.tabGuideSteps)
        self.tabGuideSteps.setCurrentIndex(0)

    def setGuideLayoutStep1(self):
        self.verticalGuideLayoutStep1 = QVBoxLayout(self.tabGuideStep1)
        self.verticalGuideLayoutStep1.setObjectName(_fromUtf8("verticalGuideLayoutStep1"))
        self.guideLabelStep1 = QLabel(self.dockWidgetContents)
        self.guideLabelStep1.setObjectName(_fromUtf8("guideLabelStep1"))
        self.guideLabelStep1.setText("Zadejte název obce a popis")
        self.guideLabelStep1.setWordWrap(True)
        self.verticalGuideLayoutStep1.addWidget(self.guideLabelStep1)
        self.guideMunicipalitySearch = QLineEdit()
        self.guideMunicipalitySearch.setMaximumWidth(280)
        self.guideMunicipalitySearch.setAlignment(Qt.AlignLeft)
        self.guideMunicipalitySearch.setPlaceholderText("Zadejte název obce ...")
        self.verticalGuideLayoutStep1.addWidget(self.guideMunicipalitySearch)
        self.guideSearchDescription = QLineEdit()
        self.guideSearchDescription.setMaximumWidth(280)
        self.guideSearchDescription.setAlignment(Qt.AlignLeft)
        self.guideSearchDescription.setPlaceholderText("Zadejte stručný popis pátrání")
        self.verticalGuideLayoutStep1.addWidget(self.guideSearchDescription)
        self.guideStep1Next = QPushButton(self.dockWidgetContents)
        self.guideStep1Next.setObjectName(_fromUtf8("guideStep1Next"))
        self.guideStep1Next.setText("Další")
        self.verticalGuideLayoutStep1.addWidget(self.guideStep1Next)
        self.tabGuideStep1.setLayout(self.verticalGuideLayoutStep1)

    def setGuideLayoutStep2(self):
        self.verticalGuideLayoutStep2 = QVBoxLayout(self.tabGuideStep2)
        self.verticalGuideLayoutStep2.setObjectName(_fromUtf8("verticalGuideLayoutStep2"))
        self.guideLabelStep2 = QLabel(self.dockWidgetContents)
        self.guideLabelStep2.setObjectName(_fromUtf8("guideLabelStep2"))
        self.guideLabelStep2.setText("Klikněte do mapy, kde máte hlášení o spatření osoby. Kliknout můžete vícekrát."
                                     "Mapu si můžete přiblížit, ale následně je nutné se přepnout zpět na aktuálně aktivní ikonu.")
        self.guideLabelStep2.setWordWrap(True)
        self.verticalGuideLayoutStep2.addWidget(self.guideLabelStep2)
        self.guideStep2Next = QPushButton(self.dockWidgetContents)
        self.guideStep2Next.setObjectName(_fromUtf8("guideStep2Next"))
        self.guideStep2Next.setText("Další")
        self.verticalGuideLayoutStep2.addWidget(self.guideStep2Next)
        self.tabGuideStep2.setLayout(self.verticalGuideLayoutStep2)

    def setGuideLayoutStep3(self):
        self.verticalGuideLayoutStep3 = QVBoxLayout(self.tabGuideStep3)
        self.verticalGuideLayoutStep3.setObjectName(_fromUtf8("verticalGuideLayoutStep3"))
        self.guideLabelStep3 = QLabel(self.dockWidgetContents)
        self.guideLabelStep3.setObjectName(_fromUtf8("guideLabelStep3"))
        self.guideLabelStep3.setText("Vyberte typ pohřešované osoby. Následně dojde k určení pravděpodobnosti výskytu. Výpočet může trvat i několik minut.")
        self.guideLabelStep3.setWordWrap(True)
        self.verticalGuideLayoutStep3.addWidget(self.guideLabelStep3)
        self.guideComboPerson = QComboBox(self.dockWidgetContents)
        self.guideComboPerson.setObjectName(_fromUtf8("guideComboPerson"))
        self.guideComboPerson.addItem(_fromUtf8("Dítě 1-3"))
        self.guideComboPerson.addItem(_fromUtf8("Dítě 3-6"))
        self.guideComboPerson.addItem(_fromUtf8("Dítě 7-12"))
        self.guideComboPerson.addItem(_fromUtf8("Dítě 13-15"))
        self.guideComboPerson.addItem(_fromUtf8("Deprese"))
        self.guideComboPerson.addItem(_fromUtf8("Psychická nemoc"))
        self.guideComboPerson.addItem(_fromUtf8("Retardovaný"))
        self.guideComboPerson.addItem(_fromUtf8("Alzheimer"))
        self.guideComboPerson.addItem(_fromUtf8("Turista"))
        self.guideComboPerson.addItem(_fromUtf8("Demence"))
        self.verticalGuideLayoutStep3.addWidget(self.guideComboPerson)
        self.guideStep3Next = QPushButton(self.dockWidgetContents)
        self.guideStep3Next.setObjectName(_fromUtf8("guideStep3Next"))
        self.guideStep3Next.setText("Další")
        self.verticalGuideLayoutStep3.addWidget(self.guideStep3Next)
        self.tabGuideStep3.setLayout(self.verticalGuideLayoutStep3)

    def setGuideLayoutStep4(self):
        self.verticalGuideLayoutStep4 = QVBoxLayout(self.tabGuideStep4)
        self.verticalGuideLayoutStep4.setObjectName(_fromUtf8("verticalGuideLayoutStep4"))
        self.guideLabelStep4 = QLabel(self.dockWidgetContents)
        self.guideLabelStep4.setObjectName(_fromUtf8("guideLabelStep4"))
        self.guideLabelStep4.setText("Procento případů jsem nastavil na 70%. Procento můžete změnit. "
                                     "Zvýšení procenta však vede k delší době výpočtu a výběru větší oblasti, než je obvykle možné propátrat v rozumné době.")
        self.guideLabelStep4.setWordWrap(True)
        self.verticalGuideLayoutStep4.addWidget(self.guideLabelStep4)
        self.guideSpinEnd = QSpinBox(self.dockWidgetContents)
        self.guideSpinEnd.setMaximum(100)
        self.guideSpinEnd.setObjectName(_fromUtf8("guideSpinEnd"))
        self.guideSpinEnd.setValue(70)
        self.verticalGuideLayoutStep4.addWidget(self.guideSpinEnd)
        self.guideStep4Next = QPushButton(self.dockWidgetContents)
        self.guideStep4Next.setObjectName(_fromUtf8("guideStep4Next"))
        self.guideStep4Next.setText("Další")
        self.verticalGuideLayoutStep4.addWidget(self.guideStep4Next)
        self.tabGuideStep4.setLayout(self.verticalGuideLayoutStep4)

    def setGuideLayoutStep5(self):
        self.verticalGuideLayoutStep5 = QVBoxLayout(self.tabGuideStep5)
        self.verticalGuideLayoutStep5.setObjectName(_fromUtf8("verticalGuideLayoutStep5"))
        self.guideLabelStep5 = QLabel(self.dockWidgetContents)
        self.guideLabelStep5.setObjectName(_fromUtf8("guideLabelStep5"))
        self.guideLabelStep5.setText("Zde můžete upravit počty prostředků, pokud je aktuálně znáte.")
        self.guideLabelStep5.setWordWrap(True)
        self.verticalGuideLayoutStep5.addWidget(self.guideLabelStep5)
        self.loadAvailableUnits()
        self.guideLabelStep5b = QLabel(self.dockWidgetContents)
        self.guideLabelStep5b.setObjectName(_fromUtf8("guideLabelStep5b"))
        self.guideLabelStep5b.setText("Nebo stanovit maximální dobu pátrání.")
        self.guideLabelStep5b.setWordWrap(True)
        self.verticalGuideLayoutStep5.addWidget(self.guideLabelStep5b)
        self.guideMaxTimeLabel = QLabel(self.dockWidgetContents)
        self.guideMaxTimeLabel.setText("Maximální doba pátrání")
        self.guideMaxTime = QLineEdit()
        self.guideMaxTime.setText("3")
        self.horizontalMaxTimeLayout = QHBoxLayout(self.tabGuideStep5)
        self.horizontalMaxTimeLayout.addWidget(self.guideMaxTimeLabel)
        self.horizontalMaxTimeLayout.addWidget(self.guideMaxTime)
        self.verticalGuideLayoutStep5.addLayout(self.horizontalMaxTimeLayout)
        self.guideStep5Next = QPushButton(self.dockWidgetContents)
        self.guideStep5Next.setObjectName(_fromUtf8("guideStep5Next"))
        self.guideStep5Next.setText("Další")
        self.verticalGuideLayoutStep5.addWidget(self.guideStep5Next)
        self.tabGuideStep5.setLayout(self.verticalGuideLayoutStep5)

    def setGuideLayoutStep6(self):
        self.verticalGuideLayoutStep6 = QVBoxLayout(self.tabGuideStep6)
        self.verticalGuideLayoutStep6.setObjectName(_fromUtf8("verticalGuideLayoutStep6"))
        self.guideLabelStep6 = QLabel(self.dockWidgetContents)
        self.guideLabelStep6.setObjectName(_fromUtf8("guideLabelStep6"))
        self.guideLabelStep6.setText("Téměř dokončeno. Report obsahuje odkazy na PDF pro tisk a GPX pro GPS přijímače. PDF zatím nebyly vygenerovány. Generování PDF může trvat poměrně dlouho (řádově minuty). \nNezapomeňte zadat výsledek pátrání.")
        self.guideLabelStep6.setWordWrap(True)
        self.verticalGuideLayoutStep6.addWidget(self.guideLabelStep6)
        self.chkGenerateOverallPDF = QCheckBox(self.dockWidgetContents)
        self.chkGenerateOverallPDF.setText("Vygenerovat souhrnné PDF pro tisk")
        self.verticalGuideLayoutStep6.addWidget(self.chkGenerateOverallPDF)
        #self.chkGeneratePDF = QCheckBox(self.dockWidgetContents)
        #self.chkGeneratePDF.setText(u"Vygenerovat PDF pro tisk")
        #self.verticalGuideLayoutStep6.addWidget(self.chkGeneratePDF)
        self.guideShowReport = QPushButton(self.dockWidgetContents)
        self.guideShowReport.setObjectName(_fromUtf8("guideShowReport"))
        self.guideShowReport.setText("Zobrazit report")
        self.verticalGuideLayoutStep6.addWidget(self.guideShowReport)

        self.guideCopyGpx = QPushButton(self.dockWidgetContents)
        self.guideCopyGpx.setObjectName(_fromUtf8("guideCopyGpx"))
        self.guideCopyGpx.setText("Uložit sektory na GPS")
        self.verticalGuideLayoutStep6.addWidget(self.guideCopyGpx)

        self.horizontalLayoutToolbarGuide6 = QHBoxLayout()
        self.horizontalLayoutToolbarGuide6.setObjectName(_fromUtf8("horizontalLayoutToolbarGuide6"))

        self.verticalGuideLayoutStep6.addLayout(self.horizontalLayoutToolbarGuide6)
        self.tabGuideStep6.setLayout(self.verticalGuideLayoutStep6)

    def loadAvailableUnits(self):
        settingsPath = self.pluginPath + "/../../../qgis_patrac_settings"
        with open(settingsPath + "/grass/units.txt", "r") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = row
                # dog
                if i == 0:
                    self.guideDogCountLabel = QLabel(self.dockWidgetContents)
                    self.guideDogCountLabel.setText("Pes")
                    self.guideDogCount = QLineEdit()
                    self.guideDogCount.setText(unicode_row[0])
                    self.horizontalDogCountLayout = QHBoxLayout(self.tabGuideStep5)
                    self.horizontalDogCountLayout.addWidget(self.guideDogCountLabel)
                    self.horizontalDogCountLayout.addWidget(self.guideDogCount)
                    self.verticalGuideLayoutStep5.addLayout(self.horizontalDogCountLayout)
                # person
                if i == 1:
                    self.guidePersonCountLabel = QLabel(self.dockWidgetContents)
                    self.guidePersonCountLabel.setText("Člověk do rojnice")
                    self.guidePersonCount = QLineEdit()
                    self.guidePersonCount.setText(unicode_row[0])
                    self.horizontalPersonCountLayout = QHBoxLayout(self.tabGuideStep5)
                    self.horizontalPersonCountLayout.addWidget(self.guidePersonCountLabel)
                    self.horizontalPersonCountLayout.addWidget(self.guidePersonCount)
                    self.verticalGuideLayoutStep5.addLayout(self.horizontalPersonCountLayout)
                # diver
                if i == 5:
                    self.guideDiverCountLabel = QLabel(self.dockWidgetContents)
                    self.guideDiverCountLabel.setText("Potápěč")
                    self.guideDiverCount = QLineEdit()
                    self.guideDiverCount.setText(unicode_row[0])
                    self.horizontalDiverCountLayout = QHBoxLayout(self.tabGuideStep5)
                    self.horizontalDiverCountLayout.addWidget(self.guideDiverCountLabel)
                    self.horizontalDiverCountLayout.addWidget(self.guideDiverCount)
                    self.verticalGuideLayoutStep5.addLayout(self.horizontalDiverCountLayout)
                i=i+1

    def retranslateUi(self, PatracDockWidget):
        PatracDockWidget.setWindowTitle(QApplication.translate(
            "PatracDockWidget", "Pátrač", None))
        self.btnGetArea.setText(QApplication.translate(
            "PatracDockWidget", "Určit prostor", None))
        self.label.setText(QApplication.translate(
            "PatracDockWidget", "Hodnoty min/max", None))
        self.label_2.setText(QApplication.translate(
            "PatracDockWidget", "Hodnoty max/min", None))
