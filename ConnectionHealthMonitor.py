#!/usr/bin/env python3
"""
Connection Health Monitor für VCI-Stabilität
Überwacht Hardware-Verbindungen und verhindert Datenverlust
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from threading import Lock

try:
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, QTimer, Qt
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
        QT_FRAMEWORK = "PyQt5"

@dataclass
class ConnectionStatus:
    """Status einer Hardware-Verbindung"""
    name: str
    is_connected: bool = False
    last_seen: Optional[datetime] = None
    response_time: float = 0.0
    error_count: int = 0
    total_commands: int = 0
    success_rate: float = 100.0
    
    def update_success(self, response_time: float):
        """Aktualisiert Erfolgs-Statistiken"""
        self.is_connected = True
        self.last_seen = datetime.now()
        self.response_time = response_time
        self.total_commands += 1
        self.success_rate = ((self.total_commands - self.error_count) / self.total_commands) * 100
    
    def update_error(self):
        """Aktualisiert Fehler-Statistiken"""
        self.is_connected = False
        self.error_count += 1
        self.total_commands += 1
        if self.total_commands > 0:
            self.success_rate = ((self.total_commands - self.error_count) / self.total_commands) * 100


class ConnectionHealthMonitor(QThread):
    """Überwacht Hardware-Verbindungen kontinuierlich"""
    
    # Signals
    connection_lost = Signal(str)  # connection_name
    connection_restored = Signal(str)  # connection_name
    health_updated = Signal(dict)  # {connection_name: ConnectionStatus}
    critical_failure = Signal(str, str)  # connection_name, error_message
    
    def __init__(self, serial_controller=None, parent=None):
        super().__init__(parent)
        
        self.serial_controller = serial_controller
        self.connections: Dict[str, ConnectionStatus] = {}
        self.monitoring_active = False
        self.check_interval = 2.0  # Sekunden
        self.timeout_threshold = 10.0  # Sekunden
        self.critical_error_threshold = 5  # Aufeinanderfolgende Fehler
        self.lock = Lock()
        
        # Standard-Verbindungen registrieren
        self.register_connection("VCI", "Evolution XS VCI")
        self.register_connection("Serial", "Arduino/Serial Adapter")
        
    def register_connection(self, connection_id: str, display_name: str):
        """Registriert eine neue Verbindung zur Überwachung"""
        with self.lock:
            self.connections[connection_id] = ConnectionStatus(name=display_name)
            print(f"[HEALTH] Verbindung registriert: {display_name}")
    
    def start_monitoring(self):
        """Startet kontinuierliche Überwachung"""
        self.monitoring_active = True
        self.start()
        print("[HEALTH] Connection Health Monitor gestartet")
    
    def stop_monitoring(self):
        """Stoppt Überwachung"""
        self.monitoring_active = False
        if self.isRunning():
            self.quit()
            self.wait()
        print("[HEALTH] Connection Health Monitor gestoppt")
    
    def run(self):
        """Hauptschleife für Verbindungsüberwachung"""
        while self.monitoring_active:
            try:
                self.check_all_connections()
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"[HEALTH] Monitor Fehler: {e}")
                time.sleep(self.check_interval)
    
    def check_all_connections(self):
        """Prüft alle registrierten Verbindungen"""
        with self.lock:
            for conn_id, status in self.connections.items():
                try:
                    self.check_single_connection(conn_id, status)
                except Exception as e:
                    print(f"[HEALTH] Fehler bei {conn_id}: {e}")
                    status.update_error()
                    
            # Emit health update
            self.health_updated.emit(self.connections.copy())
    
    def check_single_connection(self, conn_id: str, status: ConnectionStatus):
        """Prüft eine einzelne Verbindung"""
        start_time = time.time()
        
        if conn_id == "VCI" and self.serial_controller:
            # VCI Health Check
            if hasattr(self.serial_controller, 'use_vci') and self.serial_controller.use_vci:
                if hasattr(self.serial_controller, 'vci_adapter') and self.serial_controller.vci_adapter:
                    # VCI Ping-Test
                    try:
                        # Einfacher Test-Befehl
                        response = self.serial_controller.vci_adapter.test_connection()
                        response_time = time.time() - start_time
                        
                        if response:
                            status.update_success(response_time)
                            if not status.is_connected:
                                self.connection_restored.emit(conn_id)
                        else:
                            status.update_error()
                            if status.is_connected:
                                self.connection_lost.emit(conn_id)
                                
                    except Exception as e:
                        status.update_error()
                        if status.error_count >= self.critical_error_threshold:
                            self.critical_failure.emit(conn_id, str(e))
                            
        elif conn_id == "Serial" and self.serial_controller:
            # Serial Health Check
            try:
                if self.serial_controller.isOpen():
                    # Serial Ping-Test
                    test_response = self.serial_controller.sendReceive("PING", timeout=1.0)
                    response_time = time.time() - start_time
                    
                    if test_response:
                        status.update_success(response_time)
                        if not status.is_connected:
                            self.connection_restored.emit(conn_id)
                    else:
                        status.update_error()
                        if status.is_connected:
                            self.connection_lost.emit(conn_id)
                else:
                    status.update_error()
                    
            except Exception as e:
                status.update_error()
                if status.error_count >= self.critical_error_threshold:
                    self.critical_failure.emit(conn_id, str(e))
    
    def get_connection_health(self) -> Dict[str, ConnectionStatus]:
        """Gibt aktuellen Gesundheitsstatus zurück"""
        with self.lock:
            return self.connections.copy()
    
    def reset_connection_stats(self, connection_id: str):
        """Setzt Statistiken einer Verbindung zurück"""
        with self.lock:
            if connection_id in self.connections:
                status = self.connections[connection_id]
                status.error_count = 0
                status.total_commands = 0
                status.success_rate = 100.0
                print(f"[HEALTH] Statistiken für {connection_id} zurückgesetzt")


class ConnectionHealthWidget(QWidget):
    """GUI Widget für Connection Health Monitoring"""
    
    def __init__(self, health_monitor: ConnectionHealthMonitor, parent=None):
        super().__init__(parent)
        
        self.health_monitor = health_monitor
        self.connection_labels = {}
        self.connection_bars = {}
        
        self.setup_ui()
        self.connect_signals()
        
        # Auto-refresh Timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(1000)  # 1 Sekunde
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Connection Health Monitor")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Connection Status
        for conn_id, status in self.health_monitor.get_connection_health().items():
            conn_layout = QVBoxLayout()
            
            # Name Label
            name_label = QLabel(status.name)
            name_label.setStyleSheet("font-weight: bold;")
            conn_layout.addWidget(name_label)
            
            # Status Label
            status_label = QLabel("Disconnected")
            status_label.setStyleSheet("color: red;")
            self.connection_labels[conn_id] = status_label
            conn_layout.addWidget(status_label)
            
            # Success Rate Bar
            success_bar = QProgressBar()
            success_bar.setRange(0, 100)
            success_bar.setValue(100)
            self.connection_bars[conn_id] = success_bar
            conn_layout.addWidget(success_bar)
            
            layout.addLayout(conn_layout)
        
        # Control Buttons
        button_layout = QVBoxLayout()
        
        start_btn = QPushButton("Start Monitoring")
        start_btn.clicked.connect(self.health_monitor.start_monitoring)
        button_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("Stop Monitoring") 
        stop_btn.clicked.connect(self.health_monitor.stop_monitoring)
        button_layout.addWidget(stop_btn)
        
        # Reset Button für jede Verbindung
        for conn_id in self.health_monitor.get_connection_health().keys():
            reset_btn = QPushButton(f"Reset {conn_id} Stats")
            reset_btn.clicked.connect(lambda checked, cid=conn_id: self.health_monitor.reset_connection_stats(cid))
            button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
    
    def connect_signals(self):
        """Verbindet Health Monitor Signals"""
        self.health_monitor.connection_lost.connect(self.on_connection_lost)
        self.health_monitor.connection_restored.connect(self.on_connection_restored)
        self.health_monitor.health_updated.connect(self.on_health_updated)
        self.health_monitor.critical_failure.connect(self.on_critical_failure)
    
    def on_connection_lost(self, connection_name: str):
        """Behandelt Verbindungsverlust"""
        self.log_message(f"⚠️ Verbindung verloren: {connection_name}")
        
    def on_connection_restored(self, connection_name: str):
        """Behandelt Verbindungswiederherstellung"""
        self.log_message(f"✅ Verbindung wiederhergestellt: {connection_name}")
    
    def on_health_updated(self, health_data: Dict):
        """Aktualisiert Health Display"""
        for conn_id, status in health_data.items():
            if conn_id in self.connection_labels:
                label = self.connection_labels[conn_id]
                bar = self.connection_bars[conn_id]
                
                if status.is_connected:
                    label.setText(f"Connected - {status.response_time:.2f}ms - {status.success_rate:.1f}%")
                    label.setStyleSheet("color: green;")
                else:
                    label.setText(f"Disconnected - Errors: {status.error_count}")
                    label.setStyleSheet("color: red;")
                
                bar.setValue(int(status.success_rate))
    
    def on_critical_failure(self, connection_name: str, error_message: str):
        """Behandelt kritische Ausfälle"""
        self.log_message(f"🔥 KRITISCHER FEHLER bei {connection_name}: {error_message}")
    
    def refresh_display(self):
        """Aktualisiert Display periodisch"""
        health_data = self.health_monitor.get_connection_health()
        self.on_health_updated(health_data)
    
    def log_message(self, message: str):
        """Fügt Log-Nachricht hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")


# Integration Helper
def integrate_connection_health_monitor(main_window, serial_controller):
    """Integriert Connection Health Monitor in Hauptanwendung"""
    
    # Monitor erstellen
    health_monitor = ConnectionHealthMonitor(serial_controller)
    
    # Widget erstellen
    health_widget = ConnectionHealthWidget(health_monitor)
    
    # Auto-Start bei Verbindung
    def on_port_connected():
        health_monitor.start_monitoring()
    
    def on_port_disconnected():
        health_monitor.stop_monitoring()
    
    # An MainWindow anhängen
    main_window.connection_health_monitor = health_monitor
    main_window.connection_health_widget = health_widget
    
    print("[HEALTH] Connection Health Monitor integriert")
    
    return health_monitor, health_widget