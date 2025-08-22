#!/usr/bin/env python3
"""
Feature Template System für PyPSADiag
Vordefinierte Feature-Sets für Bulk-Aktivierung und Fahrzeugprofile
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

try:
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                                 QComboBox, QCheckBox, QGroupBox, QTabWidget, QTreeWidget,
                                 QTreeWidgetItem, QProgressBar, QSpinBox, QLineEdit,
                                 QMessageBox, QFileDialog, QSplitter)
    from PySide6.QtGui import QFont, QColor, QIcon
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, QTimer, Qt
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                                   QComboBox, QCheckBox, QGroupBox, QTabWidget, QTreeWidget,
                                   QTreeWidgetItem, QProgressBar, QSpinBox, QLineEdit,
                                   QMessageBox, QFileDialog, QSplitter)
        from PyQt5.QtGui import QFont, QColor, QIcon
        QT_FRAMEWORK = "PyQt5"

class FeatureCategory(Enum):
    """Kategorien für Feature-Organisation"""
    COMFORT = "Comfort & Convenience"
    PERFORMANCE = "Performance & Driving"
    SAFETY = "Safety & Security"
    LIGHTING = "Lighting & Visibility"
    INFOTAINMENT = "Infotainment & Navigation"
    CLIMATE = "Climate & Air"
    MAINTENANCE = "Maintenance & Service"
    ADVANCED = "Advanced & Expert"

class RiskLevel(Enum):
    """Risikostufen für Features"""
    LOW = "Low Risk"
    MEDIUM = "Medium Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"

@dataclass
class Feature:
    """Einzelnes Feature mit Metadaten"""
    id: str
    name: str
    description: str
    category: FeatureCategory
    risk_level: RiskLevel
    ecu_target: str
    zone_modifications: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    vehicle_compatibility: List[str] = field(default_factory=list)
    popularity_score: int = 50  # 0-100
    activation_time_estimate: int = 30  # Sekunden
    backup_required: bool = True
    expert_only: bool = False
    
    def to_dict(self) -> Dict:
        """Konvertiert zu Dictionary"""
        data = asdict(self)
        data['category'] = self.category.value
        data['risk_level'] = self.risk_level.value
        return data

@dataclass
class FeatureTemplate:
    """Vordefiniertes Feature-Set Template"""
    id: str
    name: str
    description: str
    category: str
    features: List[str]  # Feature IDs
    target_audience: str
    estimated_time: int
    risk_assessment: str
    prerequisites: List[str] = field(default_factory=list)
    post_activation_notes: List[str] = field(default_factory=list)
    vehicle_profiles: List[str] = field(default_factory=list)
    popularity: int = 50
    created_by: str = "System"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class VehicleTemplate:
    """Fahrzeugspezifisches Template"""
    id: str
    manufacturer: str
    model: str
    year_from: int
    year_to: int
    platform: str
    vin_patterns: List[str]
    recommended_features: List[str]
    blocked_features: List[str] = field(default_factory=list)
    special_notes: str = ""

class FeatureTemplateManager:
    """Verwaltet Feature-Templates und Bulk-Operationen"""
    
    def __init__(self, templates_directory: str = "templates"):
        self.templates_dir = Path(templates_directory)
        self.templates_dir.mkdir(exist_ok=True)
        
        self.features: Dict[str, Feature] = {}
        self.templates: Dict[str, FeatureTemplate] = {}
        self.vehicle_templates: Dict[str, VehicleTemplate] = {}
        
        self.load_builtin_features()
        self.load_builtin_templates()
        self.load_custom_templates()
        
        print(f"[TEMPLATES] Feature Template Manager initialisiert")
        print(f"[TEMPLATES] {len(self.features)} Features, {len(self.templates)} Templates geladen")
    
    def load_builtin_features(self):
        """Lädt eingebaute Feature-Definitionen"""
        
        builtin_features = [
            # Comfort Features
            Feature(
                id="coming_home_lights",
                name="Coming Home Beleuchtung",
                description="Beleuchtung beim Aussteigen für 30-60 Sekunden",
                category=FeatureCategory.LIGHTING,
                risk_level=RiskLevel.LOW,
                ecu_target="BSI",
                zone_modifications={"C1": {"byte_5": "0x01"}, "C3": {"byte_2": "0x1E"}},
                vehicle_compatibility=["PSA", "Stellantis"],
                popularity_score=85
            ),
            
            Feature(
                id="leaving_home_lights", 
                name="Leaving Home Beleuchtung",
                description="Beleuchtung beim Einsteigen aktivieren",
                category=FeatureCategory.LIGHTING,
                risk_level=RiskLevel.LOW,
                ecu_target="BSI",
                zone_modifications={"C1": {"byte_6": "0x01"}, "C3": {"byte_3": "0x1E"}},
                dependencies=["coming_home_lights"],
                popularity_score=75
            ),
            
            Feature(
                id="auto_door_lock",
                name="Automatische Türverriegelung",
                description="Türen automatisch bei Fahrtbeginn verriegeln",
                category=FeatureCategory.SAFETY,
                risk_level=RiskLevel.MEDIUM,
                ecu_target="BSI",
                zone_modifications={"C2": {"byte_1": "0x01"}},
                popularity_score=90
            ),
            
            Feature(
                id="speed_dependent_locking",
                name="Geschwindigkeitsabhängige Verriegelung",
                description="Türen ab 10 km/h automatisch verriegeln",
                category=FeatureCategory.SAFETY,
                risk_level=RiskLevel.MEDIUM,
                ecu_target="BSI",
                zone_modifications={"C2": {"byte_2": "0x0A"}},
                dependencies=["auto_door_lock"],
                popularity_score=80
            ),
            
            Feature(
                id="daytime_running_lights",
                name="Tagfahrlicht Konfiguration",
                description="Tagfahrlicht automatisch bei Motorstart",
                category=FeatureCategory.LIGHTING,
                risk_level=RiskLevel.LOW,
                ecu_target="BSI",
                zone_modifications={"C4": {"byte_1": "0x01"}},
                popularity_score=95
            ),
            
            Feature(
                id="mirror_fold_on_lock",
                name="Spiegel einklappen beim Abschließen",
                description="Außenspiegel automatisch beim Verriegeln einklappen",
                category=FeatureCategory.COMFORT,
                risk_level=RiskLevel.LOW,
                ecu_target="BSI", 
                zone_modifications={"C5": {"byte_3": "0x01"}},
                vehicle_compatibility=["premium_models"],
                popularity_score=70
            ),
            
            # Performance Features
            Feature(
                id="sport_mode_enhanced",
                name="Erweiterte Sport-Modus",
                description="Aggressiveres Mapping für Gaspedal und Getriebe",
                category=FeatureCategory.PERFORMANCE,
                risk_level=RiskLevel.HIGH,
                ecu_target="Engine",
                zone_modifications={"E1": {"byte_10": "0xFF"}, "E2": {"byte_5": "0x80"}},
                expert_only=True,
                popularity_score=60
            ),
            
            Feature(
                id="launch_control",
                name="Launch Control",
                description="Optimaler Startvorgang für maximale Beschleunigung",
                category=FeatureCategory.PERFORMANCE,
                risk_level=RiskLevel.CRITICAL,
                ecu_target="Engine",
                zone_modifications={"E3": {"byte_1": "0x01", "byte_2": "0x1F4"}},
                dependencies=["sport_mode_enhanced"],
                expert_only=True,
                popularity_score=30
            ),
            
            # Safety Features
            Feature(
                id="emergency_brake_assist",
                name="Notbremsassistent",
                description="Erweiterte Notbremsfunktion aktivieren",
                category=FeatureCategory.SAFETY,
                risk_level=RiskLevel.MEDIUM,
                ecu_target="ESP",
                zone_modifications={"A1": {"byte_7": "0x01"}},
                popularity_score=85
            ),
            
            # Climate Features  
            Feature(
                id="auto_climate_comfort",
                name="Komfort-Klimaautomatik",
                description="Intelligente Klimaregelung mit Vorausschau",
                category=FeatureCategory.CLIMATE,
                risk_level=RiskLevel.LOW,
                ecu_target="Climate",
                zone_modifications={"CC1": {"byte_4": "0x01"}},
                popularity_score=75
            )
        ]
        
        for feature in builtin_features:
            self.features[feature.id] = feature
    
    def load_builtin_templates(self):
        """Lädt eingebaute Feature-Templates"""
        
        builtin_templates = [
            FeatureTemplate(
                id="comfort_package_basic",
                name="Basis Komfort-Paket",
                description="Grundlegende Komfort-Features für den täglichen Gebrauch",
                category="Comfort",
                features=["coming_home_lights", "leaving_home_lights", "auto_door_lock", "daytime_running_lights"],
                target_audience="Alle Benutzer",
                estimated_time=120,
                risk_assessment="Niedriges Risiko - Empfohlen für alle",
                vehicle_profiles=["psa_standard", "stellantis_basic"],
                popularity=95
            ),
            
            FeatureTemplate(
                id="comfort_package_premium",
                name="Premium Komfort-Paket",
                description="Erweiterte Komfort-Features inklusive Spiegel-Funktionen",
                category="Comfort",
                features=["coming_home_lights", "leaving_home_lights", "auto_door_lock", 
                         "speed_dependent_locking", "daytime_running_lights", "mirror_fold_on_lock"],
                target_audience="Premium-Fahrzeuge",
                estimated_time=180,
                risk_assessment="Niedriges bis mittleres Risiko",
                prerequisites=["Premium-Ausstattung mit elektrischen Spiegeln"],
                vehicle_profiles=["psa_premium", "ds_models"],
                popularity=80
            ),
            
            FeatureTemplate(
                id="safety_package_standard",
                name="Standard Sicherheits-Paket",
                description="Grundlegende Sicherheitsfeatures für erhöhten Schutz",
                category="Safety", 
                features=["auto_door_lock", "speed_dependent_locking", "emergency_brake_assist"],
                target_audience="Sicherheitsbewusste Fahrer",
                estimated_time=150,
                risk_assessment="Mittleres Risiko - Vorsicht bei ESP-Modifikationen",
                vehicle_profiles=["psa_standard", "stellantis_basic", "psa_premium"],
                popularity=85
            ),
            
            FeatureTemplate(
                id="lighting_package_complete",
                name="Komplettes Beleuchtungs-Paket",
                description="Alle verfügbaren Beleuchtungsfeatures",
                category="Lighting",
                features=["coming_home_lights", "leaving_home_lights", "daytime_running_lights"],
                target_audience="Beleuchtungs-Enthusiasten",
                estimated_time=90,
                risk_assessment="Niedriges Risiko",
                post_activation_notes=["Beleuchtungszeiten können in den Fahrzeugeinstellungen angepasst werden"],
                popularity=90
            ),
            
            FeatureTemplate(
                id="performance_package_expert",
                name="Performance-Paket (Experten)",
                description="Hochleistungs-Features für erfahrene Benutzer",
                category="Performance",
                features=["sport_mode_enhanced", "launch_control"],
                target_audience="Experten und Tuning-Enthusiasten",
                estimated_time=300,
                risk_assessment="HOHES RISIKO - Nur für Experten!",
                prerequisites=["Umfassendes Backup", "Expertenwissen erforderlich", "Garantieverlust möglich"],
                post_activation_notes=[
                    "Launch Control nur auf geschlossenen Kursen verwenden",
                    "Erhöhter Verschleiß möglich",
                    "Regelmäßige Überprüfung der Motorparameter empfohlen"
                ],
                popularity=25
            ),
            
            FeatureTemplate(
                id="daily_driver_essentials",
                name="Täglicher Fahrer - Essentials",
                description="Die wichtigsten Features für den Alltag",
                category="Mixed",
                features=["daytime_running_lights", "auto_door_lock", "coming_home_lights", "auto_climate_comfort"],
                target_audience="Alltagsfahrer",
                estimated_time=200,
                risk_assessment="Niedriges Risiko - Ideal für Einsteiger",
                popularity=100
            )
        ]
        
        for template in builtin_templates:
            self.templates[template.id] = template
    
    def load_custom_templates(self):
        """Lädt benutzerdefinierte Templates aus Dateien"""
        
        templates_file = self.templates_dir / "custom_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for template_data in data.get('templates', []):
                        template = FeatureTemplate(**template_data)
                        self.templates[template.id] = template
                        
                    print(f"[TEMPLATES] {len(data.get('templates', []))} benutzerdefinierte Templates geladen")
                    
            except Exception as e:
                print(f"[TEMPLATES] Fehler beim Laden der Templates: {e}")
    
    def save_custom_templates(self):
        """Speichert benutzerdefinierte Templates"""
        
        custom_templates = [t for t in self.templates.values() if t.created_by != "System"]
        
        if custom_templates:
            templates_file = self.templates_dir / "custom_templates.json"
            
            export_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "templates": [asdict(t) for t in custom_templates]
            }
            
            try:
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                print(f"[TEMPLATES] {len(custom_templates)} Templates gespeichert")
            except Exception as e:
                print(f"[TEMPLATES] Fehler beim Speichern: {e}")
    
    def get_features_by_category(self, category: FeatureCategory) -> List[Feature]:
        """Gibt Features einer Kategorie zurück"""
        return [f for f in self.features.values() if f.category == category]
    
    def get_templates_by_category(self, category: str) -> List[FeatureTemplate]:
        """Gibt Templates einer Kategorie zurück"""
        return [t for t in self.templates.values() if t.category.lower() == category.lower()]
    
    def get_popular_templates(self, limit: int = 5) -> List[FeatureTemplate]:
        """Gibt beliebteste Templates zurück"""
        sorted_templates = sorted(self.templates.values(), key=lambda t: t.popularity, reverse=True)
        return sorted_templates[:limit]
    
    def create_custom_template(self, name: str, description: str, feature_ids: List[str], 
                             category: str = "Custom", **kwargs) -> FeatureTemplate:
        """Erstellt benutzerdefiniertes Template"""
        
        template_id = f"custom_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        # Geschätzte Zeit basierend auf Features berechnen
        estimated_time = sum(self.features[fid].activation_time_estimate 
                           for fid in feature_ids if fid in self.features)
        
        # Risikobewertung basierend auf Features
        risk_levels = [self.features[fid].risk_level for fid in feature_ids if fid in self.features]
        if any(r == RiskLevel.CRITICAL for r in risk_levels):
            risk_assessment = "Kritisches Risiko"
        elif any(r == RiskLevel.HIGH for r in risk_levels):
            risk_assessment = "Hohes Risiko"
        elif any(r == RiskLevel.MEDIUM for r in risk_levels):
            risk_assessment = "Mittleres Risiko"
        else:
            risk_assessment = "Niedriges Risiko"
        
        template = FeatureTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            features=feature_ids,
            target_audience=kwargs.get('target_audience', 'Benutzerdefiniert'),
            estimated_time=estimated_time,
            risk_assessment=risk_assessment,
            created_by="User",
            **{k: v for k, v in kwargs.items() if k != 'target_audience'}
        )
        
        self.templates[template_id] = template
        self.save_custom_templates()
        
        print(f"[TEMPLATES] Benutzerdefiniertes Template erstellt: {name}")
        return template
    
    def validate_template(self, template: FeatureTemplate) -> Tuple[bool, List[str]]:
        """Validiert Template auf Konflikte und Abhängigkeiten"""
        
        issues = []
        
        # Prüfe ob alle Features existieren
        missing_features = [fid for fid in template.features if fid not in self.features]
        if missing_features:
            issues.append(f"Fehlende Features: {', '.join(missing_features)}")
        
        # Prüfe Abhängigkeiten
        available_features = set(template.features)
        for fid in template.features:
            if fid in self.features:
                feature = self.features[fid]
                missing_deps = [dep for dep in feature.dependencies if dep not in available_features]
                if missing_deps:
                    issues.append(f"Feature '{feature.name}' benötigt: {', '.join(missing_deps)}")
        
        # Prüfe Konflikte
        for fid in template.features:
            if fid in self.features:
                feature = self.features[fid]
                conflicts = [conf for conf in feature.conflicts if conf in available_features]
                if conflicts:
                    issues.append(f"Feature '{feature.name}' konfligiert mit: {', '.join(conflicts)}")
        
        return len(issues) == 0, issues
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Gibt Template-Statistiken zurück"""
        
        stats = {
            "total_features": len(self.features),
            "total_templates": len(self.templates),
            "features_by_category": {},
            "templates_by_category": {},
            "risk_distribution": {},
            "most_popular_template": None,
            "average_template_time": 0
        }
        
        # Features nach Kategorie
        for feature in self.features.values():
            cat = feature.category.value
            stats["features_by_category"][cat] = stats["features_by_category"].get(cat, 0) + 1
        
        # Templates nach Kategorie
        for template in self.templates.values():
            cat = template.category
            stats["templates_by_category"][cat] = stats["templates_by_category"].get(cat, 0) + 1
        
        # Risiko-Verteilung
        for feature in self.features.values():
            risk = feature.risk_level.value
            stats["risk_distribution"][risk] = stats["risk_distribution"].get(risk, 0) + 1
        
        # Beliebtestes Template
        if self.templates:
            most_popular = max(self.templates.values(), key=lambda t: t.popularity)
            stats["most_popular_template"] = most_popular.name
        
        # Durchschnittliche Zeit
        if self.templates:
            stats["average_template_time"] = sum(t.estimated_time for t in self.templates.values()) / len(self.templates)
        
        return stats


class FeatureTemplateSystemWidget(QWidget):
    """GUI Widget für Feature Template System"""
    
    def __init__(self, template_manager: FeatureTemplateManager, parent=None):
        super().__init__(parent)
        
        self.template_manager = template_manager
        self.selected_template = None
        self.custom_feature_selection = set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Feature Template System")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Tabs für verschiedene Modi
        self.tabs = QTabWidget()
        
        # Template Browser Tab
        template_tab = self.create_template_browser_tab()
        self.tabs.addTab(template_tab, "📋 Template Browser")
        
        # Custom Builder Tab
        custom_tab = self.create_custom_builder_tab()
        self.tabs.addTab(custom_tab, "🔧 Custom Builder")
        
        # Statistics Tab
        stats_tab = self.create_statistics_tab()
        self.tabs.addTab(stats_tab, "📊 Statistics")
        
        layout.addWidget(self.tabs)
        
        # Activation Controls
        activation_group = QGroupBox("Bulk Activation")
        activation_layout = QVBoxLayout(activation_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        activation_layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Select a template to begin")
        activation_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✅ Validate Template")
        self.validate_btn.clicked.connect(self.validate_current_template)
        button_layout.addWidget(self.validate_btn)
        
        self.activate_btn = QPushButton("🚀 Activate Template")
        self.activate_btn.clicked.connect(self.activate_current_template)
        self.activate_btn.setEnabled(False)
        button_layout.addWidget(self.activate_btn)
        
        self.backup_btn = QPushButton("💾 Create Backup First")
        self.backup_btn.clicked.connect(self.create_backup)
        button_layout.addWidget(self.backup_btn)
        
        activation_layout.addLayout(button_layout)
        layout.addWidget(activation_group)
    
    def create_template_browser_tab(self) -> QWidget:
        """Erstellt Template Browser Tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left: Template List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Category Filter
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Comfort", "Safety", "Lighting", "Performance", "Mixed"])
        self.category_filter.currentTextChanged.connect(self.filter_templates)
        cat_layout.addWidget(self.category_filter)
        
        # Popularity Filter
        cat_layout.addWidget(QLabel("Min Popularity:"))
        self.popularity_filter = QSpinBox()
        self.popularity_filter.setRange(0, 100)
        self.popularity_filter.setValue(0)
        self.popularity_filter.valueChanged.connect(self.filter_templates)
        cat_layout.addWidget(self.popularity_filter)
        
        left_layout.addLayout(cat_layout)
        
        # Template List
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)
        
        layout.addWidget(left_widget, 1)
        
        # Right: Template Details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Template Info
        self.template_info = QTextEdit()
        self.template_info.setReadOnly(True)
        right_layout.addWidget(self.template_info)
        
        # Feature List
        features_group = QGroupBox("Included Features")
        features_layout = QVBoxLayout(features_group)
        
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderLabels(["Feature", "Risk", "ECU", "Time"])
        features_layout.addWidget(self.feature_tree)
        
        right_layout.addWidget(features_group)
        
        layout.addWidget(right_widget, 2)
        
        # Initial Load
        self.filter_templates()
        
        return tab
    
    def create_custom_builder_tab(self) -> QWidget:
        """Erstellt Custom Builder Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Template Info
        info_group = QGroupBox("Template Information")
        info_layout = QVBoxLayout(info_group)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.custom_name_input = QLineEdit()
        name_layout.addWidget(self.custom_name_input)
        info_layout.addLayout(name_layout)
        
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.custom_desc_input = QLineEdit()
        desc_layout.addWidget(self.custom_desc_input)
        info_layout.addLayout(desc_layout)
        
        layout.addWidget(info_group)
        
        # Feature Selection
        selection_group = QGroupBox("Feature Selection")
        selection_layout = QHBoxLayout(selection_group)
        
        # Available Features
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("Available Features:"))
        
        self.available_features_tree = QTreeWidget()
        self.available_features_tree.setHeaderLabels(["Feature", "Category", "Risk"])
        self.populate_available_features()
        available_layout.addWidget(self.available_features_tree)
        
        # Add Button
        add_btn = QPushButton("➡️ Add Selected")
        add_btn.clicked.connect(self.add_selected_features)
        available_layout.addWidget(add_btn)
        
        selection_layout.addLayout(available_layout)
        
        # Selected Features
        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel("Selected Features:"))
        
        self.selected_features_list = QListWidget()
        selected_layout.addWidget(self.selected_features_list)
        
        # Remove Button
        remove_btn = QPushButton("⬅️ Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_features)
        selected_layout.addWidget(remove_btn)
        
        selection_layout.addLayout(selected_layout)
        layout.addWidget(selection_group)
        
        # Create Template Button
        create_btn = QPushButton("💾 Create Custom Template")
        create_btn.clicked.connect(self.create_custom_template)
        layout.addWidget(create_btn)
        
        return tab
    
    def create_statistics_tab(self) -> QWidget:
        """Erstellt Statistics Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Refresh Button
        refresh_btn = QPushButton("🔄 Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_statistics)
        layout.addWidget(refresh_btn)
        
        # Statistics Display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        # Initial Load
        self.refresh_statistics()
        
        return tab
    
    def populate_available_features(self):
        """Füllt Available Features Tree"""
        self.available_features_tree.clear()
        
        # Gruppe nach Kategorien
        categories = {}
        for feature in self.template_manager.features.values():
            cat_name = feature.category.value
            if cat_name not in categories:
                categories[cat_name] = QTreeWidgetItem([cat_name])
                self.available_features_tree.addTopLevelItem(categories[cat_name])
            
            feature_item = QTreeWidgetItem([
                feature.name,
                cat_name,
                feature.risk_level.value
            ])
            feature_item.setData(0, Qt.UserRole, feature.id)
            categories[cat_name].addChild(feature_item)
        
        self.available_features_tree.expandAll()
    
    def filter_templates(self):
        """Filtert Template-Liste"""
        self.template_list.clear()
        
        category_filter = self.category_filter.currentText()
        min_popularity = self.popularity_filter.value()
        
        for template in self.template_manager.templates.values():
            # Category Filter
            if category_filter != "All" and template.category != category_filter:
                continue
            
            # Popularity Filter
            if template.popularity < min_popularity:
                continue
            
            item = QListWidgetItem(f"{template.name} ({template.popularity}★)")
            item.setData(Qt.UserRole, template.id)
            
            # Color coding by risk
            if "Hohes Risiko" in template.risk_assessment or "RISIKO" in template.risk_assessment:
                item.setBackground(QColor(255, 200, 200))
            elif "Mittleres Risiko" in template.risk_assessment:
                item.setBackground(QColor(255, 255, 200))
            else:
                item.setBackground(QColor(200, 255, 200))
            
            self.template_list.addItem(item)
    
    def on_template_selected(self, current, previous):
        """Behandelt Template-Auswahl"""
        if not current:
            return
        
        template_id = current.data(Qt.UserRole)
        if template_id in self.template_manager.templates:
            self.selected_template = self.template_manager.templates[template_id]
            self.display_template_details()
            self.activate_btn.setEnabled(True)
    
    def display_template_details(self):
        """Zeigt Template-Details an"""
        if not self.selected_template:
            return
        
        # Template Info
        info_text = f"""
<h2>{self.selected_template.name}</h2>
<p><b>Description:</b> {self.selected_template.description}</p>
<p><b>Category:</b> {self.selected_template.category}</p>
<p><b>Target Audience:</b> {self.selected_template.target_audience}</p>
<p><b>Estimated Time:</b> {self.selected_template.estimated_time} seconds</p>
<p><b>Risk Assessment:</b> <span style="color: {'red' if 'Hoh' in self.selected_template.risk_assessment else 'orange' if 'Mittel' in self.selected_template.risk_assessment else 'green'};">{self.selected_template.risk_assessment}</span></p>
<p><b>Popularity:</b> {self.selected_template.popularity}/100</p>
"""
        
        if self.selected_template.prerequisites:
            info_text += f"<p><b>Prerequisites:</b><br>{'<br>'.join(self.selected_template.prerequisites)}</p>"
        
        if self.selected_template.post_activation_notes:
            info_text += f"<p><b>Post-Activation Notes:</b><br>{'<br>'.join(self.selected_template.post_activation_notes)}</p>"
        
        self.template_info.setHtml(info_text)
        
        # Feature Tree
        self.feature_tree.clear()
        for feature_id in self.selected_template.features:
            if feature_id in self.template_manager.features:
                feature = self.template_manager.features[feature_id]
                item = QTreeWidgetItem([
                    feature.name,
                    feature.risk_level.value,
                    feature.ecu_target,
                    f"{feature.activation_time_estimate}s"
                ])
                
                # Color coding
                if feature.risk_level == RiskLevel.HIGH or feature.risk_level == RiskLevel.CRITICAL:
                    item.setBackground(0, QColor(255, 200, 200))
                elif feature.risk_level == RiskLevel.MEDIUM:
                    item.setBackground(0, QColor(255, 255, 200))
                
                self.feature_tree.addTopLevelItem(item)
        
        self.feature_tree.resizeColumnToContents(0)
    
    def add_selected_features(self):
        """Fügt ausgewählte Features hinzu"""
        selected_items = self.available_features_tree.selectedItems()
        
        for item in selected_items:
            if item.parent():  # Nur Feature-Items, nicht Kategorien
                feature_id = item.data(0, Qt.UserRole)
                if feature_id and feature_id not in self.custom_feature_selection:
                    self.custom_feature_selection.add(feature_id)
                    
                    feature = self.template_manager.features[feature_id]
                    list_item = QListWidgetItem(f"{feature.name} ({feature.risk_level.value})")
                    list_item.setData(Qt.UserRole, feature_id)
                    self.selected_features_list.addItem(list_item)
    
    def remove_selected_features(self):
        """Entfernt ausgewählte Features"""
        selected_items = self.selected_features_list.selectedItems()
        
        for item in selected_items:
            feature_id = item.data(Qt.UserRole)
            if feature_id in self.custom_feature_selection:
                self.custom_feature_selection.remove(feature_id)
            
            row = self.selected_features_list.row(item)
            self.selected_features_list.takeItem(row)
    
    def create_custom_template(self):
        """Erstellt benutzerdefiniertes Template"""
        name = self.custom_name_input.text().strip()
        description = self.custom_desc_input.text().strip()
        
        if not name or not description or not self.custom_feature_selection:
            QMessageBox.warning(self, "Incomplete", "Please fill all fields and select features")
            return
        
        try:
            template = self.template_manager.create_custom_template(
                name=name,
                description=description,
                feature_ids=list(self.custom_feature_selection)
            )
            
            QMessageBox.information(self, "Success", f"Custom template '{name}' created successfully!")
            
            # Clear inputs
            self.custom_name_input.clear()
            self.custom_desc_input.clear()
            self.selected_features_list.clear()
            self.custom_feature_selection.clear()
            
            # Refresh template list
            self.filter_templates()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create template: {str(e)}")
    
    def validate_current_template(self):
        """Validiert aktuelles Template"""
        if not self.selected_template:
            QMessageBox.warning(self, "No Template", "Please select a template first")
            return
        
        valid, issues = self.template_manager.validate_template(self.selected_template)
        
        if valid:
            QMessageBox.information(self, "Validation Successful", "Template is valid and ready for activation!")
            self.status_label.setText("✅ Template validated - Ready for activation")
        else:
            issue_text = "\n".join(f"• {issue}" for issue in issues)
            QMessageBox.warning(self, "Validation Failed", f"Template validation failed:\n\n{issue_text}")
            self.status_label.setText("❌ Template validation failed")
    
    def activate_current_template(self):
        """Aktiviert aktuelles Template"""
        if not self.selected_template:
            return
        
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Activation",
            f"Are you sure you want to activate template '{self.selected_template.name}'?\n\n"
            f"This will activate {len(self.selected_template.features)} features.\n"
            f"Estimated time: {self.selected_template.estimated_time} seconds\n"
            f"Risk level: {self.selected_template.risk_assessment}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_template_activation()
    
    def start_template_activation(self):
        """Startet Template-Aktivierung"""
        print(f"[TEMPLATES] Aktiviere Template: {self.selected_template.name}")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.activate_btn.setEnabled(False)
        
        # Simulation der Aktivierung
        total_features = len(self.selected_template.features)
        
        for i, feature_id in enumerate(self.selected_template.features):
            if feature_id in self.template_manager.features:
                feature = self.template_manager.features[feature_id]
                
                progress = int((i + 1) / total_features * 100)
                self.progress_bar.setValue(progress)
                self.status_label.setText(f"Aktiviere: {feature.name}...")
                
                # Hier würde die tatsächliche Feature-Aktivierung stattfinden
                print(f"[TEMPLATES] Aktiviere Feature: {feature.name} auf {feature.ecu_target}")
                
                # Simulation delay
                QTimer.singleShot(100, lambda: None)  # Non-blocking delay simulation
        
        # Completion
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✅ Template '{self.selected_template.name}' erfolgreich aktiviert!")
        
        QMessageBox.information(
            self, 
            "Activation Complete", 
            f"Template '{self.selected_template.name}' has been successfully activated!\n\n"
            f"{len(self.selected_template.features)} features were configured."
        )
        
        self.activate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def create_backup(self):
        """Erstellt Backup vor Aktivierung"""
        QMessageBox.information(self, "Backup", "Backup creation would be triggered here")
    
    def refresh_statistics(self):
        """Aktualisiert Statistiken"""
        stats = self.template_manager.get_template_statistics()
        
        stats_html = f"""
<h2>Feature Template Statistics</h2>

<h3>Overview</h3>
<ul>
<li><b>Total Features:</b> {stats['total_features']}</li>
<li><b>Total Templates:</b> {stats['total_templates']}</li>
<li><b>Most Popular Template:</b> {stats['most_popular_template'] or 'N/A'}</li>
<li><b>Average Template Time:</b> {stats['average_template_time']:.0f} seconds</li>
</ul>

<h3>Features by Category</h3>
<ul>
"""
        
        for category, count in stats['features_by_category'].items():
            stats_html += f"<li><b>{category}:</b> {count}</li>"
        
        stats_html += """
</ul>

<h3>Templates by Category</h3>
<ul>
"""
        
        for category, count in stats['templates_by_category'].items():
            stats_html += f"<li><b>{category}:</b> {count}</li>"
        
        stats_html += """
</ul>

<h3>Risk Distribution</h3>
<ul>
"""
        
        for risk, count in stats['risk_distribution'].items():
            color = "green" if "Low" in risk else "orange" if "Medium" in risk else "red"
            stats_html += f'<li><span style="color: {color};"><b>{risk}:</b></span> {count}</li>'
        
        stats_html += "</ul>"
        
        self.stats_text.setHtml(stats_html)


# Integration Helper
def integrate_feature_template_system(main_window, enhanced_system=None):
    """Integriert Feature Template System in Hauptanwendung"""
    
    # Template Manager erstellen
    template_manager = FeatureTemplateManager()
    
    # Widget erstellen
    template_widget = FeatureTemplateSystemWidget(template_manager)
    
    # In MainWindow integrieren
    main_window.feature_template_manager = template_manager
    main_window.template_widget = template_widget
    
    # Integration mit Enhanced System
    if enhanced_system and hasattr(enhanced_system, 'backup_manager'):
        # Template-Aktivierung mit automatischem Backup
        def activate_template_with_backup(template):
            backup_id = enhanced_system.backup_manager.create_snapshot(
                name=f"Pre_Template_{template.name}",
                description=f"Backup vor Template-Aktivierung: {template.name}",
                backup_type="template_activation"
            )
            print(f"[TEMPLATES] Backup erstellt vor Template-Aktivierung: {backup_id}")
    
    print("[TEMPLATES] Feature Template System integriert")
    
    return template_manager, template_widget