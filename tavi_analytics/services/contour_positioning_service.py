"""
轮廓定位服务

提供高层的轮廓定位API，组合轮廓几何计算和MPR平面定位功能。
这是一个业务服务层，协调领域模型和底层几何操作。
"""

import logging
from typing import Optional, Dict, Any, Union
import numpy as np

# 导入底层的平面定位管理器
try:
    from ..utils.mpr_positioning import get_plane_position_manager
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from utils.mpr_positioning import get_plane_position_manager

# 导入轮廓相关的领域模型
try:
    from ..core.domain_models import (
    CriticalContourType, 
        ContourBase,
    ContourFactory,
    DynamicContourType
    )
except ImportError:
    from core.domain_models import (
    CriticalContourType, 
        ContourBase,
    ContourFactory,
    DynamicContourType
    )


class ContourPositionService:
    """
    轮廓定位服务
    
    提供基于轮廓的MPR视图定位功能，组合了轮廓几何计算和平面定位。
    这是一个高层业务服务，为模块提供轮廓相关的定位API。
    """
    
    # 支持的轮廓类型配置（基础名称）
    SUPPORTED_CONTOURS = {
        'valve_stent_bottom': CriticalContourType.VALVE_STENT_BOTTOM,
        'sinus_of_valsalva': CriticalContourType.SINUS_OF_VALSALVA,
        'custom': None  # 自定义轮廓，需要手动指定节点名称
    }
    
    # 期像后缀映射
    PHASE_SUFFIXES = {
        'diastole': 'End_Diastole',
        'systole': 'End_Systole',
        'end_diastole': 'End_Diastole',
        'end_systole': 'End_Systole'
    }
    
    def __init__(self):
        """初始化轮廓定位服务"""
        self.plane_position_manager = get_plane_position_manager()
        self.current_phase = None
        logging.info("ContourPositionService 初始化完成")
    
    def set_current_phase(self, phase: Optional[str]):
        """
        设置当前期像
        
        Args:
            phase: 期像类型 ('diastole', 'systole', 'end_diastole', 'end_systole')
        """
        self.current_phase = phase
        if phase:
            logging.info(f"ContourPositionService 当前期像设置为: {phase}")
    
    def get_current_phase(self) -> Optional[str]:
        """获取当前期像"""
        return self.current_phase
    
    def switch_to_contour(self, contour_type: Union[str, DynamicContourType], node_name: Optional[str] = None, phase: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到指定轮廓
        
        Args:
            contour_type: 轮廓类型，可以是预置类型键（如 'valve_stent_bottom'）、
                          动态多层级类型对象（DynamicContourType），
                          或其字符串值（如 'Stent_Frame_base_up_0.5_plane'）
            node_name: 自定义节点名称，仅在 contour_type='custom' 时使用
            phase: 期像类型，如果为None则使用当前期像
            
        Returns:
            bool: 切换成功返回True
            
        Examples:
            # 切换到瓣膜支架底轮廓（使用当前期像）
            success = service.switch_to_contour('valve_stent_bottom')
            
            # 切换到特定期像的瓣膜支架底轮廓
            success = service.switch_to_contour('valve_stent_bottom', phase='diastole')
            
            # 切换到自定义轮廓
            success = service.switch_to_contour('custom', 'MyCustomContour')
        """
        try:
            use_phase = phase or self.current_phase
            
            # 1. 获取轮廓实例和几何参数
            center_point, normal_vector = self._get_contour_geometry(contour_type, node_name, use_phase)
            
            if center_point is None or normal_vector is None:
                logging.error(f"无法获取轮廓几何参数: {contour_type}")
                return False
            
            logging.info(f"开始切换到轮廓: {contour_type}，期像: {use_phase}")
            logging.info(f"轮廓中心点: [{center_point[0]:.2f}, {center_point[1]:.2f}, {center_point[2]:.2f}]")
            logging.info(f"轮廓法向量: [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
            
            # 2. 使用底层平面定位管理器执行MPR定位
            success = self.plane_position_manager.position_to_plane(center_point, normal_vector)
            
            if success:
                logging.info(f"成功切换到轮廓: {contour_type}")
                # 在3D视图中短暂显示该轮廓3秒，然后隐藏
                try:
                    import slicer, qt
                    node_to_flash = None
                    # 确定节点名称
                    if (contour_type == 'custom') and node_name:
                        node_to_flash = slicer.mrmlScene.GetFirstNodeByName(node_name)
                    else:
                        # 预置或动态类型
                        type_key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
                        use_phase = phase or self.current_phase
                        if type_key in self.SUPPORTED_CONTOURS:
                            critical_contour_type = self.SUPPORTED_CONTOURS[type_key]
                            contour = ContourFactory.create_contour(critical_contour_type, use_phase)
                            if contour:
                                node_to_flash = slicer.mrmlScene.GetFirstNodeByName(contour.get_node_name())
                        elif CriticalContourType.is_multi_level_plane_type(type_key):
                            contour = ContourFactory.create_contour(type_key, use_phase)
                            if contour:
                                node_to_flash = slicer.mrmlScene.GetFirstNodeByName(contour.get_node_name())

                    if node_to_flash:
                        disp = node_to_flash.GetDisplayNode()
                        if disp:
                            # 先确保节点存在，如不存在则尝试让领域模型创建一次
                            try:
                                disp.SetVisibility(True)
                                if hasattr(disp, 'SetVisibility3D'):
                                    disp.SetVisibility3D(True)
                                if hasattr(disp, 'SetVisibility2D'):
                                    disp.SetVisibility2D(False)
                            except Exception:
                                pass

                            # 使用单次计时器在3秒后隐藏
                            def _hide_after_delay():
                                try:
                                    disp.SetVisibility(False)
                                    if hasattr(disp, 'SetVisibility3D'):
                                        disp.SetVisibility3D(False)
                                except Exception:
                                    pass
                            timer = qt.QTimer()
                            timer.setSingleShot(True)
                            timer.setInterval(3000)
                            # 需要保持引用，避免被GC回收
                            self._last_flash_timer = timer
                            timer.timeout.connect(_hide_after_delay)
                            timer.start()
                except Exception as e:
                    logging.warning(f"切换后闪现轮廓失败: {e}")
            else:
                logging.error(f"切换到轮廓失败: {contour_type}")
            
            return success
            
        except Exception as e:
            logging.error(f"切换到轮廓时出错: {e}")
            return False
    
    def _get_contour_geometry(self, contour_type: Union[str, DynamicContourType], node_name: Optional[str] = None, 
                            phase: Optional[str] = None) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        获取轮廓的几何参数
        
        Args:
            contour_type: 轮廓类型（预置键/动态类型/动态类型字符串）
            node_name: 自定义节点名称
            phase: 期像类型
            
        Returns:
            tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            # 统一获取类型键字符串
            type_key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)

            if type_key == 'custom':
                if not node_name:
                    logging.error("自定义轮廓类型需要提供节点名称")
                    return None, None
                return self._calculate_custom_contour_geometry(node_name)
            
            elif type_key in self.SUPPORTED_CONTOURS:
                critical_contour_type = self.SUPPORTED_CONTOURS[type_key]
                if not critical_contour_type:
                    logging.error(f"不支持的轮廓类型: {type_key}")
                    return None, None
                
                # 创建轮廓实例并计算几何参数
                contour = ContourFactory.create_contour(critical_contour_type, phase)
                if not contour:
                    logging.error(f"无法创建轮廓实例: {type_key}")
                    return None, None
                
                return contour.calculate_plane_parameters()
            
            # 兼容：动态多层级平面类型（例如 'Stent_Frame_base_up_0.5_plane'）
            elif CriticalContourType.is_multi_level_plane_type(type_key):
                # 单一路径：使用领域模型的动态轮廓，交由其自身实现计算逻辑
                use_phase = phase or self.current_phase
                contour = ContourFactory.create_contour(type_key, use_phase)
                if not contour:
                    logging.error(f"无法创建动态轮廓实例: {type_key}")
                    return None, None
                return contour.calculate_plane_parameters()
            
            else:
                logging.error(f"不支持的轮廓类型: {type_key}")
                return None, None
                
        except Exception as e:
            logging.error(f"获取轮廓几何参数时出错: {e}")
            return None, None
    
    def _calculate_custom_contour_geometry(self, node_name: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        计算自定义轮廓的几何参数
        
        Args:
            node_name: 自定义节点名称
            
        Returns:
            tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            import slicer
            
            contour_node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if not contour_node:
                logging.error(f"未找到自定义轮廓节点: {node_name}")
                return None, None
            
            # 使用通用的几何计算方法
            return self._calculate_contour_geometry_from_node(contour_node)
            
        except Exception as e:
            logging.error(f"计算自定义轮廓几何参数时出错: {e}")
            return None, None
    
    def _calculate_contour_geometry_from_node(self, contour_node) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        从轮廓节点计算几何参数（通用方法）
        
        Args:
            contour_node: 轮廓标记点节点
            
        Returns:
            tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            num_points = contour_node.GetNumberOfControlPoints()
            if num_points < 3:
                logging.error(f"标记点数量不足，需要至少3个点，当前有{num_points}个点")
                return None, None
            
            # 获取所有标记点的坐标（RAS坐标系）
            points = []
            for i in range(num_points):
                point = [0.0, 0.0, 0.0]
                contour_node.GetNthControlPointPosition(i, point)
                points.append(point)
            
            points_array = np.array(points)
            logging.debug(f"获取到{num_points}个标记点")
            
            # 1. 计算中心点（所有点的质心）
            center_point = np.mean(points_array, axis=0)
            
            # 2. 使用奇异值分解(SVD)最小二乘法拟合平面
            # 将点相对于中心点进行中心化
            centered_points = points_array - center_point
            
            # 使用SVD找到最佳拟合平面
            # 法向量是最小奇异值对应的方向
            U, S, Vt = np.linalg.svd(centered_points)
            normal_vector = Vt[-1]  # 最后一行是最小奇异值对应的方向
            
            # 确保法向量指向正Z方向（头部方向）
            if normal_vector[2] < 0:
                normal_vector = -normal_vector
            
            # 归一化法向量
            normal_vector = normal_vector / np.linalg.norm(normal_vector)
            
            return center_point, normal_vector
            
        except Exception as e:
            logging.error(f"计算轮廓几何参数时出错: {e}")
            return None, None

    # 删除兜底点集计算方法，统一由领域模型负责
    
    def _get_phase_aware_node_name(self, base_name: str, phase: Optional[str] = None) -> str:
        """
        根据期像生成完整的节点名称
        
        Args:
            base_name: 基础节点名称
            phase: 期像类型，如果为None则使用当前期像
            
        Returns:
            str: 包含期像后缀的完整节点名称
        """
        if not base_name:
            return base_name
            
        use_phase = phase or self.current_phase
        if not use_phase:
            return base_name
            
        phase_suffix = self.PHASE_SUFFIXES.get(use_phase)
        if phase_suffix:
            return f"{base_name}_{phase_suffix}"
        else:
            return base_name
    
    def get_contour_info(self, contour_type: str, node_name: Optional[str] = None, phase: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定轮廓的详细信息
        
        Args:
            contour_type: 轮廓类型
            node_name: 自定义节点名称（当contour_type='custom'时使用）
            phase: 期像类型，如果为None则使用当前期像
            
        Returns:
            Optional[Dict]: 轮廓信息字典，包含中心点、法向量等
        """
        try:
            center_point, normal_vector = self._get_contour_geometry(contour_type, node_name, phase)
            
            if center_point is None or normal_vector is None:
                return None
            
            # 确定实际使用的节点名称
            if contour_type == 'custom':
                actual_node_name = node_name
            else:
                critical_contour_type = self.SUPPORTED_CONTOURS.get(contour_type)
                if critical_contour_type:
                    contour = ContourFactory.create_contour(critical_contour_type, phase)
                    actual_node_name = contour.get_node_name() if contour else None
                else:
                    actual_node_name = None
            
            return {
                'contour_type': contour_type,
                'node_name': actual_node_name,
                'center_point': center_point.tolist(),
                'normal_vector': normal_vector.tolist(),
                'phase': phase or self.current_phase,
                'node_exists': actual_node_name is not None
            }
            
        except Exception as e:
            logging.error(f"获取轮廓信息时出错: {e}")
            return None
    
    def check_phase_contour_availability(self, phase: Optional[str] = None) -> Dict[str, Dict]:
        """
        检查指定期像下所有轮廓的可用性
        
        Args:
            phase: 期像类型，如果为None则使用当前期像
            
        Returns:
            Dict[str, Dict]: 轮廓可用性状态字典
        """
        try:
            availability = {}
            use_phase = phase or self.current_phase
            
            import slicer
            
            for contour_type, critical_contour_type in self.SUPPORTED_CONTOURS.items():
                if contour_type == 'custom':
                    continue
                    
                if critical_contour_type:
                    # 创建轮廓实例以获取节点名称
                    contour = ContourFactory.create_contour(critical_contour_type, use_phase)
                    if contour:
                        node_name = contour.get_node_name()
                        node = slicer.mrmlScene.GetFirstNodeByName(node_name)
                        
                        availability[contour_type] = {
                            'available': node is not None,
                            'node_name': node_name,
                            'node_exists': node is not None,
                            'current_phase': use_phase
                        }
                        
                        if node:
                            try:
                                num_points = node.GetNumberOfControlPoints()
                                availability[contour_type].update({
                                    'num_points': num_points,
                                    'has_geometry': num_points >= 3,
                                    'actual_node_name': node.GetName()
                                })
                            except Exception:
                                availability[contour_type].update({
                                    'num_points': 0,
                                    'has_geometry': False,
                                    'actual_node_name': node_name
                                })
                    else:
                        availability[contour_type] = {
                            'available': False,
                            'node_name': None,
                            'node_exists': False,
                            'current_phase': use_phase
                        }
                else:
                    availability[contour_type] = {
                        'available': False,
                        'node_name': None,
                        'node_exists': False,
                        'current_phase': use_phase
                    }
            
            return availability
            
        except Exception as e:
            logging.error(f"检查轮廓可用性时出错: {e}")
            return {}
    
    def get_supported_contours(self) -> Dict[str, str]:
        """
        获取支持的轮廓类型列表
        
        Returns:
            Dict[str, str]: 轮廓类型到描述的映射
        """
        return {
            'valve_stent_bottom': '瓣膜支架底部轮廓',
            'sinus_of_valsalva': 'Sinus Of Valsalva轮廓',
            'custom': '自定义轮廓'
        }
    
    def get_phase_aware_supported_contours(self, phase: Optional[str] = None) -> Dict[str, str]:
        """
        获取期像感知的支持轮廓列表
        
        Args:
            phase: 期像类型，如果为None则使用当前期像
            
        Returns:
            Dict[str, str]: 轮廓类型到完整节点名称的映射
        """
        result = {}
        use_phase = phase or self.current_phase
        
        for contour_type, critical_contour_type in self.SUPPORTED_CONTOURS.items():
            if contour_type == 'custom':
                result[contour_type] = None
            elif critical_contour_type:
                contour = ContourFactory.create_contour(critical_contour_type, use_phase)
                result[contour_type] = contour.get_node_name() if contour else None
            else:
                result[contour_type] = None
                
        return result


# 全局实例（可选，便于快速使用）
_contour_position_service = None

def get_contour_position_service() -> ContourPositionService:
    """
    获取全局轮廓定位服务实例
    
    Returns:
        ContourPositionService: 轮廓定位服务实例
    """
    global _contour_position_service
    if _contour_position_service is None:
        _contour_position_service = ContourPositionService()
    return _contour_position_service

def switch_to_contour(contour_type: str, node_name: Optional[str] = None, phase: Optional[str] = None) -> bool:
    """
    便捷函数：一键切换到指定轮廓
    
    Args:
        contour_type: 轮廓类型
        node_name: 自定义节点名称（可选）
        phase: 期像类型（可选）
        
    Returns:
        bool: 切换成功返回True
        
    Examples:
        # 切换到瓣膜支架底轮廓（使用服务的当前期像）
        success = switch_to_contour('valve_stent_bottom')
        
        # 切换到特定期像的瓣膜支架底轮廓
        success = switch_to_contour('valve_stent_bottom', phase='diastole')
        
        # 切换到自定义轮廓
        success = switch_to_contour('custom', 'MyCustomContour')
    """
    service = get_contour_position_service()
    return service.switch_to_contour(contour_type, node_name, phase)
