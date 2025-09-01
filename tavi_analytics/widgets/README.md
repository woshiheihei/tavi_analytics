# UI组件使用文档

## 概述

本目录包含可在多个模块间复用的UI组件，为TAVI Analytics插件提供统一的用户界面元素。

## 组件列表

### 1. 期像选择组件 (PhaseSelectionWidget)

`PhaseSelectionWidget` 是一个可在多个模块间复用的期像选择UI组件，提供舒张末期和收缩末期的切换功能。

#### 功能特性

- 🫀 **舒张末期切换**：切换到舒张末期进行分析
- 💓 **收缩末期切换**：切换到收缩末期进行分析  
- 🔄 **自动期像切换**：模块激活时自动切换到指定期像
- 📊 **状态显示**：实时显示期像切换状态
- 🎯 **信号通信**：通过Qt信号与父组件通信

#### 使用方法

```python
from ..widgets.phase_selection_widget import PhaseSelectionWidget

# 创建期像选择组件
self.phase_selection = PhaseSelectionWidget(session, self)

# 连接信号
self.phase_selection.phaseChanged.connect(self._on_phase_changed)
self.phase_selection.statusUpdated.connect(self._on_phase_status_updated)

# 添加到布局
layout.addWidget(self.phase_selection)
```

### 2. 关键视图管理器 (KeyViewManagerWidget)

`KeyViewManagerWidget` 提供MPR视图标记、管理和恢复的标准化用户界面。

#### 功能特性

- 📌 **视图标记功能**：支持快捷键标记当前MPR视图
- 📋 **已标记视图列表**：显示所有已标记的视图
- 🔄 **视图恢复操作**：一键恢复到标记的视图位置
- 🗑️ **视图删除功能**：管理和删除不需要的视图标记
- 📊 **统计信息**：显示视图标记统计和期像分布
- 💾 **导入导出**：支持视图标记的备份和恢复

#### 使用方法

```python
from ..widgets import KeyViewManagerWidget, create_key_view_manager

# 创建关键视图管理器
self.key_view_manager = create_key_view_manager(
    analysis_type="HALT",  # 分析类型
    session=self.session,  # 会话对象
    compact=False,         # 是否紧凑模式
    parent=self
)

# 连接信号
self.key_view_manager.viewMarked.connect(self._on_view_marked)
self.key_view_manager.viewRestored.connect(self._on_view_restored)
self.key_view_manager.statusUpdated.connect(self._on_status_updated)

# 添加到布局
layout.addWidget(self.key_view_manager)
```

### 3. 瓣膜叠加组件 (ValveOverlayWidget) ⭐ 新增

`ValveOverlayWidget` 提供一键将瓣膜支架叠加到Red切片视图的功能。

#### 功能特性

- 🩺 **一键叠加**：自动检测瓣膜数据并叠加到Red视图
- 🔍 **自动对齐**：瓣膜支架自动对齐到当前Red切片位置和方向
- 🎚️ **透明度调节**：实时调整瓣膜叠加的透明度
- ⚙️ **位置微调**：支持通过Transforms模块进行精细调整
- 📊 **状态监控**：实时显示叠加状态和瓣膜数据状态
- 🔄 **重置功能**：一键重置叠加到初始状态

#### 使用方法

```python
from ..widgets import ValveOverlayWidget, create_valve_overlay_widget

# 创建瓣膜叠加组件
self.valve_overlay = create_valve_overlay_widget(session=self.session, parent=self)

# 连接信号
self.valve_overlay.overlayEnabled.connect(self._on_overlay_changed)
self.valve_overlay.opacityChanged.connect(self._on_opacity_changed)
self.valve_overlay.statusUpdated.connect(self._on_status_updated)

# 添加回调函数（可选）
self.valve_overlay.add_overlay_callback(self._overlay_callback)
self.valve_overlay.add_opacity_callback(self._opacity_callback)

# 添加到布局
layout.addWidget(self.valve_overlay)
```

#### 外部控制接口

```python
# 强制启用/禁用叠加
self.valve_overlay.force_enable_overlay()
self.valve_overlay.force_disable_overlay()

# 设置透明度
self.valve_overlay.set_opacity(0.5)  # 50%透明度

# 获取当前状态
is_active = self.valve_overlay.get_overlay_status()
current_opacity = self.valve_overlay.get_current_opacity()

# 刷新瓣膜数据检查
self.valve_overlay.refresh_valve_data()
```

#### 演示示例

```python
# 运行演示（在Slicer Python Console中）
from tavi_analytics.widgets.valve_overlay_demo import show_valve_overlay_demo

demo = show_valve_overlay_demo()
# 这将显示一个包含瓣膜叠加组件的演示窗口
```

#### 前提条件

- Slicer中已加载名为 `valve` 的瓣膜体数据（VectorVolume 或 ScalarVolume）
- Red视图已调整到目标MPR位置

#### 工作原理

组件基于3D Slicer的叠加技术，通过以下步骤实现瓣膜叠加：

1. **自动检测**：搜索名为"valve"的体数据节点
2. **矩阵计算**：计算瓣膜到Red切片的变换矩阵
3. **变换应用**：创建并应用线性变换节点
4. **叠加配置**：设置Red视图的前景叠加
5. **实时控制**：提供透明度和位置的实时调整

### 4. 分区卡片组件 (SectionCard)

`SectionCard` 提供统一的卡片式分区布局，用于组织模块内容。

#### 使用方法

```python
from ..widgets import SectionCard

# 创建分区卡片
card = SectionCard(
    title="分析结果",
    icon_text="📊",
    variant="blue",  # 可选: blue, green, purple, neutral
    parent=self
)

# 添加内容
card.add_widget(your_content_widget)
layout.addWidget(card)
```

### 5. 紧凑期像切换 (CompactPhaseToggle)

`CompactPhaseToggle` 提供紧凑的期像切换控件。

#### 使用方法

```python
from ..widgets import CompactPhaseToggle

toggle = CompactPhaseToggle(session=self.session, parent=self)
toggle.phaseChanged.connect(self._on_phase_changed)
layout.addWidget(toggle)
```

## 设计原则

1. **可复用性**：组件独立封装，可在多个模块中使用
2. **一致性**：UI样式与项目整体风格保持一致
3. **灵活性**：支持自定义配置和扩展
4. **响应性**：通过信号机制实现与父组件的松耦合通信
5. **可维护性**：集中管理通用功能，便于维护和更新

## 故障排除

### 瓣膜叠加组件常见问题

1. **找不到瓣膜数据**
   - 确认Slicer中已加载名为"valve"的体数据
   - 点击刷新按钮重新检查数据

2. **叠加位置不准确**
   - 确保Red视图已调整到正确的MPR位置
   - 使用"微调位置"功能进行精细调整

3. **透明度调节无效**
   - 确认叠加已启用
   - 检查Red视图的前景设置

如需更多帮助，请查看各组件的源代码注释或联系开发团队。
