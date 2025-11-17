# Development Setup Guide

This guide will help you set up your development environment for TAVR Analytics.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Tools](#development-tools)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Debugging](#debugging)
- [Common Issues](#common-issues)

## Prerequisites

### Required Software

1. **3D Slicer** (version 5.0 or higher)
   - Download from: https://download.slicer.org/
   - Install the appropriate version for your operating system

2. **Git**
   - Windows: https://git-scm.com/download/win
   - macOS: `brew install git` or included with Xcode
   - Linux: `sudo apt-get install git` (Ubuntu/Debian)

3. **Python 3.6+**
   - Usually included with 3D Slicer
   - For standalone testing: https://www.python.org/downloads/

### Recommended Tools

- **Visual Studio Code** or **PyCharm** for code editing
- **Git GUI client** (optional): GitHub Desktop, GitKraken, SourceTree

## Environment Setup

### 1. Clone the Repository

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/tavi_analytics.git
cd tavi_analytics

# Add upstream remote
git remote add upstream https://github.com/woshiheihei/tavi_analytics.git
```

### 2. Set Up 3D Slicer

#### Configure Slicer to Load the Extension

1. Open 3D Slicer
2. Go to `Edit` → `Application Settings`
3. Navigate to the `Modules` section
4. Click `Add` under "Additional module paths"
5. Browse to your cloned `tavi_analytics` directory
6. Select the directory and click `OK`
7. Restart 3D Slicer

#### Verify Installation

1. After restarting, open the module selector
2. Look for "TAVR Analytics" under the "Cardiac" category
3. If found, the extension is loaded successfully

### 3. Install Development Dependencies (Optional)

For running tests and code quality tools outside of Slicer:

```bash
# Install development tools
pip install -r requirements-dev.txt

# Or install individual tools
pip install pytest pytest-cov pylint black isort flake8 mypy bandit
```

**Note**: Create a `requirements-dev.txt` file with development dependencies if needed.

## Development Tools

### Visual Studio Code Setup

1. **Install Python Extension**
   ```
   Name: Python
   Id: ms-python.python
   ```

2. **Install Pylance** (for better Python IntelliSense)
   ```
   Name: Pylance
   Id: ms-python.vscode-pylance
   ```

3. **Configure VS Code Settings** (`.vscode/settings.json`):
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.linting.flake8Enabled": true,
     "python.formatting.provider": "black",
     "python.formatting.blackArgs": ["--line-length", "120"],
     "editor.formatOnSave": true,
     "editor.rulers": [120],
     "files.exclude": {
       "**/__pycache__": true,
       "**/*.pyc": true
     }
   }
   ```

### PyCharm Setup

1. **Configure Python Interpreter**
   - Go to `File` → `Settings` → `Project: tavi_analytics` → `Python Interpreter`
   - Select the Python interpreter from your Slicer installation

2. **Configure Code Style**
   - Go to `File` → `Settings` → `Editor` → `Code Style` → `Python`
   - Set line length to 120
   - Enable "Use Black formatter"

3. **Enable Version Control**
   - PyCharm should auto-detect Git
   - Configure in `File` → `Settings` → `Version Control`

## Running Tests

### Run All Tests

```bash
# From the repository root
cd tavi_analytics/tests

# Run all tests
python -m unittest discover -v

# Or with pytest (if installed)
pytest -v
```

### Run Specific Test Files

```bash
# Run a specific test file
python -m unittest test_session.py

# Run a specific test class
python -m unittest test_session.TestTAVRStudySession

# Run a specific test method
python -m unittest test_session.TestTAVRStudySession.test_singleton_pattern
```

### Run Tests with Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage report
pytest --cov=tavi_analytics --cov-report=html

# Open coverage report
# The report will be in htmlcov/index.html
```

## Code Quality

### Format Code

```bash
# Format code with Black
black --line-length 120 tavi_analytics/

# Check formatting without changes
black --check --line-length 120 tavi_analytics/
```

### Sort Imports

```bash
# Sort imports with isort
isort --profile black --line-length 120 tavi_analytics/

# Check import order
isort --check-only --profile black tavi_analytics/
```

### Run Linters

```bash
# Flake8 - Style guide enforcement
flake8 tavi_analytics/ --max-line-length=120 --extend-ignore=E203,E501,W503

# Pylint - Code analysis
pylint tavi_analytics/ --rcfile=.pylintrc

# Mypy - Type checking (optional)
mypy tavi_analytics/ --ignore-missing-imports
```

### Security Check

```bash
# Run Bandit security scanner
bandit -r tavi_analytics/ -ll
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Debugging

### Debug in 3D Slicer

1. **Enable Python Console**
   - In Slicer, go to `View` → `Python Interactor`
   - The console will show error messages and print statements

2. **Add Debug Prints**
   ```python
   import logging
   logging.info("Debug message")
   logging.error("Error message")
   ```

3. **Reload Module**
   - After making code changes, reload the module in Slicer
   - In Python Console: `slicer.util.reloadScriptedModule('tavi_analytics')`

4. **Use Python Debugger**
   ```python
   import pdb; pdb.set_trace()  # Set breakpoint
   ```

### Debug Tests

```bash
# Run tests with verbose output
python -m unittest test_session.py -v

# Run with Python debugger
python -m pdb -m unittest test_session.py
```

### Common Debugging Commands in Slicer Console

```python
# List all loaded modules
slicer.util.getModuleNames()

# Get reference to a node
node = slicer.util.getNode('YourNodeName')

# List all nodes
nodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')

# Reload module after code changes
slicer.util.reloadScriptedModule('tavi_analytics')
```

## Common Issues

### Issue 1: Module Not Loading in Slicer

**Problem**: Extension doesn't appear in module selector

**Solutions**:
- Verify the path in Application Settings → Modules
- Check for Python syntax errors in console
- Ensure CMakeLists.txt is properly configured
- Restart Slicer after changes

### Issue 2: Import Errors

**Problem**: "ModuleNotFoundError" or similar import errors

**Solutions**:
- Ensure all `__init__.py` files exist in package directories
- Check that the tavi_analytics directory is in sys.path
- Verify relative imports are correct

### Issue 3: Tests Fail with Slicer Imports

**Problem**: Tests fail because `slicer` module is not available

**Solutions**:
- Mock Slicer dependencies in tests:
  ```python
  from unittest.mock import MagicMock
  sys.modules['slicer'] = MagicMock()
  sys.modules['vtk'] = MagicMock()
  sys.modules['qt'] = MagicMock()
  ```

### Issue 4: Code Style Issues

**Problem**: Linting errors or formatting issues

**Solutions**:
- Run black formatter: `black tavi_analytics/`
- Run isort: `isort tavi_analytics/`
- Check .pylintrc for disabled warnings

### Issue 5: Git Merge Conflicts

**Problem**: Conflicts when pulling from upstream

**Solutions**:
```bash
# Fetch upstream changes
git fetch upstream

# Merge changes
git merge upstream/main

# If conflicts, resolve them and:
git add .
git commit -m "Resolve merge conflicts"
```

## Additional Resources

### Documentation

- [3D Slicer Developer Guide](https://slicer.readthedocs.io/en/latest/developer_guide/index.html)
- [Python Module Development](https://slicer.readthedocs.io/en/latest/developer_guide/python_faq.html)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

### Useful Links

- [Project Repository](https://github.com/woshiheihei/tavi_analytics)
- [Issue Tracker](https://github.com/woshiheihei/tavi_analytics/issues)
- [3D Slicer Forum](https://discourse.slicer.org/)

## Getting Help

If you encounter issues:

1. Check this guide and [CONTRIBUTING.md](CONTRIBUTING.md)
2. Search existing [GitHub Issues](https://github.com/woshiheihei/tavi_analytics/issues)
3. Ask on the [3D Slicer Forum](https://discourse.slicer.org/)
4. Open a new issue with detailed description

---

Happy coding! 🚀
