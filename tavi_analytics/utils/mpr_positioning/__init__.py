"""
MPR平面定位模块

提供通用的MPR平面定位功能，基于几何参数（原点+法向量）配置切片视图。
这是一个纯几何操作模块，不涉及具体的业务领域概念。

主要组件：
- PlanePositionManager: 核心平面定位管理器
- plane_position_manager: 便捷的管理器实例获取函数
"""

from .plane_position_manager import PlanePositionManager, get_plane_position_manager

__all__ = ['PlanePositionManager', 'get_plane_position_manager']
