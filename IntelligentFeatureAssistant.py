"""
   IntelligentFeatureAssistant.py

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

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QProgressBar, QScrollArea, QFrame,
                                 QGroupBox, QCheckBox, QComboBox, QTextEdit,
                                 QWizard, QWizardPage, QRadioButton, QButtonGroup,
                                 QListWidget, QListWidgetItem, QMessageBox)
    from PySide6.QtCore import QThread, Signal, Qt
    from PySide6.QtGui import QFont, QPixmap, QIcon
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QProgressBar, QScrollArea, QFrame,
                                   QGroupBox, QCheckBox, QComboBox, QTextEdit,
                                   QWizard, QWizardPage, QRadioButton, QButtonGroup,
                                   QListWidget, QListWidgetItem, QMessageBox)
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, Qt
        from PyQt5.QtGui import QFont, QPixmap, QIcon
        QT_FRAMEWORK = "PyQt5"


class VINAnalyzer:
    """Analysiert VIN-Nummern und extrahiert Fahrzeugdaten"""
    
    def __init__(self):
        self.vehicle_database = self.load_vehicle_database()
    
    def load_vehicle_database(self) -> Dict:
        """Lädt Fahrzeug-Datenbank"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "vehicle_profiles.json")
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load vehicle database: {e}")
        
        # Fallback Datenbank
        return {
            "PSA_VEHICLES": {
                "VR1": {"brand": "Peugeot", "model": "208", "year_range": "2019-2025"},
                "VR7": {"brand": "Peugeot", "model": "2008", "year_range": "2019-2025"},
                "VR3": {"brand": "Citroën", "model": "C3", "year_range": "2016-2025"},
                "VAH": {"brand": "Opel", "model": "Corsa", "year_range": "2019-2025"},
                "VAG": {"brand": "Opel", "model": "Mokka", "year_range": "2020-2025"}
            }
        }
    
    def analyze_vin(self, vin: str) -> Dict:
        """Analysiert VIN und gibt Fahrzeugdaten zurück"""
        if not vin or len(vin) != 17:
            return {"error": "Invalid VIN length"}
        
        # VIN Parsing
        wmi = vin[:3]  # World Manufacturer Identifier
        vds = vin[3:9]  # Vehicle Descriptor Section
        vis = vin[9:]   # Vehicle Identifier Section
        
        model_code = vin[3:6] if len(vin) >= 6 else "UNKNOWN"
        year_digit = vin[9] if len(vin) > 9 else "X"
        
        # Model year decoding
        year_map = {
            'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
            'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
            'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025
        }
        
        model_year = year_map.get(year_digit, "Unknown")
        
        # Fahrzeug-Erkennung
        vehicle_info = self.identify_vehicle(model_code, wmi)
        
        return {
            "vin": vin,
            "wmi": wmi,
            "model_code": model_code,
            "model_year": model_year,
            "vehicle_info": vehicle_info,
            "valid": True
        }
    
    def identify_vehicle(self, model_code: str, wmi: str) -> Dict:
        """Identifiziert Fahrzeug basierend auf VIN"""
        for code, info in self.vehicle_database.get("PSA_VEHICLES", {}).items():
            if model_code.startswith(code):
                return info
        
        # PSA WMI Codes
        psa_wmi_codes = {
            "VF7": "Peugeot",
            "VF3": "Peugeot", 
            "VF1": "Peugeot",
            "VR1": "Peugeot",
            "VR7": "Peugeot",
            "VF6": "Citroën",
            "VF2": "Citroën",
            "VR3": "Citroën",
            "W0L": "Opel",
            "VAH": "Opel",
            "VAG": "Opel"
        }
        
        brand = psa_wmi_codes.get(wmi, "Unknown PSA")
        
        return {
            "brand": brand,
            "model": "Unknown Model",
            "year_range": "Unknown",
            "confidence": 0.7 if brand != "Unknown PSA" else 0.3
        }


class FeatureRiskAnalyzer:
    """Analysiert Risiken bei Feature-Aktivierungen"""
    
    RISK_LEVELS = {
        "LOW": {"color": "#4CAF50", "icon": "🟢", "score": 1},
        "MEDIUM": {"color": "#FF9800", "icon": "🟡", "score": 2}, 
        "HIGH": {"color": "#F44336", "icon": "🔴", "score": 3}
    }
    
    def __init__(self):
        self.feature_risks = self.load_risk_database()
    
    def load_risk_database(self) -> Dict:
        """Lädt Feature-Risiko-Datenbank"""
        return {
            # Komfort Features - Niedriges Risiko
            "auto_lights": {"risk": "LOW", "reason": "Sicherheitsrelevant aber reversibel"},
            "convenience_lighting": {"risk": "LOW", "reason": "Nur Komfort, keine Sicherheit"},
            "window_comfort": {"risk": "LOW", "reason": "Komfort-Feature ohne Sicherheitsimpact"},
            
            # Fahrer-Assistenz - Mittleres Risiko
            "park_assist": {"risk": "MEDIUM", "reason": "Sicherheitsfeature, benötigt Sensoren"},
            "lane_assist": {"risk": "MEDIUM", "reason": "Aktives Sicherheitssystem"},
            "speed_limiter": {"risk": "MEDIUM", "reason": "Fahrdynamik-relevant"},
            
            # Motor/Getriebe - Hohes Risiko
            "engine_tuning": {"risk": "HIGH", "reason": "Motorsicherheit kritisch"},
            "gearbox_settings": {"risk": "HIGH", "reason": "Getriebe-Parameter kritisch"},
            "abs_settings": {"risk": "HIGH", "reason": "Bremssicherheit kritisch"},
            "airbag_settings": {"risk": "HIGH", "reason": "Lebenswichtige Sicherheit"}
        }
    
    def analyze_feature_risk(self, feature_id: str, vehicle_info: Dict) -> Dict:
        """Analysiert Risiko für spezifisches Feature"""
        
        # Basis-Risiko aus Datenbank
        base_risk = self.feature_risks.get(feature_id, {"risk": "MEDIUM", "reason": "Unbekanntes Feature"})
        
        risk_factors = []
        risk_modifiers = 0
        
        # Fahrzeug-spezifische Risiko-Modifikation
        if vehicle_info.get("model_year", 0) < 2015:
            risk_modifiers += 1
            risk_factors.append("Älteres Fahrzeug (vor 2015)")
        
        confidence = vehicle_info.get("confidence", 1.0)
        if confidence < 0.8:
            risk_modifiers += 1
            risk_factors.append("Fahrzeug-Identifikation unsicher")
        
        # Risiko-Level anpassen
        base_level = base_risk["risk"]
        final_risk = self.adjust_risk_level(base_level, risk_modifiers)
        
        return {
            "feature_id": feature_id,
            "risk_level": final_risk,
            "base_risk": base_level,
            "risk_factors": risk_factors,
            "recommendation": self.get_risk_recommendation(final_risk),
            "visual": self.RISK_LEVELS[final_risk],
            "description": base_risk["reason"]
        }
    
    def adjust_risk_level(self, base_level: str, modifiers: int) -> str:
        """Passt Risiko-Level basierend auf Modifikatoren an"""
        levels = ["LOW", "MEDIUM", "HIGH"]
        current_index = levels.index(base_level)
        new_index = min(len(levels) - 1, current_index + modifiers)
        return levels[new_index]
    
    def get_risk_recommendation(self, risk_level: str) -> str:
        """Gibt Empfehlung basierend auf Risiko-Level"""
        recommendations = {
            "LOW": "✅ Sicher aktivierbar - Backup empfohlen",
            "MEDIUM": "⚠️ Mit Vorsicht - Backup zwingend erforderlich", 
            "HIGH": "🛑 Nur für Experten - Vollständiges Backup + Werkstatt"
        }
        return recommendations.get(risk_level, "Unbekanntes Risiko")


class FeatureWizardPage(QWizardPage):
    """Einzelne Wizard-Seite für Feature-Aktivierung"""
    
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setTitle(title)
        if subtitle:
            self.setSubTitle(subtitle)
        
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)


class VINInputPage(FeatureWizardPage):
    """VIN-Eingabe Seite"""
    
    def __init__(self, assistant):
        super().__init__("Fahrzeug-Identifikation", "Geben Sie Ihre VIN-Nummer ein für maßgeschneiderte Feature-Empfehlungen")
        
        self.assistant = assistant
        self.setup_ui()
    
    def setup_ui(self):
        # VIN Input
        self.vin_input = QComboBox()
        self.vin_input.setEditable(True)
        self.vin_input.setPlaceholderText("VIN-Nummer eingeben (17 Zeichen)")
        
        # Beispiel VINs
        self.vin_input.addItems([
            "VR7XXXXXXXXXXXXXXX",  # Peugeot 2008
            "VAHXXXXXXXXXXXXXXX",  # Opel Corsa
            "VR3XXXXXXXXXXXXXXX"   # Citroën C3
        ])
        
        self.layout.addWidget(QLabel("VIN-Nummer:"))
        self.layout.addWidget(self.vin_input)
        
        # Fahrzeug Info Display
        self.vehicle_info_display = QTextEdit()
        self.vehicle_info_display.setMaximumHeight(120)
        self.vehicle_info_display.setReadOnly(True)
        self.layout.addWidget(QLabel("Erkanntes Fahrzeug:"))
        self.layout.addWidget(self.vehicle_info_display)
        
        # VIN Analyse Button
        analyze_btn = QPushButton("VIN analysieren")
        analyze_btn.clicked.connect(self.analyze_vin)
        self.layout.addWidget(analyze_btn)
        
        self.layout.addStretch()
        
        # Register field für Wizard
        self.registerField("vin", self.vin_input, "currentText")
    
    def analyze_vin(self):
        """Analysiert eingegebene VIN"""
        vin = self.vin_input.currentText().strip().upper()
        
        if not vin:
            self.vehicle_info_display.setText("Bitte VIN-Nummer eingeben")
            return
        
        # VIN analysieren
        result = self.assistant.vin_analyzer.analyze_vin(vin)
        
        if "error" in result:
            self.vehicle_info_display.setText(f"❌ Fehler: {result['error']}")
            return
        
        # Ergebnis anzeigen
        vehicle_info = result.get("vehicle_info", {})
        info_text = f"""
✅ VIN erfolgreich analysiert

🚗 Fahrzeug: {vehicle_info.get('brand', 'Unbekannt')} {vehicle_info.get('model', 'Unbekannt')}
📅 Baujahr: {result.get('model_year', 'Unbekannt')}
🔧 Modell-Code: {result.get('model_code', 'Unbekannt')}
📊 Konfidenz: {vehicle_info.get('confidence', 0)*100:.0f}%

Basierend auf diesen Daten werden passende Features vorgeschlagen.
        """
        
        self.vehicle_info_display.setText(info_text.strip())
        
        # Daten für nächste Seite speichern
        self.assistant.vehicle_data = result


class FeatureSelectionPage(FeatureWizardPage):
    """Feature-Auswahl Seite mit Risiko-Bewertung"""
    
    def __init__(self, assistant):
        super().__init__("Feature-Auswahl", "Wählen Sie Features basierend auf Ihrem Fahrzeug und Risiko-Toleranz")
        
        self.assistant = assistant
        self.feature_checkboxes = {}
        self.setup_ui()
    
    def setup_ui(self):
        # Scroll Area für Features
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Feature-Kategorien
        categories = {
            "Komfort & Beleuchtung": [
                {"id": "auto_lights", "name": "Automatisches Licht", "desc": "Coming/Leaving Home, Follow-Me-Home"},
                {"id": "convenience_lighting", "name": "Komfort-Beleuchtung", "desc": "Welcome-Beleuchtung, Ambiente-Licht"},
                {"id": "window_comfort", "name": "Fenster-Komfort", "desc": "Ein-Touch-Bedienung aller Fenster"}
            ],
            "Fahrer-Assistenz": [
                {"id": "park_assist", "name": "Park-Assistent", "desc": "Halbautomatisches Einparken"},
                {"id": "lane_assist", "name": "Spurhalte-Assistent", "desc": "Warnung bei Spurverlassen"},
                {"id": "speed_limiter", "name": "Geschwindigkeitsbegrenzer", "desc": "Programmierbare Höchstgeschwindigkeit"}
            ],
            "Erweiterte Funktionen": [
                {"id": "engine_tuning", "name": "Motor-Optimierung", "desc": "Erweiterte Motor-Parameter"},
                {"id": "gearbox_settings", "name": "Getriebe-Einstellungen", "desc": "Sport-/Eco-Modi"},
            ]
        }
        
        for category, features in categories.items():
            # Kategorie-Header
            category_group = QGroupBox(category)
            category_layout = QVBoxLayout(category_group)
            
            for feature in features:
                # Feature mit Risiko-Analyse
                feature_widget = self.create_feature_widget(feature)
                category_layout.addWidget(feature_widget)
            
            scroll_layout.addWidget(category_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        self.layout.addWidget(scroll)
    
    def create_feature_widget(self, feature: Dict) -> QWidget:
        """Erstellt Widget für einzelnes Feature mit Risiko-Bewertung"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout(widget)
        
        # Feature Checkbox
        checkbox = QCheckBox(feature["name"])
        checkbox.setToolTip(feature["desc"])
        self.feature_checkboxes[feature["id"]] = checkbox
        
        # Risiko-Analyse
        vehicle_data = getattr(self.assistant, 'vehicle_data', {})
        vehicle_info = vehicle_data.get('vehicle_info', {})
        risk_analysis = self.assistant.risk_analyzer.analyze_feature_risk(feature["id"], vehicle_info)
        
        # Risiko-Anzeige
        risk_label = QLabel(f"{risk_analysis['visual']['icon']} {risk_analysis['risk_level']}")
        risk_label.setStyleSheet(f"color: {risk_analysis['visual']['color']}; font-weight: bold;")
        risk_label.setToolTip(risk_analysis['recommendation'])
        
        # Layout
        layout.addWidget(checkbox, 3)
        layout.addWidget(QLabel(feature["desc"]), 4)
        layout.addWidget(risk_label, 1)
        
        return widget
    
    def get_selected_features(self) -> List[str]:
        """Gibt ausgewählte Features zurück"""
        selected = []
        for feature_id, checkbox in self.feature_checkboxes.items():
            if checkbox.isChecked():
                selected.append(feature_id)
        return selected


class SummaryPage(FeatureWizardPage):
    """Zusammenfassung und Bestätigung"""
    
    def __init__(self, assistant):
        super().__init__("Zusammenfassung", "Überprüfen Sie Ihre Auswahl vor der Aktivierung")
        
        self.assistant = assistant
        self.setup_ui()
    
    def setup_ui(self):
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.layout.addWidget(self.summary_display)
        
        # Backup Warnung
        backup_warning = QLabel("⚠️ WICHTIG: Automatisches Backup wird vor Aktivierung erstellt!")
        backup_warning.setStyleSheet("background-color: #FFF3CD; padding: 10px; border-radius: 5px; font-weight: bold;")
        self.layout.addWidget(backup_warning)
    
    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird"""
        # Zusammenfassung generieren
        vehicle_data = getattr(self.assistant, 'vehicle_data', {})
        selected_features = self.assistant.get_selected_features()
        
        summary = self.generate_summary(vehicle_data, selected_features)
        self.summary_display.setText(summary)
    
    def generate_summary(self, vehicle_data: Dict, selected_features: List[str]) -> str:
        """Generiert Aktivierungs-Zusammenfassung"""
        vehicle_info = vehicle_data.get('vehicle_info', {})
        
        summary = f"""
🚗 FAHRZEUG-INFORMATION
Marke: {vehicle_info.get('brand', 'Unbekannt')}
Modell: {vehicle_info.get('model', 'Unbekannt')}  
Baujahr: {vehicle_data.get('model_year', 'Unbekannt')}
VIN: {vehicle_data.get('vin', 'Nicht verfügbar')}

🔧 FEATURES ZUR AKTIVIERUNG ({len(selected_features)} ausgewählt)
"""
        
        if not selected_features:
            summary += "\n❌ Keine Features ausgewählt"
            return summary
        
        # Feature-Details mit Risiko
        total_risk_score = 0
        for feature_id in selected_features:
            risk_analysis = self.assistant.risk_analyzer.analyze_feature_risk(feature_id, vehicle_info)
            summary += f"\n{risk_analysis['visual']['icon']} {feature_id.replace('_', ' ').title()}"
            summary += f"\n   Risiko: {risk_analysis['risk_level']} - {risk_analysis['description']}"
            summary += f"\n   Empfehlung: {risk_analysis['recommendation']}\n"
            
            total_risk_score += risk_analysis['visual']['score']
        
        # Gesamt-Risiko
        avg_risk = total_risk_score / len(selected_features)
        if avg_risk <= 1.5:
            overall_risk = "🟢 NIEDRIG"
        elif avg_risk <= 2.5:
            overall_risk = "🟡 MITTEL"
        else:
            overall_risk = "🔴 HOCH"
        
        summary += f"\n📊 GESAMT-RISIKO: {overall_risk}"
        summary += f"\n\n✅ NÄCHSTE SCHRITTE:"
        summary += f"\n1. Automatisches Backup wird erstellt"
        summary += f"\n2. Features werden nacheinander aktiviert"
        summary += f"\n3. Erfolgs-/Fehler-Bericht wird angezeigt"
        summary += f"\n4. Bei Problemen: Ein-Klick-Rollback verfügbar"
        
        return summary


class IntelligentFeatureAssistant(QWizard):
    """Hauptklasse für intelligenten Feature-Assistenten"""
    
    # Signals
    feature_activation_requested = Signal(list)  # Liste der Features zur Aktivierung
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Intelligenter Feature-Assistent")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(800, 600)
        
        # Analyzer initialisieren
        self.vin_analyzer = VINAnalyzer()
        self.risk_analyzer = FeatureRiskAnalyzer()
        
        # Daten-Storage
        self.vehicle_data = {}
        
        # Wizard-Seiten hinzufügen
        self.addPage(VINInputPage(self))
        self.addPage(FeatureSelectionPage(self))
        self.addPage(SummaryPage(self))
        
        # Wizard-Buttons anpassen
        self.setButtonText(QWizard.WizardButton.FinishButton, "Features aktivieren")
        
        # Signals verbinden
        self.finished.connect(self.on_wizard_finished)
    
    def get_selected_features(self) -> List[str]:
        """Gibt ausgewählte Features von FeatureSelectionPage zurück"""
        selection_page = self.page(1)  # Index 1 = FeatureSelectionPage
        if hasattr(selection_page, 'get_selected_features'):
            return selection_page.get_selected_features()
        return []
    
    def on_wizard_finished(self, result: int):
        """Wird aufgerufen wenn Wizard beendet wird"""
        if result == QWizard.DialogCode.Accepted:
            selected_features = self.get_selected_features()
            if selected_features:
                self.feature_activation_requested.emit(selected_features)
            else:
                QMessageBox.information(self, "Information", "Keine Features ausgewählt")


# Test/Demo Funktionen
def create_demo_assistant():
    """Erstellt Demo-Assistent für Testing"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    assistant = IntelligentFeatureAssistant()
    
    def on_features_requested(features):
        print(f"Features zur Aktivierung: {features}")
    
    assistant.feature_activation_requested.connect(on_features_requested)
    assistant.show()
    
    return assistant, app


if __name__ == "__main__":
    assistant, app = create_demo_assistant()
    app.exec() if hasattr(app, 'exec') else app.exec_()