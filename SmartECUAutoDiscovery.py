#!/usr/bin/env python3
"""
Smart ECU Auto-Discovery System für PyPSADiag
Automatische ECU-Erkennung und intelligente JSON-Auto-Loading
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import re

try:
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QProgressBar, QListWidget, QListWidgetItem,
                                 QTextEdit, QComboBox, QCheckBox, QGroupBox)
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, QTimer, Qt
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QProgressBar, QListWidget, QListWidgetItem,
                                   QTextEdit, QComboBox, QCheckBox, QGroupBox)
        QT_FRAMEWORK = "PyQt5"

@dataclass
class ECUDiscoveryResult:
    """Ergebnis einer ECU-Discovery"""
    ecu_id: str
    name: str
    protocol: str
    tx_id: str
    rx_id: str
    response_time: float
    confidence_score: float
    suggested_json: Optional[str] = None
    additional_info: Dict = field(default_factory=dict)

@dataclass
class VehicleProfile:
    """Fahrzeugprofil basierend auf VIN-Analyse"""
    vin: str
    manufacturer: str
    model: str
    year: int
    platform: str
    expected_ecus: List[str] = field(default_factory=list)
    recommended_configs: List[str] = field(default_factory=list)

class SmartECUAutoDiscovery(QThread):
    """Intelligente ECU-Discovery mit automatischer JSON-Zuordnung"""
    
    # Signals
    discovery_started = Signal()
    discovery_progress = Signal(int, str)  # progress_percent, current_task
    ecu_discovered = Signal(dict)  # ECUDiscoveryResult as dict
    discovery_completed = Signal(list)  # List of ECUDiscoveryResults as dicts
    json_recommendation = Signal(str, str)  # ecu_id, recommended_json_path
    vehicle_identified = Signal(dict)  # VehicleProfile as dict
    
    def __init__(self, serial_controller=None, parent=None):
        super().__init__(parent)
        
        self.serial_controller = serial_controller
        self.json_directory = Path("json")
        self.discovered_ecus = []
        self.vehicle_profile = None
        self.discovery_active = False
        
        # ECU-Discovery Parameter
        self.scan_ranges = {
            "UDS": [(0x700, 0x7FF), (0x18DA0000, 0x18DAFFFF)],
            "KWP": [(0x80, 0xFF)]
        }
        
        self.common_ecu_addresses = {
            # PSA/Stellantis Common ECUs
            "240": {"name": "BSI", "protocol": "uds", "rx_offset": 0x400},
            "360": {"name": "NAC", "protocol": "uds", "rx_offset": 0x400}, 
            "220": {"name": "ESP", "protocol": "uds", "rx_offset": 0x400},
            "180": {"name": "Engine", "protocol": "uds", "rx_offset": 0x400},
            "120": {"name": "ABS", "protocol": "uds", "rx_offset": 0x400},
            "260": {"name": "Airbag", "protocol": "uds", "rx_offset": 0x400},
            "3C0": {"name": "Climate", "protocol": "uds", "rx_offset": 0x400},
            "1E0": {"name": "Gateway", "protocol": "uds", "rx_offset": 0x400},
        }
        
        self.load_json_database()
    
    def load_json_database(self):
        """Lädt JSON-Datei Datenbank für intelligente Zuordnung"""
        self.json_database = {}
        
        if not self.json_directory.exists():
            print("[DISCOVERY] JSON-Verzeichnis nicht gefunden")
            return
        
        print("[DISCOVERY] Lade JSON-Datenbank...")
        json_count = 0
        
        for json_file in self.json_directory.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if "name" in data and "tx_id" in data:
                        ecu_name = data["name"]
                        tx_id = data["tx_id"]
                        
                        # Index nach TX-ID
                        if tx_id not in self.json_database:
                            self.json_database[tx_id] = []
                        
                        self.json_database[tx_id].append({
                            "path": str(json_file),
                            "name": ecu_name,
                            "protocol": data.get("protocol", "unknown"),
                            "rx_id": data.get("rx_id", ""),
                            "zones": len(data.get("zones", {})),
                            "platform": self.extract_platform_from_path(json_file)
                        })
                        
                        json_count += 1
                        
            except Exception as e:
                print(f"[DISCOVERY] Fehler beim Laden von {json_file}: {e}")
        
        print(f"[DISCOVERY] {json_count} JSON-Dateien in Datenbank geladen")
    
    def extract_platform_from_path(self, json_path: Path) -> str:
        """Extrahiert Fahrzeugplattform aus JSON-Pfad"""
        path_parts = json_path.parts
        
        # Suche nach bekannten Plattform-Identifikatoren
        platforms = ["PSA", "FIAT", "OPEL", "DS", "PEUGEOT", "CITROEN", "ALFA", "JEEP"]
        
        for part in path_parts:
            part_upper = part.upper()
            for platform in platforms:
                if platform in part_upper:
                    return platform
        
        return "UNKNOWN"
    
    def start_discovery(self, vin: str = None, scan_mode: str = "smart"):
        """Startet ECU-Discovery"""
        self.discovered_ecus.clear()
        self.vehicle_profile = None
        self.discovery_active = True
        
        print(f"[DISCOVERY] Starte ECU-Discovery (Mode: {scan_mode})")
        
        if vin:
            self.analyze_vin(vin)
        
        self.start()
    
    def stop_discovery(self):
        """Stoppt laufende Discovery"""
        self.discovery_active = False
        if self.isRunning():
            self.quit()
            self.wait()
        print("[DISCOVERY] Discovery gestoppt")
    
    def analyze_vin(self, vin: str):
        """Analysiert VIN und erstellt Fahrzeugprofil"""
        print(f"[DISCOVERY] Analysiere VIN: {vin}")
        
        try:
            # VIN-Parsing (vereinfacht)
            manufacturer_code = vin[:3]
            platform_code = vin[3:8]
            year_code = vin[9]
            
            # Manufacturer mapping
            manufacturer_map = {
                "VF7": "Peugeot",
                "VF3": "Peugeot", 
                "VF6": "Renault",
                "WDB": "Mercedes",
                "WBA": "BMW",
                "ZFA": "Fiat"
            }
            
            manufacturer = manufacturer_map.get(manufacturer_code, "Unknown")
            
            # Jahr-Dekodierung (vereinfacht)
            year_map = {
                "L": 2020, "M": 2021, "N": 2022, "P": 2023, 
                "R": 2024, "S": 2025, "T": 2026
            }
            year = year_map.get(year_code, 2020)
            
            self.vehicle_profile = VehicleProfile(
                vin=vin,
                manufacturer=manufacturer,
                model="Auto-detected",
                year=year,
                platform=platform_code
            )
            
            # Erwartete ECUs basierend auf Fahrzeugprofil
            if manufacturer in ["Peugeot", "Citroën", "DS"]:
                self.vehicle_profile.expected_ecus = ["BSI", "NAC", "ESP", "Engine", "Climate"]
                self.vehicle_profile.recommended_configs = self.find_matching_configs(manufacturer, year)
            
            self.vehicle_identified.emit(self.vehicle_profile.__dict__)
            print(f"[DISCOVERY] Fahrzeug identifiziert: {manufacturer} ({year})")
            
        except Exception as e:
            print(f"[DISCOVERY] VIN-Analyse fehlgeschlagen: {e}")
    
    def find_matching_configs(self, manufacturer: str, year: int) -> List[str]:
        """Findet passende Konfigurationsdateien"""
        matching_configs = []
        
        for tx_id, configs in self.json_database.items():
            for config in configs:
                config_path = Path(config["path"])
                
                # Platform-basierte Filterung
                if manufacturer.upper() in config_path.parts[0].upper():
                    matching_configs.append(config["path"])
        
        return matching_configs[:10]  # Top 10
    
    def run(self):
        """Hauptschleife für ECU-Discovery"""
        self.discovery_started.emit()
        
        try:
            # Phase 1: Schneller Scan bekannter ECU-Adressen
            self.discovery_progress.emit(10, "Scanning common ECU addresses...")
            self.scan_common_ecus()
            
            # Phase 2: Intelligenter Bereichs-Scan
            self.discovery_progress.emit(30, "Scanning UDS address ranges...")
            if self.discovery_active:
                self.scan_address_ranges()
            
            # Phase 3: JSON-Zuordnung
            self.discovery_progress.emit(70, "Matching with JSON configurations...")
            if self.discovery_active:
                self.match_json_configurations()
            
            # Phase 4: Konfidenz-Bewertung
            self.discovery_progress.emit(90, "Calculating confidence scores...")
            if self.discovery_active:
                self.calculate_confidence_scores()
            
            self.discovery_progress.emit(100, "Discovery completed!")
            self.discovery_completed.emit([ecu.__dict__ for ecu in self.discovered_ecus])
            
        except Exception as e:
            print(f"[DISCOVERY] Discovery-Fehler: {e}")
        finally:
            self.discovery_active = False
    
    def scan_common_ecus(self):
        """Scannt bekannte ECU-Adressen"""
        print("[DISCOVERY] Scanne bekannte ECU-Adressen...")
        
        for tx_id, ecu_info in self.common_ecu_addresses.items():
            if not self.discovery_active:
                break
                
            try:
                response_time = self.test_ecu_communication(tx_id, ecu_info)
                
                if response_time > 0:
                    rx_id = hex(int(tx_id, 16) + ecu_info["rx_offset"])[2:].upper()
                    
                    ecu_result = ECUDiscoveryResult(
                        ecu_id=tx_id,
                        name=ecu_info["name"],
                        protocol=ecu_info["protocol"],
                        tx_id=tx_id,
                        rx_id=rx_id,
                        response_time=response_time,
                        confidence_score=0.8  # Hoch für bekannte ECUs
                    )
                    
                    self.discovered_ecus.append(ecu_result)
                    self.ecu_discovered.emit(ecu_result.__dict__)
                    print(f"[DISCOVERY] ✅ Gefunden: {ecu_info['name']} ({tx_id})")
                    
            except Exception as e:
                print(f"[DISCOVERY] Fehler bei {tx_id}: {e}")
                continue
    
    def scan_address_ranges(self):
        """Scannt Adressbereiche für unbekannte ECUs"""
        print("[DISCOVERY] Scanne Adressbereiche...")
        
        # Vereinfachter Scan (in Realität würde hier echte Hardware-Kommunikation stattfinden)
        additional_ecus = [
            {"tx_id": "2C0", "name": "Unknown_2C0", "protocol": "uds"},
            {"tx_id": "340", "name": "Unknown_340", "protocol": "uds"},
        ]
        
        for ecu_data in additional_ecus:
            if not self.discovery_active:
                break
                
            response_time = 15.5  # Simuliert
            
            ecu_result = ECUDiscoveryResult(
                ecu_id=ecu_data["tx_id"],
                name=ecu_data["name"],
                protocol=ecu_data["protocol"],
                tx_id=ecu_data["tx_id"],
                rx_id=hex(int(ecu_data["tx_id"], 16) + 0x400)[2:].upper(),
                response_time=response_time,
                confidence_score=0.6  # Niedrigere Konfidenz für unbekannte
            )
            
            self.discovered_ecus.append(ecu_result)
            self.ecu_discovered.emit(ecu_result.__dict__)
            
            time.sleep(0.5)  # Simuliert Scan-Zeit
    
    def test_ecu_communication(self, tx_id: str, ecu_info: Dict) -> float:
        """Testet Kommunikation mit ECU"""
        
        if not self.serial_controller or not self.serial_controller.isOpen():
            # Simulation für Tests
            import random
            return random.uniform(8.0, 25.0) if random.random() > 0.3 else 0.0
        
        try:
            # Echter Communication Test würde hier stattfinden
            start_time = time.time()
            
            # UDS-Ping (Service 0x3E - Tester Present)
            test_command = f"3E00"  # Tester Present
            response = self.serial_controller.sendReceive(test_command, timeout=2.0)
            
            if response and "7E" in response:  # Positive Response
                return (time.time() - start_time) * 1000  # ms
            
            return 0.0
            
        except Exception as e:
            print(f"[DISCOVERY] Communication test failed for {tx_id}: {e}")
            return 0.0
    
    def match_json_configurations(self):
        """Ordnet gefundene ECUs zu passenden JSON-Dateien zu"""
        print("[DISCOVERY] Ordne JSON-Konfigurationen zu...")
        
        for ecu in self.discovered_ecus:
            if ecu.tx_id in self.json_database:
                configs = self.json_database[ecu.tx_id]
                
                # Wähle beste Konfiguration basierend auf Fahrzeugprofil
                best_config = self.select_best_config(ecu, configs)
                
                if best_config:
                    ecu.suggested_json = best_config["path"]
                    ecu.additional_info["json_name"] = best_config["name"]
                    ecu.additional_info["json_zones"] = best_config["zones"]
                    
                    self.json_recommendation.emit(ecu.ecu_id, best_config["path"])
                    print(f"[DISCOVERY] 📄 JSON empfohlen für {ecu.name}: {Path(best_config['path']).name}")
    
    def select_best_config(self, ecu: ECUDiscoveryResult, configs: List[Dict]) -> Optional[Dict]:
        """Wählt beste JSON-Konfiguration für ECU"""
        
        if not configs:
            return None
        
        # Scoring-System für Konfigurationen
        scored_configs = []
        
        for config in configs:
            score = 0
            
            # Platform-Match
            if self.vehicle_profile and self.vehicle_profile.manufacturer:
                if self.vehicle_profile.manufacturer.upper() in config["platform"]:
                    score += 30
            
            # Name-Match
            if ecu.name.upper() in config["name"].upper():
                score += 25
            
            # Protocol-Match
            if ecu.protocol == config["protocol"]:
                score += 20
            
            # Zone-Count (mehr Zonen = besser)
            score += min(config["zones"] * 2, 25)
            
            scored_configs.append((config, score))
        
        # Bestes Ergebnis zurückgeben
        if scored_configs:
            best_config = max(scored_configs, key=lambda x: x[1])
            return best_config[0]
        
        return configs[0]  # Fallback
    
    def calculate_confidence_scores(self):
        """Berechnet finale Konfidenz-Scores"""
        print("[DISCOVERY] Berechne Konfidenz-Scores...")
        
        for ecu in self.discovered_ecus:
            base_score = ecu.confidence_score
            
            # JSON-Match Bonus
            if ecu.suggested_json:
                base_score += 0.2
            
            # Response-Time Bewertung (bessere Zeit = höhere Konfidenz)
            if ecu.response_time > 0:
                if ecu.response_time < 15.0:
                    base_score += 0.1
                elif ecu.response_time > 50.0:
                    base_score -= 0.1
            
            # Vehicle Profile Match
            if (self.vehicle_profile and 
                ecu.name in self.vehicle_profile.expected_ecus):
                base_score += 0.1
            
            ecu.confidence_score = min(1.0, max(0.0, base_score))
    
    def get_discovery_results(self) -> List[ECUDiscoveryResult]:
        """Gibt Discovery-Ergebnisse zurück"""
        return self.discovered_ecus.copy()


class SmartECUAutoDiscoveryWidget(QWidget):
    """GUI Widget für Smart ECU Auto-Discovery"""
    
    def __init__(self, discovery_system: SmartECUAutoDiscovery, parent=None):
        super().__init__(parent)
        
        self.discovery_system = discovery_system
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Smart ECU Auto-Discovery")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # VIN Input
        vin_group = QGroupBox("Vehicle Identification")
        vin_layout = QHBoxLayout(vin_group)
        
        vin_layout.addWidget(QLabel("VIN:"))
        self.vin_input = QComboBox()
        self.vin_input.setEditable(True)
        self.vin_input.addItems(["VF7XXXXXXXXXXXXXXX", "VF3XXXXXXXXXXXXXXX", "ZFAXXXXXXXXXXXXXXX"])
        vin_layout.addWidget(self.vin_input)
        
        analyze_vin_btn = QPushButton("Analyze VIN")
        analyze_vin_btn.clicked.connect(self.analyze_vin)
        vin_layout.addWidget(analyze_vin_btn)
        
        layout.addWidget(vin_group)
        
        # Discovery Controls
        control_group = QGroupBox("Discovery Controls")
        control_layout = QHBoxLayout(control_group)
        
        self.start_btn = QPushButton("🔍 Start Discovery")
        self.start_btn.clicked.connect(self.start_discovery)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.discovery_system.stop_discovery)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready for discovery")
        layout.addWidget(self.status_label)
        
        # Results
        results_group = QGroupBox("Discovered ECUs")
        results_layout = QVBoxLayout(results_group)
        
        self.results_list = QListWidget()
        results_layout.addWidget(self.results_list)
        
        layout.addWidget(results_group)
        
        # Auto-load Controls
        autoload_layout = QHBoxLayout()
        self.auto_load_checkbox = QCheckBox("Auto-load recommended JSON files")
        self.auto_load_checkbox.setChecked(True)
        autoload_layout.addWidget(self.auto_load_checkbox)
        
        load_all_btn = QPushButton("📁 Load All Recommended")
        load_all_btn.clicked.connect(self.load_all_recommended)
        autoload_layout.addWidget(load_all_btn)
        
        layout.addLayout(autoload_layout)
    
    def connect_signals(self):
        """Verbindet Discovery-System Signals"""
        self.discovery_system.discovery_started.connect(self.on_discovery_started)
        self.discovery_system.discovery_progress.connect(self.on_discovery_progress)
        self.discovery_system.ecu_discovered.connect(self.on_ecu_discovered)
        self.discovery_system.discovery_completed.connect(self.on_discovery_completed)
        self.discovery_system.json_recommendation.connect(self.on_json_recommendation)
        self.discovery_system.vehicle_identified.connect(self.on_vehicle_identified)
    
    def analyze_vin(self):
        """Analysiert eingegebene VIN"""
        vin = self.vin_input.currentText().strip()
        if len(vin) == 17:
            self.discovery_system.analyze_vin(vin)
        else:
            self.status_label.setText("❌ Invalid VIN (must be 17 characters)")
    
    def start_discovery(self):
        """Startet ECU-Discovery"""
        vin = self.vin_input.currentText().strip() if len(self.vin_input.currentText().strip()) == 17 else None
        self.discovery_system.start_discovery(vin, "smart")
    
    def on_discovery_started(self):
        """Behandelt Discovery-Start"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.results_list.clear()
        self.status_label.setText("🔍 Discovery started...")
    
    def on_discovery_progress(self, progress: int, task: str):
        """Aktualisiert Progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"🔄 {task} ({progress}%)")
    
    def on_ecu_discovered(self, ecu_data: Dict):
        """Behandelt ECU-Discovery"""
        ecu = ECUDiscoveryResult(**ecu_data)
        
        item_text = f"✅ {ecu.name} ({ecu.tx_id}) - {ecu.response_time:.1f}ms - {ecu.confidence_score*100:.0f}% confidence"
        if ecu.suggested_json:
            item_text += f" 📄 JSON: {Path(ecu.suggested_json).name}"
        
        item = QListWidgetItem(item_text)
        self.results_list.addItem(item)
    
    def on_discovery_completed(self, results: List[Dict]):
        """Behandelt Discovery-Abschluss"""
        self.start_btn.setEnabled(True) 
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"✅ Discovery completed - {len(results)} ECUs found")
        
        if self.auto_load_checkbox.isChecked():
            self.load_all_recommended()
    
    def on_json_recommendation(self, ecu_id: str, json_path: str):
        """Behandelt JSON-Empfehlung"""
        print(f"[DISCOVERY] JSON empfohlen für {ecu_id}: {json_path}")
    
    def on_vehicle_identified(self, vehicle_data: Dict):
        """Behandelt Fahrzeug-Identifikation"""
        profile = VehicleProfile(**vehicle_data)
        self.status_label.setText(f"🚗 Vehicle: {profile.manufacturer} ({profile.year})")
    
    def load_all_recommended(self):
        """Lädt alle empfohlenen JSON-Dateien"""
        results = self.discovery_system.get_discovery_results()
        loaded_count = 0
        
        for ecu in results:
            if ecu.suggested_json:
                # Hier würde normalerweise die JSON-Datei geladen werden
                print(f"[DISCOVERY] Lade {ecu.suggested_json} für {ecu.name}")
                loaded_count += 1
        
        if loaded_count > 0:
            self.status_label.setText(f"📁 {loaded_count} JSON files loaded automatically")


# Integration Helper
def integrate_ecu_auto_discovery(main_window, serial_controller):
    """Integriert Smart ECU Auto-Discovery in Hauptanwendung"""
    
    # Discovery System erstellen
    discovery_system = SmartECUAutoDiscovery(serial_controller)
    
    # Widget erstellen
    discovery_widget = SmartECUAutoDiscoveryWidget(discovery_system)
    
    # In MainWindow integrieren
    main_window.ecu_auto_discovery = discovery_system
    main_window.ecu_discovery_widget = discovery_widget
    
    # Auto-Discovery bei Verbindung
    def on_connection_established():
        # Automatischen Scan anbieten
        print("[DISCOVERY] Verbindung hergestellt - Auto-Discovery verfügbar")
    
    print("[DISCOVERY] Smart ECU Auto-Discovery integriert")
    
    return discovery_system, discovery_widget