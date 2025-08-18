# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TAVR Analytics is a 3D Slicer extension for standardized TAVR (Transcatheter Aortic Valve Replacement) post-operative analysis. It implements a clinical workflow based on the Hangzhou Protocol core lab evaluation form, providing a multi-module system for analyzing 4D cardiac CT data.

## Core Architecture

### Single Instance Pattern
The system uses singleton patterns for core components to ensure data consistency:
- `TAVRStudySession`: Central state management for patient data, 4D CT sequences, and cardiac phase markings
- `ModuleManager`: Handles module lifecycle, dependencies, and inter-module communication
- `PluginConfig`: Configuration management and plugin metadata

### Module System
The extension is built around a modular architecture with 5 planned modules:

**Module 1 (module1/)**: Data Import & Scene Preparation
- 4D DICOM sequence loading and validation
- Patient information management with DICOM metadata extraction
- Valve-specific configuration (supports multiple manufacturers)
- Cardiac cycle management with interactive timeline
- Key files: `module1_widget.py`, `cardiac_cycle_widget.py`, `data_loading_dialog.py`

**Module 2 (module2/)**: Automated Analysis
- Fully automated analysis pipeline
- Algorithm client integration (`alg_client.py`)
- Automatic phase switching capabilities
- Key files: `module2_widget.py`, `module2_logic.py`

**Module 3 (module3/)**: Automated Measurements
- Interactive measurement tools
- HALT (Hypoattenuated Leaflet Thickening) analysis
- PASTE analysis workflow
- MPR positioning and view management
- Key files: `module3_widget.py`, `halt_analysis_widget.py`, `paste_analysis_widget.py`

### Data Models & Session Management

**TAVRStudySession** (`core/session.py`):
- Manages patient data (`PatientData` from `core/data_models.py`)
- Handles 4D CT sequence node references
- Stores cardiac phase markings (end-diastole, end-systole)
- Manages segmentation and landmark nodes
- Provides phase-specific contour data management

**Domain Models** (`core/domain_models.py`):
- `ContourDataManager`: Handles contour/plane data for measurements
- `PhaseContourRepository`: Manages contour data across cardiac phases
- `CardiacPhase`: Enum for cardiac cycle phases

### UI System
Modern shadcn/ui inspired design system in `ui/`:
- `styles.py`: Core style definitions with semantic color system
- `style_utils.py`: Utility classes for consistent styling
- `main_ui.py`: Primary application interface
- Standardized button creation via `LayoutManager.create_button_with_style()`

## Development Commands

### Testing
The project uses Python's unittest framework:
```bash
# Run all tests from the plugin directory
python -m unittest discover tests/

# Run specific test
python tests/test_session.py

# Run tests through 3D Slicer's test system
# (when integrated into Slicer)
```

### 3D Slicer Integration
This is a Slicer ScriptedLoadableModule. Development workflow:
1. Place the `tavi_analytics` folder in Slicer's modules directory
2. Restart Slicer or use Developer mode for hot reload
3. Access via Modules → Cardiac → TAVR Analytics

### Configuration Files
- `valve_config.json`: Defines supported valve manufacturers and models
- `config.json`: Plugin configuration settings
- `CMakeLists.txt`: Slicer module build configuration

## Key Implementation Patterns

### Module Communication
Uses event-driven architecture via `ModuleEventBus`:
- Modules subscribe to events (MODULE_ACTIVATED, SESSION_CHANGED, etc.)
- Central event publishing for loose coupling
- Message passing between modules

### Session State Management
All modules access shared state through `TAVRStudySession`:
```python
session = TAVRStudySession()  # Returns singleton instance
patient_data = session.get_patient_data()
sequence_node = session.get_volume_sequence_node()
```

### Widget Creation Pattern
Modules follow adapter pattern with standardized interfaces:
```python
class ModuleXAdapter(ModuleInterface):
    def create_widget(self, session, parent=None):
        return ModuleXWidget(session, parent)
```

### Error Handling & Logging
- Centralized logging configuration via `PluginConfig.setup_logging()`
- Comprehensive error handling in module loading/activation
- State validation before operations

## Cardiac Workflow Integration

### Phase Management
- End-diastole and end-systole marking capabilities
- Automatic phase switching for analysis
- Real-time cardiac cycle navigation with percentage display

### Valve-Specific Analysis
- Multi-manufacturer valve support (Medtronic, Edwards, Venus, etc.)
- Strategy pattern for valve-specific measurement algorithms
- Configurable analysis parameters per valve type

### DICOM Integration
- Robust DICOM metadata extraction from multiple sources
- Series Description detection with fallback strategies
- Sequence browser integration for 4D data navigation

## Critical Dependencies

### 3D Slicer APIs
- `slicer.mrmlScene`: Scene graph management
- `vtkMRMLSequenceNode`: 4D data handling
- `vtkMRMLSequenceBrowserNode`: Timeline navigation
- `vtkMRMLSegmentationNode`: Anatomical segmentation

### Qt Framework
- PyQt5/PySide for UI components
- Signal/slot pattern for inter-widget communication
- Custom styled widgets using project design system

## File Organization Principles

- `core/`: Fundamental data structures and session management
- `module*/`: Self-contained functional modules with adapters
- `ui/`: Shared UI components and styling system
- `utils/`: Utility functions for DICOM, layout, logging
- `services/`: Shared services like contour positioning
- `widgets/`: Reusable UI components (phase selection, etc.)

## Development Notes

### Hot Reload in Slicer
When developing, use Slicer's reload mechanism or place the module in developer modules directory for easier iteration.

### Memory Management
The singleton pattern requires careful handling during scene resets. Session cleanup is triggered on scene close events.

### Cross-Module Data Sharing
Always use the session singleton for shared state. Avoid direct module-to-module references to maintain loose coupling.