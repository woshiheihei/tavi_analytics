# 样式重构文档

## 🎨 TAVR Analytics 统一样式系统

### 📋 重构概述

我们已经完成了样式系统的重构，将分散在各个组件中的样式代码抽离到统一的样式系统中。这个重构带来了以下好处：

1. **样式复用** - 避免重复的样式定义
2. **统一设计** - 确保整个应用的视觉一致性
3. **易于维护** - 样式集中管理，修改更容易
4. **主题支持** - 为未来的主题切换打下基础

### 🏗️ 架构说明

#### 核心文件结构
```
tavi_analytics/ui/
├── styles.py          # 核心样式系统
├── style_utils.py     # 样式工具类
└── main_ui.py         # 主界面（已重构）

tavi_analytics/module1/
└── cardiac_cycle_widget.py  # 心动周期组件（已重构）
```

#### 样式系统层次
1. **基础层** (`styles.py`)
   - `ThemeColor` - 颜色常量定义
   - `FontSize` - 字体大小定义  
   - `Spacing` - 间距定义
   - `BorderRadius` - 圆角定义
   - `StyleManager` - 样式生成器

2. **组件层** (`styles.py`)
   - `ComponentStyleFactory` - 为特定组件提供样式集合

3. **工具层** (`style_utils.py`)
   - `StyledWidget` - 创建样式化控件的工厂类
   - `StyleUtils` - 样式相关工具方法
   - `WidgetStyler` - 为现有控件应用样式

### 🚀 使用方法

#### 1. 创建新的样式化控件

```python
from ui.style_utils import StyledWidget

# 创建按钮
primary_button = StyledWidget.create_button("主要按钮", "primary", "normal")
secondary_button = StyledWidget.create_button("次要按钮", "secondary", "small")

# 创建标签
title_label = StyledWidget.create_label("标题文本", "title")
info_label = StyledWidget.create_label("信息文本", "info")

# 创建状态指示器
status = StyledWidget.create_status_indicator("就绪", "success")
```

#### 2. 为现有控件应用样式

```python
from ui.style_utils import style

# 链式调用应用样式
style(existing_button).as_button("primary", "large")
style(existing_label).as_label("subtitle")
style(status_label).as_status_indicator("warning")
```

#### 3. 使用组件样式集合

```python
from ui.styles import ComponentStyleFactory

# 获取心动周期组件的样式集合
styles = ComponentStyleFactory.get_cardiac_cycle_styles()

# 应用特定样式
button.setStyleSheet(styles["mark_button"])
label.setStyleSheet(styles["phase_percent_label"])
```

#### 4. 直接使用样式管理器

```python
from ui.styles import StyleManager

# 获取特定样式
button_style = StyleManager.get_button_style("primary", "normal")
label_style = StyleManager.get_label_style("title")
slider_style = StyleManager.get_slider_style()

# 应用样式
widget.setStyleSheet(button_style)
```

### 🎨 样式类型说明

#### 按钮类型
- `primary` - 主要按钮（深灰色）
- `secondary` - 次要按钮（浅灰色）
- `success` - 成功按钮（绿色）
- `warning` - 警告按钮（橙色）
- `danger` - 危险按钮（红色）

#### 按钮大小
- `small` - 小按钮（28px 高度）
- `normal` - 普通按钮（35px 高度）
- `large` - 大按钮（40px 高度）

#### 标签类型
- `normal` - 普通标签
- `title` - 标题标签
- `subtitle` - 副标题标签
- `info` - 信息标签
- `primary` - 主要标签（带背景）
- `secondary` - 次要标签（带背景）

#### 状态类型
- `normal` - 普通状态（蓝色）
- `success` - 成功状态（绿色）
- `warning` - 警告状态（橙色）
- `error` - 错误状态（红色）

### 🎯 设计原则

1. **简洁性** - 采用简洁的灰色系主题，避免过多颜色
2. **一致性** - 所有组件使用统一的颜色、字体和间距
3. **可读性** - 确保良好的对比度和可读性
4. **专业性** - 适合医疗软件的专业外观

### 🔧 扩展指南

#### 添加新的主题颜色

1. 在 `ThemeColor` 枚举中添加新颜色：
```python
class ThemeColor(Enum):
    # 现有颜色...
    NEW_COLOR = "#your_color_hex"
```

2. 在相应的样式方法中使用新颜色。

#### 添加新的组件样式

1. 在 `ComponentStyleFactory` 中添加新方法：
```python
@staticmethod
def get_your_component_styles() -> Dict[str, str]:
    return {
        "your_widget": StyleManager.get_label_style("normal"),
        # 更多样式...
    }
```

#### 添加新的样式类型

1. 在 `StyleManager` 中添加新的样式生成方法：
```python
@staticmethod
def get_your_widget_style(widget_type: str = "normal") -> str:
    # 样式生成逻辑
    return style_string
```

### 📝 迁移指南

#### 重构现有组件

1. **导入样式模块**：
```python
from ui.styles import ComponentStyleFactory
# 或
from ui.style_utils import StyledWidget, style
```

2. **替换硬编码样式**：
```python
# 之前
widget.setStyleSheet("background-color: #666; color: white; ...")

# 之后
styles = ComponentStyleFactory.get_component_styles()
widget.setStyleSheet(styles["widget_name"])
```

3. **使用样式工厂**：
```python
# 之前
button = qt.QPushButton("文本")
button.setStyleSheet("复杂的样式代码...")

# 之后
button = StyledWidget.create_button("文本", "primary", "normal")
```

### ✅ 已重构的组件

- [x] `cardiac_cycle_widget.py` - 心动周期管理组件
- [x] `main_ui.py` - 主界面组件
- [ ] 其他模块组件（待重构）

### 🔮 未来计划

1. **主题切换** - 支持亮色/暗色主题
2. **动态样式** - 根据用户偏好调整样式
3. **更多组件** - 为更多控件类型添加样式
4. **样式预览** - 开发样式预览工具

### 📚 参考资源

- [Qt样式表文档](https://doc.qt.io/qt-5/stylesheet.html)
- [材料设计指南](https://material.io/design)
- [医疗软件界面设计最佳实践](https://example.com)

---

*本文档随样式系统的发展持续更新*
