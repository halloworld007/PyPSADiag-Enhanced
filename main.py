"""
   main.py

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

import sys
import random
import json
import csv
import time
import os
from datetime import datetime
try:
    from PySide6.QtCore import Qt, Slot, QIODevice, QTranslator
    from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
except ImportError:
    try:
        from qt_compat import Qt, Slot, QIODevice, QTranslator, QApplication, QMainWindow, QFileDialog, QMessageBox
    except ImportError:
        from PyQt5.QtCore import Qt, QIODevice, QTranslator
        from PyQt5.QtCore import pyqtSlot as Slot
        from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

from PyPSADiagGUI import PyPSADiagGUI
import FileLoader
from DiagnosticCommunication import DiagnosticCommunication
from SeedKeyAlgorithm import SeedKeyAlgorithm
from SerialPort import SerialPort
from FileConverter import FileConverter
from EcuZoneTreeView  import EcuZoneTreeView
from MessageDialog  import MessageDialog
from i18n import i18n

# Enhanced Feature Activation System
try:
    from EnhancedFeatureActivationSystem import EnhancedFeatureActivationSystem
    ENHANCED_FEATURES_AVAILABLE = True
    print("[ENHANCED] Enhanced Feature Activation System verfügbar")
except ImportError as e:
    ENHANCED_FEATURES_AVAILABLE = False
    print(f"[ENHANCED] Enhanced Features nicht verfügbar: {e}")

# Professional Systems Integration
try:
    from ConnectionHealthMonitor import ConnectionHealthMonitor, integrate_connection_health_monitor
    from EnhancedErrorRecovery import EnhancedErrorRecovery, integrate_error_recovery
    from SmartECUAutoDiscovery import SmartECUAutoDiscovery, integrate_ecu_auto_discovery
    from ProfessionalLoggingSystem import PyPSALogger, integrate_professional_logging
    from FeatureTemplateSystem import FeatureTemplateManager, integrate_feature_template_system
    PROFESSIONAL_SYSTEMS_AVAILABLE = True
    print("[SYSTEMS] Professional Systems verfügbar")
except ImportError as e:
    PROFESSIONAL_SYSTEMS_AVAILABLE = False
    print(f"[SYSTEMS] Professional Systems nicht verfügbar: {e}")


"""
  - Change GUI in: PyPSADiagGUI.py
  - Run with: python main.py
"""
class MainWindow(QMainWindow):
    ui = PyPSADiagGUI()
    ecuObjectList = {}
    simulation = False
    scan = False
    stream = None
    csvWriter = None

    def __init__(self):
        super(MainWindow, self).__init__()
        self.lang_code = "en"
        self.lang = False
        if len(sys.argv) >= 2:
            for arg in sys.argv:
                if arg == "--lang":
                    self.lang = True
                elif self.lang:
                    self.lang = False
                    self.lang_code = str(arg)
                elif arg == "--simu":
                    self.simulation = True
                elif arg == "--scan":
                    self.scan = True
                elif arg == "--checkcalc":
                    try:
                        calc = SeedKeyAlgorithm()
                        calc.testCalculations()
                        sys.exit(0)
                    except Exception as e:
                        print(f"Error running seed key calculations: {e}")
                        sys.exit(1)
                elif arg == "--help":
                    print("Use --simu      For simulation")
                    print("Use --lang nl   For NL translation")
                    print("Use --checkcalc Test seed/key calculations")
                    sys.exit(0)

        self.addTranslators()

        self.ui.setupGUI(self, self.scan, self.lang_code)
        self.ui.languageComboBox.currentIndexChanged.connect(self.changeLanguage)
        
        # PSA-RE Button ist immer aktiv - Dependencies werden zur Laufzeit geprüft
        
        # Initialize Professional Features (placeholder for future features)
        

        #converter = FileConverter()
        #converter.convertNAC("./json/test_nac_original.json", "./json/test_nac_conv.json")
        #converter.convertCIROCCO("./json/test_CIROCCO_original.json", "./json/test_CIROCCO_conv.json")

        # Connect button signals to slots
        self.ui.sendCommand.clicked.connect(self.sendCommand)
        self.ui.openCSVFile.clicked.connect(self.openCSVFile)
        self.ui.saveCSVFile.clicked.connect(self.saveCSVFile)
        self.ui.openZoneFile.clicked.connect(self.openZoneFile)
        self.ui.readZone.clicked.connect(self.readZone)
        self.ui.writeZone.clicked.connect(self.writeZone)
        self.ui.rebootEcu.clicked.connect(self.rebootEcu)
        self.ui.readEcuFaults.clicked.connect(self.readEcuFaults)
        self.ui.clearEcuFaults.clicked.connect(self.clearEcuFaults)
        self.ui.SearchConnectPort.clicked.connect(self.searchConnectPort)
        self.ui.ConnectPort.clicked.connect(self.connectPort)
        self.ui.DisconnectPort.clicked.connect(self.disconnectPort)
        self.ui.hideNoResponseZone.stateChanged.connect(self.hideNoResponseZones)
        self.ui.safeQuickSetupWizard.clicked.connect(self.launchSafeQuickSetupWizard)
        
        # Connect PSA-RE Community Sync - Immer verbinden, Dependencies zur Laufzeit prüfen
        try:
            if hasattr(self.ui, 'psaReSyncButton'):
                self.ui.psaReSyncButton.clicked.connect(self.startPSARESync)
                print("[PSA-RE] Community Sync Button verbunden (Dependencies werden zur Laufzeit geprüft)")
            else:
                print("[PSA-RE] FEHLER: Button nicht in GUI gefunden!")
        except Exception as e:
            print(f"[PSA-RE] Verbindung fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()

        # Connect Other/General signals to slots
        self.ui.command.returnPressed.connect(self.sendCommand)

        # Setup serial controller
        self.serialController = SerialPort(self.simulation)
        self.serialController.fillPortNameCombobox(self.ui.portNameComboBox)

        # Set initial button states
        self.ui.DisconnectPort.setEnabled(False)
        self.ui.readZone.setEnabled(False)
        self.ui.writeZone.setEnabled(False)
        self.ui.rebootEcu.setEnabled(False)
        self.ui.clearEcuFaults.setEnabled(False)
        self.ui.readEcuFaults.setEnabled(False)
        self.ui.virginWriteZone.setCheckState(Qt.Unchecked)
        self.ui.writeSecureTraceability.setCheckState(Qt.Checked)
#        self.ui.useSketchSeedGenerator.setCheckState(Qt.Unchecked)

        # UDS
        self.udsCommunication = DiagnosticCommunication(self.serialController, "uds")
        self.udsCommunication.receivedPacketSignal.connect(self.serialPacketReceiverCallback)
        self.udsCommunication.outputToTextEditSignal.connect(self.outputToTextEditCallback)
        self.udsCommunication.updateZoneDataSignal.connect(self.updateZoneDataback)

        # KWP_IS
        self.kwpisCommunication = DiagnosticCommunication(self.serialController, "kwp_is")
        self.kwpisCommunication.receivedPacketSignal.connect(self.serialPacketReceiverCallback)
        self.kwpisCommunication.outputToTextEditSignal.connect(self.outputToTextEditCallback)
        self.kwpisCommunication.updateZoneDataSignal.connect(self.updateZoneDataback)

        # KWP_HAB
        self.kwphabCommunication = DiagnosticCommunication(self.serialController, "kwp_hab")
        self.kwphabCommunication.receivedPacketSignal.connect(self.serialPacketReceiverCallback)
        self.kwphabCommunication.outputToTextEditSignal.connect(self.outputToTextEditCallback)
        self.kwphabCommunication.updateZoneDataSignal.connect(self.updateZoneDataback)

        # Open CSV reader, load file with method "enable(path)"
        self.fileLoaderThread = FileLoader.FileLoaderThread()
        self.fileLoaderThread.newRowSignal.connect(self.csvReadCallback)

        # Initialize Enhanced Feature Activation System (after all communication objects are created)
        self.setupEnhancedFeatures()

    def setupEnhancedFeatures(self):
        """Initialisiert Enhanced Feature Activation System"""
        if ENHANCED_FEATURES_AVAILABLE:
            try:
                print("[ENHANCED] Initialisiere Enhanced Feature System...")
                
                # Enhanced System erstellen mit realer ECU-Liste
                self.enhanced_system = EnhancedFeatureActivationSystem(
                    communication_bridge=self.udsCommunication,
                    real_ecu_list=self.ecuObjectList
                )
                
                # Als neuen Tab hinzufügen (falls Tab-System vorhanden)
                if hasattr(self.ui, 'tabWidget'):
                    try:
                        tab_index = self.ui.tabWidget.addTab(self.enhanced_system, "🚀 Enhanced Features")
                        print(f"[ENHANCED] Enhanced Features Tab hinzugefügt (Index: {tab_index})")
                    except Exception as e:
                        print(f"[ENHANCED] Tab-Integration fehlgeschlagen: {e}")
                        # Fallback: Als eigenständiges Fenster
                        self.enhanced_system.setWindowTitle("PyPSADiag - Enhanced Feature Activation")
                        print("[ENHANCED] Enhanced System als eigenständiges Fenster verfügbar")
                
                # Enhanced Features Menü-Eintrag hinzufügen (falls Menü vorhanden)
                if hasattr(self.ui, 'menubar') or hasattr(self.ui, 'menuBar'):
                    try:
                        menubar = getattr(self.ui, 'menubar', None) or getattr(self.ui, 'menuBar', None)
                        if menubar:
                            # Versuche existierendes "Features" Menü zu finden oder erstelle neues
                            features_menu = None
                            for action in menubar.actions():
                                if action.text() in ["Features", "&Features", "Tools", "&Tools"]:
                                    features_menu = action.menu()
                                    break
                            
                            if not features_menu:
                                # Neues Features-Menü erstellen
                                features_menu = menubar.addMenu("&Enhanced Features")
                            
                            # Enhanced Features Action hinzufügen
                            enhanced_action = features_menu.addAction("🚀 Enhanced Feature Activation")
                            enhanced_action.triggered.connect(self.showEnhancedFeatures)
                            print("[ENHANCED] Menü-Eintrag für Enhanced Features hinzugefügt")
                            
                    except Exception as e:
                        print(f"[ENHANCED] Menü-Integration fehlgeschlagen: {e}")
                
                print("[ENHANCED] Enhanced Feature System erfolgreich initialisiert")
                print("[ENHANCED] >> Zugriff über Tastenkombination: Strg+E")
                print("[ENHANCED] >> Verfügbare Features:")
                print("[ENHANCED]    * Intelligenter Feature-Assistent")
                print("[ENHANCED]    * Visual Feature Browser")
                print("[ENHANCED]    * Erweiterte Pre-Activation Checks")
                print("[ENHANCED]    * Smart Backup System")
                
                # Professional Systems Integration
                self.setupProfessionalSystems()
                
                # Keyboard-Shortcut hinzufügen
                try:
                    try:
                        from PySide6.QtGui import QShortcut, QKeySequence
                    except ImportError:
                        from PySide6.QtWidgets import QShortcut
                        from PySide6.QtGui import QKeySequence
                    
                    self.enhanced_shortcut = QShortcut("Ctrl+E", self)
                    self.enhanced_shortcut.activated.connect(self.showEnhancedFeatures)
                    print("[ENHANCED] Keyboard-Shortcut Strg+E aktiviert")
                    
                except ImportError:
                    try:
                        from PyQt5.QtWidgets import QShortcut
                        from PyQt5.QtGui import QKeySequence
                        
                        self.enhanced_shortcut = QShortcut("Ctrl+E", self)
                        self.enhanced_shortcut.activated.connect(self.showEnhancedFeatures)
                        print("[ENHANCED] Keyboard-Shortcut Strg+E aktiviert")
                        
                    except Exception:
                        print("[ENHANCED] Keyboard-Shortcuts nicht verfügbar")
                except Exception as e:
                    print(f"[ENHANCED] Shortcut-Fehler: {e}")
                
            except Exception as e:
                print(f"[ENHANCED] Fehler bei Enhanced Features Setup: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[ENHANCED] Enhanced Features nicht verfügbar - Module nicht importiert")
    
    def setupProfessionalSystems(self):
        """Initialisiert Professional Systems"""
        if PROFESSIONAL_SYSTEMS_AVAILABLE:
            try:
                print("[SYSTEMS] Initialisiere Professional Systems...")
                
                # Rekursions-Schutz für Logging
                self._system_init_in_progress = True
                
                # 1. Professional Logging System
                try:
                    self.professional_logger, self.logging_widget = integrate_professional_logging(self, "logs")
                    # KEIN LOGGING während der Initialisierung um Rekursion zu vermeiden
                    print("[SYSTEMS] [OK] Professional Logging System initialisiert")
                except Exception as e:
                    print(f"[SYSTEMS] [ERROR] Logging System Fehler: {e}")
                
                # 2. Connection Health Monitor
                try:
                    self.health_monitor, self.health_widget = integrate_connection_health_monitor(self, self.serialController)
                    # KEIN LOGGING während der Initialisierung
                    print("[SYSTEMS] [OK] Connection Health Monitor initialisiert")
                except Exception as e:
                    print(f"[SYSTEMS] [ERROR] Health Monitor Fehler: {e}")
                
                # 3. Enhanced Error Recovery
                try:
                    backup_manager = self.enhanced_system.backup_manager if hasattr(self, 'enhanced_system') else None
                    self.error_recovery = integrate_error_recovery(self, self.serialController, backup_manager)
                    # KEIN LOGGING während der Initialisierung
                    print("[SYSTEMS] [OK] Enhanced Error Recovery initialisiert")
                except Exception as e:
                    print(f"[SYSTEMS] [ERROR] Error Recovery Fehler: {e}")
                
                # 4. Smart ECU Auto-Discovery
                try:
                    self.ecu_discovery, self.discovery_widget = integrate_ecu_auto_discovery(self, self.serialController)
                    # KEIN LOGGING während der Initialisierung
                    print("[SYSTEMS] [OK] Smart ECU Auto-Discovery initialisiert")
                except Exception as e:
                    print(f"[SYSTEMS] [ERROR] ECU Discovery Fehler: {e}")
                
                # 5. Feature Template System
                try:
                    enhanced_system = self.enhanced_system if hasattr(self, 'enhanced_system') else None
                    self.template_manager, self.template_widget = integrate_feature_template_system(self, enhanced_system)
                    # KEIN LOGGING während der Initialisierung
                    print("[SYSTEMS] [OK] Feature Template System initialisiert")
                except Exception as e:
                    print(f"[SYSTEMS] [ERROR] Template System Fehler: {e}")
                
                # Rekursions-Schutz aufheben
                self._system_init_in_progress = False
                
                # JETZT erst loggen, nachdem alles initialisiert ist
                if hasattr(self, 'professional_logger'):
                    try:
                        self.professional_logger.info("SYSTEM", "Professional Systems initialisiert", session_id=self.professional_logger.session_id)
                    except Exception:
                        pass  # Logging-Fehler nicht weiter propagieren
                
                print("[SYSTEMS] Professional Systems erfolgreich initialisiert")
                print("[SYSTEMS] >> Verfügbare Professional Features:")
                print("[SYSTEMS]    * Connection Health Monitoring")
                print("[SYSTEMS]    * Enhanced Error Recovery")
                print("[SYSTEMS]    * Smart ECU Auto-Discovery") 
                print("[SYSTEMS]    * Professional Logging")
                print("[SYSTEMS]    * Feature Template System")
                
                # Keyboard-Shortcuts für Professional Features
                self.setupProfessionalShortcuts()
                
            except Exception as e:
                print(f"[SYSTEMS] Fehler bei Professional Systems Setup: {e}")
                if hasattr(self, 'professional_logger'):
                    self.professional_logger.log_exception("SYSTEM", e, "setupProfessionalSystems")
                import traceback
                traceback.print_exc()
        else:
            print("[SYSTEMS] Professional Systems nicht verfügbar - Module nicht importiert")
    
    def setupProfessionalShortcuts(self):
        """Erstellt Keyboard-Shortcuts für Professional Features"""
        try:
            # Strg+L für Logging System
            try:
                from PySide6.QtGui import QShortcut
            except ImportError:
                from PyQt5.QtWidgets import QShortcut
            
            if hasattr(self, 'logging_widget'):
                self.logging_shortcut = QShortcut("Ctrl+L", self)
                self.logging_shortcut.activated.connect(self.showLoggingSystem)
                print("[SYSTEMS] Keyboard-Shortcut Strg+L für Logging aktiviert")
            
            if hasattr(self, 'health_widget'):
                self.health_shortcut = QShortcut("Ctrl+H", self)
                self.health_shortcut.activated.connect(self.showHealthMonitor)
                print("[SYSTEMS] Keyboard-Shortcut Strg+H für Health Monitor aktiviert")
            
            if hasattr(self, 'discovery_widget'):
                self.discovery_shortcut = QShortcut("Ctrl+D", self)
                self.discovery_shortcut.activated.connect(self.showECUDiscovery)
                print("[SYSTEMS] Keyboard-Shortcut Strg+D für ECU Discovery aktiviert")
            
            if hasattr(self, 'template_widget'):
                self.template_shortcut = QShortcut("Ctrl+T", self)
                self.template_shortcut.activated.connect(self.showTemplateSystem)
                print("[SYSTEMS] Keyboard-Shortcut Strg+T für Templates aktiviert")
                
        except Exception as e:
            print(f"[SYSTEMS] Shortcut-Fehler: {e}")
    
    def showLoggingSystem(self):
        """Zeigt Professional Logging System"""
        if hasattr(self, 'logging_widget'):
            self.logging_widget.setWindowTitle("PyPSADiag - Professional Logging")
            self.logging_widget.show()
            self.logging_widget.raise_()
            self.logging_widget.activateWindow()
    
    def showHealthMonitor(self):
        """Zeigt Connection Health Monitor"""
        if hasattr(self, 'health_widget'):
            self.health_widget.setWindowTitle("PyPSADiag - Connection Health Monitor")
            self.health_widget.show()
            self.health_widget.raise_()
            self.health_widget.activateWindow()
    
    def showECUDiscovery(self):
        """Zeigt Smart ECU Auto-Discovery"""
        if hasattr(self, 'discovery_widget'):
            self.discovery_widget.setWindowTitle("PyPSADiag - Smart ECU Discovery")
            self.discovery_widget.show()
            self.discovery_widget.raise_()
            self.discovery_widget.activateWindow()
    
    def showTemplateSystem(self):
        """Zeigt Feature Template System"""
        if hasattr(self, 'template_widget'):
            self.template_widget.setWindowTitle("PyPSADiag - Feature Templates")
            self.template_widget.show()
            self.template_widget.raise_()
            self.template_widget.activateWindow()
    
    def openEnhancedFeatures(self):
        """Öffnet Enhanced Features Dialog - alias für showEnhancedFeatures"""
        self.showEnhancedFeatures()
    
    def syncEnhancedFeaturesEcuList(self):
        """Synchronisiert ECU-Liste mit Enhanced Features System"""
        if hasattr(self, 'enhanced_system') and self.enhanced_system:
            # Sammle alle verfügbaren ECU-Informationen
            all_ecus = {}
            
            # Einzelne ECU aus ecuObjectList
            if self.ecuObjectList and isinstance(self.ecuObjectList, dict):
                if "name" in self.ecuObjectList:
                    all_ecus[self.ecuObjectList["name"]] = self.ecuObjectList
            
            # Multi-ECU Support: Prüfe ecuComboBox für weitere ECUs
            if hasattr(self.ui, 'ecuComboBox') and self.ui.ecuComboBox:
                combo_count = self.ui.ecuComboBox.count()
                if combo_count > 1:  # Mehr als nur die aktuelle ECU
                    print(f"[ENHANCED] Multi-ECU erkannt: {combo_count} ECUs in ComboBox")
                    for i in range(combo_count):
                        ecu_name = self.ui.ecuComboBox.itemText(i)
                        if ecu_name and ecu_name not in all_ecus:
                            # Erstelle ECU-Entry für alle ComboBox-ECUs
                            all_ecus[ecu_name] = {
                                "name": ecu_name,
                                "tx_id": "auto",  # Wird vom System ermittelt
                                "rx_id": "auto",
                                "protocol": "uds",  # Standard
                                "zones": {},  # Wird beim ersten Zugriff gefüllt
                                "multi_ecu_mode": True
                            }
            
            # Erweiterte ECU-Discovery: Prüfe auf erkannte ECUs über VCI-Scan
            if hasattr(self, 'scan') and self.scan:
                print("[ENHANCED] Scan-Modus aktiv - erweiterte ECU-Erkennung")
                # Hier könnte erweiterte ECU-Discovery implementiert werden
            
            if all_ecus:
                self.enhanced_system.update_ecu_list(all_ecus)
                print(f"[ENHANCED] ECU-Liste synchronisiert: {len(all_ecus)} ECUs")
            else:
                print("[ENHANCED] Keine ECUs für Synchronisation verfügbar")

    def showEnhancedFeatures(self):
        """Zeigt Enhanced Features System"""
        if hasattr(self, 'enhanced_system'):
            try:
                # ECU-Liste vor dem Anzeigen synchronisieren
                self.syncEnhancedFeaturesEcuList()
                
                # Falls als Tab integriert, zum Tab wechseln
                if hasattr(self.ui, 'tabWidget'):
                    for i in range(self.ui.tabWidget.count()):
                        if self.ui.tabWidget.tabText(i).contains("Enhanced Features"):
                            self.ui.tabWidget.setCurrentIndex(i)
                            return
                
                # Falls als eigenständiges Fenster, zeigen
                self.enhanced_system.show()
                self.enhanced_system.raise_()
                self.enhanced_system.activateWindow()
                
            except Exception as e:
                print(f"[ENHANCED] Fehler beim Anzeigen des Enhanced Systems: {e}")
        else:
            print("[ENHANCED] Enhanced System nicht verfügbar")

    def addTranslators(self):
            self.translator = QTranslator()
            self.loadTranslator()
            QApplication.instance().installTranslator(self.translator)

    def changeLanguage(self, index):
            lang_code = self.ui.languageComboBox.itemData(index)
            if lang_code:
                self.lang_code = lang_code

            self.loadTranslator()
            self.ui.translateGUI(self)
            if self.ecuObjectList is not None and not (isinstance(self.ecuObjectList, dict) and len(self.ecuObjectList) == 0):
                self.updateEcuZonesAndKeys(self.ecuObjectList)

    def loadTranslator(self):
            qm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "translations", f"PyPSADiag_{self.lang_code}.qm")
            self.translator.load(qm_path)

    # Update ECU Combobox and Zone Tree view with "new" Zone file
    def updateEcuZonesAndKeys(self, ecuObjectList: dict):
        # Update ECU Zone ComboBox
        self.ui.ecuComboBox.clear()
        name = ecuObjectList["name"]
        self.ui.ecuComboBox.addItem(name)
        if "zones" in ecuObjectList:
            zoneObjectList = ecuObjectList["zones"]
            # Update ECU Key ComboBox
            self.ui.ecuKeyComboBox.clear()
            keyType = ecuObjectList["key_type"]
            if keyType == "single":
                key = str(ecuObjectList["keys"])
                item = name + " - " + key
                self.ui.ecuKeyComboBox.addItem(item, key)
            elif keyType == "multi":
                for keyItem in ecuObjectList["keys"]:
                    key = str(ecuObjectList["keys"][keyItem])
                    item = str(keyItem) + " - " + key
                    self.ui.ecuKeyComboBox.addItem(item, key)
        elif "ecu" in ecuObjectList:
            zoneObjectList = ecuObjectList["ecu"]
        else:
            self.writeToOutputView(i18n().tr("Not correct JSON file"))
            return;

        for zoneObject in zoneObjectList:
            self.ui.ecuComboBox.addItem(str(zoneObject))

        self.ui.treeView.updateView(ecuObjectList)
        
        # Enhanced Features ECU-Liste aktualisieren
        self.syncEnhancedFeaturesEcuList()

    def writeToOutputView(self, text: str):
        self.ui.output.append(str(datetime.now()) + " --|  " + text)
        self.ui.output.viewport().repaint()

    @Slot()
    def searchConnectPort(self):
        self.serialController.fillPortNameCombobox(self.ui.portNameComboBox)

    @Slot()
    def connectPort(self):
        port_name = self.ui.portNameComboBox.currentText()
        success = self.serialController.open(port_name, 115200)
        
        if success:
            # Set button states
            self.ui.ConnectPort.setEnabled(False)
            self.ui.DisconnectPort.setEnabled(True)
            
            # Check if using VCI
            if port_name == "Evolution XS VCI" or self.serialController.use_vci:
                self.writeToOutputView("Connected to Evolution XS VCI")
                # Configure VCI if ECU is already loaded
                if hasattr(self, 'ecuObjectList') and self.ecuObjectList:
                    success = self.serialController.configure_vci(
                        self.ecuObjectList["tx_id"],
                        self.ecuObjectList["rx_id"], 
                        self.ecuObjectList["protocol"]
                    )
                    if success:
                        self.writeToOutputView("VCI configured for ECU communication")
                    else:
                        self.writeToOutputView("VCI configuration failed")
            else:
                # Traditional serial communication - send Reset command
                cmd = "R"
                self.writeToOutputView("> " + cmd)
                receiveData = self.serialController.sendReceive(cmd)
                self.writeToOutputView("< " + receiveData)
        else:
            self.writeToOutputView("Failed to connect to " + port_name)
        
        # Enhanced Features ECU-Liste nach Verbindung synchronisieren
        self.syncEnhancedFeaturesEcuList()

    @Slot()
    def disconnectPort(self):
        if self.stream != None:
            self.stream.close()
        self.serialController.close()
        self.ui.ConnectPort.setEnabled(True)
        self.ui.DisconnectPort.setEnabled(False)
        self.ui.readZone.setEnabled(False)
        self.ui.writeZone.setEnabled(False)
        self.ui.writeZone.setEnabled(False)
        self.ui.clearEcuFaults.setEnabled(False)
        self.ui.readEcuFaults.setEnabled(False)
        self.ui.rebootEcu.setEnabled(False)
#        self.ui.useSketchSeedGenerator.setCheckState(Qt.Unchecked)
#        self.ui.useSketchSeedGenerator.setEnabled(True)

    @Slot()
    def hideNoResponseZones(self, state):
        self.ui.treeView.hideNoResponseZones(state == 2)

    @Slot()
    def sendCommand(self):
        if self.serialController.isOpen():
            cmd = self.ui.command.text()
            self.ui.command.clear()
            self.writeToOutputView(cmd)
            self.receiveData = self.serialController.sendReceive(cmd)
            self.writeToOutputView(self.receiveData)
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))

    @Slot()
    def openCSVFile(self):
        path = os.path.join(os.path.dirname(__file__), "csv")
        fileName = QFileDialog.getOpenFileName(self, i18n().tr("Open CSV Zone File"), path, i18n().tr("CSV Files") + "(*.csv)")
        if fileName[0] == "":
            return

        self.ui.treeView.clearZoneListValues()
        self.ui.setFilePathInWindowsTitle(fileName[0])
        self.fileLoaderThread.enable(fileName[0], 0)

    @Slot()
    def saveCSVFile(self):
        path = os.path.join(os.path.dirname(__file__), "csv")
        fileName = QFileDialog.getSaveFileName(self, i18n().tr("Save CSV Zone File"), path, i18n().tr("CSV Files") + "(*.csv)")
        if fileName[0] == "":
            return

        # Open CSV for writing
        self.ui.setFilePathInWindowsTitle(fileName[0])
        self.stream = open(fileName[0], 'w', newline='')
        self.csvWriter = csv.writer(self.stream)
        if self.stream != None:
            valueList = self.ui.treeView.getValuesAsCSV()
            for tabList in valueList:
                for zone in tabList:
                    self.csvWriter.writerow(zone)
            self.stream.flush()

    @Slot()
    def openZoneFile(self):
        path = os.path.join(os.path.dirname(__file__), "json")
        fileName = QFileDialog.getOpenFileName(self, i18n().tr("Open JSON Zone File"), path, i18n().tr("JSON Files") + "(*.json)")
        if fileName[0] == "":
            return
        file = open(fileName[0], 'r', encoding='utf-8')
        jsonFile = file.read()
        self.ecuObjectList = json.loads(jsonFile.encode("utf-8"))
        # Do we need to include a JSON File and attach it to 'zones'
        if "include_zone_object" in self.ecuObjectList:
            includeZonePath = os.path.join(os.path.dirname(__file__), self.ecuObjectList["include_zone_object"])
            if os.path.exists(includeZonePath):
                includeZoneFile = open(includeZonePath, 'r', encoding='utf-8')
                includeJsonFile = includeZoneFile.read()
                includeObjectList = json.loads(includeJsonFile.encode("utf-8"))
                self.ecuObjectList["zones"].update(includeObjectList)
            else:
                self.writeToOutputView(i18n().tr("Include Zone file not found: ") + includeZonePath)

        self.updateEcuZonesAndKeys(self.ecuObjectList)
        self.ui.setFilePathInWindowsTitle("")
        self.ui.readZone.setEnabled(True)
        self.ui.writeZone.setEnabled(True)
        self.ui.writeZone.setEnabled(True)
        self.ui.clearEcuFaults.setEnabled(True)
        self.ui.readEcuFaults.setEnabled(True)
        self.ui.rebootEcu.setEnabled(True)
        
        # Configure VCI if already connected
        if self.serialController.isOpen() and self.serialController.use_vci:
            success = self.serialController.configure_vci(
                self.ecuObjectList["tx_id"],
                self.ecuObjectList["rx_id"],
                self.ecuObjectList["protocol"]
            )
            if success:
                self.writeToOutputView("VCI configured for ECU: " + self.ecuObjectList["name"])
            else:
                self.writeToOutputView("VCI configuration failed for ECU: " + self.ecuObjectList["name"])

    @Slot()
    def readZone(self):
        if self.serialController.isOpen():
            path = os.path.join(os.path.dirname(__file__), "csv")
            fileName = QFileDialog.getSaveFileName(self, i18n().tr("Save CSV Zone File"), path, i18n().tr("CSV Files") + "(*.csv)")
            if fileName[0] == "":
                return

            # Open CSV for writing
            self.ui.setFilePathInWindowsTitle(fileName[0])
            self.stream = open(fileName[0], 'w', newline='')
            self.csvWriter = csv.writer(self.stream)

            # Setup CAN_EMIT_ID
            ecu = ">" + self.ecuObjectList["tx_id"] + ":" + self.ecuObjectList["rx_id"]

            # Setup LIN_ID if present
            lin = ""
            if "lin_id" in self.ecuObjectList:
                lin = "L" + self.ecuObjectList["lin_id"]

            if self.ecuObjectList["protocol"] == "uds":
                # Read Requested Zone or ALL Zones from ECU
                if self.ui.ecuComboBox.currentIndex() == 0:
                    self.udsCommunication.setZonesToRead(ecu, lin, self.ecuObjectList["zones"])
                else:
                    zone = {}
                    zone[self.ui.ecuComboBox.currentText()] = self.ecuObjectList["zones"][self.ui.ecuComboBox.currentText()];
                    self.udsCommunication.setZonesToRead(ecu, lin, zone)
            elif self.ecuObjectList["protocol"] == "kwp_is":
                # Read Requested Zone or ALL Zones from ECU
                if self.ui.ecuComboBox.currentIndex() == 0:
                    self.kwpisCommunication.setZonesToRead(ecu, lin, self.ecuObjectList["zones"])
                else:
                    zone = {}
                    zone[self.ui.ecuComboBox.currentText()] = self.ecuObjectList["zones"][self.ui.ecuComboBox.currentText()];
                    self.kwpisCommunication.setZonesToRead(ecu, lin, zone)
            elif self.ecuObjectList["protocol"] == "kwp_hab":
                # Read Requested Zone or ALL Zones from ECU
                if self.ui.ecuComboBox.currentIndex() == 0:
                    self.kwphabCommunication.setZonesToRead(ecu, lin, self.ecuObjectList["zones"])
                else:
                    zone = {}
                    zone[self.ui.ecuComboBox.currentText()] = self.ecuObjectList["zones"][self.ui.ecuComboBox.currentText()];
                    self.kwphabCommunication.setZonesToRead(ecu, lin, zone)
            else:
                self.writeToOutputView(i18n().tr("Protocol not supported yet!"))
                return
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))


    @Slot()
    def writeZone(self):
        if self.serialController.isOpen():
            # Setup text of changed zones and put it into MessageBox
            virginWrite = self.ui.virginWriteZone.isChecked()
            self.ui.virginWriteZone.setCheckState(Qt.Unchecked)
            text = ""
            changeCount = 0
            valueList = self.ui.treeView.getZoneListOfHexValue(virginWrite)
            for tabList in valueList:
                for zone in tabList:
                    text += str(zone) + "\r\n"
                    changeCount += 1
            if changeCount == 0:
                self.writeToOutputView(i18n().tr("Nothing changed"))
                return

            # Give some option to check values and to cancel the write
            # SICHERHEIT: Automatisches Backup vor Zone-Schreibung
            backup_created = False
            if hasattr(self, 'enhanced_system') and self.enhanced_system:
                try:
                    ecu_name = self.ecuObjectList.get("name", "Unknown_ECU")
                    snapshot = self.enhanced_system.backup_manager.create_snapshot(
                        name=f"Auto_Backup_before_{ecu_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        description=f"Automatisches Backup vor Zone-Schreibung: {changeCount} Änderungen",
                        backup_type="pre_write",
                        ecu_addresses=[ecu_name]
                    )
                    if snapshot:
                        backup_created = True
                        print(f"[BACKUP] Automatisches Backup erstellt: {snapshot.id}")
                        self.writeToOutputView(f"[SICHERHEIT] Backup erstellt: {snapshot.id}")
                except Exception as e:
                    print(f"[BACKUP] Warnung - Backup fehlgeschlagen: {e}")
                    self.writeToOutputView(f"[WARNUNG] Backup fehlgeschlagen: {e}")

            changedialog = MessageDialog(self, i18n().tr("Write zone(s) to ECU"), i18n().tr("Write"), 
                                       text + (f"\n[SICHERHEIT] Backup erstellt: ✓" if backup_created else "\n[WARNUNG] Kein Backup erstellt!"))
            if MessageDialog.Rejected == changedialog.exec():
                return

            # Get the corresponding ECU Key from Combobox
            index = self.ui.ecuKeyComboBox.currentIndex()
            key = self.ui.ecuKeyComboBox.itemData(index)
            # Setup CAN_EMIT_ID
            ecu = ">" + self.ecuObjectList["tx_id"] + ":" + self.ecuObjectList["rx_id"]

            # Setup LIN_ID if present
            lin = ""
            if "lin_id" in self.ecuObjectList:
                lin = "L" + self.ecuObjectList["lin_id"]

            if self.ecuObjectList["protocol"] == "uds":
#                self.udsCommunication.writeZoneList(self.ui.useSketchSeedGenerator.isChecked(), ecu, lin, key, valueList, self.ui.writeSecureTraceability.isChecked())
                self.udsCommunication.writeZoneList(False, ecu, lin, key, valueList, self.ui.writeSecureTraceability.isChecked())
            elif self.ecuObjectList["protocol"] == "kwp_is":
                self.kwpisCommunication.writeZoneList(False, ecu, lin, key, valueList, self.ui.writeSecureTraceability.isChecked())
            elif self.ecuObjectList["protocol"] == "kwp_hab":
                self.kwphabCommunication.writeZoneList(False, ecu, lin, key, valueList, self.ui.writeSecureTraceability.isChecked())
            else:
                self.writeToOutputView(i18n().tr("Protocol not supported yet!"))
                return
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))


    @Slot()
    def rebootEcu(self):
        if self.serialController.isOpen():
            # Setup CAN_EMIT_ID
            ecu = ">" + self.ecuObjectList["tx_id"] + ":" + self.ecuObjectList["rx_id"]

            if self.ecuObjectList["protocol"] == "uds":
                self.udsCommunication.rebootEcu(ecu)
            elif self.ecuObjectList["protocol"] == "kwp_hab":
                self.kwphabCommunication.rebootEcu(ecu)
            else:
                self.writeToOutputView(i18n().tr("Protocol not supported yet!"))
                return
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))

    @Slot()
    def readEcuFaults(self):
        if self.serialController.isOpen():
            # Setup CAN_EMIT_ID
            ecu = ">" + self.ecuObjectList["tx_id"] + ":" + self.ecuObjectList["rx_id"]

            if self.ecuObjectList["protocol"] == "uds":
                self.udsCommunication.readEcuFaults(ecu)
            else:
                self.writeToOutputView(i18n().tr("Protocol not supported yet!"))
                return
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))

    @Slot()
    def clearEcuFaults(self):
        if self.serialController.isOpen():
            # Setup CAN_EMIT_ID
            ecu = ">" + self.ecuObjectList["tx_id"] + ":" + self.ecuObjectList["rx_id"]

            # Give some option to cancel the Clear Fault Codes
            changedialog = MessageDialog(self, i18n().tr("Clearing Fault Codes of ECU:"), i18n().tr("Ok"), ecu)
            if MessageDialog.Rejected == changedialog.exec():
                return

            if self.ecuObjectList["protocol"] == "uds":
                self.udsCommunication.clearEcuFaults(ecu)
            else:
                self.writeToOutputView(i18n().tr("Protocol not supported yet!"))
                return
        else:
            self.writeToOutputView(i18n().tr("Port not open!"))

    @Slot()
    def csvReadCallback(self, value: list):
        # Did we had an empty line in CSV? Then skip it.
        if len(value) >= 2:
            self.ui.treeView.changeZoneOption(value[0], value[1]);

    @Slot()
    def updateZoneDataback(self, zoneData: str, value: str):
        self.ui.treeView.changeZoneOption(zoneData, value)

    @Slot()
    def outputToTextEditCallback(self, text: str):
        self.writeToOutputView(text)

    @Slot()
    def serialPacketReceiverCallback(self, packet: list, time: float):
        self.writeToOutputView(str(packet))
        if self.stream != None:
            self.csvWriter.writerow(packet)
            self.stream.flush()
    
    def activatePSAREButton(self):
        """Aktiviert PSA-RE Button basierend auf verfügbaren Dependencies"""
        try:
            from PyPSADiagGUI import PSA_RE_AVAILABLE
            
            if hasattr(self.ui, 'psaReSyncButton'):
                # Teste aktuellen Import-Status
                try:
                    from PSA_RE_Integration import create_psa_re_integration
                    current_available = True
                    print("[PSA-RE] Dependencies verfügbar - Button aktiviert")
                except ImportError as e:
                    current_available = False
                    print(f"[PSA-RE] Dependencies fehlen: {e}")
                
                # Aktualisiere Button
                if current_available:
                    self.ui.psaReSyncButton.setText("Community Sync")
                    self.ui.psaReSyncButton.setEnabled(True)
                    self.ui.psaReSyncButton.setToolTip("Synchronisiere Community ECU-Definitionen von PSA-RE Repository")
                else:
                    self.ui.psaReSyncButton.setText("Community Sync (Disabled)")
                    self.ui.psaReSyncButton.setEnabled(False)
                    self.ui.psaReSyncButton.setToolTip("PSA-RE Integration nicht verfügbar - pip install requests pyyaml")
                    
        except Exception as e:
            print(f"[PSA-RE] Button-Aktivierung fehlgeschlagen: {e}")

    def setupProfessionalFeatures(self):
        """Initialize Professional Features Integration"""
        try:
            # Connect Diagbox Integration if available
            if hasattr(self.ui, 'diagboxWidget'):
                self.ui.diagboxWidget.setParent(self)
                
                # Connect Diagbox signals if available
                if hasattr(self.ui.diagboxWidget, 'flash_started'):
                    self.ui.diagboxWidget.flash_started.connect(self.onFlashStarted)
                if hasattr(self.ui.diagboxWidget, 'flash_completed'):
                    self.ui.diagboxWidget.flash_completed.connect(self.onFlashCompleted)
            
            # Connect Enhanced Flash Manager if available
            if hasattr(self.ui, 'flashManagerWidget'):
                self.ui.flashManagerWidget.setParent(self)
                
                # Load Diagbox data into Flash Manager
                if hasattr(self.ui.flashManagerWidget, 'load_diagbox_data'):
                    self.ui.flashManagerWidget.load_diagbox_data()
            
            # Initialize PSA-RE Integration
            self.setupPSAREIntegration()
                
        except Exception:
            pass
    
    def setupPSAREIntegration(self):
        """Initialize PSA-RE Community Integration"""
        try:
            from PyPSADiagGUI import PSA_RE_AVAILABLE
            if PSA_RE_AVAILABLE:
                from PSA_RE_Integration import create_psa_re_integration
                
                # Create PSA-RE integration instance (None parent is OK for QObject)
                self.psaReIntegration = create_psa_re_integration(None)
                
                # Connect signals
                self.psaReIntegration.sync_started.connect(self.onPSARESyncStarted)
                self.psaReIntegration.sync_progress.connect(self.onPSARESyncProgress) 
                self.psaReIntegration.sync_completed.connect(self.onPSARESyncCompleted)
                self.psaReIntegration.definition_loaded.connect(self.onCommunityDefinitionLoaded)
                
                # Check for cached definitions
                status = self.psaReIntegration.get_sync_status()
                if status['cached_definitions'] > 0:
                    self.writeToOutputView(f"PSA-RE: {status['cached_definitions']} Community-Definitionen geladen")
                
                print(f"[PSA-RE] Integration initialisiert - Cache: {status['cached_definitions']} Definitionen")
                
        except Exception as e:
            print(f"[PSA-RE] Setup Fehler: {str(e)}")
            # Don't show error to user at startup - only print for debugging
    
    
    @Slot()
    def onFlashStarted(self, session):
        """Handle Flash Started Signal"""
        self.writeToOutputView(f"🔥 Flash Session gestartet: {session.ecu_name} -> {session.target_version}")
    
    @Slot()  
    def onFlashCompleted(self, session, success):
        """Handle Flash Completed Signal"""
        if success:
            self.writeToOutputView(f"✅ Flash Session abgeschlossen: {session.ecu_name}")
        else:
            self.writeToOutputView(f"❌ Flash Session fehlgeschlagen: {session.ecu_name}")
    
    @Slot()
    def launchSafeQuickSetupWizard(self):
        """Startet den Safe Quick Setup Wizard"""
        try:
            from SafeQuickSetupWizard_Complete import create_safe_quick_setup_wizard
            
            # Erstelle Wizard
            wizard = create_safe_quick_setup_wizard(self)
            if wizard:
                # Setze ECU-Daten falls verfügbar
                if hasattr(self, 'ecuObjectList') and self.ecuObjectList:
                    wizard.detected_vehicle = {
                        'ecu_data': self.ecuObjectList,
                        'serial_controller': self.serialController
                    }
                
                # Zeige Wizard
                result = wizard.exec()
                
                # QDialog.Accepted ist die korrekte Konstante (1)
                if result == 1:  # QDialog.Accepted
                    self.writeToOutputView("Safe Quick Setup Wizard erfolgreich abgeschlossen!")
                else:
                    self.writeToOutputView("Safe Quick Setup Wizard abgebrochen")
            else:
                self.writeToOutputView("Safe Quick Setup Wizard konnte nicht gestartet werden")
                
        except Exception as e:
            self.writeToOutputView(f"Fehler beim Starten des Safe Quick Setup Wizard: {str(e)}")
    
    # PSA-RE Community Integration Methods
    @Slot()
    def showPSARENotAvailable(self):
        """Versucht PSA-RE zu aktivieren oder zeigt Fehlermeldung"""
        self.writeToOutputView("Versuche PSA-RE zu aktivieren...")
        
        # Versuche nochmal die Dependencies zu laden
        try:
            import requests
            import yaml
            from PSA_RE_Integration import create_psa_re_integration
            
            # Dependencies sind verfügbar! Aktiviere Button
            self.writeToOutputView("PSA-RE Dependencies gefunden! Aktiviere Integration...")
            self.ui.psaReSyncButton.setText("Community Sync")
            self.ui.psaReSyncButton.setEnabled(True)
            self.ui.psaReSyncButton.setToolTip("Synchronisiere Community ECU-Definitionen von PSA-RE Repository")
            
            # Verbinde mit echter Sync-Funktion
            self.ui.psaReSyncButton.clicked.disconnect()  # Entferne alte Verbindung
            self.ui.psaReSyncButton.clicked.connect(self.startPSARESync)
            
            self.writeToOutputView("PSA-RE Integration aktiviert! Button ist jetzt funktional.")
            
            # Starte sofort einen Sync
            self.startPSARESync()
            
        except ImportError as e:
            # Dependencies wirklich nicht verfügbar
            try:
                from PySide6.QtWidgets import QMessageBox
            except ImportError:
                try:
                    from qt_compat import QMessageBox
                except ImportError:
                    from PyQt5.QtWidgets import QMessageBox
            
            QMessageBox.information(self, "PSA-RE Integration", 
                                   f"PSA-RE Community Integration ist nicht verfügbar.\n\n" +
                                   f"Fehler: {str(e)}\n\n" +
                                   "Installiere die benötigten Dependencies:\n" +
                                   "pip install requests pyyaml\n\n" +
                                   "Dann starte PyPSADiag neu.")
    
    @Slot()
    def startPSARESync(self):
        """Startet PSA-RE Community-Synchronisation - mit Dependency-Check zur Laufzeit"""
        self.writeToOutputView("=== Community Sync Button geklickt! ===")
        
        try:
            # Versuche Dependencies zu importieren
            self.writeToOutputView("Prüfe PSA-RE Dependencies...")
            
            try:
                import requests
                import yaml
                self.writeToOutputView(f"OK Dependencies gefunden: requests {requests.__version__}")
            except ImportError as dep_error:
                self.writeToOutputView(f"Dependencies fehlen - {dep_error}")
                self.writeToOutputView("Installiere automatisch...")
                
                # Automatische Installation
                import subprocess
                import sys
                
                try:
                    self.writeToOutputView("Führe aus: pip install requests pyyaml")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', 'requests', 'pyyaml'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        self.writeToOutputView("OK Dependencies installiert!")
                        self.writeToOutputView("Versuche erneut...")
                        
                        # Versuche erneut zu importieren
                        import requests
                        import yaml
                        self.writeToOutputView(f"OK Dependencies jetzt verfügbar: requests {requests.__version__}")
                    else:
                        self.writeToOutputView("FEHLER bei Installation:")
                        self.writeToOutputView(result.stderr)
                        return
                        
                except Exception as install_error:
                    self.writeToOutputView(f"Installation fehlgeschlagen: {install_error}")
                    self.writeToOutputView("Installiere manuell: pip install requests pyyaml")
                    return
            
            # Versuche PSA-RE Integration zu importieren
            try:
                from PSA_RE_Integration import create_psa_re_integration
                self.writeToOutputView("OK PSA-RE Integration Modul verfügbar")
            except ImportError as mod_error:
                self.writeToOutputView(f"FEHLER: PSA-RE Modul nicht verfügbar - {mod_error}")
                return
            
            # Erstelle Integration falls nicht vorhanden
            if not hasattr(self, 'psaReIntegration') or not self.psaReIntegration:
                self.writeToOutputView("Erstelle PSA-RE Integration...")
                self.psaReIntegration = create_psa_re_integration(None)
                self.writeToOutputView("OK PSA-RE Integration erstellt")
            
            # Starte Sync
            self.writeToOutputView("=== Starte PSA-RE Community-Sync ===")
            
            # Kurzer Test
            status = self.psaReIntegration.get_sync_status()
            self.writeToOutputView(f"Cache-Status: {status['cached_definitions']} Definitionen")
            
            # Repository-Test
            self.writeToOutputView("Teste Repository-Verbindung...")
            repo_info = self.psaReIntegration._fetch_repository_info()
            if repo_info:
                self.writeToOutputView(f"OK Repository: {repo_info['name']} ({repo_info['stargazers_count']} Stars)")
                
                # Vollständiger Sync
                self.writeToOutputView("Starte vollständige Synchronisation...")
                self.psaReIntegration.sync_community_definitions(force_update=True)
            else:
                self.writeToOutputView("WARNUNG: Repository nicht erreichbar (Offline?)")
                
        except Exception as e:
            self.writeToOutputView(f"=== PSA-RE Sync Fehler ===")
            self.writeToOutputView(f"Fehler: {str(e)}")
            import traceback
            self.writeToOutputView("Stack Trace:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.writeToOutputView(f"  {line}")
    
    @Slot()
    def onPSARESyncStarted(self):
        """PSA-RE Sync gestartet"""
        self.writeToOutputView("PSA-RE: Verbinde mit Community Repository...")
        self.ui.updateStatusBar("PSA-RE Synchronisation läuft...")
    
    @Slot(int, str)
    def onPSARESyncProgress(self, progress, message):
        """PSA-RE Sync Fortschritt"""
        self.writeToOutputView(f"PSA-RE [{progress}%]: {message}")
        
    @Slot(bool, str) 
    def onPSARESyncCompleted(self, success, message):
        """PSA-RE Sync abgeschlossen"""
        if success:
            self.writeToOutputView(f"PSA-RE: {message}")
            self.ui.updateStatusBar("PSA-RE Sync erfolgreich")
            
            # Update available definitions in UI if needed
            self.updateCommunityDefinitionsInUI()
        else:
            self.writeToOutputView(f"PSA-RE Fehler: {message}")
            self.ui.updateStatusBar("PSA-RE Sync fehlgeschlagen")
    
    @Slot(str, dict)
    def onCommunityDefinitionLoaded(self, filename, definition):
        """Community-Definition geladen"""
        self.writeToOutputView(f"Community-Definition geladen: {definition.get('name', filename)}")
    
    def updateCommunityDefinitionsInUI(self):
        """Aktualisiert verfügbare Community-Definitionen in der UI"""
        try:
            if hasattr(self, 'psaReIntegration'):
                definitions = self.psaReIntegration.get_available_community_definitions()
                
                # Zeige verfügbare Community-Definitionen
                if definitions:
                    self.writeToOutputView(f"Verfügbare Community-Definitionen: {len(definitions)}")
                    for definition in definitions[:5]:  # Zeige erste 5
                        arch = definition.get('architecture', 'Unknown')
                        zones = definition.get('zone_count', 0)
                        self.writeToOutputView(f"  - {definition['name']} ({arch}, {zones} Zonen)")
                        
                    # Hier könnte man die Definitionen in die Zone-File Auswahl integrieren
                    
        except Exception as e:
            self.writeToOutputView(f"UI Update Fehler: {str(e)}")
    
    def loadCommunityDefinition(self, filename):
        """Lädt eine Community-Definition als Zone-File"""
        try:
            if hasattr(self, 'psaReIntegration'):
                definition = self.psaReIntegration.load_community_definition(filename)
                if definition:
                    # Konvertiere zu PyPSADiag Format und lade als ECU
                    # Hier würde die Integration in die bestehende Zone-Loading Logik erfolgen
                    self.writeToOutputView(f"Community-Definition geladen: {definition['name']}")
                    return True
        except Exception as e:
            self.writeToOutputView(f"Community-Definition Load Fehler: {str(e)}")
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
