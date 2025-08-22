"""
HardwareCompatibilityChecker.py

🔒 HARDWARE COMPATIBILITY & SICHERHEITS-VALIDATOR für PyPSADiag
- Überprüft Hardware-Kompatibilität vor Feature-Aktivierung
- Validiert VCI/Serial Connection Status
- Erkennt unterstützte ECU-Typen automatisch
- Verhindert unsichere Operationen auf inkompatiblen Systemen
"""

# Qt Framework Kompatibilität
try:
    from PySide6.QtCore import QObject, Signal
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal
        QT_FRAMEWORK = "PyQt5"
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class HardwareCompatibilityResult:
    """Ergebnis einer Hardware-Kompatibilitätsprüfung"""
    
    def __init__(self, compatible: bool, ecu_type: str = "", issues: List[str] = None, warnings: List[str] = None):
        self.compatible = compatible
        self.ecu_type = ecu_type
        self.issues = issues or []
        self.warnings = warnings or []
        self.timestamp = None
        
    def is_safe_for_features(self, features: List[str]) -> bool:
        """Prüft ob Hardware sicher für spezifische Features ist"""
        if not self.compatible:
            return False
            
        # Zusätzliche Feature-spezifische Checks
        risky_features = ["advanced_coding", "flash_update", "ecu_reset"]
        for feature in features:
            if feature in risky_features and self.warnings:
                return False
                
        return True


class HardwareComponent:
    """Hardware-Komponente Definition"""
    
    def __init__(self, component_id, name, ecu_location, detection_method):
        self.component_id = component_id
        self.name = name
        self.ecu_location = ecu_location  # Welches ECU diese Hardware verwaltet
        self.detection_method = detection_method  # Wie wird die Hardware erkannt
        self.required_parameters = []  # Welche Parameter müssen gelesen werden
        self.validation_checks = []  # Zusätzliche Validierungen
        self.alternative_components = []  # Alternative Hardware für gleiche Funktion


class HardwareValidationResult:
    """Ergebnis einer Hardware-Validierung"""
    
    def __init__(self, component_id, is_available, detection_details=None):
        self.component_id = component_id
        self.is_available = is_available
        self.detection_details = detection_details or {}
        self.confidence_level = 0.0  # 0.0-1.0
        self.limitations = []  # Bekannte Einschränkungen
        self.alternative_available = False


class HardwareCompatibilityChecker(QObject):
    """🔒 Hardware Compatibility & Security Checker"""
    
    # Signals
    compatibility_checked = Signal(HardwareCompatibilityResult)
    hardware_detected = Signal(str, dict)  # hardware_type, details
    hardwareDetected = Signal(dict)  # Legacy compatibility
    validationProgress = Signal(int)
    validationMessage = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Supported Hardware Database
        self.supported_hardware = {
            "Evolution XS VCI": {
                "protocols": ["UDS", "KWP2000", "CAN", "LIN"],
                "max_baudrate": 500000,
                "safety_level": "professional",
                "auto_backup": True,
                "multi_ecu": True
            },
            "Arduino CAN": {
                "protocols": ["UDS", "CAN"],
                "max_baudrate": 115200,
                "safety_level": "basic",
                "auto_backup": False,
                "multi_ecu": False
            },
            "OBD2 Generic": {
                "protocols": ["UDS"],
                "max_baudrate": 38400,
                "safety_level": "minimal",
                "auto_backup": False,
                "multi_ecu": False
            }
        }
        
        # Compatible ECU Database - NUR SICHERE, VERIFIZIERTE ECUs
        self.compatible_ecus = {
            "BSI": {
                "models": ["208 II", "2008 II", "308 III", "C4 III", "Corsa F"],
                "years": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
                "safe_features": [
                    "auto_door_lock", "welcome_light", "follow_me_home", 
                    "comfort_blinker", "drl_config", "service_reset"
                ],
                "protocols": ["UDS"],
                "backup_required": True
            },
            "EMF": {
                "models": ["208 II", "2008 II", "308 III", "C4 III", "Corsa F"],
                "years": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
                "safe_features": [
                    "auto_light", "tunnel_light", "speed_warning"
                ],
                "protocols": ["UDS"],
                "backup_required": True
            },
            "CIROCCO": {
                "models": ["308 III", "C4 III"],
                "years": ["2021", "2022", "2023", "2024", "2025"],
                "safe_features": [
                    "welcome_light", "follow_me_home", "comfort_blinker"
                ],
                "protocols": ["UDS"],
                "backup_required": True
            }
        }
        
        self.last_check_result = None
        
        # Legacy components for backward compatibility
        self.hardware_components = {}
        self.feature_hardware_requirements = {}
        self.detected_hardware = {}
        
        self.initialize_hardware_database()
        self.initialize_feature_requirements()
    
    def check_hardware_compatibility(self, serial_controller, ecu_data: dict = None) -> HardwareCompatibilityResult:
        """Führt vollständige Hardware-Kompatibilitätsprüfung durch"""
        issues = []
        warnings = []
        ecu_type = ""
        
        try:
            # 1. Prüfe Verbindungsstatus
            if not serial_controller or not serial_controller.isOpen():
                issues.append("❌ Keine aktive Verbindung zum Diagnose-Interface")
                return HardwareCompatibilityResult(False, "", issues, warnings)
            
            # 2. Erkenne Hardware-Typ
            hardware_type = self._detect_hardware_type(serial_controller)
            if not hardware_type:
                issues.append("❌ Unbekannter Hardware-Typ")
                return HardwareCompatibilityResult(False, "", issues, warnings)
            
            # 3. Prüfe Hardware-Support
            if hardware_type not in self.supported_hardware:
                issues.append(f"❌ Hardware '{hardware_type}' nicht unterstützt")
                return HardwareCompatibilityResult(False, "", issues, warnings)
            
            hardware_info = self.supported_hardware[hardware_type]
            
            # 4. Prüfe ECU-Kompatibilität (falls ECU-Daten verfügbar)
            if ecu_data:
                ecu_check = self._check_ecu_compatibility(ecu_data, hardware_info)
                if not ecu_check["compatible"]:
                    issues.extend(ecu_check["issues"])
                else:
                    ecu_type = ecu_check["ecu_type"]
                    warnings.extend(ecu_check["warnings"])
            
            # 5. Sicherheitslevel-Prüfung
            safety_level = hardware_info["safety_level"]
            if safety_level == "minimal":
                warnings.append("⚠️ Minimales Sicherheitslevel - nur Basis-Features empfohlen")
            elif safety_level == "basic":
                warnings.append("⚠️ Basis-Sicherheitslevel - automatisches Backup nicht verfügbar")
                
            # 6. Multi-ECU Support
            if not hardware_info.get("multi_ecu", False):
                warnings.append("⚠️ Multi-ECU Operationen nicht unterstützt")
                
            # Ergebnis erstellen
            compatible = len(issues) == 0
            result = HardwareCompatibilityResult(compatible, ecu_type, issues, warnings)
            
            self.last_check_result = result
            self.compatibility_checked.emit(result)
            
            return result
            
        except Exception as e:
            issues.append(f"❌ Fehler bei Hardware-Check: {str(e)}")
            return HardwareCompatibilityResult(False, "", issues, warnings)
    
    def _detect_hardware_type(self, serial_controller) -> Optional[str]:
        """Erkennt Hardware-Typ basierend auf Verbindung"""
        try:
            # VCI Detection
            if hasattr(serial_controller, 'use_vci') and serial_controller.use_vci:
                return "Evolution XS VCI"
            
            # Serial Arduino Detection
            port_name = getattr(serial_controller, 'portName', '')
            if 'COM' in port_name or 'Arduino' in port_name:
                return "Arduino CAN"
            
            # Fallback für unbekannte serielle Verbindungen
            if serial_controller.isOpen():
                return "OBD2 Generic"
                
            return None
            
        except Exception:
            return None
    
    def _check_ecu_compatibility(self, ecu_data: dict, hardware_info: dict) -> Dict:
        """Prüft ECU-spezifische Kompatibilität"""
        result = {
            "compatible": False,
            "ecu_type": "",
            "issues": [],
            "warnings": []
        }
        
        try:
            # ECU Name/Type extrahieren
            ecu_name = ecu_data.get("name", "")
            protocol = ecu_data.get("protocol", "")
            
            # Finde passenden ECU-Typ
            detected_ecu_type = None
            for ecu_type, ecu_info in self.compatible_ecus.items():
                if ecu_type.lower() in ecu_name.lower():
                    detected_ecu_type = ecu_type
                    break
            
            if not detected_ecu_type:
                result["issues"].append(f"❌ ECU-Typ '{ecu_name}' nicht in Kompatibilitäts-Datenbank")
                return result
            
            ecu_info = self.compatible_ecus[detected_ecu_type]
            result["ecu_type"] = detected_ecu_type
            
            # Prüfe Protokoll-Support
            if protocol.upper() not in hardware_info["protocols"]:
                result["issues"].append(f"❌ Protokoll '{protocol}' nicht von Hardware unterstützt")
                return result
            
            if protocol.upper() not in ecu_info["protocols"]:
                result["issues"].append(f"❌ Protokoll '{protocol}' nicht für ECU-Typ '{detected_ecu_type}' freigegeben")
                return result
            
            # Prüfe Backup-Anforderungen
            if ecu_info.get("backup_required", False) and not hardware_info.get("auto_backup", False):
                result["warnings"].append(f"⚠️ ECU '{detected_ecu_type}' erfordert automatisches Backup")
            
            result["compatible"] = True
            return result
            
        except Exception as e:
            result["issues"].append(f"❌ Fehler bei ECU-Kompatibilitätsprüfung: {str(e)}")
            return result
    
    def get_safe_features_for_ecu(self, ecu_type: str) -> List[str]:
        """Gibt sichere Features für einen ECU-Typ zurück"""
        if ecu_type in self.compatible_ecus:
            return self.compatible_ecus[ecu_type]["safe_features"].copy()
        return []
    
    def is_feature_safe(self, feature_id: str, ecu_type: str, hardware_type: str) -> bool:
        """Prüft ob ein Feature für die Kombination aus ECU und Hardware sicher ist"""
        try:
            # ECU-Level Check
            if ecu_type not in self.compatible_ecus:
                return False
                
            safe_features = self.compatible_ecus[ecu_type]["safe_features"]
            if feature_id not in safe_features:
                return False
            
            # Hardware-Level Check
            if hardware_type not in self.supported_hardware:
                return False
                
            hardware_info = self.supported_hardware[hardware_type]
            safety_level = hardware_info["safety_level"]
            
            # Bestimmte Features nur für professionelle Hardware
            professional_only = ["flash_update", "advanced_coding"]
            if feature_id in professional_only and safety_level != "professional":
                return False
                
            return True
            
        except Exception:
            return False
    
    def get_compatibility_report(self) -> str:
        """Erstellt einen detaillierten Kompatibilitätsbericht"""
        if not self.last_check_result:
            return "❓ Keine Kompatibilitätsprüfung durchgeführt"
        
        result = self.last_check_result
        report = []
        
        # Hauptstatus
        if result.compatible:
            report.append("✅ Hardware-Kompatibilität: OK")
        else:
            report.append("❌ Hardware-Kompatibilität: FEHLGESCHLAGEN")
        
        # ECU Info
        if result.ecu_type:
            report.append(f"🔧 Erkannter ECU-Typ: {result.ecu_type}")
        
        # Issues
        if result.issues:
            report.append("\n❌ Probleme:")
            for issue in result.issues:
                report.append(f"  • {issue}")
        
        # Warnings
        if result.warnings:
            report.append("\n⚠️ Warnungen:")
            for warning in result.warnings:
                report.append(f"  • {warning}")
        
        return "\n".join(report)
    
    def initialize_hardware_database(self):
        """Initialisiere Hardware-Komponenten-Datenbank"""
        
        # Lichtsensoren
        light_sensor = HardwareComponent(
            'light_sensor', 'Lichtsensor (Automatisches Licht)',
            'BSI', 'parameter_read'
        )
        light_sensor.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Exterior_Light_Level', 'address': '0x3021'},
            {'ecu': 'BSI', 'parameter': 'Light_Sensor_Status', 'address': '0x3022'}
        ]
        light_sensor.validation_checks = [
            {'type': 'value_range', 'min': 0, 'max': 255},
            {'type': 'dynamic_change', 'timeout': 5}  # Wert muss sich ändern können
        ]
        
        # Regensensor
        rain_sensor = HardwareComponent(
            'rain_sensor', 'Regensensor (Automatische Scheibenwischer)',
            'BSI', 'parameter_read'
        )
        rain_sensor.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Rain_Sensor_Value', 'address': '0x3025'},
            {'ecu': 'BSI', 'parameter': 'Rain_Sensor_Sensitivity', 'address': '0x3026'}
        ]
        rain_sensor.validation_checks = [
            {'type': 'presence_check', 'expected_value': '!=0xFF'}
        ]
        
        # Frontkamera (für ADAS)
        front_camera = HardwareComponent(
            'front_camera', 'Frontkamera (Spurhalteassistent, Verkehrszeichenerkennung)',
            'CVM', 'ecu_presence'
        )
        front_camera.required_parameters = [
            {'ecu': 'CVM', 'parameter': 'Camera_Status', 'address': '0x4001'},
            {'ecu': 'CVM', 'parameter': 'Camera_Calibration_Status', 'address': '0x4002'}
        ]
        front_camera.validation_checks = [
            {'type': 'calibration_check', 'required_status': 'calibrated'}
        ]
        
        # Einparksensoren
        parking_sensors_rear = HardwareComponent(
            'parking_sensors_rear', 'Einparksensoren hinten',
            'BSI', 'sensor_array_check'
        )
        parking_sensors_rear.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Rear_Sensor_1', 'address': '0x5001'},
            {'ecu': 'BSI', 'parameter': 'Rear_Sensor_2', 'address': '0x5002'},
            {'ecu': 'BSI', 'parameter': 'Rear_Sensor_3', 'address': '0x5003'},
            {'ecu': 'BSI', 'parameter': 'Rear_Sensor_4', 'address': '0x5004'}
        ]
        parking_sensors_rear.validation_checks = [
            {'type': 'sensor_count', 'min_sensors': 2, 'max_sensors': 4}
        ]
        
        # Tempomat Hardware
        cruise_control_hw = HardwareComponent(
            'cruise_control_switches', 'Tempomat-Bedienelemente',
            'CMM', 'switch_detection'
        )
        cruise_control_hw.required_parameters = [
            {'ecu': 'CMM', 'parameter': 'Cruise_Control_Switch_Status', 'address': '0x6001'},
            {'ecu': 'COMBINE', 'parameter': 'Speed_Display_Available', 'address': '0x6002'}
        ]
        
        # Adaptives Licht (Bi-Xenon/LED)
        adaptive_light = HardwareComponent(
            'adaptive_headlights', 'Adaptive Scheinwerfer (Bi-Xenon/LED)',
            'BSI', 'actuator_test'
        )
        adaptive_light.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Headlight_Type', 'address': '0x7001'},
            {'ecu': 'BSI', 'parameter': 'Adaptive_Light_Motor_Status', 'address': '0x7002'}
        ]
        adaptive_light.validation_checks = [
            {'type': 'actuator_movement', 'test_command': 'light_adjustment_test'}
        ]
        
        # Klimaautomatik
        automatic_climate = HardwareComponent(
            'automatic_climate', 'Klimaautomatik-Sensoren',
            'CLIMATE', 'sensor_cluster'
        )
        automatic_climate.required_parameters = [
            {'ecu': 'CLIMATE', 'parameter': 'Interior_Temperature', 'address': '0x8001'},
            {'ecu': 'CLIMATE', 'parameter': 'Exterior_Temperature', 'address': '0x8002'},
            {'ecu': 'CLIMATE', 'parameter': 'Sun_Sensor', 'address': '0x8003'}
        ]
        
        # Bluetooth Hardware
        bluetooth_module = HardwareComponent(
            'bluetooth_module', 'Bluetooth-Modul',
            'NAC', 'communication_test'
        )
        bluetooth_module.required_parameters = [
            {'ecu': 'NAC', 'parameter': 'Bluetooth_Module_Present', 'address': '0x9001'},
            {'ecu': 'NAC', 'parameter': 'Bluetooth_Version', 'address': '0x9002'}
        ]
        
        # ESP/ABS für erweiterte Funktionen
        esp_system = HardwareComponent(
            'esp_abs_system', 'ESP/ABS System (für Fahrassistenz)',
            'ABS', 'system_check'
        )
        esp_system.required_parameters = [
            {'ecu': 'ABS', 'parameter': 'ESP_Available', 'address': '0xA001'},
            {'ecu': 'ABS', 'parameter': 'Wheel_Speed_Sensors', 'address': '0xA002'}
        ]
        
        # === ERWEITERTE HARDWARE-KOMPONENTEN === #
        
        # ADAS & Kamera-Systeme
        rear_camera = HardwareComponent(
            'rear_camera', 'Rückfahrkamera',
            'CVM', 'video_signal_check'
        )
        rear_camera.required_parameters = [
            {'ecu': 'CVM', 'parameter': 'Rear_Camera_Status', 'address': '0x4010'},
            {'ecu': 'CVM', 'parameter': 'Video_Signal_Present', 'address': '0x4011'}
        ]
        
        surround_cameras = HardwareComponent(
            'surround_cameras', '360° Kamera-System',
            'CVM', 'multi_camera_check'
        )
        surround_cameras.required_parameters = [
            {'ecu': 'CVM', 'parameter': 'Front_Camera_Status', 'address': '0x4020'},
            {'ecu': 'CVM', 'parameter': 'Left_Camera_Status', 'address': '0x4021'},
            {'ecu': 'CVM', 'parameter': 'Right_Camera_Status', 'address': '0x4022'},
            {'ecu': 'CVM', 'parameter': 'Rear_Camera_Status', 'address': '0x4023'}
        ]
        
        radar_front = HardwareComponent(
            'radar_front', 'Front-Radar (ACC/ADAS)',
            'RADAR', 'radar_signal_check'
        )
        radar_front.required_parameters = [
            {'ecu': 'RADAR', 'parameter': 'Radar_Status', 'address': '0x5010'},
            {'ecu': 'RADAR', 'parameter': 'Target_Detection', 'address': '0x5011'}
        ]
        
        radar_rear = HardwareComponent(
            'radar_rear', 'Heck-Radar (Blind Spot)',
            'RADAR', 'radar_signal_check'
        )
        radar_rear.required_parameters = [
            {'ecu': 'RADAR', 'parameter': 'Rear_Radar_Left', 'address': '0x5020'},
            {'ecu': 'RADAR', 'parameter': 'Rear_Radar_Right', 'address': '0x5021'}
        ]
        
        # Beleuchtungs-Systeme
        matrix_led = HardwareComponent(
            'matrix_led', 'Matrix LED Scheinwerfer',
            'BSI', 'led_matrix_test'
        )
        matrix_led.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'LED_Matrix_Type', 'address': '0x7010'},
            {'ecu': 'BSI', 'parameter': 'Matrix_Control_Available', 'address': '0x7011'}
        ]
        
        dynamic_bending_light = HardwareComponent(
            'dynamic_bending_light', 'Dynamisches Kurvenlicht',
            'BSI', 'servo_motor_test'
        )
        dynamic_bending_light.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Bending_Light_Motor_Left', 'address': '0x7020'},
            {'ecu': 'BSI', 'parameter': 'Bending_Light_Motor_Right', 'address': '0x7021'}
        ]
        
        led_daytime_running = HardwareComponent(
            'led_daytime_running', 'LED Tagfahrlicht',
            'BSI', 'led_current_check'
        )
        led_daytime_running.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'DRL_LED_Status', 'address': '0x7030'}
        ]
        
        # Komfort & Interieur
        head_up_display = HardwareComponent(
            'head_up_display', 'Head-Up Display',
            'HUD', 'display_test'
        )
        head_up_display.required_parameters = [
            {'ecu': 'HUD', 'parameter': 'Display_Status', 'address': '0x8010'},
            {'ecu': 'HUD', 'parameter': 'Projector_Available', 'address': '0x8011'}
        ]
        
        massage_seats = HardwareComponent(
            'massage_seats', 'Massage-Sitze',
            'SEATS', 'massage_motor_test'
        )
        massage_seats.required_parameters = [
            {'ecu': 'SEATS', 'parameter': 'Massage_Motor_Driver', 'address': '0x8020'},
            {'ecu': 'SEATS', 'parameter': 'Massage_Motor_Passenger', 'address': '0x8021'}
        ]
        
        heated_steering_wheel = HardwareComponent(
            'heated_steering_wheel', 'Beheizbares Lenkrad',
            'BSI', 'heating_element_check'
        )
        heated_steering_wheel.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Steering_Wheel_Heater', 'address': '0x8030'}
        ]
        
        ventilated_seats = HardwareComponent(
            'ventilated_seats', 'Belüftete Sitze',
            'SEATS', 'ventilation_fan_test'
        )
        ventilated_seats.required_parameters = [
            {'ecu': 'SEATS', 'parameter': 'Seat_Ventilation_Driver', 'address': '0x8040'},
            {'ecu': 'SEATS', 'parameter': 'Seat_Ventilation_Passenger', 'address': '0x8041'}
        ]
        
        # Fahrwerk & Suspension
        air_suspension = HardwareComponent(
            'air_suspension', 'Luftfederung',
            'SUSPENSION', 'air_pressure_check'
        )
        air_suspension.required_parameters = [
            {'ecu': 'SUSPENSION', 'parameter': 'Air_Compressor_Status', 'address': '0x9010'},
            {'ecu': 'SUSPENSION', 'parameter': 'Air_Spring_Pressure', 'address': '0x9011'}
        ]
        
        adaptive_dampers = HardwareComponent(
            'adaptive_dampers', 'Adaptive Dämpfer',
            'SUSPENSION', 'damper_control_check'
        )
        adaptive_dampers.required_parameters = [
            {'ecu': 'SUSPENSION', 'parameter': 'Damper_Control_FL', 'address': '0x9020'},
            {'ecu': 'SUSPENSION', 'parameter': 'Damper_Control_FR', 'address': '0x9021'},
            {'ecu': 'SUSPENSION', 'parameter': 'Damper_Control_RL', 'address': '0x9022'},
            {'ecu': 'SUSPENSION', 'parameter': 'Damper_Control_RR', 'address': '0x9023'}
        ]
        
        # Erweiterte Audio-Systeme
        premium_sound = HardwareComponent(
            'premium_sound', 'Premium Sound System',
            'NAC', 'amplifier_check'
        )
        premium_sound.required_parameters = [
            {'ecu': 'NAC', 'parameter': 'External_Amplifier', 'address': '0xA010'},
            {'ecu': 'NAC', 'parameter': 'Speaker_Count', 'address': '0xA011'}
        ]
        
        active_noise_cancellation = HardwareComponent(
            'active_noise_cancellation', 'Aktive Geräuschunterdrückung',
            'NAC', 'microphone_array_check'
        )
        active_noise_cancellation.required_parameters = [
            {'ecu': 'NAC', 'parameter': 'ANC_Microphones', 'address': '0xA020'},
            {'ecu': 'NAC', 'parameter': 'ANC_Processing_Unit', 'address': '0xA021'}
        ]
        
        # Sicherheits-Systeme
        night_vision = HardwareComponent(
            'night_vision', 'Nachtsicht-System',
            'CAMERA', 'infrared_camera_check'
        )
        night_vision.required_parameters = [
            {'ecu': 'CAMERA', 'parameter': 'IR_Camera_Status', 'address': '0xB010'},
            {'ecu': 'CAMERA', 'parameter': 'Thermal_Sensor', 'address': '0xB011'}
        ]
        
        driver_monitoring = HardwareComponent(
            'driver_monitoring', 'Fahrerüberwachung',
            'CAMERA', 'internal_camera_check'
        )
        driver_monitoring.required_parameters = [
            {'ecu': 'CAMERA', 'parameter': 'Interior_Camera_Status', 'address': '0xB020'},
            {'ecu': 'CAMERA', 'parameter': 'Eye_Tracking_Available', 'address': '0xB021'}
        ]
        
        # Connectivity & Telematics
        cellular_modem = HardwareComponent(
            'cellular_modem', 'Mobilfunk-Modem (4G/5G)',
            'TELEMATICS', 'network_connectivity_check'
        )
        cellular_modem.required_parameters = [
            {'ecu': 'TELEMATICS', 'parameter': 'Modem_Status', 'address': '0xC010'},
            {'ecu': 'TELEMATICS', 'parameter': 'Signal_Strength', 'address': '0xC011'}
        ]
        
        wifi_hotspot = HardwareComponent(
            'wifi_hotspot', 'WiFi Hotspot',
            'TELEMATICS', 'wifi_module_check'
        )
        wifi_hotspot.required_parameters = [
            {'ecu': 'TELEMATICS', 'parameter': 'WiFi_Module_Status', 'address': '0xC020'},
            {'ecu': 'TELEMATICS', 'parameter': 'WiFi_Antenna_Status', 'address': '0xC021'}
        ]
        
        # Erweiterte Sensoren
        lidar_sensor = HardwareComponent(
            'lidar_sensor', 'LiDAR Sensor (Premium ADAS)',
            'LIDAR', 'laser_scanning_check'
        )
        lidar_sensor.required_parameters = [
            {'ecu': 'LIDAR', 'parameter': 'Laser_Status', 'address': '0xD010'},
            {'ecu': 'LIDAR', 'parameter': 'Point_Cloud_Data', 'address': '0xD011'}
        ]
        
        ultrasonic_sensors_front = HardwareComponent(
            'ultrasonic_sensors_front', 'Ultraschall-Sensoren vorne',
            'BSI', 'ultrasonic_array_check'
        )
        ultrasonic_sensors_front.required_parameters = [
            {'ecu': 'BSI', 'parameter': 'Front_Sensor_1', 'address': '0x5030'},
            {'ecu': 'BSI', 'parameter': 'Front_Sensor_2', 'address': '0x5031'},
            {'ecu': 'BSI', 'parameter': 'Front_Sensor_3', 'address': '0x5032'},
            {'ecu': 'BSI', 'parameter': 'Front_Sensor_4', 'address': '0x5033'}
        ]
        
        # In erweiterte Datenbank speichern
        extended_components = [
            light_sensor, rain_sensor, front_camera, parking_sensors_rear,
            cruise_control_hw, adaptive_light, automatic_climate, 
            bluetooth_module, esp_system,
            # Erweiterte Komponenten
            rear_camera, surround_cameras, radar_front, radar_rear,
            matrix_led, dynamic_bending_light, led_daytime_running,
            head_up_display, massage_seats, heated_steering_wheel, ventilated_seats,
            air_suspension, adaptive_dampers, premium_sound, active_noise_cancellation,
            night_vision, driver_monitoring, cellular_modem, wifi_hotspot,
            lidar_sensor, ultrasonic_sensors_front
        ]
        
        for component in extended_components:
            self.hardware_components[component.component_id] = component
    
    def initialize_feature_requirements(self):
        """Initialisiere Feature-Hardware-Anforderungen"""
        
        self.feature_hardware_requirements = {
            # Komfort Features
            'auto_lights': {
                'required_hardware': ['light_sensor'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            'auto_wipers': {
                'required_hardware': ['rain_sensor'],
                'optional_hardware': [],
                'minimum_confidence': 0.7
            },
            'auto_door_lock': {
                'required_hardware': [],  # Nur Software-Feature
                'optional_hardware': [],
                'minimum_confidence': 1.0
            },
            'speed_door_lock': {
                'required_hardware': [],  # Nutzt vorhandene Speed-Sensoren
                'optional_hardware': ['esp_abs_system'],
                'minimum_confidence': 0.9
            },
            
            # Audio Features
            'bluetooth_a2dp': {
                'required_hardware': ['bluetooth_module'],
                'optional_hardware': [],
                'minimum_confidence': 0.9
            },
            'nac_apps': {
                'required_hardware': [],  # NAC-ECU selbst ist erforderlich
                'optional_hardware': [],
                'minimum_confidence': 1.0
            },
            
            # Sicherheits Features
            'cruise_control': {
                'required_hardware': ['cruise_control_switches', 'esp_abs_system'],
                'optional_hardware': [],
                'minimum_confidence': 0.9
            },
            'speed_limiter': {
                'required_hardware': ['cruise_control_switches'],
                'optional_hardware': ['esp_abs_system'],
                'minimum_confidence': 0.8
            },
            'lane_assist': {
                'required_hardware': ['front_camera', 'esp_abs_system'],
                'optional_hardware': [],
                'minimum_confidence': 0.95
            },
            'parking_sensors': {
                'required_hardware': ['parking_sensors_rear'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            
            # Beleuchtung Features
            'adaptive_headlights': {
                'required_hardware': ['adaptive_light'],
                'optional_hardware': ['light_sensor'],
                'minimum_confidence': 0.9
            },
            'led_daytime_running': {
                'required_hardware': [],  # Hängt vom Scheinwerfer-Typ ab
                'optional_hardware': ['adaptive_light'],
                'minimum_confidence': 0.7
            },
            
            # Motor Features
            'stop_start': {
                'required_hardware': [],  # Motorabhängig
                'optional_hardware': [],
                'minimum_confidence': 0.8,
                'engine_compatibility': ['1.2L_PureTech', '1.6L_BlueHDi', '1.0L_3cyl']
            },
            
            # Klima Features
            'auto_climate': {
                'required_hardware': ['automatic_climate'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            
            # === ERWEITERTE FEATURE-HARDWARE-MAPPINGS === #
            
            # ADAS Features
            'rear_camera_system': {
                'required_hardware': ['rear_camera'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            'surround_view': {
                'required_hardware': ['surround_cameras'],
                'optional_hardware': ['rear_camera'],
                'minimum_confidence': 0.9
            },
            'adaptive_cruise_control': {
                'required_hardware': ['radar_front', 'esp_abs_system'],
                'optional_hardware': ['front_camera'],
                'minimum_confidence': 0.9
            },
            'blind_spot_monitoring': {
                'required_hardware': ['radar_rear'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            'autonomous_parking': {
                'required_hardware': ['surround_cameras', 'ultrasonic_sensors_front', 'parking_sensors_rear'],
                'optional_hardware': ['radar_front'],
                'minimum_confidence': 0.95
            },
            
            # Erweiterte Beleuchtung
            'matrix_led_headlights': {
                'required_hardware': ['matrix_led'],
                'optional_hardware': ['light_sensor'],
                'minimum_confidence': 0.9
            },
            'dynamic_curve_lighting': {
                'required_hardware': ['dynamic_bending_light'],
                'optional_hardware': ['esp_abs_system'],
                'minimum_confidence': 0.8
            },
            'led_drl_system': {
                'required_hardware': ['led_daytime_running'],
                'optional_hardware': [],
                'minimum_confidence': 0.7
            },
            
            # Komfort Features Premium
            'head_up_display_system': {
                'required_hardware': ['head_up_display'],
                'optional_hardware': [],
                'minimum_confidence': 0.9
            },
            'massage_seat_function': {
                'required_hardware': ['massage_seats'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            'heated_steering_wheel_function': {
                'required_hardware': ['heated_steering_wheel'],
                'optional_hardware': [],
                'minimum_confidence': 0.7
            },
            'ventilated_seat_function': {
                'required_hardware': ['ventilated_seats'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            
            # Fahrwerk Features
            'air_suspension_system': {
                'required_hardware': ['air_suspension'],
                'optional_hardware': [],
                'minimum_confidence': 0.9
            },
            'adaptive_suspension': {
                'required_hardware': ['adaptive_dampers'],
                'optional_hardware': ['esp_abs_system'],
                'minimum_confidence': 0.8
            },
            
            # Premium Audio
            'premium_audio_system': {
                'required_hardware': ['premium_sound'],
                'optional_hardware': ['bluetooth_module'],
                'minimum_confidence': 0.8
            },
            'noise_cancellation_system': {
                'required_hardware': ['active_noise_cancellation'],
                'optional_hardware': ['premium_sound'],
                'minimum_confidence': 0.9
            },
            
            # Sicherheits-Features Premium
            'night_vision_system': {
                'required_hardware': ['night_vision'],
                'optional_hardware': ['head_up_display'],
                'minimum_confidence': 0.95
            },
            'driver_attention_monitoring': {
                'required_hardware': ['driver_monitoring'],
                'optional_hardware': ['front_camera'],
                'minimum_confidence': 0.9
            },
            
            # Connectivity Features
            'cellular_connectivity': {
                'required_hardware': ['cellular_modem'],
                'optional_hardware': [],
                'minimum_confidence': 0.8
            },
            'wifi_hotspot_function': {
                'required_hardware': ['wifi_hotspot'],
                'optional_hardware': ['cellular_modem'],
                'minimum_confidence': 0.8
            },
            
            # Zukunftstechnologien
            'lidar_adas_system': {
                'required_hardware': ['lidar_sensor'],
                'optional_hardware': ['radar_front', 'front_camera'],
                'minimum_confidence': 0.95
            },
            'front_parking_assist': {
                'required_hardware': ['ultrasonic_sensors_front'],
                'optional_hardware': ['front_camera'],
                'minimum_confidence': 0.8
            }
        }
    
    def check_hardware_for_feature(self, feature_id, detected_ecus, vehicle_profile=None):
        """Prüfe Hardware-Verfügbarkeit für ein bestimmtes Feature"""
        
        if feature_id not in self.feature_hardware_requirements:
            return HardwareValidationResult(feature_id, False, 
                                          {'error': 'Feature nicht in Hardware-DB'})
        
        requirements = self.feature_hardware_requirements[feature_id]
        validation_results = []
        overall_confidence = 1.0
        
        # Prüfe erforderliche Hardware
        for hw_id in requirements['required_hardware']:
            if hw_id in self.hardware_components:
                hw_component = self.hardware_components[hw_id]
                validation = self._validate_hardware_component(hw_component, detected_ecus, vehicle_profile)
                validation_results.append(validation)
                
                if not validation.is_available:
                    return HardwareValidationResult(feature_id, False, {
                        'missing_hardware': hw_id,
                        'component_name': hw_component.name,
                        'validation_details': validation.detection_details
                    })
                
                overall_confidence *= validation.confidence_level
        
        # Prüfe optionale Hardware
        optional_available = []
        for hw_id in requirements.get('optional_hardware', []):
            if hw_id in self.hardware_components:
                hw_component = self.hardware_components[hw_id]
                validation = self._validate_hardware_component(hw_component, detected_ecus, vehicle_profile)
                if validation.is_available:
                    optional_available.append(hw_id)
                    overall_confidence *= 1.1  # Bonus für optionale Hardware
        
        # Prüfe Mindest-Confidence
        min_confidence = requirements.get('minimum_confidence', 0.8)
        is_available = overall_confidence >= min_confidence
        
        return HardwareValidationResult(feature_id, is_available, {
            'confidence': overall_confidence,
            'required_hardware_status': validation_results,
            'optional_hardware': optional_available,
            'minimum_confidence': min_confidence
        })
    
    def _validate_hardware_component(self, component, detected_ecus, vehicle_profile=None):
        """Validiere eine einzelne Hardware-Komponente"""
        
        # Prüfe ob das erforderliche ECU verfügbar ist
        required_ecu = component.ecu_location
        ecu_available = False
        
        for ecu in detected_ecus:
            ecu_name = ecu.get('name', '').upper()
            if required_ecu in ecu_name:
                ecu_available = True
                break
        
        if not ecu_available:
            return HardwareValidationResult(component.component_id, False, {
                'error': f'ECU {required_ecu} nicht verfügbar',
                'required_ecu': required_ecu,
                'detected_ecus': [ecu.get('name', '') for ecu in detected_ecus]
            })
        
        # Simuliere Hardware-Erkennung basierend auf Detection-Method
        detection_method = component.detection_method
        confidence = 0.0
        details = {}
        
        if detection_method == 'parameter_read':
            # Simuliere Parameter-Lesung
            confidence = self._simulate_parameter_detection(component, vehicle_profile)
            details['method'] = 'Parameter gelesen'
            
        elif detection_method == 'ecu_presence':
            # ECU-Anwesenheit prüfen
            confidence = 0.9 if ecu_available else 0.0
            details['method'] = 'ECU Anwesenheit geprüft'
            
        elif detection_method == 'sensor_array_check':
            # Mehrere Sensoren prüfen
            confidence = self._simulate_sensor_array_check(component, vehicle_profile)
            details['method'] = 'Sensor-Array geprüft'
            
        elif detection_method == 'actuator_test':
            # Aktuator-Test
            confidence = self._simulate_actuator_test(component, vehicle_profile)
            details['method'] = 'Aktuator getestet'
            
        elif detection_method == 'communication_test':
            # Kommunikationstest
            confidence = self._simulate_communication_test(component, vehicle_profile)
            details['method'] = 'Kommunikation getestet'
            
        elif detection_method == 'system_check':
            # System-Check
            confidence = self._simulate_system_check(component, vehicle_profile)
            details['method'] = 'System geprüft'
            
        else:
            confidence = 0.5  # Default für unbekannte Methoden
            details['method'] = 'Standard-Erkennung'
        
        is_available = confidence >= 0.7
        
        result = HardwareValidationResult(component.component_id, is_available, details)
        result.confidence_level = confidence
        
        return result
    
    def _simulate_parameter_detection(self, component, vehicle_profile):
        """Simuliere Parameter-basierte Hardware-Erkennung"""
        
        # Fahrzeugspezifische Wahrscheinlichkeiten
        if vehicle_profile:
            vehicle_name = getattr(vehicle_profile, 'name', '').lower()
            production_year = getattr(vehicle_profile, 'production_years', '')
            
            # Neuere Fahrzeuge haben mehr Sensoren
            if any(year in production_year for year in ['2018', '2019', '2020', '2021', '2022', '2023', '2024']):
                base_confidence = 0.9
            elif any(year in production_year for year in ['2015', '2016', '2017']):
                base_confidence = 0.7
            else:
                base_confidence = 0.5
            
            # Fahrzeugmodell-spezifische Anpassungen
            if 'ds' in vehicle_name or 'allure' in vehicle_name or 'gt' in vehicle_name:
                base_confidence *= 1.1  # Premium-Ausstattung
            elif 'active' in vehicle_name or 'access' in vehicle_name:
                base_confidence *= 0.8  # Basis-Ausstattung
        else:
            base_confidence = 0.7
        
        # Komponenten-spezifische Anpassungen
        component_id = component.component_id
        
        if component_id == 'light_sensor':
            # Lichtsensor ist in den meisten modernen Fahrzeugen vorhanden
            return min(base_confidence * 1.1, 1.0)
        elif component_id == 'rain_sensor':
            # Regensensor ist weniger verbreitet
            return min(base_confidence * 0.8, 1.0)
        elif component_id == 'front_camera':
            # Kamera nur in neueren/höheren Ausstattungen
            return min(base_confidence * 0.6, 1.0)
        
        return base_confidence
    
    def _simulate_sensor_array_check(self, component, vehicle_profile):
        """Simuliere Sensor-Array-Erkennung (z.B. Einparksensoren)"""
        
        base_confidence = 0.6  # Einparksensoren sind optional
        
        if vehicle_profile:
            vehicle_name = getattr(vehicle_profile, 'name', '').lower()
            
            # Premium-Modelle haben öfter Einparksensoren
            if any(keyword in vehicle_name for keyword in ['allure', 'gt', 'shine', 'ds']):
                base_confidence = 0.8
            elif any(keyword in vehicle_name for keyword in ['pack', 'plus']):
                base_confidence = 0.7
        
        return base_confidence
    
    def _simulate_actuator_test(self, component, vehicle_profile):
        """Simuliere Aktuator-Test (z.B. adaptive Scheinwerfer)"""
        
        base_confidence = 0.4  # Adaptive Scheinwerfer sind selten
        
        if vehicle_profile:
            vehicle_name = getattr(vehicle_profile, 'name', '').lower()
            production_year = getattr(vehicle_profile, 'production_years', '')
            
            # Nur in Premium-Modellen und neueren Fahrzeugen
            if ('ds' in vehicle_name or 'gt' in vehicle_name) and any(year in production_year for year in ['2019', '2020', '2021', '2022', '2023', '2024']):
                base_confidence = 0.8
            elif 'xenon' in vehicle_name or 'led' in vehicle_name:
                base_confidence = 0.6
        
        return base_confidence
    
    def _simulate_communication_test(self, component, vehicle_profile):
        """Simuliere Kommunikationstest (z.B. Bluetooth)"""
        
        base_confidence = 0.8  # Bluetooth ist weit verbreitet
        
        if vehicle_profile:
            production_year = getattr(vehicle_profile, 'production_years', '')
            
            # Bluetooth wird mit den Jahren standard
            if any(year in production_year for year in ['2018', '2019', '2020', '2021', '2022', '2023', '2024']):
                base_confidence = 0.95
            elif any(year in production_year for year in ['2015', '2016', '2017']):
                base_confidence = 0.8
            else:
                base_confidence = 0.5
        
        return base_confidence
    
    def _simulate_system_check(self, component, vehicle_profile):
        """Simuliere System-Check (z.B. ESP/ABS)"""
        
        # ESP/ABS ist seit 2014 Pflicht in Europa
        base_confidence = 0.95
        
        if vehicle_profile:
            production_year = getattr(vehicle_profile, 'production_years', '')
            
            # Vor 2014 war ESP optional
            if any(year in production_year for year in ['2010', '2011', '2012', '2013']):
                base_confidence = 0.7
        
        return base_confidence
    
    def check_multi_ecu_hardware_compatibility(self, feature_list, detected_ecus, vehicle_profile=None):
        """Prüfe Hardware-Kompatibilität für mehrere Features gleichzeitig"""
        
        self.validationMessage.emit("Starte Multi-ECU Hardware-Validierung...")
        
        compatibility_results = {}
        hardware_conflicts = []
        shared_hardware = {}
        
        total_features = len(feature_list)
        
        for i, feature_id in enumerate(feature_list):
            self.validationProgress.emit(int((i / total_features) * 100))
            self.validationMessage.emit(f"Prüfe Hardware für {feature_id}...")
            
            result = self.check_hardware_for_feature(feature_id, detected_ecus, vehicle_profile)
            compatibility_results[feature_id] = result
            
            # Prüfe auf geteilte Hardware-Komponenten
            if feature_id in self.feature_hardware_requirements:
                requirements = self.feature_hardware_requirements[feature_id]
                for hw_id in requirements.get('required_hardware', []):
                    if hw_id not in shared_hardware:
                        shared_hardware[hw_id] = []
                    shared_hardware[hw_id].append(feature_id)
        
        # Prüfe auf Hardware-Konflikte
        for hw_id, features in shared_hardware.items():
            if len(features) > 1:
                # Prüfe ob Hardware gleichzeitig genutzt werden kann
                hw_component = self.hardware_components.get(hw_id)
                if hw_component and not self._can_share_hardware(hw_component, features):
                    hardware_conflicts.append({
                        'hardware': hw_id,
                        'conflicting_features': features,
                        'resolution': 'Sequential activation required'
                    })
        
        self.validationProgress.emit(100)
        self.validationMessage.emit("Multi-ECU Hardware-Validierung abgeschlossen")
        
        return {
            'individual_results': compatibility_results,
            'hardware_conflicts': hardware_conflicts,
            'shared_hardware': shared_hardware,
            'overall_compatibility': self._calculate_overall_compatibility(compatibility_results)
        }
    
    def _can_share_hardware(self, hardware_component, features):
        """Prüfe ob Hardware zwischen Features geteilt werden kann"""
        
        # Die meisten Hardware-Komponenten können geteilt werden
        # Ausnahmen sind Aktuatoren die exklusiven Zugriff benötigen
        
        exclusive_hardware = [
            'adaptive_light',  # Kann nicht gleichzeitig für verschiedene Features bewegt werden
        ]
        
        return hardware_component.component_id not in exclusive_hardware
    
    def _calculate_overall_compatibility(self, individual_results):
        """Berechne Gesamt-Kompatibilität"""
        
        if not individual_results:
            return 0.0
        
        available_count = sum(1 for result in individual_results.values() if result.is_available)
        total_count = len(individual_results)
        
        return available_count / total_count
    
    def get_hardware_recommendations(self, vehicle_profile, target_features):
        """Gebe Hardware-Empfehlungen für gewünschte Features"""
        
        recommendations = []
        missing_hardware = set()
        
        for feature_id in target_features:
            if feature_id in self.feature_hardware_requirements:
                requirements = self.feature_hardware_requirements[feature_id]
                
                for hw_id in requirements.get('required_hardware', []):
                    if hw_id in self.hardware_components:
                        hw_component = self.hardware_components[hw_id]
                        missing_hardware.add((hw_id, hw_component.name, feature_id))
        
        # Erstelle Empfehlungen
        for hw_id, hw_name, feature_id in missing_hardware:
            recommendations.append({
                'hardware_id': hw_id,
                'hardware_name': hw_name,
                'required_for_feature': feature_id,
                'installation_complexity': self._get_installation_complexity(hw_id),
                'estimated_cost': self._get_estimated_cost(hw_id, vehicle_profile)
            })
        
        return recommendations
    
    def _get_installation_complexity(self, hardware_id):
        """Schätze Installations-Komplexität"""
        
        complexity_map = {
            'light_sensor': 'low',
            'rain_sensor': 'medium',
            'front_camera': 'high',
            'parking_sensors_rear': 'medium',
            'cruise_control_switches': 'medium',
            'adaptive_light': 'high',
            'automatic_climate': 'high',
            'bluetooth_module': 'low',
            'esp_abs_system': 'very_high'
        }
        
        return complexity_map.get(hardware_id, 'unknown')
    
    def _get_estimated_cost(self, hardware_id, vehicle_profile):
        """Schätze Kosten für Hardware-Nachrüstung"""
        
        # Grobe Kostenschätzungen in Euro
        cost_map = {
            'light_sensor': (50, 150),
            'rain_sensor': (100, 250),
            'front_camera': (800, 1500),
            'parking_sensors_rear': (200, 500),
            'cruise_control_switches': (150, 300),
            'adaptive_light': (1000, 2000),
            'automatic_climate': (500, 1000),
            'bluetooth_module': (100, 200),
            'esp_abs_system': (2000, 3000)  # Meist nicht nachrüstbar
        }
        
        base_cost = cost_map.get(hardware_id, (0, 0))
        
        # Fahrzeugalter-Anpassung
        if vehicle_profile:
            production_year = getattr(vehicle_profile, 'production_years', '')
            if any(year in production_year for year in ['2010', '2011', '2012', '2013']):
                # Ältere Fahrzeuge: höhere Nachrüstkosten
                base_cost = (base_cost[0] * 1.3, base_cost[1] * 1.5)
        
        return {
            'min_cost': int(base_cost[0]),
            'max_cost': int(base_cost[1]),
            'currency': 'EUR',
            'includes_installation': True
        }


# Factory Functions
def create_hardware_checker(parent=None) -> HardwareCompatibilityChecker:
    """Factory-Funktion für Hardware Checker"""
    return HardwareCompatibilityChecker(parent)

def quick_compatibility_check(serial_controller, ecu_data: dict = None) -> bool:
    """Schnelle Kompatibilitätsprüfung - gibt nur True/False zurück"""
    checker = HardwareCompatibilityChecker()
    result = checker.check_hardware_compatibility(serial_controller, ecu_data)
    return result.compatible


# Test-Funktion
if __name__ == "__main__":
    print("Hardware Compatibility Checker - Test")
    checker = HardwareCompatibilityChecker()
    
    # Test ECU-Daten
    test_ecu = {
        "name": "BSI 2019 Corsa F",
        "protocol": "UDS",
        "tx_id": "752",
        "rx_id": "652"
    }
    
    print(f"Safe Features for BSI: {checker.get_safe_features_for_ecu('BSI')}")
    print(f"Feature 'auto_door_lock' safe for BSI + Evolution XS VCI: {checker.is_feature_safe('auto_door_lock', 'BSI', 'Evolution XS VCI')}")