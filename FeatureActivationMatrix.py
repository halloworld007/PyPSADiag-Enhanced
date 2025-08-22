"""
FeatureActivationMatrix.py

Intelligente Feature-Aktivierungsmatrix für PSA/Stellantis Fahrzeuge
- Zeigt nur verfügbare Features für verbundenes Fahrzeug
- Berücksichtigt Cross-ECU-Abhängigkeiten
- Benutzerfreundliche Oberfläche ohne technische Vorkenntnisse
"""

# Qt Framework Kompatibilität
try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QCheckBox, QProgressBar, QTextEdit, QComboBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QCheckBox, QProgressBar, QTextEdit, QComboBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
        QT_FRAMEWORK = "PyQt5"
import json
from datetime import datetime

# Import Hardware Compatibility Checker
try:
    from HardwareCompatibilityChecker import HardwareCompatibilityChecker, HardwareValidationResult
    HARDWARE_CHECKER_AVAILABLE = True
except ImportError:
    HARDWARE_CHECKER_AVAILABLE = False


class FeatureCapability:
    """Einzelne Feature-Fähigkeit"""
    
    def __init__(self, feature_id, name, description, category):
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.category = category
        self.required_ecus = []
        self.dependency_features = []
        self.activation_steps = []
        self.user_friendly_name = name
        self.difficulty_level = "easy"  # easy, medium, hard
        self.estimated_time = "2-5 min"
        self.warnings = []
        self.compatible_years = []
        self.compatible_engines = []


class CrossECUDependency:
    """Cross-ECU Abhängigkeit"""
    
    def __init__(self, primary_ecu, secondary_ecus, description):
        self.primary_ecu = primary_ecu
        self.secondary_ecus = secondary_ecus if isinstance(secondary_ecus, list) else [secondary_ecus]
        self.description = description
        self.activation_order = []
        self.validation_steps = []


class ActivationProcedure:
    """Aktivierungsprozedur"""
    
    def __init__(self, procedure_id, steps, validation_method=None):
        self.procedure_id = procedure_id
        self.steps = steps
        self.validation_method = validation_method
        self.estimated_duration = 0
        self.required_conditions = []


class FeatureActivationMatrix(QObject):
    """Feature-Aktivierungsmatrix Hauptklasse"""
    
    # Signals
    featureActivated = Signal(str, bool)  # feature_id, success
    activationProgress = Signal(int)  # percentage
    activationMessage = Signal(str)
    vehicleDetected = Signal(dict)
    dependencyAnalyzed = Signal(dict)
    hardwareValidated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_vehicle = None
        self.detected_ecus = []
        self.available_features = {}
        self.activation_dependencies = {}
        self.hardware_checker = None
        
        # Initialize hardware checker if available
        if HARDWARE_CHECKER_AVAILABLE:
            self.hardware_checker = HardwareCompatibilityChecker()
            self.hardware_checker.hardwareDetected.connect(self.hardwareValidated.emit)
        self.user_selections = {}
        
        # Initialize comprehensive feature database
        self.initialize_feature_database()
        self.initialize_dependency_mapping()
    
    def initialize_feature_database(self):
        """Initialisiere UMFASSENDE Feature-Datenbank - ALLE PSA/Stellantis Features"""
        
        # BSI (Body System Interface) Features
        bsi_features = {
            'auto_lights': FeatureCapability(
                'auto_lights', 'Automatisches Licht', 
                'Scheinwerfer schalten sich automatisch bei Dämmerung ein/aus',
                'bsi'
            ),
            'auto_wipers': FeatureCapability(
                'auto_wipers', 'Regensensor', 
                'Scheibenwischer reagieren automatisch auf Regen',
                'bsi'
            ),
            'welcome_lighting': FeatureCapability(
                'welcome_lighting', 'Begrüßungsbeleuchtung',
                'Beleuchtung beim Entriegeln des Fahrzeugs',
                'bsi'
            ),
            'follow_me_home': FeatureCapability(
                'follow_me_home', 'Follow-Me-Home Beleuchtung',
                'Scheinwerfer bleiben nach Abstellen kurz an',
                'bsi'
            ),
            'auto_door_lock': FeatureCapability(
                'auto_door_lock', 'Automatische Türverriegelung',
                'Türen verriegeln automatisch beim Wegfahren',
                'bsi'
            ),
            'speed_door_lock': FeatureCapability(
                'speed_door_lock', 'Geschwindigkeitsverriegelung',
                'Türen verriegeln ab bestimmter Geschwindigkeit',
                'bsi'
            ),
            'selective_unlock': FeatureCapability(
                'selective_unlock', 'Selektives Entriegeln',
                'Erst Fahrertür, dann alle Türen entriegeln',
                'bsi'
            ),
            'window_comfort': FeatureCapability(
                'window_comfort', 'Komfort-Fensterheber',
                'Fenster über Fernbedienung öffnen/schließen',
                'bsi'
            ),
            'central_locking': FeatureCapability(
                'central_locking', 'Zentralverriegelung',
                'Alle Türen gleichzeitig ver-/entriegeln',
                'bsi'
            ),
            'deadlock': FeatureCapability(
                'deadlock', 'Diebstahlschutz-Verriegelung',
                'Türen von innen nicht öffenbar',
                'bsi'
            ),
            'interior_lighting': FeatureCapability(
                'interior_lighting', 'Innenraumbeleuchtung',
                'Automatische Innenbeleuchtung beim Einsteigen',
                'bsi'
            ),
            'mirror_fold': FeatureCapability(
                'mirror_fold', 'Spiegelklappung',
                'Außenspiegel klappen beim Verriegeln ein',
                'bsi'
            ),
            'mirror_heating': FeatureCapability(
                'mirror_heating', 'Spiegelheizung',
                'Beheizung der Außenspiegel',
                'bsi'
            ),
            'seat_heating': FeatureCapability(
                'seat_heating', 'Sitzheizung',
                'Beheizung der Vordersitze',
                'bsi'
            ),
            'steering_heating': FeatureCapability(
                'steering_heating', 'Lenkradheizung',
                'Beheizung des Lenkrads',
                'bsi'
            ),
            'key_card': FeatureCapability(
                'key_card', 'Keyless Entry',
                'Keycard/Hands-free Zugang',
                'bsi'
            ),
            'panic_alarm': FeatureCapability(
                'panic_alarm', 'Panikalarm',
                'Alarmanlage über Fernbedienung',
                'bsi'
            ),
            'perimeter_alarm': FeatureCapability(
                'perimeter_alarm', 'Überwachungsalarm',
                'Alarmanlage bei unbefugtem Zugang',
                'bsi'
            ),
            'volumetric_alarm': FeatureCapability(
                'volumetric_alarm', 'Volumetrischer Alarm',
                'Innenraumüberwachung per Ultraschall',
                'bsi'
            ),
            'tilt_alarm': FeatureCapability(
                'tilt_alarm', 'Neigungsalarm',
                'Alarm bei Fahrzeuganhebung/Abschleppen',
                'bsi'
            ),
            'electric_windows': FeatureCapability(
                'electric_windows', 'Elektrische Fensterheber',
                'Automatische Fensterheber mit One-Touch',
                'bsi'
            ),
            'sunroof_control': FeatureCapability(
                'sunroof_control', 'Schiebedachsteuerung',
                'Elektrisches Schiebedach',
                'bsi'
            ),
            'tailgate_control': FeatureCapability(
                'tailgate_control', 'Heckklappensteuerung',
                'Elektrische Heckklappe',
                'bsi'
            )
        }
        
        # CMM (Common Motor Management) Features  
        cmm_features = {
            'stop_start': FeatureCapability(
                'stop_start', 'Start-Stop System',
                'Motor schaltet bei Stillstand automatisch ab',
                'cmm'
            ),
            'eco_mode': FeatureCapability(
                'eco_mode', 'ECO-Modus',
                'Sparsame Fahrweise für geringeren Verbrauch',
                'cmm'
            ),
            'sport_mode': FeatureCapability(
                'sport_mode', 'Sport-Modus',
                'Sportlichere Abstimmung von Motor und Fahrwerk',
                'cmm'
            ),
            'dpf_regen': FeatureCapability(
                'dpf_regen', 'DPF-Regeneration',
                'Automatische Reinigung des Dieselpartikelfilters',
                'cmm'
            ),
            'engine_braking': FeatureCapability(
                'engine_braking', 'Motorbremse',
                'Verstärkte Motorbremswirkung',
                'cmm'
            ),
            'cruise_control': FeatureCapability(
                'cruise_control', 'Tempomat',
                'Geschwindigkeit automatisch halten',
                'cmm'
            ),
            'speed_limiter': FeatureCapability(
                'speed_limiter', 'Geschwindigkeitsbegrenzer',
                'Maximale Geschwindigkeit einstellbar',
                'cmm'
            ),
            'adaptive_cruise': FeatureCapability(
                'adaptive_cruise', 'Adaptiver Tempomat',
                'Automatischer Abstand zum Vorderfahrzeug',
                'cmm'
            ),
            'launch_control': FeatureCapability(
                'launch_control', 'Launch Control',
                'Optimaler Beschleunigungsstart',
                'cmm'
            ),
            'traction_control': FeatureCapability(
                'traction_control', 'Traktionskontrolle',
                'Verhinderung von Radschlupf',
                'cmm'
            ),
            'throttle_mapping': FeatureCapability(
                'throttle_mapping', 'Gaspedal-Kennlinie',
                'Anpassung der Gaspedalcharakteristik',
                'cmm'
            ),
            'auto_hold': FeatureCapability(
                'auto_hold', 'Auto Hold',
                'Automatisches Halten an Ampeln/im Stau',
                'cmm'
            ),
            'hill_assist': FeatureCapability(
                'hill_assist', 'Berganfahrhilfe',
                'Verhindert Zurückrollen am Berg',
                'cmm'
            ),
            'rev_matching': FeatureCapability(
                'rev_matching', 'Rev Matching',
                'Automatische Drehzahlanpassung beim Schalten',
                'cmm'
            ),
            'overboost': FeatureCapability(
                'overboost', 'Overboost',
                'Temporäre Leistungssteigerung',
                'cmm'
            ),
            'exhaust_valve': FeatureCapability(
                'exhaust_valve', 'Auspuffklappensteuerung',
                'Variable Auspuffgeräusche',
                'cmm'
            ),
            'cold_start': FeatureCapability(
                'cold_start', 'Kaltstartoptimierung',
                'Optimierter Kaltstart bei niedrigen Temperaturen',
                'cmm'
            ),
            'adblue_heating': FeatureCapability(
                'adblue_heating', 'AdBlue Heizung',
                'Heizung für SCR-System bei Diesel',
                'cmm'
            ),
            'glow_plug': FeatureCapability(
                'glow_plug', 'Glühkerzensteuerung',
                'Optimierte Glühkerzenaktivierung',
                'cmm'
            ),
            'turbo_lag': FeatureCapability(
                'turbo_lag', 'Anti-Lag System',
                'Reduzierung des Turbolochs',
                'cmm'
            )
        }
        
        # ABS/ESP Features
        abs_esp_features = {
            'abs_system': FeatureCapability(
                'abs_system', 'ABS Antiblockiersystem',
                'Verhindert Blockieren der Räder beim Bremsen',
                'abs'
            ),
            'esp_system': FeatureCapability(
                'esp_system', 'ESP Fahrdynamikregelung',
                'Elektronische Stabilitätskontrolle',
                'abs'
            ),
            'asr_system': FeatureCapability(
                'asr_system', 'ASR Antriebsschlupfregelung',
                'Verhindert Durchdrehen der Antriebsräder',
                'abs'
            ),
            'ebd_system': FeatureCapability(
                'ebd_system', 'EBD Elektronische Bremskraftverteilung',
                'Optimale Bremskraftverteilung',
                'abs'
            ),
            'ba_system': FeatureCapability(
                'ba_system', 'Bremsassistent',
                'Erkennt Notbremsungen und verstärkt',
                'abs'
            ),
            'ebv_system': FeatureCapability(
                'ebv_system', 'EBV Elektronische Bremskraftverteilung',
                'Verteilung der Bremskraft auf alle Räder',
                'abs'
            ),
            'hdc_system': FeatureCapability(
                'hdc_system', 'HDC Bergabfahrhilfe',
                'Kontrollierte Bergabfahrt ohne Bremspedal',
                'abs'
            ),
            'aeb_system': FeatureCapability(
                'aeb_system', 'AEB Notbremsassistent',
                'Automatische Notbremsung bei Hindernissen',
                'abs'
            ),
            'esp_sport': FeatureCapability(
                'esp_sport', 'ESP Sport Modus',
                'Reduzierte ESP-Eingriffe für sportliches Fahren',
                'abs'
            ),
            'esp_off': FeatureCapability(
                'esp_off', 'ESP Deaktivierung',
                'Vollständige ESP-Abschaltung',
                'abs'
            ),
            'brake_assist': FeatureCapability(
                'brake_assist', 'Erweiterte Bremsunterstützung',
                'Intelligente Bremsdruckmodulation',
                'abs'
            ),
            'cornering_brake': FeatureCapability(
                'cornering_brake', 'Kurvenbremssteuerung',
                'Optimierte Bremsung in Kurven',
                'abs'
            ),
            'load_compensation': FeatureCapability(
                'load_compensation', 'Beladungskompensation',
                'Anpassung an Fahrzeugbeladung',
                'abs'
            ),
            'trailer_stability': FeatureCapability(
                'trailer_stability', 'Anhängerstabilisierung',
                'Stabilisierung beim Ziehen von Anhängern',
                'abs'
            )
        }
        
        # NAC (Network Audio Controller) Features
        nac_features = {
            'dab_radio': FeatureCapability(
                'dab_radio', 'DAB+ Radio',
                'Digitaler Radioempfang aktivieren',
                'nac'
            ),
            'bluetooth_a2dp': FeatureCapability(
                'bluetooth_a2dp', 'Bluetooth Audio',
                'Musik-Streaming über Bluetooth',
                'nac'
            ),
            'bluetooth_hfp': FeatureCapability(
                'bluetooth_hfp', 'Bluetooth Freisprechen',
                'Telefonie über Bluetooth',
                'nac'
            ),
            'usb_audio': FeatureCapability(
                'usb_audio', 'USB Audio',
                'Musikwiedergabe über USB-Anschluss',
                'nac'
            ),
            'voice_recognition': FeatureCapability(
                'voice_recognition', 'Sprachsteuerung',
                'Freisprechanlage mit Spracherkennung',
                'nac'
            ),
            'nac_apps': FeatureCapability(
                'nac_apps', 'NAC Anwendungen',
                'Erweiterte Funktionen des Infotainment-Systems',
                'nac'
            ),
            'mirror_link': FeatureCapability(
                'mirror_link', 'Smartphone Integration',
                'Apple CarPlay / Android Auto',
                'nac'
            ),
            'wifi_hotspot': FeatureCapability(
                'wifi_hotspot', 'WiFi Hotspot',
                'Internet-Hotspot für Passagiere',
                'nac'
            ),
            'streaming_services': FeatureCapability(
                'streaming_services', 'Streaming Dienste',
                'Spotify, Deezer, etc. direkt im Fahrzeug',
                'nac'
            ),
            'navigation_online': FeatureCapability(
                'navigation_online', 'Online Navigation',
                'Echtzeit-Verkehrsdaten und POI-Updates',
                'nac'
            ),
            'weather_service': FeatureCapability(
                'weather_service', 'Wetterdienst',
                'Aktuelle Wetterdaten und Vorhersagen',
                'nac'
            ),
            'news_service': FeatureCapability(
                'news_service', 'Nachrichtendienst',
                'Aktuelle Nachrichten im Fahrzeug',
                'nac'
            ),
            'fuel_prices': FeatureCapability(
                'fuel_prices', 'Tankstellenpreise',
                'Aktuelle Kraftstoffpreise anzeigen',
                'nac'
            ),
            'parking_info': FeatureCapability(
                'parking_info', 'Parkplatz-Information',
                'Verfügbare Parkplätze in der Umgebung',
                'nac'
            ),
            'remote_services': FeatureCapability(
                'remote_services', 'Remote Services',
                'Fernsteuerung über Smartphone-App',
                'nac'
            ),
            'stolen_vehicle': FeatureCapability(
                'stolen_vehicle', 'Diebstahlverfolgung',
                'GPS-Tracking bei Fahrzeugdiebstahl',
                'nac'
            ),
            'emergency_call': FeatureCapability(
                'emergency_call', 'Automatischer Notruf',
                'eCall bei Unfall automatisch',
                'nac'
            ),
            'roadside_assistance': FeatureCapability(
                'roadside_assistance', 'Pannenhilfe',
                'Direkter Kontakt zur Pannenhilfe',
                'nac'
            ),
            'vehicle_health': FeatureCapability(
                'vehicle_health', 'Fahrzeugdiagnose',
                'Remote-Diagnose und Wartungshinweise',
                'nac'
            ),
            'geo_fencing': FeatureCapability(
                'geo_fencing', 'Geo-Fencing',
                'Benachrichtigung bei Verlassen bestimmter Bereiche',
                'nac'
            ),
            'speed_alerts': FeatureCapability(
                'speed_alerts', 'Geschwindigkeitswarnungen',
                'Warnung bei Überschreitung eingestellter Limits',
                'nac'
            ),
            'trip_statistics': FeatureCapability(
                'trip_statistics', 'Fahrtstatistiken',
                'Detaillierte Auswertung der Fahrten',
                'nac'
            ),
            'eco_coaching': FeatureCapability(
                'eco_coaching', 'Eco Coaching',
                'Tipps für sparsames Fahren',
                'nac'
            ),
            'find_my_car': FeatureCapability(
                'find_my_car', 'Fahrzeug finden',
                'GPS-Standort des geparkten Fahrzeugs',
                'nac'
            )
        }
        
        # COMBINE (Instrument Cluster) Features
        combine_features = {
            'digital_speedometer': FeatureCapability(
                'digital_speedometer', 'Digitaler Tacho',
                'Digitale Geschwindigkeitsanzeige',
                'combine'
            ),
            'configurable_display': FeatureCapability(
                'configurable_display', 'Konfigurierbares Display',
                'Anpassbare Instrumentenanzeige',
                'combine'
            ),
            'trip_computer': FeatureCapability(
                'trip_computer', 'Bordcomputer',
                'Detaillierte Verbrauchs- und Fahrtdaten',
                'combine'
            ),
            'warning_symbols': FeatureCapability(
                'warning_symbols', 'Warnsymbole',
                'Erweiterte Warn- und Statussymbole',
                'combine'
            ),
            'service_reminder': FeatureCapability(
                'service_reminder', 'Service-Erinnerung',
                'Automatische Wartungserinnerungen',
                'combine'
            ),
            'gear_indicator': FeatureCapability(
                'gear_indicator', 'Ganganzeige',
                'Aktueller Gang bei Schaltgetriebe',
                'combine'
            ),
            'shift_light': FeatureCapability(
                'shift_light', 'Schaltpunkt-Anzeige',
                'Optimaler Schaltpunkt für Verbrauch',
                'combine'
            ),
            'ambient_lighting': FeatureCapability(
                'ambient_lighting', 'Ambientebeleuchtung',
                'Stimmungsbeleuchtung im Innenraum',
                'combine'
            ),
            'welcome_sequence': FeatureCapability(
                'welcome_sequence', 'Begrüßungssequenz',
                'Animierte Begrüßung beim Einschalten',
                'combine'
            ),
            'night_mode': FeatureCapability(
                'night_mode', 'Nachtmodus',
                'Reduzierte Helligkeit bei Nacht',
                'combine'
            ),
            'custom_themes': FeatureCapability(
                'custom_themes', 'Benutzerdefinierte Themes',
                'Personalisierte Farbschemata',
                'combine'
            ),
            'multi_info_display': FeatureCapability(
                'multi_info_display', 'Multi-Info Display',
                'Erweiterte Fahrzeuginformationen',
                'combine'
            ),
            'tyre_pressure': FeatureCapability(
                'tyre_pressure', 'Reifendruckanzeige',
                'Aktueller Reifendruck aller Räder',
                'combine'
            ),
            'oil_life': FeatureCapability(
                'oil_life', 'Motoröl-Lebensdauer',
                'Verbleibende Ölwechselintervalle',
                'combine'
            ),
            'fuel_range': FeatureCapability(
                'fuel_range', 'Reichweitenanzeige',
                'Geschätzte Reichweite mit aktuellem Tankinhalt',
                'combine'
            ),
            'average_consumption': FeatureCapability(
                'average_consumption', 'Durchschnittsverbrauch',
                'Langzeit-Verbrauchsanzeige',
                'combine'
            ),
            'instant_consumption': FeatureCapability(
                'instant_consumption', 'Momentanverbrauch',
                'Aktueller Kraftstoffverbrauch',
                'combine'
            ),
            'eco_meter': FeatureCapability(
                'eco_meter', 'Eco-Meter',
                'Effizienz der Fahrweise anzeigen',
                'combine'
            ),
            'performance_timer': FeatureCapability(
                'performance_timer', 'Performance Timer',
                '0-100 km/h und andere Messungen',
                'combine'
            ),
            'g_force_meter': FeatureCapability(
                'g_force_meter', 'G-Kraft Anzeige',
                'Beschleunigungs- und Bremskräfte',
                'combine'
            )
        }
        
        # Climate Control Features
        climate_features = {
            'auto_climate': FeatureCapability(
                'auto_climate', 'Automatische Klimaanlage',
                'Klimaanlage mit Temperaturregelung',
                'climate'
            ),
            'dual_zone': FeatureCapability(
                'dual_zone', 'Dual-Zone Klimaautomatik',
                'Getrennte Temperaturregelung Fahrer/Beifahrer',
                'climate'
            ),
            'tri_zone': FeatureCapability(
                'tri_zone', 'Tri-Zone Klimaautomatik',
                'Getrennte Temperaturregelung vorn + hinten',
                'climate'
            ),
            'climate_timer': FeatureCapability(
                'climate_timer', 'Klima-Timer',
                'Klimaanlage vor Fahrtantritt aktivieren',
                'climate'
            ),
            'air_quality': FeatureCapability(
                'air_quality', 'Luftqualitätssensor',
                'Automatischer Umluftbetrieb bei schlechter Luft',
                'climate'
            ),
            'windscreen_heating': FeatureCapability(
                'windscreen_heating', 'Scheibenheizung',
                'Elektrische Windschutzscheibenheizung',
                'climate'
            ),
            'rear_window_heating': FeatureCapability(
                'rear_window_heating', 'Heckscheibenheizung',
                'Beheizung der Heckscheibe',
                'climate'
            ),
            'humidity_sensor': FeatureCapability(
                'humidity_sensor', 'Feuchtigkeitssensor',
                'Automatische Entfeuchtung',
                'climate'
            ),
            'solar_sensor': FeatureCapability(
                'solar_sensor', 'Sonnensensor',
                'Anpassung der Klimaanlage an Sonneneinstrahlung',
                'climate'
            ),
            'cabin_air_filter': FeatureCapability(
                'cabin_air_filter', 'Innenraumfilter-Überwachung',
                'Warnung bei Filterwechsel',
                'climate'
            ),
            'remote_climate': FeatureCapability(
                'remote_climate', 'Fernsteuerung Klimaanlage',
                'Klimaanlage per App steuern',
                'climate'
            ),
            'eco_climate': FeatureCapability(
                'eco_climate', 'Eco Klimamodus',
                'Energieeffiziente Klimaregelung',
                'climate'
            ),
            'rapid_heat': FeatureCapability(
                'rapid_heat', 'Schnellheizung',
                'Schnelle Aufheizung des Innenraums',
                'climate'
            ),
            'rapid_cool': FeatureCapability(
                'rapid_cool', 'Schnellkühlung',
                'Schnelle Abkühlung des Innenraums',
                'climate'
            ),
            'residual_heat': FeatureCapability(
                'residual_heat', 'Restwärme',
                'Nutzung der Motorwärme nach Abstellen',
                'climate'
            )
        }
        
        # Airbag System Features
        airbag_features = {
            'driver_airbag': FeatureCapability(
                'driver_airbag', 'Fahrerairbag',
                'Airbag für Fahrerseite',
                'airbag'
            ),
            'passenger_airbag': FeatureCapability(
                'passenger_airbag', 'Beifahrerairbag',
                'Airbag für Beifahrerseite',
                'airbag'
            ),
            'side_airbags': FeatureCapability(
                'side_airbags', 'Seitenairbags',
                'Seitliche Airbags für Kopf/Körper',
                'airbag'
            ),
            'curtain_airbags': FeatureCapability(
                'curtain_airbags', 'Kopfairbags',
                'Kopfschutz-Airbags (Curtain)',
                'airbag'
            ),
            'knee_airbag': FeatureCapability(
                'knee_airbag', 'Knieairbag',
                'Schutz für Knie des Fahrers',
                'airbag'
            ),
            'passenger_detect': FeatureCapability(
                'passenger_detect', 'Beifahrererkennung',
                'Automatische Erkennung Beifahrer vorhanden',
                'airbag'
            ),
            'child_seat_detect': FeatureCapability(
                'child_seat_detect', 'Kindersitzerkennung',
                'Erkennung und Deaktivierung bei Kindersitz',
                'airbag'
            ),
            'seat_position': FeatureCapability(
                'seat_position', 'Sitzpositionserkennung',
                'Anpassung der Airbag-Auslösung an Sitzposition',
                'airbag'
            ),
            'belt_pretensioner': FeatureCapability(
                'belt_pretensioner', 'Gurtstraffer',
                'Automatisches Straffen der Sicherheitsgurte',
                'airbag'
            ),
            'impact_sensors': FeatureCapability(
                'impact_sensors', 'Aufprallsensoren',
                'Erweiterte Crash-Sensoren',
                'airbag'
            ),
            'rollover_sensor': FeatureCapability(
                'rollover_sensor', 'Überschlagsensor',
                'Erkennung von Fahrzeugüberschlägen',
                'airbag'
            ),
            'multi_stage': FeatureCapability(
                'multi_stage', 'Mehrstufige Airbags',
                'Adaptive Airbag-Auslösung je nach Unfallschwere',
                'airbag'
            )
        }
        
        # Camera/Vision System Features
        camera_features = {
            'backup_camera': FeatureCapability(
                'backup_camera', 'Rückfahrkamera',
                'Kamerabild beim Rückwärtsfahren',
                'camera'
            ),
            'front_camera': FeatureCapability(
                'front_camera', 'Frontkamera',
                'Kamera für Assistenzsysteme',
                'camera'
            ),
            'surround_view': FeatureCapability(
                'surround_view', '360° Kamera',
                'Rundumblick-Kamerasystem',
                'camera'
            ),
            'lane_detection': FeatureCapability(
                'lane_detection', 'Spurerkennung',
                'Automatische Fahrspurerkennung',
                'camera'
            ),
            'traffic_sign': FeatureCapability(
                'traffic_sign', 'Verkehrszeichenerkennung',
                'Erkennung und Anzeige von Verkehrszeichen',
                'camera'
            ),
            'blind_spot_camera': FeatureCapability(
                'blind_spot_camera', 'Totwinkel-Kamera',
                'Kamera für tote Winkel',
                'camera'
            ),
            'driver_monitoring': FeatureCapability(
                'driver_monitoring', 'Fahrerüberwachung',
                'Kamera zur Fahreraufmerksamkeitsüberwachung',
                'camera'
            ),
            'gesture_control': FeatureCapability(
                'gesture_control', 'Gestensteuerung',
                'Steuerung per Handbewegungen',
                'camera'
            ),
            'parking_assist': FeatureCapability(
                'parking_assist', 'Parkassistent',
                'Automatisches Einparken mit Kameraunterstützung',
                'camera'
            ),
            'object_detection': FeatureCapability(
                'object_detection', 'Objekterkennung',
                'Erkennung von Hindernissen und Personen',
                'camera'
            ),
            'night_vision': FeatureCapability(
                'night_vision', 'Nachtsicht',
                'Infrarot-Nachtsichtassistent',
                'camera'
            ),
            'recording_mode': FeatureCapability(
                'recording_mode', 'Dashcam Modus',
                'Aufzeichnung der Fahrt',
                'camera'
            )
        }
        
        # Lighting System Features
        lighting_features = {
            'led_headlights': FeatureCapability(
                'led_headlights', 'LED Scheinwerfer',
                'LED-Hauptscheinwerfer',
                'lighting'
            ),
            'led_drls': FeatureCapability(
                'led_drls', 'LED Tagfahrlicht',
                'LED-Tagfahrlicht aktivieren',
                'lighting'
            ),
            'cornering_lights': FeatureCapability(
                'cornering_lights', 'Abbiegelicht',
                'Zusätzliche Beleuchtung beim Abbiegen',
                'lighting'
            ),
            'adaptive_lighting': FeatureCapability(
                'adaptive_lighting', 'Adaptives Licht',
                'Lichtverteilung passt sich der Fahrsituation an',
                'lighting'
            ),
            'high_beam_assist': FeatureCapability(
                'high_beam_assist', 'Fernlicht-Assistent',
                'Automatisches Fernlicht mit Abblendfunktion',
                'lighting'
            ),
            'matrix_led': FeatureCapability(
                'matrix_led', 'Matrix LED',
                'Selektives Ein-/Ausschalten einzelner LED-Segmente',
                'lighting'
            ),
            'laser_lights': FeatureCapability(
                'laser_lights', 'Laser-Scheinwerfer',
                'Laser-Fernlicht für extreme Reichweite',
                'lighting'
            ),
            'dynamic_indicators': FeatureCapability(
                'dynamic_indicators', 'Dynamische Blinker',
                'Sequenzielle LED-Blinker',
                'lighting'
            ),
            'fog_lights': FeatureCapability(
                'fog_lights', 'Nebelscheinwerfer',
                'Zusätzliche Beleuchtung bei Nebel',
                'lighting'
            ),
            'rear_fog_light': FeatureCapability(
                'rear_fog_light', 'Nebelschlussleuchte',
                'Rückwärtige Nebelleuchte',
                'lighting'
            ),
            'emergency_lights': FeatureCapability(
                'emergency_lights', 'Notbeleuchtung',
                'Automatische Warnblinkanlage bei Notbremsung',
                'lighting'
            ),
            'puddle_lights': FeatureCapability(
                'puddle_lights', 'Pfützenlichter',
                'Bodenbeleuchtung an Türgriffen',
                'lighting'
            ),
            'approach_lights': FeatureCapability(
                'approach_lights', 'Anfahrbeleuchtung',
                'Beleuchtung beim Nähern zum Fahrzeug',
                'lighting'
            ),
            'mood_lighting': FeatureCapability(
                'mood_lighting', 'Stimmungsbeleuchtung',
                'Farbige Innenraumbeleuchtung',
                'lighting'
            )
        }
        
        # Parking/Assistance Features
        parking_features = {
            'parking_sensors_front': FeatureCapability(
                'parking_sensors_front', 'Einparkhilfe vorn',
                'Ultraschallsensoren vorne',
                'parking'
            ),
            'parking_sensors_rear': FeatureCapability(
                'parking_sensors_rear', 'Einparkhilfe hinten',
                'Ultraschallsensoren hinten',
                'parking'
            ),
            'park_assist': FeatureCapability(
                'park_assist', 'Parkassistent',
                'Automatisches Einparken',
                'parking'
            ),
            'perpendicular_park': FeatureCapability(
                'perpendicular_park', 'Querparken',
                'Automatisches Quereinparken',
                'parking'
            ),
            'parallel_park': FeatureCapability(
                'parallel_park', 'Längsparken',
                'Automatisches Längseinparken',
                'parking'
            ),
            'park_out_assist': FeatureCapability(
                'park_out_assist', 'Ausparkassistent',
                'Hilfe beim Ausparken',
                'parking'
            ),
            'remote_park': FeatureCapability(
                'remote_park', 'Ferngesteuertes Parken',
                'Parken per Smartphone ferngesteuert',
                'parking'
            ),
            'trailer_assist': FeatureCapability(
                'trailer_assist', 'Anhänger-Assistent',
                'Rückwärtsfahren mit Anhänger',
                'parking'
            ),
            'curb_warning': FeatureCapability(
                'curb_warning', 'Bordsteinwarnung',
                'Warnung vor Bordsteinkontakt',
                'parking'
            ),
            'garage_door': FeatureCapability(
                'garage_door', 'Garagentor-Öffner',
                'Integrierte Garagentor-Fernbedienung',
                'parking'
            )
        }
        
        # Seats & Comfort Features
        seats_features = {
            'electric_seats': FeatureCapability(
                'electric_seats', 'Elektrische Sitze',
                'Elektrische Sitzverstellung',
                'seats'
            ),
            'memory_seats': FeatureCapability(
                'memory_seats', 'Memory-Sitze',
                'Speicherbare Sitzpositionen',
                'seats'
            ),
            'heated_seats': FeatureCapability(
                'heated_seats', 'Beheizbare Sitze',
                'Sitzheizung vorn und hinten',
                'seats'
            ),
            'ventilated_seats': FeatureCapability(
                'ventilated_seats', 'Belüftete Sitze',
                'Sitzbelüftung für Kühlung',
                'seats'
            ),
            'massage_seats': FeatureCapability(
                'massage_seats', 'Massage-Sitze',
                'Integrierte Massagefunktion',
                'seats'
            ),
            'lumbar_support': FeatureCapability(
                'lumbar_support', 'Lordosenstütze',
                'Elektrische Lordosenstütze',
                'seats'
            ),
            'seat_extension': FeatureCapability(
                'seat_extension', 'Oberschenkelauflage',
                'Verlängerbare Sitzfläche',
                'seats'
            ),
            'easy_entry': FeatureCapability(
                'easy_entry', 'Easy Entry',
                'Automatisches Zurückfahren bei Ausstieg',
                'seats'
            ),
            'seat_belts_height': FeatureCapability(
                'seat_belts_height', 'Gurtverstellung',
                'Höhenverstellbare Sicherheitsgurte',
                'seats'
            )
        }
        
        # Suspension Features
        suspension_features = {
            'adaptive_dampers': FeatureCapability(
                'adaptive_dampers', 'Adaptive Dämpfer',
                'Elektronisch verstellbare Stoßdämpfer',
                'suspension'
            ),
            'air_suspension': FeatureCapability(
                'air_suspension', 'Luftfederung',
                'Luftfederung mit Höhenverstellung',
                'suspension'
            ),
            'active_suspension': FeatureCapability(
                'active_suspension', 'Aktive Federung',
                'Aktiv gesteuerte Federung',
                'suspension'
            ),
            'ride_height': FeatureCapability(
                'ride_height', 'Bodenfreiheit-Verstellung',
                'Variable Bodenfreiheit',
                'suspension'
            ),
            'load_leveling': FeatureCapability(
                'load_leveling', 'Niveauregulierung',
                'Automatische Höhenanpassung bei Beladung',
                'suspension'
            ),
            'sport_suspension': FeatureCapability(
                'sport_suspension', 'Sport-Fahrwerk',
                'Sportlich abgestimmtes Fahrwerk',
                'suspension'
            ),
            'comfort_suspension': FeatureCapability(
                'comfort_suspension', 'Komfort-Fahrwerk',
                'Komfortabel abgestimmtes Fahrwerk',
                'suspension'
            ),
            'electronic_sway_bar': FeatureCapability(
                'electronic_sway_bar', 'Elektronischer Stabilisator',
                'Aktive Wankstabilisierung',
                'suspension'
            )
        }
        
        # Transmission Features
        transmission_features = {
            'paddle_shifters': FeatureCapability(
                'paddle_shifters', 'Schaltwippen',
                'Schaltwippen am Lenkrad',
                'transmission'
            ),
            'sport_mode_trans': FeatureCapability(
                'sport_mode_trans', 'Sport-Modus Getriebe',
                'Sportliche Getriebeprogrammierung',
                'transmission'
            ),
            'eco_mode_trans': FeatureCapability(
                'eco_mode_trans', 'Eco-Modus Getriebe',
                'Sparsame Getriebeprogrammierung',
                'transmission'
            ),
            'manual_mode': FeatureCapability(
                'manual_mode', 'Manueller Modus',
                'Manuelle Gangwahl bei Automatik',
                'transmission'
            ),
            'launch_mode': FeatureCapability(
                'launch_mode', 'Launch Modus',
                'Optimaler Start für Beschleunigung',
                'transmission'
            ),
            'kickdown': FeatureCapability(
                'kickdown', 'Kickdown',
                'Automatisches Herunterschalten bei Vollgas',
                'transmission'
            ),
            'creep_mode': FeatureCapability(
                'creep_mode', 'Kriechgang',
                'Langsames Anfahren ohne Gas',
                'transmission'
            ),
            'hill_start': FeatureCapability(
                'hill_start', 'Berganfahrhilfe Getriebe',
                'Getriebe-integrierte Berganfahrhilfe',
                'transmission'
            )
        }
        
        # Combine all features
        self.available_features = {
            **bsi_features,
            **cmm_features,
            **abs_esp_features,
            **nac_features,
            **combine_features,
            **climate_features,
            **airbag_features,
            **camera_features,
            **lighting_features,
            **parking_features,
            **seats_features,
            **suspension_features,
            **transmission_features
        }
        
        # Set detailed properties for each feature
        self._set_comprehensive_feature_properties()
    
    def _set_comprehensive_feature_properties(self):
        """Setze umfassende Eigenschaften für ALLE Features"""
        
        # BSI Features
        bsi_features_config = {
            'auto_lights': {
                'required_ecus': ['BSI', 'COMBINE'],
                'difficulty': 'easy',
                'warnings': ['Lichtsensor muss vorhanden sein'],
                'compatible_years': [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'auto_wipers': {
                'required_ecus': ['BSI', 'COMBINE'],
                'difficulty': 'easy',
                'warnings': ['Regensensor muss vorhanden sein'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'welcome_lighting': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'follow_me_home': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'auto_door_lock': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'speed_door_lock': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'dependency_features': ['auto_door_lock'],
                'warnings': [],
                'compatible_years': [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'selective_unlock': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'window_comfort': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Elektrische Fensterheber erforderlich'],
                'compatible_years': [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'central_locking': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'deadlock': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Sicherheitsfeature - vorsichtig verwenden'],
                'compatible_years': [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'interior_lighting': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'mirror_fold': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Elektrische Spiegel erforderlich'],
                'compatible_years': [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'mirror_heating': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'seat_heating': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Sitzheizung muss eingebaut sein'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'steering_heating': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Lenkradheizung muss eingebaut sein'],
                'compatible_years': [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'key_card': {
                'required_ecus': ['BSI'],
                'difficulty': 'hard',
                'warnings': ['Keyless System erforderlich', 'Komplex zu aktivieren'],
                'compatible_years': [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'panic_alarm': {
                'required_ecus': ['BSI'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_years': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'perimeter_alarm': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Alarmanlage muss vorhanden sein'],
                'compatible_years': [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'volumetric_alarm': {
                'required_ecus': ['BSI'],
                'difficulty': 'hard',
                'warnings': ['Ultraschallsensoren erforderlich'],
                'compatible_years': [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'tilt_alarm': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Neigungssensor erforderlich'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'electric_windows': {
                'required_ecus': ['BSI'],
                'difficulty': 'medium',
                'warnings': ['Elektrische Fensterheber erforderlich'],
                'compatible_years': [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'sunroof_control': {
                'required_ecus': ['BSI'],
                'difficulty': 'hard',
                'warnings': ['Schiebedach muss eingebaut sein'],
                'compatible_years': [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'tailgate_control': {
                'required_ecus': ['BSI'],
                'difficulty': 'hard',
                'warnings': ['Elektrische Heckklappe erforderlich'],
                'compatible_years': [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            }
        }
        
        # CMM Features  
        cmm_features_config = {
            'stop_start': {
                'required_ecus': ['CMM', 'BSI'],
                'difficulty': 'medium',
                'warnings': ['Nicht bei allen Motoren verfügbar'],
                'compatible_engines': ['1.2 PureTech', '1.6 THP', '1.6 HDi', '2.0 HDi', '1.5 BlueHDi'],
                'compatible_years': [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'eco_mode': {
                'required_ecus': ['CMM', 'COMBINE'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_engines': ['1.2 PureTech', '1.6 THP', '1.6 HDi', '2.0 HDi', '1.5 BlueHDi'],
                'compatible_years': [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'sport_mode': {
                'required_ecus': ['CMM', 'COMBINE'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_engines': ['1.6 THP', '2.0 THP', '1.6 THP 200'],
                'compatible_years': [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'dpf_regen': {
                'required_ecus': ['CMM', 'COMBINE'],
                'difficulty': 'medium',
                'warnings': ['Nur bei Dieselmotoren', 'Nicht während Fahrt'],
                'compatible_engines': ['1.6 HDi', '2.0 HDi', '1.5 BlueHDi', '2.0 BlueHDi'],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'engine_braking': {
                'required_ecus': ['CMM'],
                'difficulty': 'medium',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'cruise_control': {
                'required_ecus': ['CMM', 'BSI', 'COMBINE'],
                'difficulty': 'medium',
                'dependency_features': ['speed_limiter'],
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'speed_limiter': {
                'required_ecus': ['CMM', 'COMBINE'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'adaptive_cruise': {
                'required_ecus': ['CMM', 'BSI', 'COMBINE', 'CAMERA'],
                'difficulty': 'hard',
                'dependency_features': ['cruise_control', 'front_camera'],
                'warnings': ['Frontkamera erforderlich'],
                'compatible_engines': ['ALL'],
                'compatible_years': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'launch_control': {
                'required_ecus': ['CMM', 'ABS'],
                'difficulty': 'hard',
                'warnings': ['Nur für Sportmodelle', 'Getriebeverschleiß möglich'],
                'compatible_engines': ['1.6 THP 200', '2.0 THP'],
                'compatible_years': [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'traction_control': {
                'required_ecus': ['CMM', 'ABS'],
                'difficulty': 'medium',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'throttle_mapping': {
                'required_ecus': ['CMM'],
                'difficulty': 'hard',
                'warnings': ['Kann Fahrverhalten stark verändern'],
                'compatible_engines': ['ALL'],
                'compatible_years': [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'auto_hold': {
                'required_ecus': ['CMM', 'ABS', 'BSI'],
                'difficulty': 'medium',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'hill_assist': {
                'required_ecus': ['CMM', 'ABS'],
                'difficulty': 'easy',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'rev_matching': {
                'required_ecus': ['CMM'],
                'difficulty': 'hard',
                'warnings': ['Nur bei Schaltgetriebe'],
                'compatible_engines': ['1.6 THP', '2.0 THP'],
                'compatible_years': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'overboost': {
                'required_ecus': ['CMM'],
                'difficulty': 'hard',
                'warnings': ['Nur bei Turbomotoren', 'Verschleiß möglich'],
                'compatible_engines': ['1.6 THP', '2.0 THP', '1.6 HDi', '2.0 HDi'],
                'compatible_years': [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'exhaust_valve': {
                'required_ecus': ['CMM'],
                'difficulty': 'hard',
                'warnings': ['Auspuffklappenventil erforderlich'],
                'compatible_engines': ['1.6 THP 200', '2.0 THP'],
                'compatible_years': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'cold_start': {
                'required_ecus': ['CMM'],
                'difficulty': 'medium',
                'warnings': [],
                'compatible_engines': ['ALL'],
                'compatible_years': [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'adblue_heating': {
                'required_ecus': ['CMM'],
                'difficulty': 'medium',
                'warnings': ['Nur bei SCR-Dieseln'],
                'compatible_engines': ['1.5 BlueHDi', '2.0 BlueHDi'],
                'compatible_years': [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'glow_plug': {
                'required_ecus': ['CMM'],
                'difficulty': 'medium',
                'warnings': ['Nur bei Dieselmotoren'],
                'compatible_engines': ['1.6 HDi', '2.0 HDi', '1.5 BlueHDi', '2.0 BlueHDi'],
                'compatible_years': [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            },
            'turbo_lag': {
                'required_ecus': ['CMM'],
                'difficulty': 'hard',
                'warnings': ['Nur bei Turbomotoren', 'Experimental'],
                'compatible_engines': ['1.6 THP', '2.0 THP', '1.6 HDi', '2.0 HDi'],
                'compatible_years': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
            }
        }
        
        # Apply configurations to features
        for feature_id, config in bsi_features_config.items():
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = config['required_ecus']
                feature.difficulty_level = config['difficulty']
                feature.warnings = config['warnings']
                feature.compatible_years = config['compatible_years']
                if 'dependency_features' in config:
                    feature.dependency_features = config['dependency_features']
        
        for feature_id, config in cmm_features_config.items():
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = config['required_ecus']
                feature.difficulty_level = config['difficulty']
                feature.warnings = config['warnings']
                feature.compatible_years = config['compatible_years']
                feature.compatible_engines = config['compatible_engines']
                if 'dependency_features' in config:
                    feature.dependency_features = config['dependency_features']
        
        # Quick configuration for other ECU features
        self._configure_remaining_features()
    
    def _configure_remaining_features(self):
        """Konfiguriere verbleibende Features schnell"""
        
        # ABS/ESP Features
        abs_features = ['abs_system', 'esp_system', 'asr_system', 'ebd_system', 'ba_system', 
                       'ebv_system', 'hdc_system', 'aeb_system', 'esp_sport', 'esp_off',
                       'brake_assist', 'cornering_brake', 'load_compensation', 'trailer_stability']
        
        for feature_id in abs_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['ABS']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2005, 2025))
                if 'esp' in feature_id or 'aeb' in feature_id:
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2008, 2025))
        
        # NAC Features
        nac_features = ['dab_radio', 'bluetooth_a2dp', 'bluetooth_hfp', 'usb_audio', 'voice_recognition',
                       'nac_apps', 'mirror_link', 'wifi_hotspot', 'streaming_services', 'navigation_online',
                       'weather_service', 'news_service', 'fuel_prices', 'parking_info', 'remote_services',
                       'stolen_vehicle', 'emergency_call', 'roadside_assistance', 'vehicle_health',
                       'geo_fencing', 'speed_alerts', 'trip_statistics', 'eco_coaching', 'find_my_car']
        
        for feature_id in nac_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['NAC']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2010, 2025))
                if any(x in feature_id for x in ['wifi', 'streaming', 'online', 'remote']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2014, 2025))
        
        # COMBINE Features
        combine_features = ['digital_speedometer', 'configurable_display', 'trip_computer', 'warning_symbols',
                           'service_reminder', 'gear_indicator', 'shift_light', 'ambient_lighting',
                           'welcome_sequence', 'night_mode', 'custom_themes', 'multi_info_display',
                           'tyre_pressure', 'oil_life', 'fuel_range', 'average_consumption',
                           'instant_consumption', 'eco_meter', 'performance_timer', 'g_force_meter']
        
        for feature_id in combine_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['COMBINE']
                feature.difficulty_level = 'easy'
                feature.compatible_years = list(range(2008, 2025))
                if any(x in feature_id for x in ['configurable', 'custom', 'performance', 'g_force']):
                    feature.difficulty_level = 'medium'
                    feature.compatible_years = list(range(2012, 2025))
        
        # Climate Features
        climate_features = ['auto_climate', 'dual_zone', 'tri_zone', 'climate_timer', 'air_quality',
                           'windscreen_heating', 'rear_window_heating', 'humidity_sensor', 'solar_sensor',
                           'cabin_air_filter', 'remote_climate', 'eco_climate', 'rapid_heat',
                           'rapid_cool', 'residual_heat']
        
        for feature_id in climate_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['CLIMATE']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2006, 2025))
                if any(x in feature_id for x in ['dual', 'tri', 'remote']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2010, 2025))
        
        # Airbag Features
        airbag_features = ['driver_airbag', 'passenger_airbag', 'side_airbags', 'curtain_airbags',
                          'knee_airbag', 'passenger_detect', 'child_seat_detect', 'seat_position',
                          'belt_pretensioner', 'impact_sensors', 'rollover_sensor', 'multi_stage']
        
        for feature_id in airbag_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['AIRBAG']
                feature.difficulty_level = 'hard'
                feature.warnings = ['Sicherheitssystem - nur von Experten']
                feature.compatible_years = list(range(2004, 2025))
                if any(x in feature_id for x in ['driver', 'passenger']):
                    feature.compatible_years = list(range(2000, 2025))
        
        # Camera Features
        camera_features = ['backup_camera', 'front_camera', 'surround_view', 'lane_detection',
                          'traffic_sign', 'blind_spot_camera', 'driver_monitoring', 'gesture_control',
                          'parking_assist', 'object_detection', 'night_vision', 'recording_mode']
        
        for feature_id in camera_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['CAMERA']
                feature.difficulty_level = 'hard'
                feature.compatible_years = list(range(2012, 2025))
                if 'backup' in feature_id:
                    feature.difficulty_level = 'medium'
                    feature.compatible_years = list(range(2008, 2025))
        
        # Lighting Features
        lighting_features = ['led_headlights', 'led_drls', 'cornering_lights', 'adaptive_lighting',
                            'high_beam_assist', 'matrix_led', 'laser_lights', 'dynamic_indicators',
                            'fog_lights', 'rear_fog_light', 'emergency_lights', 'puddle_lights',
                            'approach_lights', 'mood_lighting']
        
        for feature_id in lighting_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['BSI']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2008, 2025))
                if any(x in feature_id for x in ['matrix', 'laser', 'adaptive']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2015, 2025))
        
        # Parking Features
        parking_features = ['parking_sensors_front', 'parking_sensors_rear', 'park_assist',
                           'perpendicular_park', 'parallel_park', 'park_out_assist', 'remote_park',
                           'trailer_assist', 'curb_warning', 'garage_door']
        
        for feature_id in parking_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['BSI', 'PARKING']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2008, 2025))
                if any(x in feature_id for x in ['park_assist', 'remote']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2014, 2025))
        
        # Seats Features
        seats_features = ['electric_seats', 'memory_seats', 'heated_seats', 'ventilated_seats',
                         'massage_seats', 'lumbar_support', 'seat_extension', 'easy_entry',
                         'seat_belts_height']
        
        for feature_id in seats_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['BSI', 'SEATS']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2008, 2025))
                if any(x in feature_id for x in ['massage', 'ventilated']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2015, 2025))
        
        # Suspension Features
        suspension_features = ['adaptive_dampers', 'air_suspension', 'active_suspension', 'ride_height',
                              'load_leveling', 'sport_suspension', 'comfort_suspension', 'electronic_sway_bar']
        
        for feature_id in suspension_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['SUSPENSION']
                feature.difficulty_level = 'hard'
                feature.warnings = ['Fahrwerk-Änderungen nur von Experten']
                feature.compatible_years = list(range(2010, 2025))
                if 'active' in feature_id:
                    feature.compatible_years = list(range(2018, 2025))
        
        # Transmission Features
        transmission_features = ['paddle_shifters', 'sport_mode_trans', 'eco_mode_trans', 'manual_mode',
                                'launch_mode', 'kickdown', 'creep_mode', 'hill_start']
        
        for feature_id in transmission_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                feature.required_ecus = ['TRANSMISSION']
                feature.difficulty_level = 'medium'
                feature.compatible_years = list(range(2008, 2025))
                if any(x in feature_id for x in ['launch', 'paddle']):
                    feature.difficulty_level = 'hard'
                    feature.compatible_years = list(range(2012, 2025))
    
    def initialize_dependency_mapping(self):
        """Initialisiere UMFASSENDE Cross-ECU Abhängigkeiten für ALLE Features"""
        
        self.activation_dependencies = {
            # BSI Dependencies
            'auto_lights': CrossECUDependency(
                'BSI', ['COMBINE'], 
                'BSI verarbeitet Lichtsensor und steuert COMBINE-Anzeige'
            ),
            'auto_wipers': CrossECUDependency(
                'BSI', ['COMBINE'],
                'BSI verarbeitet Regensensor-Signal für COMBINE'
            ),
            'window_comfort': CrossECUDependency(
                'BSI', ['CMM'],
                'BSI kommuniziert mit CMM für Fensterheber-Steuerung'
            ),
            'mirror_fold': CrossECUDependency(
                'BSI', ['CMM'],
                'BSI benötigt Fahrzeuggeschwindigkeit von CMM für automatisches Klappen'
            ),
            'key_card': CrossECUDependency(
                'BSI', ['CMM', 'COMBINE'],
                'Keyless Entry benötigt Motor- und Anzeige-Status'
            ),
            
            # CMM Dependencies
            'cruise_control': CrossECUDependency(
                'CMM', ['BSI', 'COMBINE', 'ABS'],
                'Tempomat erfordert Koordination zwischen Motor, BSI, Anzeige und ABS'
            ),
            'adaptive_cruise': CrossECUDependency(
                'CMM', ['BSI', 'COMBINE', 'ABS', 'CAMERA'],
                'Adaptiver Tempomat benötigt zusätzlich Kameradaten'
            ),
            'stop_start': CrossECUDependency(
                'CMM', ['BSI', 'COMBINE'],
                'Start-Stop benötigt BSI-Status und COMBINE-Anzeige'
            ),
            'launch_control': CrossECUDependency(
                'CMM', ['ABS', 'TRANSMISSION'],
                'Launch Control koordiniert Motor, ABS und Getriebe'
            ),
            'auto_hold': CrossECUDependency(
                'CMM', ['ABS', 'BSI'],
                'Auto Hold verbindet Motor, Bremsen und BSI'
            ),
            'hill_assist': CrossECUDependency(
                'CMM', ['ABS'],
                'Berganfahrhilfe koordiniert Motor und Bremssystem'
            ),
            'traction_control': CrossECUDependency(
                'CMM', ['ABS'],
                'Traktionskontrolle verbindet Motor und ABS'
            ),
            'dpf_regen': CrossECUDependency(
                'CMM', ['COMBINE'],
                'DPF-Regeneration zeigt Status in COMBINE an'
            ),
            'eco_mode': CrossECUDependency(
                'CMM', ['COMBINE', 'TRANSMISSION'],
                'ECO-Modus koordiniert Motor, Anzeige und Getriebe'
            ),
            'sport_mode': CrossECUDependency(
                'CMM', ['COMBINE', 'TRANSMISSION', 'SUSPENSION'],
                'Sport-Modus aktiviert Motor, Getriebe und Fahrwerk'
            ),
            
            # ABS/ESP Dependencies
            'esp_system': CrossECUDependency(
                'ABS', ['CMM', 'BSI'],
                'ESP koordiniert mit Motor und BSI für Fahrstabilität'
            ),
            'aeb_system': CrossECUDependency(
                'ABS', ['CAMERA', 'CMM'],
                'Notbremsassistent benötigt Kamera und Motorsteuerung'
            ),
            'trailer_stability': CrossECUDependency(
                'ABS', ['CMM', 'BSI'],
                'Anhängerstabilisierung koordiniert Bremsen, Motor und BSI'
            ),
            'cornering_brake': CrossECUDependency(
                'ABS', ['BSI'],
                'Kurvenbremssteuerung benötigt Lenkwinkeldaten vom BSI'
            ),
            
            # NAC Dependencies
            'nac_apps': CrossECUDependency(
                'NAC', ['BSI', 'COMBINE'],
                'NAC-Apps benötigen Fahrzeugstatus von BSI und COMBINE'
            ),
            'bluetooth_a2dp': CrossECUDependency(
                'NAC', ['BSI'],
                'Bluetooth Audio benötigt Zündungsstatus von BSI'
            ),
            'voice_recognition': CrossECUDependency(
                'NAC', ['BSI', 'COMBINE'],
                'Sprachsteuerung benötigt BSI- und COMBINE-Integration'
            ),
            'mirror_link': CrossECUDependency(
                'NAC', ['BSI', 'COMBINE'],
                'Smartphone Integration benötigt BSI und COMBINE'
            ),
            'navigation_online': CrossECUDependency(
                'NAC', ['BSI', 'CMM'],
                'Online-Navigation benötigt BSI und Fahrdaten vom CMM'
            ),
            'remote_services': CrossECUDependency(
                'NAC', ['BSI', 'CMM', 'CLIMATE'],
                'Remote Services steuern BSI, Motor und Klimaanlage'
            ),
            'emergency_call': CrossECUDependency(
                'NAC', ['BSI', 'AIRBAG'],
                'eCall benötigt BSI-Status und Airbag-Sensoren'
            ),
            'stolen_vehicle': CrossECUDependency(
                'NAC', ['BSI', 'CMM'],
                'Diebstahlverfolgung koordiniert mit BSI und Motor'
            ),
            'speed_alerts': CrossECUDependency(
                'NAC', ['CMM', 'COMBINE'],
                'Geschwindigkeitswarnungen benötigen CMM und COMBINE'
            ),
            
            # COMBINE Dependencies
            'configurable_display': CrossECUDependency(
                'COMBINE', ['BSI', 'CMM'],
                'Konfigurierbares Display benötigt BSI- und Motor-Daten'
            ),
            'tyre_pressure': CrossECUDependency(
                'COMBINE', ['BSI'],
                'Reifendruckanzeige erhält Daten über BSI'
            ),
            'service_reminder': CrossECUDependency(
                'COMBINE', ['CMM'],
                'Service-Erinnerung basiert auf Motor-Betriebsdaten'
            ),
            'performance_timer': CrossECUDependency(
                'COMBINE', ['CMM', 'ABS'],
                'Performance Timer benötigt Motor- und ABS-Daten'
            ),
            'g_force_meter': CrossECUDependency(
                'COMBINE', ['ABS'],
                'G-Kraft Anzeige erhält Daten vom ABS'
            ),
            'shift_light': CrossECUDependency(
                'COMBINE', ['CMM'],
                'Schaltpunkt-Anzeige benötigt Motor-Daten'
            ),
            
            # Climate Dependencies
            'dual_zone': CrossECUDependency(
                'CLIMATE', ['BSI'],
                'Dual-Zone Klimaautomatik benötigt BSI für Sensorendaten'
            ),
            'remote_climate': CrossECUDependency(
                'CLIMATE', ['BSI', 'NAC'],
                'Fernsteuerung der Klimaanlage über NAC und BSI'
            ),
            'auto_climate': CrossECUDependency(
                'CLIMATE', ['BSI', 'CMM'],
                'Auto-Klimaanlage benötigt BSI-Sensoren und Motor-Status'
            ),
            'air_quality': CrossECUDependency(
                'CLIMATE', ['BSI'],
                'Luftqualitätssensor wird über BSI gesteuert'
            ),
            
            # Camera Dependencies
            'surround_view': CrossECUDependency(
                'CAMERA', ['NAC', 'BSI'],
                '360° Kamera benötigt NAC für Display und BSI für Steuerung'
            ),
            'lane_detection': CrossECUDependency(
                'CAMERA', ['COMBINE', 'ABS'],
                'Spurerkennung zeigt Warnung in COMBINE und kann ABS aktivieren'
            ),
            'traffic_sign': CrossECUDependency(
                'CAMERA', ['COMBINE', 'NAC'],
                'Verkehrszeichenerkennung zeigt Daten in COMBINE und NAC'
            ),
            'driver_monitoring': CrossECUDependency(
                'CAMERA', ['BSI', 'COMBINE'],
                'Fahrerüberwachung benötigt BSI und zeigt Status in COMBINE'
            ),
            'parking_assist': CrossECUDependency(
                'CAMERA', ['BSI', 'ABS', 'CMM'],
                'Parkassistent koordiniert Kamera, BSI, Bremsen und Motor'
            ),
            'night_vision': CrossECUDependency(
                'CAMERA', ['NAC', 'BSI'],
                'Nachtsicht zeigt Bild in NAC und wird über BSI gesteuert'
            ),
            
            # Lighting Dependencies
            'adaptive_lighting': CrossECUDependency(
                'BSI', ['CMM', 'ABS'],
                'Adaptives Licht benötigt Geschwindigkeit von CMM und Lenkwinkel von ABS'
            ),
            'matrix_led': CrossECUDependency(
                'BSI', ['CAMERA'],
                'Matrix LED benötigt Kameradaten für Gegenverkehrserkennung'
            ),
            'high_beam_assist': CrossECUDependency(
                'BSI', ['CAMERA'],
                'Fernlicht-Assistent benötigt Kamera für Fahrzeugerkennung'
            ),
            'cornering_lights': CrossECUDependency(
                'BSI', ['CMM'],
                'Abbiegelicht benötigt Lenkwinkeldaten'
            ),
            'dynamic_indicators': CrossECUDependency(
                'BSI', ['CMM'],
                'Dynamische Blinker synchronisieren mit Fahrzeuggeschwindigkeit'
            ),
            
            # Parking Dependencies
            'park_assist': CrossECUDependency(
                'BSI', ['CAMERA', 'ABS', 'CMM'],
                'Parkassistent koordiniert Sensoren, Kamera, Bremsen und Lenkung'
            ),
            'remote_park': CrossECUDependency(
                'BSI', ['NAC', 'CAMERA', 'ABS', 'CMM'],
                'Ferngesteuertes Parken benötigt alle Fahrsysteme'
            ),
            'parallel_park': CrossECUDependency(
                'BSI', ['CMM', 'ABS'],
                'Längsparken steuert Motor und Bremsen'
            ),
            'trailer_assist': CrossECUDependency(
                'BSI', ['CAMERA', 'CMM'],
                'Anhänger-Assistent benötigt Kamera und Motorsteuerung'
            ),
            
            # Seats Dependencies
            'memory_seats': CrossECUDependency(
                'BSI', ['NAC'],
                'Memory-Sitze können über NAC-System programmiert werden'
            ),
            'heated_seats': CrossECUDependency(
                'BSI', ['CLIMATE'],
                'Sitzheizung koordiniert mit Klimaanlage'
            ),
            'massage_seats': CrossECUDependency(
                'BSI', ['NAC'],
                'Massage-Sitze werden über NAC gesteuert'
            ),
            
            # Suspension Dependencies
            'adaptive_dampers': CrossECUDependency(
                'SUSPENSION', ['CMM', 'ABS'],
                'Adaptive Dämpfer reagieren auf Motor- und Fahrdaten'
            ),
            'air_suspension': CrossECUDependency(
                'SUSPENSION', ['BSI', 'CMM'],
                'Luftfederung benötigt BSI-Sensoren und Motor-Status'
            ),
            'active_suspension': CrossECUDependency(
                'SUSPENSION', ['CMM', 'ABS', 'BSI'],
                'Aktive Federung koordiniert mit Motor, ABS und BSI'
            ),
            'sport_suspension': CrossECUDependency(
                'SUSPENSION', ['CMM'],
                'Sport-Fahrwerk synchronisiert mit Motor-Sportmodus'
            ),
            
            # Transmission Dependencies
            'paddle_shifters': CrossECUDependency(
                'TRANSMISSION', ['CMM', 'COMBINE'],
                'Schaltwippen kommunizieren mit Motor und Anzeige'
            ),
            'launch_mode': CrossECUDependency(
                'TRANSMISSION', ['CMM', 'ABS'],
                'Launch Modus koordiniert Getriebe, Motor und ABS'
            ),
            'sport_mode_trans': CrossECUDependency(
                'TRANSMISSION', ['CMM', 'COMBINE'],
                'Sport-Getriebe synchronisiert mit Motor und Anzeige'
            ),
            'manual_mode': CrossECUDependency(
                'TRANSMISSION', ['COMBINE'],
                'Manueller Modus zeigt Gangwahl in COMBINE'
            ),
            
            # Airbag Dependencies (kritisch!)
            'passenger_detect': CrossECUDependency(
                'AIRBAG', ['BSI'],
                'Beifahrererkennung kommuniziert mit BSI'
            ),
            'child_seat_detect': CrossECUDependency(
                'AIRBAG', ['BSI'],
                'Kindersitzerkennung deaktiviert über BSI'
            ),
            'multi_stage': CrossECUDependency(
                'AIRBAG', ['CMM', 'ABS'],
                'Mehrstufige Airbags benötigen Crash-Daten von CMM und ABS'
            ),
            'rollover_sensor': CrossECUDependency(
                'AIRBAG', ['ABS'],
                'Überschlagsensor koordiniert mit ABS-Sensoren'
            )
        }
    
    def analyze_vehicle_capabilities(self, vehicle_profile, detected_ecus):
        """Analysiere Fahrzeugfähigkeiten mit Hardware-Validierung"""
        self.current_vehicle = vehicle_profile
        self.detected_ecus = detected_ecus
        
        available_features = {}
        hardware_status = {}
        
        # Gehe durch alle Features
        for feature_id, feature in self.available_features.items():
            capability_result = self._check_feature_capability(feature, vehicle_profile, detected_ecus)
            
            # Hardware-Überprüfung wenn Hardware Checker verfügbar
            hardware_validation = None
            if self.hardware_checker and HARDWARE_CHECKER_AVAILABLE:
                hardware_validation = self.hardware_checker.check_hardware_for_feature(
                    feature_id, detected_ecus, vehicle_profile
                )
                hardware_status[feature_id] = hardware_validation
            
            # Feature ist nur verfügbar wenn sowohl ECU-Check als auch Hardware-Check erfolgreich
            feature_available = capability_result['available']
            if hardware_validation:
                feature_available = feature_available and hardware_validation.is_available
            
            if feature_available:
                feature_info = {
                    'feature': feature,
                    'compatibility': capability_result['compatibility'],
                    'missing_requirements': capability_result['missing_requirements'],
                    'dependencies': self._analyze_feature_dependencies(feature_id),
                    'activation_complexity': capability_result['complexity'],
                    'hardware_status': 'verified' if hardware_validation and hardware_validation.is_available else 'not_checked'
                }
                
                # Hardware-spezifische Informationen hinzufügen
                if hardware_validation:
                    feature_info['hardware_confidence'] = hardware_validation.confidence_level
                    feature_info['hardware_details'] = hardware_validation.detection_details
                
                available_features[feature_id] = feature_info
        
        result = {
            'vehicle': vehicle_profile.name if vehicle_profile else 'Unknown',
            'total_features': len(self.available_features),
            'available_features': len(available_features),
            'features': available_features,
            'detected_ecus': detected_ecus,
            'hardware_status': hardware_status,
            'recommendations': self._generate_recommendations(available_features),
            'hardware_checker_available': HARDWARE_CHECKER_AVAILABLE
        }
        
        self.vehicleDetected.emit(result)
        return result
    
    def _check_feature_capability(self, feature, vehicle_profile, detected_ecus):
        """Prüfe Feature-Fähigkeit für Fahrzeug"""
        
        # Extract ECU names from detected ECUs
        detected_ecu_names = []
        for ecu in detected_ecus:
            if isinstance(ecu, dict):
                ecu_name = ecu.get('name', '').upper()
                if any(keyword in ecu_name for keyword in ['BSI', 'NAC', 'CMM', 'ABS', 'COMBINE', 'CLIMATE']):
                    for keyword in ['BSI', 'NAC', 'CMM', 'ABS', 'COMBINE', 'CLIMATE']:
                        if keyword in ecu_name:
                            detected_ecu_names.append(keyword)
                            break
        
        # Check required ECUs
        missing_ecus = []
        for required_ecu in feature.required_ecus:
            if required_ecu not in detected_ecu_names:
                missing_ecus.append(required_ecu)
        
        # Vehicle compatibility check
        compatibility_score = 100
        compatibility_issues = []
        
        if vehicle_profile:
            # Check production year compatibility
            if feature.compatible_years:
                vehicle_years = vehicle_profile.production_years
                if '-' in vehicle_years:
                    start_year, end_year = vehicle_years.split('-')
                    try:
                        start_year = int(start_year)
                        end_year = int(end_year) if end_year.isdigit() else 2024
                        
                        feature_year_compatible = False
                        for year_range in feature.compatible_years:
                            if start_year <= year_range <= end_year:
                                feature_year_compatible = True
                                break
                        
                        if not feature_year_compatible:
                            compatibility_score -= 30
                            compatibility_issues.append("Baujahr nicht optimal kompatibel")
                    except:
                        pass
            
            # Check engine compatibility  
            if feature.compatible_engines:
                vehicle_engines = vehicle_profile.engine_variants.keys() if hasattr(vehicle_profile, 'engine_variants') else []
                engine_compatible = any(
                    engine_type in str(vehicle_engines) 
                    for engine_type in feature.compatible_engines
                )
                
                if not engine_compatible:
                    compatibility_score -= 20
                    compatibility_issues.append("Motor möglicherweise nicht kompatibel")
        
        # Determine complexity
        complexity = "easy"
        if len(missing_ecus) > 0:
            complexity = "impossible"
        elif len(feature.required_ecus) > 2:
            complexity = "medium" 
        elif feature.dependency_features:
            complexity = "medium"
        
        return {
            'available': len(missing_ecus) == 0,
            'compatibility': compatibility_score,
            'missing_requirements': missing_ecus + compatibility_issues,
            'complexity': complexity
        }
    
    def _analyze_feature_dependencies(self, feature_id):
        """Analysiere Feature-Abhängigkeiten"""
        dependencies = {}
        
        # Direct feature dependencies
        feature = self.available_features[feature_id]
        for dep_feature_id in feature.dependency_features:
            if dep_feature_id in self.available_features:
                dependencies[dep_feature_id] = {
                    'name': self.available_features[dep_feature_id].user_friendly_name,
                    'required': True,
                    'description': f"Benötigt {self.available_features[dep_feature_id].user_friendly_name}"
                }
        
        # Cross-ECU dependencies
        if feature_id in self.activation_dependencies:
            cross_ecu_dep = self.activation_dependencies[feature_id]
            dependencies['cross_ecu'] = {
                'primary_ecu': cross_ecu_dep.primary_ecu,
                'secondary_ecus': cross_ecu_dep.secondary_ecus,
                'description': cross_ecu_dep.description
            }
        
        return dependencies
    
    def _generate_recommendations(self, available_features):
        """Generiere Empfehlungen für Benutzer"""
        recommendations = []
        
        # Category-based recommendations
        categories = {}
        for feature_id, feature_info in available_features.items():
            category = feature_info['feature'].category
            if category not in categories:
                categories[category] = []
            categories[category].append(feature_info)
        
        # Recommend easy wins first
        easy_features = [
            f for f in available_features.values() 
            if f['activation_complexity'] == 'easy'
        ]
        
        if easy_features:
            recommendations.append({
                'type': 'quick_wins',
                'title': 'Schnell aktivierbare Features',
                'description': f'{len(easy_features)} Features können einfach aktiviert werden',
                'features': [f['feature'].feature_id for f in easy_features[:3]]
            })
        
        # Recommend by category
        for category, features in categories.items():
            if len(features) >= 2:
                category_names = {
                    'comfort': 'Komfort & Bequemlichkeit',
                    'audio': 'Audio & Unterhaltung', 
                    'safety': 'Sicherheit & Assistenz',
                    'lighting': 'Beleuchtung',
                    'engine': 'Motor & Fahrleistung',
                    'climate': 'Klima & Umgebung'
                }
                
                recommendations.append({
                    'type': 'category',
                    'title': f'{category_names.get(category, category.title())} Features',
                    'description': f'{len(features)} Features in dieser Kategorie verfügbar',
                    'features': [f['feature'].feature_id for f in features]
                })
        
        return recommendations
    
    def create_activation_plan(self, selected_features):
        """Erstelle Aktivierungsplan für ausgewählte Features"""
        plan = {
            'features': selected_features,
            'total_steps': 0,
            'estimated_time': 0,
            'activation_order': [],
            'warnings': [],
            'ecu_sessions_required': set()
        }
        
        # Analyze dependencies and create order
        ordered_features = self._resolve_activation_order(selected_features)
        plan['activation_order'] = ordered_features
        
        # Calculate time and steps
        for feature_id in ordered_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                plan['total_steps'] += len(feature.activation_steps) or 3  # Default 3 steps
                
                # Add ECU sessions required
                for ecu in feature.required_ecus:
                    plan['ecu_sessions_required'].add(ecu)
                
                # Collect warnings
                plan['warnings'].extend(feature.warnings)
        
        # Estimate time (2 minutes per feature + 1 minute per ECU session)
        plan['estimated_time'] = len(ordered_features) * 2 + len(plan['ecu_sessions_required']) * 1
        
        return plan
    
    def _resolve_activation_order(self, selected_features):
        """Löse Aktivierungsreihenfolge mit Abhängigkeiten auf"""
        ordered = []
        remaining = selected_features.copy()
        
        while remaining:
            # Find features with no unresolved dependencies
            ready_features = []
            for feature_id in remaining:
                feature = self.available_features[feature_id]
                dependencies_satisfied = True
                
                for dep_feature_id in feature.dependency_features:
                    if dep_feature_id in selected_features and dep_feature_id not in ordered:
                        dependencies_satisfied = False
                        break
                
                if dependencies_satisfied:
                    ready_features.append(feature_id)
            
            if not ready_features:
                # Circular dependency or unresolvable - add remaining
                ready_features = remaining
            
            # Add ready features to order
            for feature_id in ready_features:
                ordered.append(feature_id)
                remaining.remove(feature_id)
        
        return ordered
    
    def check_multi_ecu_activation_compatibility(self, selected_features):
        """Prüfe Multi-ECU Aktivierungs-Kompatibilität"""
        
        if not self.hardware_checker or not HARDWARE_CHECKER_AVAILABLE:
            return {
                'compatible': True,
                'message': 'Hardware checker not available - proceeding without validation'
            }
        
        self.activationMessage.emit("Prüfe Multi-ECU Kompatibilität...")
        
        # Prüfe Hardware-Kompatibilität für alle Features
        compatibility_result = self.hardware_checker.check_multi_ecu_hardware_compatibility(
            selected_features, self.detected_ecus, self.current_vehicle
        )
        
        overall_compatibility = compatibility_result['overall_compatibility']
        hardware_conflicts = compatibility_result['hardware_conflicts']
        
        if overall_compatibility < 0.8:
            return {
                'compatible': False,
                'message': f'Hardware-Kompatibilität nur {overall_compatibility*100:.1f}%',
                'details': compatibility_result
            }
        
        if hardware_conflicts:
            return {
                'compatible': True,
                'requires_sequential': True,
                'message': f'{len(hardware_conflicts)} Hardware-Konflikte erkannt - sequenzielle Aktivierung erforderlich',
                'conflicts': hardware_conflicts,
                'details': compatibility_result
            }
        
        return {
            'compatible': True,
            'requires_sequential': False,
            'message': 'Multi-ECU Aktivierung möglich',
            'details': compatibility_result
        }
    
    def create_multi_ecu_activation_plan(self, selected_features):
        """Erstelle Multi-ECU Aktivierungsplan"""
        
        # Prüfe Kompatibilität
        compatibility = self.check_multi_ecu_activation_compatibility(selected_features)
        
        if not compatibility['compatible']:
            return {
                'success': False,
                'message': compatibility['message'],
                'plan': None
            }
        
        # Gruppiere Features nach ECUs
        ecu_groups = {}
        for feature_id in selected_features:
            if feature_id in self.available_features:
                feature = self.available_features[feature_id]
                for ecu in feature.required_ecus:
                    if ecu not in ecu_groups:
                        ecu_groups[ecu] = []
                    ecu_groups[ecu].append(feature_id)
        
        # Erstelle Aktivierungsplan
        if compatibility.get('requires_sequential', False):
            # Sequenzielle Aktivierung
            activation_plan = self._create_sequential_activation_plan(ecu_groups, selected_features)
        else:
            # Parallele Aktivierung möglich
            activation_plan = self._create_parallel_activation_plan(ecu_groups, selected_features)
        
        return {
            'success': True,
            'message': 'Multi-ECU Aktivierungsplan erstellt',
            'plan': activation_plan,
            'compatibility': compatibility
        }
    
    def _create_sequential_activation_plan(self, ecu_groups, selected_features):
        """Erstelle sequenziellen Aktivierungsplan"""
        
        plan = {
            'type': 'sequential',
            'phases': [],
            'estimated_duration': 0,
            'safety_checks': []
        }
        
        # Sortiere ECUs nach Priorität
        ecu_priority = ['BSI', 'CMM', 'COMBINE', 'NAC', 'ABS', 'CLIMATE', 'CAMERA']
        sorted_ecus = sorted(ecu_groups.keys(), key=lambda x: ecu_priority.index(x) if x in ecu_priority else 999)
        
        phase_number = 1
        for ecu in sorted_ecus:
            features_for_ecu = ecu_groups[ecu]
            
            phase = {
                'phase': phase_number,
                'ecu': ecu,
                'features': features_for_ecu,
                'duration_estimate': len(features_for_ecu) * 2 + 3,  # 2 min per feature + 3 min setup
                'safety_validations': [
                    f'Validate {ecu} communication',
                    f'Check {ecu} security access',
                    f'Verify feature prerequisites'
                ],
                'rollback_plan': f'Restore {ecu} original configuration'
            }
            
            plan['phases'].append(phase)
            plan['estimated_duration'] += phase['duration_estimate']
            phase_number += 1
        
        # Gesamt-Sicherheitschecks
        plan['safety_checks'] = [
            'Vehicle immobilizer check',
            'Engine running state verification',
            'Battery voltage monitoring',
            'Communication stability test'
        ]
        
        return plan
    
    def _create_parallel_activation_plan(self, ecu_groups, selected_features):
        """Erstelle parallelen Aktivierungsplan"""
        
        plan = {
            'type': 'parallel',
            'ecu_sessions': [],
            'estimated_duration': 0,
            'safety_checks': []
        }
        
        max_duration = 0
        
        for ecu, features in ecu_groups.items():
            session = {
                'ecu': ecu,
                'features': features,
                'duration_estimate': len(features) * 1.5 + 2,  # Faster with parallel processing
                'safety_validations': [
                    f'Validate {ecu} communication',
                    f'Check {ecu} security access'
                ]
            }
            
            plan['ecu_sessions'].append(session)
            max_duration = max(max_duration, session['duration_estimate'])
        
        plan['estimated_duration'] = max_duration + 5  # Extra time for coordination
        
        # Parallele Sicherheitschecks
        plan['safety_checks'] = [
            'Multi-ECU communication test',
            'Simultaneous security access verification',
            'Cross-ECU dependency validation',
            'System stability monitoring'
        ]
        
        return plan
    
    def activate_features(self, activation_plan, communication_interface=None):
        """Aktiviere Features nach Plan"""
        self.activationMessage.emit("Starte Feature-Aktivierung...")
        
        total_features = len(activation_plan['activation_order'])
        
        for i, feature_id in enumerate(activation_plan['activation_order']):
            progress = int((i / total_features) * 100)
            self.activationProgress.emit(progress)
            
            feature = self.available_features[feature_id]
            self.activationMessage.emit(f"Aktiviere: {feature.user_friendly_name}")
            
            # Simulate activation process
            success = self._perform_feature_activation(feature_id, communication_interface)
            
            self.featureActivated.emit(feature_id, success)
            
            if not success:
                self.activationMessage.emit(f"Fehler bei: {feature.user_friendly_name}")
                return False
        
        self.activationProgress.emit(100)
        self.activationMessage.emit("Alle Features erfolgreich aktiviert!")
        return True
    
    def _perform_feature_activation(self, feature_id, communication_interface):
        """Führe tatsächliche Feature-Aktivierung durch"""
        # This would integrate with the actual diagnostic communication
        # For now, return True to simulate successful activation
        
        try:
            feature = self.available_features[feature_id]
            
            # Simulate different activation procedures based on feature
            if feature_id == 'auto_lights':
                # BSI configuration for automatic lights
                return self._activate_bsi_feature('auto_lights', communication_interface)
            elif feature_id == 'nac_apps':
                # NAC programming for extended features
                return self._activate_nac_feature('extended_apps', communication_interface)
            elif feature_id == 'stop_start':
                # CMM configuration for start-stop
                return self._activate_cmm_feature('start_stop', communication_interface)
            else:
                # Generic activation
                return True
                
        except Exception as e:
            self.activationMessage.emit(f"Aktivierungsfehler: {e}")
            return False
    
    def _activate_bsi_feature(self, feature, communication_interface):
        """Aktiviere BSI-Feature"""
        # Would use PSASpecialDiagnostics for actual BSI communication
        return True
    
    def _activate_nac_feature(self, feature, communication_interface):
        """Aktiviere NAC-Feature"""
        # Would use PSASpecialDiagnostics for actual NAC communication  
        return True
    
    def _activate_cmm_feature(self, feature, communication_interface):
        """Aktiviere CMM-Feature"""
        # Would use PSASpecialDiagnostics for actual CMM communication
        return True
    
    def get_feature_categories(self):
        """Hole Feature-Kategorien für UI"""
        categories = {}
        for feature_id, feature in self.available_features.items():
            category = feature.category
            if category not in categories:
                categories[category] = {
                    'name': self._get_category_display_name(category),
                    'features': [],
                    'icon': self._get_category_icon(category)
                }
            categories[category]['features'].append(feature_id)
        
        return categories
    
    def _get_category_display_name(self, category):
        """Hole Anzeigename für Kategorie"""
        names = {
            'comfort': 'Komfort & Bequemlichkeit',
            'audio': 'Audio & Unterhaltung',
            'safety': 'Sicherheit & Assistenz', 
            'lighting': 'Beleuchtung',
            'engine': 'Motor & Fahrleistung',
            'climate': 'Klima & Umgebung'
        }
        return names.get(category, category.title())
    
    def _get_category_icon(self, category):
        """Hole Icon für Kategorie"""
        icons = {
            'comfort': '🏠',
            'audio': '🎵',
            'safety': '🛡️',
            'lighting': '💡',
            'engine': '⚙️',
            'climate': '🌡️'
        }
        return icons.get(category, '⚡')
    
    def export_activation_report(self, activation_plan, results, filename):
        """Exportiere Aktivierungsreport"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'vehicle': self.current_vehicle.name if self.current_vehicle else 'Unknown',
            'plan': activation_plan,
            'results': results,
            'summary': {
                'total_features': len(activation_plan['activation_order']),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success'])
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.activationMessage.emit(f"Export-Fehler: {e}")
            return False


class FeatureActivationWidget(QWidget):
    """Benutzerfreundliches Feature-Aktivierungs-Widget"""
    
    def __init__(self, activation_matrix):
        super().__init__()
        self.activation_matrix = activation_matrix
        self.available_features = {}
        self.selected_features = []
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup UI"""
        main_layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Feature-Aktivierung fuer Ihr Fahrzeug")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header_label)
        
        # Vehicle info
        self.vehicle_info_label = QLabel("Fahrzeug wird erkannt...")
        main_layout.addWidget(self.vehicle_info_label)
        
        # Scrollable area for feature categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        
        scroll_widget = QWidget()
        self.categories_layout = QVBoxLayout(scroll_widget)
        self.categories_layout.addStretch()  # Add stretch at bottom
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("Fahrzeug analysieren")
        self.activate_button = QPushButton("Features aktivieren")
        self.activate_button.setEnabled(False)
        
        buttons_layout.addWidget(self.analyze_button)
        buttons_layout.addWidget(self.activate_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Hardware Status Tab
        hardware_group = QGroupBox("Hardware-Status")
        hardware_layout = QVBoxLayout(hardware_group)
        
        self.hardware_table = QTableWidget()
        self.hardware_table.setMaximumHeight(150)
        self.hardware_table.setColumnCount(4)
        self.hardware_table.setHorizontalHeaderLabels([
            "Feature", "Hardware", "Status", "Vertrauen"
        ])
        self.hardware_table.horizontalHeader().setStretchLastSection(True)
        hardware_layout.addWidget(self.hardware_table)
        
        main_layout.addWidget(hardware_group)
        
        # Status - also scrollable
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        main_layout.addWidget(self.status_text)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        """Verbinde Signals"""
        self.activation_matrix.vehicleDetected.connect(self.update_available_features)
        self.activation_matrix.activationProgress.connect(self.progress_bar.setValue)
        self.activation_matrix.activationMessage.connect(self.add_status_message)
        self.activation_matrix.featureActivated.connect(self.feature_activation_result)
        self.activation_matrix.hardwareValidated.connect(self.update_hardware_status)
        
        self.analyze_button.clicked.connect(self.analyze_vehicle)
        self.activate_button.clicked.connect(self.activate_selected_features)
    
    def analyze_vehicle(self):
        """Analysiere Fahrzeug"""
        self.add_status_message("Starte Fahrzeuganalyse...")
        
        # Would integrate with actual vehicle detection
        # For demo, use mock data
        mock_vehicle_profile = type('MockProfile', (), {
            'name': 'Peugeot 308 (Demo)',
            'production_years': '2014-2021'
        })()
        
        mock_detected_ecus = [
            {'name': 'BSI Body Control'},
            {'name': 'CMM Engine Control'},
            {'name': 'NAC Infotainment'},
            {'name': 'COMBINE Instrument Cluster'}
        ]
        
        self.activation_matrix.analyze_vehicle_capabilities(mock_vehicle_profile, mock_detected_ecus)
    
    def update_available_features(self, analysis_result):
        """Update verfügbare Features"""
        self.available_features = analysis_result['features']
        
        # Update vehicle info
        vehicle_name = analysis_result['vehicle']
        available_count = analysis_result['available_features']
        total_count = analysis_result['total_features']
        
        self.vehicle_info_label.setText(
            f"🚗 {vehicle_name} - {available_count}/{total_count} Features verfügbar"
        )
        
        # Clear existing categories
        self.clear_categories()
        
        # Create category groups
        categories = self.activation_matrix.get_feature_categories()
        
        for category_id, category_info in categories.items():
            category_features = [
                fid for fid in category_info['features'] 
                if fid in self.available_features
            ]
            
            if category_features:
                self.create_category_group(category_info, category_features)
        
        self.activate_button.setEnabled(True)
        self.add_status_message(f"Analyse abgeschlossen. {available_count} Features verfügbar.")
        
        # Update Hardware-Status Tabelle
        if 'hardware_status' in analysis_result:
            self.update_hardware_table(analysis_result['hardware_status'])
    
    def clear_categories(self):
        """Lösche bestehende Kategorien"""
        while self.categories_layout.count():
            child = self.categories_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_category_group(self, category_info, feature_ids):
        """Erstelle Kategorie-Gruppe"""
        group = QGroupBox(f"{category_info['icon']} {category_info['name']}")
        group_layout = QVBoxLayout()
        
        for feature_id in feature_ids:
            feature_info = self.available_features[feature_id]
            feature = feature_info['feature']
            
            # Feature checkbox
            checkbox = QCheckBox(feature.user_friendly_name)
            checkbox.setToolTip(feature.description)
            checkbox.setProperty('feature_id', feature_id)
            checkbox.toggled.connect(self.feature_selection_changed)
            
            # Complexity indicator
            complexity = feature_info['activation_complexity']
            complexity_colors = {
                'easy': 'green',
                'medium': 'orange', 
                'hard': 'red'
            }
            
            complexity_label = QLabel(f"({complexity})")
            complexity_label.setStyleSheet(f"color: {complexity_colors.get(complexity, 'black')};")
            
            # Feature layout
            feature_layout = QHBoxLayout()
            feature_layout.addWidget(checkbox)
            feature_layout.addWidget(complexity_label)
            feature_layout.addStretch()
            
            group_layout.addLayout(feature_layout)
        
        group.setLayout(group_layout)
        self.categories_layout.addWidget(group)
    
    def feature_selection_changed(self, checked):
        """Feature-Auswahl geändert"""
        checkbox = self.sender()
        feature_id = checkbox.property('feature_id')
        
        if checked and feature_id not in self.selected_features:
            self.selected_features.append(feature_id)
        elif not checked and feature_id in self.selected_features:
            self.selected_features.remove(feature_id)
        
        # Update activation button
        self.activate_button.setText(f"⚡ {len(self.selected_features)} Features aktivieren")
    
    def activate_selected_features(self):
        """Aktiviere ausgewählte Features"""
        if not self.selected_features:
            self.add_status_message("Keine Features ausgewählt.")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create activation plan
        plan = self.activation_matrix.create_activation_plan(self.selected_features)
        
        self.add_status_message(f"Aktiviere {len(self.selected_features)} Features...")
        self.add_status_message(f"Geschätzte Zeit: {plan['estimated_time']} Minuten")
        
        # Start activation
        self.activation_matrix.activate_features(plan)
    
    def feature_activation_result(self, feature_id, success):
        """Feature-Aktivierungsergebnis"""
        if feature_id in self.available_features:
            feature_name = self.available_features[feature_id]['feature'].user_friendly_name
            status = "✅ Erfolgreich" if success else "❌ Fehler"
            self.add_status_message(f"{status}: {feature_name}")
    
    def update_hardware_table(self, hardware_status):
        """Update Hardware-Status Tabelle"""
        self.hardware_table.setRowCount(len(hardware_status))
        
        row = 0
        for feature_id, validation_result in hardware_status.items():
            if validation_result and hasattr(validation_result, 'is_available'):
                # Feature Name
                feature_name = feature_id
                if feature_id in self.activation_matrix.available_features:
                    feature_name = self.activation_matrix.available_features[feature_id].user_friendly_name
                
                self.hardware_table.setItem(row, 0, QTableWidgetItem(feature_name))
                
                # Hardware Status
                hardware_info = "Unbekannt"
                if hasattr(validation_result, 'detection_details'):
                    method = validation_result.detection_details.get('method', 'Standard')
                    hardware_info = method
                
                self.hardware_table.setItem(row, 1, QTableWidgetItem(hardware_info))
                
                # Status
                status = "Verfügbar" if validation_result.is_available else "Nicht verfügbar"
                status_item = QTableWidgetItem(status)
                from PySide6.QtGui import QColor
                status_item.setBackground(QColor(144, 238, 144) if validation_result.is_available else QColor(255, 182, 193))
                self.hardware_table.setItem(row, 2, status_item)
                
                # Vertrauen
                confidence = getattr(validation_result, 'confidence_level', 0.0)
                confidence_text = f"{confidence*100:.1f}%"
                self.hardware_table.setItem(row, 3, QTableWidgetItem(confidence_text))
                
                row += 1
        
        self.hardware_table.resizeColumnsToContents()
    
    def update_hardware_status(self, hardware_data):
        """Update Hardware-Status von Signal"""
        if 'hardware_status' in hardware_data:
            self.update_hardware_table(hardware_data['hardware_status'])
    
    def add_status_message(self, message):
        """Füge Status-Nachricht hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
    
    def activate_selected_features(self):
        """Aktiviere ausgewählte Features mit Hardware-Validierung"""
        if not hasattr(self, 'selected_features') or not self.selected_features:
            self.add_status_message("Keine Features ausgewählt")
            return
        
        self.add_status_message("Prüfe Multi-ECU Kompatibilität...")
        
        # Multi-ECU Aktivierungsplan erstellen
        if hasattr(self.activation_matrix, 'create_multi_ecu_activation_plan'):
            plan_result = self.activation_matrix.create_multi_ecu_activation_plan(self.selected_features)
            
            if plan_result['success']:
                plan = plan_result['plan']
                compatibility = plan_result['compatibility']
                
                if plan['type'] == 'sequential':
                    self.add_status_message(f"Sequenzielle Aktivierung erforderlich - {len(plan['phases'])} Phasen")
                    self.add_status_message(f"Geschätzte Dauer: {plan['estimated_duration']} Minuten")
                else:
                    self.add_status_message(f"Parallele Aktivierung möglich - {len(plan['ecu_sessions'])} ECU-Sessions")
                    self.add_status_message(f"Geschätzte Dauer: {plan['estimated_duration']} Minuten")
                
                self.add_status_message(compatibility['message'])
                
                # Hier würde die tatsächliche Aktivierung stattfinden
                self.add_status_message("Feature-Aktivierung gestartet...")
                
            else:
                self.add_status_message(f"Multi-ECU Plan Fehler: {plan_result['message']}")
        else:
            # Fallback auf Standard-Aktivierung
            standard_plan = self.activation_matrix.create_activation_plan(self.selected_features)
            self.add_status_message(f"Standard-Aktivierung: {standard_plan['estimated_time']} min")
    
    def feature_selection_changed(self, checked):
        """Handle Feature-Auswahl Änderung"""
        checkbox = self.sender()
        feature_id = checkbox.property('feature_id')
        
        if not hasattr(self, 'selected_features'):
            self.selected_features = []
        
        if checked and feature_id not in self.selected_features:
            self.selected_features.append(feature_id)
        elif not checked and feature_id in self.selected_features:
            self.selected_features.remove(feature_id)
        
        self.add_status_message(f"Feature {feature_id}: {'ausgewählt' if checked else 'abgewählt'}")
        
        # Update Button Status
        self.activate_button.setEnabled(len(self.selected_features) > 0)