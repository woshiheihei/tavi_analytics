# Contributing to TAVR Analytics

Thank you for your interest in contributing to TAVR Analytics! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

1. **3D Slicer**: Install [3D Slicer](https://download.slicer.org/) version 5.0 or higher
2. **Git**: Ensure you have Git installed on your system
3. **Python Knowledge**: Familiarity with Python 3.6+ and Qt/PythonQt
4. **Medical Imaging**: Basic understanding of medical imaging and DICOM standards is helpful

### Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tavi_analytics.git
   cd tavi_analytics
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/woshiheihei/tavi_analytics.git
   ```

4. Configure 3D Slicer to load the extension:
   - Open 3D Slicer
   - Go to `Edit` → `Application Settings` → `Modules`
   - Add the path to your local `tavi_analytics` directory
   - Restart 3D Slicer

## Development Workflow

### Creating a New Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### Syncing with Upstream

Keep your fork up to date:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

1. **Indentation**: 4 spaces (no tabs)
2. **Line Length**: Maximum 100 characters (soft limit), 120 characters (hard limit)
3. **Naming Conventions**:
   - Classes: `PascalCase` (e.g., `TAVRStudySession`)
   - Functions/Methods: `snake_case` (e.g., `get_patient_data`)
   - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
   - Private members: `_leading_underscore` (e.g., `_internal_method`)

4. **Imports**: 
   - Standard library imports first
   - Third-party imports second
   - Local application imports last
   - Each group separated by a blank line

5. **Type Hints**: Use type hints where possible for better code clarity:
   ```python
   def process_data(patient_id: str, threshold: float = 0.5) -> Dict[str, Any]:
       pass
   ```

### Code Organization

1. **Module Structure**: Follow the existing module pattern
   - Each module should have: `__init__.py`, adapter, logic, widget
   - Use the adapter pattern for module interfaces

2. **Documentation Strings**: Use docstrings for all public classes and methods:
   ```python
   def calculate_volume(segment_node: vtkMRMLSegmentationNode) -> float:
       """
       Calculate the volume of a segmentation.
       
       Args:
           segment_node: The segmentation node to measure
           
       Returns:
           The volume in cubic millimeters
           
       Raises:
           ValueError: If the segment node is invalid
       """
       pass
   ```

3. **Logging**: Use the logging module instead of print statements:
   ```python
   import logging
   logging.info("Processing started")
   logging.error(f"Error occurred: {error_message}")
   ```

### Design Patterns

Follow these design patterns used in the project:
- **Singleton Pattern**: For session and manager classes
- **Adapter Pattern**: For module interfaces
- **Observer Pattern**: For event handling with Slicer scenes
- **Strategy Pattern**: For different algorithms (segmentation, measurement)

## Testing Guidelines

### Writing Tests

1. **Test Structure**: Place tests in the `tavi_analytics/tests/` directory
2. **Test Naming**: Name test files as `test_<module_name>.py`
3. **Test Classes**: Use `unittest.TestCase` for test classes
4. **Mock Dependencies**: Mock Slicer dependencies when testing in isolation

Example test:
```python
import unittest
from unittest.mock import MagicMock

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {"key": "value"}
    
    def test_basic_functionality(self):
        """Test that basic functionality works"""
        result = my_function(self.test_data)
        self.assertEqual(result, expected_value)
    
    def tearDown(self):
        """Clean up after tests"""
        pass
```

### Running Tests

```bash
cd tavi_analytics/tests
python -m unittest discover
```

Or run specific tests:
```bash
python -m unittest test_session.py
```

### Test Coverage

- Aim for at least 70% code coverage for new code
- Critical paths should have 90%+ coverage
- Include tests for edge cases and error conditions

## Commit Message Guidelines

Write clear and meaningful commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(module2): add automatic valve segmentation

Implement threshold-based segmentation for TAVR valve stents.
Uses HU value range 800+ for metal detection.

Closes #123
```

```
fix(session): prevent duplicate session initialization

Fixed bug where multiple session instances could be created
under certain conditions.
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest upstream changes
2. **Run tests** and ensure they pass
3. **Check code style** (if linting tools are available)
4. **Update documentation** if you've changed functionality
5. **Add/update tests** for new features or bug fixes

### Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Go to the GitHub repository and create a Pull Request

3. Fill out the PR template with:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was this tested?
   - **Screenshots**: If applicable (especially for UI changes)
   - **Related Issues**: Link to relevant issues

4. Request review from maintainers

### PR Review Process

- Be responsive to feedback
- Make requested changes in new commits (don't force-push during review)
- Once approved, a maintainer will merge your PR

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated and passing
- [ ] No new warnings introduced
- [ ] Related issues linked

## Documentation

### Code Documentation

1. **Module Documentation**: Each module should have a README in its `doc/` subdirectory
2. **Inline Comments**: Comment complex algorithms and non-obvious code
3. **Docstrings**: All public APIs must have docstrings
4. **Chinese and English**: Documentation should be available in both languages where possible

### Documentation Updates

When adding new features:
1. Update the main README.md
2. Add module-specific documentation
3. Update architectural diagrams if needed
4. Include usage examples

## Questions or Problems?

- **Open an Issue**: For bugs or feature requests
- **Discussion**: For general questions about development

## License

By contributing to TAVR Analytics, you agree that your contributions will be licensed under the same license as the project (to be determined).

---

Thank you for contributing to TAVR Analytics! Your efforts help improve TAVR post-operative care and research.
