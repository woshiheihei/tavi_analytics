"""
TAVI Analytics 领域模型
定义关键的业务领域对象和数据结构
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class CriticalPlaneType(Enum):
    """关键平面类型枚举"""
    VALVE_STENT_BOTTOM = "plane_bootom"  # 瓣膜支架的最底端闭合曲线
    SINUS_OF_VALSALVA = "plane_max"     # Sinus Of Valsalva的位置
    STENT_BEST_FIT = "plane_0"          # 支架的best fit plane


@dataclass
class VisualizationConfig:
    """可视化配置"""
    color: Tuple[float, float, float]  # RGB颜色
    line_width: float                  # 线宽
    glyph_scale: float                # 控制点大小
    opacity: float = 1.0              # 透明度
    
    @classmethod
    def create_default_curve_config(cls) -> 'VisualizationConfig':
        """创建默认曲线配置"""
        return cls(
            color=(0.8, 0.2, 0.2),  # 红色
            line_width=2.0,
            glyph_scale=1.5
        )


class PlaneVisualizationManager:
    """平面可视化管理器 - 统一管理所有显示属性配置"""
    
    # 统一的显示配置
    VISUALIZATION_CONFIGS = {
        CriticalPlaneType.VALVE_STENT_BOTTOM: VisualizationConfig(
            color=(0.0, 0.85, 0.4),  # 更鲜亮的青绿色，表示支架
            line_width=3.0,
            glyph_scale=1.5
        ),
        CriticalPlaneType.SINUS_OF_VALSALVA: VisualizationConfig(
            color=(0.1, 0.6, 1.0),  # 更亮的天蓝色，表示窦部
            line_width=2.5,
            glyph_scale=1.5
        ),
        CriticalPlaneType.STENT_BEST_FIT: VisualizationConfig(
            color=(1.0, 0.55, 0.0),  # 亮橙色，表示支架拟合
            line_width=2.0,
            glyph_scale=1.5
        )
    }
    
    @classmethod
    def get_config(cls, plane_type: CriticalPlaneType) -> VisualizationConfig:
        """获取指定平面类型的可视化配置"""
        return cls.VISUALIZATION_CONFIGS.get(plane_type, VisualizationConfig.create_default_curve_config())
    
    @classmethod
    def apply_display_properties(cls, display_node, config: VisualizationConfig):
        """应用显示属性到Slicer显示节点"""
        if display_node:
            # 基础可见性与尺寸
            display_node.SetVisibility(True)
            if hasattr(display_node, 'SetLineWidth'):
                display_node.SetLineWidth(config.line_width)
            if hasattr(display_node, 'SetGlyphScale'):
                display_node.SetGlyphScale(config.glyph_scale)
            if hasattr(display_node, 'SetOpacity'):
                display_node.SetOpacity(config.opacity)

            # 颜色统一：关闭标量/颜色表模式，强制使用实体颜色
            try:
                if hasattr(display_node, 'SetScalarVisibility'):
                    display_node.SetScalarVisibility(False)
                if hasattr(display_node, 'SetUseColorNode'):
                    display_node.SetUseColorNode(False)  # 优先使用实体颜色
                # 一些版本使用 ColorMode，0=Solid
                if hasattr(display_node, 'SetColorMode'):
                    try:
                        display_node.SetColorMode(0)
                    except Exception:
                        pass
            except Exception:
                pass

            # 设定基础/选中/激活颜色全一致，避免“选中即红色”的覆盖
            r, g, b = config.color
            try:
                display_node.SetColor(r, g, b)
            except Exception:
                pass
            if hasattr(display_node, 'SetSelectedColor'):
                try:
                    display_node.SetSelectedColor(r, g, b)
                except Exception:
                    pass
            if hasattr(display_node, 'SetActiveColor'):
                try:
                    display_node.SetActiveColor(r, g, b)
                except Exception:
                    pass

            # 投影/切片中的颜色（若可用）
            if hasattr(display_node, 'SetSliceProjectionColor'):
                try:
                    display_node.SetSliceProjectionColor(r, g, b)
                except Exception:
                    pass

            # 刷新
            try:
                display_node.Modified()
            except Exception:
                pass


@dataclass
class PlaneGeometry:
    """平面几何数据基类"""
    points: List[List[float]]           # 原始点集
    less_points: List[List[float]]      # 简化点集
    plane_params: List[float]           # 平面参数 [a, b, c, d]
    perimeter: float                    # 周长
    area: float                         # 面积
    ped: float                          # PED (Perimeter-derived Equivalent Diameter)
    aed: float                          # AED (Area-derived Equivalent Diameter)
    max_dist: float                     # 最大距离
    min_dist: float                     # 最小距离
    average_dist: float                 # 平均距离
    max_dist_pair: List[List[float]]    # 最大距离点对
    min_dist_pair: List[List[float]]    # 最小距离点对
    
    # Slicer节点管理
    _slicer_node_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将平面几何数据转换为字典格式"""
        # 安全转换节点ID（处理可能的节点对象）
        slicer_node_id = None
        if self._slicer_node_id is not None:
            if isinstance(self._slicer_node_id, str):
                slicer_node_id = self._slicer_node_id
            elif hasattr(self._slicer_node_id, 'GetID'):
                try:
                    slicer_node_id = self._slicer_node_id.GetID()
                except Exception:
                    slicer_node_id = None
            else:
                slicer_node_id = str(self._slicer_node_id) if self._slicer_node_id else None
        
        return {
            'points': self.points,
            'less_points': self.less_points,
            'plane_params': self.plane_params,
            'perimeter': self.perimeter,
            'area': self.area,
            'ped': self.ped,
            'aed': self.aed,
            'max_dist': self.max_dist,
            'min_dist': self.min_dist,
            'average_dist': self.average_dist,
            'max_dist_pair': self.max_dist_pair,
            'min_dist_pair': self.min_dist_pair,
            '_slicer_node_id': slicer_node_id  # 安全的节点ID
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaneGeometry':
        """从字典创建平面几何对象"""
        instance = cls(
            points=data.get('points', []),
            less_points=data.get('less_points', []),
            plane_params=data.get('plane_params', []),
            perimeter=data.get('perimeter', 0.0),
            area=data.get('area', 0.0),
            ped=data.get('ped', 0.0),
            aed=data.get('aed', 0.0),
            max_dist=data.get('max_dist', 0.0),
            min_dist=data.get('min_dist', 0.0),
            average_dist=data.get('average_dist', 0.0),
            max_dist_pair=data.get('max_dist_pair', []),
            min_dist_pair=data.get('min_dist_pair', [])
        )
        instance._slicer_node_id = data.get('_slicer_node_id')
        return instance
    
    @property
    def has_valid_geometry(self) -> bool:
        """检查几何数据是否有效"""
        return (
            len(self.points) >= 3 or len(self.less_points) >= 3
        ) and self.area > 0
    
    @property
    def effective_points(self) -> List[List[float]]:
        """获取有效的点集（优先使用less_points）"""
        return self.less_points if self.less_points else self.points
    
    def create_slicer_curve_node(self, node_name: str, plane_type: Optional[CriticalPlaneType] = None) -> Optional[str]:
        """
        在Slicer中创建曲线节点
        
        Args:
            node_name: 节点名称
            plane_type: 平面类型，用于获取对应的可视化配置
            
        Returns:
            str: 创建的节点ID，失败返回None
        """
        try:
            import slicer
            
            # 检查是否已存在同名节点
            existing_node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if existing_node:
                # 删除已存在的节点
                slicer.mrmlScene.RemoveNode(existing_node)
            
            # 创建新的曲线节点
            curve_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
            curve_node.SetName(node_name)
            
            # 添加控制点
            points_to_use = self.effective_points
            if not points_to_use:
                logging.warning(f"平面 {node_name} 没有有效的点数据")
                return None
            
            # 清除现有点
            curve_node.RemoveAllControlPoints()
            
            # 添加点到曲线（进行LPS到RAS坐标转换）
            for point in points_to_use:
                if len(point) >= 3:
                    # LPS到RAS转换：x -> -x, y -> -y, z -> z
                    ras_x = -point[0]
                    ras_y = -point[1] 
                    ras_z = point[2]
                    curve_node.AddControlPoint(ras_x, ras_y, ras_z)
            
            # 创建闭合效果：添加第一个点作为最后一个点（也要转换坐标）
            if points_to_use and len(points_to_use) > 2:
                first_point = points_to_use[0]
                if len(first_point) >= 3:
                    ras_x = -first_point[0]
                    ras_y = -first_point[1]
                    ras_z = first_point[2]
                    curve_node.AddControlPoint(ras_x, ras_y, ras_z)
            
            # 设置为样条曲线（基本类型）
            try:
                curve_node.SetCurveTypeToSpline()
            except:
                # 如果样条曲线也不支持，使用线性
                try:
                    curve_node.SetCurveTypeToLinear()
                except:
                    # 如果都不支持，保持默认
                    pass
            
            # 取消默认选中，避免使用“选中色”（通常是红色）
            try:
                if hasattr(curve_node, 'SetAllControlPointsSelected'):
                    curve_node.SetAllControlPointsSelected(False)
            except Exception:
                pass

            # 应用可视化配置
            display_node = curve_node.GetDisplayNode()
            if display_node:
                if plane_type:
                    # 使用特定平面类型的配置
                    config = PlaneVisualizationManager.get_config(plane_type)
                    PlaneVisualizationManager.apply_display_properties(display_node, config)
                else:
                    # 使用默认配置
                    default_config = VisualizationConfig.create_default_curve_config()
                    PlaneVisualizationManager.apply_display_properties(display_node, default_config)
            
            self._slicer_node_id = curve_node.GetID()
            logging.info(f"成功创建平面曲线节点: {node_name} (ID: {self._slicer_node_id})")
            
            return self._slicer_node_id
            
        except Exception as e:
            logging.error(f"创建Slicer曲线节点失败: {e}")
            return None
    
    def get_slicer_node(self):
        """获取对应的Slicer节点"""
        if not self._slicer_node_id:
            return None
        
        try:
            import slicer
            return slicer.mrmlScene.GetNodeByID(self._slicer_node_id)
        except:
            return None
    
    def remove_slicer_node(self):
        """移除对应的Slicer节点"""
        node = self.get_slicer_node()
        if node:
            try:
                import slicer
                slicer.mrmlScene.RemoveNode(node)
                self._slicer_node_id = None
                logging.info("已移除Slicer曲线节点")
            except Exception as e:
                logging.error(f"移除Slicer节点失败: {e}")


@dataclass
class ValveStentBottomPlane(PlaneGeometry):
    """瓣膜支架最底端平面"""
    
    @property
    def description(self) -> str:
        return "瓣膜支架最底端闭合曲线"
    
    @property
    def standard_node_name(self) -> str:
        return "ValveStent_Bottom_Plane"
    
    def get_stent_diameter(self) -> Dict[str, float]:
        """获取支架相关的直径测量"""
        return {
            'perimeter_derived_diameter': self.ped,
            'area_derived_diameter': self.aed,
            'max_diameter': self.max_dist,
            'min_diameter': self.min_dist,
            'average_diameter': self.average_dist
        }
    
    def create_visualization(self) -> bool:
        """创建可视化节点"""
        node_id = self.create_slicer_curve_node(self.standard_node_name, CriticalPlaneType.VALVE_STENT_BOTTOM)
        return node_id is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """将瓣膜支架底部平面数据转换为字典格式"""
        base_dict = super().to_dict()
        base_dict['plane_type'] = 'ValveStentBottomPlane'
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValveStentBottomPlane':
        """从字典创建瓣膜支架底部平面对象"""
        instance = cls(
            points=data.get('points', []),
            less_points=data.get('less_points', []),
            plane_params=data.get('plane_params', []),
            perimeter=data.get('perimeter', 0.0),
            area=data.get('area', 0.0),
            ped=data.get('ped', 0.0),
            aed=data.get('aed', 0.0),
            max_dist=data.get('max_dist', 0.0),
            min_dist=data.get('min_dist', 0.0),
            average_dist=data.get('average_dist', 0.0),
            max_dist_pair=data.get('max_dist_pair', []),
            min_dist_pair=data.get('min_dist_pair', [])
        )
        instance._slicer_node_id = data.get('_slicer_node_id')
        return instance


@dataclass
class SinusOfValsalvaPlane(PlaneGeometry):
    """Sinus Of Valsalva平面"""
    
    @property
    def description(self) -> str:
        return "Sinus Of Valsalva位置平面"
    
    @property
    def standard_node_name(self) -> str:
        return "SinusOfValsalva_Plane"
    
    def get_sinus_measurements(self) -> Dict[str, float]:
        """获取窦部相关测量"""
        return {
            'sinus_perimeter': self.perimeter,
            'sinus_area': self.area,
            'sinus_ped': self.ped,
            'sinus_aed': self.aed,
            'sinus_max_diameter': self.max_dist,
            'sinus_min_diameter': self.min_dist
        }
    
    def create_visualization(self) -> bool:
        """创建可视化节点"""
        node_id = self.create_slicer_curve_node(self.standard_node_name, CriticalPlaneType.SINUS_OF_VALSALVA)
        return node_id is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """将Sinus Of Valsalva平面数据转换为字典格式"""
        base_dict = super().to_dict()
        base_dict['plane_type'] = 'SinusOfValsalvaPlane'
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SinusOfValsalvaPlane':
        """从字典创建Sinus Of Valsalva平面对象"""
        instance = cls(
            points=data.get('points', []),
            less_points=data.get('less_points', []),
            plane_params=data.get('plane_params', []),
            perimeter=data.get('perimeter', 0.0),
            area=data.get('area', 0.0),
            ped=data.get('ped', 0.0),
            aed=data.get('aed', 0.0),
            max_dist=data.get('max_dist', 0.0),
            min_dist=data.get('min_dist', 0.0),
            average_dist=data.get('average_dist', 0.0),
            max_dist_pair=data.get('max_dist_pair', []),
            min_dist_pair=data.get('min_dist_pair', [])
        )
        instance._slicer_node_id = data.get('_slicer_node_id')
        return instance


@dataclass
class StentBestFitPlane:
    """支架最佳拟合平面"""
    name: str
    plane_params: Optional[List[float]]  # 可能为空字符串
    distance_to_zjd: float              # 到某个参考点的距离
    points: Optional[List[List[float]]] = None  # 添加点数据支持
    
    # Slicer节点管理（对于这个平面，可能不创建曲线，而是创建平面节点）
    _slicer_node_id: Optional[str] = None
    
    @property
    def description(self) -> str:
        return "支架最佳拟合平面"
    
    @property
    def standard_node_name(self) -> str:
        return "StentBestFit_Plane"
    
    @property
    def has_valid_params(self) -> bool:
        """检查平面参数是否有效"""
        return (
            self.plane_params is not None and 
            isinstance(self.plane_params, list) and 
            len(self.plane_params) >= 4
        )
    
    @property
    def has_curve_points(self) -> bool:
        """检查是否有足够的点数据创建曲线"""
        return (
            self.points is not None and 
            isinstance(self.points, list) and 
            len(self.points) >= 3
        )
    
    def get_distance_measurement(self) -> Dict[str, float]:
        """获取距离测量"""
        return {
            'distance_to_reference': self.distance_to_zjd
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """将支架最佳拟合平面数据转换为字典格式"""
        return {
            'plane_type': 'StentBestFitPlane',
            'name': self.name,
            'plane_params': self.plane_params,
            'distance_to_zjd': self.distance_to_zjd,
            'points': self.points,
            '_slicer_node_id': self._slicer_node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StentBestFitPlane':
        """从字典创建支架最佳拟合平面对象"""
        instance = cls(
            name=data.get('name', ''),
            plane_params=data.get('plane_params'),
            distance_to_zjd=data.get('distance_to_zjd', 0.0),
            points=data.get('points')
        )
        instance._slicer_node_id = data.get('_slicer_node_id')
        return instance
    
    def create_visualization(self) -> bool:
        """创建可视化节点（优先创建闭合曲线，然后是平面，最后是标记点）"""
        try:
            import slicer
            import vtk
            import logging
            
            # 检查是否已存在同名节点
            existing_node = slicer.mrmlScene.GetFirstNodeByName(self.standard_node_name)
            if existing_node:
                slicer.mrmlScene.RemoveNode(existing_node)
            
            # 优先级1：如果有点数据，创建闭合曲线（与其他平面一致）
            if self.has_curve_points:
                curve_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode')
                curve_node.SetName(self.standard_node_name)
                
                # 清除现有点
                curve_node.RemoveAllControlPoints()
                
                # 添加点到曲线（进行LPS到RAS坐标转换）
                for point in self.points:
                    if len(point) >= 3:
                        # LPS到RAS转换：x -> -x, y -> -y, z -> z
                        ras_x = -point[0]
                        ras_y = -point[1] 
                        ras_z = point[2]
                        curve_node.AddControlPoint(ras_x, ras_y, ras_z)
                
                # 创建闭合效果：添加第一个点作为最后一个点（也要转换坐标）
                if len(self.points) > 2:
                    first_point = self.points[0]
                    if len(first_point) >= 3:
                        ras_x = -first_point[0]
                        ras_y = -first_point[1]
                        ras_z = first_point[2]
                        curve_node.AddControlPoint(ras_x, ras_y, ras_z)
                
                # 设置为样条曲线
                try:
                    curve_node.SetCurveTypeToSpline()
                except:
                    try:
                        curve_node.SetCurveTypeToLinear()
                    except:
                        pass
                
                # 取消默认选中
                try:
                    if hasattr(curve_node, 'SetAllControlPointsSelected'):
                        curve_node.SetAllControlPointsSelected(False)
                except Exception:
                    pass

                # 应用统一的可视化配置
                display_node = curve_node.GetDisplayNode()
                if display_node:
                    config = PlaneVisualizationManager.get_config(CriticalPlaneType.STENT_BEST_FIT)
                    PlaneVisualizationManager.apply_display_properties(display_node, config)
                
                self._slicer_node_id = curve_node.GetID()
                logging.info(f"成功创建支架拟合闭合曲线: {self.standard_node_name}")
                return True
            
            # 优先级2：如果有平面参数，创建平面节点
            elif self.has_valid_params:
                plane_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsPlaneNode')
                plane_node.SetName(self.standard_node_name)
                
                # 设置平面参数 [a, b, c, d] -> ax + by + cz + d = 0
                a, b, c, d = self.plane_params[:4]
                
                # 计算平面的原点（最接近原点的点）
                norm_sq = a*a + b*b + c*c
                if norm_sq > 0:
                    origin_lps = [-a*d/norm_sq, -b*d/norm_sq, -c*d/norm_sq]
                    normal_lps = [a, b, c]
                    
                    # LPS到RAS转换
                    origin_ras = [-origin_lps[0], -origin_lps[1], origin_lps[2]]
                    normal_ras = [-normal_lps[0], -normal_lps[1], normal_lps[2]]
                    
                    plane_node.SetOrigin(origin_ras)
                    plane_node.SetNormal(normal_ras)
                    
                    # 应用统一的可视化配置（平面节点）
                    display_node = plane_node.GetDisplayNode()
                    if display_node:
                        config = PlaneVisualizationManager.get_config(CriticalPlaneType.STENT_BEST_FIT)
                        # 复用统一样式，并稍微透明一些
                        PlaneVisualizationManager.apply_display_properties(display_node, config)
                        try:
                            display_node.SetOpacity(0.3)
                        except Exception:
                            pass
                    
                    self._slicer_node_id = plane_node.GetID()
                    logging.info(f"成功创建支架拟合平面节点: {self.standard_node_name}")
                    return True
            
            # 优先级3：创建标记点表示距离信息
            else:
                point_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
                point_node.SetName(self.standard_node_name + "_Reference")
                
                # 在原点创建一个标记点
                point_node.AddControlPoint(0, 0, 0)
                point_node.SetNthControlPointLabel(0, f"Best Fit Ref (d={self.distance_to_zjd:.1f}mm)")
                
                # 应用统一的可视化配置（标记点）
                display_node = point_node.GetDisplayNode()
                if display_node:
                    config = PlaneVisualizationManager.get_config(CriticalPlaneType.STENT_BEST_FIT)
                    PlaneVisualizationManager.apply_display_properties(display_node, config)
                    # 放大标记点便于查看
                    try:
                        display_node.SetGlyphScale(3.0)
                    except Exception:
                        pass

                # 取消默认选中
                try:
                    if hasattr(point_node, 'SetAllControlPointsSelected'):
                        point_node.SetAllControlPointsSelected(False)
                except Exception:
                    pass
                
                self._slicer_node_id = point_node.GetID()
                logging.info(f"成功创建支架拟合参考点: {self.standard_node_name}")
                return True
                
        except Exception as e:
            logging.error(f"创建支架拟合平面可视化失败: {e}")
            return False
        
        return False
    
    def get_slicer_node(self):
        """获取对应的Slicer节点"""
        if not self._slicer_node_id:
            return None
        
        try:
            import slicer
            return slicer.mrmlScene.GetNodeByID(self._slicer_node_id)
        except:
            return None
    
    def remove_slicer_node(self):
        """移除对应的Slicer节点"""
        node = self.get_slicer_node()
        if node:
            try:
                import slicer
                slicer.mrmlScene.RemoveNode(node)
                self._slicer_node_id = None
                logging.info("已移除支架拟合平面节点")
            except Exception as e:
                logging.error(f"移除支架拟合平面节点失败: {e}")


class PlaneDataManager:
    """
    平面数据管理器
    负责管理和访问关键平面数据
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._valve_stent_bottom: Optional[ValveStentBottomPlane] = None
        self._sinus_of_valsalva: Optional[SinusOfValsalvaPlane] = None
        self._stent_best_fit: Optional[StentBestFitPlane] = None
        self._raw_data: Dict[str, Any] = {}
    
    def load_from_measurement_json(self, measurement_data: Dict[str, Any]) -> bool:
        """
        从measurement.json数据中加载关键平面
        
        Args:
            measurement_data: 从measurement.json解析的原始数据
            
        Returns:
            bool: 加载成功返回True
        """
        try:
            self._raw_data = measurement_data.copy()
            success_count = 0
            
            # 加载瓣膜支架底部平面
            if self._load_valve_stent_bottom(measurement_data):
                success_count += 1
                
            # 加载Sinus Of Valsalva平面
            if self._load_sinus_of_valsalva(measurement_data):
                success_count += 1
                
            # 加载支架最佳拟合平面
            if self._load_stent_best_fit(measurement_data):
                success_count += 1
            
            self.logger.info(f"成功加载 {success_count}/3 个关键平面")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"加载平面数据失败: {e}")
            return False
    
    def _load_valve_stent_bottom(self, data: Dict[str, Any]) -> bool:
        """加载瓣膜支架底部平面"""
        try:
            plane_key = CriticalPlaneType.VALVE_STENT_BOTTOM.value
            if plane_key not in data:
                self.logger.warning(f"未找到 {plane_key} 数据")
                return False
            
            plane_data = data[plane_key]
            
            self._valve_stent_bottom = ValveStentBottomPlane(
                points=plane_data.get('points', []),
                less_points=plane_data.get('less_points', []),
                plane_params=plane_data.get('plane_params', []),
                perimeter=plane_data.get('perimeter', 0.0),
                area=plane_data.get('area', 0.0),
                ped=plane_data.get('PED', 0.0),
                aed=plane_data.get('AED', 0.0),
                max_dist=plane_data.get('max_dist', 0.0),
                min_dist=plane_data.get('min_dist', 0.0),
                average_dist=plane_data.get('average_dist', 0.0),
                max_dist_pair=plane_data.get('max_dist_pair', []),
                min_dist_pair=plane_data.get('min_dist_pair', [])
            )
            
            if self._valve_stent_bottom.has_valid_geometry:
                self.logger.info(f"成功加载瓣膜支架底部平面，面积: {self._valve_stent_bottom.area}")
                return True
            else:
                self.logger.warning("瓣膜支架底部平面几何数据无效")
                return False
                
        except Exception as e:
            self.logger.error(f"加载瓣膜支架底部平面失败: {e}")
            return False
    
    def _load_sinus_of_valsalva(self, data: Dict[str, Any]) -> bool:
        """加载Sinus Of Valsalva平面"""
        try:
            plane_key = CriticalPlaneType.SINUS_OF_VALSALVA.value
            if plane_key not in data:
                self.logger.warning(f"未找到 {plane_key} 数据")
                return False
            
            plane_data = data[plane_key]
            
            self._sinus_of_valsalva = SinusOfValsalvaPlane(
                points=plane_data.get('points', []),
                less_points=plane_data.get('less_points', []),
                plane_params=plane_data.get('plane_params', []),
                perimeter=plane_data.get('perimeter', 0.0),
                area=plane_data.get('area', 0.0),
                ped=plane_data.get('PED', 0.0),
                aed=plane_data.get('AED', 0.0),
                max_dist=plane_data.get('max_dist', 0.0),
                min_dist=plane_data.get('min_dist', 0.0),
                average_dist=plane_data.get('average_dist', 0.0),
                max_dist_pair=plane_data.get('max_dist_pair', []),
                min_dist_pair=plane_data.get('min_dist_pair', [])
            )
            
            if self._sinus_of_valsalva.has_valid_geometry:
                self.logger.info(f"成功加载Sinus Of Valsalva平面，面积: {self._sinus_of_valsalva.area}")
                return True
            else:
                self.logger.warning("Sinus Of Valsalva平面几何数据无效")
                return False
                
        except Exception as e:
            self.logger.error(f"加载Sinus Of Valsalva平面失败: {e}")
            return False
    
    def _load_stent_best_fit(self, data: Dict[str, Any]) -> bool:
        """加载支架最佳拟合平面"""
        try:
            plane_key = CriticalPlaneType.STENT_BEST_FIT.value
            if plane_key not in data:
                self.logger.warning(f"未找到 {plane_key} 数据")
                return False
            
            plane_data = data[plane_key]
            
            # 处理可能为空字符串的plane_params
            plane_params = plane_data.get('plane_params')
            if isinstance(plane_params, str) and plane_params == "":
                plane_params = None
            
            # 尝试提取点数据（用于创建闭合曲线）
            points = None
            for points_field in ['points', 'curve_points', 'less_points']:
                if points_field in plane_data:
                    candidate_points = plane_data[points_field]
                    if isinstance(candidate_points, list) and len(candidate_points) >= 3:
                        # 验证点数据格式
                        valid_points = []
                        for point in candidate_points:
                            if isinstance(point, list) and len(point) >= 3:
                                valid_points.append([float(point[0]), float(point[1]), float(point[2])])
                        
                        if len(valid_points) >= 3:
                            points = valid_points
                            self.logger.info(f"从 {points_field} 字段加载了 {len(points)} 个点用于支架最佳拟合平面")
                            break
            
            self._stent_best_fit = StentBestFitPlane(
                name=plane_data.get('name', plane_key),
                plane_params=plane_params,
                distance_to_zjd=plane_data.get('dis_to_zjd', 0.0),
                points=points
            )
            
            # 输出加载信息
            info_parts = [f"到参考点距离: {self._stent_best_fit.distance_to_zjd}"]
            if self._stent_best_fit.has_curve_points:
                info_parts.append(f"包含 {len(points)} 个曲线点")
            if self._stent_best_fit.has_valid_params:
                info_parts.append("包含平面参数")
            
            self.logger.info(f"成功加载支架最佳拟合平面，{', '.join(info_parts)}")
            return True
                
        except Exception as e:
            self.logger.error(f"加载支架最佳拟合平面失败: {e}")
            return False
    
    # 业务访问方法
    def get_valve_stent_bottom(self) -> Optional[ValveStentBottomPlane]:
        """获取瓣膜支架底部平面"""
        return self._valve_stent_bottom
    
    def get_sinus_of_valsalva(self) -> Optional[SinusOfValsalvaPlane]:
        """获取Sinus Of Valsalva平面"""
        return self._sinus_of_valsalva
    
    def get_stent_best_fit(self) -> Optional[StentBestFitPlane]:
        """获取支架最佳拟合平面"""
        return self._stent_best_fit
    
    def has_critical_planes(self) -> bool:
        """检查是否已加载关键平面"""
        return any([
            self._valve_stent_bottom is not None,
            self._sinus_of_valsalva is not None,
            self._stent_best_fit is not None
        ])
    
    def get_loaded_planes_summary(self) -> Dict[str, bool]:
        """获取已加载平面的摘要"""
        return {
            'valve_stent_bottom_loaded': self._valve_stent_bottom is not None,
            'sinus_of_valsalva_loaded': self._sinus_of_valsalva is not None,
            'stent_best_fit_loaded': self._stent_best_fit is not None,
            'has_any_critical_plane': self.has_critical_planes()
        }
    
    def get_all_measurements(self) -> Dict[str, Any]:
        """获取所有平面的测量数据"""
        measurements = {}
        
        if self._valve_stent_bottom:
            measurements['valve_stent_bottom'] = self._valve_stent_bottom.get_stent_diameter()
            
        if self._sinus_of_valsalva:
            measurements['sinus_of_valsalva'] = self._sinus_of_valsalva.get_sinus_measurements()
            
        if self._stent_best_fit:
            measurements['stent_best_fit'] = self._stent_best_fit.get_distance_measurement()
        
        return measurements
    
    def clear(self):
        """清空所有平面数据"""
        # 先移除可视化节点
        self.remove_all_visualizations()
        
        self._valve_stent_bottom = None
        self._sinus_of_valsalva = None
        self._stent_best_fit = None
        self._raw_data.clear()
        self.logger.info("已清空所有平面数据")
    
    def clear_all(self):
        """清空所有平面数据（兼容性方法）"""
        self.clear()
    
    # 可视化管理方法
    def create_all_visualizations(self) -> Dict[str, bool]:
        """为所有已加载的平面创建可视化"""
        results = {}
        
        if self._valve_stent_bottom:
            results["valve_stent_bottom"] = self._valve_stent_bottom.create_visualization()
        
        if self._sinus_of_valsalva:
            results["sinus_of_valsalva"] = self._sinus_of_valsalva.create_visualization()
        
        if self._stent_best_fit:
            results["stent_best_fit"] = self._stent_best_fit.create_visualization()
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"可视化创建结果: {success_count}/{len(results)}个成功")
        return results
    
    def remove_all_visualizations(self):
        """移除所有平面的可视化节点"""
        if self._valve_stent_bottom:
            self._valve_stent_bottom.remove_slicer_node()
        
        if self._sinus_of_valsalva:
            self._sinus_of_valsalva.remove_slicer_node()
        
        if self._stent_best_fit:
            self._stent_best_fit.remove_slicer_node()
        
        self.logger.info("已移除所有平面可视化节点")
    
    def get_visualization_status(self) -> Dict[str, bool]:
        """获取各平面的可视化状态"""
        status = {}
        
        if self._valve_stent_bottom:
            node = self._valve_stent_bottom.get_slicer_node()
            status["valve_stent_bottom"] = node is not None
        
        if self._sinus_of_valsalva:
            node = self._sinus_of_valsalva.get_slicer_node()
            status["sinus_of_valsalva"] = node is not None
        
        if self._stent_best_fit:
            node = self._stent_best_fit.get_slicer_node()
            status["stent_best_fit"] = node is not None
        
        return status
    
    def get_business_summary(self) -> Dict[str, Any]:
        """获取完整的业务摘要信息"""
        summary = {
            'loaded_planes': self.get_loaded_planes_summary(),
            'measurements': self.get_all_measurements(),
            'visualization_status': self.get_visualization_status(),
            'plane_details': {}
        }
        
        # 添加详细的平面信息
        if self._valve_stent_bottom:
            summary['plane_details']['valve_stent_bottom'] = {
                'description': self._valve_stent_bottom.description,
                'point_count': len(self._valve_stent_bottom.points),
                'area': self._valve_stent_bottom.area,
                'perimeter': self._valve_stent_bottom.perimeter
            }
        
        if self._sinus_of_valsalva:
            summary['plane_details']['sinus_of_valsalva'] = {
                'description': self._sinus_of_valsalva.description,
                'point_count': len(self._sinus_of_valsalva.points),
                'area': self._sinus_of_valsalva.area,
                'perimeter': self._sinus_of_valsalva.perimeter
            }
        
        if self._stent_best_fit:
            summary['plane_details']['stent_best_fit'] = {
                'description': self._stent_best_fit.description,
                'has_valid_params': self._stent_best_fit.has_valid_params,
                'distance_to_zjd': self._stent_best_fit.distance_to_zjd
            }
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """将平面管理器数据转换为字典格式"""
        data = {
            'raw_data': self._raw_data,
            'valve_stent_bottom': None,
            'sinus_of_valsalva': None,
            'stent_best_fit': None
        }
        
        if self._valve_stent_bottom:
            data['valve_stent_bottom'] = self._valve_stent_bottom.to_dict()
        
        if self._sinus_of_valsalva:
            data['sinus_of_valsalva'] = self._sinus_of_valsalva.to_dict()
        
        if self._stent_best_fit:
            data['stent_best_fit'] = self._stent_best_fit.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaneDataManager':
        """从字典创建平面管理器对象"""
        manager = cls()
        manager._raw_data = data.get('raw_data', {})
        
        # 恢复瓣膜支架底部平面
        valve_stent_data = data.get('valve_stent_bottom')
        if valve_stent_data:
            manager._valve_stent_bottom = ValveStentBottomPlane.from_dict(valve_stent_data)
        
        # 恢复Sinus Of Valsalva平面
        sinus_data = data.get('sinus_of_valsalva')
        if sinus_data:
            manager._sinus_of_valsalva = SinusOfValsalvaPlane.from_dict(sinus_data)
        
        # 恢复支架最佳拟合平面
        stent_data = data.get('stent_best_fit')
        if stent_data:
            manager._stent_best_fit = StentBestFitPlane.from_dict(stent_data)
        
        return manager
