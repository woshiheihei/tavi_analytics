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
        self.current_phase = None  # 当前期像
        logging.info("Module3Logic 初始化完成")
    
    def set_current_phase(self, phase: str):
        """
        设置当前期像
        
        Args:
            phase: 期像类型 ('diastole', 'systole', 'end_diastole', 'end_systole')
        """
        self.current_phase = phase
        # 同步到平面管理器
        self.plane_manager.set_current_phase(phase)
        logging.info(f"Module3Logic 当前期像设置为: {phase}")
    
    def get_current_phase(self) -> Optional[str]:
        """获取当前期像"""
        return self.current_phase
    
    def switch_to_valve_stent_bottom_plane(self, phase: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到ValveStent_Bottom_Plane平面
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self.current_phase
            logging.info(f"开始切换到ValveStent_Bottom_Plane平面，期像: {use_phase}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('valve_stent_bottom', phase=use_phase)
            
            if success:
                logging.info("成功切换到ValveStent_Bottom_Plane平面")
            else:
                logging.error("切换到ValveStent_Bottom_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到ValveStent_Bottom_Plane平面时出错: {e}")
            return False
    
    def switch_to_sinus_of_valsalva_plane(self, phase: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到SinusOfValsalva_Plane平面
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self.current_phase
            logging.info(f"开始切换到SinusOfValsalva_Plane平面，期像: {use_phase}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('sinus_of_valsalva', phase=use_phase)
            
            if success:
                logging.info("成功切换到SinusOfValsalva_Plane平面")
            else:
                logging.error("切换到SinusOfValsalva_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到SinusOfValsalva_Plane平面时出错: {e}")
            return False
    
    def switch_to_stent_best_fit_plane(self, phase: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到StentBestFit_Plane平面
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self.current_phase
            logging.info(f"开始切换到StentBestFit_Plane平面，期像: {use_phase}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('stent_best_fit', phase=use_phase)
            
            if success:
                logging.info("成功切换到StentBestFit_Plane平面")
            else:
                logging.error("切换到StentBestFit_Plane平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到StentBestFit_Plane平面时出错: {e}")
            return False
    
    def switch_to_custom_plane(self, node_name: str, phase: Optional[str] = None) -> bool:
        """
        切换到自定义平面
        
        Args:
            node_name: 自定义平面节点名称
            phase: 指定期像，如果为None则使用当前期像
            
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self.current_phase
            logging.info(f"开始切换到自定义平面: {node_name}，期像: {use_phase}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane('custom', node_name, phase=use_phase)
            
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
            Dict[str, str]: 平面类型到期像感知节点名称的映射
        """
        return self.plane_manager.get_phase_aware_supported_planes()
    
    def get_plane_info(self, plane_type: str, node_name: Optional[str] = None, phase: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定平面的详细信息
        
        Args:
            plane_type: 平面类型
            node_name: 自定义节点名称（当plane_type='custom'时使用）
            phase: 指定期像，如果为None则使用当前期像
            
        Returns:
            Optional[Dict]: 平面信息字典，包含中心点、法向量等
        """
        use_phase = phase or self.current_phase
        return self.plane_manager.get_plane_info(plane_type, node_name, use_phase)
    
    def switch_to_plane_by_type(self, plane_type: str, phase: Optional[str] = None) -> bool:
        """
        通用平面切换方法
        
        Args:
            plane_type: 平面类型，支持 'valve_stent_bottom', 'sinus_of_valsalva', 'stent_best_fit'
            phase: 指定期像，如果为None则使用当前期像
            
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self.current_phase
            logging.info(f"开始切换到{plane_type}平面，期像: {use_phase}")
            
            # 使用平面定位管理器执行切换
            success = self.plane_manager.switch_to_plane(plane_type, phase=use_phase)
            
            if success:
                logging.info(f"成功切换到{plane_type}平面")
            else:
                logging.error(f"切换到{plane_type}平面失败")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到{plane_type}平面时出错: {e}")
            return False
    
    def check_plane_availability(self, phase: Optional[str] = None) -> dict:
        """
        检查所有关键平面的可用性
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            dict: 各个平面的可用性状态
        """
        try:
            use_phase = phase or self.current_phase
            return self.plane_manager.check_phase_plane_availability(use_phase)
        except Exception as e:
            logging.error(f"检查平面可用性时出错: {e}")
            return {}

    def cleanup(self):
        """清理资源"""
        try:
            logging.info("Module3Logic 清理完成")
        except Exception as e:
            logging.error(f"Module3Logic 清理失败: {e}")
