"""
平面定位管理器

该模块提供通用的平面一键定位功能，包括：
- 从标记点计算平面几何参数
- 配置MPR切片视图方向
- 医学标准方向设置
- 精确的中心点定位

主要用于将MPR视图快速切换到指定的解剖平面，支持多种平面类型。

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import slicer


class PlanePositionManager:
    """
    平面定位管理器
    
    提供通用的平面一键定位功能，可以将MPR视图快速切换到指定的解剖平面。
    支持从标记点自动计算平面参数，并按医学标准设置视图方向。
    """
    
    # 支持的平面类型配置
    SUPPORTED_PLANES = {
        'valve_stent_bottom': 'ValveStent_Bottom_Plane',
        'sinus_of_valsalva': 'SinusOfValsalva_Plane',
        'stent_best_fit': 'StentBestFit_Plane',
        'aortic_annulus': 'AorticAnnulus_Plane',
        'custom': None  # 自定义平面，需要手动指定节点名称
    }
    
    def __init__(self):
        """初始化平面定位管理器"""
        logging.info("PlanePositionManager 初始化完成")
    
    def switch_to_plane(self, plane_type: str, node_name: Optional[str] = None) -> bool:
        """
        一键将当前MPR视图切换到指定平面
        
        Args:
            plane_type: 平面类型，支持的类型见 SUPPORTED_PLANES
            node_name: 自定义节点名称，仅在 plane_type='custom' 时使用
            
        Returns:
            bool: 切换成功返回True
            
        Examples:
            # 切换到瓣膜支架底平面
            success = manager.switch_to_plane('valve_stent_bottom')
            
            # 切换到自定义平面
            success = manager.switch_to_plane('custom', 'MyCustomPlane')
        """
        try:
            # 1. 确定节点名称
            if plane_type == 'custom':
                if not node_name:
                    logging.error("自定义平面类型需要提供节点名称")
                    return False
                target_node_name = node_name
            elif plane_type in self.SUPPORTED_PLANES:
                target_node_name = self.SUPPORTED_PLANES[plane_type]
                if not target_node_name:
                    logging.error(f"不支持的平面类型: {plane_type}")
                    return False
            else:
                logging.error(f"不支持的平面类型: {plane_type}")
                return False
            
            # 2. 获取平面节点
            plane_node = slicer.mrmlScene.GetFirstNodeByName(target_node_name)
            if not plane_node:
                logging.error(f"未找到平面节点: {target_node_name}")
                return False
            
            logging.info(f"开始切换到平面: {target_node_name}")
            
            # 3. 计算平面的中心点和法向量
            center_point, normal_vector = self._calculate_plane_geometry(plane_node)
            if center_point is None or normal_vector is None:
                logging.error("无法计算平面几何参数")
                return False
            
            logging.info(f"平面中心点: [{center_point[0]:.2f}, {center_point[1]:.2f}, {center_point[2]:.2f}]")
            logging.info(f"平面法向量: [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
            
            # 4. 配置切片节点
            success = self._configure_mpr_slices(center_point, normal_vector)
            
            if success:
                logging.info(f"成功切换到平面: {target_node_name}")
                return True
            else:
                logging.error(f"切换到平面失败: {target_node_name}")
                return False
                
        except Exception as e:
            logging.error(f"切换到平面时出错: {e}")
            return False
    
    def _calculate_plane_geometry(self, plane_node) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        从平面节点的标记点计算平面几何参数
        
        Args:
            plane_node: 平面标记点节点
            
        Returns:
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            num_points = plane_node.GetNumberOfControlPoints()
            if num_points < 3:
                logging.error(f"标记点数量不足，需要至少3个点，当前有{num_points}个点")
                return None, None
            
            # 获取所有标记点的坐标（RAS坐标系）
            points = []
            for i in range(num_points):
                point = [0.0, 0.0, 0.0]
                plane_node.GetNthControlPointPosition(i, point)
                points.append(point)
            
            points_array = np.array(points)
            logging.info(f"获取到{num_points}个标记点")
            
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
            logging.error(f"计算平面几何参数时出错: {e}")
            return None, None
    
    def _configure_mpr_slices(self, center_point: np.ndarray, normal_vector: np.ndarray) -> bool:
        """
        配置MPR切片视图以显示指定平面
        
        Args:
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）
            
        Returns:
            bool: 配置成功返回True
        """
        try:
            # 获取三个标准切片节点
            slice_nodes = {
                'axial': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed"),      # 轴状面（红色）
                'coronal': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen"),  # 冠状面（绿色）
                'sagittal': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow") # 矢状面（黄色）
            }
            
            if not all(slice_nodes.values()):
                logging.error("无法获取标准切片节点")
                return False
            
            # 1. 设置轴状面为目标平面
            self._set_slice_orientation(
                slice_nodes['axial'], center_point, normal_vector, "axial"
            )
            
            # 2. 计算与主平面垂直的两个方向向量
            # 选择参考向量计算垂直方向
            if abs(normal_vector[2]) < 0.9:  
                reference_vector = np.array([0, 0, 1])  # Z轴作为参考
            else:
                reference_vector = np.array([1, 0, 0])  # X轴作为参考
            
            # 计算第一个垂直方向（冠状面用）
            perpendicular1 = np.cross(normal_vector, reference_vector)
            perpendicular1 = perpendicular1 / np.linalg.norm(perpendicular1)
            
            # 计算第二个垂直方向（矢状面用）
            perpendicular2 = np.cross(normal_vector, perpendicular1)
            perpendicular2 = perpendicular2 / np.linalg.norm(perpendicular2)
            
            # 3. 设置冠状面和矢状面与主平面垂直
            self._set_slice_orientation(
                slice_nodes['coronal'], center_point, perpendicular1, "coronal"
            )
            
            self._set_slice_orientation(
                slice_nodes['sagittal'], center_point, perpendicular2, "sagittal"
            )
            
            # 4. 刷新所有视图
            self._refresh_slice_views()
            
            # 5. 验证切片中心点设置
            self._verify_slice_centers(center_point, slice_nodes)
            
            return True
            
        except Exception as e:
            logging.error(f"配置MPR切片时出错: {e}")
            return False
    
    def _set_slice_orientation(self, slice_node, center_point: np.ndarray, 
                             normal_vector: np.ndarray, slice_type: str):
        """
        设置单个切片的方向和位置（符合医学标准）
        
        Args:
            slice_node: 切片节点
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）  
            slice_type: 切片类型 ('axial', 'coronal', 'sagittal')
        """
        try:
            # 根据切片类型应用医学标准方向
            if slice_type == "axial":
                self._set_axial_orientation(slice_node, center_point, normal_vector)
            elif slice_type == "coronal":
                self._set_coronal_orientation(slice_node, center_point, normal_vector)
            elif slice_type == "sagittal":
                self._set_sagittal_orientation(slice_node, center_point, normal_vector)
            else:
                # 默认通用方向设置
                self._set_generic_orientation(slice_node, center_point, normal_vector)
            
            logging.debug(f"已设置{slice_node.GetName()}的医学标准方向")
            
        except Exception as e:
            logging.error(f"设置切片方向时出错: {e}")
    
    def _set_axial_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray):
        """设置轴位/横断面（Axial）的医学标准方向。

        标准观察方向：从患者足侧向头侧看。
        图像上方=Anterior，图像下方=Posterior，图像左侧=Right，图像右侧=Left。
        """
        try:
            # 轴位：从足侧向头侧看的横断面
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：指向患者左侧（-R方向），在图像中显示为右侧（符合放射学约定）
            x_axis = np.array([-1, 0, 0])  # 指向Left（-R）
            
            # 如果法向量与X轴近似平行，选择其他参考向量
            if abs(np.dot(z_axis, x_axis)) > 0.9:
                x_axis = np.array([0, 1, 0])  # 指向Anterior
            
            # 计算实际的X轴（垂直于法向量）
            x_axis = x_axis - np.dot(x_axis, z_axis) * z_axis
            x_axis = x_axis / np.linalg.norm(x_axis)

            # 强制X轴朝向 -R（以保持左右显示的一致性）
            if np.dot(x_axis, np.array([-1, 0, 0])) < 0:
                x_axis = -x_axis
            
            # Y轴：通过叉积计算（确保右手系），应指向 +A（图像上方=Anterior）
            y_axis = np.cross(x_axis, z_axis)
            y_axis = y_axis / np.linalg.norm(y_axis)

            # 若Y未朝向 +A，则同时翻转X和Y以保持右手系且满足Top=Anterior
            if np.dot(y_axis, np.array([0, 1, 0])) < 0:
                x_axis = -x_axis
                y_axis = -y_axis
            
            # 构建并应用变换矩阵
            self._apply_transformation_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置轴状面方向时出错: {e}")
    
    def _set_coronal_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray):
        """设置冠状位/额状面（Coronal）的医学标准方向。

        标准观察方向：从患者前方向后方看。
        图像上方=Superior，图像下方=Inferior，图像左侧=Right，图像右侧=Left。
        """
        try:
            # 冠状位：从前往后看的截面
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：指向患者左侧
            x_axis = np.array([-1, 0, 0])  # 指向Left
            
            # 如果法向量与X轴近似平行，选择其他参考向量
            if abs(np.dot(z_axis, x_axis)) > 0.9:
                x_axis = np.array([0, 0, 1])  # 指向Superior
            
            # 计算实际的X轴（垂直于法向量）
            x_axis = x_axis - np.dot(x_axis, z_axis) * z_axis
            x_axis = x_axis / np.linalg.norm(x_axis)
            
            # Y轴：应该指向头部方向
            y_axis = np.cross(z_axis, x_axis)
            y_axis = y_axis / np.linalg.norm(y_axis)
            
            # 确保Y轴指向Superior方向
            if np.dot(y_axis, np.array([0, 0, 1])) < 0:
                y_axis = -y_axis
            
            # 构建并应用变换矩阵
            self._apply_transformation_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置冠状面方向时出错: {e}")
    
    def _set_sagittal_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray):
        """设置矢状位（Sagittal）的医学标准方向。

        标准观察方向：从患者左侧向右侧看。
        图像上方=Superior，图像下方=Inferior，图像左侧=Anterior，图像右侧=Posterior。
        """
        try:
            # 矢状位：从左侧向右侧看的截面
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：应指向 -A（确保图像左侧=Anterior，右侧=Posterior）
            x_axis = np.array([0, -1, 0])  # 指向 -Anterior
            
            # 如果法向量与X轴近似平行，选择其他参考向量
            if abs(np.dot(z_axis, x_axis)) > 0.9:
                x_axis = np.array([0, 0, 1])  # 指向Superior
            
            # 计算实际的X轴（垂直于法向量）
            x_axis = x_axis - np.dot(x_axis, z_axis) * z_axis
            x_axis = x_axis / np.linalg.norm(x_axis)
            
            # Y轴：应该指向头部方向
            y_axis = np.cross(z_axis, x_axis)
            y_axis = y_axis / np.linalg.norm(y_axis)
            
            # 确保Y轴指向Superior方向
            if np.dot(y_axis, np.array([0, 0, 1])) < 0:
                y_axis = -y_axis
            
            # 构建并应用变换矩阵
            self._apply_transformation_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置矢状面方向时出错: {e}")
    
    def _set_generic_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray):
        """设置通用方向（原有逻辑）"""
        try:
            # 计算与法向量垂直的两个正交向量
            if abs(normal_vector[0]) < 0.9:
                ref = np.array([1, 0, 0])
            elif abs(normal_vector[1]) < 0.9:
                ref = np.array([0, 1, 0])
            else:
                ref = np.array([0, 0, 1])
            
            # 计算两个正交的切线向量
            u_vector = np.cross(normal_vector, ref)
            u_vector = u_vector / np.linalg.norm(u_vector)
            
            v_vector = np.cross(normal_vector, u_vector)
            v_vector = v_vector / np.linalg.norm(v_vector)
            
            # 构建并应用变换矩阵
            self._apply_transformation_matrix(slice_node, center_point, u_vector, v_vector, normal_vector)
            
        except Exception as e:
            logging.error(f"设置通用方向时出错: {e}")
    
    def _apply_transformation_matrix(self, slice_node, center_point: np.ndarray, 
                                   x_axis: np.ndarray, y_axis: np.ndarray, z_axis: np.ndarray):
        """构建并应用变换矩阵"""
        try:
            # 构建4x4变换矩阵
            transform_matrix = np.eye(4)
            
            # 设置旋转部分（前3x3）
            transform_matrix[0:3, 0] = x_axis    # X方向
            transform_matrix[0:3, 1] = y_axis    # Y方向  
            transform_matrix[0:3, 2] = z_axis    # Z方向（法向量）
            
            # 设置平移部分（第4列前3行）
            transform_matrix[0:3, 3] = center_point
            
            # 转换为VTK矩阵
            vtk_matrix = slicer.util.vtkMatrixFromArray(transform_matrix)
            
            # 设置切片方向为Reformat模式
            slice_node.SetOrientation("Reformat")
            
            # 应用变换矩阵
            slice_node.GetSliceToRAS().DeepCopy(vtk_matrix)
            slice_node.UpdateMatrices()
            
        except Exception as e:
            logging.error(f"应用变换矩阵时出错: {e}")
    
    def _refresh_slice_views(self):
        """刷新所有切片视图"""
        try:
            layout_manager = slicer.app.layoutManager()
            for slice_name in ["Red", "Green", "Yellow"]:
                slice_widget = layout_manager.sliceWidget(slice_name)
                if slice_widget:
                    slice_logic = slice_widget.sliceLogic()
                    if slice_logic:
                        slice_logic.FitSliceToAll()
        except Exception as e:
            logging.error(f"刷新切片视图时出错: {e}")
    
    def _verify_slice_centers(self, target_center: np.ndarray, slice_nodes: Dict):
        """
        验证并修正所有切片的中心点位置
        
        Args:
            target_center: 目标中心点（RAS坐标）
            slice_nodes: 切片节点字典
        """
        try:
            logging.debug("验证切片中心点位置:")
            
            for slice_type, slice_node in slice_nodes.items():
                if slice_node:
                    matrix = slice_node.GetSliceToRAS()
                    current_center = np.array([
                        matrix.GetElement(0, 3),
                        matrix.GetElement(1, 3),
                        matrix.GetElement(2, 3)
                    ])
                    
                    deviation = np.linalg.norm(current_center - target_center)
                    logging.debug(f"  {slice_type}切片中心点偏差: {deviation:.3f}mm")
                    
                    # 如果偏差较大，进行修正
                    if deviation > 0.01:  # 0.01mm精度阈值
                        logging.debug(f"  修正{slice_type}切片中心点...")
                        matrix.SetElement(0, 3, target_center[0])
                        matrix.SetElement(1, 3, target_center[1])
                        matrix.SetElement(2, 3, target_center[2])
                        slice_node.UpdateMatrices()
            
        except Exception as e:
            logging.error(f"验证切片中心点时出错: {e}")
    
    @staticmethod
    def get_supported_planes() -> Dict[str, str]:
        """
        获取支持的平面类型列表
        
        Returns:
            Dict[str, str]: 平面类型到节点名称的映射
        """
        return PlanePositionManager.SUPPORTED_PLANES.copy()
    
    def get_plane_info(self, plane_type: str, node_name: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定平面的详细信息
        
        Args:
            plane_type: 平面类型
            node_name: 自定义节点名称（当plane_type='custom'时使用）
            
        Returns:
            Optional[Dict]: 平面信息字典，包含中心点、法向量等
        """
        try:
            # 确定节点名称
            if plane_type == 'custom':
                if not node_name:
                    return None
                target_node_name = node_name
            elif plane_type in self.SUPPORTED_PLANES:
                target_node_name = self.SUPPORTED_PLANES[plane_type]
                if not target_node_name:
                    return None
            else:
                return None
            
            # 获取平面节点
            plane_node = slicer.mrmlScene.GetFirstNodeByName(target_node_name)
            if not plane_node:
                return None
            
            # 计算平面几何参数
            center_point, normal_vector = self._calculate_plane_geometry(plane_node)
            if center_point is None or normal_vector is None:
                return None
            
            return {
                'node_name': target_node_name,
                'plane_type': plane_type,
                'center_point': center_point.tolist(),
                'normal_vector': normal_vector.tolist(),
                'num_points': plane_node.GetNumberOfControlPoints(),
                'node_exists': True
            }
            
        except Exception as e:
            logging.error(f"获取平面信息时出错: {e}")
            return None


# 全局实例（可选，便于快速使用）
_plane_manager = None

def get_plane_manager() -> PlanePositionManager:
    """
    获取全局平面定位管理器实例
    
    Returns:
        PlanePositionManager: 平面定位管理器实例
    """
    global _plane_manager
    if _plane_manager is None:
        _plane_manager = PlanePositionManager()
    return _plane_manager

def switch_to_plane(plane_type: str, node_name: Optional[str] = None) -> bool:
    """
    便捷函数：一键切换到指定平面
    
    Args:
        plane_type: 平面类型
        node_name: 自定义节点名称（可选）
        
    Returns:
        bool: 切换成功返回True
        
    Examples:
        # 切换到瓣膜支架底平面
        success = switch_to_plane('valve_stent_bottom')
        
        # 切换到自定义平面
        success = switch_to_plane('custom', 'MyCustomPlane')
    """
    manager = get_plane_manager()
    return manager.switch_to_plane(plane_type, node_name)
