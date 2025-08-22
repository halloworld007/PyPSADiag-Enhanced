#!/usr/bin/env python3
"""
AutomaticBackupSystem.py

Automatic Backup System for PyPSADiag Enhanced
Automatically creates backups before critical operations
"""

import os
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
# Qt Framework Kompatibilität
try:
    from PySide6.QtCore import QObject, Signal, QTimer
    from PySide6.QtWidgets import QMessageBox
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat"
    except ImportError:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal, QTimer
        from PyQt5.QtWidgets import QMessageBox
        QT_FRAMEWORK = "PyQt5"


class AutomaticBackupSystem(QObject):
    """Automatic Backup System for critical operations"""
    
    backup_created = Signal(str, str)  # backup_path, description
    backup_failed = Signal(str, str)   # error_message, operation
    backup_restored = Signal(str)      # backup_path
    
    def __init__(self, backup_dir="backups"):
        super().__init__()
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup settings
        self.settings = {
            "auto_backup_enabled": True,
            "max_backups": 50,
            "backup_before_flash": True,
            "backup_before_coding": True,
            "backup_before_key_programming": True,
            "backup_before_settings_change": True,
            "compress_backups": True,
            "cleanup_old_backups": True,
            "cleanup_days": 30
        }
        
        self.settings_file = "backup_settings.json"
        self.load_settings()
        
        # Critical operations that trigger backups
        self.critical_operations = [
            "ecu_flash",
            "ecu_coding", 
            "key_programming",
            "immobilizer_sync",
            "feature_activation",
            "calibration_update",
            "software_update",
            "bsi_configuration"
        ]
        
        # Setup cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_backups)
        self.cleanup_timer.start(24 * 60 * 60 * 1000)  # Daily cleanup
        
        print("[INFO] Automatic Backup System initialized")
    
    def load_settings(self):
        """Lade Backup-Einstellungen"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print(f"[WARN] Backup settings load error: {e}")
    
    def save_settings(self):
        """Speichere Backup-Einstellungen"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Backup settings save error: {e}")
            return False
    
    def is_critical_operation(self, operation):
        """Prüfe ob Operation kritisch ist und Backup benötigt"""
        return operation.lower() in self.critical_operations
    
    def create_backup_before_operation(self, operation, ecu_info=None, additional_data=None):
        """Erstelle Backup vor kritischer Operation"""
        if not self.settings["auto_backup_enabled"]:
            print(f"[INFO] Auto-backup disabled, skipping backup for {operation}")
            return None
        
        if not self.is_critical_operation(operation):
            print(f"[INFO] Operation '{operation}' is not critical, no backup needed")
            return None
        
        try:
            # Check operation-specific settings
            if operation == "ecu_flash" and not self.settings["backup_before_flash"]:
                return None
            if operation == "ecu_coding" and not self.settings["backup_before_coding"]:
                return None
            if operation == "key_programming" and not self.settings["backup_before_key_programming"]:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create backup info
            backup_info = {
                "timestamp": timestamp,
                "operation": operation,
                "description": f"Automatic backup before {operation}",
                "ecu_info": ecu_info or {},
                "additional_data": additional_data or {},
                "backup_version": "2.0",
                "created_by": "AutomaticBackupSystem"
            }
            
            # Create backup filename
            safe_operation = operation.replace(" ", "_").replace("/", "_")
            if ecu_info and "name" in ecu_info:
                safe_ecu = ecu_info["name"].replace(" ", "_").replace("/", "_")
                backup_name = f"auto_backup_{safe_operation}_{safe_ecu}_{timestamp}"
            else:
                backup_name = f"auto_backup_{safe_operation}_{timestamp}"
            
            # Create backup
            backup_path = self.create_backup(backup_name, backup_info)
            
            if backup_path:
                print(f"[INFO] Automatic backup created: {backup_path}")
                self.backup_created.emit(str(backup_path), backup_info["description"])
                return backup_path
            else:
                print(f"[ERROR] Automatic backup failed for operation: {operation}")
                self.backup_failed.emit("Backup creation failed", operation)
                return None
                
        except Exception as e:
            print(f"[ERROR] Automatic backup error: {e}")
            self.backup_failed.emit(str(e), operation)
            return None
    
    def create_backup(self, backup_name, backup_info=None):
        """Erstelle Backup mit gegebenem Namen"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if not backup_info:
                backup_info = {
                    "timestamp": timestamp,
                    "description": f"Manual backup: {backup_name}",
                    "backup_version": "2.0",
                    "created_by": "AutomaticBackupSystem"
                }
            
            # Create backup directory
            backup_path = self.backup_dir / f"{backup_name}_{timestamp}"
            backup_path.mkdir(exist_ok=True)
            
            # Files to backup
            backup_files = [
                "vehicle_profiles.json",
                "theme_settings.json", 
                "backup_settings.json",
                "feature_activation_settings.json",
                "hardware_validation_cache.json"
            ]
            
            # Backup configuration files
            backed_up_files = []
            for filename in backup_files:
                if os.path.exists(filename):
                    try:
                        shutil.copy2(filename, backup_path / filename)
                        backed_up_files.append(filename)
                    except Exception as e:
                        print(f"[WARN] Could not backup {filename}: {e}")
            
            # Backup Python cache and important directories
            important_dirs = ["logs", "exports", "custom_themes"]
            for dirname in important_dirs:
                if os.path.exists(dirname) and os.path.isdir(dirname):
                    try:
                        shutil.copytree(dirname, backup_path / dirname, dirs_exist_ok=True)
                        backed_up_files.append(f"{dirname}/")
                    except Exception as e:
                        print(f"[WARN] Could not backup directory {dirname}: {e}")
            
            # Create backup manifest
            manifest = {
                **backup_info,
                "backed_up_files": backed_up_files,
                "backup_path": str(backup_path),
                "file_count": len(backed_up_files)
            }
            
            with open(backup_path / "backup_manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Compress backup if enabled
            if self.settings["compress_backups"]:
                zip_path = backup_path.with_suffix('.zip')
                self.compress_backup(backup_path, zip_path)
                
                # Remove uncompressed backup
                shutil.rmtree(backup_path)
                backup_path = zip_path
            
            print(f"[INFO] Backup created: {backup_path} ({len(backed_up_files)} files)")
            return backup_path
            
        except Exception as e:
            print(f"[ERROR] Backup creation failed: {e}")
            return None
    
    def compress_backup(self, source_dir, zip_path):
        """Komprimiere Backup zu ZIP"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
            
            print(f"[INFO] Backup compressed to: {zip_path}")
            
        except Exception as e:
            print(f"[ERROR] Backup compression failed: {e}")
    
    def list_backups(self):
        """Liste alle verfügbaren Backups"""
        try:
            backups = []
            
            # Find backup files and directories
            for item in self.backup_dir.iterdir():
                if item.is_dir() or item.suffix == '.zip':
                    backup_info = self.get_backup_info(item)
                    if backup_info:
                        backups.append({
                            "path": item,
                            "name": item.name,
                            "info": backup_info,
                            "size": self.get_backup_size(item),
                            "created": datetime.fromtimestamp(item.stat().st_ctime)
                        })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return backups
            
        except Exception as e:
            print(f"[ERROR] List backups failed: {e}")
            return []
    
    def get_backup_info(self, backup_path):
        """Hole Backup-Informationen"""
        try:
            manifest_path = None
            
            if backup_path.is_dir():
                manifest_path = backup_path / "backup_manifest.json"
            elif backup_path.suffix == '.zip':
                # Extract manifest from ZIP
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    if "backup_manifest.json" in zipf.namelist():
                        manifest_content = zipf.read("backup_manifest.json")
                        return json.loads(manifest_content.decode('utf-8'))
            
            if manifest_path and manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Fallback info from filename
            return {
                "timestamp": backup_path.name,
                "description": f"Backup: {backup_path.name}",
                "backup_version": "unknown"
            }
            
        except Exception as e:
            print(f"[WARN] Could not read backup info for {backup_path}: {e}")
            return None
    
    def get_backup_size(self, backup_path):
        """Hole Backup-Größe"""
        try:
            if backup_path.is_file():
                return backup_path.stat().st_size
            elif backup_path.is_dir():
                total_size = 0
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
                return total_size
            return 0
        except Exception:
            return 0
    
    def restore_backup(self, backup_path, confirm=True):
        """Stelle Backup wieder her"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                print(f"[ERROR] Backup not found: {backup_path}")
                return False
            
            # Get backup info
            backup_info = self.get_backup_info(backup_path)
            if not backup_info:
                print(f"[ERROR] Could not read backup info")
                return False
            
            # Confirmation dialog if needed
            if confirm:
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    None, "Restore Backup",
                    f"Restore backup from {backup_info.get('timestamp', 'unknown')}?\n\n"
                    f"Description: {backup_info.get('description', 'N/A')}\n\n"
                    f"This will overwrite current settings!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return False
            
            # Create safety backup of current state
            safety_backup = self.create_backup("restore_safety_backup")
            if safety_backup:
                print(f"[INFO] Safety backup created: {safety_backup}")
            
            # Extract and restore files
            if backup_path.suffix == '.zip':
                success = self.restore_from_zip(backup_path)
            else:
                success = self.restore_from_directory(backup_path)
            
            if success:
                print(f"[INFO] Backup restored successfully from: {backup_path}")
                self.backup_restored.emit(str(backup_path))
                return True
            else:
                print(f"[ERROR] Backup restore failed")
                return False
                
        except Exception as e:
            print(f"[ERROR] Backup restore error: {e}")
            return False
    
    def restore_from_zip(self, zip_path):
        """Stelle aus ZIP-Backup wieder her"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Extract files to current directory
                for member in zipf.namelist():
                    if not member.endswith('/'):  # Skip directories
                        zipf.extract(member, '.')
            
            return True
            
        except Exception as e:
            print(f"[ERROR] ZIP restore failed: {e}")
            return False
    
    def restore_from_directory(self, backup_dir):
        """Stelle aus Verzeichnis-Backup wieder her"""
        try:
            for item in backup_dir.iterdir():
                if item.name == "backup_manifest.json":
                    continue
                
                if item.is_file():
                    shutil.copy2(item, item.name)
                elif item.is_dir():
                    if os.path.exists(item.name):
                        shutil.rmtree(item.name)
                    shutil.copytree(item, item.name)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Directory restore failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Räume alte Backups auf"""
        if not self.settings["cleanup_old_backups"]:
            return
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.settings["cleanup_days"])
            removed_count = 0
            
            for item in self.backup_dir.iterdir():
                if item.stat().st_ctime < cutoff_date.timestamp():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                print(f"[INFO] Cleaned up {removed_count} old backups")
            
            # Also enforce max backup limit
            self.enforce_backup_limit()
            
        except Exception as e:
            print(f"[ERROR] Backup cleanup failed: {e}")
    
    def enforce_backup_limit(self):
        """Erzwinge maximale Anzahl von Backups"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.settings["max_backups"]:
                # Remove oldest backups
                excess_count = len(backups) - self.settings["max_backups"]
                for backup in backups[-excess_count:]:  # Oldest backups are at the end
                    backup_path = backup["path"]
                    if backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    else:
                        backup_path.unlink()
                
                print(f"[INFO] Removed {excess_count} excess backups (limit: {self.settings['max_backups']})")
            
        except Exception as e:
            print(f"[ERROR] Backup limit enforcement failed: {e}")
    
    def delete_backup(self, backup_path):
        """Lösche spezifisches Backup"""
        try:
            backup_path = Path(backup_path)
            
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            else:
                backup_path.unlink()
            
            print(f"[INFO] Backup deleted: {backup_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Backup deletion failed: {e}")
            return False
    
    def get_backup_statistics(self):
        """Hole Backup-Statistiken"""
        try:
            backups = self.list_backups()
            
            total_size = sum(backup["size"] for backup in backups)
            
            # Group by operation type
            operations = {}
            for backup in backups:
                operation = backup["info"].get("operation", "unknown")
                operations[operation] = operations.get(operation, 0) + 1
            
            return {
                "total_backups": len(backups),
                "total_size": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "operations": operations,
                "oldest_backup": backups[-1]["created"] if backups else None,
                "newest_backup": backups[0]["created"] if backups else None,
                "settings": self.settings.copy()
            }
            
        except Exception as e:
            print(f"[ERROR] Backup statistics failed: {e}")
            return {}


# Global backup system instance
_backup_system = None

def get_backup_system():
    """Hole globales Backup System"""
    global _backup_system
    if _backup_system is None:
        _backup_system = AutomaticBackupSystem()
    return _backup_system


if __name__ == "__main__":
    """Test Automatic Backup System"""
    backup_system = get_backup_system()
    
    print("=== Automatic Backup System Test ===")
    
    # Test backup creation
    print("\n1. Testing backup creation...")
    backup_path = backup_system.create_backup_before_operation(
        "ecu_coding",
        {"name": "BSI Body Control", "address": "0x240"},
        {"vehicle": "Peugeot 308", "year": "2020"}
    )
    
    if backup_path:
        print(f"   Backup created: {backup_path}")
    
    # Test backup listing
    print("\n2. Testing backup listing...")
    backups = backup_system.list_backups()
    print(f"   Found {len(backups)} backups")
    
    for backup in backups[:3]:  # Show first 3
        print(f"   - {backup['name']} ({backup['info'].get('description', 'N/A')})")
    
    # Test statistics
    print("\n3. Testing statistics...")
    stats = backup_system.get_backup_statistics()
    print(f"   Total backups: {stats['total_backups']}")
    print(f"   Total size: {stats['total_size_mb']} MB")
    print(f"   Operations: {stats['operations']}")
    
    print("\n=== Test completed ===")