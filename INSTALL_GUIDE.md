# TAVR Analytics 插件 - 安装与使用指南

## 安装说明

### 1. 前提条件
- 3D Slicer 5.0 或更高版本
- 确保已安装 Sequences 模块（通常默认包含）

### 2. 安装步骤

#### 方法一：开发模式安装
1. 将整个 `tavi_analytics` 文件夹复制到您的工作目录
2. 打开 3D Slicer
3. 进入 `Edit` -> `Application Settings` -> `Modules`
4. 在 `Additional module paths` 中添加 `tavi_analytics` 文件夹的路径
5. 重启 3D Slicer
6. 在模块选择器中找到 `Cardiac` 分类下的 `TAVR Analytics`

#### 方法二：扩展包安装（推荐用于发布版本）
1. 创建扩展包（需要按照 Slicer 扩展包规范）
2. 通过 Extension Manager 安装

## 快速开始

### 第一次使用

1. **打开模块**
   - 在 Slicer 主界面中，选择 `Modules` -> `Cardiac` -> `TAVR Analytics`

2. **快速测试**
   - 点击 `加载演示数据` 按钮
   - 系统会自动创建模拟的 4D 心脏 CT 数据
   - 您可以立即开始测试心动周期管理功能

3. **心动周期导航**
   - 使用滑块浏览不同的心动周期时相
   - 观察 Slicer 视图中的实时更新
   - 在合适的时相点击标记按钮

### 使用真实数据

1. **准备数据**
   - 确保您有 4D 心脏 CT DICOM 数据
   - 数据应包含完整的心动周期时间序列

2. **导入数据**
   - 点击 `数据导入与配置` 按钮
   - 在弹出的对话框中点击 `加载4D DICOM序列`
   - 如果场景中没有数据，系统会引导您到 DICOM 模块
   - 在 DICOM 浏览器中导入并加载您的数据

3. **配置患者信息**
   - 系统会自动从 DICOM 元数据中提取患者信息
   - 手动填写或确认所有必填项：
     - 受试者编号
     - 瓣膜品牌和型号
   - 其他信息可选填写

4. **确认配置**
   - 确认所有信息正确后，点击 `确认并继续`
   - 系统将激活心动周期管理功能

## 主要功能使用

### 心动周期管理

1. **时相导航**
   - 使用水平滑块浏览心动周期
   - 顶部显示当前时相的 R-R 间期百分比
   - 所有 Slicer 视图会实时同步更新

2. **关键时相标记**
   - 浏览到舒张末期，点击 `标记舒张末期`
   - 浏览到收缩末期，点击 `标记收缩末期`
   - 标记信息会显示在界面下方
   - 标记的时相信息会保存供后续模块使用

### 数据管理

1. **重新配置**
   - 在主界面点击 `重新配置数据` 可以更改设置
   - 系统会询问是否放弃当前进度

2. **会话状态**
   - 插件使用单例模式管理会话状态
   - 所有配置和标记信息在会话期间保持

## 瓣膜配置

### 支持的瓣膜型号

当前支持以下瓣膜品牌和型号：

- **Medtronic**: Evolut R/PRO, Evolut FX, CoreValve, Evolut PRO+
- **Edwards Lifesciences**: SAPIEN 3, SAPIEN 3 Ultra, SAPIEN XT
- **Venus Medtech**: VenusA-Valve, VenusA-Plus
- **MicroPort**: VitaFlow
- **Peijia Medical**: TaurusOne

### 添加新瓣膜型号

1. 编辑 `Resources/valve_config.json` 文件
2. 按照现有格式添加新的品牌或型号
3. 重启 Slicer 或重新加载模块

## 常见问题

### Q: 无法加载 DICOM 数据
**A**: 确保数据是有效的 4D 心脏 CT 序列，包含多个时间点的容积数据。检查 DICOM 文件的完整性。

### Q: 瓣膜型号列表为空
**A**: 检查 `valve_config.json` 文件是否存在且格式正确。确保选择了瓣膜品牌。

### Q: 心动周期滑块不工作
**A**: 确保已正确加载 4D 序列数据，并且完成了数据配置步骤。

### Q: 标记的时相信息丢失
**A**: 时相标记在会话期间保持，但场景重置或关闭会清除标记。确保在需要时重新标记。

## 开发信息

### 模块结构
```
tavi_analytics/
├── tavi_analytics.py          # 主模块文件
├── Resources/
│   ├── Icons/
│   │   └── tavi_analytics.png # 模块图标
│   ├── UI/
│   │   └── tavi_analytics.ui  # 界面文件
│   └── valve_config.json      # 瓣膜配置
└── Testing/                   # 测试文件
```

### API 接口

模块提供标准化的 API 供其他模块调用：

```python
# 获取会话实例
session = TAVRStudySession()

# 获取患者数据
patient_data = session.get_patient_data()

# 获取瓣膜信息
valve_info = session.get_selected_valve()

# 获取标记的时相
end_diastole = session.get_marked_phase('end_diastole')
```

### 扩展开发

该模块为 TAVR 分析工作流的基础模块，后续可以开发：

- 模块二：分割与标志点定义
- 模块三：自动化测量
- 模块四：报告生成

所有后续模块都可以通过 TAVRStudySession API 获取必要的数据和配置信息。

## 技术支持

如有问题或建议，请联系开发团队。

## 版本信息

- 当前版本：1.0.0
- 兼容 Slicer 版本：5.0+
- 最后更新：2025-08-04
