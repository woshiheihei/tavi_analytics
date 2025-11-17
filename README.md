# TAVR Analytics

<div align="center">

![TAVR Analytics](tavi_analytics.png)

**A 3D Slicer Extension for TAVR Post-Operative CT Analysis**

[![3D Slicer](https://img.shields.io/badge/3D%20Slicer-Compatible-blue)](https://www.slicer.org/)
[![Python](https://img.shields.io/badge/Python-3.6%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-TBD-lightgrey)](LICENSE)

[English](#english) | [中文](#中文)

</div>

---

## English

### Overview

TAVR Analytics is a comprehensive 3D Slicer extension designed to streamline and standardize the post-operative assessment workflow for Transcatheter Aortic Valve Replacement (TAVR) procedures. This plugin integrates data loading, 4D visualization, semi-automated segmentation, guided measurement, and automated report generation into a unified platform.

### Key Features

- **📊 Integrated Workflow**: Single-platform solution from data import to final report
- **🫀 4D CT Support**: Full cardiac cycle visualization and analysis
- **✂️ Semi-Automated Segmentation**: Guided segmentation tools for valve and aortic structures
- **📏 Automated Measurements**: Comprehensive geometric and clinical measurements
- **📑 Standardized Reports**: Automatic generation of clinical assessment forms
- **🔍 Advanced Analysis**: Support for HALT, RELM, and SFD evaluation

### Clinical Significance

The plugin addresses critical challenges in TAVR post-operative assessment:
- **Efficiency**: Reduces analysis time by integrating measurement and reporting
- **Accuracy**: Minimizes manual transcription errors
- **Standardization**: Ensures consistent evaluation across studies
- **Research Support**: Facilitates systematic analysis of large patient cohorts

Key clinical metrics supported:
- **HALT** (Hypoattenuated Leaflet Thickening): Early indicator of subclinical leaflet thrombosis
- **RELM** (Reduced Leaflet Motion): Assessment of valve leaflet mobility
- **SFD** (Sinus Filling Defect): Independent predictor of Major Adverse Cardiac and Cerebrovascular Events (MACCO)

### Architecture

The plugin follows a modular architecture with five main modules:

1. **Module 1**: Data Import and Scene Preparation
   - DICOM 4D CT sequence loading
   - Automatic patient information extraction
   - Cardiac cycle phase management

2. **Module 2**: Guided Segmentation
   - Semi-automated valve stent segmentation
   - Aortic root and lumen delineation
   - Anatomical landmark definition

3. **Module 3**: Automated Measurements
   - Geometric measurements (dimensions, angles, areas)
   - Clinical parameters calculation
   - Result validation and review

4. **Module 4**: Visualization and Interaction (Planned)
   - Multi-planar reconstruction
   - 3D rendering and manipulation
   - Custom view configurations

5. **Module 5**: Report Generation (Planned)
   - Automated form filling
   - Image annotation and capture
   - PDF report export

### Technical Stack

- **Platform**: 3D Slicer 5.x
- **Language**: Python 3.6+
- **UI Framework**: Qt (via PythonQt)
- **Build System**: CMake
- **Key Dependencies**: 
  - VTK (Visualization Toolkit)
  - ITK (Insight Segmentation and Registration Toolkit)
  - SlicerRT

### Installation

#### Prerequisites

1. Install [3D Slicer](https://download.slicer.org/) (version 5.0 or higher)
2. Ensure Python 3.6+ is available in your Slicer installation

#### Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/woshiheihei/tavi_analytics.git
   ```

2. Open 3D Slicer

3. Load the extension:
   - Go to `Edit` → `Application Settings` → `Modules`
   - Add the path to `tavi_analytics` directory
   - Restart 3D Slicer

4. The "TAVR Analytics" module should now appear in the "Cardiac" category

### Usage

#### Quick Start

1. Launch the TAVR Analytics module from the module selector
2. Click "Import Data" to load your 4D CT DICOM sequence
3. Review and confirm patient information
4. Mark key cardiac phases (end-diastole and end-systole)
5. Follow the guided workflow through segmentation and measurement
6. Review results and generate the final report

#### Detailed Documentation

For detailed usage instructions, please refer to:
- [Module 1 Documentation](tavi_analytics/module1/doc/README_Module1.md)
- [Complete DICOM Integration Guide](doc/关键文档/COMPLETE_DICOM_INTEGRATION.md)
- [UI Style System Overview](tavi_analytics/ui/doc/UI_STYLE_SYSTEM_OVERVIEW.md)

### Development

#### Project Structure

```
tavi_analytics/
├── tavi_analytics/           # Main plugin package
│   ├── core/                 # Core components (session, models, managers)
│   ├── module1/              # Data import and scene preparation
│   ├── module2/              # Guided segmentation
│   ├── module3/              # Automated measurements
│   ├── module4/              # Visualization (planned)
│   ├── module5/              # Report generation (planned)
│   ├── ui/                   # UI components and styles
│   ├── utils/                # Utility functions
│   └── tests/                # Unit tests
├── doc/                      # Documentation
├── prd/                      # Product requirement documents
└── CMakeLists.txt            # CMake build configuration
```

#### Design Patterns

- **Singleton**: Used for session management and module manager
- **Adapter Pattern**: Module adapters for standardized interface
- **Observer Pattern**: For scene and data updates
- **Strategy Pattern**: For different segmentation and measurement algorithms

#### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

#### Development Setup

1. Clone the repository
2. Set up your development environment with 3D Slicer
3. Install development dependencies (if any)
4. Run tests:
   ```bash
   cd tavi_analytics/tests
   python test_session.py
   ```

### Testing

Currently, the project includes unit tests for core functionality:
- Session management tests
- Data model validation
- Module registration tests

To run tests:
```bash
cd tavi_analytics/tests
python -m unittest test_session.py
```

### Roadmap

- [x] Module 1: Data Import and Scene Preparation
- [x] Module 2: Guided Segmentation
- [x] Module 3: Automated Measurements
- [ ] Module 4: Advanced Visualization
- [ ] Module 5: Report Generation
- [ ] Enhanced test coverage
- [ ] Continuous Integration setup
- [ ] Documentation translation
- [ ] Performance optimization

### Known Issues

- Some DICOM metadata parsing may vary across different CT manufacturers
- Performance optimization needed for large 4D datasets
- UI responsiveness improvements in progress

### Support

For questions, issues, or suggestions:
- Open an [Issue](https://github.com/woshiheihei/tavi_analytics/issues)
- Refer to the [Documentation](doc/)

### License

[To be determined - Please add appropriate license]

### Acknowledgments

This plugin is developed based on the Hangzhou Protocol for TAVR Post-Operative CT Core Laboratory Assessment. It aims to standardize the TAVR post-operative analysis workflow for clinical research and practice.

### Citation

If you use this software in your research, please cite:
```
[Citation information to be added]
```

---

## 中文

### 概述

TAVR Analytics 是一款全面的3D Slicer扩展插件，旨在简化和标准化经导管主动脉瓣置换术（TAVR）术后评估工作流程。该插件将数据导入、4D可视化、半自动分割、引导式测量和自动化报告生成集成到统一平台中。

### 主要特性

- **📊 集成工作流**: 从数据导入到最终报告的单平台解决方案
- **🫀 4D CT支持**: 完整心动周期可视化和分析
- **✂️ 半自动分割**: 瓣膜和主动脉结构的引导式分割工具
- **📏 自动化测量**: 全面的几何和临床测量
- **📑 标准化报告**: 自动生成临床评估表单
- **🔍 高级分析**: 支持HALT、RELM和SFD评估

### 临床意义

该插件解决了TAVR术后评估中的关键挑战：
- **效率**: 通过集成测量和报告功能减少分析时间
- **准确性**: 最小化手动转录错误
- **标准化**: 确保研究间评估的一致性
- **研究支持**: 促进大型患者队列的系统分析

支持的关键临床指标：
- **HALT**（瓣叶低密度增厚）：亚临床瓣叶血栓的早期指标
- **RELM**（瓣叶活动度减退）：瓣膜瓣叶活动度评估
- **SFD**（窦内充盈缺损）：主要不良心脑血管事件（MACCO）的独立预测因子

### 架构

插件遵循模块化架构，包含五个主要模块：

1. **模块一**：数据导入与场景准备
   - DICOM 4D CT序列加载
   - 自动提取患者信息
   - 心动周期时相管理

2. **模块二**：引导式分割
   - 半自动瓣膜支架分割
   - 主动脉根部和腔内描绘
   - 解剖标志点定义

3. **模块三**：自动化测量
   - 几何测量（尺寸、角度、面积）
   - 临床参数计算
   - 结果验证和审查

4. **模块四**：可视化与交互（计划中）
   - 多平面重建
   - 3D渲染和操作
   - 自定义视图配置

5. **模块五**：报告生成（计划中）
   - 自动表单填充
   - 图像标注和捕获
   - PDF报告导出

### 技术栈

- **平台**: 3D Slicer 5.x
- **语言**: Python 3.6+
- **UI框架**: Qt（通过PythonQt）
- **构建系统**: CMake
- **主要依赖**: 
  - VTK（可视化工具包）
  - ITK（影像分割与配准工具包）
  - SlicerRT

### 安装

#### 先决条件

1. 安装 [3D Slicer](https://download.slicer.org/)（5.0版本或更高）
2. 确保您的Slicer安装中包含Python 3.6+

#### 安装步骤

1. 克隆此仓库：
   ```bash
   git clone https://github.com/woshiheihei/tavi_analytics.git
   ```

2. 打开3D Slicer

3. 加载扩展：
   - 转到 `Edit` → `Application Settings` → `Modules`
   - 添加 `tavi_analytics` 目录路径
   - 重启3D Slicer

4. "TAVR Analytics"模块现在应该出现在"Cardiac"类别中

### 使用

#### 快速开始

1. 从模块选择器启动TAVR Analytics模块
2. 点击"导入数据"加载您的4D CT DICOM序列
3. 审查并确认患者信息
4. 标记关键心动周期时相（舒张末期和收缩末期）
5. 按照引导式工作流程完成分割和测量
6. 审查结果并生成最终报告

#### 详细文档

详细使用说明请参考：
- [模块一文档](tavi_analytics/module1/doc/README_Module1.md)
- [完整DICOM集成指南](doc/关键文档/COMPLETE_DICOM_INTEGRATION.md)
- [UI样式系统概述](tavi_analytics/ui/doc/UI_STYLE_SYSTEM_OVERVIEW.md)

### 开发

#### 项目结构

```
tavi_analytics/
├── tavi_analytics/           # 主插件包
│   ├── core/                 # 核心组件（会话、模型、管理器）
│   ├── module1/              # 数据导入与场景准备
│   ├── module2/              # 引导式分割
│   ├── module3/              # 自动化测量
│   ├── module4/              # 可视化（计划中）
│   ├── module5/              # 报告生成（计划中）
│   ├── ui/                   # UI组件和样式
│   ├── utils/                # 工具函数
│   └── tests/                # 单元测试
├── doc/                      # 文档
├── prd/                      # 产品需求文档
└── CMakeLists.txt            # CMake构建配置
```

#### 设计模式

- **单例模式**: 用于会话管理和模块管理器
- **适配器模式**: 模块适配器提供标准化接口
- **观察者模式**: 用于场景和数据更新
- **策略模式**: 用于不同的分割和测量算法

#### 贡献

我们欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

#### 开发环境设置

1. 克隆仓库
2. 使用3D Slicer设置您的开发环境
3. 安装开发依赖（如有）
4. 运行测试：
   ```bash
   cd tavi_analytics/tests
   python test_session.py
   ```

### 测试

目前，项目包含核心功能的单元测试：
- 会话管理测试
- 数据模型验证
- 模块注册测试

运行测试：
```bash
cd tavi_analytics/tests
python -m unittest test_session.py
```

### 路线图

- [x] 模块一：数据导入与场景准备
- [x] 模块二：引导式分割
- [x] 模块三：自动化测量
- [ ] 模块四：高级可视化
- [ ] 模块五：报告生成
- [ ] 增强测试覆盖率
- [ ] 持续集成设置
- [ ] 文档翻译
- [ ] 性能优化

### 已知问题

- 不同CT制造商的DICOM元数据解析可能有所不同
- 需要对大型4D数据集进行性能优化
- UI响应性改进正在进行中

### 支持

如有问题、问题或建议：
- 打开 [Issue](https://github.com/woshiheihei/tavi_analytics/issues)
- 参考 [文档](doc/)

### 许可证

[待确定 - 请添加适当的许可证]

### 致谢

该插件基于杭州方案TAVR术后CT核心实验室评估表开发。旨在为临床研究和实践标准化TAVR术后分析工作流程。

### 引用

如果您在研究中使用此软件，请引用：
```
[待添加引用信息]
```

---

