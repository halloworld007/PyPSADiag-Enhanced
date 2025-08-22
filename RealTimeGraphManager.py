#!/usr/bin/env python3
"""
RealTimeGraphManager.py

Live-Graphen für ECU-Parameter in Echtzeit
Echtzeitvisualisierung von Fahrzeugdaten mit interaktiven Diagrammen
"""

import sys
import time
import json
from collections import deque
from datetime import datetime, timedelta
# Use Qt compatibility layer
from qt_compat import *

try:
    # Configure PyQtGraph for Qt5/Qt6 compatibility
    import os
    if QT_FRAMEWORK == "PyQt5":
        os.environ.setdefault('PYQTGRAPH_QT_LIB', 'PyQt5')
    elif QT_FRAMEWORK == "PySide6":
        os.environ.setdefault('PYQTGRAPH_QT_LIB', 'PySide6')
        
    import pyqtgraph as pg
    import numpy as np
    PYQTGRAPH_AVAILABLE = True
    print(f"[OK] PyQtGraph configured for {QT_FRAMEWORK}")
except ImportError as e:
    # Quiet fallback - PyQtGraph not available but system will work with basic plots
    PYQTGRAPH_AVAILABLE = False
    print(f"[WARN] PyQtGraph not available: {e}")
    # Fallback-Implementierung
    class MockPyQtGraph:
        class PlotWidget:
            def __init__(self, *args, **kwargs):
                self.legend = None
                
            def setLabel(self, *args, **kwargs):
                pass
                
            def setTitle(self, *args, **kwargs):
                pass
                
            def showGrid(self, *args, **kwargs):
                pass
                
            def setBackground(self, *args, **kwargs):
                pass
                
            def addLegend(self, *args, **kwargs):
                return MockLegend()
                
            def plot(self, *args, **kwargs):
                return MockPyQtGraph.PlotDataItem()
                
            def autoRange(self, *args, **kwargs):
                pass
                
        class PlotDataItem:
            def __init__(self, *args, **kwargs):
                pass
                
            def setData(self, *args, **kwargs):
                pass
                
            def setVisible(self, *args, **kwargs):
                pass
                
        @staticmethod
        def mkPen(*args, **kwargs):
            return MockPen()
            
    class MockLegend:
        def __init__(self):
            pass
            
    class MockPen:
        def __init__(self):
            pass
    pg = MockPyQtGraph()
    
try:
    import numpy as np
except ImportError:
    # Numpy Fallback
    class MockNumpy:
        @staticmethod
        def array(data):
            return list(data)
        @staticmethod
        def sin(x):
            return [0] * len(x) if hasattr(x, '__len__') else 0
        @staticmethod
        def linspace(start, stop, num):
            return list(range(num))
    np = MockNumpy()


class ECUParameter:
    """ECU Parameter Definition"""
    
    def __init__(self, name, unit, min_val=0, max_val=100, color='#0078d4'):
        self.name = name
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.color = color
        self.values = deque(maxlen=1000)  # Letzte 1000 Werte
        self.timestamps = deque(maxlen=1000)
        self.enabled = True
        self.current_value = 0
        
    def add_value(self, value, timestamp=None):
        """Neuen Wert hinzufügen"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.values.append(float(value))
        self.timestamps.append(timestamp)
        self.current_value = value
        
    def get_plot_data(self):
        """Daten für Plot aufbereiten"""
        if not self.values:
            return [], []
        
        # Zeitstempel in Sekunden seit Start konvertieren
        if not self.timestamps:
            return list(self.values), []
            
        start_time = self.timestamps[0]
        times = [(ts - start_time).total_seconds() for ts in self.timestamps]
        
        return times, list(self.values)


class RealTimeGraphWidget(QWidget):
    """Echtzeit-Graph Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameters = {}
        self.update_interval = 100  # ms
        self.pyqtgraph_available = PYQTGRAPH_AVAILABLE
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """UI Setup"""
        layout = QVBoxLayout(self)
        
        # Control Panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        if self.pyqtgraph_available:
            # Graph Widget with PyQtGraph
            self.graph_widget = pg.PlotWidget()
            self.graph_widget.setLabel('left', 'Wert')
            self.graph_widget.setLabel('bottom', 'Zeit (Sekunden)')
            self.graph_widget.setTitle('ECU Parameter - Live-Monitoring')
            self.graph_widget.showGrid(x=True, y=True)
            self.graph_widget.setBackground('w')
            
            # Legend
            self.legend = self.graph_widget.addLegend()
            
            layout.addWidget(self.graph_widget)
        else:
            # Fallback Graph Widget (basic text display)
            self.create_fallback_graph_widget(layout)
        
        # Status Panel
        status_panel = self.create_status_panel()
        layout.addWidget(status_panel)
        
    def create_fallback_graph_widget(self, layout):
        """Fallback Graph Widget für den Fall dass PyQtGraph nicht verfügbar ist"""
        fallback_frame = QFrame()
        fallback_frame.setFrameStyle(QFrame.StyledPanel)
        fallback_frame.setStyleSheet("background-color: #f8f9fa; border: 2px solid #dee2e6;")
        fallback_layout = QVBoxLayout(fallback_frame)
        
        # Info Label
        info_label = QLabel("📊 Live Parameter Monitor (Fallback-Modus)")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0066cc; padding: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        fallback_layout.addWidget(info_label)
        
        # Notice
        notice_label = QLabel("PyQtGraph nicht verfügbar - Textbasierte Parameteranzeige")
        notice_label.setStyleSheet("color: #6c757d; padding: 5px; font-style: italic;")
        notice_label.setAlignment(Qt.AlignCenter)
        fallback_layout.addWidget(notice_label)
        
        # Parameter Display Area
        self.parameter_display = QTextEdit()
        self.parameter_display.setReadOnly(True)
        self.parameter_display.setMaximumHeight(300)
        self.parameter_display.setStyleSheet("background-color: white; font-family: monospace;")
        fallback_layout.addWidget(self.parameter_display)
        
        layout.addWidget(fallback_frame)
        
    def create_control_panel(self):
        """Control Panel erstellen"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Start/Stop
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)
        
        # Update Interval
        layout.addWidget(QLabel("Update:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(50, 5000)
        self.interval_spin.setValue(self.update_interval)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.valueChanged.connect(self.set_update_interval)
        layout.addWidget(self.interval_spin)
        
        # Auto-Scale
        self.autoscale_cb = QCheckBox("Auto-Scale")
        self.autoscale_cb.setChecked(True)
        layout.addWidget(self.autoscale_cb)
        
        # Clear Data
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)
        
        # Export
        export_btn = QPushButton("💾 Export")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)
        
        
        layout.addStretch()
        
        # Parameter Selection
        self.param_list = QListWidget()
        self.param_list.setMaximumHeight(80)
        self.param_list.itemChanged.connect(self.on_parameter_toggled)
        layout.addWidget(self.param_list)
        
        return panel
        
    def create_status_panel(self):
        """Status Panel erstellen"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        
        self.status_label = QLabel("Status: Bereit")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.fps_label = QLabel("FPS: --")
        layout.addWidget(self.fps_label)
        
        self.points_label = QLabel("Punkte: 0")
        layout.addWidget(self.points_label)
        
        return panel
        
    def setup_timer(self):
        """Timer Setup"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_graphs)
        
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)
        
        self.last_update = time.time()
        self.update_count = 0
        self.monitoring = False
        
    def add_parameter(self, name, unit="", min_val=0, max_val=100, color=None):
        """Parameter hinzufügen"""
        if color is None:
            colors = ['#0078d4', '#107c10', '#d13438', '#ff8c00', '#5c2d91', '#0099bc']
            color = colors[len(self.parameters) % len(colors)]
            
        param = ECUParameter(name, unit, min_val, max_val, color)
        self.parameters[name] = param
        
        # Parameter zur Liste hinzufügen
        item = QListWidgetItem(f"{name} ({unit})")
        item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole, name)
        self.param_list.addItem(item)
        
        if self.pyqtgraph_available:
            # Plot-Line erstellen
            pen = pg.mkPen(color=color, width=2)
            param.plot_line = self.graph_widget.plot([], [], pen=pen, name=name)
        else:
            # Fallback - keine Plot-Line
            param.plot_line = None
        
    def update_parameter(self, name, value):
        """Parameter-Wert aktualisieren"""
        if name in self.parameters:
            self.parameters[name].add_value(value)
            
    def toggle_monitoring(self):
        """Monitoring starten/stoppen"""
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
            
    def start_monitoring(self):
        """Monitoring starten"""
        self.monitoring = True
        self.start_btn.setText("⏸ Stop")
        self.update_timer.start(self.update_interval)
        self.status_label.setText("Status: Monitoring aktiv")
        
    def stop_monitoring(self):
        """Monitoring stoppen"""
        self.monitoring = False
        self.start_btn.setText("▶ Start")
        self.update_timer.stop()
        self.status_label.setText("Status: Angehalten")
        
    def set_update_interval(self, interval):
        """Update-Intervall setzen"""
        self.update_interval = interval
        if self.monitoring:
            self.update_timer.setInterval(interval)
            
    def update_graphs(self):
        """Graphen aktualisieren"""
        try:
            total_points = 0
            
            if self.pyqtgraph_available:
                # PyQtGraph Update
                for param in self.parameters.values():
                    if param.enabled and param.values and param.plot_line:
                        times, values = param.get_plot_data()
                        param.plot_line.setData(times, values)
                        total_points += len(values)
                        
                # Auto-Scale
                if self.autoscale_cb.isChecked():
                    self.graph_widget.autoRange()
            else:
                # Fallback Text Update
                self.update_text_display()
                total_points = sum(len(param.values) for param in self.parameters.values())
                
            self.points_label.setText(f"Punkte: {total_points}")
            self.update_count += 1
            
        except Exception as e:
            print(f"Graph update error: {e}")
            
    def update_text_display(self):
        """Text-Display für Fallback-Modus aktualisieren"""
        if not hasattr(self, 'parameter_display'):
            return
            
        display_text = "=== Live ECU Parameter ===\n\n"
        
        for name, param in self.parameters.items():
            if param.enabled and param.values:
                current_value = param.current_value
                display_text += f"{name}: {current_value:.2f} {param.unit}\n"
                
                # Zeige letzte 5 Werte
                recent_values = list(param.values)[-5:]
                display_text += f"  Letzte Werte: {', '.join([f'{v:.1f}' for v in recent_values])}\n"
                display_text += f"  Min/Max: {min(param.values):.1f} / {max(param.values):.1f}\n\n"
        
        self.parameter_display.setPlainText(display_text)
            
    def update_fps(self):
        """FPS aktualisieren"""
        current_time = time.time()
        elapsed = current_time - self.last_update
        if elapsed > 0:
            fps = self.update_count / elapsed
            self.fps_label.setText(f"FPS: {fps:.1f}")
        
        self.last_update = current_time
        self.update_count = 0
        
    def on_parameter_toggled(self, item):
        """Parameter aktivieren/deaktivieren"""
        param_name = item.data(Qt.UserRole)
        if param_name in self.parameters:
            enabled = item.checkState() == Qt.Checked
            self.parameters[param_name].enabled = enabled
            
            if self.pyqtgraph_available and self.parameters[param_name].plot_line:
                self.parameters[param_name].plot_line.setVisible(enabled)
    
    
    def create_status_message(self, message):
        """Status-Nachricht anzeigen"""
        if hasattr(self, 'parameter_display'):
            # Fallback-Modus
            self.parameter_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        else:
            # Normale GUI - könnte in Status-Label angezeigt werden
            pass
            
    def clear_data(self):
        """Alle Daten löschen"""
        for param in self.parameters.values():
            param.values.clear()
            param.timestamps.clear()
            
            if self.pyqtgraph_available and param.plot_line:
                param.plot_line.setData([], [])
            
    def export_data(self):
        """Daten exportieren"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Graph Data", 
                f"ecu_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;JSON Files (*.json)"
            )
            
            if filename:
                if filename.endswith('.json'):
                    self.export_json(filename)
                else:
                    self.export_csv(filename)
                    
                QMessageBox.information(self, "Export", f"Daten exportiert nach:\n{filename}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Export fehlgeschlagen:\n{str(e)}")
            
    def export_csv(self, filename):
        """CSV Export"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            headers = ['Timestamp']
            for param_name in self.parameters.keys():
                headers.append(f"{param_name}")
                
            writer.writerow(headers)
            
            # Finde maximale Anzahl von Datenpunkten
            max_len = max(len(param.values) for param in self.parameters.values()) if self.parameters else 0
            
            # Daten schreiben
            for i in range(max_len):
                row = []
                
                # Timestamp
                if i < len(list(self.parameters.values())[0].timestamps):
                    timestamp = list(self.parameters.values())[0].timestamps[i]
                    row.append(timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'))
                else:
                    row.append('')
                
                # Parameter-Werte
                for param in self.parameters.values():
                    if i < len(param.values):
                        row.append(param.values[i])
                    else:
                        row.append('')
                        
                writer.writerow(row)
                
    def export_json(self, filename):
        """JSON Export"""
        data = {
            'export_time': datetime.now().isoformat(),
            'parameters': {}
        }
        
        for name, param in self.parameters.items():
            data['parameters'][name] = {
                'unit': param.unit,
                'min_val': param.min_val,
                'max_val': param.max_val,
                'color': param.color,
                'values': list(param.values),
                'timestamps': [ts.isoformat() for ts in param.timestamps]
            }
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class RealTimeGraphManager(QMainWindow):
    """Hauptfenster für Live-Graph Management"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyPSADiag - Live ECU Parameter Monitoring")
        self.setGeometry(100, 100, 1200, 800)
        
        # Parent reference for ECU access
        self.parent_window = parent
        self.serial_controller = None
        self.ecu_connected = False
        
        self.setup_ui()
        self.setup_sample_data()
        self.setup_ecu_connection()
        
    def setup_ui(self):
        """UI Setup"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Graph Widget
        self.graph_manager = RealTimeGraphWidget()
        layout.addWidget(self.graph_manager)
        
        # Setup Menubar
        self.setup_menubar()
        
    def setup_menubar(self):
        """Menubar erstellen"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('Datei')
        
        export_action = QAction('Exportieren...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.graph_manager.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu('Ansicht')
        
        fullscreen_action = QAction('Vollbild', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
    def toggle_fullscreen(self):
        """Vollbild umschalten"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def setup_sample_data(self):
        """Beispiel-Parameter erstellen"""
        # Standard ECU Parameter
        self.graph_manager.add_parameter("Motortemperatur", "°C", 0, 120, '#d13438')
        self.graph_manager.add_parameter("Kühlmitteltemperatur", "°C", 0, 100, '#0078d4')
        self.graph_manager.add_parameter("Motordrehzahl", "U/min", 0, 8000, '#107c10')
        self.graph_manager.add_parameter("Fahrzeuggeschwindigkeit", "km/h", 0, 250, '#ff8c00')
        self.graph_manager.add_parameter("Kraftstoffverbrauch", "l/100km", 0, 20, '#5c2d91')
        self.graph_manager.add_parameter("Batterispannung", "V", 10, 16, '#0099bc')
        
        # Simulations-Timer für Demo (nur wenn keine ECU verbunden)
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.generate_demo_data)
        if not self.ecu_connected:
            self.demo_timer.start(200)  # Alle 200ms neue Demo-Daten
        
    def generate_demo_data(self):
        """Demo-Daten generieren"""
        if not self.graph_manager.monitoring:
            return
            
        import random
        
        # Simulierte ECU-Daten
        current_time = time.time()
        
        # Motortemperatur: 70-95°C mit langsamen Schwankungen
        temp = 82 + 10 * np.sin(current_time * 0.1) + random.gauss(0, 2)
        self.graph_manager.update_parameter("Motortemperatur", max(0, min(120, temp)))
        
        # Kühlmitteltemperatur: etwas niedriger
        coolant_temp = temp - 5 + random.gauss(0, 1)
        self.graph_manager.update_parameter("Kühlmitteltemperatur", max(0, min(100, coolant_temp)))
        
        # Motordrehzahl: variable
        rpm = 1500 + 2000 * abs(np.sin(current_time * 0.3)) + random.gauss(0, 100)
        self.graph_manager.update_parameter("Motordrehzahl", max(0, min(8000, rpm)))
        
        # Geschwindigkeit
        speed = 50 + 30 * np.sin(current_time * 0.2) + random.gauss(0, 5)
        self.graph_manager.update_parameter("Fahrzeuggeschwindigkeit", max(0, min(250, speed)))
        
        # Kraftstoffverbrauch
        consumption = 8 + 4 * abs(np.sin(current_time * 0.25)) + random.gauss(0, 0.5)
        self.graph_manager.update_parameter("Kraftstoffverbrauch", max(0, min(20, consumption)))
        
        # Batterispannung
        voltage = 12.8 + 0.5 * np.sin(current_time * 0.05) + random.gauss(0, 0.1)
        self.graph_manager.update_parameter("Batterispannung", max(10, min(16, voltage)))
    
    


def main():
    """Hauptfunktion für Testing"""
    app = QApplication(sys.argv)
    
    # Styles
    app.setStyle('Fusion')
    
    window = RealTimeGraphManager()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    main()