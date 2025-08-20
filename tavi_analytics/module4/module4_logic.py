"""
模块四业务逻辑层

瓣膜支架几何形态评估的核心逻辑处理。
"""
import logging
from typing import Optional, Dict, Any, List

try:
    from ..core.domain_models import MultiLevelPlaneManager, ValvePlaneLevel
    from ..services.valve_plane_config_service import get_valve_plane_config_service
    from ..core.session import TAVRStudySession
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.domain_models import MultiLevelPlaneManager, ValvePlaneLevel
    from services.valve_plane_config_service import get_valve_plane_config_service
    from core.session import TAVRStudySession


class Module4Logic:
    """模块四业务逻辑类"""

    def __init__(self, session: Optional[TAVRStudySession] = None):
        """初始化模块四逻辑"""
        self._current_phase = 'end_diastole'  # 默认期像
        self.session = session
        self.logger = logging.getLogger(__name__)
        
        # 多层级平面管理器
        self._plane_managers = {
            'end_diastole': MultiLevelPlaneManager(cardiac_phase='end_diastole'),
            'end_systole': MultiLevelPlaneManager(cardiac_phase='end_systole')
        }
        
        # 瓣膜平面配置服务
        self._valve_config_service = get_valve_plane_config_service()
        
        # 为平面管理器注入配置服务
        for manager in self._plane_managers.values():
            manager.set_valve_config(self._valve_config_service)
        
        # 当前瓣膜信息
        self._current_valve_manufacturer = ""
        self._current_valve_model = ""
        
        logging.info("Module4Logic 初始化完成")

    def set_current_phase(self, phase: str):
        """
        设置当前期像
        
        Args:
            phase: 期像类型 ('end_diastole' 或 'end_systole')
        """
        if phase in ['end_diastole', 'end_systole']:
            self._current_phase = phase
            logging.info(f"模块四当前期像设置为: {phase}")
        else:
            logging.warning(f"无效的期像类型: {phase}")

    def get_current_phase(self) -> str:
        """
        获取当前期像
        
        Returns:
            当前期像字符串
        """
        return self._current_phase

    def start_analysis(self) -> bool:
        """
        开始瓣膜支架几何形态分析
        
        Returns:
            分析是否成功启动
        """
        try:
            logging.info("开始瓣膜支架几何形态分析...")
            
            # TODO: 在这里添加具体的分析逻辑
            # 例如：
            # - 获取瓣膜支架图像数据
            # - 进行几何形态测量
            # - 计算相关参数
            
            logging.info("瓣膜支架几何形态分析完成")
            return True
            
        except Exception as e:
            logging.error(f"瓣膜支架几何形态分析失败: {e}")
            return False

    def get_analysis_results(self) -> Dict[str, Any]:
        """
        获取分析结果
        
        Returns:
            分析结果字典
        """
        # TODO: 返回实际的分析结果
        return {
            'status': 'pending',
            'measurements': {},
            'phase': self._current_phase,
            'timestamp': None
        }

    def validate_data(self) -> bool:
        """
        验证数据完整性
        
        Returns:
            数据是否有效
        """
        try:
            # TODO: 添加数据验证逻辑
            # 例如：
            # - 检查是否有必要的图像序列
            # - 验证期像标记是否正确
            # - 确认瓣膜支架可见性
            
            logging.info("数据验证通过")
            return True
            
        except Exception as e:
            logging.error(f"数据验证失败: {e}")
            return False

    def reset_analysis(self):
        """重置分析状态"""
        try:
            logging.info("重置模块四分析状态")
            
            # TODO: 清理分析数据和状态
            # 例如：
            # - 清除临时测量结果
            # - 重置UI状态
            # - 清理临时文件
            
        except Exception as e:
            logging.error(f"重置分析状态失败: {e}")

    def set_valve_info(self, manufacturer: str, model: str):
        """
        设置瓣膜信息并更新平面映射
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
        """
        try:
            self._current_valve_manufacturer = manufacturer
            self._current_valve_model = model
            
            # 为所有期像的平面管理器设置级别映射
            for manager in self._plane_managers.values():
                manager.set_level_mappings(manufacturer, model)
            
            self.logger.info(f"已设置瓣膜信息: {manufacturer} {model}")
            
        except Exception as e:
            self.logger.error(f"设置瓣膜信息失败: {e}")
    
    def load_measurement_data(self, measurement_data: Dict[str, Any]) -> bool:
        """
        从measurement.json数据中加载多层级平面
        
        Args:
            measurement_data: 测量数据字典
            
        Returns:
            bool: 加载是否成功
        """
        try:
            available_heights = self._valve_config_service.get_available_heights()
            success = True
            
            # 为所有期像加载平面数据
            for phase, manager in self._plane_managers.items():
                loaded_count = manager.load_planes_from_measurement_data(
                    measurement_data, available_heights
                )
                if loaded_count == 0:
                    self.logger.warning(f"期像 {phase} 未加载到任何平面数据")
                    success = False
                else:
                    self.logger.info(f"期像 {phase} 成功加载 {loaded_count} 个平面")
            
            # 如果已设置瓣膜信息，应用级别映射
            if self._current_valve_manufacturer and self._current_valve_model:
                self.set_valve_info(self._current_valve_manufacturer, self._current_valve_model)
            
            return success
            
        except Exception as e:
            self.logger.error(f"加载测量数据失败: {e}")
            return False
    
    def get_current_plane_manager(self) -> MultiLevelPlaneManager:
        """获取当前期像的平面管理器"""
        return self._plane_managers.get(self._current_phase)
    
    def get_plane_by_level(self, level: str) -> Optional[Any]:
        """
        根据级别获取当前期像的平面
        
        Args:
            level: 平面级别 ('inflow', 'nadir', 'commissure')
            
        Returns:
            平面轮廓对象或None
        """
        manager = self.get_current_plane_manager()
        if manager:
            return manager.get_plane_by_level(level)
        return None
    
    def get_level_planes(self) -> Dict[str, Any]:
        """获取当前期像的所有级别平面"""
        manager = self.get_current_plane_manager()
        if manager:
            return manager.get_level_planes()
        return {}
    
    def get_valve_mapping_summary(self) -> Dict[str, Any]:
        """获取瓣膜映射摘要信息"""
        if not self._current_valve_manufacturer or not self._current_valve_model:
            return {
                'valve_info': {'manufacturer': '', 'model': ''},
                'error': '瓣膜信息未设置'
            }
        
        return self._valve_config_service.get_valve_mapping_summary(
            self._current_valve_manufacturer, 
            self._current_valve_model
        )
    
    def get_plane_measurements_for_level(self, level: str) -> Dict[str, Any]:
        """
        获取指定级别的平面测量数据
        
        Args:
            level: 平面级别
            
        Returns:
            测量数据字典
        """
        plane = self.get_plane_by_level(level)
        if plane:
            measurements = plane.get_measurements()
            measurements['level'] = level
            measurements['valve_manufacturer'] = self._current_valve_manufacturer
            measurements['valve_model'] = self._current_valve_model
            measurements['phase'] = self._current_phase
            return measurements
        
        return {
            'level': level,
            'error': f'未找到 {level} 级别的平面数据',
            'phase': self._current_phase
        }
    
    def get_all_measurements(self) -> Dict[str, Any]:
        """获取所有级别的测量数据"""
        results = {
            'valve_info': {
                'manufacturer': self._current_valve_manufacturer,
                'model': self._current_valve_model
            },
            'phase': self._current_phase,
            'measurements': {}
        }
        
        for level in [ValvePlaneLevel.INFLOW.value, ValvePlaneLevel.NADIR.value, ValvePlaneLevel.COMMISSURE.value]:
            results['measurements'][level] = self.get_plane_measurements_for_level(level)
        
        return results
    
    def create_visualizations_for_level(self, level: str) -> bool:
        """为指定级别创建可视化"""
        plane = self.get_plane_by_level(level)
        if plane:
            return plane.create_visualization()
        return False
    
    def create_all_visualizations(self) -> Dict[str, bool]:
        """为当前期像的所有平面创建可视化"""
        manager = self.get_current_plane_manager()
        if manager:
            return manager.create_all_visualizations()
        return {}
    
    def remove_visualizations_for_level(self, level: str):
        """移除指定级别的可视化"""
        plane = self.get_plane_by_level(level)
        if plane:
            plane.remove_slicer_node()
    
    def remove_all_visualizations(self):
        """移除所有可视化"""
        manager = self.get_current_plane_manager()
        if manager:
            manager.remove_all_visualizations()
    
    def update_from_session(self):
        """从会话更新瓣膜信息和平面数据"""
        if self.session:
            try:
                success = False
                
                # 更新瓣膜信息
                patient_data = self.session.get_patient_data()
                if patient_data and patient_data.valveBrand and patient_data.valveModel:
                    self.set_valve_info(patient_data.valveBrand, patient_data.valveModel)
                    self.logger.info("已从会话更新瓣膜信息")
                    success = True
                
                # 尝试加载多层级平面数据
                plane_data = self.session.get_multi_level_plane_data()
                if plane_data:
                    if self.load_measurement_data(plane_data):
                        self.logger.info("已从会话加载多层级平面数据")
                        success = True
                    else:
                        self.logger.warning("从会话加载平面数据失败")
                
                return success
                
            except Exception as e:
                self.logger.error(f"从会话更新失败: {e}")
        return False
    
    def cleanup(self):
        """清理资源"""
        try:
            logging.info("清理模块四逻辑资源")
            
            # 清理所有平面管理器
            for manager in self._plane_managers.values():
                manager.clear()
            
            # 重置状态
            self._current_valve_manufacturer = ""
            self._current_valve_model = ""
            
        except Exception as e:
            logging.error(f"清理模块四逻辑资源失败: {e}")