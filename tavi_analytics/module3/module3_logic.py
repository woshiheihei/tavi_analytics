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
    
    def switch_to_sinus_of_valsalva_plane(self) -> bool:
        """
        一键将当前MPR视图切换到SinusOfValsalva_Plane平面
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            logging.info("开始切换到SinusOfValsalva_Plane平面...")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('sinus_of_valsalva')
            
            if success:
                logging.info("成功切换到SinusOfValsalva_Plane平面")
            else:
                logging.error("切换到SinusOfValsalva_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到SinusOfValsalva_Plane平面时出错: {e}")
            return False
    
    def switch_to_stent_best_fit_plane(self) -> bool:
        """
        一键将当前MPR视图切换到StentBestFit_Plane平面
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            logging.info("开始切换到StentBestFit_Plane平面...")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('stent_best_fit')
            
            if success:
                logging.info("成功切换到StentBestFit_Plane平面")
            else:
                logging.error("切换到StentBestFit_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到StentBestFit_Plane平面时出错: {e}")
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
    
    def switch_to_plane_by_type(self, plane_type: str) -> bool:
        """
        通用平面切换方法
        
        Args:
            plane_type: 平面类型，支持 'valve_stent_bottom', 'sinus_of_valsalva', 'stent_best_fit'
            
        Returns:
            bool: 切换成功返回True
        """
        try:
            logging.info(f"开始切换到{plane_type}平面...")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane(plane_type)
            
            if success:
                logging.info(f"成功切换到{plane_type}平面")
            else:
                logging.error(f"切换到{plane_type}平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到{plane_type}平面时出错: {e}")
            return False
    
    def check_plane_availability(self) -> dict:
        """
        检查所有关键平面的可用性
        
        Returns:
            dict: 各个平面的可用性状态
        """
        try:
            supported_planes = self.plane_manager.get_supported_planes()
            availability = {}
            
            for plane_type, node_name in supported_planes.items():
                if plane_type == 'custom':
                    continue
                    
                if node_name:
                    # 检查节点是否存在
                    import slicer
                    node = slicer.mrmlScene.GetFirstNodeByName(node_name)
                    availability[plane_type] = {
                        'available': node is not None,
                        'node_name': node_name,
                        'node_exists': node is not None
                    }
                    
                    if node:
                        # 获取更多信息
                        plane_info = self.plane_manager.get_plane_info(plane_type)
                        if plane_info:
                            availability[plane_type].update({
                                'num_points': plane_info.get('num_points', 0),
                                'has_geometry': plane_info.get('num_points', 0) >= 3
                            })
                else:
                    availability[plane_type] = {
                        'available': False,
                        'node_name': None,
                        'node_exists': False
                    }
            
            return availability
            
        except Exception as e:
            logging.error(f"检查平面可用性时出错: {e}")
            return {}

    def cleanup(self):
        """清理资源"""
        try:
            logging.info("Module3Logic 清理完成")
        except Exception as e:
            logging.error(f"Module3Logic 清理失败: {e}")
