#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSA_RE_Integration.py

🔄 PSA-RE Community Integration für PyPSADiag Enhanced
- Integration mit prototux/PSA-RE Repository
- YAML ECU-Definitions Support
- Community-Datenbank Synchronisation
- Erweiterte Architektur-Erkennung (AEE2010/AEE2004)
- Collaborative Reverse Engineering Support

Repository: https://github.com/prototux/PSA-RE
"""

# Qt Framework Kompatibilität
try:
    from PySide6.QtCore import QObject, Signal, QThread, QTimer
    from PySide6.QtWidgets import QMessageBox, QProgressDialog
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal, QThread, QTimer
        from PyQt5.QtWidgets import QMessageBox, QProgressDialog
        QT_FRAMEWORK = "PyQt5"

import json
import os
import requests
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Optional imports
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

class PSAArchitecture:
    """PSA Fahrzeug-Architektur Definition"""
    
    def __init__(self, name: str, description: str, years: str, protocols: List[str]):
        self.name = name
        self.description = description
        self.years = years
        self.protocols = protocols
        self.supported_ecus = []
        self.diagnostic_features = []
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'years': self.years,
            'protocols': self.protocols,
            'supported_ecus': self.supported_ecus,
            'diagnostic_features': self.diagnostic_features
        }


class PSAREDefinition:
    """PSA-RE Community-Definition"""
    
    def __init__(self, filename: str, content: Dict):
        self.filename = filename
        self.content = content
        self.architecture = content.get('architecture', 'Unknown')
        self.vehicle_models = content.get('vehicles', [])
        self.ecu_definitions = content.get('ecus', {})
        self.diagnostic_services = content.get('diagnostics', {})
        self.last_updated = datetime.now()
        
    def to_pypsa_format(self) -> Dict:
        """Konvertiert PSA-RE Format zu PyPSADiag JSON Format"""
        pypsa_format = {
            'name': self.filename.replace('.yaml', '').replace('_', ' ').title(),
            'description': f"Community-Definition aus PSA-RE ({self.architecture})",
            'protocol': self._extract_protocol(),
            'architecture': self.architecture,
            'vehicles': self.vehicle_models,
            'zones': self._convert_zones(),
            'diagnostic_services': self.diagnostic_services,
            'source': 'PSA-RE Community',
            'last_updated': self.last_updated.isoformat()
        }
        return pypsa_format
    
    def _extract_protocol(self) -> str:
        """Extrahiert Hauptprotokoll aus Definition"""
        if 'UDS' in str(self.content).upper():
            return 'UDS'
        elif 'KWP' in str(self.content).upper():
            return 'KWP2000'
        else:
            return 'UDS'  # Default
    
    def _convert_zones(self) -> List[Dict]:
        """Konvertiert ECU-Definitionen zu PyPSADiag Zonen"""
        zones = []
        
        for ecu_name, ecu_data in self.ecu_definitions.items():
            if isinstance(ecu_data, dict):
                zone = {
                    'zone': ecu_name,
                    'description': ecu_data.get('description', f'{ecu_name} ECU'),
                    'address': ecu_data.get('address', '0x00'),
                    'parameters': self._extract_parameters(ecu_data)
                }
                zones.append(zone)
        
        return zones
    
    def _extract_parameters(self, ecu_data: Dict) -> List[Dict]:
        """Extrahiert Parameter aus ECU-Daten"""
        parameters = []
        
        # Versuche verschiedene Formate zu parsen
        if 'parameters' in ecu_data:
            for param_name, param_data in ecu_data['parameters'].items():
                param = {
                    'name': param_name,
                    'address': param_data.get('address', '0x00'),
                    'size': param_data.get('size', 1),
                    'description': param_data.get('description', param_name)
                }
                parameters.append(param)
        
        return parameters


class PSAREIntegration(QObject):
    """🔄 Haupt-Integration Klasse für PSA-RE Community"""
    
    # Signals
    sync_started = Signal()
    sync_progress = Signal(int, str)  # progress, message
    sync_completed = Signal(bool, str)  # success, message
    definition_loaded = Signal(str, dict)  # filename, definition
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # PSA-RE Repository URLs
        self.github_api_url = "https://api.github.com/repos/prototux/PSA-RE"
        self.raw_content_url = "https://raw.githubusercontent.com/prototux/PSA-RE/main"
        
        # Lokale Verzeichnisse
        self.psa_re_cache_dir = os.path.join(os.getcwd(), "psa_re_cache")
        self.community_definitions_dir = os.path.join(os.getcwd(), "community_definitions")
        
        # Erstelle Verzeichnisse
        os.makedirs(self.psa_re_cache_dir, exist_ok=True)
        os.makedirs(self.community_definitions_dir, exist_ok=True)
        
        # PSA Architektur-Definitionen
        self.psa_architectures = self._initialize_psa_architectures()
        
        # Cache
        self.cached_definitions = {}
        self.last_sync = None
        
        # Load cached data
        self._load_cached_data()
    
    def _initialize_psa_architectures(self) -> Dict[str, PSAArchitecture]:
        """Initialisiert bekannte PSA-Architekturen"""
        architectures = {}
        
        # AEE2010 (2010-2020 Fahrzeuge) - Haupt-Zielgruppe
        aee2010 = PSAArchitecture(
            "AEE2010",
            "Moderne PSA Architektur mit FullCAN",
            "2010-2020",
            ["UDS", "KWP2000", "CAN"]
        )
        aee2010.supported_ecus = ["BSI", "EMF", "CIROCCO", "NAC", "COMBINE", "ABS", "CLIMATE"]
        aee2010.diagnostic_features = ["UDS_Extended", "Seed_Key_Auth", "Flash_Reprog", "Multi_ECU"]
        architectures["AEE2010"] = aee2010
        
        # AEE2004 (2004-2010 Fahrzeuge)
        aee2004 = PSAArchitecture(
            "AEE2004", 
            "Ältere PSA Architektur mit FullCAN",
            "2004-2010",
            ["KWP2000", "CAN"]
        )
        aee2004.supported_ecus = ["BSI", "EMF", "ABS", "CLIMATE"]
        aee2004.diagnostic_features = ["KWP2000", "Basic_Diag"]
        architectures["AEE2004"] = aee2004
        
        # AEE2001 (Legacy VAN)
        aee2001 = PSAArchitecture(
            "AEE2001",
            "Legacy PSA Architektur mit VAN Bus", 
            "2001-2008",
            ["VAN", "KWP"]
        )
        aee2001.supported_ecus = ["BSI", "ABS"]
        aee2001.diagnostic_features = ["VAN_Diag", "Basic_KWP"]
        architectures["AEE2001"] = aee2001
        
        return architectures
    
    def sync_community_definitions(self, force_update: bool = False) -> bool:
        """Synchronisiert Community-Definitionen von PSA-RE"""
        
        # Prüfe ob Update nötig
        if not force_update and self.last_sync:
            time_diff = datetime.now() - self.last_sync
            if time_diff < timedelta(hours=24):  # Nur alle 24h aktualisieren
                return True
        
        try:
            self.sync_started.emit()
            self.sync_progress.emit(10, "Verbinde mit PSA-RE Repository...")
            
            # Hole Repository-Informationen
            repo_info = self._fetch_repository_info()
            if not repo_info:
                self.sync_completed.emit(False, "Repository nicht erreichbar")
                return False
            
            self.sync_progress.emit(25, "Analysiere verfügbare Definitionen...")
            
            # Hole Dateiliste
            yaml_files = self._get_yaml_files_list()
            if not yaml_files:
                self.sync_completed.emit(False, "Keine YAML-Definitionen gefunden")
                return False
            
            self.sync_progress.emit(50, f"Lade {len(yaml_files)} Definitionen...")
            
            # Lade YAML-Dateien
            loaded_count = 0
            for i, yaml_file in enumerate(yaml_files[:10]):  # Limitiert auf 10 für Performance
                progress = 50 + int((i / min(len(yaml_files), 10)) * 40)
                self.sync_progress.emit(progress, f"Lade {yaml_file}...")
                
                if self._download_yaml_definition(yaml_file):
                    loaded_count += 1
            
            self.sync_progress.emit(95, "Konvertiere zu PyPSADiag Format...")
            
            # Konvertiere Definitionen
            converted_count = self._convert_definitions_to_pypsa()
            
            self.sync_progress.emit(100, f"Sync abgeschlossen: {loaded_count} geladen, {converted_count} konvertiert")
            
            # Update timestamp
            self.last_sync = datetime.now()
            self._save_sync_metadata()
            
            self.sync_completed.emit(True, f"Erfolgreich {converted_count} Community-Definitionen synchronisiert")
            return True
            
        except Exception as e:
            self.sync_completed.emit(False, f"Sync-Fehler: {str(e)}")
            return False
    
    def _fetch_repository_info(self) -> Optional[Dict]:
        """Holt Repository-Informationen von GitHub API"""
        try:
            response = requests.get(f"{self.github_api_url}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Repository-Info Fehler: {e}")
        return None
    
    def _get_yaml_files_list(self) -> List[str]:
        """Holt Liste der YAML-Dateien vom Repository"""
        try:
            # Versuche contents API
            response = requests.get(f"{self.github_api_url}/contents", timeout=10)
            if response.status_code == 200:
                contents = response.json()
                yaml_files = []
                for item in contents:
                    if item['name'].endswith('.yaml') or item['name'].endswith('.yml'):
                        yaml_files.append(item['name'])
                return yaml_files
        except Exception as e:
            print(f"YAML-Liste Fehler: {e}")
        
        # Fallback: Bekannte Dateien
        return ['bsi.yaml', 'emf.yaml', 'nav.yaml', 'climate.yaml']
    
    def _download_yaml_definition(self, filename: str) -> bool:
        """Lädt eine YAML-Definition herunter"""
        try:
            url = f"{self.raw_content_url}/{filename}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Speichere in Cache
                cache_file = os.path.join(self.psa_re_cache_dir, filename)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return True
                
        except Exception as e:
            print(f"Download-Fehler {filename}: {e}")
        
        return False
    
    def _convert_definitions_to_pypsa(self) -> int:
        """Konvertiert PSA-RE YAML zu PyPSADiag JSON Format"""
        converted_count = 0
        
        try:
            for filename in os.listdir(self.psa_re_cache_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    yaml_file = os.path.join(self.psa_re_cache_dir, filename)
                    
                    try:
                        # Lade YAML
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            yaml_content = yaml.safe_load(f)
                        
                        if yaml_content:
                            # Erstelle PSA-RE Definition
                            psa_re_def = PSAREDefinition(filename, yaml_content)
                            
                            # Konvertiere zu PyPSADiag Format
                            pypsa_format = psa_re_def.to_pypsa_format()
                            
                            # Speichere als JSON
                            json_filename = filename.replace('.yaml', '').replace('.yml', '') + '_community.json'
                            json_file = os.path.join(self.community_definitions_dir, json_filename)
                            
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(pypsa_format, f, indent=2, ensure_ascii=False)
                            
                            # Cache in Memory
                            self.cached_definitions[json_filename] = pypsa_format
                            
                            # Signal
                            self.definition_loaded.emit(json_filename, pypsa_format)
                            
                            converted_count += 1
                            
                    except Exception as e:
                        print(f"Konvertierungs-Fehler {filename}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Konvertierungs-Fehler allgemein: {e}")
        
        return converted_count
    
    def _load_cached_data(self):
        """Lädt gecachte Definitionen"""
        try:
            # Lade Sync-Metadaten
            metadata_file = os.path.join(self.psa_re_cache_dir, 'sync_metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    if 'last_sync' in metadata:
                        self.last_sync = datetime.fromisoformat(metadata['last_sync'])
            
            # Lade Community-Definitionen
            if os.path.exists(self.community_definitions_dir):
                for filename in os.listdir(self.community_definitions_dir):
                    if filename.endswith('_community.json'):
                        json_file = os.path.join(self.community_definitions_dir, filename)
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                definition = json.load(f)
                                self.cached_definitions[filename] = definition
                        except Exception as e:
                            print(f"Cache-Load-Fehler {filename}: {e}")
                            
        except Exception as e:
            print(f"Cache-Load-Fehler: {e}")
    
    def _save_sync_metadata(self):
        """Speichert Sync-Metadaten"""
        try:
            metadata = {
                'last_sync': self.last_sync.isoformat() if self.last_sync else None,
                'definition_count': len(self.cached_definitions),
                'architectures': [arch.name for arch in self.psa_architectures.values()]
            }
            
            metadata_file = os.path.join(self.psa_re_cache_dir, 'sync_metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Metadaten-Speicher-Fehler: {e}")
    
    def get_available_community_definitions(self) -> List[Dict]:
        """Gibt verfügbare Community-Definitionen zurück"""
        definitions = []
        
        for filename, definition in self.cached_definitions.items():
            info = {
                'filename': filename,
                'name': definition.get('name', filename),
                'description': definition.get('description', ''),
                'architecture': definition.get('architecture', 'Unknown'),
                'vehicles': definition.get('vehicles', []),
                'protocol': definition.get('protocol', 'UDS'),
                'zone_count': len(definition.get('zones', [])),
                'source': 'PSA-RE Community'
            }
            definitions.append(info)
        
        return definitions
    
    def get_architecture_info(self, architecture_name: str) -> Optional[PSAArchitecture]:
        """Gibt Architektur-Informationen zurück"""
        return self.psa_architectures.get(architecture_name)
    
    def detect_vehicle_architecture(self, vehicle_info: Dict) -> Optional[str]:
        """Erkennt Fahrzeug-Architektur basierend auf Fahrzeug-Info"""
        try:
            vehicle_year = vehicle_info.get('year', 0)
            vehicle_model = vehicle_info.get('model', '').lower()
            
            # Jahr-basierte Erkennung
            if isinstance(vehicle_year, str):
                try:
                    vehicle_year = int(vehicle_year)
                except ValueError:
                    vehicle_year = 2015  # Default
            
            if vehicle_year >= 2010:
                return "AEE2010"
            elif vehicle_year >= 2004:
                return "AEE2004" 
            elif vehicle_year >= 2001:
                return "AEE2001"
            else:
                return "AEE2010"  # Default für moderne Fahrzeuge
                
        except Exception:
            return "AEE2010"  # Safe default
    
    def load_community_definition(self, filename: str) -> Optional[Dict]:
        """Lädt spezifische Community-Definition"""
        if filename in self.cached_definitions:
            return self.cached_definitions[filename]
        
        # Versuche von Disk zu laden
        json_file = os.path.join(self.community_definitions_dir, filename)
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    definition = json.load(f)
                    self.cached_definitions[filename] = definition
                    return definition
            except Exception as e:
                print(f"Lade-Fehler {filename}: {e}")
        
        return None
    
    def get_sync_status(self) -> Dict:
        """Gibt aktuellen Sync-Status zurück"""
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'cached_definitions': len(self.cached_definitions),
            'architectures': list(self.psa_architectures.keys()),
            'cache_dir': self.psa_re_cache_dir,
            'community_dir': self.community_definitions_dir,
            'sync_needed': not self.last_sync or (datetime.now() - self.last_sync) > timedelta(hours=24)
        }


# Factory Functions
def create_psa_re_integration(parent=None) -> PSAREIntegration:
    """Factory-Funktion für PSA-RE Integration"""
    return PSAREIntegration(parent)

def get_supported_architectures() -> List[str]:
    """Gibt unterstützte PSA-Architekturen zurück"""
    return ["AEE2010", "AEE2004", "AEE2001"]


# Test-Funktion
if __name__ == "__main__":
    print("PSA-RE Integration - Test")
    print("=" * 40)
    
    integration = PSAREIntegration()
    
    print("Verfügbare Architekturen:")
    for arch_name, arch in integration.psa_architectures.items():
        print(f"  {arch_name}: {arch.description} ({arch.years})")
    
    print(f"\nSync-Status: {integration.get_sync_status()}")
    
    print(f"\nCommunity-Definitionen: {len(integration.get_available_community_definitions())}")
    
    # Test Architektur-Erkennung
    test_vehicle = {"year": 2019, "model": "Corsa F"}
    detected_arch = integration.detect_vehicle_architecture(test_vehicle)
    print(f"\nTest Fahrzeug {test_vehicle} -> Architektur: {detected_arch}")