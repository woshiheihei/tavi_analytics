# TAVR Analytics UI 样式系统 - shadcn/ui 设计完成

## 项目概览

TAVR Analytics 现已成功迁移到基于 shadcn/ui 设计原则的现代化样式系统。这个新系统提供了一致、专业且可访问的用户界面，符合当代前端设计标准。

## 设计系统特性

### 🎨 现代化色彩方案

基于 shadcn/ui 的语义化颜色系统：

```python
# 主色调
PRIMARY = "#0f172a"          # slate-900 - 专业深色
PRIMARY_FOREGROUND = "#f8fafc"  # slate-50 - 主色前景

# 次要色调  
SECONDARY = "#f1f5f9"        # slate-100 - 轻柔背景
SECONDARY_FOREGROUND = "#0f172a"  # slate-900 - 次要前景

# 背景色调
BACKGROUND = "#ffffff"        # 纯白背景
FOREGROUND = "#020617"       # slate-950 - 主要文本

# 功能色调
SUCCESS = "#22c55e"          # green-500
WARNING = "#f59e0b"          # amber-500  
ERROR = "#ef4444"            # red-500
INFO = "#3b82f6"             # blue-500
```

### 📏 规范化字体系统

```python
# 字体大小 (rem 单位)
XS = "0.75rem"     # 12px
SM = "0.875rem"    # 14px  
BASE = "1rem"      # 16px
LG = "1.125rem"    # 18px
XL = "1.25rem"     # 20px

# 字体粗细
NORMAL = "400"
MEDIUM = "500"
SEMIBOLD = "600"
BOLD = "700"
```

### 🎯 一致间距体系

```python
# 间距 (rem 单位)
XS = "0.25rem"    # 4px
SM = "0.5rem"     # 8px
MD = "1rem"       # 16px
LG = "1.5rem"     # 24px
XL = "2rem"       # 32px
```

### 🔲 标准化边框和阴影

```python
# 圆角
SM = "0.125rem"   # 2px
MD = "0.375rem"   # 6px
LG = "0.5rem"     # 8px
FULL = "9999px"   # 完全圆形

# 阴影层级
SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
MD = "0 4px 6px -1px rgb(0 0 0 / 0.1)"
LG = "0 10px 15px -3px rgb(0 0 0 / 0.1)"
```

## 组件库

### 🔘 按钮组件

支持多种样式和尺寸：

```python
# 样式变体
"default"      # 标准灰色按钮
"secondary"    # 次要按钮
"destructive"  # 危险操作红色按钮
"outline"      # 轮廓按钮
"ghost"        # 幽灵按钮
"link"         # 链接样式按钮

# 尺寸选项
"sm"      # 小尺寸
"default" # 标准尺寸  
"lg"      # 大尺寸
"icon"    # 图标按钮
```

### 🏷️ 标签组件

```python
# 标签类型
"large"      # 大标题
"subtitle"   # 副标题
"primary"    # 主要文本
"secondary"  # 次要文本
"muted"      # 静音文本
```

### 📊 状态指示器

```python
# 状态类型
"default"     # 默认状态
"secondary"   # 次要状态
"destructive" # 错误状态
"outline"     # 轮廓状态
"success"     # 成功状态
"warning"     # 警告状态
```

### 🎛️ 输入控件

- **文本输入框**: 现代化设计，带焦点环
- **滑块**: 圆形滑块手柄，平滑过渡
- **分组框**: 卡片风格容器
- **分隔符**: 轻量级分割线

## 组件样式预设

### 心动周期组件样式

```python
cardiac_cycle_styles = {
    "phase_percent_label": "主要显示标签",
    "frame_info_label": "次要信息标签", 
    "series_description_label": "静音描述文本",
    "control_button": "轮廓控制按钮",
    "mark_button": "标记操作按钮",
    "slider": "时间轴滑块",
    "container": "卡片容器",
    "section_separator": "分节分隔符"
}
```

### 主界面组件样式

```python
main_ui_styles = {
    "app_title": "应用标题",
    "status_indicator": "状态指示器",
    "nav_hint": "导航提示文本",
    "welcome_label": "欢迎标签",
    "description_label": "描述文本",
    "module_button": "模块导航按钮(支持选中状态)",
    "container_card": "容器卡片"
}
```

## 使用方法

### 1. 基础组件创建

```python
from ui.style_utils import StyledWidget

# 创建样式化按钮
button = StyledWidget.create_button("保存", "default", "default")

# 创建样式化标签
label = StyledWidget.create_label("标题", "large")

# 创建状态指示器
status = StyledWidget.create_status_indicator("就绪", "default")
```

### 2. 推荐的按钮创建方法 ⭐

**推荐使用 `LayoutManager.create_button_with_style()` 方法创建按钮，这是经过验证的最佳实践：**

```python
from utils.layout_manager import LayoutManager

# 主要按钮 - 重要操作（如数据导入、确认等）
primary_button = LayoutManager.create_button_with_style(
    text="数据导入与配置",
    button_type="primary", 
    size="default",
    min_height=40
)

# 次要按钮 - 辅助操作（如刷新、查看等）
secondary_button = LayoutManager.create_button_with_style(
    text="刷新状态",
    button_type="secondary",
    size="default", 
    min_height=35
)

# 危险操作按钮 - 不可逆操作（如删除、重置等）
destructive_button = LayoutManager.create_button_with_style(
    text="重置数据",
    button_type="destructive",
    size="default",
    min_height=35
)

# 轮廓按钮 - 非主要操作
outline_button = LayoutManager.create_button_with_style(
    text="取消",
    button_type="outline",
    size="sm"
)

# 小尺寸按钮
small_button = LayoutManager.create_button_with_style(
    text="编辑",
    button_type="secondary",
    size="sm",
    min_height=30
)

# 大尺寸按钮  
large_button = LayoutManager.create_button_with_style(
    text="开始分析",
    button_type="primary",
    size="lg",
    min_height=50
)
```

**参数说明：**

- `text`: 按钮显示文本
- `button_type`: 按钮类型
  - `"primary"` - 主要按钮（蓝色背景）
  - `"secondary"` - 次要按钮（灰色背景）
  - `"destructive"` - 危险按钮（红色背景）
  - `"outline"` - 轮廓按钮（透明背景，有边框）
  - `"ghost"` - 幽灵按钮（透明背景，无边框）
  - `"link"` - 链接样式按钮
- `size`: 按钮尺寸
  - `"sm"` - 小尺寸（35px 高度）
  - `"default"` - 标准尺寸（40px 高度）
  - `"lg"` - 大尺寸（45px 高度）
- `min_height`: 可选，自定义最小高度（像素）

### 3. 动态更新按钮样式

```python
# 在运行时更新按钮样式
LayoutManager.update_button_style(button, "primary", "default")
LayoutManager.update_button_style(button, "secondary", "default")

# 或在组件内部使用辅助方法
def _update_button_style(self, button, button_type, size="default"):
    LayoutManager.update_button_style(button, button_type, size)
```

### 4. 现有组件样式化

```python
from ui.style_utils import style

# 链式调用应用样式
style(my_button).as_button("primary", "lg")
style(my_label).as_label("subtitle")
style(my_status).as_status_indicator("success")
```

### 5. 组件样式集合应用

```python
from ui.styles import ComponentStyleFactory

# 获取预设样式集合
styles = ComponentStyleFactory.get_cardiac_cycle_styles()

# 应用到具体控件
widget.setStyleSheet(styles["control_button"])
```

### 6. 自定义样式合并

```python
from ui.style_utils import StyleUtils

# 合并自定义属性
custom_style = StyleUtils.create_custom_style(
    base_style,
    {"margin": "10px", "border": "2px solid red"}
)
```

## 可访问性特性

### 🎯 高对比度

- 所有文本与背景对比度 ≥ 4.5:1
- 符合 WCAG 2.1 AA 标准

### 🔍 焦点指示

- 清晰的焦点环：`2px solid #3b82f6`
- 2px 外边距增强可见性

### ⌨️ 键盘导航

- 所有交互元素支持键盘操作
- 逻辑的标签页顺序

### 📱 响应式设计

- rem 单位支持用户字体大小偏好
- 灵活的布局适应不同屏幕尺寸

## 性能优化

### 📦 按需加载

- 模块化样式系统
- 只加载使用的组件样式

### 🎨 CSS 优化

- 最小化样式重复
- 高效的样式继承

### 🔄 缓存友好

- 样式生成结果可缓存
- 减少重复计算

## 维护指南

### 🔧 添加新组件

1. 在 `StyleManager` 中添加样式生成方法
2. 在 `ComponentStyleFactory` 中创建预设集合
3. 在 `StyledWidget` 中添加便捷创建方法

### � 按钮使用最佳实践

**优先使用 `LayoutManager.create_button_with_style()`：**

1. **按钮类型选择指南：**
   - `primary`: 页面主要操作（每个界面最多1-2个）
   - `secondary`: 次要操作、辅助功能
   - `destructive`: 删除、重置等不可逆操作
   - `outline`: 取消、返回等中性操作
   - `ghost`: 工具栏按钮、图标按钮

2. **尺寸使用建议：**
   - `sm`: 工具栏、内嵌操作按钮
   - `default`: 大部分界面按钮
   - `lg`: 重要的入口按钮、主要CTA

3. **高度设置原则：**
   - 重要按钮：40-50px
   - 普通按钮：35-40px  
   - 小按钮：30-35px

4. **代码示例：**

   ```python
   # ✅ 推荐写法
   button = LayoutManager.create_button_with_style(
       text="开始分析",
       button_type="primary", 
       size="default",
       min_height=40
   )
   
   # ❌ 不推荐直接创建
   button = qt.QPushButton("开始分析")
   button.setStyleSheet("...")  # 手动设置样式
   ```

### �🎨 自定义主题

1. 修改 `ThemeColor` 枚举中的颜色值
2. 调整 `FontSize`、`Spacing` 等设计令牌
3. 重新生成组件样式

### 📚 文档更新

- 新组件需要更新本文档
- 提供使用示例和最佳实践

## 项目文件结构

```text
tavi_analytics/ui/
├── styles.py              # 核心样式系统
├── style_utils.py          # 样式工具类  
└── main_ui.py             # 主界面(已应用新样式)

tavi_analytics/module1/
└── cardiac_cycle_widget.py # 心动周期组件(已应用新样式)

文档/
├── SHADCN_UI_MIGRATION_GUIDE.md  # 迁移指南
└── UI_STYLE_SYSTEM_OVERVIEW.md   # 本概览文档
```

## 总结

新的 shadcn/ui 样式系统为 TAVR Analytics 提供了：

✅ **现代化外观**: 专业、简洁的视觉设计  
✅ **一致性**: 统一的设计语言和组件规范  
✅ **可访问性**: 符合 Web 可访问性标准  
✅ **可维护性**: 模块化、可扩展的代码结构  
✅ **开发效率**: 预设样式和便捷工具（如 `LayoutManager.create_button_with_style()`）  
✅ **用户体验**: 直观的交互和视觉反馈  
✅ **标准化**: 统一的按钮创建和样式管理接口

### 🚀 快速开始

创建按钮的推荐方式：

```python
from utils.layout_manager import LayoutManager

# 主要操作按钮
button = LayoutManager.create_button_with_style(
    text="您的按钮文本",
    button_type="primary",  # primary | secondary | destructive | outline
    size="default",         # sm | default | lg  
    min_height=40          # 可选，自定义高度
)
```

这个样式系统为项目的长期发展奠定了坚实的基础，支持未来的功能扩展和主题定制需求。
