"""
  SimpleEnhancedMainWindow.py
  
  Einfaches Enhanced Interface mit sauberen Tabs und Fehlerbehandlung
"""

import sys
import os
from qt_compat import *
from datetime import datetime

# Import der Basis-Module (immer verfügbar)
from SimpleECUDetector import SimpleECUDetector
from MultiECUManager import MultiECUManager
from BackupRestoreSystem import BackupRestoreSystem
from EnhancedSearchFilter import EnhancedSearchFilter
from SeedKeyGenerator import SeedKeyGenerator
from LiveDashboard import LiveDashboard

# Import der Original-Klassen
from main import MainWindow

# Theme Manager Import
try:
    from ThemeManager import get_theme_manager
    THEME_MANAGER_AVAILABLE = True
    print("[OK] ThemeManager loaded")
except ImportError as e:
    print(f"[WARN] ThemeManager not available: {e}")
    THEME_MANAGER_AVAILABLE = False

# Automatic Backup System Import
try:
    from AutomaticBackupSystem import get_backup_system
    BACKUP_SYSTEM_AVAILABLE = True
    print("[OK] AutomaticBackupSystem loaded")
except ImportError as e:
    print(f"[WARN] AutomaticBackupSystem not available: {e}")
    BACKUP_SYSTEM_AVAILABLE = False

# Automatic VCI Detection Import
try:
    from AutomaticVCIDetection import get_vci_detection
    VCI_DETECTION_AVAILABLE = True
    print("[OK] AutomaticVCIDetection loaded")
except ImportError as e:
    print(f"[WARN] AutomaticVCIDetection not available: {e}")
    VCI_DETECTION_AVAILABLE = False

# ECU/VIN Database Import
try:
    from ECUVINDatabase import get_ecu_vin_database
    ECU_VIN_DATABASE_AVAILABLE = True
    print("[OK] ECUVINDatabase loaded")
except ImportError as e:
    print(f"[WARN] ECUVINDatabase not available: {e}")
    ECU_VIN_DATABASE_AVAILABLE = False

# Hardware VCI Interface Import
try:
    from HardwareVCIInterface import get_hardware_vci
    HARDWARE_VCI_AVAILABLE = True
    print("[OK] HardwareVCIInterface loaded")
except ImportError as e:
    print(f"[WARN] HardwareVCIInterface not available: {e}")
    HARDWARE_VCI_AVAILABLE = False

# Help & Manual System Import
try:
    from HelpIntegrationPatch import HelpSystemPatch
    HELP_SYSTEM_AVAILABLE = True
    print("[OK] Help & Manual System loaded")
except ImportError as e:
    print(f"[WARN] Help & Manual System not available: {e}")
    HELP_SYSTEM_AVAILABLE = False

# Erweiterte Module mit Error-Handling
ECU_DATABASE_AVAILABLE = False
PROTOCOL_ANALYZER_AVAILABLE = False
VEHICLE_PROFILE_AVAILABLE = False
DATA_LOGGING_AVAILABLE = False
SEED_KEY_BF_AVAILABLE = False

try:
    from ECUDatabase import ECUDatabase, VINDecoder
    ECU_DATABASE_AVAILABLE = True
    print("[OK] ECUDatabase loaded")
except ImportError as e:
    print(f"[WARN] ECUDatabase not available: {e}")
    ECUDatabase = None
    VINDecoder = None

try:
    from ProtocolAnalyzer import ProtocolAnalyzer
    PROTOCOL_ANALYZER_AVAILABLE = True
    print("[OK] ProtocolAnalyzer loaded")
except ImportError as e:
    print(f"[WARN] ProtocolAnalyzer not available: {e}")
    ProtocolAnalyzer = None

try:
    from VehicleProfileSystem import VehicleProfileSystem
    VEHICLE_PROFILE_AVAILABLE = True
    print("[OK] VehicleProfileSystem loaded")
except ImportError as e:
    print(f"[WARN] VehicleProfileSystem not available: {e}")
    VehicleProfileSystem = None

try:
    from DataLoggingSystem import DataLoggingSystem
    DATA_LOGGING_AVAILABLE = True
    print("[OK] DataLoggingSystem loaded")
except ImportError as e:
    print(f"[WARN] DataLoggingSystem not available: {e}")
    DataLoggingSystem = None

try:
    from SeedKeyBruteforce import SeedKeyBruteforce
    SEED_KEY_BF_AVAILABLE = True
    print("[OK] SeedKeyBruteforce loaded")
except ImportError as e:
    print(f"[WARN] SeedKeyBruteforce not available: {e}")
    SeedKeyBruteforce = None

# Professional Features importieren
try:
    from RealTimeGraphManager import RealTimeGraphWidget
    REALTIME_GRAPHS_AVAILABLE = True
    print("[OK] RealTimeGraphManager loaded")
except ImportError as e:
    # RealTimeGraphManager fallback - Live graphs will use basic implementation
    RealTimeGraphWidget = None
    REALTIME_GRAPHS_AVAILABLE = False

try:
    from PDFReportGenerator import PDFReportGenerator, DiagnosticData
    PDF_REPORTS_AVAILABLE = True
    print("[OK] PDFReportGenerator loaded")
except ImportError as e:
    # PDFReportGenerator fallback - Reports will use basic text format
    PDFReportGenerator = None
    PDF_REPORTS_AVAILABLE = False

try:
    from CodingAssistant import CodingAssistantWidget
    CODING_ASSISTANT_AVAILABLE = True
    print("[OK] CodingAssistant loaded")
except ImportError as e:
    print(f"[WARN] CodingAssistant not available: {e}")
    CodingAssistantWidget = None
    CODING_ASSISTANT_AVAILABLE = False

try:
    from FlashUpdateManager import FlashManagerWidget
    FLASH_MANAGER_AVAILABLE = True
    print("[OK] FlashUpdateManager loaded")
except ImportError as e:
    print(f"[WARN] FlashUpdateManager not available: {e}")
    FlashManagerWidget = None
    FLASH_MANAGER_AVAILABLE = False

try:
    from RealConfigManager import RealConfigManagerWidget
    CONFIG_MANAGER_AVAILABLE = True
    print("[OK] RealConfigManager loaded")
except ImportError as e:
    print(f"[WARN] RealConfigManager not available: {e}")
    RealConfigManagerWidget = None
    CONFIG_MANAGER_AVAILABLE = False

# Enhanced Event Handlers importieren
try:
    from EnhancedEventHandlers import EnhancedEventHandlers
    ENHANCED_HANDLERS_AVAILABLE = True
    print("[OK] EnhancedEventHandlers loaded")
except ImportError as e:
    print(f"[WARN] EnhancedEventHandlers not available: {e}")
    EnhancedEventHandlers = None
    ENHANCED_HANDLERS_AVAILABLE = False

# Feature Activation Matrix importieren
try:
    from FeatureActivationMatrix import FeatureActivationMatrix, FeatureActivationWidget
    FEATURE_ACTIVATION_AVAILABLE = True
    print("[OK] FeatureActivationMatrix loaded")
except ImportError as e:
    print(f"[WARN] FeatureActivationMatrix not available: {e}")
    FeatureActivationMatrix = None
    FeatureActivationWidget = None
    FEATURE_ACTIVATION_AVAILABLE = False


class SimpleEnhancedMainWindow(MainWindow, EnhancedEventHandlers if ENHANCED_HANDLERS_AVAILABLE else object):
    """Enhanced Main Window mit Fehlerbehandlung"""
    
    def __init__(self):
        super().__init__()
        
        # Basis-Module (immer verfügbar)
        self.ecu_detector = None
        self.multi_ecu_manager = None
        self.backup_system = BackupRestoreSystem()
        self.search_filter = EnhancedSearchFilter()
        self.seed_key_generator = SeedKeyGenerator()
        
        # Erweiterte Module (nur wenn verfügbar)
        self.ecu_database = ECUDatabase() if ECU_DATABASE_AVAILABLE else None
        self.protocol_analyzer = ProtocolAnalyzer() if PROTOCOL_ANALYZER_AVAILABLE else None
        self.vehicle_profile_system = VehicleProfileSystem() if VEHICLE_PROFILE_AVAILABLE else None
        self.data_logging_system = DataLoggingSystem() if DATA_LOGGING_AVAILABLE else None
        self.seed_key_bruteforce = SeedKeyBruteforce() if SEED_KEY_BF_AVAILABLE else None
        self.feature_activation_matrix = FeatureActivationMatrix() if FEATURE_ACTIVATION_AVAILABLE else None
        
        # Theme Manager
        self.theme_manager = get_theme_manager() if THEME_MANAGER_AVAILABLE else None
        
        # Automatic Backup System
        self.backup_system = get_backup_system() if BACKUP_SYSTEM_AVAILABLE else None
        
        # Automatic VCI Detection
        self.vci_detection = get_vci_detection() if VCI_DETECTION_AVAILABLE else None
        if self.vci_detection:
            # Connect VCI signals
            self.vci_detection.vci_detected.connect(self.on_vci_detected)
            self.vci_detection.vci_connected.connect(self.on_vci_connected)
            self.vci_detection.vci_disconnected.connect(self.on_vci_disconnected)
            self.vci_detection.detection_status_changed.connect(self.on_vci_status_changed)
            
            # Start VCI detection
            self.vci_detection.start_detection()
        
        # ECU/VIN Database
        self.ecu_vin_database = get_ecu_vin_database() if ECU_VIN_DATABASE_AVAILABLE else None
        
        # Hardware VCI Interface
        self.hardware_vci = get_hardware_vci() if HARDWARE_VCI_AVAILABLE else None
        if self.hardware_vci:
            # Connect hardware VCI signals
            self.hardware_vci.message_received.connect(self.on_can_message_received)
            self.hardware_vci.message_sent.connect(self.on_can_message_sent)
            self.hardware_vci.connection_status_changed.connect(self.on_hardware_connection_changed)
            self.hardware_vci.hardware_error.connect(self.on_hardware_error)
            self.hardware_vci.timing_violation.connect(self.on_timing_violation)
        
        # Setup Enhanced Interface
        self.setup_enhanced_interface()
        
        # Help System
        self.setup_help_system()
        
        # Apply saved theme
        if self.theme_manager:
            self.theme_manager.apply_theme(self.theme_manager.get_current_theme())
        
    def setup_enhanced_interface(self):
        """Setup Enhanced Interface"""
        # Erstelle Tab Widget
        self.main_tabs = QTabWidget()
        
        # Container Layout
        layout = QVBoxLayout()
        layout.addWidget(self.main_tabs)
        container = QWidget()
        container.setLayout(layout)
        
        # Original Central Widget als ersten Tab
        original_central = self.centralWidget()
        if original_central:
            self.main_tabs.addTab(original_central, "PyPSADiag")
        
        # Enhanced Tabs hinzufügen
        self.create_enhanced_tabs()
        
        # Container als Central Widget setzen
        super().setCentralWidget(container)
        
        # Titel und Features
        self.setWindowTitle("PyPSADiag Enhanced")
        self.setup_vci_integration()
        self.setup_auto_features()
        self.setup_keyboard_shortcuts()
        self.setup_themes()
        
        # Status Bar
        if not self.statusBar():
            self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("PyPSADiag Enhanced bereit - Drücke F1 für Hilfe")
        
    def create_scrollable_tab(self, content_widget):
        """Erstelle scrollbares Tab-Widget"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        return scroll_area
    
    def create_enhanced_tabs(self):
        """Erstelle Enhanced Tabs - Neue optimierte Struktur mit Gruppierung"""
        
        # 1. 📡 Connection & Diagnostics
        connection_tabs = QTabWidget()
        connection_tabs.addTab(self.create_ecu_detection_tab(), "ECU Detection")
        connection_tabs.addTab(self.create_multi_ecu_tab(), "Multi-ECU Manager")
        connection_tabs.addTab(self.create_dashboard_tab(), "Live Dashboard")
        connection_tabs.addTab(self.create_scrollable_tab(self.create_diagnostics_tab()), "Diagnostics")
        if HARDWARE_VCI_AVAILABLE:
            connection_tabs.addTab(self.create_scrollable_tab(self.create_hardware_monitor_tab()), "Hardware Monitor")
        self.main_tabs.addTab(connection_tabs, "Connection & Diagnostics")
        
        # 2. Coding & Programming
        coding_tabs = QTabWidget()
        coding_tabs.addTab(self.create_scrollable_tab(self.create_coding_assistant_tab()), "ECU Coding")
        if FEATURE_ACTIVATION_AVAILABLE:
            coding_tabs.addTab(self.create_feature_activation_tab(), "Feature Aktivierung")
            coding_tabs.addTab(self.create_scrollable_tab(self.create_hardware_validation_tab()), "Hardware Validierung")
        coding_tabs.addTab(self.create_scrollable_tab(self.create_flash_manager_tab()), "Flash Manager")
        self.main_tabs.addTab(coding_tabs, "Coding & Programming")
        
        # 3. Security & Keys
        security_tabs = QTabWidget()
        security_tabs.addTab(self.create_scrollable_tab(self.create_seedkey_tab()), "Seed/Key Basic")
        if SEED_KEY_BF_AVAILABLE:
            security_tabs.addTab(self.create_scrollable_tab(self.create_enhanced_seedkey_tab()), "Advanced Seed/Key")
        if PROTOCOL_ANALYZER_AVAILABLE:
            security_tabs.addTab(self.create_scrollable_tab(self.create_analyzer_tab()), "Protocol Analyzer")
        self.main_tabs.addTab(security_tabs, "Security & Keys")
        
        # 4. Data & Analysis
        data_tabs = QTabWidget()
        if DATA_LOGGING_AVAILABLE:
            data_tabs.addTab(self.create_scrollable_tab(self.create_logging_tab()), "Data Logging")
        data_tabs.addTab(self.create_scrollable_tab(self.create_live_graphs_tab()), "Live Graphs")
        data_tabs.addTab(self.create_scrollable_tab(self.create_pdf_reports_tab()), "PDF Reports")
        if ECU_VIN_DATABASE_AVAILABLE:
            data_tabs.addTab(self.create_scrollable_tab(self.create_vin_decoder_tab()), "VIN Decoder")
        self.main_tabs.addTab(data_tabs, "Data & Analysis")
        
        # 5. Database & Profiles
        database_tabs = QTabWidget()
        if ECU_DATABASE_AVAILABLE:
            database_tabs.addTab(self.create_scrollable_tab(self.create_database_tab()), "ECU Database")
        if VEHICLE_PROFILE_AVAILABLE:
            database_tabs.addTab(self.create_scrollable_tab(self.create_profile_tab()), "Vehicle Profile")
        database_tabs.addTab(self.create_scrollable_tab(self.create_config_manager_tab()), "PSA Configs")
        self.main_tabs.addTab(database_tabs, "Database & Profiles")
        
        # 6. Backup & Tools
        tools_tabs = QTabWidget()
        tools_tabs.addTab(self.create_backup_tab(), "Backup/Restore")
        tools_tabs.addTab(self.create_search_tab(), "Search/Filter")
        tools_tabs.addTab(self.create_scrollable_tab(self.create_settings_tab()), "Settings")
        self.main_tabs.addTab(tools_tabs, "Backup & Tools")
    
    def create_ecu_detection_tab(self):
        """ECU Detection Tab - vereinfacht ohne komplexe Features"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("ECU Detection")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Simple Controls
        controls = QHBoxLayout()
        
        start_btn = QPushButton("Start ECU Scan")
        start_btn.setObjectName("btn_scan_ecus")
        start_btn.clicked.connect(self.simple_ecu_scan)
        controls.addWidget(start_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results
        self.ecu_results = QTextEdit()
        layout.addWidget(self.ecu_results)
        
        return widget
    
    def create_multi_ecu_tab(self):
        """Multi-ECU Tab - vereinfacht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Multi-ECU Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        info = QLabel("Multi-ECU features available when ECUs are detected")
        layout.addWidget(info)
        
        return widget
    
    def create_backup_tab(self):
        """Backup Tab - vereinfacht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Backup & Restore")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        backup_btn = QPushButton("Create Simple Backup")
        backup_btn.setObjectName("btn_create_backup")
        backup_btn.clicked.connect(self.simple_backup)
        layout.addWidget(backup_btn)
        
        layout.addStretch()
        return widget
    
    def create_search_tab(self):
        """Search Tab - vereinfacht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Search & Filter")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...")
        layout.addWidget(search_input)
        
        results = QListWidget()
        layout.addWidget(results)
        
        return widget
    
    def create_seedkey_tab(self):
        """Seed/Key Tab - Basis-Version"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Seed/Key Generator")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Algorithm Selection
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algorithm:"))
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(self.seed_key_generator.get_available_algorithms())
        algo_layout.addWidget(self.algorithm_combo)
        layout.addLayout(algo_layout)
        
        # Seed/Key
        seedkey_layout = QHBoxLayout()
        seedkey_layout.addWidget(QLabel("Seed:"))
        
        self.seed_input = QLineEdit()
        seedkey_layout.addWidget(self.seed_input)
        
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate_key)
        seedkey_layout.addWidget(generate_btn)
        layout.addLayout(seedkey_layout)
        
        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel("Key:"))
        
        self.key_output = QLineEdit()
        self.key_output.setReadOnly(True)
        result_layout.addWidget(self.key_output)
        layout.addLayout(result_layout)
        
        return widget
    
    def create_dashboard_tab(self):
        """Dashboard Tab"""
        if hasattr(self, 'live_dashboard') and self.live_dashboard:
            return self.live_dashboard
        
        self.live_dashboard = LiveDashboard()
        return self.live_dashboard
    
    def create_diagnostics_tab(self):
        """Diagnostics Tab - vereinfacht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Diagnostics")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        info = QLabel("Advanced diagnostics available with vehicle connection")
        layout.addWidget(info)
        
        layout.addStretch()
        return widget
    
    # Erweiterte Tabs (nur wenn Module verfügbar)
    def create_database_tab(self):
        """ECU Database Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("ECU Database & VIN Decoder")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # VIN Decoder Sektion
        vin_group = QGroupBox("VIN Decoder")
        vin_layout = QVBoxLayout(vin_group)
        
        vin_input_layout = QHBoxLayout()
        vin_input_layout.addWidget(QLabel("VIN (17 Zeichen):"))
        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText("z.B. VF32A9HZ8EC123456")
        self.vin_input.setMaxLength(17)
        vin_input_layout.addWidget(self.vin_input)
        
        decode_btn = QPushButton("VIN dekodieren")
        decode_btn.setObjectName("btn_decode_vin")
        decode_btn.clicked.connect(self.decode_vin)
        vin_input_layout.addWidget(decode_btn)
        vin_layout.addLayout(vin_input_layout)
        
        self.vin_result = QTextEdit()
        self.vin_result.setMaximumHeight(120)
        self.vin_result.setReadOnly(True)
        vin_layout.addWidget(self.vin_result)
        
        layout.addWidget(vin_group)
        
        # ECU Search Sektion
        search_group = QGroupBox("ECU Suche")
        search_layout = QVBoxLayout(search_group)
        
        search_input_layout = QHBoxLayout()
        search_input_layout.addWidget(QLabel("Suche:"))
        self.ecu_search_input = QLineEdit()
        self.ecu_search_input.setPlaceholderText("ECU-ID, Name oder Hersteller...")
        self.ecu_search_input.textChanged.connect(self.search_ecus)
        search_input_layout.addWidget(self.ecu_search_input)
        search_layout.addLayout(search_input_layout)
        
        # Suchergebnisse und Details nebeneinander
        results_layout = QHBoxLayout()
        
        # Suchergebnisse
        results_left = QVBoxLayout()
        results_left.addWidget(QLabel("Suchergebnisse:"))
        self.ecu_search_results = QListWidget()
        self.ecu_search_results.itemClicked.connect(self.show_ecu_details)
        results_left.addWidget(self.ecu_search_results)
        
        # ECU Details
        details_right = QVBoxLayout()
        details_right.addWidget(QLabel("ECU Details:"))
        self.ecu_details = QTextEdit()
        self.ecu_details.setReadOnly(True)
        details_right.addWidget(self.ecu_details)
        
        results_widget_left = QWidget()
        results_widget_left.setLayout(results_left)
        results_widget_right = QWidget()
        results_widget_right.setLayout(details_right)
        
        results_layout.addWidget(results_widget_left)
        results_layout.addWidget(results_widget_right)
        search_layout.addLayout(results_layout)
        
        layout.addWidget(search_group)
        
        # Database Management Buttons
        db_buttons = QHBoxLayout()
        
        export_btn = QPushButton("Export Database")
        export_btn.clicked.connect(self.export_database)
        db_buttons.addWidget(export_btn)
        
        import_btn = QPushButton("Import Database")
        import_btn.clicked.connect(self.import_database)
        db_buttons.addWidget(import_btn)
        
        stats_btn = QPushButton("Database Stats")
        stats_btn.clicked.connect(self.show_database_stats)
        db_buttons.addWidget(stats_btn)
        
        db_buttons.addStretch()
        layout.addLayout(db_buttons)
        
        return widget
    
    def create_analyzer_tab(self):
        """Protocol Analyzer Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Protocol Analyzer - CAN-Bus Traffic")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Control Panel
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        # Decoder Selection
        controls_layout.addWidget(QLabel("Decoder:"))
        self.decoder_combo = QComboBox()
        self.decoder_combo.addItems(["Auto", "UDS", "KWP2000", "Raw"])
        self.decoder_combo.currentTextChanged.connect(self.change_decoder)
        controls_layout.addWidget(self.decoder_combo)
        
        controls_layout.addStretch()
        
        # Start/Stop Buttons
        self.analyzer_start_btn = QPushButton("Start Analysis")
        self.analyzer_start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.analyzer_start_btn.clicked.connect(self.start_protocol_analysis)
        controls_layout.addWidget(self.analyzer_start_btn)
        
        self.analyzer_stop_btn = QPushButton("Stop Analysis")
        self.analyzer_stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.analyzer_stop_btn.setEnabled(False)
        self.analyzer_stop_btn.clicked.connect(self.stop_protocol_analysis)
        controls_layout.addWidget(self.analyzer_stop_btn)
        
        # Export Button
        export_btn = QPushButton("Export Session")
        export_btn.clicked.connect(self.export_protocol_session)
        controls_layout.addWidget(export_btn)
        
        layout.addWidget(controls_group)
        
        # Traffic Display
        traffic_group = QGroupBox("Protocol Traffic")
        traffic_layout = QVBoxLayout(traffic_group)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.traffic_filter = QLineEdit()
        self.traffic_filter.setPlaceholderText("z.B. 180, 240, UDS...")
        filter_layout.addWidget(self.traffic_filter)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.protocol_traffic.clear())
        filter_layout.addWidget(clear_btn)
        traffic_layout.addLayout(filter_layout)
        
        # Traffic Log
        self.protocol_traffic = QTextEdit()
        self.protocol_traffic.setReadOnly(True)
        self.protocol_traffic.setFont(QFont("Consolas", 9))
        self.protocol_traffic.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                border: 1px solid #555;
            }
        """)
        traffic_layout.addWidget(self.protocol_traffic)
        
        layout.addWidget(traffic_group)
        
        # Statistics Panel
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        self.stats_frames = QLabel("Frames: 0")
        self.stats_errors = QLabel("Errors: 0")
        self.stats_rate = QLabel("Rate: 0 fps")
        
        stats_layout.addWidget(self.stats_frames)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.stats_errors)
        stats_layout.addWidget(QLabel("|"))
        stats_layout.addWidget(self.stats_rate)
        stats_layout.addStretch()
        
        layout.addWidget(stats_group)
        
        return widget
    
    def create_profile_tab(self):
        """Vehicle Profile Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Vehicle Profile System")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Auto Detection Panel
        detection_group = QGroupBox("Vehicle Detection")
        detection_layout = QVBoxLayout(detection_group)
        
        detect_buttons = QHBoxLayout()
        auto_detect_btn = QPushButton("Auto-Detect Vehicle")
        auto_detect_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        auto_detect_btn.clicked.connect(self.auto_detect_vehicle)
        detect_buttons.addWidget(auto_detect_btn)
        
        refresh_btn = QPushButton("Refresh Profiles")
        refresh_btn.clicked.connect(self.refresh_profiles_list)
        detect_buttons.addWidget(refresh_btn)
        
        detect_buttons.addStretch()
        detection_layout.addLayout(detect_buttons)
        layout.addWidget(detection_group)
        
        # Current Profile Display
        current_group = QGroupBox("Current Vehicle Profile")
        current_layout = QVBoxLayout(current_group)
        
        profile_info_layout = QHBoxLayout()
        profile_info_layout.addWidget(QLabel("Active Profile:"))
        self.current_profile_label = QLabel("No profile selected")
        self.current_profile_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        profile_info_layout.addWidget(self.current_profile_label)
        profile_info_layout.addStretch()
        current_layout.addLayout(profile_info_layout)
        
        self.profile_details = QTextEdit()
        self.profile_details.setMaximumHeight(100)
        self.profile_details.setReadOnly(True)
        current_layout.addWidget(self.profile_details)
        
        layout.addWidget(current_group)
        
        # Main Content - Profile List and Procedures
        content_layout = QHBoxLayout()
        
        # Profile List (Left)
        profiles_group = QGroupBox("Available Profiles")
        profiles_layout = QVBoxLayout(profiles_group)
        
        self.profiles_list = QListWidget()
        self.profiles_list.itemClicked.connect(self.select_profile)
        profiles_layout.addWidget(self.profiles_list)
        
        profiles_widget = QWidget()
        profiles_widget.setLayout(profiles_layout)
        content_layout.addWidget(profiles_widget)
        
        # Procedures (Right)
        procedures_group = QGroupBox("Available Procedures")
        procedures_layout = QVBoxLayout(procedures_group)
        
        self.procedures_list = QListWidget()
        procedures_layout.addWidget(self.procedures_list)
        
        execute_btn = QPushButton("Execute Procedure")
        execute_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        execute_btn.clicked.connect(self.execute_procedure)
        procedures_layout.addWidget(execute_btn)
        
        procedures_widget = QWidget()
        procedures_widget.setLayout(procedures_layout)
        content_layout.addWidget(procedures_widget)
        
        layout.addLayout(content_layout)
        
        # Initialize profile list
        if VEHICLE_PROFILE_AVAILABLE:
            self.refresh_profiles_list()
        
        return widget
    
    def create_logging_tab(self):
        """Data Logging Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Data Logging & Export System")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Recording Controls
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Recording Configuration
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Interval:"))
        self.logging_interval = QSpinBox()
        self.logging_interval.setRange(100, 5000)
        self.logging_interval.setValue(1000)
        self.logging_interval.setSuffix(" ms")
        config_layout.addWidget(self.logging_interval)
        
        config_layout.addStretch()
        controls_layout.addLayout(config_layout)
        
        # Parameter Selection
        params_layout = QHBoxLayout()
        
        self.log_engine_cb = QCheckBox("Engine Data")
        self.log_engine_cb.setChecked(True)
        self.log_engine_cb.setToolTip("RPM, Coolant Temp, Throttle Position")
        params_layout.addWidget(self.log_engine_cb)
        
        self.log_vehicle_cb = QCheckBox("Vehicle Data")
        self.log_vehicle_cb.setChecked(True)
        self.log_vehicle_cb.setToolTip("Speed, Fuel Level, etc.")
        params_layout.addWidget(self.log_vehicle_cb)
        
        self.log_abs_cb = QCheckBox("ABS/ESP Data")
        self.log_abs_cb.setToolTip("Wheel speeds, brake pressure")
        params_layout.addWidget(self.log_abs_cb)
        
        params_layout.addStretch()
        controls_layout.addLayout(params_layout)
        
        # Control Buttons
        buttons_layout = QHBoxLayout()
        
        self.logging_start_btn = QPushButton("Start Recording")
        self.logging_start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.logging_start_btn.clicked.connect(self.start_data_logging)
        buttons_layout.addWidget(self.logging_start_btn)
        
        self.logging_stop_btn = QPushButton("Stop Recording")
        self.logging_stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.logging_stop_btn.setEnabled(False)
        self.logging_stop_btn.clicked.connect(self.stop_data_logging)
        buttons_layout.addWidget(self.logging_stop_btn)
        
        buttons_layout.addStretch()
        controls_layout.addLayout(buttons_layout)
        
        # Status
        self.logging_status = QLabel("Ready to record")
        self.logging_status.setStyleSheet("font-weight: bold; padding: 5px;")
        controls_layout.addWidget(self.logging_status)
        
        layout.addWidget(controls_group)
        
        # Export Options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        export_buttons = QHBoxLayout()
        
        json_btn = QPushButton("Export as JSON")
        json_btn.clicked.connect(lambda: self.export_logged_data('json'))
        export_buttons.addWidget(json_btn)
        
        csv_btn = QPushButton("Export as CSV")
        csv_btn.clicked.connect(lambda: self.export_logged_data('csv'))
        export_buttons.addWidget(csv_btn)
        
        excel_btn = QPushButton("Export as Excel")
        excel_btn.clicked.connect(lambda: self.export_logged_data('excel'))
        export_buttons.addWidget(excel_btn)
        
        export_buttons.addStretch()
        
        analysis_btn = QPushButton("Create Analysis Report")
        analysis_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        analysis_btn.clicked.connect(self.create_analysis_report)
        export_buttons.addWidget(analysis_btn)
        
        export_layout.addLayout(export_buttons)
        layout.addWidget(export_group)
        
        # Session Statistics
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_info_layout = QHBoxLayout()
        
        self.stats_duration = QLabel("Duration: 0s")
        self.stats_points = QLabel("Data Points: 0")
        self.stats_rate = QLabel("Rate: 0/sec")
        self.stats_ecus = QLabel("Active ECUs: 0")
        
        stats_info_layout.addWidget(self.stats_duration)
        stats_info_layout.addWidget(QLabel("|"))
        stats_info_layout.addWidget(self.stats_points)
        stats_info_layout.addWidget(QLabel("|"))
        stats_info_layout.addWidget(self.stats_rate)
        stats_info_layout.addWidget(QLabel("|"))
        stats_info_layout.addWidget(self.stats_ecus)
        stats_info_layout.addStretch()
        
        stats_layout.addLayout(stats_info_layout)
        
        # Live Preview (kleine Tabelle)
        self.live_data_preview = QTextEdit()
        self.live_data_preview.setMaximumHeight(120)
        self.live_data_preview.setReadOnly(True)
        self.live_data_preview.setPlainText("Live data preview will appear here when recording...")
        stats_layout.addWidget(self.live_data_preview)
        
        layout.addWidget(stats_group)
        
        return widget
    
    def create_enhanced_seedkey_tab(self):
        """Enhanced Seed/Key mit Bruteforce"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Advanced Seed/Key & Bruteforce Attack")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Enhanced Key Generation
        keygen_group = QGroupBox("Enhanced Key Generation")
        keygen_layout = QVBoxLayout(keygen_group)
        
        # Algorithm and Seed Input
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("Algorithm:"))
        self.enhanced_algorithm_combo = QComboBox()
        if hasattr(self, 'seed_key_generator') and self.seed_key_generator:
            self.enhanced_algorithm_combo.addItems(self.seed_key_generator.get_available_algorithms())
        input_layout.addWidget(self.enhanced_algorithm_combo)
        
        input_layout.addStretch()
        keygen_layout.addLayout(input_layout)
        
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("Seed:"))
        self.enhanced_seed_input = QLineEdit()
        self.enhanced_seed_input.setPlaceholderText("z.B. 1234ABCD")
        seed_layout.addWidget(self.enhanced_seed_input)
        
        generate_enhanced_btn = QPushButton("Generate Key")
        generate_enhanced_btn.clicked.connect(self.generate_enhanced_key)
        seed_layout.addWidget(generate_enhanced_btn)
        keygen_layout.addLayout(seed_layout)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self.enhanced_key_output = QLineEdit()
        self.enhanced_key_output.setReadOnly(True)
        key_layout.addWidget(self.enhanced_key_output)
        
        copy_key_btn = QPushButton("Copy")
        copy_key_btn.clicked.connect(self.copy_enhanced_key)
        key_layout.addWidget(copy_key_btn)
        keygen_layout.addLayout(key_layout)
        
        layout.addWidget(keygen_group)
        
        # Bruteforce Attack Section
        bf_group = QGroupBox("Intelligent Bruteforce Attack")
        bf_layout = QVBoxLayout(bf_group)
        
        # Attack Strategy
        strategy_layout = QHBoxLayout()
        strategy_btn = QPushButton("Suggest Attack Strategy")
        strategy_btn.setStyleSheet("background-color: #2196F3; color: white;")
        strategy_btn.clicked.connect(self.suggest_bruteforce_strategy)
        strategy_layout.addWidget(strategy_btn)
        
        strategy_layout.addStretch()
        bf_layout.addLayout(strategy_layout)
        
        # Attack Controls
        attack_controls = QHBoxLayout()
        
        self.bf_start_btn = QPushButton("Start Bruteforce")
        self.bf_start_btn.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        self.bf_start_btn.clicked.connect(self.start_bruteforce)
        attack_controls.addWidget(self.bf_start_btn)
        
        self.bf_stop_btn = QPushButton("Stop Attack")
        self.bf_stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.bf_stop_btn.setEnabled(False)
        self.bf_stop_btn.clicked.connect(self.stop_bruteforce)
        attack_controls.addWidget(self.bf_stop_btn)
        
        attack_controls.addStretch()
        bf_layout.addLayout(attack_controls)
        
        # Progress and Status
        progress_layout = QVBoxLayout()
        
        self.bf_status = QLabel("Ready for attack")
        self.bf_status.setStyleSheet("font-weight: bold; padding: 5px;")
        progress_layout.addWidget(self.bf_status)
        
        self.bf_progress = QProgressBar()
        self.bf_progress.setVisible(True)
        progress_layout.addWidget(self.bf_progress)
        
        bf_layout.addLayout(progress_layout)
        layout.addWidget(bf_group)
        
        # Attack History and Statistics
        history_layout = QHBoxLayout()
        
        # Attack History (Left)
        history_group = QGroupBox("Attack History")
        history_group_layout = QVBoxLayout(history_group)
        
        self.attack_history = QListWidget()
        self.attack_history.setMaximumHeight(150)
        history_group_layout.addWidget(self.attack_history)
        
        history_buttons = QHBoxLayout()
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self.clear_bruteforce_history)
        history_buttons.addWidget(clear_history_btn)
        
        export_history_btn = QPushButton("Export History")
        export_history_btn.clicked.connect(self.export_attack_history)
        history_buttons.addWidget(export_history_btn)
        
        history_buttons.addStretch()
        history_group_layout.addLayout(history_buttons)
        
        history_widget = QWidget()
        history_widget.setLayout(history_group_layout)
        history_layout.addWidget(history_widget)
        
        # Statistics (Right)
        stats_group = QGroupBox("Attack Statistics")
        stats_group_layout = QVBoxLayout(stats_group)
        
        stats_btn = QPushButton("Show Statistics")
        stats_btn.clicked.connect(self.show_bruteforce_stats)
        stats_group_layout.addWidget(stats_btn)
        
        # Attack Methods Overview
        methods_info = QTextEdit()
        methods_info.setReadOnly(True)
        methods_info.setMaximumHeight(100)
        methods_info.setPlainText("""Attack Methods:
1. Known Algorithms - Test known seed/key algorithms
2. Mathematical Patterns - XOR, shifts, rotations
3. Dictionary Attack - Common keys and variations
4. Bit Transformations - CRC, LFSR, nibble swaps  
5. Limited Brute Force - Systematic key space search""")
        stats_group_layout.addWidget(methods_info)
        
        stats_widget = QWidget()
        stats_widget.setLayout(stats_group_layout)
        history_layout.addWidget(stats_widget)
        
        layout.addLayout(history_layout)
        
        return widget
    
    def create_feature_activation_tab(self):
        """Feature Activation Matrix Tab"""
        if not FEATURE_ACTIVATION_AVAILABLE:
            # Fallback wenn nicht verfügbar
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            header = QLabel("🔧 Feature-Aktivierung")
            header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
            layout.addWidget(header)
            
            warning_label = QLabel("⚠️ Feature Activation Matrix nicht verfügbar")
            warning_label.setStyleSheet("color: orange; font-size: 14px; padding: 20px;")
            layout.addWidget(warning_label)
            
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setPlainText("""Die Feature-Aktivierungsmatrix ermöglicht:

• Intelligente Fahrzeugerkennung
• Anzeige nur verfügbarer Features
• Cross-ECU Abhängigkeiten berücksichtigen
• Benutzerfreundliche Aktivierung ohne Vorkenntnisse
• Automatische Validierung und Sicherheitsprüfungen

Installieren Sie das FeatureActivationMatrix-Modul für diese Funktionalität.""")
            layout.addWidget(info_text)
            
            layout.addStretch()
            return widget
        
        # Erstelle Feature Activation Widget
        widget = FeatureActivationWidget(self.feature_activation_matrix)
        return widget
    
    def create_hardware_validation_tab(self):
        """Hardware Validation Tab mit detaillierter Übersicht"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Hardware-Validierung & Kompatibilitätsprüfung")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Hardware-Scan Sektion
        scan_group = QGroupBox("Hardware-Scan")
        scan_layout = QVBoxLayout(scan_group)
        
        scan_buttons = QHBoxLayout()
        
        self.hw_scan_button = QPushButton("Hardware-Scan starten")
        self.hw_scan_button.clicked.connect(self.start_hardware_scan)
        scan_buttons.addWidget(self.hw_scan_button)
        
        self.hw_refresh_button = QPushButton("Aktualisieren")
        self.hw_refresh_button.clicked.connect(self.refresh_hardware_status)
        scan_buttons.addWidget(self.hw_refresh_button)
        
        scan_buttons.addStretch()
        scan_layout.addLayout(scan_buttons)
        
        # Hardware-Status Tabelle (größer als im Feature Tab)
        self.main_hardware_table = QTableWidget()
        self.main_hardware_table.setColumnCount(6)
        self.main_hardware_table.setHorizontalHeaderLabels([
            "Hardware-Komponente", "ECU", "Detection-Methode", "Status", "Vertrauen", "Details"
        ])
        
        # Tabellen-Layout optimieren
        header = self.main_hardware_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        scan_layout.addWidget(self.main_hardware_table)
        layout.addWidget(scan_group)
        
        # Hardware-Kategorien Übersicht
        categories_group = QGroupBox("Hardware-Kategorien")
        categories_layout = QVBoxLayout(categories_group)
        
        # Kategorie-Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.hw_category_filter = QComboBox()
        self.hw_category_filter.addItems([
            "Alle", "ADAS & Kameras", "Beleuchtung", "Komfort", 
            "Fahrwerk", "Audio", "Sicherheit", "Connectivity", "Sensoren"
        ])
        self.hw_category_filter.currentTextChanged.connect(self.filter_hardware_by_category)
        filter_layout.addWidget(self.hw_category_filter)
        
        filter_layout.addStretch()
        categories_layout.addLayout(filter_layout)
        
        # Hardware-Statistiken
        self.hw_stats_layout = QHBoxLayout()
        self.update_hardware_statistics()
        categories_layout.addLayout(self.hw_stats_layout)
        
        layout.addWidget(categories_group)
        
        # Hardware-Empfehlungen
        recommendations_group = QGroupBox("Hardware-Empfehlungen")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.hw_recommendations_table = QTableWidget()
        self.hw_recommendations_table.setColumnCount(4)
        self.hw_recommendations_table.setHorizontalHeaderLabels([
            "Empfohlene Hardware", "Benötigt für Feature", "Installationsaufwand", "Geschätzte Kosten"
        ])
        self.hw_recommendations_table.setMaximumHeight(150)
        
        recommendations_layout.addWidget(self.hw_recommendations_table)
        
        # Empfehlungen generieren Button
        rec_buttons = QHBoxLayout()
        self.generate_recommendations_button = QPushButton("Empfehlungen generieren")
        self.generate_recommendations_button.clicked.connect(self.generate_hardware_recommendations)
        rec_buttons.addWidget(self.generate_recommendations_button)
        rec_buttons.addStretch()
        
        recommendations_layout.addLayout(rec_buttons)
        layout.addWidget(recommendations_group)
        
        return widget
    
    # Hardware-Tab Methoden
    def start_hardware_scan(self):
        """Starte Hardware-Scan"""
        if not hasattr(self, 'feature_activation_matrix') or not self.feature_activation_matrix:
            print("[WARN] Feature Activation Matrix nicht verfügbar")
            return
        
        self.hw_scan_button.setEnabled(False)
        self.hw_scan_button.setText("Scanning...")
        
        try:
            # Simuliere Hardware-Scan
            if hasattr(self.feature_activation_matrix, 'hardware_checker'):
                checker = self.feature_activation_matrix.hardware_checker
                
                # Mock detected ECUs für Demo
                mock_ecus = [
                    {'name': 'BSI Body Control'},
                    {'name': 'CMM Engine Control'},
                    {'name': 'NAC Infotainment'},
                    {'name': 'COMBINE Instrument Cluster'},
                    {'name': 'ABS Control'},
                    {'name': 'CLIMATE Control'}
                ]
                
                # Mock vehicle
                mock_vehicle = type('MockProfile', (), {
                    'name': 'Hardware Scan Test',
                    'production_years': '2020-2023'
                })()
                
                # Populate hardware table
                self.populate_hardware_table(checker, mock_ecus, mock_vehicle)
                
            print("[INFO] Hardware-Scan abgeschlossen")
            
        except Exception as e:
            print(f"[ERROR] Hardware-Scan Fehler: {e}")
        
        finally:
            self.hw_scan_button.setEnabled(True)
            self.hw_scan_button.setText("Hardware-Scan starten")
    
    def populate_hardware_table(self, checker, detected_ecus, vehicle_profile):
        """Fülle Hardware-Tabelle mit Scan-Ergebnissen"""
        hardware_components = checker.hardware_components
        
        self.main_hardware_table.setRowCount(len(hardware_components))
        
        row = 0
        for hw_id, component in hardware_components.items():
            # Hardware Name
            self.main_hardware_table.setItem(row, 0, QTableWidgetItem(component.name))
            
            # ECU
            self.main_hardware_table.setItem(row, 1, QTableWidgetItem(component.ecu_location))
            
            # Detection Method
            method_display = {
                'parameter_read': 'Parameter lesen',
                'ecu_presence': 'ECU vorhanden',
                'sensor_array_check': 'Sensor-Array',
                'actuator_test': 'Aktuator-Test',
                'communication_test': 'Kommunikation',
                'system_check': 'System-Check',
                'video_signal_check': 'Video-Signal',
                'radar_signal_check': 'Radar-Signal',
                'led_matrix_test': 'LED Matrix',
                'servo_motor_test': 'Servo-Motor'
            }.get(component.detection_method, component.detection_method)
            
            self.main_hardware_table.setItem(row, 2, QTableWidgetItem(method_display))
            
            # Simuliere Hardware-Check
            validation = checker._validate_hardware_component(component, detected_ecus, vehicle_profile)
            
            # Status
            status = "Verfügbar" if validation.is_available else "Nicht verfügbar"
            status_item = QTableWidgetItem(status)
            
            # Farbkodierung
            if validation.is_available:
                status_item.setBackground(QColor(144, 238, 144))  # Grün
            else:
                status_item.setBackground(QColor(255, 182, 193))  # Rot
            
            self.main_hardware_table.setItem(row, 3, status_item)
            
            # Vertrauen
            confidence = validation.confidence_level * 100
            self.main_hardware_table.setItem(row, 4, QTableWidgetItem(f"{confidence:.1f}%"))
            
            # Details
            details = validation.detection_details.get('method', 'Standard-Erkennung')
            self.main_hardware_table.setItem(row, 5, QTableWidgetItem(details))
            
            row += 1
        
        self.main_hardware_table.resizeColumnsToContents()
        self.update_hardware_statistics()
    
    def refresh_hardware_status(self):
        """Aktualisiere Hardware-Status"""
        self.start_hardware_scan()  # Re-run scan
    
    def filter_hardware_by_category(self, category):
        """Filtere Hardware nach Kategorie"""
        if category == "Alle":
            # Zeige alle Reihen
            for row in range(self.main_hardware_table.rowCount()):
                self.main_hardware_table.setRowHidden(row, False)
        else:
            # Definiere Kategorie-Mappings
            category_mappings = {
                "ADAS & Kameras": ['front_camera', 'rear_camera', 'surround_cameras', 'radar_front', 'radar_rear', 'lidar_sensor', 'night_vision', 'driver_monitoring'],
                "Beleuchtung": ['light_sensor', 'adaptive_light', 'matrix_led', 'dynamic_bending_light', 'led_daytime_running'],
                "Komfort": ['head_up_display', 'massage_seats', 'heated_steering_wheel', 'ventilated_seats', 'automatic_climate'],
                "Fahrwerk": ['air_suspension', 'adaptive_dampers', 'esp_abs_system'],
                "Audio": ['bluetooth_module', 'premium_sound', 'active_noise_cancellation'],
                "Sicherheit": ['esp_abs_system', 'night_vision', 'driver_monitoring'],
                "Connectivity": ['cellular_modem', 'wifi_hotspot'],
                "Sensoren": ['rain_sensor', 'parking_sensors_rear', 'ultrasonic_sensors_front']
            }
            
            target_components = category_mappings.get(category, [])
            
            for row in range(self.main_hardware_table.rowCount()):
                item = self.main_hardware_table.item(row, 0)
                if item:
                    # Vereinfachte Überprüfung - schaue ob Hardware-Name mit Kategorie übereinstimmt
                    hardware_name = item.text().lower()
                    show_row = any(comp in hardware_name for comp in target_components)
                    self.main_hardware_table.setRowHidden(row, not show_row)
    
    def update_hardware_statistics(self):
        """Update Hardware-Statistiken"""
        # Clear existing stats
        while self.hw_stats_layout.count():
            child = self.hw_stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not hasattr(self, 'main_hardware_table'):
            return
        
        total_components = self.main_hardware_table.rowCount()
        available_count = 0
        
        for row in range(total_components):
            status_item = self.main_hardware_table.item(row, 3)
            if status_item and status_item.text() == "Verfügbar":
                available_count += 1
        
        # Stats Labels
        total_label = QLabel(f"Gesamt: {total_components}")
        total_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.hw_stats_layout.addWidget(total_label)
        
        available_label = QLabel(f"Verfügbar: {available_count}")
        available_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.hw_stats_layout.addWidget(available_label)
        
        unavailable_count = total_components - available_count
        unavailable_label = QLabel(f"Nicht verfügbar: {unavailable_count}")
        unavailable_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
        self.hw_stats_layout.addWidget(unavailable_label)
        
        if total_components > 0:
            compatibility = (available_count / total_components) * 100
            compat_label = QLabel(f"Kompatibilität: {compatibility:.1f}%")
            compat_label.setStyleSheet("font-weight: bold; padding: 5px;")
            self.hw_stats_layout.addWidget(compat_label)
        
        self.hw_stats_layout.addStretch()
    
    def generate_hardware_recommendations(self):
        """Generiere Hardware-Empfehlungen"""
        if not hasattr(self, 'feature_activation_matrix') or not self.feature_activation_matrix:
            print("[WARN] Feature Activation Matrix nicht verfügbar")
            return
        
        try:
            checker = self.feature_activation_matrix.hardware_checker
            
            # Mock vehicle für Empfehlungen
            mock_vehicle = type('MockProfile', (), {
                'name': 'Empfehlungs-Test',
                'production_years': '2018-2022'
            })()
            
            # Gewünschte Features für Demo
            target_features = [
                'matrix_led_headlights', 'surround_view', 'adaptive_cruise_control',
                'massage_seat_function', 'premium_audio_system', 'air_suspension_system'
            ]
            
            recommendations = checker.get_hardware_recommendations(mock_vehicle, target_features)
            
            # Populate recommendations table
            self.hw_recommendations_table.setRowCount(len(recommendations))
            
            for row, rec in enumerate(recommendations):
                self.hw_recommendations_table.setItem(row, 0, QTableWidgetItem(rec['hardware_name']))
                self.hw_recommendations_table.setItem(row, 1, QTableWidgetItem(rec['required_for_feature']))
                
                complexity_map = {
                    'low': 'Einfach',
                    'medium': 'Mittel', 
                    'high': 'Schwer',
                    'very_high': 'Sehr schwer'
                }
                complexity = complexity_map.get(rec['installation_complexity'], rec['installation_complexity'])
                self.hw_recommendations_table.setItem(row, 2, QTableWidgetItem(complexity))
                
                cost = rec['estimated_cost']
                cost_text = f"{cost['min_cost']}-{cost['max_cost']} {cost['currency']}"
                self.hw_recommendations_table.setItem(row, 3, QTableWidgetItem(cost_text))
            
            self.hw_recommendations_table.resizeColumnsToContents()
            print("[INFO] Hardware-Empfehlungen generiert")
            
        except Exception as e:
            print(f"[ERROR] Empfehlungs-Fehler: {e}")
        
        # Connect to vehicle profile system if available
        if self.vehicle_profile_system:
            # Integration mit Vehicle Profile System
            def on_vehicle_detected(profile):
                if profile and hasattr(profile, 'data'):
                    # Mock detected ECUs basierend auf Fahrzeugprofil
                    mock_ecus = []
                    if hasattr(profile, 'ecu_layout'):
                        for ecu_name, ecu_info in profile.ecu_layout.items():
                            mock_ecus.append({'name': f"{ecu_name.upper()} {ecu_info.get('name', '')}"})
                    
                    # Analysiere Fahrzeugfähigkeiten
                    widget.activation_matrix.analyze_vehicle_capabilities(profile, mock_ecus)
            
            # Connect vehicle profile changes
            if hasattr(self.vehicle_profile_system, 'profileChanged'):
                self.vehicle_profile_system.profileChanged.connect(on_vehicle_detected)
        
        return widget
    
    # Event Handlers - vereinfacht
    def simple_ecu_scan(self):
        """ECU-Scan nur mit echter Hardware-Verbindung"""
        self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting ECU scan...")
        
        # Prüfe ob Hardware wirklich verbunden ist
        if not self.hardware_vci or not getattr(self.hardware_vci, 'connected', False):
            self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: No hardware VCI connected - cannot scan ECUs")
            self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] Connect hardware interface first for real ECU detection")
            return
        
        # Echter ECU-Scan nur mit Hardware
        try:
            # Hier würde die echte ECU-Detection stattfinden
            detected_ecus = self.hardware_vci.scan_for_ecus() if hasattr(self.hardware_vci, 'scan_for_ecus') else []
            
            if detected_ecus:
                for ecu in detected_ecus:
                    self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found: {ecu}")
                self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] ECU scan completed - {len(detected_ecus)} ECUs found")
            else:
                self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] No ECUs detected on connected hardware")
        except Exception as e:
            self.ecu_results.append(f"[{datetime.now().strftime('%H:%M:%S')}] ECU scan failed: {str(e)}")
    
    def simple_backup(self):
        """Vereinfachtes Backup"""
        try:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            # Hier würde das Backup-System aufgerufen werden
            QMessageBox.information(self, "Backup", f"Backup '{backup_name}' would be created")
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Backup-Fehler: {e}")
    
    def generate_key(self):
        """Key generieren"""
        seed = self.seed_input.text()
        algorithm = self.algorithm_combo.currentText()
        
        if not seed:
            QMessageBox.warning(self, "Fehler", "Bitte Seed eingeben")
            return
        
        try:
            key = self.seed_key_generator.generate_key(seed, algorithm)
            if key:
                self.key_output.setText(key)
            else:
                QMessageBox.warning(self, "Fehler", "Key-Generierung fehlgeschlagen")
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler: {e}")
    
    # Setup-Methoden
    def setup_vci_integration(self):
        """VCI Integration - vereinfacht"""
        try:
            from VCIAdapterShared import VCIAdapterShared, ensure_shared_vci_server
            
            # Ensure SharedVCI server is running
            ensure_shared_vci_server()
            
            self.vci_adapter = VCIAdapterShared()
            print("[INFO] SharedVCI Integration ready")
        except Exception as e:
            print(f"[WARN] SharedVCI not available: {e}")
            # Fallback to regular VCI
            try:
                from VCIAdapter import VCIAdapter
                self.vci_adapter = VCIAdapter()
                print("[INFO] Fallback VCI Integration ready")
            except Exception as e2:
                print(f"[WARN] No VCI available: {e2}")
                self.vci_adapter = None
    
    def setup_auto_features(self):
        """Auto-Features - vereinfacht"""
        # Auto-Initialize nach 2 Sekunden
        QTimer.singleShot(2000, self.auto_initialize)
    
    def auto_initialize(self):
        """Auto-Initialisierung"""
        print("[INFO] Auto-initializing enhanced features...")
        self.init_enhanced_modules()
    
    def init_enhanced_modules(self):
        """Enhanced Module initialisieren"""
        controller = None
        
        if hasattr(self, 'vci_adapter') and self.vci_adapter:
            controller = self.vci_adapter
        elif hasattr(self, 'serialController') and self.serialController:
            controller = self.serialController
        
        if controller:
            if not self.ecu_detector:
                self.ecu_detector = SimpleECUDetector(controller)
            if not self.multi_ecu_manager:
                self.multi_ecu_manager = MultiECUManager(controller)
            
            # Dashboard verbinden
            if hasattr(self, 'live_dashboard') and self.live_dashboard:
                self.live_dashboard.set_controller(controller)
    
    def setup_keyboard_shortcuts(self):
        """Keyboard Shortcuts"""
        # F1 für Hilfe
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_help)
        
        # Tab Navigation (Ctrl+1-9)
        for i in range(min(9, self.main_tabs.count())):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.main_tabs.setCurrentIndex(idx))
    
    def setup_themes(self):
        """Theme Setup - vereinfacht"""
        pass  # Kann später erweitert werden
    
    def setup_help_system(self):
        """Help & Manual System Integration"""
        try:
            if HELP_SYSTEM_AVAILABLE:
                # Standard Help-Integration
                success = HelpSystemPatch.patch_main_window(self)
                if success:
                    print("[OK] Standard Help-Integration erfolgreich")
            else:
                print("[INFO] Help-System nicht verfügbar - verwende einfache Hilfe")
                
        except Exception as e:
            print(f"[ERROR] Help-System Setup fehlgeschlagen: {e}")
            # Fallback to simple help
            pass
    
    def show_help(self):
        """Hilfe anzeigen"""
        help_text = """
        PyPSADiag Enhanced - Hilfe
        
        Keyboard Shortcuts:
        • F1 - Diese Hilfe
        • Ctrl+1-9 - Tab Navigation
        
        Features:
        • ECU Detection - Intelligente ECU-Erkennung
        • Multi-ECU Management - Parallele Verwaltung
        • Backup/Restore - Datensicherung
        • Search/Filter - Erweiterte Suche
        • Seed/Key Generator - Sicherheits-Keys
        • Live Dashboard - Echtzeit-Daten
        • Advanced Diagnostics - Erweiterte Diagnose
        """
        
        # Erweiterte Features hinzufügen falls verfügbar
        if any([ECU_DATABASE_AVAILABLE, PROTOCOL_ANALYZER_AVAILABLE, 
                VEHICLE_PROFILE_AVAILABLE, DATA_LOGGING_AVAILABLE, 
                SEED_KEY_BF_AVAILABLE]):
            help_text += "\n        Erweiterte Features:"
            
            if ECU_DATABASE_AVAILABLE:
                help_text += "\n        • ECU Database - VIN-Decoder & ECU-Suche"
            if PROTOCOL_ANALYZER_AVAILABLE:
                help_text += "\n        • Protocol Analyzer - CAN-Bus Analyse"
            if VEHICLE_PROFILE_AVAILABLE:
                help_text += "\n        • Vehicle Profiles - Auto-Erkennung"
            if DATA_LOGGING_AVAILABLE:
                help_text += "\n        • Data Logging - Session Recording"
            if SEED_KEY_BF_AVAILABLE:
                help_text += "\n        • Advanced Seed/Key - Bruteforce Attack"
            if FEATURE_ACTIVATION_AVAILABLE:
                help_text += "\n        • Feature Aktivierung - Intelligente Feature-Matrix"
        
        QMessageBox.information(self, "PyPSADiag Enhanced - Hilfe", help_text)
    
    # === Vehicle Profile System Methods ===
    
    def refresh_profiles_list(self):
        """Aktualisiere Vehicle Profile Liste"""
        try:
            if not self.vehicle_profile_system:
                return
            
            self.profiles_list.clear()
            profiles = self.vehicle_profile_system.get_all_profiles()
            
            # Gruppiere nach Marken
            brands = {}
            for profile_id, profile in profiles.items():
                brand = profile.brand
                if brand not in brands:
                    brands[brand] = []
                brands[brand].append((profile_id, profile))
            
            # Füge nach Marken sortiert hinzu
            for brand in sorted(brands.keys()):
                brand_vehicles = brands[brand]
                # Sortiere Fahrzeuge nach Model
                brand_vehicles.sort(key=lambda x: x[1].model)
                
                for profile_id, profile in brand_vehicles:
                    display_name = f"{profile.brand} {profile.model} ({profile.production_years})"
                    item = QListWidgetItem(display_name)
                    item.setData(32, profile_id)  # Store profile_id as data
                    self.profiles_list.addItem(item)
            
            # Statistiken aktualisieren
            stats = self.vehicle_profile_system.get_vehicle_statistics()
            total = stats.get('total_vehicles', 0)
            brands_count = stats.get('brands', 0)
            
            print(f"[INFO] Vehicle Profiles geladen: {total} Fahrzeuge, {brands_count} Marken")
            
        except Exception as e:
            print(f"[ERROR] Profile refresh error: {e}")
    
    def select_profile(self, item):
        """Wähle Vehicle Profile aus"""
        try:
            profile_id = item.data(32)
            if not profile_id:
                return
            
            profile = self.vehicle_profile_system.get_profile_by_id(profile_id)
            if profile:
                self.vehicle_profile_system.set_current_profile(profile)
                self.update_profile_display(profile)
                
        except Exception as e:
            print(f"[ERROR] Profile selection error: {e}")
    
    def update_profile_display(self, profile):
        """Aktualisiere Profile Display"""
        try:
            if not profile:
                self.current_profile_label.setText("No profile selected")
                self.profile_details.clear()
                return
            
            # Update current profile label
            self.current_profile_label.setText(f"{profile.name} ({profile.brand})")
            
            # Update profile details
            details = []
            details.append(f"Fahrzeug: {profile.name}")
            details.append(f"Marke: {profile.brand}")
            details.append(f"Model: {profile.model}")
            details.append(f"Produktionsjahre: {profile.production_years}")
            details.append(f"VIN Patterns: {', '.join(profile.vin_patterns[:3])}{'...' if len(profile.vin_patterns) > 3 else ''}")
            
            # ECU Layout
            details.append(f"\nECU Layout ({len(profile.ecu_layout)} ECUs):")
            for ecu_name, ecu_info in list(profile.ecu_layout.items())[:6]:
                if isinstance(ecu_info, dict):
                    ecu_display = f"{ecu_name.upper()}: {ecu_info.get('name', 'Unknown')} @ {ecu_info.get('address', 'N/A')}"
                else:
                    ecu_display = f"{ecu_name.upper()}: {ecu_info}"
                details.append(f"  - {ecu_display}")
            
            if len(profile.ecu_layout) > 6:
                details.append(f"  ... und {len(profile.ecu_layout) - 6} weitere ECUs")
            
            # Engine Variants
            if profile.engine_variants:
                details.append(f"\nMotor-Varianten ({len(profile.engine_variants)}):")
                for engine_id, engine_info in list(profile.engine_variants.items())[:4]:
                    if isinstance(engine_info, dict):
                        details.append(f"  - {engine_id}: {engine_info}")
                    else:
                        details.append(f"  - {engine_id}: {engine_info}")
                if len(profile.engine_variants) > 4:
                    details.append(f"  ... und {len(profile.engine_variants) - 4} weitere")
            
            # Common Procedures
            if profile.common_procedures:
                details.append(f"\nVerfügbare Prozeduren ({len(profile.common_procedures)}):")
                for proc in profile.common_procedures[:8]:
                    details.append(f"  - {proc}")
                if len(profile.common_procedures) > 8:
                    details.append(f"  ... und {len(profile.common_procedures) - 8} weitere")
            
            # Special Notes
            if profile.special_notes:
                details.append(f"\nBesonderheiten:")
                for note in profile.special_notes[:3]:
                    details.append(f"  - {note}")
                if len(profile.special_notes) > 3:
                    details.append(f"  ... und {len(profile.special_notes) - 3} weitere")
            
            self.profile_details.setText('\n'.join(details))
            
        except Exception as e:
            print(f"[ERROR] Profile display error: {e}")
    
    def auto_detect_vehicle(self):
        """Auto-Detect Vehicle via VIN oder ECU-Scan"""
        try:
            if not self.vehicle_profile_system:
                QMessageBox.warning(self, "Vehicle Profile", "Vehicle Profile System nicht verfügbar!")
                return
            
            # Dialog für VIN-Eingabe
            from PySide6.QtWidgets import QInputDialog
            vin, ok = QInputDialog.getText(self, "Vehicle Detection", 
                                         "VIN eingeben für Auto-Detection (oder leer lassen für ECU-basierte Erkennung):")
            
            if ok:
                if vin.strip():
                    # VIN-basierte Erkennung
                    result = self.vehicle_profile_system.detect_vehicle_by_vin(vin.strip())
                    
                    if result['profile']:
                        profile = result['profile']
                        confidence = result['confidence']
                        
                        self.update_profile_display(profile)
                        print(f"[INFO] Fahrzeug erkannt: {profile.name} (Konfidenz: {confidence}%)")
                        
                        # Aktualisiere Liste-Auswahl
                        for i in range(self.profiles_list.count()):
                            item = self.profiles_list.item(i)
                            if item.text().startswith(f"{profile.brand} {profile.model}"):
                                self.profiles_list.setCurrentItem(item)
                                break
                    else:
                        QMessageBox.information(self, "Vehicle Detection", 
                                              f"Kein Fahrzeug für VIN '{vin}' gefunden.\n\nVIN Decoded Info:\n{result.get('vin_decoded', {})}")
                else:
                    # ECU-basierte Erkennung (simuliert)
                    simulated_ecus = [
                        {'address': 0x180, 'name': 'Engine ECU'},
                        {'address': 0x240, 'name': 'BSI Body Control'},
                        {'address': 0x2C0, 'name': 'NAC Infotainment'},
                        {'address': 0x160, 'name': 'Combine Cluster'}
                    ]
                    
                    result = self.vehicle_profile_system.detect_vehicle_by_ecus(simulated_ecus)
                    
                    if result and result['profile']:
                        profile = result['profile']
                        score = result['score']
                        
                        self.update_profile_display(profile)
                        print(f"[INFO] Fahrzeug erkannt via ECUs: {profile.name} (Score: {score:.1f})")
                        
                        # Aktualisiere Liste-Auswahl
                        for i in range(self.profiles_list.count()):
                            item = self.profiles_list.item(i)
                            if item.text().startswith(f"{profile.brand} {profile.model}"):
                                self.profiles_list.setCurrentItem(item)
                                break
                    else:
                        QMessageBox.information(self, "Vehicle Detection", 
                                              "Kein Fahrzeug basierend auf gefundenen ECUs erkannt.\n\nECU-Scan erforderlich.")
                
        except Exception as e:
            QMessageBox.critical(self, "Auto-Detection Error", f"Fehler bei Auto-Detection: {e}")
            print(f"[ERROR] Auto-Detection Fehler: {e}")
    
    def create_settings_tab(self):
        """Settings Tab mit Theme-Optionen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("PyPSADiag Enhanced - Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #0066cc;")
        layout.addWidget(header)
        
        # Theme Settings Group
        theme_group = QGroupBox("Appearance & Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        # Current theme display
        theme_info_layout = QHBoxLayout()
        theme_info_layout.addWidget(QLabel("Current Theme:"))
        
        self.current_theme_label = QLabel("Dark Professional")
        self.current_theme_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        theme_info_layout.addWidget(self.current_theme_label)
        theme_info_layout.addStretch()
        theme_layout.addLayout(theme_info_layout)
        
        # Theme buttons
        theme_buttons_layout = QHBoxLayout()
        
        # Dark theme button
        dark_theme_btn = QPushButton("Dark Theme")
        dark_theme_btn.setStyleSheet("background-color: #2b2b2b; color: white; font-weight: bold; padding: 8px;")
        dark_theme_btn.clicked.connect(lambda: self.apply_theme("dark"))
        theme_buttons_layout.addWidget(dark_theme_btn)
        
        # Light theme button  
        light_theme_btn = QPushButton("Light Theme")
        light_theme_btn.setStyleSheet("background-color: #f0f0f0; color: black; font-weight: bold; padding: 8px;")
        light_theme_btn.clicked.connect(lambda: self.apply_theme("light"))
        theme_buttons_layout.addWidget(light_theme_btn)
        
        # Toggle theme button
        toggle_theme_btn = QPushButton("Toggle Theme")
        toggle_theme_btn.setStyleSheet("background-color: #0066cc; color: white; font-weight: bold; padding: 8px;")
        toggle_theme_btn.clicked.connect(self.toggle_theme)
        theme_buttons_layout.addWidget(toggle_theme_btn)
        
        theme_layout.addLayout(theme_buttons_layout)
        
        # Theme info
        theme_info = QLabel("Themes support PSA/Stellantis design elements with professional appearance.")
        theme_info.setStyleSheet("color: #666666; font-style: italic; padding: 5px;")
        theme_layout.addWidget(theme_info)
        
        layout.addWidget(theme_group)
        
        # System Information Group
        system_group = QGroupBox("System Information")
        system_layout = QVBoxLayout(system_group)
        
        # System info
        system_info = [
            f"PyPSADiag Enhanced Version: 2.0",
            f"Vehicle Profiles: {len(self.vehicle_profile_system.profiles) if self.vehicle_profile_system else 'N/A'}",
            f"Hardware Components: {len(self.feature_activation_matrix.hardware_checker.hardware_components) if self.feature_activation_matrix and hasattr(self.feature_activation_matrix, 'hardware_checker') and self.feature_activation_matrix.hardware_checker else 'N/A'}",
            f"Theme Manager: {'Available' if self.theme_manager else 'Not Available'}",
            f"VCI Detection: {'Active' if self.vci_detection else 'Not Available'}",
            f"Connected VCIs: {len(self.vci_detection.get_connected_vcis()) if self.vci_detection else 0}",
            f"ECU/VIN Database: {'Available' if self.ecu_vin_database else 'Not Available'}",
            f"Database ECUs: {len(self.ecu_vin_database.ecu_definitions) if self.ecu_vin_database else 0}",
            f"Hardware VCI: {'Available' if self.hardware_vci else 'Not Available'}",
            f"Hardware Connected: {'Yes' if self.hardware_vci and self.hardware_vci.connected else 'No'}"
        ]
        
        for info in system_info:
            info_label = QLabel(info)
            info_label.setStyleSheet("padding: 2px; font-family: monospace;")
            system_layout.addWidget(info_label)
        
        layout.addWidget(system_group)
        
        # Module Status Group
        modules_group = QGroupBox("Module Status")
        modules_layout = QVBoxLayout(modules_group)
        
        modules_status = [
            ("ECU Database", ECU_DATABASE_AVAILABLE),
            ("Protocol Analyzer", PROTOCOL_ANALYZER_AVAILABLE),
            ("Vehicle Profiles", VEHICLE_PROFILE_AVAILABLE),
            ("Data Logging", DATA_LOGGING_AVAILABLE),
            ("Seed/Key Bruteforce", SEED_KEY_BF_AVAILABLE),
            ("Feature Activation", FEATURE_ACTIVATION_AVAILABLE),
            ("Theme Manager", THEME_MANAGER_AVAILABLE),
            ("VCI Detection", VCI_DETECTION_AVAILABLE),
            ("Automatic Backup", BACKUP_SYSTEM_AVAILABLE),
            ("ECU/VIN Database", ECU_VIN_DATABASE_AVAILABLE),
            ("Hardware VCI Interface", HARDWARE_VCI_AVAILABLE)
        ]
        
        for module_name, available in modules_status:
            status_layout = QHBoxLayout()
            status_layout.addWidget(QLabel(f"{module_name}:"))
            
            status_label = QLabel("Available" if available else "Not Available")
            status_label.setStyleSheet(f"color: {'#28a745' if available else '#dc3545'}; font-weight: bold;")
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            
            modules_layout.addLayout(status_layout)
        
        layout.addWidget(modules_group)
        
        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Export/Import theme buttons
        advanced_buttons_layout = QHBoxLayout()
        
        export_theme_btn = QPushButton("Export Current Theme")
        export_theme_btn.clicked.connect(self.export_current_theme)
        advanced_buttons_layout.addWidget(export_theme_btn)
        
        import_theme_btn = QPushButton("Import Theme")
        import_theme_btn.clicked.connect(self.import_theme)
        advanced_buttons_layout.addWidget(import_theme_btn)
        
        reset_settings_btn = QPushButton("Reset to Defaults")
        reset_settings_btn.clicked.connect(self.reset_settings)
        advanced_buttons_layout.addWidget(reset_settings_btn)
        
        advanced_layout.addLayout(advanced_buttons_layout)
        
        # Backup Management Section
        backup_section_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("Create Manual Backup")
        create_backup_btn.clicked.connect(self.create_manual_backup)
        backup_section_layout.addWidget(create_backup_btn)
        
        list_backups_btn = QPushButton("View Backups")
        list_backups_btn.clicked.connect(self.show_backup_manager)
        backup_section_layout.addWidget(list_backups_btn)
        
        backup_stats_btn = QPushButton("Backup Statistics")
        backup_stats_btn.clicked.connect(self.show_backup_stats)
        backup_section_layout.addWidget(backup_stats_btn)
        
        advanced_layout.addLayout(backup_section_layout)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        
        # Update theme label if manager available
        if self.theme_manager:
            self.update_theme_label()
            self.theme_manager.theme_changed.connect(self.update_theme_label)
        
        return widget
    
    def apply_theme(self, theme_name):
        """Theme anwenden"""
        try:
            if self.theme_manager:
                success = self.theme_manager.apply_theme(theme_name)
                if success:
                    print(f"[INFO] Theme '{theme_name}' applied successfully")
                else:
                    QMessageBox.warning(self, "Theme Error", f"Failed to apply theme '{theme_name}'")
            else:
                QMessageBox.information(self, "Theme Manager", "Theme Manager is not available")
        except Exception as e:
            QMessageBox.critical(self, "Theme Error", f"Error applying theme: {e}")
    
    def toggle_theme(self):
        """Toggle zwischen Dark und Light Theme"""
        try:
            if self.theme_manager:
                success = self.theme_manager.toggle_theme()
                if success:
                    print("[INFO] Theme toggled successfully")
                else:
                    QMessageBox.warning(self, "Theme Error", "Failed to toggle theme")
            else:
                QMessageBox.information(self, "Theme Manager", "Theme Manager is not available")
        except Exception as e:
            QMessageBox.critical(self, "Theme Error", f"Error toggling theme: {e}")
    
    def update_theme_label(self):
        """Update Theme Label"""
        if self.theme_manager and hasattr(self, 'current_theme_label'):
            current_theme = self.theme_manager.get_current_theme()
            theme_info = self.theme_manager.get_theme_info(current_theme)
            display_name = theme_info.get('name', current_theme.title())
            self.current_theme_label.setText(display_name)
    
    def export_current_theme(self):
        """Export aktuelles Theme"""
        try:
            if not self.theme_manager:
                QMessageBox.information(self, "Theme Manager", "Theme Manager is not available")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Theme", f"theme_{self.theme_manager.get_current_theme()}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                success = self.theme_manager.export_theme(self.theme_manager.get_current_theme(), filename)
                if success:
                    QMessageBox.information(self, "Export Success", f"Theme exported to {filename}")
                else:
                    QMessageBox.warning(self, "Export Error", "Failed to export theme")
                    
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting theme: {e}")
    
    def import_theme(self):
        """Import Theme"""
        try:
            if not self.theme_manager:
                QMessageBox.information(self, "Theme Manager", "Theme Manager is not available")
                return
            
            filename, _ = QFileDialog.getOpenFileName(
                self, "Import Theme", "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                success = self.theme_manager.import_theme(filename)
                if success:
                    QMessageBox.information(self, "Import Success", "Theme imported successfully")
                else:
                    QMessageBox.warning(self, "Import Error", "Failed to import theme")
                    
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing theme: {e}")
    
    def reset_settings(self):
        """Reset alle Settings zu Defaults"""
        try:
            reply = QMessageBox.question(
                self, "Reset Settings", 
                "Are you sure you want to reset all settings to defaults?\n\nThis will:\n- Reset theme to Dark\n- Clear custom themes\n- Reset all preferences",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.theme_manager:
                    # Reset theme to dark
                    self.theme_manager.apply_theme("dark")
                    
                    # Clear custom themes
                    self.theme_manager.custom_themes.clear()
                    self.theme_manager.save_theme_settings()
                
                QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults")
                print("[INFO] Settings reset to defaults")
                
        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error resetting settings: {e}")
    
    # === Backup Management Methods ===
    
    def create_manual_backup(self):
        """Erstelle manuelles Backup"""
        try:
            if not self.backup_system:
                QMessageBox.information(self, "Backup System", "Backup System is not available")
                return
            
            # Input Dialog für Backup-Namen
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                self, "Create Manual Backup", 
                "Enter backup name:",
                text=f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if ok and name:
                backup_path = self.backup_system.create_backup(name)
                if backup_path:
                    QMessageBox.information(
                        self, "Backup Created", 
                        f"Manual backup created successfully!\n\nPath: {backup_path}"
                    )
                    print(f"[INFO] Manual backup created: {backup_path}")
                else:
                    QMessageBox.warning(self, "Backup Error", "Failed to create backup")
                    
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Error creating backup: {e}")
    
    def show_backup_manager(self):
        """Zeige Backup Manager Dialog"""
        try:
            if not self.backup_system:
                QMessageBox.information(self, "Backup System", "Backup System is not available")
                return
            
            # Backup Manager Dialog erstellen
            from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                         QListWidget, QListWidgetItem, QPushButton,
                                         QLabel, QSplitter, QTextEdit)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Backup Manager")
            dialog.setModal(True)
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Info Label
            info_label = QLabel("Available Backups:")
            layout.addWidget(info_label)
            
            # Splitter für Liste und Details
            splitter = QSplitter()
            layout.addWidget(splitter)
            
            # Backup Liste
            backup_list = QListWidget()
            splitter.addWidget(backup_list)
            
            # Details Area
            details_area = QTextEdit()
            details_area.setReadOnly(True)
            splitter.addWidget(details_area)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("Refresh")
            restore_btn = QPushButton("Restore Selected")
            delete_btn = QPushButton("Delete Selected")
            close_btn = QPushButton("Close")
            
            button_layout.addWidget(refresh_btn)
            button_layout.addWidget(restore_btn)
            button_layout.addWidget(delete_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            # Load backups
            def load_backups():
                backup_list.clear()
                details_area.clear()
                
                backups = self.backup_system.list_backups()
                for backup in backups:
                    item = QListWidgetItem(backup["name"])
                    item.setData(1, backup)  # Store backup data
                    backup_list.addItem(item)
            
            # Show backup details
            def show_details():
                current_item = backup_list.currentItem()
                if current_item:
                    backup = current_item.data(1)
                    info = backup["info"]
                    
                    details = f"""Backup Details:
                    
Name: {backup['name']}
Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}
Size: {backup['size'] / 1024 / 1024:.2f} MB
Description: {info.get('description', 'N/A')}
Operation: {info.get('operation', 'N/A')}
Version: {info.get('backup_version', 'N/A')}
Created by: {info.get('created_by', 'N/A')}

Files: {info.get('file_count', 0)}
Path: {backup['path']}
"""
                    details_area.setText(details)
            
            # Restore backup
            def restore_backup():
                current_item = backup_list.currentItem()
                if current_item:
                    backup = current_item.data(1)
                    success = self.backup_system.restore_backup(backup["path"])
                    if success:
                        QMessageBox.information(dialog, "Restore Success", "Backup restored successfully!")
                        dialog.accept()
                    else:
                        QMessageBox.warning(dialog, "Restore Error", "Failed to restore backup")
            
            # Delete backup
            def delete_backup():
                current_item = backup_list.currentItem()
                if current_item:
                    backup = current_item.data(1)
                    reply = QMessageBox.question(
                        dialog, "Delete Backup",
                        f"Are you sure you want to delete this backup?\n\n{backup['name']}",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        success = self.backup_system.delete_backup(backup["path"])
                        if success:
                            load_backups()
                            QMessageBox.information(dialog, "Delete Success", "Backup deleted successfully!")
                        else:
                            QMessageBox.warning(dialog, "Delete Error", "Failed to delete backup")
            
            # Connect signals
            backup_list.itemSelectionChanged.connect(show_details)
            refresh_btn.clicked.connect(load_backups)
            restore_btn.clicked.connect(restore_backup)
            delete_btn.clicked.connect(delete_backup)
            close_btn.clicked.connect(dialog.accept)
            
            # Initial load
            load_backups()
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Manager Error", f"Error opening backup manager: {e}")
    
    def show_backup_stats(self):
        """Zeige Backup-Statistiken"""
        try:
            if not self.backup_system:
                QMessageBox.information(self, "Backup System", "Backup System is not available")
                return
            
            stats = self.backup_system.get_backup_statistics()
            
            stats_text = f"""Backup System Statistics:

Total Backups: {stats.get('total_backups', 0)}
Total Size: {stats.get('total_size_mb', 0):.2f} MB

Backup Settings:
- Auto Backup: {'Enabled' if stats.get('settings', {}).get('auto_backup_enabled', False) else 'Disabled'}
- Max Backups: {stats.get('settings', {}).get('max_backups', 50)}
- Compression: {'Enabled' if stats.get('settings', {}).get('compress_backups', False) else 'Disabled'}
- Auto Cleanup: {'Enabled' if stats.get('settings', {}).get('cleanup_old_backups', False) else 'Disabled'}
- Cleanup Days: {stats.get('settings', {}).get('cleanup_days', 30)}

Operations:"""
            
            operations = stats.get('operations', {})
            for operation, count in operations.items():
                stats_text += f"\n- {operation}: {count}"
            
            if stats.get('newest_backup'):
                stats_text += f"\n\nNewest Backup: {stats['newest_backup'].strftime('%Y-%m-%d %H:%M:%S')}"
            if stats.get('oldest_backup'):
                stats_text += f"\nOldest Backup: {stats['oldest_backup'].strftime('%Y-%m-%d %H:%M:%S')}"
            
            QMessageBox.information(self, "Backup Statistics", stats_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Statistics Error", f"Error getting backup statistics: {e}")
    
    # === VCI Detection Signal Handlers ===
    
    def on_vci_detected(self, vci):
        """VCI Interface erkannt"""
        try:
            print(f"[VCI] Detected: {vci.name} on {vci.port}")
            
            # Show notification
            from PySide6.QtWidgets import QSystemTrayIcon
            if QSystemTrayIcon.isSystemTrayAvailable():
                QSystemTrayIcon.showMessage(
                    "VCI Detected",
                    f"Found {vci.name} on {vci.port}",
                    QSystemTrayIcon.Information,
                    3000
                )
            
            # Try auto-connect for known good interfaces
            if vci.name in ["ELM327", "OpenPort 2.0"]:
                self.vci_detection.connect_vci(vci.name.lower().replace(" ", "").replace(".", ""))
                
        except Exception as e:
            print(f"[ERROR] VCI detection handler failed: {e}")
    
    def on_vci_connected(self, vci):
        """VCI Interface verbunden"""
        try:
            print(f"[VCI] Connected: {vci.name} on {vci.port}")
            
            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"VCI Connected: {vci.name}", 5000)
            
            # Show info dialog
            QMessageBox.information(
                self, "VCI Connected",
                f"Successfully connected to {vci.name} on {vci.port}\n\n"
                f"Supported protocols: {', '.join(vci.protocols)}"
            )
            
        except Exception as e:
            print(f"[ERROR] VCI connection handler failed: {e}")
    
    def on_vci_disconnected(self, vci):
        """VCI Interface getrennt"""
        try:
            print(f"[VCI] Disconnected: {vci.name}")
            
            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"VCI Disconnected: {vci.name}", 3000)
            
            # Show warning
            QMessageBox.warning(
                self, "VCI Disconnected",
                f"Lost connection to {vci.name}\n\n"
                f"Please check cable and reconnect if needed."
            )
            
        except Exception as e:
            print(f"[ERROR] VCI disconnection handler failed: {e}")
    
    def on_vci_status_changed(self, status):
        """VCI Status Update"""
        try:
            print(f"[VCI] Status: {status}")
            
            # Update status bar if available
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"VCI: {status}", 2000)
                
        except Exception as e:
            print(f"[ERROR] VCI status handler failed: {e}")
    
    # === VIN Decoder Tab ===
    
    def create_vin_decoder_tab(self):
        """VIN Decoder Tab mit ECU/VIN Database"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("VIN Decoder & ECU Database")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #0066cc;")
        layout.addWidget(header)
        
        # VIN Input Group
        vin_group = QGroupBox("VIN Decoder")
        vin_layout = QVBoxLayout(vin_group)
        
        # VIN Input
        vin_input_layout = QHBoxLayout()
        vin_input_layout.addWidget(QLabel("VIN (17 characters):"))
        
        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText("Enter VIN (e.g., VF3ABCDEF12345678)")
        self.vin_input.setMaxLength(17)
        self.vin_input.textChanged.connect(self.on_vin_input_changed)
        vin_input_layout.addWidget(self.vin_input)
        
        decode_btn = QPushButton("Decode VIN")
        decode_btn.clicked.connect(self.decode_vin)
        vin_input_layout.addWidget(decode_btn)
        
        vin_layout.addLayout(vin_input_layout)
        
        # VIN Results
        self.vin_results = QTextEdit()
        self.vin_results.setReadOnly(True)
        self.vin_results.setMaximumHeight(200)
        vin_layout.addWidget(self.vin_results)
        
        layout.addWidget(vin_group)
        
        # ECU Database Group
        ecu_group = QGroupBox("ECU Database")
        ecu_layout = QVBoxLayout(ecu_group)
        
        # ECU Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search ECUs:"))
        
        self.ecu_search_input = QLineEdit()
        self.ecu_search_input.setPlaceholderText("Search by name, function, or supplier")
        self.ecu_search_input.textChanged.connect(self.search_ecus)
        search_layout.addWidget(self.ecu_search_input)
        
        ecu_layout.addLayout(search_layout)
        
        # ECU List
        self.ecu_list = QListWidget()
        self.ecu_list.itemSelectionChanged.connect(self.on_ecu_selected)
        ecu_layout.addWidget(self.ecu_list)
        
        # ECU Details
        self.ecu_details = QTextEdit()
        self.ecu_details.setReadOnly(True)
        self.ecu_details.setMaximumHeight(300)
        ecu_layout.addWidget(self.ecu_details)
        
        layout.addWidget(ecu_group)
        
        # Database Statistics
        stats_group = QGroupBox("Database Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.db_stats_label = QLabel()
        stats_layout.addWidget(self.db_stats_label)
        
        # Update stats button
        update_stats_btn = QPushButton("Update Statistics")
        update_stats_btn.clicked.connect(self.update_database_stats)
        stats_layout.addWidget(update_stats_btn)
        
        layout.addWidget(stats_group)
        
        # Initialize
        self.load_ecu_list()
        self.update_database_stats()
        
        layout.addStretch()
        return widget
    
    def on_vin_input_changed(self, text):
        """VIN Input Validation"""
        try:
            # Real-time validation
            if len(text) == 17:
                self.vin_input.setStyleSheet("border: 2px solid green;")
            elif len(text) > 0:
                self.vin_input.setStyleSheet("border: 2px solid orange;")
            else:
                self.vin_input.setStyleSheet("")
                
        except Exception as e:
            print(f"[ERROR] VIN input validation failed: {e}")
    
    def decode_vin(self):
        """Decode VIN using database"""
        try:
            if not self.ecu_vin_database:
                QMessageBox.information(self, "VIN Decoder", "ECU/VIN Database not available")
                return
            
            vin = self.vin_input.text().strip().upper()
            if len(vin) != 17:
                QMessageBox.warning(self, "Invalid VIN", "VIN must be exactly 17 characters")
                return
            
            # Decode VIN
            result = self.ecu_vin_database.identify_vehicle_by_vin(vin)
            
            if result.get('valid'):
                # Format results
                results_text = f"""VIN DECODE RESULTS:

VIN: {result['vin']}
Valid: {result['valid']}

MANUFACTURER INFORMATION:
Brand: {result['manufacturer']['brand']}
Country: {result['manufacturer']['country']}
Manufacturer: {result['manufacturer']['manufacturer']}

VEHICLE INFORMATION:
Model Year: {result['model_year']}
Plant: {result['plant']}
Serial Number: {result['serial_number']}

VEHICLE TYPE:
Type: {result['vehicle_info'].get('type', 'Unknown')}
Engine Code: {result['vehicle_info'].get('engine_code', 'Unknown')}
Body Style: {result['vehicle_info'].get('body_style', 'Unknown')}

POSSIBLE VEHICLES:
"""
                
                possible_vehicles = result.get('possible_vehicles', [])
                if possible_vehicles:
                    for vehicle in possible_vehicles:
                        results_text += f"- {vehicle['info']['model']} {vehicle['info']['generation']} ({vehicle['info']['years']})\n"
                else:
                    results_text += "- No specific vehicle matches found\n"
                
                results_text += f"\nRECOMMENDED ECUs:\n"
                recommended_ecus = result.get('recommended_ecus', [])
                if recommended_ecus:
                    for ecu in recommended_ecus:
                        required = "Required" if ecu['required'] else "Optional"
                        results_text += f"- {ecu['address']}: {ecu['name']} ({required})\n"
                else:
                    results_text += "- No specific ECU recommendations\n"
                
                results_text += f"\nDecoded: {result['decoded_date']}"
                
                self.vin_results.setText(results_text)
                
            else:
                error_msg = result.get('error', 'Unknown error')
                self.vin_results.setText(f"VIN DECODE ERROR:\n\n{error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "VIN Decode Error", f"Error decoding VIN: {e}")
    
    def load_ecu_list(self):
        """Load ECU list"""
        try:
            if not self.ecu_vin_database:
                return
            
            self.ecu_list.clear()
            
            for address, ecu in self.ecu_vin_database.ecu_definitions.items():
                item_text = f"0x{address:X}: {ecu['name']} ({ecu['type']})"
                item = QListWidgetItem(item_text)
                item.setData(1, address)  # Store address
                self.ecu_list.addItem(item)
                
        except Exception as e:
            print(f"[ERROR] Load ECU list failed: {e}")
    
    def search_ecus(self, search_text):
        """Search ECUs in real-time"""
        try:
            if not self.ecu_vin_database or not search_text:
                self.load_ecu_list()
                return
            
            results = self.ecu_vin_database.search_ecus(search_text)
            
            self.ecu_list.clear()
            for address, ecu, match_type in results:
                item_text = f"0x{address:X}: {ecu['name']} ({ecu['type']}) - Match: {match_type}"
                item = QListWidgetItem(item_text)
                item.setData(1, address)
                self.ecu_list.addItem(item)
                
        except Exception as e:
            print(f"[ERROR] ECU search failed: {e}")
    
    def on_ecu_selected(self):
        """ECU selected in list"""
        try:
            current_item = self.ecu_list.currentItem()
            if not current_item or not self.ecu_vin_database:
                return
            
            ecu_address = current_item.data(1)
            ecu = self.ecu_vin_database.get_ecu_by_address(ecu_address)
            
            if ecu:
                # Format ECU details
                details_text = f"""ECU DETAILS:

Name: {ecu['name']}
Short Name: {ecu['short_name']}
Type: {ecu['type']}
Address: 0x{ecu_address:X}

PROTOCOLS:
{', '.join(ecu['protocols'])}

FUNCTIONS:
"""
                for func in ecu['functions']:
                    details_text += f"- {func}\n"
                
                details_text += f"\nDATA IDENTIFIERS ({len(ecu['data_identifiers'])}):\n"
                for data_id, description in ecu['data_identifiers'].items():
                    details_text += f"- 0x{data_id:X}: {description}\n"
                
                details_text += f"\nSUPPLIERS:\n"
                for supplier in ecu['suppliers']:
                    details_text += f"- {supplier}\n"
                
                details_text += f"\nTYPICAL ADDRESSES:\n"
                for addr in ecu['typical_addresses']:
                    details_text += f"- 0x{addr:X}\n"
                
                self.ecu_details.setText(details_text)
            
        except Exception as e:
            print(f"[ERROR] ECU selection failed: {e}")
    
    def update_database_stats(self):
        """Update database statistics"""
        try:
            if not self.ecu_vin_database:
                self.db_stats_label.setText("ECU/VIN Database not available")
                return
            
            stats = self.ecu_vin_database.get_database_statistics()
            
            stats_text = f"""Database Statistics:
            
Total ECUs: {stats['total_ecus']}
Total Vehicles: {stats['total_vehicles']}
WMI Codes: {stats['total_wmi_codes']}
Supported Brands: {len(stats['brands_supported'])}
Suppliers: {len(stats['suppliers'])}

ECU Types:"""
            
            for ecu_type, count in stats['ecu_types'].items():
                stats_text += f"\n- {ecu_type}: {count}"
            
            stats_text += f"\n\nBrands: {', '.join(stats['brands_supported'][:5])}"
            if len(stats['brands_supported']) > 5:
                stats_text += f" and {len(stats['brands_supported']) - 5} more..."
            
            self.db_stats_label.setText(stats_text)
            
        except Exception as e:
            print(f"[ERROR] Database stats update failed: {e}")
    
    # === Hardware Monitor Tab ===
    
    def create_hardware_monitor_tab(self):
        """Hardware Monitor Tab für echte VCI Hardware"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("Hardware VCI Monitor")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #0066cc;")
        layout.addWidget(header)
        
        # Connection Status Group
        connection_group = QGroupBox("VCI Connection Status")
        conn_layout = QVBoxLayout(connection_group)
        
        self.hardware_status_label = QLabel("No hardware VCI connected")
        conn_layout.addWidget(self.hardware_status_label)
        
        # Connection controls
        conn_controls = QHBoxLayout()
        
        self.connect_hardware_btn = QPushButton("Connect Hardware VCI")
        self.connect_hardware_btn.clicked.connect(self.connect_hardware_vci)
        conn_controls.addWidget(self.connect_hardware_btn)
        
        self.disconnect_hardware_btn = QPushButton("Disconnect")
        self.disconnect_hardware_btn.clicked.connect(self.disconnect_hardware_vci)
        self.disconnect_hardware_btn.setEnabled(False)
        conn_controls.addWidget(self.disconnect_hardware_btn)
        
        conn_controls.addStretch()
        conn_layout.addLayout(conn_controls)
        
        layout.addWidget(connection_group)
        
        # CAN Message Monitor Group
        can_group = QGroupBox("CAN Message Monitor")
        can_layout = QVBoxLayout(can_group)
        
        # Message controls
        msg_controls = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Messages")
        clear_btn.clicked.connect(self.clear_can_messages)
        msg_controls.addWidget(clear_btn)
        
        self.auto_scroll_check = QCheckBox("Auto Scroll")
        self.auto_scroll_check.setChecked(True)
        msg_controls.addWidget(self.auto_scroll_check)
        
        msg_controls.addStretch()
        can_layout.addLayout(msg_controls)
        
        # Message list
        self.can_message_list = QTextEdit()
        self.can_message_list.setReadOnly(True)
        self.can_message_list.setMaximumHeight(300)
        self.can_message_list.setFont(QFont("Courier", 9))
        can_layout.addWidget(self.can_message_list)
        
        layout.addWidget(can_group)
        
        # Timing Statistics Group
        timing_group = QGroupBox("CAN-Bus Timing Statistics")
        timing_layout = QVBoxLayout(timing_group)
        
        self.timing_stats_label = QLabel()
        timing_layout.addWidget(self.timing_stats_label)
        
        # Update timing stats button
        update_timing_btn = QPushButton("Update Timing Stats")
        update_timing_btn.clicked.connect(self.update_timing_stats)
        timing_layout.addWidget(update_timing_btn)
        
        layout.addWidget(timing_group)
        
        # Test Controls Group
        test_group = QGroupBox("Hardware Test Controls")
        test_layout = QVBoxLayout(test_group)
        
        # ECU communication test
        ecu_test_layout = QHBoxLayout()
        ecu_test_layout.addWidget(QLabel("ECU Address:"))
        
        self.test_ecu_input = QLineEdit()
        self.test_ecu_input.setPlaceholderText("0x1A0")
        self.test_ecu_input.setMaxLength(6)
        ecu_test_layout.addWidget(self.test_ecu_input)
        
        test_ecu_btn = QPushButton("Test ECU Communication")
        test_ecu_btn.clicked.connect(self.test_ecu_communication)
        ecu_test_layout.addWidget(test_ecu_btn)
        
        test_layout.addLayout(ecu_test_layout)
        
        # VIN read test
        read_vin_btn = QPushButton("Read VIN from ECU")
        read_vin_btn.clicked.connect(self.read_vin_from_hardware)
        test_layout.addWidget(read_vin_btn)
        
        layout.addWidget(test_group)
        
        # Initialize
        self.update_hardware_status()
        self.update_timing_stats()
        
        layout.addStretch()
        return widget
    
    def connect_hardware_vci(self):
        """Connect to hardware VCI"""
        try:
            if not self.hardware_vci:
                QMessageBox.information(self, "Hardware VCI", "Hardware VCI interface not available")
                return
            
            # Check if VCI detection found any interfaces
            if self.vci_detection and self.vci_detection.get_known_vcis():
                known_vcis = self.vci_detection.get_known_vcis()
                
                # Use first available VCI for testing
                vci_id, vci_info = next(iter(known_vcis.items()))
                
                # Attempt connection
                success = self.hardware_vci.connect_hardware_vci(vci_info, vci_info.port)
                
                if success:
                    QMessageBox.information(
                        self, "Hardware Connected",
                        f"Successfully connected to {vci_info.name} on {vci_info.port}"
                    )
                    self.connect_hardware_btn.setEnabled(False)
                    self.disconnect_hardware_btn.setEnabled(True)
                else:
                    QMessageBox.warning(
                        self, "Connection Failed",
                        f"Failed to connect to {vci_info.name}"
                    )
            else:
                QMessageBox.information(
                    self, "No VCI Found",
                    "No VCI interfaces detected. Please connect a VCI and try again."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error connecting to hardware VCI: {e}")
    
    def disconnect_hardware_vci(self):
        """Disconnect from hardware VCI"""
        try:
            if self.hardware_vci:
                success = self.hardware_vci.disconnect_vci()
                if success:
                    self.connect_hardware_btn.setEnabled(True)
                    self.disconnect_hardware_btn.setEnabled(False)
                    self.update_hardware_status()
                    
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Error disconnecting VCI: {e}")
    
    def clear_can_messages(self):
        """Clear CAN message display"""
        if hasattr(self, 'can_message_list'):
            self.can_message_list.clear()
    
    def update_hardware_status(self):
        """Update hardware status display"""
        try:
            if not self.hardware_vci:
                if hasattr(self, 'hardware_status_label'):
                    self.hardware_status_label.setText("Hardware VCI interface not available")
                return
            
            status = self.hardware_vci.get_hardware_status()
            
            status_text = f"""Hardware VCI Status:

Connected: {status['connected']}
VCI Type: {status['vci_type'] or 'None'}
Communication Active: {status['communication_active']}
DLL Available: {status['dll_available']}

Message Queues:
- Pending Messages: {status['pending_messages']}
- Received Messages: {status['received_messages']}"""
            
            if hasattr(self, 'hardware_status_label'):
                self.hardware_status_label.setText(status_text)
                
        except Exception as e:
            print(f"[ERROR] Hardware status update failed: {e}")
    
    def update_timing_stats(self):
        """Update timing statistics display"""
        try:
            if not self.hardware_vci:
                if hasattr(self, 'timing_stats_label'):
                    self.timing_stats_label.setText("Hardware VCI interface not available")
                return
            
            stats = self.hardware_vci.get_timing_statistics()
            
            stats_text = f"""CAN-Bus Timing Statistics:

Total Messages: {stats['total_messages']}
Inter-frame Violations: {stats['inter_frame_violations']}
Timeout Violations: {stats['timeout_violations']}
Success Rate: {stats['success_rate']:.1f}%

Timing Parameters:
- Inter-frame Delay: 2.0ms
- Response Timeout: 100.0ms
- P2 Client: 50.0ms
- P2* Client: 5.0s

Last Activity:
- Time since TX: {stats['time_since_last_tx']:.3f}s
- Time since RX: {stats['time_since_last_rx']:.3f}s"""
            
            if hasattr(self, 'timing_stats_label'):
                self.timing_stats_label.setText(stats_text)
                
        except Exception as e:
            print(f"[ERROR] Timing stats update failed: {e}")
    
    def test_ecu_communication(self):
        """Test ECU communication via hardware VCI"""
        try:
            if not self.hardware_vci or not self.hardware_vci.connected:
                QMessageBox.warning(self, "Not Connected", "Hardware VCI not connected")
                return
            
            ecu_address_str = self.test_ecu_input.text().strip()
            if not ecu_address_str:
                ecu_address_str = "0x1A0"  # Default engine ECU
            
            try:
                ecu_address = int(ecu_address_str, 16)
            except ValueError:
                QMessageBox.warning(self, "Invalid Address", "Invalid ECU address format")
                return
            
            # Send diagnostic session control (Service 0x10)
            can_msg = self.hardware_vci.send_can_message(ecu_address, 0x10, [0x01])
            
            if can_msg:
                self.add_can_message_to_display(can_msg)
                QMessageBox.information(
                    self, "Test Sent",
                    f"Test message sent to ECU 0x{ecu_address:X}\nCheck message monitor for response"
                )
            else:
                QMessageBox.warning(self, "Send Failed", "Failed to send test message")
                
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"ECU communication test failed: {e}")
    
    def read_vin_from_hardware(self):
        """Read VIN from hardware ECU"""
        try:
            if not self.hardware_vci or not self.hardware_vci.connected:
                QMessageBox.warning(self, "Not Connected", "Hardware VCI not connected")
                return
            
            # Send read VIN request (Service 0x22, Data ID 0xF190)
            can_msg = self.hardware_vci.send_can_message(0x1A0, 0x22, [0xF1, 0x90])
            
            if can_msg:
                self.add_can_message_to_display(can_msg)
                QMessageBox.information(
                    self, "VIN Request Sent",
                    "VIN read request sent to Engine ECU (0x1A0)\nCheck message monitor for response"
                )
            else:
                QMessageBox.warning(self, "Send Failed", "Failed to send VIN request")
                
        except Exception as e:
            QMessageBox.critical(self, "VIN Read Error", f"VIN read failed: {e}")
    
    def add_can_message_to_display(self, can_msg):
        """Add CAN message to display"""
        try:
            if not hasattr(self, 'can_message_list'):
                return
            
            timestamp = datetime.fromtimestamp(can_msg.timestamp).strftime("%H:%M:%S.%f")[:-3]
            direction = "TX" if can_msg.direction == 'TX' else "RX"
            
            msg_line = f"{timestamp} {direction} ID:0x{can_msg.msg_id:03X} DLC:{can_msg.dlc} Data:{can_msg.data.hex().upper()}"
            
            self.can_message_list.append(msg_line)
            
            # Auto scroll if enabled
            if hasattr(self, 'auto_scroll_check') and self.auto_scroll_check.isChecked():
                scrollbar = self.can_message_list.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
        except Exception as e:
            print(f"[ERROR] Add CAN message failed: {e}")
    
    # === Hardware VCI Signal Handlers ===
    
    def on_can_message_received(self, can_msg):
        """Handle received CAN message"""
        try:
            print(f"[CAN RX] ID:0x{can_msg.msg_id:X} Data:{can_msg.data.hex().upper()}")
            self.add_can_message_to_display(can_msg)
            self.update_timing_stats()
            
        except Exception as e:
            print(f"[ERROR] CAN message received handler failed: {e}")
    
    def on_can_message_sent(self, can_msg):
        """Handle sent CAN message"""
        try:
            print(f"[CAN TX] ID:0x{can_msg.msg_id:X} Data:{can_msg.data.hex().upper()}")
            # Message already added to display by send function
            
        except Exception as e:
            print(f"[ERROR] CAN message sent handler failed: {e}")
    
    def on_hardware_connection_changed(self, vci_type, connected):
        """Handle hardware connection status change"""
        try:
            status = "connected" if connected else "disconnected"
            print(f"[HARDWARE] {vci_type} {status}")
            
            self.update_hardware_status()
            
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Hardware VCI {vci_type} {status}", 5000)
                
        except Exception as e:
            print(f"[ERROR] Hardware connection handler failed: {e}")
    
    def on_hardware_error(self, error):
        """Handle hardware error"""
        try:
            print(f"[HARDWARE ERROR] {error.vci_type}: {error} (Code: {error.error_code})")
            
            QMessageBox.critical(
                self, "Hardware Error",
                f"Hardware VCI Error: {error}\n\n"
                f"VCI Type: {error.vci_type}\n"
                f"Error Code: {error.error_code}\n"
                f"Time: {error.timestamp.strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            print(f"[ERROR] Hardware error handler failed: {e}")
    
    def on_timing_violation(self, message, actual_time):
        """Handle timing violation"""
        try:
            print(f"[TIMING] Violation: {message} ({actual_time:.3f}s)")
            
            # Update timing stats
            self.update_timing_stats()
            
            # Show warning for critical violations
            if "timeout" in message.lower():
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Timing violation: {message}", 3000)
                    
        except Exception as e:
            print(f"[ERROR] Timing violation handler failed: {e}")

    # Professional Features Tab Methods
    def create_live_graphs_tab(self):
        """Live-Graphen Tab erstellen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📊 Live ECU Parameter Monitoring")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(header)
        
        if REALTIME_GRAPHS_AVAILABLE:
            try:
                # Live-Graph Widget einbetten
                self.live_graph_widget = RealTimeGraphWidget()
                layout.addWidget(self.live_graph_widget)
                
                # Quick-Start Button
                start_btn = QPushButton("🚀 Live-Monitoring starten")
                start_btn.clicked.connect(self.start_live_monitoring)
                start_btn.setStyleSheet("QPushButton { background-color: #0066cc; color: white; font-weight: bold; padding: 8px; }")
                layout.addWidget(start_btn)
                
            except Exception as e:
                error_label = QLabel(f"❌ Live-Graphen Fehler: {str(e)}")
                error_label.setStyleSheet("color: #d13438; padding: 10px;")
                layout.addWidget(error_label)
        else:
            info_label = QLabel("⚠️ Live-Graphen nicht verfügbar\n\nBenötigt: pyqtgraph, numpy")
            info_label.setStyleSheet("color: #ff8c00; padding: 20px; font-size: 12px;")
            layout.addWidget(info_label)
            
        return widget
    
    def create_pdf_reports_tab(self):
        """PDF-Reports Tab erstellen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("📄 Professional PDF Reports")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(header)
        
        if PDF_REPORTS_AVAILABLE:
            # Report-Typ Auswahl
            type_group = QGroupBox("Report-Typ")
            type_layout = QVBoxLayout(type_group)
            
            self.report_type_combo = QComboBox()
            self.report_type_combo.addItems([
                "Vollständiger Diagnose-Report",
                "Fehlercode-Report", 
                "Live-Daten Report",
                "ECU-Informationen Report"
            ])
            type_layout.addWidget(self.report_type_combo)
            layout.addWidget(type_group)
            
            # Report-Optionen
            options_group = QGroupBox("Optionen")
            options_layout = QVBoxLayout(options_group)
            
            self.include_charts_cb = QCheckBox("Diagramme einschließen")
            self.include_charts_cb.setChecked(True)
            options_layout.addWidget(self.include_charts_cb)
            
            self.include_images_cb = QCheckBox("Bilder einschließen")
            self.include_images_cb.setChecked(True)
            options_layout.addWidget(self.include_images_cb)
            
            layout.addWidget(options_group)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            preview_btn = QPushButton("👁 Vorschau")
            preview_btn.clicked.connect(self.preview_pdf_report)
            button_layout.addWidget(preview_btn)
            
            generate_btn = QPushButton("📄 Report erstellen")
            generate_btn.clicked.connect(self.generate_pdf_report)
            generate_btn.setStyleSheet("QPushButton { background-color: #00d084; color: white; font-weight: bold; padding: 8px; }")
            button_layout.addWidget(generate_btn)
            
            layout.addLayout(button_layout)
            
        else:
            info_label = QLabel("⚠️ PDF-Reports nicht verfügbar\n\nBenötigt: reportlab, matplotlib")
            info_label.setStyleSheet("color: #ff8c00; padding: 20px; font-size: 12px;")
            layout.addWidget(info_label)
            
        layout.addStretch()
        return widget
    
    def create_coding_assistant_tab(self):
        """ECU Coding Assistant Tab erstellen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("🛠️ ECU Coding Assistant")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(header)
        
        if CODING_ASSISTANT_AVAILABLE:
            try:
                # Coding Assistant Widget einbetten
                self.coding_assistant_widget = CodingAssistantWidget()
                layout.addWidget(self.coding_assistant_widget)
                
            except Exception as e:
                error_label = QLabel(f"❌ Coding Assistant Fehler: {str(e)}")
                error_label.setStyleSheet("color: #d13438; padding: 10px;")
                layout.addWidget(error_label)
        else:
            info_label = QLabel("⚠️ ECU Coding Assistant nicht verfügbar\n\nBenötigt: CodingAssistant Modul")
            info_label.setStyleSheet("color: #ff8c00; padding: 20px; font-size: 12px;")
            layout.addWidget(info_label)
            
        return widget
    
    def create_flash_manager_tab(self):
        """Flash Manager Tab erstellen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("💾 ECU Flash/Update Manager")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(header)
        
        # Warnung
        warning = QLabel("⚠️ WARNUNG: ECU-Flash kann bei Fehlern zu irreparablen Schäden führen!")
        warning.setStyleSheet("background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px;")
        layout.addWidget(warning)
        
        if FLASH_MANAGER_AVAILABLE:
            try:
                # Flash Manager Widget einbetten
                self.flash_manager_widget = FlashManagerWidget()
                layout.addWidget(self.flash_manager_widget)
                
            except Exception as e:
                error_label = QLabel(f"❌ Flash Manager Fehler: {str(e)}")
                error_label.setStyleSheet("color: #d13438; padding: 10px;")
                layout.addWidget(error_label)
        else:
            info_label = QLabel("⚠️ Flash Manager nicht verfügbar\n\nBenötigt: FlashUpdateManager Modul")
            info_label.setStyleSheet("color: #ff8c00; padding: 20px; font-size: 12px;")
            layout.addWidget(info_label)
            
        return widget
    
    def create_config_manager_tab(self):
        """PSA Config Manager Tab erstellen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("PSA Config Manager - ECHTE .nac/.cmb Dateien")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(header)
        
        # Info
        info = QLabel("Arbeitet mit echten PSA/Stellantis Konfigurationsdateien aus dem Configs-Verzeichnis")
        info.setStyleSheet("background-color: #e8f4fd; color: #0c5460; border: 1px solid #bee5eb; padding: 10px; border-radius: 4px;")
        layout.addWidget(info)
        
        if CONFIG_MANAGER_AVAILABLE:
            try:
                # Config Manager Widget einbetten
                self.config_manager_widget = RealConfigManagerWidget()
                layout.addWidget(self.config_manager_widget)
                
            except Exception as e:
                error_label = QLabel(f"❌ Config Manager Fehler: {str(e)}")
                error_label.setStyleSheet("color: #d13438; padding: 10px;")
                layout.addWidget(error_label)
        else:
            info_label = QLabel("⚠️ Config Manager nicht verfügbar\n\nBenötigt: RealConfigManager Modul")
            info_label.setStyleSheet("color: #ff8c00; padding: 20px; font-size: 12px;")
            layout.addWidget(info_label)
            
        return widget
    
    # Professional Features Event Handlers
    def start_live_monitoring(self):
        """Live-Monitoring starten"""
        if hasattr(self, 'live_graph_widget') and self.live_graph_widget:
            self.live_graph_widget.start_monitoring()
            QMessageBox.information(self, "Live-Monitoring", "Live-Parameter Monitoring gestartet!")
    
    def preview_pdf_report(self):
        """PDF-Report Vorschau"""
        QMessageBox.information(self, "Report Vorschau", "PDF-Report Vorschau würde hier angezeigt werden")
    
    def generate_pdf_report(self):
        """PDF-Report generieren"""
        if PDF_REPORTS_AVAILABLE:
            try:
                from PDFReportGenerator import create_sample_report
                success, message, filename = create_sample_report()
                
                if success:
                    QMessageBox.information(
                        self, "Report erstellt",
                        f"PDF-Report erfolgreich erstellt!\n\nDatei: {filename}"
                    )
                else:
                    QMessageBox.warning(self, "Fehler", f"Report-Erstellung fehlgeschlagen:\n{message}")
                    
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"PDF-Report Fehler: {str(e)}")


def main():
    """Hauptfunktion für direkten Start"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimpleEnhancedMainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())