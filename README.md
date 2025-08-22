# 🚗 PyPSADiag Enhanced - Advanced Fork of PyPSADiag

## 📋 Overview

PyPSADiag Enhanced is an **advanced fork** of the original [PyPSADiag](https://github.com/Barracuda09/PyPSADiag) project by Barracuda09. This enhanced version extends the base functionality with professional VCI support, advanced UI features, enhanced logging systems, and comprehensive feature activation capabilities for PSA/Stellantis vehicles (Peugeot, Citroën, DS, Opel, Vauxhall).

### 🙏 **Credits to Original Project**
- **Original PyPSADiag**: Created by [Barracuda09](https://github.com/Barracuda09/PyPSADiag)
- **Base Functionality**: JSON ECU configuration, diagnostic communication, multi-language support
- **Educational Foundation**: Core diagnostic protocols and safety-first approach

## ✨ Enhanced Features (vs Original PyPSADiag)

### 🔧 **Core Diagnostic Functions** *(from original)*
- **Multi-Protocol Support**: UDS, KWP2000, KWP-HAB, KWP-IS
- **ECU Detection & Communication**: JSON-based ECU configuration
- **Zone Reading/Writing**: Complete ECU configuration management
- **Multi-Language Support**: English, German, Dutch, Polish, Italian, Ukrainian
- **Educational Safety**: Comprehensive warnings and safety-first approach

### 🚀 **NEW Enhanced Features** *(PyPSADiag Enhanced additions)*
- **Evolution XS VCI Support**: Professional PSA VCI with 32-bit bridge integration
- **Shared VCI Bridge System**: Multiple applications can share VCI connection
- **Advanced UI with Grouped Tabs**: Professional interface organization
- **Real-Time Data Visualization**: Live graphing and monitoring systems
- **Professional Logging System**: Multi-level logging with performance metrics
- **Intelligent Feature Activation**: Safe activation matrix with hardware validation
- **Automatic Backup System**: Enhanced backup before all modifications
- **Advanced ECU Auto-Discovery**: Intelligent ECU detection and configuration
- **Performance Optimization**: Memory management and response time improvements
- **Enhanced Error Recovery**: Smart error handling and recovery procedures

### 🏢 **Hardware Support**
- **Evolution XS VCI**: Professional PSA diagnostic interface
- **Arduino-based Adapters**: Serial communication interfaces
- **Shared VCI Access**: Multiple applications can use same VCI
- **32-bit VCI Bridge**: Handles 32-bit VCI DLLs from 64-bit Python

### 🌍 **Internationalization**
- **Multi-Language Support**: English, German, Dutch, Polish, Italian, Ukrainian
- **Qt Translation System**: Professional localization framework

## 🚀 **Quick Start**

### Prerequisites
- Python 3.12 or higher
- Windows/Linux/macOS (Windows recommended for VCI support)
- VCI hardware or compatible OBD interface

### Installation
```bash
# Clone repository (replace [YOUR-USERNAME] with actual GitHub username)
git clone https://github.com/[YOUR-USERNAME]/PyPSADiag-Enhanced.git
cd PyPSADiag-Enhanced

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Quick Commands
```bash
# Run with specific language
python main.py --lang nl

# Run in simulation mode (no hardware needed)
python main.py --simu

# Run with scan mode
python main.py --scan

# Test seed/key calculations
python main.py --checkcalc
```

## 🏗️ **Project Structure**

### **Core Components**
- `main.py` - Application entry point
- `PyPSADiagGUI.py` - Main GUI interface (PySide6)
- `DiagnosticCommunication.py` - Protocol handlers (UDS, KWP)
- `SerialController.py` / `SerialPort.py` - Hardware communication
- `SeedKeyAlgorithm.py` - ECU security algorithms

### **Enhanced Features**
- `SimpleEnhancedMainWindow.py` - Enhanced UI with grouped tabs
- `SharedVCIBridge.py` - VCI sharing system
- `ProfessionalLoggingSystem.py` - Advanced logging
- `FeatureActivationMatrix.py` - Safe feature activation
- `RealTimeGraphManager.py` - Live data visualization

### **ECU Configurations**
- `json/` - ECU configuration files for different vehicle models
- `data/` - Common diagnostic data and parameters
- `simu/` - Simulation data for testing without hardware

## 🛡️ **Safety & Legal**

### ⚠️ **Important Disclaimers**
- **Educational Purpose Only**: This tool is for learning and research
- **Use at Your Own Risk**: Always backup ECU data before modifications
- **No Warranty**: Authors provide no warranty for functionality or safety
- **Vehicle Safety**: Improper use can affect vehicle safety systems

### 🔒 **Safety Features**
- **Automatic Backups**: All ECU data backed up before changes
- **Hardware Validation**: Checks for required hardware before activation
- **Safe Activation Modes**: Prevents dangerous modifications
- **Recovery Procedures**: Instructions for restoring original configurations

## 🤝 **Contributing**

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Areas for Contribution
- **New Vehicle Support**: Add ECU configurations for more models
- **Protocol Implementation**: Extend diagnostic protocol support
- **UI Improvements**: Enhance user interface and experience
- **Documentation**: Improve guides and technical documentation
- **Testing**: Add test cases and validation

## 📄 **License**

This project is licensed under the **GNU General Public License v2.0** - see the [LICENSE.txt](LICENSE.txt) file for details.

**Key Points:**
- ✅ **Free for personal and commercial use**
- ✅ **Source code must remain open**
- ✅ **Derivative works must use GPL-2.0**
- ✅ **Educational and research friendly**
- ⚠️ **Same license as original PyPSADiag**

## 🌟 **Acknowledgments**

### 🙏 **Thanks To**
- **[Barracuda09](https://github.com/Barracuda09)** for creating the original PyPSADiag foundation
- **PSA/Stellantis Community** for reverse engineering efforts
- **OleoDisag Project** for diagnostic protocol insights
- **Evolution XS VCI** developers for hardware documentation
- **Contributors** who helped improve this enhanced version

### 🔗 **Related Projects**
- **[Original PyPSADiag](https://github.com/Barracuda09/PyPSADiag)** - Base project by Barracuda09
- [PSA-RE](https://github.com/psa-re) - PSA Reverse Engineering Community
- [OleoDisag](https://github.com/zenmatic/oleodiag) - Original diagnostic tool inspiration

## 🆘 **Support**

### 📞 **Getting Help**
- **GitHub Issues**: Report bugs and request features
- **Community Forums**: Join PSA diagnostic communities
- **Documentation**: Read the comprehensive guides included

### 🐛 **Reporting Issues**
When reporting issues, please include:
- Vehicle model and year
- Hardware used (VCI type)
- Error messages or unexpected behavior
- Steps to reproduce the issue

---

## ⭐ **Star this project if you find it useful!**

**Made with ❤️ for the automotive diagnostic community**

### 📊 **Project Stats**
![GitHub stars](https://img.shields.io/github/stars/[USERNAME]/PyPSADiag-Enhanced)
![GitHub forks](https://img.shields.io/github/forks/[USERNAME]/PyPSADiag-Enhanced)
![GitHub issues](https://img.shields.io/github/issues/[USERNAME]/PyPSADiag-Enhanced)
![License](https://img.shields.io/github/license/[USERNAME]/PyPSADiag-Enhanced)
