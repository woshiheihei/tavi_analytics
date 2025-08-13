# 期像选择组件使用文档

## 概述

`PhaseSelectionWidget` 是一个可在多个模块间复用的期像选择UI组件，提供舒张末期和收缩末期的切换功能。

## 功能特性

- 🫀 **舒张末期切换**：切换到舒张末期进行分析
- 💓 **收缩末期切换**：切换到收缩末期进行分析  
- 🔄 **自动期像切换**：模块激活时自动切换到指定期像
- 📊 **状态显示**：实时显示期像切换状态
- 🎯 **信号通信**：通过Qt信号与父组件通信

## 使用方法

### 1. 导入组件

```python
from ..widgets.phase_selection_widget import PhaseSelectionWidget
```

### 2. 创建实例

```python
# 在模块初始化时创建期像选择组件
self.phase_selection = PhaseSelectionWidget(session, self)
```

### 3. 连接信号

```python
# 连接期像变更信号
self.phase_selection.phaseChanged.connect(self._on_phase_changed)

# 连接状态更新信号
self.phase_selection.statusUpdated.connect(self._on_phase_status_updated)
```

### 4. 添加到布局

```python
# 将组件添加到界面布局中
layout.addWidget(self.phase_selection)
```

### 5. 实现回调方法

```python
def _on_phase_changed(self, phase: str):
    """期像改变时的回调"""
    logging.info(f"期像已切换到: {phase}")
    # phase 可能的值: 'diastole' (舒张末期) 或 'systole' (收缩末期)

def _on_phase_status_updated(self, status: str):
    """期像状态更新时的回调"""
    logging.debug(f"期像状态更新: {status}")
```

### 6. 模块激活时自动切换

```python
def on_activated(self):
    """模块激活时调用"""
    # 自动激活期像选择，默认切换到舒张末期
    self.phase_selection.auto_activate(preferred_phase='diastole')
    
    # 可选：设置自定义说明文本
    self.phase_selection.set_info_text("您的自定义说明文本")
```

### 7. 获取当前期像

```python
current_phase = self.phase_selection.get_current_phase()
# 返回值: 'diastole', 'systole' 或 None
```

### 8. 设置会话对象

```python
def set_session(self, session):
    self.session = session
    if hasattr(self, 'phase_selection'):
        self.phase_selection.set_session(session)
```

### 9. 清理资源

```python
def cleanup(self):
    if hasattr(self, 'phase_selection'):
        self.phase_selection.cleanup()
```

## 组件API

### 属性

- `current_phase`: 当前选择的期像类型

### 方法

- `get_current_phase()`: 获取当前期像
- `set_current_phase(phase)`: 设置当前期像并更新按钮状态
- `auto_activate(preferred_phase)`: 自动激活并切换到指定期像
- `set_info_text(text)`: 设置说明文本
- `set_session(session)`: 设置会话对象
- `cleanup()`: 清理资源

### 信号

- `phaseChanged(str)`: 期像改变信号，参数为期像类型
- `statusUpdated(str)`: 状态更新信号，参数为状态消息

## 已集成的模块

### 模块二（Module2Widget）

- ✅ 已集成期像选择组件
- ✅ 支持全自动分析的期像切换
- ✅ 默认激活舒张末期

### 模块三（Module3Widget）

- ✅ 已集成期像选择组件
- ✅ 支持测量分析的期像选择
- ✅ 默认激活舒张末期

## 设计原则

1. **可复用性**：组件独立封装，可在多个模块中使用
2. **一致性**：UI样式与项目整体风格保持一致
3. **灵活性**：支持自定义说明文本和首选期像
4. **响应性**：通过信号机制实现与父组件的松耦合通信
5. **可维护性**：集中管理期像切换逻辑，便于维护和更新

## 扩展指南

如需在其他模块中使用此组件，只需：

1. 导入 `PhaseSelectionWidget`
2. 在 `__init__` 中创建实例
3. 连接必要的信号
4. 添加到界面布局
5. 在适当的生命周期方法中调用相应的API

这样就能快速复用期像选择功能，无需重复开发。
