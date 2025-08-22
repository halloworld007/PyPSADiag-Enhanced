# 🤝 Contributing to PyPSADiag Enhanced

Thank you for your interest in contributing to PyPSADiag Enhanced! This document provides guidelines for contributing to this open-source automotive diagnostic tool.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Reporting](#issue-reporting)
7. [Development Standards](#development-standards)

---

## 🤝 Code of Conduct

### Our Commitment

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- **Be respectful** in all interactions
- **Be constructive** when providing feedback
- **Be patient** with newcomers and questions
- **Focus on what's best** for the community and project

### Unacceptable Behavior

- Harassment, discrimination, or hostile behavior
- Inappropriate or offensive language
- Personal attacks or trolling
- Publishing others' private information without permission

---

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.12+** installed
- **Git** for version control
- **Basic understanding** of automotive diagnostics (helpful but not required)
- **PySide6 knowledge** for GUI contributions (optional)

### Areas for Contribution

We welcome contributions in these areas:

#### 🔧 **Code Contributions**
- **New Vehicle Support**: Add ECU configurations for additional models
- **Protocol Implementation**: Extend diagnostic protocol support
- **Bug Fixes**: Resolve existing issues and improve stability
- **Performance Improvements**: Optimize code for better performance
- **Feature Enhancements**: Improve existing functionality

#### 📚 **Documentation**
- **User Guides**: Improve installation and usage documentation
- **Technical Documentation**: Enhance developer documentation
- **Translation**: Help translate the application to new languages
- **Examples**: Provide more real-world usage examples

#### 🧪 **Testing**
- **Unit Tests**: Add test coverage for core functionality
- **Integration Tests**: Test hardware compatibility
- **Validation Scripts**: Verify ECU configurations
- **Simulation Data**: Provide test data for development

#### 🎨 **UI/UX Improvements**
- **Interface Design**: Enhance user interface elements
- **Accessibility**: Improve accessibility features
- **Themes**: Develop new visual themes
- **Workflow Optimization**: Streamline user workflows

---

## 💻 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR-USERNAME/PyPSADiag-Enhanced.git
cd PyPSADiag-Enhanced
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt
```

### 3. Run Tests

```bash
# Run the application in simulation mode
python main.py --simu

# Test seed/key calculations
python main.py --checkcalc

# Test different languages
python main.py --lang nl
```

### 4. Set Up Git Hooks (Optional)

```bash
# Set up pre-commit hooks for code quality
# (Add specific instructions based on your setup)
```

---

## 📝 Contributing Guidelines

### 🔄 Workflow Overview

1. **Create Issue** - Discuss your proposed changes
2. **Fork Repository** - Create your own copy
3. **Create Branch** - Use descriptive branch names
4. **Make Changes** - Follow coding standards
5. **Test Changes** - Ensure nothing breaks
6. **Submit PR** - Request review and merge

### 🌿 Branch Naming

Use clear, descriptive branch names:

```
feature/add-corsa-e-support
bugfix/fix-vci-connection-timeout
docs/improve-installation-guide
refactor/cleanup-diagnostic-protocols
translation/add-spanish-support
```

### 💡 Commit Messages

Follow conventional commit format:

```
feat: add support for Corsa-E ECU configurations
fix: resolve VCI connection timeout issues
docs: improve installation instructions for Windows
refactor: simplify diagnostic communication code
test: add unit tests for seed-key algorithms
```

### 📁 File Organization

When adding new files, follow the existing structure:

```
PyPSADiag-Enhanced/
├── json/                    # ECU configuration files
│   ├── BRAND/              # Organized by vehicle brand
│   └── MODEL/              # Model-specific configurations
├── i18n/                   # Translation files
├── simu/                   # Simulation data
├── docs/                   # Documentation files
└── tests/                  # Test files (if implemented)
```

---

## 🔍 Pull Request Process

### Before Submitting

1. **Update Documentation** - Ensure docs reflect your changes
2. **Test Thoroughly** - Test on multiple scenarios
3. **Check Code Style** - Follow existing conventions
4. **Update CHANGELOG** - Add entry for your changes (if applicable)

### PR Requirements

- **Clear Title** - Summarize the change in the title
- **Detailed Description** - Explain what and why
- **Testing Notes** - Describe how you tested the changes
- **Screenshots** - Include screenshots for UI changes
- **Breaking Changes** - Clearly mark any breaking changes

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Tested in simulation mode
- [ ] Tested with real hardware
- [ ] Added/updated tests
- [ ] Tested on different vehicle models

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

---

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

```markdown
**Vehicle Information:**
- Make/Model/Year: Opel Corsa F 2021
- Engine: 1.2T
- ECU Version: BSI 2010

**Hardware Setup:**
- VCI Type: Evolution XS
- Connection: USB/Bluetooth
- Operating System: Windows 11

**Bug Description:**
Clear description of the unexpected behavior

**Steps to Reproduce:**
1. Start PyPSADiag
2. Connect to BSI
3. Read Zone 2101
4. Error occurs

**Expected Behavior:**
What should happen instead

**Screenshots/Logs:**
Attach relevant screenshots or log files
```

### Feature Requests

For new features, please include:

```markdown
**Feature Description:**
Clear description of the proposed feature

**Use Case:**
Why would this feature be useful?

**Implementation Ideas:**
Any thoughts on how it could be implemented

**Alternative Solutions:**
Other ways to achieve the same goal
```

---

## 🔧 Development Standards

### Code Style

- **Follow PEP 8** for Python code formatting
- **Use type hints** where applicable
- **Write docstrings** for functions and classes
- **Keep functions focused** - single responsibility principle
- **Use meaningful variable names**

### Safety Guidelines

**CRITICAL**: This tool interacts with vehicle safety systems

- **Always validate input** before writing to ECUs
- **Implement safety checks** for critical operations
- **Provide clear warnings** for risky operations
- **Maintain backup functionality** for all write operations
- **Test thoroughly** before releasing changes

### ECU Configuration Guidelines

When adding new ECU configurations:

```json
{
  "comment": "Clear description of the ECU and vehicle",
  "ecuname": "BSI_2010",
  "tx_id": "0x733",
  "rx_id": "0x633",
  "protocol": "UDS",
  "zones": {
    "2101": {
      "name": "Configuration Zone",
      "description": "Main configuration parameters",
      "safety_level": "medium"
    }
  }
}
```

### Documentation Standards

- **Use clear English** (or appropriate language)
- **Include examples** for complex procedures
- **Add safety warnings** where appropriate
- **Keep screenshots current** with latest UI
- **Test all instructions** before publishing

---

## 🌍 Translation Guidelines

### Adding New Languages

1. **Create translation file**:
   ```bash
   pyside6-lupdate *.py -source-language en_EN -ts ./i18n/PyPSADiag_LANG.qt.ts
   ```

2. **Translate using Qt Linguist**:
   ```bash
   pyside6-linguist ./i18n/PyPSADiag_LANG.qt.ts
   ```

3. **Compile translations**:
   ```bash
   pyside6-lrelease ./i18n/PyPSADiag_LANG.qt.ts -qm ./i18n/translations/PyPSADiag_LANG.qm
   ```

### Translation Standards

- **Keep technical terms** in original language where appropriate
- **Maintain context** - automotive terms have specific meanings
- **Test in application** - ensure UI fits properly
- **Include country/region variants** when necessary

---

## 🆘 Getting Help

### Community Support

- **GitHub Issues** - Ask questions or report problems
- **Documentation** - Check existing documentation first
- **Code Comments** - Read inline documentation in code

### Development Questions

For development-related questions:

1. **Check existing issues** - Your question might already be answered
2. **Search documentation** - Look through project docs
3. **Create new issue** - Use the "question" label
4. **Be specific** - Provide context and relevant details

---

## 📄 License Agreement

By contributing to PyPSADiag Enhanced, you agree that your contributions will be licensed under the same **GNU General Public License v2.0** that covers the project.

### Key Points

- ✅ **Your contributions are voluntary**
- ✅ **You retain copyright to your contributions**
- ✅ **GPL-2.0 ensures source code remains open**
- ✅ **Same license as original PyPSADiag project**
- ✅ **No warranty or liability from contributors**

---

## 🎯 Recognition

### Contributors

All contributors will be:

- **Listed in CONTRIBUTORS.md** (if created)
- **Credited in release notes** for significant contributions
- **Mentioned in commit history** permanently
- **Appreciated by the community** for their efforts

### Types of Recognition

- **Code Contributors** - Direct code contributions
- **Documentation Contributors** - Improved documentation
- **Translators** - Language translations
- **Testers** - Bug reports and testing
- **Community Helpers** - Answering questions and helping others

---

## 🚀 Ready to Contribute?

1. **Read this guide thoroughly**
2. **Set up your development environment**
3. **Look for "good first issue" labels** for beginners
4. **Join the community** by creating or commenting on issues
5. **Start small** with documentation or minor bug fixes
6. **Ask questions** if you're unsure about anything

**Thank you for contributing to PyPSADiag Enhanced!** 🚗✨

---

*Together, we're building better automotive diagnostic tools for everyone.*
