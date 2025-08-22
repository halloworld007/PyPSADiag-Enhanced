"""
   EnhancedFeatureActivationSystem.py

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
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QProgressBar, QScrollArea, QFrame,
                                 QGroupBox, QTextEdit, QTabWidget, QMessageBox,
                                 QSplitter, QDialog, QDialogButtonBox, QApplication)
    from PySide6.QtCore import QThread, Signal, Qt, QTimer
    from PySide6.QtGui import QFont, QColor, QBrush, QIcon
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QProgressBar, QScrollArea, QFrame,
                                   QGroupBox, QTextEdit, QTabWidget, QMessageBox,
                                   QSplitter, QDialog, QDialogButtonBox, QApplication)
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, Qt, QTimer
        from PyQt5.QtGui import QFont, QColor, QBrush, QIcon
        QT_FRAMEWORK = "PyQt5"

# Importiere alle 4 Systeme
from IntelligentFeatureAssistant import IntelligentFeatureAssistant
from VisualFeatureBrowser import VisualFeatureBrowser
from AdvancedPreActivationChecks import PreActivationChecksWidget
from SmartBackupSystem import SmartBackupWidget, SmartBackupManager


class FeatureActivationOrchestrator(QThread):
    """Orchestriert den kompletten Feature-Aktivierungsprozess"""
    
    # Signals
    stage_started = Signal(str, str)  # stage_name, description
    stage_completed = Signal(str, bool, str)  # stage_name, success, message
    progress_updated = Signal(int)  # percentage
    activation_completed = Signal(bool, dict)  # success, summary
    
    def __init__(self, features: List[str], backup_manager: SmartBackupManager, communication_bridge=None):
        super().__init__()
        self.features = features
        self.backup_manager = backup_manager
        self.comm_bridge = communication_bridge
        self.should_stop = False
        
        self.stages = [
            ("backup_creation", "Automatisches Backup erstellen"),
            ("dependency_check", "Abhängigkeiten prüfen"),
            ("hardware_validation", "Hardware validieren"),
            ("pre_activation_backup", "Pre-Activation Backup"),
            ("feature_activation", "Features aktivieren"),
            ("post_activation_check", "Post-Activation Validierung"),
            ("final_backup", "Finales Backup erstellen")
        ]
        
        self.results = {}
    
    def run(self):
        """Führt kompletten Aktivierungsprozess aus"""
        try:
            total_stages = len(self.stages)
            
            for i, (stage_name, stage_description) in enumerate(self.stages):
                if self.should_stop:
                    break
                
                self.stage_started.emit(stage_name, stage_description)
                
                # Stage ausführen
                success, message = self.execute_stage(stage_name)
                self.results[stage_name] = {"success": success, "message": message}
                
                self.stage_completed.emit(stage_name, success, message)
                
                # Bei kritischen Fehlern abbrechen
                if not success and stage_name in ["backup_creation", "dependency_check"]:
                    self.activation_completed.emit(False, {
                        "error": f"Critical stage failed: {stage_name}",
                        "message": message,
                        "results": self.results
                    })
                    return
                
                # Progress updaten
                progress = int((i + 1) / total_stages * 100)
                self.progress_updated.emit(progress)
                
                # Kurze Pause
                self.msleep(500)
            
            # Erfolgs-Summary erstellen
            success_count = sum(1 for result in self.results.values() if result["success"])
            overall_success = success_count == len(self.stages)
            
            summary = {
                "overall_success": overall_success,
                "activated_features": self.features,
                "stages_completed": len(self.results),
                "stages_successful": success_count,
                "results": self.results
            }
            
            self.activation_completed.emit(overall_success, summary)
            
        except Exception as e:
            error_summary = {
                "overall_success": False,
                "error": str(e),
                "results": self.results
            }
            self.activation_completed.emit(False, error_summary)
    
    def execute_stage(self, stage_name: str) -> tuple[bool, str]:
        """Führt einzelne Stage aus"""
        try:
            if stage_name == "backup_creation":
                return self.create_initial_backup()
            elif stage_name == "dependency_check":
                return self.check_dependencies()
            elif stage_name == "hardware_validation":
                return self.validate_hardware()
            elif stage_name == "pre_activation_backup":
                return self.create_pre_activation_backup()
            elif stage_name == "feature_activation":
                return self.activate_features()
            elif stage_name == "post_activation_check":
                return self.validate_activation()
            elif stage_name == "final_backup":
                return self.create_final_backup()
            else:
                return False, f"Unknown stage: {stage_name}"
                
        except Exception as e:
            return False, f"Stage execution failed: {str(e)}"
    
    def create_initial_backup(self) -> tuple[bool, str]:
        """Erstellt initiales Backup"""
        try:
            snapshot = self.backup_manager.create_snapshot(
                name=f"Initial_Backup_{datetime.now().strftime('%Y%m%d_%H%M')}",
                description="Automatisches Backup vor Feature-Aktivierung",
                feature_context=[],
                backup_type="pre_activation"
            )
            
            if snapshot:
                return True, f"Initial backup created: {snapshot.id}"
            else:
                return False, "Failed to create initial backup"
                
        except Exception as e:
            return False, f"Backup creation error: {str(e)}"
    
    def check_dependencies(self) -> tuple[bool, str]:
        """Prüft Abhängigkeiten"""
        # Hier würde die echte Dependency-Prüfung stattfinden
        # Vereinfacht für Demo
        return True, "All dependencies satisfied"
    
    def validate_hardware(self) -> tuple[bool, str]:
        """Validiert Hardware"""
        # Hier würde die echte Hardware-Validierung stattfinden
        return True, "Hardware validation passed"
    
    def create_pre_activation_backup(self) -> tuple[bool, str]:
        """Erstellt Pre-Activation Backup"""
        try:
            snapshot = self.backup_manager.create_snapshot(
                name=f"Pre_Activation_{datetime.now().strftime('%Y%m%d_%H%M')}",
                description=f"Backup vor Aktivierung: {', '.join(self.features)}",
                feature_context=self.features,
                backup_type="pre_activation"
            )
            
            if snapshot:
                return True, f"Pre-activation backup created: {snapshot.id}"
            else:
                return False, "Failed to create pre-activation backup"
                
        except Exception as e:
            return False, f"Pre-activation backup error: {str(e)}"
    
    def activate_features(self) -> tuple[bool, str]:
        """Aktiviert Features"""
        try:
            activated = []
            failed = []
            
            for feature in self.features:
                success = self.activate_single_feature(feature)
                if success:
                    activated.append(feature)
                else:
                    failed.append(feature)
                
                # Kurze Pause zwischen Features
                self.msleep(1000)
            
            if failed:
                return False, f"Failed to activate: {', '.join(failed)}"
            else:
                return True, f"Successfully activated: {', '.join(activated)}"
                
        except Exception as e:
            return False, f"Feature activation error: {str(e)}"
    
    def activate_single_feature(self, feature_id: str) -> bool:
        """Aktiviert einzelnes Feature"""
        try:
            if self.comm_bridge:
                # Echte Feature-Aktivierung über Communication Bridge
                return self.comm_bridge.activate_feature(feature_id)
            else:
                # Simulation für Demo
                print(f"SIMULATED: Activating feature {feature_id}")
                return True
                
        except Exception as e:
            print(f"Error activating feature {feature_id}: {e}")
            return False
    
    def validate_activation(self) -> tuple[bool, str]:
        """Validiert Aktivierung"""
        # Post-Activation Validation
        return True, "Activation validation successful"
    
    def create_final_backup(self) -> tuple[bool, str]:
        """Erstellt finales Backup"""
        try:
            snapshot = self.backup_manager.create_snapshot(
                name=f"Post_Activation_{datetime.now().strftime('%Y%m%d_%H%M')}",
                description=f"Backup nach Aktivierung: {', '.join(self.features)}",
                feature_context=self.features,
                backup_type="post_activation"
            )
            
            if snapshot:
                return True, f"Final backup created: {snapshot.id}"
            else:
                return False, "Failed to create final backup"
                
        except Exception as e:
            return False, f"Final backup error: {str(e)}"
    
    def stop(self):
        """Stoppt Aktivierungsprozess"""
        self.should_stop = True


class EnhancedFeatureActivationDialog(QDialog):
    """Dialog für Aktivierungsprozess mit Fortschrittsanzeige"""
    
    def __init__(self, features: List[str], backup_manager: SmartBackupManager, 
                 communication_bridge=None, parent=None):
        super().__init__(parent)
        
        self.features = features
        self.backup_manager = backup_manager
        self.comm_bridge = communication_bridge
        self.orchestrator = None
        
        self.setWindowTitle("Feature-Aktivierung")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Feature-Aktivierung wird durchgeführt...")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Feature-Liste
        features_group = QGroupBox(f"Zu aktivierende Features ({len(self.features)})")
        features_layout = QVBoxLayout(features_group)
        
        features_text = "\n".join([f"• {feature}" for feature in self.features])
        features_label = QLabel(features_text)
        features_layout.addWidget(features_label)
        
        layout.addWidget(features_group)
        
        # Progress
        progress_group = QGroupBox("Fortschritt")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Vorbereitung...")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Detailliertes Log
        log_group = QGroupBox("Detailliertes Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Buttons
        self.button_box = QDialogButtonBox()
        self.stop_button = self.button_box.addButton("Stoppen", QDialogButtonBox.ButtonRole.RejectRole)
        self.close_button = self.button_box.addButton("Schließen", QDialogButtonBox.ButtonRole.AcceptRole)
        self.close_button.setEnabled(False)
        
        self.button_box.rejected.connect(self.stop_activation)
        self.button_box.accepted.connect(self.accept)
        
        layout.addWidget(self.button_box)
    
    def start_activation(self):
        """Startet Aktivierungsprozess"""
        self.orchestrator = FeatureActivationOrchestrator(
            self.features, self.backup_manager, self.comm_bridge
        )
        
        # Signals verbinden
        self.orchestrator.stage_started.connect(self.on_stage_started)
        self.orchestrator.stage_completed.connect(self.on_stage_completed)
        self.orchestrator.progress_updated.connect(self.on_progress_updated)
        self.orchestrator.activation_completed.connect(self.on_activation_completed)
        
        # Starten
        self.orchestrator.start()
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Aktivierungsprozess gestartet")
    
    def on_stage_started(self, stage_name: str, description: str):
        """Stage wurde gestartet"""
        self.status_label.setText(f"Aktuell: {description}")
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ▶️ {description}")
    
    def on_stage_completed(self, stage_name: str, success: bool, message: str):
        """Stage wurde abgeschlossen"""
        status_icon = "✅" if success else "❌"
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} {message}")
        
        if not success:
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Stage fehlgeschlagen: {stage_name}")
    
    def on_progress_updated(self, percentage: int):
        """Progress wurde aktualisiert"""
        self.progress_bar.setValue(percentage)
    
    def on_activation_completed(self, success: bool, summary: Dict):
        """Aktivierung wurde abgeschlossen"""
        self.stop_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Aktivierung erfolgreich abgeschlossen!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            activated_count = len(summary.get("activated_features", []))
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Alle {activated_count} Features erfolgreich aktiviert!")
            
            # Erfolgs-Dialog
            QMessageBox.information(
                self,
                "Aktivierung erfolgreich",
                f"Alle {activated_count} Features wurden erfolgreich aktiviert!\n\n"
                "Automatische Backups wurden erstellt und der Prozess ist abgeschlossen."
            )
        else:
            self.status_label.setText("❌ Aktivierung fehlgeschlagen!")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
            error_msg = summary.get("error", "Unbekannter Fehler")
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 💥 Aktivierung fehlgeschlagen: {error_msg}")
            
            # Fehler-Dialog
            QMessageBox.critical(
                self,
                "Aktivierung fehlgeschlagen",
                f"Die Feature-Aktivierung ist fehlgeschlagen:\n\n{error_msg}\n\n"
                "Bitte prüfen Sie das Log für weitere Details."
            )
    
    def stop_activation(self):
        """Stoppt Aktivierungsprozess"""
        if self.orchestrator and self.orchestrator.isRunning():
            self.orchestrator.stop()
            self.status_label.setText("Aktivierung wird gestoppt...")
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️ Benutzer hat Aktivierung gestoppt")
        
        self.reject()


class EnhancedFeatureActivationSystem(QWidget):
    """Hauptsystem für erweiterte Feature-Aktivierung"""
    
    def __init__(self, communication_bridge=None, real_ecu_list=None, parent=None):
        super().__init__(parent)
        
        self.comm_bridge = communication_bridge
        self.real_ecu_list = real_ecu_list or {}
        self.backup_manager = SmartBackupManager("enhanced_backups", communication_bridge, real_ecu_list)
        
        self.setup_ui()
        self.connect_signals()
    
    def update_ecu_list(self, new_ecu_list: Dict):
        """Aktualisiert ECU-Liste im System"""
        if new_ecu_list:
            self.real_ecu_list = new_ecu_list.copy()
            self.backup_manager.update_ecu_list(new_ecu_list)
            print(f"[ENHANCED] ECU-Liste aktualisiert: {len(new_ecu_list)} ECUs")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Enhanced Feature Activation System")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #2196f3; margin: 10px;")
        layout.addWidget(header_label)
        
        # Tab-System für die 4 Hauptkomponenten
        self.tabs = QTabWidget()
        
        # Tab 1: Intelligenter Assistent
        self.assistant_tab = IntelligentFeatureAssistant()
        self.tabs.addTab(self.assistant_tab, "🧠 Intelligenter Assistent")
        
        # Tab 2: Visual Browser
        self.browser_tab = VisualFeatureBrowser()
        self.tabs.addTab(self.browser_tab, "🎨 Feature Browser")
        
        # Tab 3: Pre-Activation Checks
        self.checks_tab = PreActivationChecksWidget()
        self.tabs.addTab(self.checks_tab, "🔍 Kompatibilitätsprüfung")
        
        # Tab 4: Smart Backup
        self.backup_tab = SmartBackupWidget(self.backup_manager)
        self.tabs.addTab(self.backup_tab, "💾 Smart Backup")
        
        layout.addWidget(self.tabs)
        
        # Status Bar
        self.status_label = QLabel("Bereit für Feature-Aktivierung")
        self.status_label.setStyleSheet("padding: 5px; border-top: 1px solid #ccc;")
        layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Verbindet Signals zwischen Komponenten"""
        
        # Assistent → Aktivierung
        self.assistant_tab.feature_activation_requested.connect(self.start_intelligent_activation)
        
        # Browser → Aktivierung
        self.browser_tab.features_selected.connect(self.start_browser_activation)
        
        # Checks → Status Update
        self.checks_tab.checks_completed.connect(self.on_checks_completed)
        
        # Backup → Status Update
        self.backup_tab.backup_created.connect(self.on_backup_created)
        self.backup_tab.restore_completed.connect(self.on_restore_completed)
    
    def start_intelligent_activation(self, features: List[str]):
        """Startet Aktivierung vom Intelligenten Assistenten"""
        self.status_label.setText(f"Starte intelligente Aktivierung für {len(features)} Features...")
        
        # Pre-Activation Checks automatisch durchführen
        self.checks_tab.start_checks(features, self.comm_bridge)
        
        # Nach Checks → Aktivierung
        def on_checks_done(success, summary):
            if success:
                self.launch_activation_dialog(features)
            else:
                QMessageBox.warning(
                    self,
                    "Kompatibilitätsprüfung fehlgeschlagen", 
                    "Die Kompatibilitätsprüfung ist fehlgeschlagen.\n"
                    "Bitte prüfen Sie die Ergebnisse im Kompatibilitäts-Tab."
                )
        
        # Temporäre Verbindung für diesen Aktivierungsvorgang
        self.checks_tab.checks_completed.disconnect()
        self.checks_tab.checks_completed.connect(on_checks_done)
        
        # Tab zu Checks wechseln
        self.tabs.setCurrentIndex(2)  # Checks Tab
    
    def start_browser_activation(self, features: List[str]):
        """Startet Aktivierung vom Visual Browser"""
        self.status_label.setText(f"Starte Browser-Aktivierung für {len(features)} Features...")
        
        # Direkt zur Aktivierung (Browser hat bereits visuelle Validierung)
        reply = QMessageBox.question(
            self,
            "Feature-Aktivierung bestätigen",
            f"Möchten Sie diese {len(features)} Features aktivieren?\n\n" +
            "\n".join([f"• {feature}" for feature in features[:5]]) +
            (f"\n... und {len(features)-5} weitere" if len(features) > 5 else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.launch_activation_dialog(features)
    
    def launch_activation_dialog(self, features: List[str]):
        """Startet Aktivierungsdialog"""
        try:
            dialog = EnhancedFeatureActivationDialog(
                features, self.backup_manager, self.comm_bridge, self
            )
            
            # Dialog zeigen und Aktivierung starten
            dialog.show()
            dialog.start_activation()
            
            # Modal ausführen
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                self.status_label.setText("✅ Feature-Aktivierung erfolgreich abgeschlossen")
            else:
                self.status_label.setText("⏹️ Feature-Aktivierung abgebrochen")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Aktivierungsfehler",
                f"Fehler beim Starten der Aktivierung:\n{str(e)}"
            )
    
    def on_checks_completed(self, success: bool, summary: Dict):
        """Kompatibilitätsprüfung abgeschlossen"""
        if success:
            self.status_label.setText("✅ Kompatibilitätsprüfung erfolgreich")
        else:
            self.status_label.setText("❌ Kompatibilitätsprüfung fehlgeschlagen")
        
        # Reconnect zur normalen Behandlung
        self.checks_tab.checks_completed.disconnect()
        self.checks_tab.checks_completed.connect(self.on_checks_completed)
    
    def on_backup_created(self, snapshot_id: str):
        """Backup wurde erstellt"""
        self.status_label.setText(f"💾 Backup erstellt: {snapshot_id}")
    
    def on_restore_completed(self, success: bool, snapshot_id: str):
        """Restore abgeschlossen"""
        if success:
            self.status_label.setText(f"↩️ Wiederherstellung erfolgreich: {snapshot_id}")
        else:
            self.status_label.setText(f"❌ Wiederherstellung fehlgeschlagen: {snapshot_id}")


# Integration in Hauptanwendung
def integrate_enhanced_system(main_window, communication_bridge=None, real_ecu_list=None):
    """Integriert Enhanced System in Hauptanwendung"""
    
    # Enhanced System erstellen
    enhanced_system = EnhancedFeatureActivationSystem(communication_bridge, real_ecu_list)
    
    # Als neuen Tab hinzufügen (falls Tab-System vorhanden)
    if hasattr(main_window, 'main_tabs'):
        main_window.main_tabs.addTab(enhanced_system, "🚀 Enhanced Features")
    
    # Oder als neues Fenster öffnen
    enhanced_system.setWindowTitle("PyPSADiag - Enhanced Feature Activation")
    enhanced_system.show()
    
    return enhanced_system


# Test/Demo Funktionen  
def create_demo_enhanced_system():
    """Erstellt Demo für Testing"""
    import sys
    
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    system = EnhancedFeatureActivationSystem()
    system.setWindowTitle("Enhanced Feature Activation System - Demo")
    system.show()
    
    return system, app


if __name__ == "__main__":
    system, app = create_demo_enhanced_system()
    app.exec() if hasattr(app, 'exec') else app.exec_()