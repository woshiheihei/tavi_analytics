"""
轮廓定位模块

该模块提供完整的轮廓一键定位功能，包括：
- ContourPositionManager: 核心轮廓定位管理器类
- 便捷函数: switch_to_contour(), get_contour_manager()
- 医学标准方向设置
- 多种轮廓类型支持

使用示例:
    from utils.contour_position import switch_to_contour, ContourPositionManager
    
    # 方法1: 使用便捷函数
    success = switch_to_contour('valve_stent_bottom')
    
    # 方法2: 使用管理器实例
    manager = ContourPositionManager()
    success = manager.switch_to_contour('valve_stent_bottom')

作者：TAVR Research Team
创建时间：2025年8月
"""

try:
    from .contour_position_manager import ContourPositionManager, get_contour_manager, switch_to_contour
except ImportError:
    from contour_position_manager import ContourPositionManager, get_contour_manager, switch_to_contour

__all__ = [
    "ContourPositionManager",
    "get_contour_manager", 
    "switch_to_contour"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "TAVR Research Team"
__email__ = "tavr@research.team"
