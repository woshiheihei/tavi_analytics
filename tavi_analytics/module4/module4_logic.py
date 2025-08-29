"""
模块四业务逻辑层

瓣膜支架几何形态评估的核心逻辑处理。
重构后使用统一的ContourDataManager管理所有轮廓（包括多层级平面）。
"""
import logging
from typing import Optional, Dict, Any, List

try:
    from ..core.domain_models import ValvePlaneLevel, CriticalContourType, CardiacPhase
    from ..services.valve_plane_config_service import get_valve_plane_config_service
    from ..services.contour_positioning_service import get_contour_position_service
    from ..core.session import TAVRStudySession
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.domain_models import ValvePlaneLevel, CriticalContourType, CardiacPhase
    from services.valve_plane_config_service import get_valve_plane_config_service
    from services.contour_positioning_service import get_contour_position_service
    from core.session import TAVRStudySession


class Module4Logic:
    """模块四业务逻辑类 - 使用统一的轮廓管理系统"""

    def __init__(self, session: Optional[TAVRStudySession] = None):
        """初始化模块四逻辑"""
        self._current_phase = 'end_diastole'  # 默认期像
        self.session = session
        self.logger = logging.getLogger(__name__)
        
        # 瓣膜平面配置服务
        self._valve_config_service = get_valve_plane_config_service()
        
        # 轮廓定位服务
        self.contour_service = get_contour_position_service()
        
        # 当前瓣膜信息
        self._current_valve_manufacturer = ""
        self._current_valve_model = ""
        
        # 注册期像切换监听
        self._setup_phase_listener()
        
        logging.info("Module4Logic 初始化完成（使用统一轮廓管理）")

    def _setup_phase_listener(self):
        """设置期像切换监听"""
        if self.session:
            try:
                # 获取期像管理服务
                phase_service = self.session.get_phase_management_service()
                self.logger.info(f"Module4Logic 获取期像管理服务: {phase_service}")
                
                # 连接期像切换信号
                phase_service.phaseChanged.connect(self._on_phase_changed)
                self.logger.info("Module4Logic 已连接期像切换信号")
                
                # 获取当前期像状态
                current_service_phase = phase_service.get_current_phase()
                self.logger.info(f"Module4Logic 当前服务期像: {current_service_phase}")
                
                # 同步期像到轮廓服务
                self.contour_service.set_current_phase(current_service_phase)
                
            except Exception as e:
                self.logger.error(f"设置期像监听失败: {e}")
                import traceback
                self.logger.error(f"详细错误: {traceback.format_exc()}")
        else:
            self.logger.warning("Module4Logic 无session，跳过期像监听设置")
    
    def _on_phase_changed(self, old_phase: str, new_phase: str):
        """期像切换回调"""
        self.logger.info(f"Module4Logic 收到期像切换信号: {old_phase} -> {new_phase}")
        try:
            # 映射界面期像到内部期像
            phase_mapping = {
                'diastole': 'end_diastole',
                'systole': 'end_systole'
            }
            
            internal_phase = phase_mapping.get(new_phase, 'end_diastole')
            old_internal_phase = self._current_phase
            
            self.logger.info(f"Module4Logic 内部期像映射: {new_phase} -> {internal_phase}")
            
            if internal_phase != self._current_phase:
                self._current_phase = internal_phase
                # 同步到轮廓服务
                self.contour_service.set_current_phase(internal_phase)
                self.logger.info(f"Module4Logic 期像已切换: {old_internal_phase} -> {internal_phase}")
            else:
                self.logger.info(f"Module4Logic 期像无变化，保持: {internal_phase}")
                
        except Exception as e:
            self.logger.error(f"处理期像切换失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")

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
            
            # 通过会话为所有期像的轮廓管理器设置级别映射
            if self.session:
                for phase in ['end_diastole', 'end_systole']:
                    manager = self.session.get_phase_contour_manager(phase)
                    manager.set_valve_level_mappings(manufacturer, model, self._valve_config_service)
            
            self.logger.info(f"已设置瓣膜信息: {manufacturer} {model}")
            
        except Exception as e:
            self.logger.error(f"设置瓣膜信息失败: {e}")
    
    def load_measurement_data(self, measurement_data: Dict[str, Any], phase: Optional[str] = None) -> bool:
        """
        从measurement.json数据中加载多层级平面轮廓
        
        Args:
            measurement_data: 测量数据字典
            phase: 可选，指定仅加载到某一期像（'end_diastole' 或 'end_systole'）；
                   省略表示加载到两期像（向后兼容行为）
            
        Returns:
            bool: 加载是否成功
        """
        try:
            available_heights = self._valve_config_service.get_available_heights()
            success_count = 0
            
            self.logger.info(f"开始加载测量数据，可用高度: {available_heights}")
            self.logger.info(f"数据键: {list(measurement_data.keys()) if measurement_data else 'None'}")
            
            if not self.session:
                self.logger.error("无法加载数据：session未设置")
                return False
            
            # 确定需要加载的期像集合（单期或双期）
            phases_to_load: List[str]
            if phase in ['end_diastole', 'end_systole']:
                phases_to_load = [phase]
            else:
                phases_to_load = ['end_diastole', 'end_systole']
            
            # 为指定期像加载轮廓数据（包括多层级平面）
            for use_phase in phases_to_load:
                try:
                    manager = self.session.get_phase_contour_manager(use_phase)
                    
                    # 使用新的统一加载方法（自动包含多层级平面）
                    if manager.load_from_measurement_json(measurement_data):
                        # 如果自动加载没有包含所有高度，尝试专门加载多层级平面
                        loaded_plane_count = manager.load_multi_level_planes_from_measurement_data(
                            measurement_data, available_heights
                        )
                        self.logger.info(f"期像 {use_phase} 加载了 {loaded_plane_count} 个多层级平面轮廓")
                        success_count += 1
                    else:
                        self.logger.warning(f"期像 {use_phase} 数据加载失败")
                        
                except Exception as e:
                    self.logger.error(f"期像 {use_phase} 加载失败: {e}")
            
            # 至少有一个期像成功加载即认为成功
            success = success_count > 0
            
            if success:
                self.logger.info(f"数据加载完成，{success_count}/2 个期像成功加载数据")
                
                # 如果已设置瓣膜信息，应用级别映射
                if self._current_valve_manufacturer and self._current_valve_model:
                    self.set_valve_info(self._current_valve_manufacturer, self._current_valve_model)
            else:
                self.logger.error("所有期像都未能加载数据")
            
            return success
            
        except Exception as e:
            self.logger.error(f"加载测量数据失败: {e}")
            return False
    
    def get_current_contour_manager(self):
        """获取当前期像的轮廓管理器"""
        if self.session:
            return self.session.get_phase_contour_manager(self._current_phase)
        return None
    
    def get_plane_by_level(self, level: str) -> Optional[Any]:
        """
        根据级别获取当前期像的平面轮廓
        
        Args:
            level: 平面级别 ('inflow', 'nadir', 'commissure')
            
        Returns:
            平面轮廓对象或None
        """
        try:
            manager = self.get_current_contour_manager()
            if manager:
                # 查找该级别对应的多层级平面轮廓
                for plane in manager.get_multi_level_planes():
                    if plane.level_type == level:
                        return plane
            return None
        except Exception as e:
            self.logger.error(f"获取级别平面失败: {e}")
            return None
    
    def get_plane_by_height(self, height: float) -> Optional[Any]:
        """
        根据高度获取当前期像的平面轮廓
        
        Args:
            height: 平面高度 (cm)
            
        Returns:
            平面轮廓对象或None
        """
        try:
            manager = self.get_current_contour_manager()
            if manager:
                return manager.get_multi_level_plane_by_height(height)
            return None
        except Exception as e:
            self.logger.error(f"获取高度平面失败: {e}")
            return None
    
    def get_level_planes(self) -> Dict[str, Any]:
        """获取当前期像的所有级别平面"""
        try:
            manager = self.get_current_contour_manager()
            if manager:
                return manager.get_level_planes()
            return {}
        except Exception as e:
            self.logger.error(f"获取级别平面失败: {e}")
            return {}
    
    def get_available_plane_heights(self) -> List[float]:
        """获取当前期像的所有可用平面高度"""
        try:
            manager = self.get_current_contour_manager()
            if manager:
                return manager.get_available_plane_heights()
            return []
        except Exception as e:
            self.logger.error(f"获取可用高度失败: {e}")
            return []
    
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
    
    #（已移除）显示/隐藏平面可视化相关方法
    
    # ========== 新增：轮廓定位方法（参考module3） ==========
    
    def switch_to_multi_level_plane(self, height: float, phase: Optional[str] = None) -> bool:
        """
        切换到指定高度的多层级平面
        
        Args:
            height: 平面高度 (cm)
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self._current_phase
            plane_type = CriticalContourType.create_multi_level_plane_type(height)
            
            self.logger.info(f"开始切换到多层级平面 {height}cm，期像: {use_phase}")
            
            # 使用轮廓定位服务执行切换
            success = self.contour_service.switch_to_contour(plane_type, phase=use_phase)
            
            if success:
                self.logger.info(f"成功切换到多层级平面 {height}cm")
            else:
                self.logger.error(f"切换到多层级平面 {height}cm 失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"切换到多层级平面时出错: {e}")
            return False
    
    def switch_to_level_plane(self, level: str, phase: Optional[str] = None) -> bool:
        """
        切换到指定级别的平面
        
        Args:
            level: 平面级别 ('inflow', 'nadir', 'commissure')
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            # 首先获取该级别对应的高度
            plane = self.get_plane_by_level(level)
            if not plane:
                self.logger.error(f"未找到级别 {level} 对应的平面")
                return False
            
            # 使用高度进行切换
            return self.switch_to_multi_level_plane(plane.height, phase)
            
        except Exception as e:
            self.logger.error(f"切换到级别平面时出错: {e}")
            return False
    
    def switch_to_valve_stent_bottom_contour(self, phase: Optional[str] = None) -> bool:
        """
        切换到瓣膜支架底部轮廓
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self._current_phase
            self.logger.info(f"开始切换到瓣膜支架底部轮廓，期像: {use_phase}")
            
            # 使用轮廓定位服务执行切换
            success = self.contour_service.switch_to_contour('valve_stent_bottom', phase=use_phase)
            
            if success:
                self.logger.info("成功切换到瓣膜支架底部轮廓")
            else:
                self.logger.error("切换到瓣膜支架底部轮廓失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"切换到瓣膜支架底部轮廓时出错: {e}")
            return False
    
    def switch_to_sinus_of_valsalva_contour(self, phase: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到SinusOfValsalva轮廓
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            use_phase = phase or self._current_phase
            self.logger.info(f"开始切换到SinusOfValsalva轮廓，期像: {use_phase}")
            
            # 使用轮廓定位服务执行切换
            success = self.contour_service.switch_to_contour('sinus_of_valsalva', phase=use_phase)
            
            if success:
                self.logger.info("成功切换到SinusOfValsalva轮廓")
            else:
                self.logger.error("切换到SinusOfValsalva轮廓失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"切换到SinusOfValsalva轮廓时出错: {e}")
            return False
    
    # 兼容方法：与module3保持API一致
    def switch_to_sinus_of_valsalva_plane(self, phase: Optional[str] = None) -> bool:
        """兼容方法：调用新的轮廓方法"""
        return self.switch_to_sinus_of_valsalva_contour(phase)
    
    def get_supported_contours(self) -> Dict[str, str]:
        """
        获取支持的轮廓类型列表
        
        Returns:
            Dict[str, str]: 轮廓类型到期像感知节点名称的映射
        """
        return self.contour_service.get_phase_aware_supported_contours()
    
    def get_contour_info(self, contour_type: str, node_name: Optional[str] = None, phase: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定轮廓的详细信息
        
        Args:
            contour_type: 轮廓类型
            node_name: 自定义节点名称（当contour_type='custom'时使用）
            phase: 指定期像，如果为None则使用当前期像
            
        Returns:
            Optional[Dict]: 轮廓信息字典，包含中心点、法向量等
        """
        use_phase = phase or self._current_phase
        return self.contour_service.get_contour_info(contour_type, node_name, use_phase)
    
    def check_contour_availability(self, phase: Optional[str] = None) -> dict:
        """
        检查所有关键轮廓的可用性
        
        Args:
            phase: 指定期像，如果为None则使用当前期像
        
        Returns:
            dict: 各个轮廓的可用性状态
        """
        try:
            use_phase = phase or self._current_phase
            return self.contour_service.check_phase_contour_availability(use_phase)
        except Exception as e:
            self.logger.error(f"检查轮廓可用性时出错: {e}")
            return {}
    
    def get_multi_level_plane_summary(self) -> Dict[str, Any]:
        """获取多层级平面摘要信息"""
        try:
            manager = self.get_current_contour_manager()
            if not manager:
                return {'error': '无法获取轮廓管理器'}
            
            planes = manager.get_multi_level_planes()
            available_heights = manager.get_available_plane_heights()
            level_planes = manager.get_level_planes()
            
            return {
                'phase': self._current_phase,
                'total_planes': len(planes),
                'available_heights': available_heights,
                'level_mappings': {
                    level: plane.height if plane else None 
                    for level, plane in level_planes.items()
                },
                'valve_info': {
                    'manufacturer': self._current_valve_manufacturer,
                    'model': self._current_valve_model
                }
            }
        except Exception as e:
            self.logger.error(f"获取多层级平面摘要失败: {e}")
            return {'error': str(e)}
    
    def update_from_session(self):
        """从会话更新瓣膜信息和轮廓数据"""
        if self.session:
            try:
                success = False
                
                # 重新设置期像监听
                self._setup_phase_listener()
                
                # 更新瓣膜信息
                patient_data = self.session.get_patient_data()
                if patient_data and patient_data.valveBrand and patient_data.valveModel:
                    self.set_valve_info(patient_data.valveBrand, patient_data.valveModel)
                    self.logger.info("已从会话更新瓣膜信息")
                    success = True
                
                # 从会话的轮廓仓库获取多层级平面数据
                try:
                    contour_repository = self.session.get_contour_repository()
                    if contour_repository:
                        # 检查是否有多层级平面数据
                        for phase in ['end_diastole', 'end_systole']:
                            manager = contour_repository.get_manager(phase)
                            planes = manager.get_multi_level_planes()
                            if planes:
                                self.logger.info(f"从会话获取到期像 {phase} 的 {len(planes)} 个多层级平面")
                                success = True
                    else:
                        self.logger.warning("会话中未找到轮廓仓库")
                        
                except Exception as e:
                    self.logger.error(f"从会话获取轮廓数据失败: {e}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"从会话更新失败: {e}")
        return False
    
    def cleanup(self):
        """清理资源"""
        try:
            logging.info("清理模块四逻辑资源")
            # 目前无可视化资源需要统一清理
            
            # 重置状态
            self._current_valve_manufacturer = ""
            self._current_valve_model = ""
            
        except Exception as e:
            logging.error(f"清理模块四逻辑资源失败: {e}")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象并重新建立期像监听"""
        old_session = self.session
        self.session = session
        if old_session != session:
            self.logger.info("Module4Logic session已更新，重新设置期像监听")
            self._setup_phase_listener()