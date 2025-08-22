#!/usr/bin/env python3
"""
qt_compat.py

Qt Framework Compatibility Layer
Unterstützt sowohl PySide6 als auch PyQt5 automatisch
"""

import sys
import types

# Try PySide6 first, fallback to PyQt5
QT_FRAMEWORK = None

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    QT_FRAMEWORK = "PySide6"
    print(f"[OK] Using Qt Framework: {QT_FRAMEWORK}")
    
    # Store original modules for import hook
    _pyside6_widgets = sys.modules.get('PySide6.QtWidgets')
    _pyside6_core = sys.modules.get('PySide6.QtCore')
    _pyside6_gui = sys.modules.get('PySide6.QtGui')
    
except ImportError:
    try:
        from PyQt5.QtWidgets import *
        from PyQt5.QtCore import *
        from PyQt5.QtGui import *
        # Also ensure QThread is available globally
        from PyQt5.QtCore import QThread
        QT_FRAMEWORK = "PyQt5"
        print(f"[OK] Using Qt Framework: {QT_FRAMEWORK}")
        
        # Create PySide6 compatibility modules using PyQt5
        class PySide6Module:
            def __init__(self, pyqt5_module):
                self._pyqt5_module = pyqt5_module
                
            def __getattr__(self, name):
                # Handle Signal/Slot compatibility
                if name == 'Signal':
                    from PyQt5.QtCore import pyqtSignal
                    return pyqtSignal
                elif name == 'Slot':
                    from PyQt5.QtCore import pyqtSlot
                    return pyqtSlot
                return getattr(self._pyqt5_module, name)
        
        # Import PyQt5 modules
        import PyQt5.QtWidgets as qt5_widgets
        import PyQt5.QtCore as qt5_core 
        import PyQt5.QtGui as qt5_gui
        
        # Create PySide6 compatibility modules
        pyside6_widgets = PySide6Module(qt5_widgets)
        pyside6_core = PySide6Module(qt5_core)
        pyside6_gui = PySide6Module(qt5_gui)
        
        # Create PySide6 package structure
        pyside6_package = types.ModuleType('PySide6')
        pyside6_package.QtWidgets = pyside6_widgets
        pyside6_package.QtCore = pyside6_core
        pyside6_package.QtGui = pyside6_gui
        
        # Inject into sys.modules for import compatibility
        sys.modules['PySide6'] = pyside6_package
        sys.modules['PySide6.QtWidgets'] = pyside6_widgets
        sys.modules['PySide6.QtCore'] = pyside6_core
        sys.modules['PySide6.QtGui'] = pyside6_gui
        
    except ImportError:
        raise ImportError("Neither PySide6 nor PyQt5 is available. Please install one of them.")

# Compatibility adjustments for PyQt5 vs PySide6
if QT_FRAMEWORK == "PyQt5":
    # PyQt5 uses different signal names in some cases
    # Also handle QRegExp vs QRegularExpression differences
    try:
        from PyQt5.QtCore import QRegExp
        from PyQt5.QtGui import QRegExpValidator
    except ImportError:
        # Fallback if QRegExpValidator is not available
        QRegExpValidator = None
    
    # In PyQt5, QAction is in QtWidgets, not QtGui
    try:
        from PyQt5.QtWidgets import QAction
    except ImportError:
        try:
            from PyQt5.QtGui import QAction
        except ImportError:
            QAction = None
            
elif QT_FRAMEWORK == "PySide6":
    # PySide6 is the preferred framework
    try:
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator as QRegExpValidator
    except ImportError:
        QRegExpValidator = None
    
    try:
        from PySide6.QtGui import QAction
    except ImportError:
        try:
            from PySide6.QtWidgets import QAction
        except ImportError:
            QAction = None

# Ensure all commonly used Qt classes are available in the global namespace
# This is needed because 'from X import *' doesn't always work as expected with __all__

# Core classes that should always be available
globals().update({
    'QT_FRAMEWORK': QT_FRAMEWORK,
})

# Make QRegExpValidator available if it was imported
if 'QRegExpValidator' in locals():
    globals()['QRegExpValidator'] = QRegExpValidator

# Ensure Signal and Slot are available for both frameworks
if QT_FRAMEWORK == "PyQt5":
    from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, QThread
elif QT_FRAMEWORK == "PySide6":
    from PySide6.QtCore import Signal, Slot, QThread

# Make these available globally
globals().update({
    'Signal': Signal,
    'Slot': Slot, 
    'QThread': QThread
})

# Add QAction if available
if 'QAction' in locals() and QAction is not None:
    globals()['QAction'] = QAction