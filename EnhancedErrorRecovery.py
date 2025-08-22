#!/usr/bin/env python3
"""
Enhanced Error Recovery System für PyPSADiag
Automatisches Recovery bei Fehlern mit intelligenten Retry-Mechanismen
"""

import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

try:
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar
    QT_FRAMEWORK = "PySide6"
except ImportError:
    try:
        from qt_compat import *
        QT_FRAMEWORK = "qt_compat" 
    except ImportError:
        from PyQt5.QtCore import QThread, pyqtSignal as Signal, QTimer, Qt
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar
        QT_FRAMEWORK = "PyQt5"

class RecoveryStrategy(Enum):
    """Recovery-Strategien für verschiedene Fehlertypen"""
    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RECONNECT_AND_RETRY = "reconnect_and_retry"
    ROLLBACK_AND_RETRY = "rollback_and_retry"
    MANUAL_INTERVENTION = "manual_intervention"
    FAIL_SAFE = "fail_safe"

@dataclass
class RecoveryRule:
    """Regel für automatisches Error Recovery"""
    error_pattern: str  # Regex pattern für Fehler-Erkennung
    strategy: RecoveryStrategy
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    timeout_seconds: float = 30.0
    rollback_function: Optional[Callable] = None
    custom_recovery: Optional[Callable] = None

@dataclass 
class RecoveryAttempt:
    """Ein Recovery-Versuch"""
    timestamp: datetime
    error_message: str
    strategy: RecoveryStrategy
    attempt_number: int
    success: bool = False
    recovery_time: float = 0.0
    additional_info: Dict = field(default_factory=dict)

class EnhancedErrorRecovery:
    """Hauptklasse für intelligentes Error Recovery"""
    
    def __init__(self, serial_controller=None, backup_manager=None):
        self.serial_controller = serial_controller
        self.backup_manager = backup_manager
        
        self.recovery_rules: List[RecoveryRule] = []
        self.recovery_history: List[RecoveryAttempt] = []
        self.active_recoveries: Dict[str, int] = {}  # operation_id -> attempt_count
        self.lock = Lock()
        
        self.setup_default_rules()
        
    def setup_default_rules(self):
        """Erstellt Standard-Recovery-Regeln"""
        
        # VCI Connection Errors
        self.add_recovery_rule(
            error_pattern=r"VCI.*connection.*lost|VCI.*timeout",
            strategy=RecoveryStrategy.RECONNECT_AND_RETRY,
            max_attempts=3,
            backoff_seconds=2.0
        )
        
        # Serial Communication Errors
        self.add_recovery_rule(
            error_pattern=r"Serial.*error|Port.*not.*open|Communication.*timeout",
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            max_attempts=5,
            backoff_seconds=1.0,
            backoff_multiplier=1.5
        )
        
        # ECU Response Errors
        self.add_recovery_rule(
            error_pattern=r"ECU.*no.*response|ECU.*timeout|Negative.*response",
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            max_attempts=3,
            backoff_seconds=0.5
        )
        
        # Write Operation Errors (Critical!)
        self.add_recovery_rule(
            error_pattern=r"Write.*failed|Zone.*write.*error",
            strategy=RecoveryStrategy.ROLLBACK_AND_RETRY,
            max_attempts=2,
            rollback_function=self.rollback_to_backup
        )
        
        # Memory/Resource Errors
        self.add_recovery_rule(
            error_pattern=r"Memory.*error|Resource.*unavailable|Out.*of.*memory",
            strategy=RecoveryStrategy.FAIL_SAFE,
            max_attempts=1
        )
        
        print("[RECOVERY] Standard Recovery-Regeln geladen")
    
    def add_recovery_rule(self, error_pattern: str, strategy: RecoveryStrategy, **kwargs):
        """Fügt neue Recovery-Regel hinzu"""
        rule = RecoveryRule(error_pattern=error_pattern, strategy=strategy, **kwargs)
        self.recovery_rules.append(rule)
        print(f"[RECOVERY] Regel hinzugefügt: {error_pattern} -> {strategy.value}")
    
    def handle_error(self, error: Exception, operation_id: str = None, context: Dict = None) -> bool:
        """Hauptfunktion für Error Handling mit automatischem Recovery"""
        
        error_message = str(error)
        operation_id = operation_id or f"operation_{int(time.time())}"
        context = context or {}
        
        print(f"[RECOVERY] Handling error in {operation_id}: {error_message}")
        
        # Finde passende Recovery-Regel
        matching_rule = self.find_matching_rule(error_message)
        if not matching_rule:
            print(f"[RECOVERY] Keine Recovery-Regel für Fehler gefunden: {error_message}")
            return False
        
        # Prüfe aktuelle Versuche für diese Operation
        with self.lock:
            current_attempts = self.active_recoveries.get(operation_id, 0)
            if current_attempts >= matching_rule.max_attempts:
                print(f"[RECOVERY] Max attempts ({matching_rule.max_attempts}) erreicht für {operation_id}")
                return False
            
            self.active_recoveries[operation_id] = current_attempts + 1
        
        # Führe Recovery aus
        success = self.execute_recovery(
            error_message, 
            matching_rule, 
            operation_id, 
            current_attempts + 1,
            context
        )
        
        # Cleanup bei Erfolg
        if success:
            with self.lock:
                if operation_id in self.active_recoveries:
                    del self.active_recoveries[operation_id]
        
        return success
    
    def find_matching_rule(self, error_message: str) -> Optional[RecoveryRule]:
        """Findet passende Recovery-Regel für Fehler"""
        import re
        
        for rule in self.recovery_rules:
            if re.search(rule.error_pattern, error_message, re.IGNORECASE):
                return rule
        
        return None
    
    def execute_recovery(self, error_message: str, rule: RecoveryRule, 
                        operation_id: str, attempt_number: int, context: Dict) -> bool:
        """Führt Recovery-Strategie aus"""
        
        start_time = time.time()
        recovery_attempt = RecoveryAttempt(
            timestamp=datetime.now(),
            error_message=error_message,
            strategy=rule.strategy,
            attempt_number=attempt_number
        )
        
        try:
            print(f"[RECOVERY] Starte {rule.strategy.value} (Versuch {attempt_number}/{rule.max_attempts})")
            
            if rule.strategy == RecoveryStrategy.RETRY_IMMEDIATE:
                success = self.retry_immediate(context)
                
            elif rule.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                success = self.retry_with_backoff(rule, attempt_number, context)
                
            elif rule.strategy == RecoveryStrategy.RECONNECT_AND_RETRY:
                success = self.reconnect_and_retry(context)
                
            elif rule.strategy == RecoveryStrategy.ROLLBACK_AND_RETRY:
                success = self.rollback_and_retry(rule, context)
                
            elif rule.strategy == RecoveryStrategy.MANUAL_INTERVENTION:
                success = self.request_manual_intervention(error_message, context)
                
            elif rule.strategy == RecoveryStrategy.FAIL_SAFE:
                success = self.fail_safe_shutdown(error_message, context)
                
            else:
                print(f"[RECOVERY] Unbekannte Strategie: {rule.strategy}")
                success = False
                
            recovery_attempt.success = success
            recovery_attempt.recovery_time = time.time() - start_time
            
            if success:
                print(f"[RECOVERY] ✅ Recovery erfolgreich nach {recovery_attempt.recovery_time:.2f}s")
            else:
                print(f"[RECOVERY] ❌ Recovery fehlgeschlagen nach {recovery_attempt.recovery_time:.2f}s")
            
        except Exception as e:
            recovery_attempt.success = False
            recovery_attempt.recovery_time = time.time() - start_time
            recovery_attempt.additional_info["recovery_error"] = str(e)
            print(f"[RECOVERY] Exception während Recovery: {e}")
            success = False
        
        # Recovery-Versuch protokollieren
        self.recovery_history.append(recovery_attempt)
        
        return success
    
    def retry_immediate(self, context: Dict) -> bool:
        """Sofortiger Retry ohne Wartezeit"""
        if "retry_function" in context:
            return context["retry_function"]()
        return False
    
    def retry_with_backoff(self, rule: RecoveryRule, attempt_number: int, context: Dict) -> bool:
        """Retry mit exponential backoff"""
        
        # Backoff berechnen
        backoff_time = rule.backoff_seconds * (rule.backoff_multiplier ** (attempt_number - 1))
        print(f"[RECOVERY] Warte {backoff_time:.1f}s vor Retry...")
        time.sleep(backoff_time)
        
        if "retry_function" in context:
            return context["retry_function"]()
        return False
    
    def reconnect_and_retry(self, context: Dict) -> bool:
        """Verbindung neu aufbauen und retry"""
        
        try:
            # Verbindung trennen
            if self.serial_controller and self.serial_controller.isOpen():
                self.serial_controller.close()
                print("[RECOVERY] Verbindung getrennt")
            
            # Kurz warten
            time.sleep(2.0)
            
            # Neu verbinden
            if self.serial_controller and "port_name" in context:
                success = self.serial_controller.open(context["port_name"], 115200)
                if success:
                    print("[RECOVERY] Verbindung wiederhergestellt")
                    
                    # VCI re-konfigurieren falls notwendig
                    if hasattr(self.serial_controller, 'use_vci') and self.serial_controller.use_vci:
                        if "ecu_config" in context:
                            self.serial_controller.configure_vci(**context["ecu_config"])
                    
                    # Original-Operation retry
                    if "retry_function" in context:
                        return context["retry_function"]()
                    return True
                else:
                    print("[RECOVERY] Reconnect fehlgeschlagen")
                    return False
            
        except Exception as e:
            print(f"[RECOVERY] Reconnect-Fehler: {e}")
            return False
        
        return False
    
    def rollback_and_retry(self, rule: RecoveryRule, context: Dict) -> bool:
        """Rollback zu letztem Backup und retry"""
        
        try:
            # Custom Rollback-Funktion
            if rule.rollback_function:
                success = rule.rollback_function(context)
                if not success:
                    print("[RECOVERY] Rollback fehlgeschlagen")
                    return False
            
            # Standard Backup-Rollback
            elif self.backup_manager and "backup_id" in context:
                success = self.backup_manager.restore_snapshot(context["backup_id"])
                if not success:
                    print("[RECOVERY] Backup-Restore fehlgeschlagen")
                    return False
                print("[RECOVERY] Backup erfolgreich wiederhergestellt")
            
            # Nach Rollback retry
            if "retry_function" in context:
                return context["retry_function"]()
            
            return True
            
        except Exception as e:
            print(f"[RECOVERY] Rollback-Fehler: {e}")
            return False
    
    def rollback_to_backup(self, context: Dict) -> bool:
        """Standard Backup-Rollback Funktion"""
        if self.backup_manager and "backup_id" in context:
            return self.backup_manager.restore_snapshot(context["backup_id"])
        return False
    
    def request_manual_intervention(self, error_message: str, context: Dict) -> bool:
        """Fordert manuelle Intervention an"""
        print(f"[RECOVERY] ⚠️ MANUELLE INTERVENTION ERFORDERLICH: {error_message}")
        # Hier könnte ein Dialog oder Notification angezeigt werden
        return False
    
    def fail_safe_shutdown(self, error_message: str, context: Dict) -> bool:
        """Fail-Safe Shutdown bei kritischen Fehlern"""
        print(f"[RECOVERY] 🔥 FAIL-SAFE SHUTDOWN: {error_message}")
        
        try:
            # Verbindungen sicher schließen
            if self.serial_controller and self.serial_controller.isOpen():
                self.serial_controller.close()
                
            # Notfall-Backup erstellen falls möglich
            if self.backup_manager:
                self.backup_manager.create_emergency_backup(f"Failsafe_{int(time.time())}")
            
            print("[RECOVERY] Fail-Safe Shutdown abgeschlossen")
            return True
            
        except Exception as e:
            print(f"[RECOVERY] Fehler während Fail-Safe Shutdown: {e}")
            return False
    
    def get_recovery_stats(self) -> Dict:
        """Gibt Recovery-Statistiken zurück"""
        total_attempts = len(self.recovery_history)
        successful_attempts = sum(1 for attempt in self.recovery_history if attempt.success)
        
        strategy_stats = {}
        for attempt in self.recovery_history:
            strategy = attempt.strategy.value
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "successful": 0}
            strategy_stats[strategy]["total"] += 1
            if attempt.success:
                strategy_stats[strategy]["successful"] += 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "strategy_stats": strategy_stats,
            "active_recoveries": len(self.active_recoveries)
        }


# Integration Helper
def integrate_error_recovery(main_window, serial_controller, backup_manager=None):
    """Integriert Enhanced Error Recovery in Hauptanwendung"""
    
    # Recovery System erstellen
    recovery_system = EnhancedErrorRecovery(serial_controller, backup_manager)
    
    # In MainWindow integrieren
    main_window.error_recovery = recovery_system
    
    # Original Error Handler erweitern
    def enhanced_error_handler(error, operation_id=None, context=None):
        # Erst Recovery versuchen
        recovered = recovery_system.handle_error(error, operation_id, context)
        
        if not recovered:
            # Fallback zu original error handling
            print(f"[RECOVERY] Fallback zu Standard-Fehlerbehandlung: {error}")
        
        return recovered
    
    main_window.handle_error = enhanced_error_handler
    
    print("[RECOVERY] Enhanced Error Recovery System integriert")
    
    return recovery_system