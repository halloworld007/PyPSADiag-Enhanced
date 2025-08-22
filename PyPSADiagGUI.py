"""
   PyPSADiagGUI.py

   Copyright (C) 2024 - 2025 Marc Postema (mpostema09 -at- gmail.com)

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
   Or, point your browser to http://www.gnu.org/copyleft/gpl.html
"""

import os
try:
    from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
        QMetaObject, QObject, QPoint, QRect,
        QSize, QTime, QUrl, Qt)
    from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
        QFont, QFontDatabase, QGradient, QIcon,
        QImage, QKeySequence, QLinearGradient, QPainter,
        QPalette, QPixmap, QRadialGradient, QTransform)
    from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
        QHBoxLayout, QLineEdit, QMainWindow, QPushButton,
        QSizePolicy, QSpacerItem, QSplitter, QStatusBar,
        QTextEdit, QVBoxLayout, QWidget, QTabWidget, QLabel, QScrollArea)
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import Qt, QObject, QRect, QSize, QUrl
        from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPixmap
        from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
            QHBoxLayout, QLineEdit, QMainWindow, QPushButton,
            QSizePolicy, QSpacerItem, QSplitter, QStatusBar,
            QTextEdit, QVBoxLayout, QWidget, QTabWidget, QLabel, QScrollArea)
        QT_FRAMEWORK = "PyQt5"

from EcuZoneTreeView  import EcuZoneTreeView
from HistoryLineEdit import HistoryLineEdit
from i18n import i18n

# Import Diagbox Integration
try:
    from DiagboxIntegration import DiagboxIntegration
    DIAGBOX_AVAILABLE = True
except ImportError:
    DIAGBOX_AVAILABLE = False

# Import Enhanced Flash Manager
try:
    from FlashUpdateManager import FlashManagerWidget
    FLASH_MANAGER_AVAILABLE = True
except ImportError:
    FLASH_MANAGER_AVAILABLE = False

# Import PSA-RE Community Integration
PSA_RE_AVAILABLE = False
try:
    # Test dependencies first
    import requests
    import yaml
    # If dependencies are available, try to import PSA-RE module
    from PSA_RE_Integration import create_psa_re_integration
    PSA_RE_AVAILABLE = True
    print(f"[PSA-RE] Integration erfolgreich geladen - requests: {requests.__version__}")
except ImportError as e:
    print(f"[PSA-RE] Import Fehler: {e}")
    print("[PSA-RE] Installiere Dependencies mit: pip install requests pyyaml")
    PSA_RE_AVAILABLE = False


class PyPSADiagGUI(object):
    currentDir = os.path.dirname(os.path.abspath(__file__))
    mainWindow = None

    def setFilePathInWindowsTitle(self, path: str()):
        if path == "":
            self.mainWindow.setWindowTitle("PyPSADiag")
        else:
            self.mainWindow.setWindowTitle("PyPSADiag (" + path + ")")

    def setupGUI(self, MainWindow, scan: bool(), lang_code: str):
        self.mainWindow = MainWindow
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1100, 800)
        MainWindow.setMinimumSize(800, 600)
        MainWindow.setSizeIncrement(QSize(1, 1))
        
        # Set Window Icon
        try:
            # Try to load icon from resources or create a simple one
            from PySide6.QtGui import QIcon, QPixmap, QPainter, QBrush
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(QColor(0, 123, 255)))  # Blue color
            painter.drawEllipse(4, 4, 24, 24)
            painter.setBrush(QBrush(QColor(255, 255, 255)))  # White
            painter.drawText(8, 20, "PSA")
            painter.end()
            MainWindow.setWindowIcon(QIcon(pixmap))
        except Exception as e:
            print(f"Warning: Could not create window icon: {e}")
            
        self.setFilePathInWindowsTitle("")
        self.centralwidget = QWidget(MainWindow)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)

        self.command = HistoryLineEdit()
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        # Setup languages
        self.setupLanguages(lang_code)

        self.sendCommand = QPushButton()
        self.openCSVFile = QPushButton()
        self.saveCSVFile = QPushButton()

        self.portNameComboBox = QComboBox()
        self.ConnectPort = QPushButton()
        self.SearchConnectPort = QPushButton()

        self.DisconnectPort = QPushButton()
        self.openZoneFile = QPushButton()
        self.ecuComboBox = QComboBox()
        self.ecuKeyComboBox = QComboBox()
        self.readZone = QPushButton()
        self.writeZone = QPushButton()
        self.rebootEcu = QPushButton()
        self.readEcuFaults = QPushButton()
        self.clearEcuFaults = QPushButton()
        self.safeQuickSetupWizard = QPushButton()
        self.psaReSyncButton = QPushButton()
        self.writeSecureTraceability = QCheckBox()
        self.virginWriteZone = QCheckBox()
        self.hideNoResponseZone = QCheckBox()
#        self.useSketchSeedGenerator = QCheckBox()

        self.treeView = EcuZoneTreeView(None)
        if scan:
            self.scanTreeView = EcuZoneTreeView(None)

        self.translateGUI(self)

        ###################################################
        # Setup Top Left Layout
        self.topLeftLayout = QVBoxLayout()
        self.topLeftLayout.addWidget(self.command)
        self.topLeftLayout.addWidget(self.output)
        ###################################################

        ###################################################
        # Setup Language Header Layout
        self.languageHeaderLayout = QHBoxLayout()

        self.languageHeaderLayout.addStretch()
        self.languageHeaderLayout.setContentsMargins(0, 10, 10, 0)
        self.languageHeaderLayout.addWidget(self.languageComboBox)

        ###################################################
        # Setup Top Right Layout
        self.topRightLayout = QVBoxLayout()
        
        # Set minimum width and height for top buttons too
        top_button_min_width = 120
        top_button_min_height = 32  # Konsistente Höhe auch oben
        self.sendCommand.setMinimumWidth(top_button_min_width)
        self.sendCommand.setMinimumHeight(top_button_min_height)
        self.openCSVFile.setMinimumWidth(top_button_min_width)
        self.openCSVFile.setMinimumHeight(top_button_min_height)
        self.saveCSVFile.setMinimumWidth(top_button_min_width)
        self.saveCSVFile.setMinimumHeight(top_button_min_height)
        self.portNameComboBox.setMinimumWidth(top_button_min_width)
        self.portNameComboBox.setMinimumHeight(top_button_min_height)
        self.SearchConnectPort.setMinimumWidth(top_button_min_width)
        self.SearchConnectPort.setMinimumHeight(top_button_min_height)
        self.ConnectPort.setMinimumWidth(top_button_min_width)
        self.ConnectPort.setMinimumHeight(top_button_min_height)
        self.DisconnectPort.setMinimumWidth(top_button_min_width)
        self.DisconnectPort.setMinimumHeight(top_button_min_height)
        
        # Tooltips für bessere Benutzerfreundlichkeit
        self.sendCommand.setToolTip("Sende Diagnose-Kommando an ECU")
        self.openCSVFile.setToolTip("Öffne CSV-Datei mit Zone-Daten")
        self.saveCSVFile.setToolTip("Speichere aktuelle Zone-Daten als CSV")
        self.portNameComboBox.setToolTip("Wähle seriellen Port oder VCI")
        self.SearchConnectPort.setToolTip("Suche verfügbare Ports")
        self.ConnectPort.setToolTip("Verbinde mit ausgewähltem Port")
        self.DisconnectPort.setToolTip("Trenne Verbindung")
        self.command.setToolTip("Gebe UDS/KWP Diagnose-Kommando ein (z.B. 1A80) [Enter zum Senden]")
        
        # Drag & Drop für Zone-Dateien aktivieren
        self.treeView.setToolTip("ECU-Zonen und Parameter\n\nTipp: Ziehe .json Zone-Dateien hierher zum Öffnen")
        MainWindow.setAcceptDrops(True)
        
        # Modernes Button-Styling
        self.applyModernStyling()
        
        self.topRightLayout.addWidget(self.sendCommand)
        self.topRightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.topRightLayout.addWidget(self.openCSVFile)
        self.topRightLayout.addWidget(self.saveCSVFile)
        self.topRightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.topRightLayout.addWidget(self.portNameComboBox)
        self.topRightLayout.addWidget(self.SearchConnectPort)
        self.topRightLayout.addWidget(self.ConnectPort)
        self.topRightLayout.addWidget(self.DisconnectPort)
        self.topRightLayout.addWidget(self.languageComboBox)
        self.topRightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        ###################################################

        ###################################################
        # Setup Bottom Left Layout (TreeView)
        self.bottomLeftLayout = QVBoxLayout()
        self.bottomLeftLayout.addWidget(self.treeView)
        ###################################################

        ###################################################
        # Setup Bottom Right Layout (Buttons) with Scroll Area
        self.bottomRightScrollArea = QScrollArea()
        self.bottomRightScrollArea.setWidgetResizable(True)
        self.bottomRightScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bottomRightScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.bottomRightScrollArea.setMinimumWidth(180)  # Platz für Buttons + Scrollbar
        self.bottomRightScrollArea.setFrameShape(QFrame.Shape.NoFrame)  # Kein Rahmen
        
        # Modernes ScrollArea Styling
        scroll_style = """
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
        """
        self.bottomRightScrollArea.setStyleSheet(scroll_style)
        
        # Widget für Scroll Area Content
        self.bottomRightWidget = QWidget()
        self.bottomRightLayout = QVBoxLayout(self.bottomRightWidget)
        
        # Set minimum width and height for all buttons to ensure readability
        button_min_width = 140
        button_min_height = 32  # Einheitliche Mindesthöhe für alle Buttons
        
        self.openZoneFile.setMinimumWidth(button_min_width)
        self.openZoneFile.setMinimumHeight(button_min_height)
        self.ecuComboBox.setMinimumWidth(button_min_width)
        self.ecuComboBox.setMinimumHeight(button_min_height)
        self.ecuKeyComboBox.setMinimumWidth(button_min_width) 
        self.ecuKeyComboBox.setMinimumHeight(button_min_height)
        self.readZone.setMinimumWidth(button_min_width)
        self.readZone.setMinimumHeight(button_min_height)
        self.writeZone.setMinimumWidth(button_min_width)
        self.writeZone.setMinimumHeight(button_min_height)
        self.readEcuFaults.setMinimumWidth(button_min_width)
        self.readEcuFaults.setMinimumHeight(button_min_height)
        self.clearEcuFaults.setMinimumWidth(button_min_width)
        self.clearEcuFaults.setMinimumHeight(button_min_height)
        self.rebootEcu.setMinimumWidth(button_min_width)
        self.rebootEcu.setMinimumHeight(button_min_height)
        
        # Kompaktere Checkboxen mit modernem Styling
        checkbox_style = """
            QCheckBox {
                spacing: 5px;
                font-size: 11px;
                max-height: 28px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #adb5bd;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #007bff;
                border-radius: 3px;
                background: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """
        
        self.virginWriteZone.setStyleSheet(checkbox_style)
        self.writeSecureTraceability.setStyleSheet(checkbox_style)
        self.hideNoResponseZone.setStyleSheet(checkbox_style)
        
        # Tooltips für ECU-Operationen
        self.openZoneFile.setToolTip("Öffne ECU Zone-Datei (.json)")
        self.ecuComboBox.setToolTip("Wähle ECU-Typ aus geladener Zone-Datei")
        self.ecuKeyComboBox.setToolTip("Wähle Sicherheitsschlüssel für ECU")
        self.readZone.setToolTip("Lese alle Zonen vom ECU")
        self.writeZone.setToolTip("Schreibe geänderte Zonen zum ECU")
        self.readEcuFaults.setToolTip("Lese Fehlerspeicher vom ECU")
        self.clearEcuFaults.setToolTip("Lösche Fehlerspeicher im ECU")
        self.rebootEcu.setToolTip("ECU Neustart (Vorsicht!)")
        self.virginWriteZone.setToolTip("Virgin Write - Erstprogrammierung")
        self.writeSecureTraceability.setToolTip("Schreibe Traceability-Daten")
        self.hideNoResponseZone.setToolTip("Verstecke Zonen ohne Antwort")
        
        self.bottomRightLayout.addWidget(self.openZoneFile)
        self.bottomRightLayout.addWidget(self.ecuComboBox)
        self.bottomRightLayout.addWidget(self.ecuKeyComboBox)
        self.bottomRightLayout.addWidget(self.readZone)
        self.bottomRightLayout.addWidget(self.writeZone)
        self.bottomRightLayout.addWidget(self.readEcuFaults)
        self.bottomRightLayout.addWidget(self.clearEcuFaults)
        self.bottomRightLayout.addWidget(self.rebootEcu)
        
        # Spacer before advanced features
        self.bottomRightLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # Safe Quick Setup Wizard Button
        self.safeQuickSetupWizard = QPushButton()
        self.safeQuickSetupWizard.setMinimumWidth(button_min_width)
        self.safeQuickSetupWizard.setMinimumHeight(button_min_height)  # Konsistente Höhe
        self.safeQuickSetupWizard.setToolTip("Sichere Ein-Klick Feature-Aktivierung mit Hardware-Erkennung")
        self.bottomRightLayout.addWidget(self.safeQuickSetupWizard)
        
        # PSA-RE Community Sync Button - Immer erstellen, später aktivieren/deaktivieren
        self.psaReSyncButton = QPushButton()
        self.psaReSyncButton.setMinimumWidth(button_min_width)
        self.psaReSyncButton.setMinimumHeight(button_min_height)
        self.psaReSyncButton.setToolTip("Synchronisiere Community ECU-Definitionen von PSA-RE Repository")
        
        # Text direkt setzen - immer aktiviert für einfache Lösung
        self.psaReSyncButton.setText("Community Sync")
        self.psaReSyncButton.setEnabled(True)
        self.psaReSyncButton.setToolTip("Synchronisiere Community ECU-Definitionen von PSA-RE Repository")
            
        self.bottomRightLayout.addWidget(self.psaReSyncButton)
        
        # Kompaktes Checkbox Layout - 2 Spalten für bessere Raumnutzung
        checkboxLayout = QHBoxLayout()
        checkboxLayout.setSpacing(5)  # Enger Abstand
        
        # Linke Spalte
        leftCheckboxLayout = QVBoxLayout()
        leftCheckboxLayout.setSpacing(2)  # Sehr enger Abstand
        leftCheckboxLayout.addWidget(self.virginWriteZone)
        leftCheckboxLayout.addWidget(self.writeSecureTraceability)
        checkboxLayout.addLayout(leftCheckboxLayout)
        
        # Rechte Spalte  
        rightCheckboxLayout = QVBoxLayout()
        rightCheckboxLayout.setSpacing(2)  # Sehr enger Abstand
        rightCheckboxLayout.addWidget(self.hideNoResponseZone)
        # Füge Spacer hinzu damit Höhe passt
        rightCheckboxLayout.addStretch()
        checkboxLayout.addLayout(rightCheckboxLayout)
        
        self.bottomRightLayout.addLayout(checkboxLayout)
#        self.bottomRightLayout.addWidget(self.useSketchSeedGenerator)
        self.bottomRightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Setze das Widget in die Scroll Area
        self.bottomRightScrollArea.setWidget(self.bottomRightWidget)
        ###################################################

        ###################################################
        # Add Top Left, Right Layout -> Main Top Layout
        self.topLayout = QHBoxLayout()
        self.topLayout.addLayout(self.topLeftLayout, 3)  # Command/Output gets 75%
        self.topLayout.addLayout(self.topRightLayout, 1)  # Buttons get 25%
        ###################################################

        ###################################################
        # Add Bottom Left, Right Layout -> Main Bottom Layout
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.addLayout(self.bottomLeftLayout, 3)  # TreeView gets 75%
        self.bottomLayout.addWidget(self.bottomRightScrollArea, 1)  # Scroll Area with buttons gets 25%
        ###################################################

        ###################################################
        # Setup splitter Vertical (Top-Bottom)
        self.splitterTopBottom = QSplitter()
        self.splitterTopBottom.setStyleSheet("QSplitter::handle {background: gray;}")
        self.splitterTopBottom.setOrientation(Qt.Orientation.Vertical)

        self.topWidget = QWidget()
        self.topWidget.setLayout(self.topLayout)
        self.splitterTopBottom.addWidget(self.topWidget)

        self.bottomWidget = QWidget()
        self.bottomWidget.setLayout(self.bottomLayout)
        self.splitterTopBottom.addWidget(self.bottomWidget)
        
        # Set reasonable proportions for splitter (Top 40%, Bottom 60%)
        self.splitterTopBottom.setStretchFactor(0, 2)  # Top section
        self.splitterTopBottom.setStretchFactor(1, 3)  # Bottom section
        ###################################################

        if scan:
            ###################################################
            # Setup Main Left Layout
            self.mainLeftLayout = QHBoxLayout()
            self.mainLeftLayout.addWidget(self.scanTreeView)
            ###################################################

            ###################################################
            # Setup Main Right Layout
            self.mainRightLayout = QHBoxLayout()
            self.mainRightLayout.addWidget(self.splitterTopBottom)
            ###################################################

            ###################################################
            # Setup splitter Horizontal (Left-Right)
            self.splitterLeftRight = QSplitter()
            self.splitterLeftRight.setOrientation(Qt.Orientation.Horizontal)

            self.mainLeftWidget = QWidget()
            self.mainLeftWidget.setLayout(self.mainLeftLayout)
            self.splitterLeftRight.addWidget(self.mainLeftWidget)

            self.mainRightWidget = QWidget()
            self.mainRightWidget.setLayout(self.mainRightLayout)
            self.splitterLeftRight.addWidget(self.mainRightWidget)
            ###################################################

        self.frame = QFrame(self.centralwidget)
        self.frame.setContentsMargins(10, 0, 10, 10)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        self.frameLayout = QHBoxLayout()
        if scan:
            self.frameLayout.addWidget(self.splitterLeftRight)
        else:
            self.frameLayout.addWidget(self.splitterTopBottom)
        self.frame.setLayout(self.frameLayout)

        # Setup language Widget
        self.languageWidget = QWidget()
        self.languageWidget.setLayout(self.languageHeaderLayout)

        # Setup Main Frame
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addWidget(self.languageWidget)
        self.mainLayout.addWidget(self.frame)
        
        self.centralwidget.setLayout(self.mainLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        
        # Status Bar hinzufügen
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        self.statusBar.showMessage("Bereit - Kein Port verbunden")
        MainWindow.setStatusBar(self.statusBar)
        
        # Keyboard Shortcuts hinzufügen
        self.setupKeyboardShortcuts(MainWindow)

    def setupLanguages(self, lang_code: str):
        self.languageComboBox = QComboBox()
        self.languageComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.languageComboBox.setMinimumWidth(100)

        flags_path = os.path.join(self.currentDir, "i18n", "flags")

        languages = [
            ("en", "English"),
            ("it", "Italiano"),
            ("de", "Deutsch"),
            ("nl", "Nederlands"),
            ("pl", "Polski"),
            ("uk", "Українська"),
        ]

        for code, name in languages:
            icon_path = os.path.join(flags_path, f"{code}.png")
            self.languageComboBox.addItem(QIcon(icon_path), name, code)

        index = self.languageComboBox.findData(lang_code)
        if index != -1:
            self.languageComboBox.setCurrentIndex(index)

    def translateGUI(self, MainWindow):
        self.sendCommand.setText(i18n().tr("Send Command"))
        self.openCSVFile.setText(i18n().tr("Open CSV File"))
        self.saveCSVFile.setText(i18n().tr("Write CSV File"))
        self.ConnectPort.setText(i18n().tr("Connect"))
        self.SearchConnectPort.setText(i18n().tr("Search"))
        self.DisconnectPort.setText(i18n().tr("Disconnect"))
        self.openZoneFile.setText(i18n().tr("Open Zone File"))
        self.readZone.setText(i18n().tr("Read"))
        self.writeZone.setText(i18n().tr("Write"))
        self.rebootEcu.setText(i18n().tr("Reboot ECU"))
        self.readEcuFaults.setText(i18n().tr("Read ECU Faults"))
        self.clearEcuFaults.setText(i18n().tr("Clear ECU Faults"))
        self.safeQuickSetupWizard.setText("Safe Quick Setup")
        
        # PSA-RE Button Text wird von main.py activatePSAREButton() gesetzt
        # Nicht hier überschreiben!
            
        self.writeSecureTraceability.setText(i18n().tr("Secure Traceability"))
        self.virginWriteZone.setText(i18n().tr("Virgin Write"))
        self.hideNoResponseZone.setText(i18n().tr("Hide 'No Response'"))
#        self.useSketchSeedGenerator.setText(i18n().tr("Use Sketch Seed Generator"))
    
    def updateStatusBar(self, message):
        """Update Status Bar mit aktueller Verbindung/ECU Info"""
        if hasattr(self, 'statusBar'):
            self.statusBar.showMessage(message)
    
    def setupKeyboardShortcuts(self, MainWindow):
        """Setup nützliche Keyboard Shortcuts"""
        try:
            from PySide6.QtGui import QShortcut, QKeySequence
            from PySide6.QtCore import Qt
            
            # Ctrl+O - Open Zone File
            open_shortcut = QShortcut(QKeySequence("Ctrl+O"), MainWindow)
            open_shortcut.activated.connect(lambda: self.openZoneFile.click())
            
            # Ctrl+S - Save CSV File  
            save_shortcut = QShortcut(QKeySequence("Ctrl+S"), MainWindow)
            save_shortcut.activated.connect(lambda: self.saveCSVFile.click())
            
            # F5 - Search/Connect Port
            connect_shortcut = QShortcut(QKeySequence("F5"), MainWindow)
            connect_shortcut.activated.connect(lambda: self.SearchConnectPort.click())
            
            # Enter - Send Command (when command field has focus)
            enter_shortcut = QShortcut(QKeySequence("Return"), MainWindow)
            enter_shortcut.activated.connect(lambda: self.sendCommand.click() if self.command.hasFocus() else None)
            
            # F1 - Read Zone
            read_shortcut = QShortcut(QKeySequence("F1"), MainWindow)
            read_shortcut.activated.connect(lambda: self.readZone.click())
            
            # F2 - Write Zone
            write_shortcut = QShortcut(QKeySequence("F2"), MainWindow)
            write_shortcut.activated.connect(lambda: self.writeZone.click())
            
            # Update tooltips to show shortcuts
            self.openZoneFile.setToolTip("Öffne ECU Zone-Datei (.json) [Ctrl+O]")
            self.saveCSVFile.setToolTip("Speichere aktuelle Zone-Daten als CSV [Ctrl+S]")
            self.SearchConnectPort.setToolTip("Suche verfügbare Ports [F5]")
            self.sendCommand.setToolTip("Sende Diagnose-Kommando an ECU [Enter]")
            self.readZone.setToolTip("Lese alle Zonen vom ECU [F1]")
            self.writeZone.setToolTip("Schreibe geänderte Zonen zum ECU [F2]")
            
        except Exception as e:
            print(f"Warning: Could not setup keyboard shortcuts: {e}")
    
    def applyModernStyling(self):
        """Modernes, konsistentes Button-Styling"""
        button_style = """
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                color: #495057;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #212529;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                border-color: #dee2e6;
                color: #adb5bd;
            }
        """
        
        # Spezielle Styling für wichtige Aktionen
        important_button_style = """
            QPushButton {
                background-color: #007bff;
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
                border-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                border-color: #6c757d;
            }
        """
        
        danger_button_style = """
            QPushButton {
                background-color: #dc3545;
                border: 1px solid #dc3545;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
                border-color: #bd2130;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
                border-color: #a71e2a;
            }
        """
        
        # Standard Buttons
        standard_buttons = [
            self.openCSVFile, self.saveCSVFile, self.SearchConnectPort,
            self.openZoneFile, self.readZone, self.readEcuFaults
        ]
        for btn in standard_buttons:
            btn.setStyleSheet(button_style)
        
        # Wichtige Aktionen (blau)
        important_buttons = [self.sendCommand, self.ConnectPort, self.safeQuickSetupWizard]
        if PSA_RE_AVAILABLE:
            important_buttons.append(self.psaReSyncButton)
        for btn in important_buttons:
            btn.setStyleSheet(important_button_style)
            
        # PSA-RE Button styling (auch wenn disabled)
        if not PSA_RE_AVAILABLE:
            self.psaReSyncButton.setStyleSheet(button_style)  # Standard styling für disabled
            
        # Gefährliche Aktionen (rot)
        danger_buttons = [self.writeZone, self.clearEcuFaults, self.rebootEcu, self.DisconnectPort]
        for btn in danger_buttons:
            btn.setStyleSheet(danger_button_style)
    
    
    

