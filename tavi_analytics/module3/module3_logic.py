"""
模块三逻辑组件

自动化测量相关算法与流程。
"""
import logging
from typing import Dict, List, Tuple, Optional
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic

# 导入平面定位管理器
try:
    from ..utils.plane_position import get_plane_manager
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from utils.plane_position import get_plane_manager


class Module3Logic(ScriptedLoadableModuleLogic):
    """模块三业务逻辑"""

    def __init__(self) -> None:
        super().__init__()
        self.plane_manager = get_plane_manager()
        logging.info("Module3Logic 初始化完成")
    
    def switch_to_valve_stent_bottom_plane(self) -> bool:
        """
        一键将当前MPR视图切换到ValveStent_Bottom_Plane平面
        
        这是一个简化的接口方法，内部使用 PlanePositionManager 来实现。
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            logging.info("开始切换到ValveStent_Bottom_Plane平面...")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('valve_stent_bottom')
            
            if success:
                logging.info("成功切换到ValveStent_Bottom_Plane平面")
            else:
                logging.error("切换到ValveStent_Bottom_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到ValveStent_Bottom_Plane平面时出错: {e}")
            return False
    
    def switch_to_custom_plane(self, node_name: str) -> bool:
        """
        切换到自定义平面
        
        Args:
            node_name: 自定义平面节点名称
            
        Returns:
            bool: 切换成功返回True
        """
        try:
            logging.info(f"开始切换到自定义平面: {node_name}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('custom', node_name)
            
            if success:
                logging.info(f"成功切换到自定义平面: {node_name}")
            else:
                logging.error(f"切换到自定义平面失败: {node_name}")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到自定义平面时出错: {e}")
            return False
    
    def get_supported_planes(self) -> Dict[str, str]:
        """
        获取支持的平面类型列表
        
        Returns:
            Dict[str, str]: 平面类型到节点名称的映射
        """
        return self.plane_manager.get_supported_planes()
    
    def get_plane_info(self, plane_type: str, node_name: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定平面的详细信息
        
        Args:
            plane_type: 平面类型
            node_name: 自定义节点名称（当plane_type='custom'时使用）
            
        Returns:
            Optional[Dict]: 平面信息字典，包含中心点、法向量等
        """
        return self.plane_manager.get_plane_info(plane_type, node_name)

    def cleanup(self):
        """清理资源"""
        try:
            logging.info("Module3Logic 清理完成")
        except Exception as e:
            logging.error(f"Module3Logic 清理失败: {e}")
