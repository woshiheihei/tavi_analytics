# Changelog

All notable changes to TAVR Analytics will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README.md with bilingual (English/Chinese) documentation
- MIT License file
- CONTRIBUTING.md with detailed contribution guidelines
- DEVELOPMENT.md with complete setup and debugging guide
- Pre-commit hooks configuration for automated code quality checks
- GitHub Actions CI/CD pipeline for automated testing and quality assurance
- pyproject.toml for modern Python tooling configuration
- .pylintrc for code quality standards
- requirements.txt for dependency management
- Expanded test suite:
  - test_module_manager.py: Module management tests
  - test_data_models.py: Data model validation tests
- Code quality tools integration (Black, isort, Flake8, Pylint, Bandit)
- Security scanning with Bandit
- Multi-version Python testing (3.8-3.11)

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Added Bandit security scanner for vulnerability detection
- Implemented pre-commit security checks

## [0.1.0] - 2025-01-XX

### Added
- Module 1: Data Import and Scene Preparation
  - 4D CT DICOM sequence loading
  - Automatic patient information extraction from DICOM metadata
  - Cardiac cycle phase management
  - Time-based sequence visualization
  
- Module 2: Guided Segmentation
  - Semi-automated valve stent segmentation
  - Aortic root and lumen segmentation
  - Anatomical landmark definition tools
  - Integration with 3D Slicer Segment Editor
  
- Module 3: Automated Measurements
  - Geometric measurements (dimensions, angles, areas)
  - Clinical parameter calculations
  - Result validation and review interface
  - JSON-based measurement storage
  
- Core Infrastructure
  - TAVRStudySession singleton for session management
  - ModuleManager for module lifecycle management
  - PluginConfig for configuration management
  - Data models for patient and measurement data
  - UI style system with consistent theming
  
- UI Components
  - MainUI with modular layout
  - Patient information display
  - Session status tracking
  - Module navigation interface
  - Status indicators and progress tracking

### Known Issues
- DICOM metadata parsing may vary across different CT manufacturers
- Performance optimization needed for large 4D datasets
- UI responsiveness improvements in progress

---

## Release Notes Format

### Version Number Guidelines

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality in a backwards compatible manner
- **PATCH** version: Backwards compatible bug fixes

### Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes

### Date Format

Dates are in YYYY-MM-DD format.

---

## Contributing

When making changes:
1. Update this CHANGELOG.md under the [Unreleased] section
2. Follow the categories listed above
3. Describe changes from the user's perspective
4. Link to relevant issues/PRs when applicable

## Links

- [Repository](https://github.com/woshiheihei/tavi_analytics)
- [Issues](https://github.com/woshiheihei/tavi_analytics/issues)
- [Pull Requests](https://github.com/woshiheihei/tavi_analytics/pulls)
