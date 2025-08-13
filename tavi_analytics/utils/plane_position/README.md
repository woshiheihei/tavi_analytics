# 平面定位模块 (Plane Position Module)

## 概述

平面定位模块是TAVI Analytics项目中的一个核心基础组件，提供通用的平面一键定位功能。该模块从模块三中抽离出来，经过重构设计，现在可以在项目的任何地方快速调用，实现MPR视图的精确平面定位。

## 功能特性

### 🎯 核心功能
- **一键平面切换**: 将MPR视图快速切换到指定的解剖平面
- **几何参数计算**: 从标记点自动计算平面中心点和法向量  
- **医学标准方向**: 符合放射学约定的视图方向设置
- **精确定位**: 0.01mm精度的中心点控制

### 🔧 技术特性
- **SVD算法**: 使用奇异值分解最小二乘法拟合平面
- **医学坐标系**: 基于RAS坐标系统(Right-Anterior-Superior)
- **多切片协调**: 轴状面、冠状面、矢状面的同步配置
- **错误处理**: 完善的异常捕获和日志记录

### 📦 设计特性
- **模块化**: 独立的功能组件，易于复用
- **多API**: 提供便捷函数、管理器实例、模块集成等多种使用方式
- **类型安全**: 支持预定义平面类型和自定义平面
- **扩展性**: 轻松添加新的平面类型支持

## 支持的平面类型

| 平面类型 | 节点名称 | 描述 |
|---------|---------|------|
| `valve_stent_bottom` | `ValveStent_Bottom_Plane` | 瓣膜支架底平面 |
| `sinus_of_valsalva` | `SinusOfValsalva_Plane` | 窦管交界平面 |
| `aortic_annulus` | `AorticAnnulus_Plane` | 主动脉瓣环平面 |
| `custom` | 用户指定 | 自定义平面 |

## 使用方法

### 方法1: 便捷函数（推荐用于简单场景）

```python
from utils.plane_position import switch_to_plane

# 切换到瓣膜支架底平面
success = switch_to_plane('valve_stent_bottom')

# 切换到自定义平面
success = switch_to_plane('custom', 'MyCustomPlane')
```

### 方法2: 管理器实例（推荐用于复杂场景）

```python
from utils.plane_position import PlanePositionManager

# 创建管理器实例
manager = PlanePositionManager()

# 获取支持的平面列表
planes = manager.get_supported_planes()

# 获取平面详细信息
info = manager.get_plane_info('valve_stent_bottom')
if info:
    print(f"平面节点: {info['node_name']}")
    print(f"中心点: {info['center_point']}")
    print(f"法向量: {info['normal_vector']}")

# 执行平面切换
success = manager.switch_to_plane('valve_stent_bottom')
```

### 方法3: 全局管理器

```python
from utils.plane_position import get_plane_manager

# 获取全局管理器实例
manager = get_plane_manager()
success = manager.switch_to_plane('valve_stent_bottom')
```

### 方法4: 通过模块三集成（向后兼容）

```python
from module3.module3_logic import Module3Logic

logic = Module3Logic()

# 使用原有方法名
success = logic.switch_to_valve_stent_bottom_plane()

# 使用新的通用方法
success = logic.switch_to_custom_plane('ValveStent_Bottom_Plane')
```

## API 参考

### PlanePositionManager 类

#### 主要方法

```python
def switch_to_plane(self, plane_type: str, node_name: Optional[str] = None) -> bool:
    """
    一键将当前MPR视图切换到指定平面
    
    Args:
        plane_type: 平面类型，支持的类型见 SUPPORTED_PLANES
        node_name: 自定义节点名称，仅在 plane_type='custom' 时使用
        
    Returns:
        bool: 切换成功返回True
    """
```

```python
def get_plane_info(self, plane_type: str, node_name: Optional[str] = None) -> Optional[Dict]:
    """
    获取指定平面的详细信息
    
    Returns:
        Dict: 包含 node_name, center_point, normal_vector, num_points 等信息
    """
```

```python
@staticmethod
def get_supported_planes() -> Dict[str, str]:
    """获取支持的平面类型列表"""
```

#### 返回值示例

```python
# get_plane_info() 返回值示例
{
    'node_name': 'ValveStent_Bottom_Plane',
    'plane_type': 'valve_stent_bottom',
    'center_point': [x, y, z],        # RAS坐标
    'normal_vector': [nx, ny, nz],    # 归一化法向量
    'num_points': 12,                 # 标记点数量
    'node_exists': True               # 节点是否存在
}
```

### 便捷函数

```python
def switch_to_plane(plane_type: str, node_name: Optional[str] = None) -> bool:
    """便捷函数：一键切换到指定平面"""

def get_plane_manager() -> PlanePositionManager:
    """获取全局平面定位管理器实例"""
```

## 技术实现

### 几何算法

1. **平面拟合**: 使用SVD奇异值分解进行最小二乘法平面拟合
2. **中心点计算**: 所有标记点的质心
3. **法向量计算**: 最小奇异值对应的方向向量
4. **方向确定**: 确保法向量指向正Z方向（头部方向）

### 医学标准方向

#### 轴状面 (Axial - Red切片)
- **视角**: 从上往下看的横截面
- **X轴**: 指向患者左侧（符合放射学约定）
- **Y轴**: 指向患者前方
- **Z轴**: 沿着法向量方向

#### 冠状面 (Coronal - Green切片)  
- **视角**: 从前往后看的截面
- **X轴**: 指向患者左侧
- **Y轴**: 指向患者头部
- **Z轴**: 沿着法向量方向

#### 矢状面 (Sagittal - Yellow切片)
- **视角**: 从右侧看向左侧的截面
- **X轴**: 指向患者前方
- **Y轴**: 指向患者头部
- **Z轴**: 沿着法向量方向

### 坐标系统

使用3D Slicer的RAS坐标系：
- **R (Right)**: X轴正方向指向患者右侧
- **A (Anterior)**: Y轴正方向指向患者前方
- **S (Superior)**: Z轴正方向指向患者头部

## 前提条件

1. **节点存在**: 场景中需要存在指定名称的平面节点
2. **标记点数量**: 节点至少包含3个控制点
3. **MPR布局**: 当前处于MPR布局模式
4. **活动数据**: 存在活动的体数据节点

## 错误处理

### 常见错误及解决方案

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| 未找到节点 | 节点名称不存在或拼写错误 | 检查节点名称的准确性 |
| 点数不足 | 控制点少于3个 | 添加更多标记点 |
| 计算失败 | 点共线或数据异常 | 检查点的分布和有效性 |
| 切换失败 | MPR布局问题或数据缺失 | 确认布局和数据状态 |

### 调试方法

```python
# 检查节点是否存在
import slicer
node = slicer.mrmlScene.GetFirstNodeByName("ValveStent_Bottom_Plane")
if node:
    print(f"节点存在，包含 {node.GetNumberOfControlPoints()} 个点")

# 获取详细信息
from utils.plane_position import PlanePositionManager
manager = PlanePositionManager()
info = manager.get_plane_info('valve_stent_bottom')
if info:
    print("平面信息:", info)
else:
    print("无法获取平面信息")
```

## 测试和验证

### 运行测试脚本

```python
# 在3D Slicer Python控制台中执行
exec(open(r'c:\code\python\slicer\tavi_analytics\test_plane_position_refactor.py').read())
```

### 查看使用示例

```python
# 在3D Slicer Python控制台中执行  
exec(open(r'c:\code\python\slicer\tavi_analytics\demo_plane_position_usage.py').read())
```

## 文件结构

```
utils/plane_position/
├── __init__.py                    # 模块初始化和导出
├── plane_position_manager.py      # 核心实现
├── README.md                      # 本文档
└── examples/                      # 使用示例（可选）
    ├── basic_usage.py
    ├── advanced_usage.py
    └── integration_examples.py
```

## 版本历史

### v1.0.0 (2025-08-13)
- 🎉 初始版本发布
- ✅ 从模块三完整抽离平面定位功能
- ✅ 重构为独立可复用组件
- ✅ 提供多种API使用方式
- ✅ 保持向后兼容性
- ✅ 完善的文档和测试

## 后续计划

### v1.1.0 (计划中)
- 🔄 支持更多预定义平面类型
- 🎬 添加平滑的视图切换动画
- 💾 支持平面配置的保存和恢复
- 📊 增加平面质量评估功能

### v1.2.0 (计划中)
- 🧮 支持多种平面拟合算法
- 🔧 批量平面操作功能
- 📈 性能优化和内存管理
- 🌐 国际化支持

## 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-plane-type`)
3. 提交更改 (`git commit -am 'Add new plane type'`)
4. 推送分支 (`git push origin feature/new-plane-type`)
5. 创建 Pull Request

## 许可证

该模块是TAVI Analytics项目的一部分，遵循项目的许可证条款。

## 联系方式

- **项目**: TAVI Analytics
- **团队**: TAVR Research Team
- **创建时间**: 2025年8月
- **维护状态**: 积极维护

---

*该文档随代码更新而更新，如有疑问请查看源代码或联系开发团队。*
