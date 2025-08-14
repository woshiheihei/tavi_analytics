"""
轮廓定位模块 (已重构)

该模块已经重构，功能拆分为：
1. 通用MPR平面定位: utils.mpr_positioning.PlanePositionManager
2. 轮廓定位服务: services.contour_positioning_service.ContourPositionService

为了向后兼容，这里提供了旧API的重定向。
建议使用新的API以获得更好的功能分离和扩展性。

新的使用方式:
    # 直接使用平面定位 (底层API)
    from utils.mpr_positioning import get_plane_position_manager
    manager = get_plane_position_manager()
    success = manager.position_to_plane(center, normal)
    
    # 使用轮廓定位 (高层API)
    from services.contour_positioning_service import get_contour_position_service
    service = get_contour_position_service()
    success = service.switch_to_contour('valve_stent_bottom', phase='diastole')

作者：TAVR Research Team
重构时间：2025年8月
"""

import warnings


class ContourPositionManager:
    """
    轮廓定位管理器 (兼容性包装)
    
    警告：此类已废弃，建议使用 services.contour_positioning_service.ContourPositionService
    
    此类提供了与原有API兼容的接口，内部重定向到新的服务架构。
    """
    
    def __init__(self):
        warnings.warn(
            "ContourPositionManager 已废弃，请使用 services.contour_positioning_service.ContourPositionService",
            DeprecationWarning,
            stacklevel=2
        )
        # 延迟导入避免循环依赖
        try:
            from ...services.contour_positioning_service import get_contour_position_service
            self._service = get_contour_position_service()
        except ImportError:
            import os
            import sys
            current_dir = os.path.dirname(__file__)
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from services.contour_positioning_service import get_contour_position_service
            self._service = get_contour_position_service()
    
    def set_current_phase(self, phase):
        """设置当前期像 (兼容性方法)"""
        return self._service.set_current_phase(phase)
    
    def get_current_phase(self):
        """获取当前期像 (兼容性方法)"""
        return self._service.get_current_phase()
    
    def switch_to_contour(self, contour_type, node_name=None, phase=None):
        """一键切换到指定轮廓 (兼容性方法)"""
        return self._service.switch_to_contour(contour_type, node_name, phase)
    
    def get_phase_aware_supported_contours(self, phase=None):
        """获取期像感知的支持轮廓列表 (兼容性方法)"""
        return self._service.get_phase_aware_supported_contours(phase)
    
    def check_phase_contour_availability(self, phase=None):
        """检查轮廓可用性 (兼容性方法)"""
        return self._service.check_phase_contour_availability(phase)
    
    def get_contour_info(self, contour_type, node_name=None, phase=None):
        """获取轮廓信息 (兼容性方法)"""
        return self._service.get_contour_info(contour_type, node_name, phase)


def get_contour_manager():
    """
    获取轮廓定位管理器 (兼容性函数)
    
    警告：此函数已废弃，建议使用：
    from services.contour_positioning_service import get_contour_position_service
    
    Returns:
        ContourPositionManager: 兼容性包装的管理器实例
    """
    warnings.warn(
        "get_contour_manager() 已废弃，请使用 services.contour_positioning_service.get_contour_position_service()",
        DeprecationWarning,
        stacklevel=2
    )
    return ContourPositionManager()


def switch_to_contour(contour_type, node_name=None, phase=None):
    """
    便捷函数：一键切换到指定轮廓 (兼容性函数)
    
    警告：此函数已废弃，建议使用：
    from services.contour_positioning_service import switch_to_contour
    
    Args:
        contour_type: 轮廓类型
        node_name: 自定义节点名称（可选）
        phase: 期像类型（可选）
        
    Returns:
        bool: 切换成功返回True
    """
    warnings.warn(
        "switch_to_contour() 已废弃，请使用 services.contour_positioning_service.switch_to_contour()",
        DeprecationWarning,
        stacklevel=2
    )
    manager = get_contour_manager()
    return manager.switch_to_contour(contour_type, node_name, phase)


# 为了向后兼容，保留原有的导出
__all__ = [
    "ContourPositionManager",
    "get_contour_manager", 
    "switch_to_contour"
]

# 版本信息
__version__ = "1.1.0"  # 重构版本
__author__ = "TAVR Research Team"
__email__ = "tavr@research.team"
