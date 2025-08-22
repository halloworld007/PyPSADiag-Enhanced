#!/usr/bin/env python3
"""
Professional Logging System für PyPSADiag
Strukturiertes Logging mit verschiedenen Levels und Export-Funktionen
"""

import os
import logging
import json
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback

try:
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QTextEdit, QComboBox, QCheckBox,
                                 QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
                                 QFileDialog, QMessageBox, QSpinBox)
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, QTimer, Qt
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QTextEdit, QComboBox, QCheckBox,
                                   QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
                                   QFileDialog, QMessageBox, QSpinBox)
        QT_FRAMEWORK = "PyQt5"

@dataclass
class LogEvent:
    """Strukturiertes Log-Event"""
    timestamp: datetime
    level: str
    category: str
    message: str
    module: str
    function: str = ""
    line_number: int = 0
    thread_id: str = ""
    ecu_context: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Dict = None
    
    def to_dict(self):
        """Konvertiert zu Dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class PyPSALogger:
    """Hauptklasse für professionelles Logging"""
    
    def __init__(self, log_directory: str = "logs", max_file_size: int = 10*1024*1024):
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(exist_ok=True)
        
        self.max_file_size = max_file_size
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_events = []
        self.max_memory_events = 1000
        
        # Kategorien für strukturiertes Logging (vor setup_loggers!)
        self.categories = {
            "SYSTEM": "System Events",
            "COMMUNICATION": "Hardware Communication", 
            "ECU": "ECU Operations",
            "GUI": "User Interface",
            "BACKUP": "Backup Operations",
            "ERROR": "Error Events",
            "PERFORMANCE": "Performance Metrics",
            "SECURITY": "Security Events",
            "ENHANCED": "Enhanced Features"
        }
        
        # Logging-Konfiguration (nach Kategorien!)
        self.setup_loggers()
        
        print(f"[LOGGER] Professional Logging System initialisiert - Session: {self.session_id}")
    
    def setup_loggers(self):
        """Konfiguriert verschiedene Logger"""
        
        # Hauptlogger
        self.main_logger = logging.getLogger("PyPSADiag")
        self.main_logger.setLevel(logging.DEBUG)
        
        # File Handler mit Rotation
        main_log_file = self.log_dir / f"pypsa_{self.session_id}.log"
        file_handler = RotatingFileHandler(
            main_log_file, 
            maxBytes=self.max_file_size, 
            backupCount=5
        )
        
        # Detailliertes Format
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-12s | %(funcName)-15s:%(lineno)-4d | %(message)s'
        )
        file_handler.setFormatter(detailed_formatter)
        self.main_logger.addHandler(file_handler)
        
        # Separate Logger für verschiedene Kategorien
        self.category_loggers = {}
        
        for category_id, category_name in self.categories.items():
            logger = logging.getLogger(f"PyPSADiag.{category_id}")
            logger.setLevel(logging.DEBUG)
            
            # Separater File Handler für Kategorie
            cat_log_file = self.log_dir / f"pypsa_{category_id.lower()}_{self.session_id}.log"
            cat_handler = RotatingFileHandler(cat_log_file, maxBytes=self.max_file_size, backupCount=3)
            cat_handler.setFormatter(detailed_formatter)
            logger.addHandler(cat_handler)
            
            self.category_loggers[category_id] = logger
        
        # Performance Logger (separates Format)
        perf_logger = logging.getLogger("PyPSADiag.PERFORMANCE")
        perf_file = self.log_dir / f"pypsa_performance_{self.session_id}.log"
        perf_handler = RotatingFileHandler(perf_file, maxBytes=self.max_file_size, backupCount=2)
        
        perf_formatter = logging.Formatter('%(asctime)s | %(message)s')
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
    
    def log(self, level: str, category: str, message: str, **kwargs):
        """Hauptmethode für strukturiertes Logging"""
        
        # Rekursions-Schutz - verhindert endlose Logging-Schleifen
        if hasattr(self, '_logging_in_progress') and self._logging_in_progress:
            return
        
        self._logging_in_progress = True
        
        try:
            # Frame-Informationen für Kontext
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_frame = frame.f_back
                module = caller_frame.f_globals.get('__name__', 'unknown')
                function = caller_frame.f_code.co_name
                line_number = caller_frame.f_lineno
            else:
                module = function = 'unknown'
                line_number = 0
            
            # Log-Event erstellen
            log_event = LogEvent(
                timestamp=datetime.now(),
                level=level.upper(),
                category=category.upper(),
                message=message,
                module=module,
                function=function,
                line_number=line_number,
                session_id=self.session_id,
                additional_data=kwargs
            )
            
            # In Memory-Liste hinzufügen (für GUI)
            self.log_events.append(log_event)
            if len(self.log_events) > self.max_memory_events:
                self.log_events.pop(0)
            
            # An entsprechende Logger weiterleiten
            logger_level = getattr(logging, level.upper(), logging.INFO)
            
            # Hauptlogger
            self.main_logger.log(logger_level, f"[{category}] {message}")
            
            # Kategorie-Logger
            if category.upper() in self.category_loggers:
                cat_logger = self.category_loggers[category.upper()]
                
                # Erweiterte Informationen für Kategorie-Logger
                extended_message = f"{message}"
                if kwargs:
                    extended_message += f" | Data: {json.dumps(kwargs, default=str)}"
                
                cat_logger.log(logger_level, extended_message)
            
        except Exception as e:
            # Fehler beim Logging nicht weiter propagieren
            print(f"[LOGGING ERROR] {e}")
        finally:
            # Rekursions-Schutz aufheben
            self._logging_in_progress = False
    
    # Convenience-Methoden für verschiedene Log-Levels
    def debug(self, category: str, message: str, **kwargs):
        """Debug-Level Logging"""
        self.log("DEBUG", category, message, **kwargs)
    
    def info(self, category: str, message: str, **kwargs):
        """Info-Level Logging"""
        self.log("INFO", category, message, **kwargs)
    
    def warning(self, category: str, message: str, **kwargs):
        """Warning-Level Logging"""
        self.log("WARNING", category, message, **kwargs)
    
    def error(self, category: str, message: str, **kwargs):
        """Error-Level Logging"""
        self.log("ERROR", category, message, **kwargs)
    
    def critical(self, category: str, message: str, **kwargs):
        """Critical-Level Logging"""
        self.log("CRITICAL", category, message, **kwargs)
    
    # Spezielle Logging-Methoden
    def log_performance(self, operation: str, duration: float, **metrics):
        """Performance-Metriken loggen"""
        perf_data = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "timestamp": datetime.now().isoformat(),
            **metrics
        }
        
        self.category_loggers["PERFORMANCE"].info(
            f"PERF | {operation} | {duration*1000:.2f}ms | {json.dumps(metrics, default=str)}"
        )
    
    def log_communication(self, direction: str, ecu_id: str, command: str, response: str = None, **kwargs):
        """Hardware-Kommunikation loggen"""
        comm_data = {
            "direction": direction,  # "TX" oder "RX"
            "ecu_id": ecu_id,
            "command": command,
            "response": response,
            **kwargs
        }
        
        message = f"{direction} | ECU:{ecu_id} | CMD:{command}"
        if response:
            message += f" | RESP:{response[:50]}..."
        
        self.log("INFO", "COMMUNICATION", message, **comm_data)
    
    def log_exception(self, category: str, exception: Exception, context: str = ""):
        """Exception mit vollem Stack-Trace loggen"""
        exc_info = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context,
            "stack_trace": traceback.format_exc()
        }
        
        self.log("ERROR", category, f"Exception in {context}: {exception}", **exc_info)
    
    def log_security_event(self, event_type: str, details: str, severity: str = "INFO"):
        """Sicherheitsereignisse loggen"""
        security_data = {
            "event_type": event_type,
            "severity": severity,
            "user_session": self.session_id
        }
        
        self.log(severity, "SECURITY", f"Security Event: {event_type} - {details}", **security_data)
    
    def get_log_events(self, level: str = None, category: str = None, 
                      since: datetime = None, limit: int = 100) -> List[LogEvent]:
        """Filtert und gibt Log-Events zurück"""
        
        filtered_events = self.log_events
        
        # Filter anwenden
        if level:
            filtered_events = [e for e in filtered_events if e.level == level.upper()]
        
        if category:
            filtered_events = [e for e in filtered_events if e.category == category.upper()]
        
        if since:
            filtered_events = [e for e in filtered_events if e.timestamp >= since]
        
        # Limit anwenden
        return filtered_events[-limit:]
    
    def export_logs(self, format: str = "json", output_file: str = None, 
                   filters: Dict = None) -> str:
        """Exportiert Logs in verschiedenen Formaten"""
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"pypsa_export_{timestamp}.{format}"
        
        output_path = self.log_dir / output_file
        
        # Events für Export filtern
        export_events = self.log_events
        if filters:
            if 'level' in filters:
                export_events = [e for e in export_events if e.level == filters['level'].upper()]
            if 'category' in filters:
                export_events = [e for e in export_events if e.category == filters['category'].upper()]
        
        if format.lower() == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                export_data = {
                    "session_id": self.session_id,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_events": len(export_events),
                    "events": [event.to_dict() for event in export_events]
                }
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == "csv":
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if export_events:
                    writer = csv.DictWriter(f, fieldnames=export_events[0].to_dict().keys())
                    writer.writeheader()
                    for event in export_events:
                        writer.writerow(event.to_dict())
        
        print(f"[LOGGER] Logs exportiert nach: {output_path}")
        return str(output_path)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Löscht alte Log-Dateien"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for log_file in self.log_dir.glob("pypsa_*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                print(f"[LOGGER] Fehler beim Löschen von {log_file}: {e}")
        
        print(f"[LOGGER] {cleaned_count} alte Log-Dateien gelöscht")
        return cleaned_count


class LoggingSystemWidget(QWidget):
    """GUI Widget für Professional Logging System"""
    
    def __init__(self, logger: PyPSALogger, parent=None):
        super().__init__(parent)
        
        self.logger = logger
        self.auto_refresh = True
        
        self.setup_ui()
        
        # Auto-Refresh Timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_log_view)
        self.refresh_timer.start(2000)  # 2 Sekunden
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Professional Logging System")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Controls
        controls_group = QGroupBox("Log Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        # Level Filter
        controls_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.refresh_log_view)
        controls_layout.addWidget(self.level_combo)
        
        # Category Filter
        controls_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["ALL"] + list(self.logger.categories.keys()))
        self.category_combo.currentTextChanged.connect(self.refresh_log_view)
        controls_layout.addWidget(self.category_combo)
        
        # Auto-Refresh
        self.auto_refresh_checkbox = QCheckBox("Auto-Refresh")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_checkbox)
        
        # Max Events
        controls_layout.addWidget(QLabel("Max Events:"))
        self.max_events_spin = QSpinBox()
        self.max_events_spin.setRange(50, 2000)
        self.max_events_spin.setValue(200)
        self.max_events_spin.valueChanged.connect(self.refresh_log_view)
        controls_layout.addWidget(self.max_events_spin)
        
        layout.addWidget(controls_group)
        
        # Tabs für verschiedene Ansichten
        self.tabs = QTabWidget()
        
        # Live Log Tab
        live_tab = QWidget()
        live_layout = QVBoxLayout(live_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.get_monospace_font())
        live_layout.addWidget(self.log_text)
        
        self.tabs.addTab(live_tab, "Live Logs")
        
        # Structured View Tab
        structured_tab = QWidget()
        structured_layout = QVBoxLayout(structured_tab)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Category", "Module", "Function", "Message"])
        structured_layout.addWidget(self.log_table)
        
        self.tabs.addTab(structured_tab, "Structured View")
        
        layout.addWidget(self.tabs)
        
        # Export Controls
        export_group = QGroupBox("Export & Maintenance")
        export_layout = QHBoxLayout(export_group)
        
        export_json_btn = QPushButton("📄 Export JSON")
        export_json_btn.clicked.connect(lambda: self.export_logs("json"))
        export_layout.addWidget(export_json_btn)
        
        export_csv_btn = QPushButton("📊 Export CSV")
        export_csv_btn.clicked.connect(lambda: self.export_logs("csv"))
        export_layout.addWidget(export_csv_btn)
        
        clear_btn = QPushButton("🗑️ Clear View")
        clear_btn.clicked.connect(self.clear_view)
        export_layout.addWidget(clear_btn)
        
        cleanup_btn = QPushButton("🧹 Cleanup Old Logs")
        cleanup_btn.clicked.connect(self.cleanup_old_logs)
        export_layout.addWidget(cleanup_btn)
        
        layout.addWidget(export_group)
        
        # Initial Load
        self.refresh_log_view()
    
    def get_monospace_font(self):
        """Gibt Monospace-Font zurück"""
        from PySide6.QtGui import QFont
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setPointSize(9)
        return font
    
    def toggle_auto_refresh(self, enabled: bool):
        """Aktiviert/Deaktiviert Auto-Refresh"""
        self.auto_refresh = enabled
        if enabled:
            self.refresh_timer.start(2000)
        else:
            self.refresh_timer.stop()
    
    def refresh_log_view(self):
        """Aktualisiert Log-Ansicht"""
        if not self.auto_refresh and not self.sender():
            return
        
        # Filter-Parameter
        level = self.level_combo.currentText() if self.level_combo.currentText() != "ALL" else None
        category = self.category_combo.currentText() if self.category_combo.currentText() != "ALL" else None
        limit = self.max_events_spin.value()
        
        # Events abrufen
        events = self.logger.get_log_events(level=level, category=category, limit=limit)
        
        # Live-Text Update
        if self.tabs.currentIndex() == 0:  # Live Tab
            self.log_text.clear()
            for event in events:
                timestamp = event.timestamp.strftime("%H:%M:%S")
                line = f"[{timestamp}] {event.level:8} | {event.category:12} | {event.module:15} | {event.message}"
                
                # Farbcodierung basierend auf Level
                if event.level == "ERROR":
                    line = f'<span style="color: red;">{line}</span>'
                elif event.level == "WARNING":
                    line = f'<span style="color: orange;">{line}</span>'
                elif event.level == "DEBUG":
                    line = f'<span style="color: gray;">{line}</span>'
                
                self.log_text.append(line)
            
            # Scroll to bottom
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
        
        # Strukturierte Tabelle Update
        elif self.tabs.currentIndex() == 1:  # Structured Tab
            self.log_table.setRowCount(len(events))
            
            for row, event in enumerate(events):
                self.log_table.setItem(row, 0, QTableWidgetItem(event.timestamp.strftime("%H:%M:%S")))
                self.log_table.setItem(row, 1, QTableWidgetItem(event.level))
                self.log_table.setItem(row, 2, QTableWidgetItem(event.category))
                self.log_table.setItem(row, 3, QTableWidgetItem(event.module.split('.')[-1]))
                self.log_table.setItem(row, 4, QTableWidgetItem(event.function))
                self.log_table.setItem(row, 5, QTableWidgetItem(event.message))
            
            # Auto-resize columns
            self.log_table.resizeColumnsToContents()
    
    def export_logs(self, format: str):
        """Exportiert Logs mit GUI"""
        filters = {}
        
        if self.level_combo.currentText() != "ALL":
            filters['level'] = self.level_combo.currentText()
        
        if self.category_combo.currentText() != "ALL":
            filters['category'] = self.category_combo.currentText()
        
        try:
            output_file = self.logger.export_logs(format=format, filters=filters)
            QMessageBox.information(self, "Export Successful", f"Logs exported to:\n{output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export logs:\n{str(e)}")
    
    def clear_view(self):
        """Löscht aktuelle Ansicht"""
        if self.tabs.currentIndex() == 0:
            self.log_text.clear()
        else:
            self.log_table.setRowCount(0)
    
    def cleanup_old_logs(self):
        """Führt Log-Cleanup durch"""
        try:
            cleaned_count = self.logger.cleanup_old_logs(days_to_keep=30)
            QMessageBox.information(self, "Cleanup Complete", f"Cleaned up {cleaned_count} old log files")
        except Exception as e:
            QMessageBox.critical(self, "Cleanup Failed", f"Failed to cleanup logs:\n{str(e)}")


# Integration Helper
def integrate_professional_logging(main_window, log_directory: str = "logs"):
    """Integriert Professional Logging System in Hauptanwendung"""
    
    # Logger erstellen
    logger = PyPSALogger(log_directory)
    
    # Widget erstellen
    logging_widget = LoggingSystemWidget(logger)
    
    # In MainWindow integrieren
    main_window.professional_logger = logger
    main_window.logging_widget = logging_widget
    
    # Standard Python logging umleiten
    class PyPSALogHandler(logging.Handler):
        def emit(self, record):
            logger.log(
                record.levelname, 
                "SYSTEM", 
                record.getMessage(),
                module=record.module if hasattr(record, 'module') else record.name
            )
    
    # Root logger erweitern
    pypsa_handler = PyPSALogHandler()
    logging.getLogger().addHandler(pypsa_handler)
    
    print("[LOGGER] Professional Logging System integriert")
    
    return logger, logging_widget