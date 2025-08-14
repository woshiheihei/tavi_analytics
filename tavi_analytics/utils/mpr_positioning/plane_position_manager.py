"""
MPR平面定位管理器

专门处理MPR视图的平面定位功能，基于几何参数（原点+法向量）配置切片视图。
这是一个通用的几何操作模块，不涉及具体的业务领域概念，可以被任何需要平面定位的功能复用。

主要功能：
- 根据平面参数（原点+法向量）配置MPR切片视图
- 医学标准方向设置（符合放射学约定）
- 高精度的平面定位（0.01mm精度）
- 多切片协调配置

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
import slicer


class PlanePositionManager:
    """
    MPR平面定位管理器
    
    提供通用的MPR平面定位功能，可以根据几何参数（原点+法向量）将MPR视图
    快速定位到指定平面。这是一个纯几何操作模块，不涉及业务概念。
    """
    
    def __init__(self):
        """初始化平面定位管理器"""
        logging.info("PlanePositionManager 初始化完成")
    
    def position_to_plane(self, center_point: np.ndarray, normal_vector: np.ndarray) -> bool:
        """
        将MPR视图定位到指定平面
        
        Args:
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标，应为单位向量）
            
        Returns:
            bool: 定位成功返回True
            
        Examples:
            # 定位到水平面
            center = np.array([0.0, 0.0, 50.0])
            normal = np.array([0.0, 0.0, 1.0])
            success = manager.position_to_plane(center, normal)
        """
        try:
            # 验证输入参数
            if not self._validate_plane_parameters(center_point, normal_vector):
                return False
            
            # 确保法向量为单位向量
            normal_vector = normal_vector / np.linalg.norm(normal_vector)
            
            logging.info(f"定位到平面 - 中心点: [{center_point[0]:.2f}, {center_point[1]:.2f}, {center_point[2]:.2f}]")
            logging.info(f"定位到平面 - 法向量: [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
            
            # 配置切片节点
            success = self._configure_mpr_slices(center_point, normal_vector)
            
            if success:
                logging.info("MPR平面定位成功")
                return True
            else:
                logging.error("MPR平面定位失败")
                return False
                
        except Exception as e:
            logging.error(f"MPR平面定位时出错: {e}")
            return False
    
    def _validate_plane_parameters(self, center_point: np.ndarray, normal_vector: np.ndarray) -> bool:
        """
        验证平面参数的有效性
        
        Args:
            center_point: 平面中心点
            normal_vector: 平面法向量
            
        Returns:
            bool: 参数有效返回True
        """
        try:
            # 检查中心点
            if center_point is None or len(center_point) != 3:
                logging.error("中心点必须是3维向量")
                return False
            
            if not np.isfinite(center_point).all():
                logging.error("中心点包含无效值（NaN或Inf）")
                return False
            
            # 检查法向量
            if normal_vector is None or len(normal_vector) != 3:
                logging.error("法向量必须是3维向量")
                return False
            
            if not np.isfinite(normal_vector).all():
                logging.error("法向量包含无效值（NaN或Inf）")
                return False
            
            # 检查法向量不为零向量
            norm = np.linalg.norm(normal_vector)
            if norm < 1e-6:
                logging.error("法向量不能为零向量")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"验证平面参数时出错: {e}")
            return False
    
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

    def get_current_plane_parameters(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        获取当前轴状面（主要平面）的几何参数
        
        Returns:
            Optional[Tuple[np.ndarray, np.ndarray]]: (中心点, 法向量) 或 None
        """
        try:
            slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed")
            if not slice_node:
                return None
            
            matrix = slice_node.GetSliceToRAS()
            
            # 提取中心点
            center_point = np.array([
                matrix.GetElement(0, 3),
                matrix.GetElement(1, 3),
                matrix.GetElement(2, 3)
            ])
            
            # 提取法向量（Z轴方向）
            normal_vector = np.array([
                matrix.GetElement(0, 2),
                matrix.GetElement(1, 2),
                matrix.GetElement(2, 2)
            ])
            
            return center_point, normal_vector
            
        except Exception as e:
            logging.error(f"获取当前平面参数时出错: {e}")
            return None


# 全局实例（可选，便于快速使用）
_plane_position_manager = None

def get_plane_position_manager() -> PlanePositionManager:
    """
    获取全局平面定位管理器实例
    
    Returns:
        PlanePositionManager: 平面定位管理器实例
    """
    global _plane_position_manager
    if _plane_position_manager is None:
        _plane_position_manager = PlanePositionManager()
    return _plane_position_manager

def position_to_plane(center_point: np.ndarray, normal_vector: np.ndarray) -> bool:
    """
    便捷函数：将MPR视图定位到指定平面
    
    Args:
        center_point: 平面中心点（RAS坐标）
        normal_vector: 平面法向量（RAS坐标）
        
    Returns:
        bool: 定位成功返回True
        
    Examples:
        # 定位到水平面
        center = np.array([0.0, 0.0, 50.0])
        normal = np.array([0.0, 0.0, 1.0])
        success = position_to_plane(center, normal)
    """
    manager = get_plane_position_manager()
    return manager.position_to_plane(center_point, normal_vector)
