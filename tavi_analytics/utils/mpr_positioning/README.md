# MPR定位模块重构说明

## 重构背景

根据用户的建议，我们对MPR定位功能进行了重要的架构重构，将原本混合在一起的功能按照职责进行了清晰的分离。

## 原有问题

原来的 `ContourPositionManager` 混合了两个不同层次的功能：
1. **底层几何操作**：根据平面参数（原点+法向量）定位MPR
2. **上层业务逻辑**：根据轮廓节点计算几何参数

这违反了单一职责原则，导致：
- 代码职责不清晰
- 复用性差
- 测试困难
- 扩展性受限

## 重构方案

### 新的架构层次

```
┌─────────────────────────────────────┐
│           业务模块 (Module3)         │
│       (高层业务逻辑和工作流)         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      轮廓定位服务 (ContourPositionService)     │
│     (组合服务，协调轮廓和平面定位)     │
└─────────────┬───────────────────────┘
              │
    ┌─────────▼─────────┐    ┌─────────────────────┐
    │   轮廓几何计算     │    │   MPR平面定位       │
    │ (ContourBase)     │    │ (PlanePositionManager) │
    │   (领域模型)      │    │    (通用几何操作)    │
    └───────────────────┘    └─────────────────────┘
```

### 1. PlanePositionManager (通用平面定位)

**位置**: `utils/mpr_positioning/plane_position_manager.py`

**职责**:
- 纯几何操作，不涉及业务概念
- 输入：平面原点 + 法向量
- 输出：配置MPR视图
- 医学标准方向设置
- 高精度平面定位

**特点**:
- 可被任何需要平面定位的功能复用
- 独立测试
- 职责单一

### 2. 轮廓几何计算 (ContourBase)

**位置**: `core/domain_models.py` 中的 `ContourBase` 类

**职责**:
- 属于轮廓领域的业务逻辑
- 输入：轮廓节点（标记点）
- 输出：平面参数（原点+法向量）
- 轮廓相关的几何计算

**特点**:
- 每个轮廓类负责自己的几何计算
- 符合领域驱动设计
- 便于扩展新的轮廓类型

### 3. ContourPositionService (组合服务)

**位置**: `services/contour_positioning_service.py`

**职责**:
- 协调轮廓几何计算和平面定位
- 提供高层业务API
- 期像感知的节点管理
- 业务逻辑编排

**特点**:
- 组合模式，协调底层服务
- 提供便于使用的高层API
- 业务逻辑集中管理

## 重构优势

### 1. 职责分离清晰
- 每个组件只负责自己领域的事情
- 符合单一职责原则
- 代码更易理解和维护

### 2. 复用性大大提升
- `PlanePositionManager` 可以被任何需要平面定位的功能使用
- 不仅限于轮廓定位，也可用于其他几何定位需求

### 3. 测试更容易
- 可以独立测试几何计算
- 可以独立测试MPR定位
- 可以独立测试业务逻辑

### 4. 扩展性更好
- 新增其他类型的平面定位需求时更容易扩展
- 新增轮廓类型时只需实现几何计算方法
- 底层平面定位功能可以支持更多应用场景

## 使用示例

### 直接使用平面定位 (底层API)

```python
from utils.mpr_positioning import get_plane_position_manager
import numpy as np

# 直接根据几何参数定位
manager = get_plane_position_manager()
center = np.array([0.0, 0.0, 50.0])
normal = np.array([0.0, 0.0, 1.0])
success = manager.position_to_plane(center, normal)
```

### 使用轮廓定位 (高层API)

```python
from services.contour_positioning_service import get_contour_position_service

# 根据轮廓定位
service = get_contour_position_service()
success = service.switch_to_contour('valve_stent_bottom', phase='diastole')
```

### 在模块中使用 (业务层)

```python
# Module3Logic 中的用法
def switch_to_valve_stent_bottom_contour(self, phase=None):
    return self.contour_service.switch_to_contour('valve_stent_bottom', phase=phase)
```

## 向后兼容性

- 保持了原有的高层API接口
- Module3Logic 的外部接口保持不变
- 现有的调用代码无需修改

## 文件结构

```
utils/
├── mpr_positioning/           # 新增：通用MPR平面定位
│   ├── __init__.py
│   └── plane_position_manager.py
└── contour_position/          # 保留：原有的轮廓定位（可标记为废弃）
    └── ...

services/
└── contour_positioning_service.py  # 新增：轮廓定位服务

core/
└── domain_models.py          # 更新：增加几何计算方法

module3/
└── module3_logic.py          # 更新：使用新的服务架构
```

## 后续计划

1. **逐步迁移**: 其他模块可以逐步迁移到新的架构
2. **废弃旧代码**: 在确认新架构稳定后，可以废弃原有的 `contour_position` 模块
3. **扩展应用**: `PlanePositionManager` 可以被其他需要平面定位的功能使用
4. **优化性能**: 可以继续优化底层的几何计算和MPR配置

## 总结

这次重构成功地将混合的功能按照职责进行了分离，创建了更清晰、更可维护的架构。新的架构不仅解决了原有的问题，还为将来的扩展和优化奠定了良好的基础。
