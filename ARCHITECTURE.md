# TAVR Analytics Architecture

This document provides an overview of the TAVR Analytics plugin architecture, design patterns, and key components.

## Table of Contents

- [System Architecture](#system-architecture)
- [Design Patterns](#design-patterns)
- [Core Components](#core-components)
- [Module Architecture](#module-architecture)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    3D Slicer Platform                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │           TAVR Analytics Extension                │  │
│  │                                                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │ Module 1 │  │ Module 2 │  │ Module 3 │ ...  │  │
│  │  │  Import  │  │Segmentation│  │ Measure │      │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘      │  │
│  │       │             │             │              │  │
│  │  ┌────┴─────────────┴─────────────┴─────────┐   │  │
│  │  │           Core Infrastructure             │   │  │
│  │  │  - Session Management                     │   │  │
│  │  │  - Module Manager                         │   │  │
│  │  │  - Configuration                          │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │                                                   │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │              UI Layer                     │   │  │
│  │  │  - Main UI  - Widgets  - Styles          │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Layer Architecture

1. **Presentation Layer (UI)**
   - Qt-based user interfaces
   - Custom widgets and controls
   - Style management
   - User interaction handling

2. **Business Logic Layer**
   - Module-specific logic
   - Data processing algorithms
   - Clinical calculation engines
   - Validation rules

3. **Infrastructure Layer**
   - Session management
   - Module lifecycle management
   - Configuration management
   - Utility functions

4. **Data Layer**
   - Data models (PatientData, MeasurementData)
   - DICOM metadata handling
   - Slicer MRML scene integration

## Design Patterns

### 1. Singleton Pattern

Used for global state management to ensure single instances.

**Implementation:**
```python
class TAVRStudySession:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Used in:**
- `TAVRStudySession`: Global session state
- `ModuleManager`: Module lifecycle management
- `PluginConfig`: Configuration management

### 2. Adapter Pattern

Provides a unified interface for different module implementations.

**Implementation:**
```python
class ModuleAdapter:
    def __init__(self, session):
        self._session = session
        
    def get_widget(self):
        raise NotImplementedError
        
    def activate(self):
        raise NotImplementedError
        
    def cleanup(self):
        raise NotImplementedError
```

**Used in:**
- `Module1Adapter`, `Module2Adapter`, `Module3Adapter`
- Standardizes module interface
- Enables hot-swappable module implementations

### 3. Observer Pattern

Used for event-driven communication with Slicer MRML scene.

**Implementation:**
```python
class tavi_analyticsWidget(VTKObservationMixin):
    def setup(self):
        self.addObserver(
            slicer.mrmlScene, 
            slicer.mrmlScene.StartCloseEvent, 
            self._on_scene_start_close
        )
```

**Used in:**
- Scene event monitoring
- Node modification tracking
- Real-time UI updates

### 4. Strategy Pattern

Allows different algorithms to be used interchangeably.

**Potential Usage:**
- Different segmentation strategies
- Various measurement algorithms
- Alternative report formats

### 5. Factory Pattern

Creates objects without specifying exact class.

**Implementation:**
```python
class ModuleManager:
    def activate_module(self, module_name):
        module_info = self._modules.get(module_name)
        module_instance = module_info.module_class(self._session)
        return module_instance
```

## Core Components

### 1. TAVRStudySession

**Purpose**: Manages global study session state

**Responsibilities:**
- Patient data management
- Sequence node tracking
- Cardiac phase management
- DICOM metadata access
- Session lifecycle

**Key Methods:**
```python
- get_patient_data() -> PatientData
- reset() -> None
- set_cardiac_phase(phase_name, frame_number) -> None
- get_cardiac_phase(phase_name) -> Optional[int]
```

### 2. ModuleManager

**Purpose**: Manages module lifecycle and dependencies

**Responsibilities:**
- Module registration
- Module activation/deactivation
- Dependency resolution
- Inter-module communication

**Key Methods:**
```python
- register_module(module_info: ModuleInfo) -> None
- activate_module(module_name: str) -> bool
- deactivate_module(module_name: str) -> None
- get_module_widget(module_name: str) -> QWidget
```

### 3. PluginConfig

**Purpose**: Centralized configuration management

**Responsibilities:**
- Load configuration from JSON
- Provide plugin metadata
- Manage module enable/disable
- Logging configuration

**Key Methods:**
```python
- get_plugin_metadata() -> PluginMetadata
- is_module_enabled(module_name: str) -> bool
- get_valve_config() -> Dict
```

### 4. Data Models

**PatientData**: Stores patient and study information
```python
@dataclass
class PatientData:
    patientID: str = ""
    patientName: str = ""
    patientAge: int = 0
    patientSex: str = ""
    studyDate: Optional[str] = None
    valveBrand: str = ""
    valveModel: str = ""
    valveSize: str = ""
```

## Module Architecture

### Module Structure

Each module follows a consistent structure:

```
moduleX/
├── __init__.py
├── moduleX_adapter.py    # Adapter interface
├── moduleX_logic.py      # Business logic
├── moduleX_widget.py     # UI components
└── doc/
    └── README_ModuleX.md
```

### Module Lifecycle

1. **Registration**: Module registered with ModuleManager
2. **Activation**: Module instance created and initialized
3. **Display**: Widget added to main UI
4. **Interaction**: User interacts with module
5. **Deactivation**: Module cleaned up and hidden
6. **Cleanup**: Resources released

### Module Communication

Modules communicate through:
- **Shared Session**: Access to `TAVRStudySession`
- **MRML Scene**: Slicer's data management system
- **Events**: Qt signals and Slicer observers

## Data Flow

### 1. Data Import Flow (Module 1)

```
DICOM Files → Slicer DICOM DB → Volume Sequence → 
DICOM Metadata Extraction → PatientData → Session
```

### 2. Segmentation Flow (Module 2)

```
Volume Sequence → User Guidance → Segment Editor → 
Segmentation Node → MRML Scene → Available for Measurement
```

### 3. Measurement Flow (Module 3)

```
Segmentation Node → Measurement Algorithm → 
MeasurementData → JSON Storage → Display in UI
```

### 4. Report Generation Flow (Module 5, Planned)

```
Session Data + Measurements + Images → 
Report Template → PDF Generation → File Export
```

## Extension Points

### Adding a New Module

1. Create module directory with standard structure
2. Implement `ModuleAdapter` interface
3. Create logic and widget classes
4. Register in `tavi_analytics.py`
5. Add configuration to `config.json`

### Adding New Measurements

1. Extend measurement logic in Module 3
2. Update `MeasurementData` model if needed
3. Add UI controls for new measurements
4. Update report template

### Customizing UI

1. Modify `ui/styles.py` for global styles
2. Create custom widgets in `ui/` directory
3. Use `StyleManager` for consistent theming

### Adding New Data Sources

1. Extend DICOM utilities in `utils/dicom_utils.py`
2. Update metadata extraction logic
3. Modify `PatientData` model if needed

## Best Practices

### Code Organization

1. **Separation of Concerns**: Keep UI, logic, and data separate
2. **Single Responsibility**: Each class has one main purpose
3. **DRY Principle**: Reuse code through utilities and base classes

### Slicer Integration

1. **Use MRML Scene**: Store data in Slicer's scene for persistence
2. **Leverage Existing Tools**: Use Slicer's built-in functionality
3. **Follow Slicer Conventions**: Naming, structure, and patterns

### Error Handling

1. **Graceful Degradation**: Handle errors without crashing
2. **User Feedback**: Inform users of errors clearly
3. **Logging**: Use logging for debugging and troubleshooting

### Performance

1. **Lazy Loading**: Load data only when needed
2. **Caching**: Cache computed results when appropriate
3. **Progress Feedback**: Show progress for long operations

## Future Architecture Considerations

### Planned Improvements

1. **Plugin System**: Allow third-party extensions
2. **Async Processing**: Background computation for heavy tasks
3. **Cloud Integration**: Remote storage and processing
4. **AI/ML Integration**: Automated segmentation and analysis

### Scalability

1. **Modular Design**: Easy to add new modules
2. **Configurable Pipeline**: Flexible workflow customization
3. **Data Versioning**: Track changes to measurements

---

For implementation details, see:
- [Development Guide](DEVELOPMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- Individual module documentation in `tavi_analytics/moduleX/doc/`
