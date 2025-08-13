"""
模块三逻辑组件

自动化测量相关算法与流程。
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
import slicer


class Module3Logic(ScriptedLoadableModuleLogic):
    """模块三业务逻辑"""

    def __init__(self) -> None:
        super().__init__()
        logging.info("Module3Logic 初始化完成")
    
    def switch_to_valve_stent_bottom_plane(self) -> bool:
        """
        一键将当前MPR视图切换到ValveStent_Bottom_Plane平面
        
        将轴状面切换到ValveStent_Bottom_Plane平面，
        矢状面和冠状面与之垂直相交，
        中心点定位在平面闭合曲线的平均中心点。
        
        Returns:
            bool: 切换成功返回True
        """
        try:
            # 1. 获取ValveStent_Bottom_Plane节点
            valve_stent_node = slicer.mrmlScene.GetFirstNodeByName("ValveStent_Bottom_Plane")
            if not valve_stent_node:
                logging.error("未找到ValveStent_Bottom_Plane节点")
                return False
            
            # 2. 计算平面的中心点和法向量
            center_point, normal_vector = self._calculate_plane_center_and_normal(valve_stent_node)
            if center_point is None or normal_vector is None:
                logging.error("无法计算平面中心点或法向量")
                return False
            
            logging.info(f"平面中心点: {center_point}")
            logging.info(f"平面法向量: {normal_vector}")
            
            # 3. 设置切片节点的方向和位置
            success = self._configure_slice_nodes_for_valve_plane(center_point, normal_vector)
            
            if success:
                logging.info("成功切换到ValveStent_Bottom_Plane平面")
                return True
            else:
                logging.error("切换到ValveStent_Bottom_Plane平面失败")
                return False
                
        except Exception as e:
            logging.error(f"切换到ValveStent_Bottom_Plane平面时出错: {e}")
            return False
    
    def _calculate_plane_center_and_normal(self, valve_stent_node) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        从ValveStent_Bottom_Plane节点的点云计算平面中心点和法向量
        
        Args:
            valve_stent_node: ValveStent_Bottom_Plane节点
            
        Returns:
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            num_points = valve_stent_node.GetNumberOfControlPoints()
            if num_points < 3:
                logging.error(f"点数不足，需要至少3个点，当前有{num_points}个点")
                return None, None
            
            # 获取所有点的坐标（RAS坐标系）
            points = []
            for i in range(num_points):
                point = [0.0, 0.0, 0.0]
                valve_stent_node.GetNthControlPointPosition(i, point)
                points.append(point)
            
            points_array = np.array(points)
            logging.info(f"获取到{num_points}个点，坐标范围: X[{points_array[:, 0].min():.1f}, {points_array[:, 0].max():.1f}], Y[{points_array[:, 1].min():.1f}, {points_array[:, 1].max():.1f}], Z[{points_array[:, 2].min():.1f}, {points_array[:, 2].max():.1f}]")
            
            # 1. 计算中心点（所有点的平均值）
            center_point = np.mean(points_array, axis=0)
            
            # 2. 通过最小二乘法拟合平面来计算法向量
            # 将点相对于中心点进行中心化
            centered_points = points_array - center_point
            
            # 使用SVD来找到最佳拟合平面
            # 法向量是奇异值最小的方向
            U, S, Vt = np.linalg.svd(centered_points)
            normal_vector = Vt[-1]  # 最后一行是最小奇异值对应的方向
            
            # 确保法向量指向正Z方向（向上）
            if normal_vector[2] < 0:
                normal_vector = -normal_vector
            
            # 归一化法向量
            normal_vector = normal_vector / np.linalg.norm(normal_vector)
            
            logging.info(f"计算得到中心点: [{center_point[0]:.2f}, {center_point[1]:.2f}, {center_point[2]:.2f}]")
            logging.info(f"计算得到法向量: [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
            
            return center_point, normal_vector
            
        except Exception as e:
            logging.error(f"计算平面中心点和法向量时出错: {e}")
            return None, None
    
    def _configure_slice_nodes_for_valve_plane(self, center_point: np.ndarray, normal_vector: np.ndarray) -> bool:
        """
        配置切片节点以显示ValveStent_Bottom_Plane平面
        
        Args:
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）
            
        Returns:
            bool: 配置成功返回True
        """
        try:
            # 获取切片节点
            red_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed")     # 轴状面
            green_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen") # 冠状面  
            yellow_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow") # 矢状面
            
            if not all([red_slice_node, green_slice_node, yellow_slice_node]):
                logging.error("无法获取切片节点")
                return False
            
            logging.info(f"目标中心点: [{center_point[0]:.3f}, {center_point[1]:.3f}, {center_point[2]:.3f}]")
            logging.info(f"主平面法向量: [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
            
            # 1. 设置红色切片（轴状面）为ValveStent_Bottom_Plane平面
            self._set_slice_by_direct_matrix(red_slice_node, center_point, normal_vector, "Axial_ValveStent")
            
            # 2. 计算与该平面垂直的两个方向向量
            if abs(normal_vector[2]) < 0.9:  
                reference_vector = np.array([0, 0, 1])  
            else:
                reference_vector = np.array([1, 0, 0])  
            
            # 计算第一个切线向量（绿色切片用）
            tangent1 = np.cross(normal_vector, reference_vector)
            tangent1 = tangent1 / np.linalg.norm(tangent1)
            
            # 计算第二个切线向量（黄色切片用）
            tangent2 = np.cross(normal_vector, tangent1)
            tangent2 = tangent2 / np.linalg.norm(tangent2)
            
            logging.info(f"垂直方向1: [{tangent1[0]:.3f}, {tangent1[1]:.3f}, {tangent1[2]:.3f}]")
            logging.info(f"垂直方向2: [{tangent2[0]:.3f}, {tangent2[1]:.3f}, {tangent2[2]:.3f}]")
            
            # 3. 设置绿色切片（冠状面）与ValveStent_Bottom_Plane垂直
            self._set_slice_by_direct_matrix(green_slice_node, center_point, tangent1, "Coronal_Perpendicular")
            
            # 4. 设置黄色切片（矢状面）与ValveStent_Bottom_Plane垂直
            self._set_slice_by_direct_matrix(yellow_slice_node, center_point, tangent2, "Sagittal_Perpendicular")
            
            # 5. 刷新视图
            layout_manager = slicer.app.layoutManager()
            for slice_name in ["Red", "Green", "Yellow"]:
                slice_widget = layout_manager.sliceWidget(slice_name)
                if slice_widget:
                    slice_logic = slice_widget.sliceLogic()
                    if slice_logic:
                        slice_logic.FitSliceToAll()
            
            # 6. 验证所有切片的中心点位置
            self._verify_all_slice_centers(center_point)
            
            return True
            
        except Exception as e:
            logging.error(f"配置切片节点时出错: {e}")
            return False
    
    def _set_slice_by_direct_matrix(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """
        通过直接构建变换矩阵设置切片方向和位置（符合医学标准）
        
        Args:
            slice_node: 切片节点
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）  
            orientation_name: 方向名称
        """
        try:
            # 根据切片类型设置符合医学标准的方向
            slice_name = slice_node.GetName()
            
            if "Red" in slice_name:
                # 轴状面（Axial）：从上往下看的横截面
                # Z轴：沿着法向量方向
                # X轴：指向患者左侧（在图像中显示为右侧，符合放射学约定）
                # Y轴：指向患者前方
                self._set_axial_orientation(slice_node, center_point, normal_vector, orientation_name)
                
            elif "Green" in slice_name:
                # 冠状面（Coronal）：从前往后看的截面
                # Z轴：沿着法向量方向  
                # X轴：指向患者左侧
                # Y轴：指向患者头部
                self._set_coronal_orientation(slice_node, center_point, normal_vector, orientation_name)
                
            elif "Yellow" in slice_name:
                # 矢状面（Sagittal）：从右侧看向左侧的截面
                # Z轴：沿着法向量方向
                # X轴：指向患者前方
                # Y轴：指向患者头部
                self._set_sagittal_orientation(slice_node, center_point, normal_vector, orientation_name)
                
            else:
                # 默认方法（保持原有逻辑）
                self._set_generic_orientation(slice_node, center_point, normal_vector, orientation_name)
            
            logging.info(f"已设置{slice_node.GetName()}的医学标准方向为{orientation_name}")
            
        except Exception as e:
            logging.error(f"设置医学标准切片方向时出错: {e}")
    
    def _set_axial_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """设置轴状面的医学标准方向"""
        try:
            # 轴状面：从上往下看
            # 法向量应该指向Superior方向
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：指向患者左侧（-R方向），在图像中显示为右侧
            x_axis = np.array([-1, 0, 0])  # 指向Left
            
            # 如果法向量与X轴平行，选择其他参考向量
            if abs(np.dot(z_axis, x_axis)) > 0.9:
                x_axis = np.array([0, 1, 0])  # 指向Anterior
            
            # 计算实际的X轴（垂直于法向量）
            x_axis = x_axis - np.dot(x_axis, z_axis) * z_axis
            x_axis = x_axis / np.linalg.norm(x_axis)
            
            # Y轴：通过叉积计算，应该指向前方
            y_axis = np.cross(z_axis, x_axis)
            y_axis = y_axis / np.linalg.norm(y_axis)
            
            # 构建变换矩阵
            self._build_and_apply_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置轴状面方向时出错: {e}")
    
    def _set_coronal_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """设置冠状面的医学标准方向"""
        try:
            # 冠状面：从前往后看
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：指向患者左侧
            x_axis = np.array([-1, 0, 0])  # 指向Left
            
            # 如果法向量与X轴平行，选择其他参考向量
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
            
            # 构建变换矩阵
            self._build_and_apply_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置冠状面方向时出错: {e}")
    
    def _set_sagittal_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """设置矢状面的医学标准方向"""
        try:
            # 矢状面：从右侧看向左侧
            z_axis = normal_vector / np.linalg.norm(normal_vector)
            
            # X轴：指向患者前方
            x_axis = np.array([0, 1, 0])  # 指向Anterior
            
            # 如果法向量与X轴平行，选择其他参考向量
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
            
            # 构建变换矩阵
            self._build_and_apply_matrix(slice_node, center_point, x_axis, y_axis, z_axis)
            
        except Exception as e:
            logging.error(f"设置矢状面方向时出错: {e}")
    
    def _set_generic_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
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
            
            # 构建变换矩阵
            self._build_and_apply_matrix(slice_node, center_point, u_vector, v_vector, normal_vector)
            
        except Exception as e:
            logging.error(f"设置通用方向时出错: {e}")
    
    def _build_and_apply_matrix(self, slice_node, center_point: np.ndarray, x_axis: np.ndarray, y_axis: np.ndarray, z_axis: np.ndarray):
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
            logging.error(f"构建和应用变换矩阵时出错: {e}")
    
    def _verify_all_slice_centers(self, target_center: np.ndarray):
        """
        验证所有切片的中心点位置
        
        Args:
            target_center: 目标中心点（RAS坐标）
        """
        try:
            slice_nodes = [
                (slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed"), "Red"),
                (slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen"), "Green"),
                (slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow"), "Yellow")
            ]
            
            logging.info("验证切片中心点位置:")
            
            for slice_node, name in slice_nodes:
                if slice_node:
                    matrix = slice_node.GetSliceToRAS()
                    current_center = np.array([
                        matrix.GetElement(0, 3),
                        matrix.GetElement(1, 3),
                        matrix.GetElement(2, 3)
                    ])
                    
                    deviation = np.linalg.norm(current_center - target_center)
                    
                    logging.info(f"  {name}切片中心点: [{current_center[0]:.3f}, {current_center[1]:.3f}, {current_center[2]:.3f}], 偏差: {deviation:.3f}mm")
                    
                    # 如果偏差仍然较大，进行最后的修正
                    if deviation > 0.01:  # 0.01mm精度
                        logging.info(f"  执行最终中心点修正...")
                        matrix.SetElement(0, 3, target_center[0])
                        matrix.SetElement(1, 3, target_center[1])
                        matrix.SetElement(2, 3, target_center[2])
                        slice_node.UpdateMatrices()
                        
                        # 再次验证
                        final_matrix = slice_node.GetSliceToRAS()
                        final_center = np.array([
                            final_matrix.GetElement(0, 3),
                            final_matrix.GetElement(1, 3),
                            final_matrix.GetElement(2, 3)
                        ])
                        final_deviation = np.linalg.norm(final_center - target_center)
                        logging.info(f"  最终偏差: {final_deviation:.6f}mm")
            
        except Exception as e:
            logging.error(f"验证切片中心点时出错: {e}")
    
    def _set_slice_orientation_by_ntp(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """
        通过NTP方法设置切片节点的平面方向
        
        Args:
            slice_node: 切片节点
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）  
            orientation_name: 方向名称
        """
        try:
            # 选择参考向量来计算切线向量
            if abs(normal_vector[0]) < 0.9:
                ref = np.array([1, 0, 0])
            elif abs(normal_vector[1]) < 0.9:
                ref = np.array([0, 1, 0])
            else:
                ref = np.array([0, 0, 1])
            
            # 计算Transverse向量（切片的X方向）
            transverse = np.cross(normal_vector, ref)
            transverse = transverse / np.linalg.norm(transverse)
            
            # 计算Parallel向量（切片的Y方向）
            parallel = np.cross(normal_vector, transverse)
            parallel = parallel / np.linalg.norm(parallel)
            
            # 使用SetSliceToRASByNTP方法设置切片方向
            slice_node.SetSliceToRASByNTP(
                normal_vector[0], normal_vector[1], normal_vector[2],      # Normal向量
                transverse[0], transverse[1], transverse[2],              # Transverse向量  
                center_point[0], center_point[1], center_point[2],        # Position
                0  # 旋转角度
            )
            
            # 设置为Reformat模式
            slice_node.SetOrientation("Reformat")
            slice_node.UpdateMatrices()
            
            # 验证并修正切片原点位置
            self._verify_and_correct_slice_center(slice_node, center_point, orientation_name)
            
            logging.info(f"已设置{slice_node.GetName()}的方向为{orientation_name}")
            
        except Exception as e:
            logging.error(f"设置切片平面方向时出错: {e}")
    
    def _verify_and_correct_slice_center(self, slice_node, target_center: np.ndarray, orientation_name: str):
        """
        验证并修正切片中心点位置
        
        Args:
            slice_node: 切片节点
            target_center: 目标中心点（RAS坐标）
            orientation_name: 方向名称
        """
        try:
            # 获取当前切片矩阵
            matrix = slice_node.GetSliceToRAS()
            current_origin = np.array([
                matrix.GetElement(0, 3),
                matrix.GetElement(1, 3),
                matrix.GetElement(2, 3)
            ])
            
            # 计算偏差
            deviation = np.linalg.norm(current_origin - target_center)
            
            # 如果偏差超过阈值，直接修正原点位置
            if deviation > 0.1:  # 0.1mm阈值
                logging.info(f"修正{slice_node.GetName()}中心点偏差: {deviation:.2f}mm")
                
                # 直接设置矩阵的平移部分
                matrix.SetElement(0, 3, target_center[0])
                matrix.SetElement(1, 3, target_center[1])
                matrix.SetElement(2, 3, target_center[2])
                
                # 重新应用矩阵
                slice_node.GetSliceToRAS().DeepCopy(matrix)
                slice_node.UpdateMatrices()
                
                # 验证修正结果
                corrected_matrix = slice_node.GetSliceToRAS()
                corrected_origin = np.array([
                    corrected_matrix.GetElement(0, 3),
                    corrected_matrix.GetElement(1, 3),
                    corrected_matrix.GetElement(2, 3)
                ])
                
                final_deviation = np.linalg.norm(corrected_origin - target_center)
                logging.info(f"{slice_node.GetName()}修正后偏差: {final_deviation:.3f}mm")
            else:
                logging.info(f"{slice_node.GetName()}中心点位置正确，偏差: {deviation:.3f}mm")
                
        except Exception as e:
            logging.error(f"验证修正切片中心点时出错: {e}")
    
    def _set_slice_plane_orientation(self, slice_node, center_point: np.ndarray, normal_vector: np.ndarray, orientation_name: str):
        """
        设置单个切片节点的平面方向（兼容性方法，已弃用）
        
        Args:
            slice_node: 切片节点
            center_point: 平面中心点（RAS坐标）
            normal_vector: 平面法向量（RAS坐标）  
            orientation_name: 方向名称
        """
        # 重定向到新的方法
        self._set_slice_orientation_by_ntp(slice_node, center_point, normal_vector, orientation_name)

    def cleanup(self):
        """清理资源"""
        try:
            logging.info("Module3Logic 清理完成")
        except Exception as e:
            logging.error(f"Module3Logic 清理失败: {e}")
