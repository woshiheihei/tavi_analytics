"""
平面定位模块

该模块提供完整的平面一键定位功能，包括：
- PlanePositionManager: 核心平面定位管理器类
- 便捷函数: switch_to_plane(), get_plane_manager()
- 医学标准方向设置
- 多种平面类型支持

使用示例:
    from utils.plane_position import switch_to_plane, PlanePositionManager
    
    # 方法1: 使用便捷函数
    success = switch_to_plane('valve_stent_bottom')
    
    # 方法2: 使用管理器实例
    manager = PlanePositionManager()
    success = manager.switch_to_plane('valve_stent_bottom')

作者：TAVR Research Team
创建时间：2025年8月
"""

try:
    from .plane_position_manager import PlanePositionManager, get_plane_manager, switch_to_plane
except ImportError:
    from plane_position_manager import PlanePositionManager, get_plane_manager, switch_to_plane

__all__ = [
    "PlanePositionManager",
    "get_plane_manager", 
    "switch_to_plane"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "TAVR Research Team"
__email__ = "tavr@research.team"
