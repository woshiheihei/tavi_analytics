"""
TAVI Analytics 领域模型
定义关键的业务领域对象和数据结构
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union, Type
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class CriticalContourType(Enum):
    """关键轮廓类型枚举"""
    VALVE_STENT_BOTTOM = "Stent_Frame_Base_plane"  # 瓣膜支架的最底端闭合轮廓
    SINUS_OF_VALSALVA = "SOV_plane"     # Sinus Of Valsalva的轮廓
    
    # 动态轮廓类型支持
    @classmethod
    def create_multi_level_plane_type(cls, height: float) -> 'DynamicContourType':
        """创建多层级平面轮廓类型"""
        return DynamicContourType(f"Stent_Frame_base_up_{height}_plane", height)
    
    @classmethod
    def is_multi_level_plane_type(cls, type_value: str) -> bool:
        """检查是否为多层级平面类型"""
        import re
        pattern = r"^Stent_Frame_base_up_([0-9]+(?:\.[0-9]+)?)_plane$"
        return bool(re.match(pattern, type_value))
    
    @classmethod
    def parse_multi_level_height(cls, type_value: str) -> Optional[float]:
        """从类型值中解析高度"""
        import re
        pattern = r"^Stent_Frame_base_up_([0-9]+(?:\.[0-9]+)?)_plane$"
        match = re.match(pattern, type_value)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


class DynamicContourType:
    """动态轮廓类型 - 用于支持运行时生成的轮廓类型（如多层级平面）"""
    
    def __init__(self, value: str, height: Optional[float] = None):
        self.value = value
        self.height = height
        self.name = value  # 兼容Enum接口
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f"DynamicContourType('{self.value}')"
    
    def __eq__(self, other):
        if isinstance(other, DynamicContourType):
            return self.value == other.value
        elif isinstance(other, CriticalContourType):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        return False
    
    def __hash__(self):
        return hash(self.value)


class CardiacPhase(Enum):
    """心动周期时相（用于对分割与平面进行“期像”归类）"""
    END_DIASTOLE = "end_diastole"   # 舒张末期
    END_SYSTOLE = "end_systole"     # 收缩末期


class LeafletType(Enum):
    """瓣叶类型枚举"""
    LEFT_CORONARY = "left_coronary"     # 左冠状瓣叶
    RIGHT_CORONARY = "right_coronary"   # 右冠状瓣叶  
    NON_CORONARY = "non_coronary"       # 无冠状瓣叶


class PasteAnalysisType(Enum):
    """PASTE分析类型枚举"""
    HALT = "halt"   # Heart Arrested Leaflet Timing
    RELM = "relm"   # Radial Extension Leaflet Motion
    SFD = "sfd"     # Systolic Flow Dynamics
    PFD = "pfd"     # Post-implant Flow Dynamics


class ValvePlaneLevel(Enum):
    """瓣膜平面级别枚举"""
    INFLOW = "inflow"               # 流入段
    NADIR = "nadir"                 # 最低点
    COMMISSURE = "commissure"       # 连合水平


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


class ContourVisualizationManager:
    """轮廓可视化管理器 - 统一管理所有显示属性配置"""
    
    # 统一的显示配置
    VISUALIZATION_CONFIGS = {
        CriticalContourType.VALVE_STENT_BOTTOM: VisualizationConfig(
            color=(0.0, 0.85, 0.4),  # 更鲜亮的青绿色，表示支架
            line_width=3.0,
            glyph_scale=1.5
        ),
        CriticalContourType.SINUS_OF_VALSALVA: VisualizationConfig(
            color=(0.1, 0.6, 1.0),  # 更亮的天蓝色，表示窦部
            line_width=2.5,
            glyph_scale=1.5
    )
    }
    
    @classmethod
    def get_config(cls, contour_type: CriticalContourType) -> VisualizationConfig:
        """获取指定轮廓类型的可视化配置"""
        return cls.VISUALIZATION_CONFIGS.get(contour_type, VisualizationConfig.create_default_curve_config())
    
    @classmethod
    def apply_display_properties(cls, display_node, config: VisualizationConfig):
        """应用显示属性到Slicer显示节点"""
        if display_node:
            # 基础可见性与尺寸（默认隐藏所有轮廓线）
            display_node.SetVisibility(False)
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

            # 需求：在三个 slice 窗口中不显示轮廓（关闭所有2D相关渲染）
            try:
                if hasattr(display_node, 'SetVisibility2D'):
                    display_node.SetVisibility2D(False)
            except Exception:
                pass
            try:
                # 对 Markups 显示节点，关闭切片投影
                if hasattr(display_node, 'SetSliceProjection'):
                    display_node.SetSliceProjection(False)
            except Exception:
                pass


class ContourBase(ABC):
    """轮廓基类 - 定义所有轮廓的通用接口"""
    
    def __init__(self, cardiac_phase: Optional[str] = None):
        self.cardiac_phase = cardiac_phase
        self._slicer_node_id: Optional[str] = None
    
    @property
    @abstractmethod
    def contour_type(self) -> CriticalContourType:
        """轮廓类型"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """轮廓描述"""
        pass
    
    @property
    @abstractmethod
    def standard_node_name(self) -> str:
        """标准节点名称"""
        pass
    
    
    @abstractmethod
    def create_visualization(self) -> bool:
        """创建可视化"""
        pass
    
    @abstractmethod
    def get_measurements(self) -> Dict[str, Any]:
        """获取测量数据"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """基础 to_dict 实现，使用模板方法模式"""
        # 如果继承了 ContourGeometry，调用其 to_dict
        if hasattr(super(), 'to_dict'):
            base_dict = super().to_dict()
        else:
            base_dict = {'cardiac_phase': self.cardiac_phase}
        
        # 添加轮廓类型
        base_dict['contour_type'] = self.__class__.__name__
        
        # 让子类添加额外字段
        extra_fields = self.get_extra_dict_fields()
        if extra_fields:
            base_dict.update(extra_fields)
        
        return base_dict
    
    def get_extra_dict_fields(self) -> Dict[str, Any]:
        """子类可重写此方法添加额外字段"""
        return {}
    
    
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
                logging.info(f"已移除{self.description}节点")
            except Exception as e:
                logging.error(f"移除{self.description}节点失败: {e}")
    
    def _get_phase_suffix(self, phase: str) -> str:
        """将期像转换为显示友好的后缀"""
        if phase == 'end_diastole':
            return 'End_Diastole'
        elif phase == 'end_systole':
            return 'End_Systole'
        else:
            return phase
    
    def calculate_plane_parameters(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        计算轮廓的平面参数（中心点和法向量）

        单一路径：严格基于场景中的节点进行计算；若节点不存在或不可用，则返回None。

        Returns:
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        node_name = None
        try:
            node_name = self.get_node_name()
            try:
                import slicer
                contour_node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            except Exception:
                contour_node = None

            if contour_node:
                return self._calculate_contour_geometry(contour_node)
            else:
                logging.error(f"未找到场景节点：{node_name}，无法计算平面参数")
                return None, None
        except Exception as e:
            logging.error(f"通过场景节点计算平面参数失败（{node_name}）：{e}")
            return None, None
    
    def _calculate_contour_geometry(self, contour_node) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        从轮廓节点的标记点计算几何参数
        
        Args:
            contour_node: 轮廓标记点节点
            
        Returns:
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]: (中心点, 法向量)
        """
        try:
            import numpy as np
            
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
    
    def get_node_name(self) -> str:
        """
        获取期像感知的节点名称
        
        Returns:
            str: 包含期像后缀的完整节点名称
        """
        # standard_node_name 已经包含期像后缀，直接返回
        return self.standard_node_name


class ContourFactory:
    """轮廓工厂 - 负责创建和注册轮廓类型"""
    
    _registry: Dict[Union[CriticalContourType, str], Type[ContourBase]] = {}
    
    @classmethod
    def register(cls, contour_type: Union[CriticalContourType, DynamicContourType, str], contour_class: Type[ContourBase]):
        """注册轮廓类型"""
        key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
        cls._registry[key] = contour_class
        logging.info(f"注册轮廓类型: {key} -> {contour_class.__name__}")
    
    @classmethod
    def create_contour(cls, contour_type: Union[CriticalContourType, DynamicContourType, str], 
                      cardiac_phase: Optional[str] = None, **kwargs) -> Optional[ContourBase]:
        """创建轮廓实例"""
        key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
        
        # 首先尝试直接查找注册的类型
        if key in cls._registry:
            contour_class = cls._registry[key]
            return contour_class(cardiac_phase=cardiac_phase, **kwargs)
        
        # 如果是多层级平面类型，使用MultiLevelPlaneContour
        if CriticalContourType.is_multi_level_plane_type(key):
            height = CriticalContourType.parse_multi_level_height(key)
            if height is not None:
                return MultiLevelPlaneContour(height=height, cardiac_phase=cardiac_phase, **kwargs)
        
        logging.warning(f"未注册的轮廓类型: {key}")
        return None
    
    @classmethod
    def get_registered_types(cls) -> List[Union[CriticalContourType, str]]:
        """获取所有已注册的轮廓类型"""
        result = []
        for key in cls._registry.keys():
            # 尝试找到对应的枚举值
            for enum_type in CriticalContourType:
                if enum_type.value == key:
                    result.append(enum_type)
                    break
            else:
                # 如果没找到枚举值，添加字符串
                result.append(key)
        return result
    
    @classmethod
    def load_contour_from_data(cls, contour_type: Union[CriticalContourType, DynamicContourType, str], 
                              data: Dict[str, Any], cardiac_phase: Optional[str] = None) -> Optional[ContourBase]:
        """从数据创建并加载轮廓"""
        contour = cls.create_contour(contour_type, cardiac_phase)
        if contour and contour.load_from_data(data):
            return contour
        return None
    
    @classmethod
    def discover_contour_types_from_data(cls, measurement_data: Dict[str, Any]) -> List[Union[CriticalContourType, DynamicContourType]]:
        """从measurement数据中发现所有可用的轮廓类型"""
        discovered_types = []
        
        # 添加标准轮廓类型
        for standard_type in CriticalContourType:
            if standard_type.value in measurement_data:
                discovered_types.append(standard_type)
        
        # 发现多层级平面类型
        import re
        pattern = re.compile(r"^Stent_Frame_base_up_([0-9]+(?:\.[0-9]+)?)_plane$")
        for key in measurement_data.keys():
            match = pattern.match(key)
            if match:
                try:
                    height = float(match.group(1))
                    dynamic_type = CriticalContourType.create_multi_level_plane_type(height)
                    discovered_types.append(dynamic_type)
                except ValueError:
                    continue
        
        return discovered_types


@dataclass
class ContourGeometry:
    """轮廓几何数据基类 - 标准化字段名"""
    name: str = ""                               # 名称
    points: List[List[float]] = None            # 完整多边形点集
    plane_params: List[float] = None            # 平面参数 [a, b, c, d]
    less_points: List[List[float]] = None       # 可选的简化多边形点集
    perimeter: float = 0.0                      # 可选的周长
    area: float = 0.0                           # 可选的面积
    PED: float = 0.0                            # 可选的 PED (Perimeter-derived Equivalent Diameter)
    AED: float = 0.0                            # 可选的 AED (Area-derived Equivalent Diameter)
    max_dist_pair: List[List[float]] = None     # 可选的最大距离点对
    max_dist: float = 0.0                       # 可选的最大距离
    min_dist_pair: List[List[float]] = None     # 可选的最小距离点对
    min_dist: float = 0.0                       # 可选的最小距离
    average_dist: float = 0.0                   # 可选的平均距离
    
    # Slicer节点管理
    _slicer_node_id: Optional[str] = None
    # 期像信息，用于生成包含期像的节点名称
    cardiac_phase: Optional[str] = None  # 'end_diastole' 或 'end_systole'
    
    def __post_init__(self):
        """初始化后处理，确保列表字段不为None"""
        if self.points is None:
            self.points = []
        if self.plane_params is None:
            self.plane_params = []
        if self.less_points is None:
            self.less_points = []
        if self.max_dist_pair is None:
            self.max_dist_pair = []
        if self.min_dist_pair is None:
            self.min_dist_pair = []
    
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据字典加载轮廓数据"""
        try:
            # 设置ContourGeometry的标准字段
            self.name = data.get('name', '')
            self.points = data.get('points', [])
            self.less_points = data.get('less_points', [])
            self.plane_params = data.get('plane_params', [])
            self.perimeter = data.get('perimeter', 0.0)
            self.area = data.get('area', 0.0)
            # 标准字段名：PED/AED（不再兼容旧字段，严格按标准字段读取）
            self.PED = data.get('PED', 0.0)
            self.AED = data.get('AED', 0.0)
            # 标准字段名：max_dist_pair, max_dist, min_dist_pair, min_dist, average_dist（严格字段）
            self.max_dist_pair = data.get('max_dist_pair', [])
            self.max_dist = data.get('max_dist', 0.0)
            self.min_dist_pair = data.get('min_dist_pair', [])
            self.min_dist = data.get('min_dist', 0.0)
            self.average_dist = data.get('average_dist', 0.0)
            self._slicer_node_id = data.get('_slicer_node_id')
            return True
        except Exception as e:
            logging.error(f"加载轮廓几何数据失败: {e}")
            return False
    
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
            'name': self.name,
            'points': self.points,
            'plane_params': self.plane_params,
            'less_points': self.less_points,
            'perimeter': self.perimeter,
            'area': self.area,
            'PED': self.PED,
            'AED': self.AED,
            'max_dist_pair': self.max_dist_pair,
            'max_dist': self.max_dist,
            'min_dist_pair': self.min_dist_pair,
            'min_dist': self.min_dist,
            'average_dist': self.average_dist,
            '_slicer_node_id': slicer_node_id,  # 安全的节点ID
            'cardiac_phase': self.cardiac_phase
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContourGeometry':
        """从字典创建轮廓几何对象"""
        instance = cls(
            name=data.get('name', ''),
            points=data.get('points', []),
            plane_params=data.get('plane_params', []),
            less_points=data.get('less_points', []),
            perimeter=data.get('perimeter', 0.0),
            area=data.get('area', 0.0),
            PED=data.get('PED', 0.0),
            AED=data.get('AED', 0.0),
            max_dist_pair=data.get('max_dist_pair', []),
            max_dist=data.get('max_dist', 0.0),
            min_dist_pair=data.get('min_dist_pair', []),
            min_dist=data.get('min_dist', 0.0),
            average_dist=data.get('average_dist', 0.0),
            cardiac_phase=data.get('cardiac_phase')
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
        if self.less_points and len(self.less_points) > 0:
            return self.less_points
        return self.points if self.points else []
    
    def create_slicer_curve_node(self, node_name: str, contour_type: Optional[CriticalContourType] = None) -> Optional[str]:
        """
        在Slicer中创建曲线节点
        
        Args:
            node_name: 节点名称
            contour_type: 轮廓类型，用于获取对应的可视化配置
            
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
                if contour_type:
                    # 使用特定轮廓类型的配置
                    config = ContourVisualizationManager.get_config(contour_type)
                    ContourVisualizationManager.apply_display_properties(display_node, config)
                else:
                    # 使用默认配置
                    default_config = VisualizationConfig.create_default_curve_config()
                    ContourVisualizationManager.apply_display_properties(display_node, default_config)
                # 明确关闭2D显示与投影
                try:
                    if hasattr(display_node, 'SetVisibility2D'):
                        display_node.SetVisibility2D(False)
                except Exception:
                    pass
                try:
                    if hasattr(display_node, 'SetSliceProjection'):
                        display_node.SetSliceProjection(False)
                except Exception:
                    pass
                # 明确保持默认隐藏（仅在定位时短暂显示）
                try:
                    display_node.SetVisibility(False)
                    if hasattr(display_node, 'SetVisibility3D'):
                        display_node.SetVisibility3D(False)
                except Exception:
                    pass
            
            self._slicer_node_id = curve_node.GetID()
            logging.info(f"成功创建平面曲线节点: {node_name} (ID: {self._slicer_node_id})")
            
            return self._slicer_node_id
            
        except Exception as e:
            logging.error(f"创建Slicer曲线节点失败: {e}")
            return None
    


@dataclass
class ValveStentBottomContour(ContourGeometry, ContourBase):
    """瓣膜支架最底端轮廓"""
    
    def __init__(self, name="", points=None, plane_params=None, less_points=None, 
                 perimeter=0.0, area=0.0, PED=0.0, AED=0.0, max_dist_pair=None,
                 max_dist=0.0, min_dist_pair=None, min_dist=0.0, average_dist=0.0, 
                 cardiac_phase=None):
        # 初始化ContourGeometry的数据
        super().__init__(
            name=name,
            points=points or [],
            plane_params=plane_params or [],
            less_points=less_points or [],
            perimeter=perimeter,
            area=area,
            PED=PED,
            AED=AED,
            max_dist_pair=max_dist_pair or [],
            max_dist=max_dist,
            min_dist_pair=min_dist_pair or [],
            min_dist=min_dist,
            average_dist=average_dist
        )
        # 初始化ContourBase
        ContourBase.__init__(self, cardiac_phase)
    
    @property
    def contour_type(self) -> CriticalContourType:
        return CriticalContourType.VALVE_STENT_BOTTOM
    
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_stent_diameter()
    
    @property
    def description(self) -> str:
        return "瓣膜支架最底端闭合轮廓"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像信息的标准节点名称"""
        base_name = "ValveStent_Bottom_Contour"
        if self.cardiac_phase:
            # 将期像转换为显示友好的名称
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    
    def get_stent_diameter(self) -> Dict[str, float]:
        """获取支架相关的直径测量"""
        return {
            'perimeter_derived_diameter': self.PED,
            'area_derived_diameter': self.AED,
            'max_diameter': self.max_dist,
            'min_diameter': self.min_dist,
            'average_diameter': self.average_dist
        }
    
    def create_visualization(self) -> bool:
        """创建可视化节点"""
        node_id = self.create_slicer_curve_node(self.standard_node_name, CriticalContourType.VALVE_STENT_BOTTOM)
        return node_id is not None
    
    


@dataclass
class SinusOfValsalvaContour(ContourGeometry, ContourBase):
    """Sinus Of Valsalva轮廓"""
    
    def __init__(self, name="", points=None, plane_params=None, less_points=None, 
                 perimeter=0.0, area=0.0, PED=0.0, AED=0.0, max_dist_pair=None,
                 max_dist=0.0, min_dist_pair=None, min_dist=0.0, average_dist=0.0, 
                 cardiac_phase=None):
        # 初始化ContourGeometry的数据
        super().__init__(
            name=name,
            points=points or [],
            plane_params=plane_params or [],
            less_points=less_points or [],
            perimeter=perimeter,
            area=area,
            PED=PED,
            AED=AED,
            max_dist_pair=max_dist_pair or [],
            max_dist=max_dist,
            min_dist_pair=min_dist_pair or [],
            min_dist=min_dist,
            average_dist=average_dist
        )
        # 初始化ContourBase
        ContourBase.__init__(self, cardiac_phase)
    
    @property
    def contour_type(self) -> CriticalContourType:
        return CriticalContourType.SINUS_OF_VALSALVA
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_sinus_measurements()
    
    @property
    def description(self) -> str:
        return "Sinus Of Valsalva轮廓"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像信息的标准节点名称"""
        base_name = "SinusOfValsalva_Contour"
        if self.cardiac_phase:
            # 将期像转换为显示友好的名称
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    
    def get_sinus_measurements(self) -> Dict[str, float]:
        """获取窦部相关测量"""
        return {
            'sinus_perimeter': self.perimeter,
            'sinus_area': self.area,
            'sinus_ped': self.PED,
            'sinus_aed': self.AED,
            'sinus_max_diameter': self.max_dist,
            'sinus_min_diameter': self.min_dist
        }
    
    def create_visualization(self) -> bool:
        """创建可视化节点"""
        node_id = self.create_slicer_curve_node(self.standard_node_name, CriticalContourType.SINUS_OF_VALSALVA)
        return node_id is not None
    
    

class ContourDataManager:
    """
    轮廓数据管理器
    负责管理和访问关键轮廓数据
    """
    
    def __init__(self, cardiac_phase: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # 使用字符串键的字典存储轮廓，支持动态类型
        self._contours: Dict[str, ContourBase] = {}
        self._raw_data: Dict[str, Any] = {}
        self.cardiac_phase = cardiac_phase  # 期像信息：'end_diastole' 或 'end_systole'
    
    def load_from_measurement_json(self, measurement_data: Dict[str, Any]) -> bool:
        """
        从measurement.json数据中加载关键轮廓
        
        Args:
            measurement_data: 从measurement.json解析的原始数据
            
        Returns:
            bool: 加载成功返回True
        """
        try:
            self._raw_data = measurement_data.copy()
            success_count = 0
            
            # 自动发现所有可用的轮廓类型（包括多层级平面）
            discovered_types = ContourFactory.discover_contour_types_from_data(measurement_data)
            
            # 动态加载所有发现的轮廓类型
            for contour_type in discovered_types:
                if self._load_contour_dynamic(measurement_data, contour_type):
                    success_count += 1
            
            self.logger.info(f"成功加载 {success_count}/{len(discovered_types)} 个轮廓（包括多层级平面）")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"加载轮廓数据失败: {e}")
            return False
    
    def _load_contour_dynamic(self, data: Dict[str, Any], contour_type: Union[CriticalContourType, DynamicContourType]) -> bool:
        """动态加载指定类型的轮廓"""
        try:
            contour_key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
            if contour_key not in data:
                self.logger.warning(f"未找到 {contour_key} 数据")
                return False
            
            contour_data = data[contour_key]
            
            # 使用工厂创建轮廓实例
            contour = ContourFactory.load_contour_from_data(contour_type, contour_data, self.cardiac_phase)
            if contour:
                # 使用字符串键存储，以支持动态类型
                storage_key = contour_key
                self._contours[storage_key] = contour
                self.logger.info(f"成功加载{contour.description}")
                return True
            else:
                self.logger.error(f"创建{contour_key}轮廓失败")
                return False
                
        except Exception as e:
            contour_key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
            self.logger.error(f"加载{contour_key}轮廓失败: {e}")
            return False
    
    # ========== 动态轮廓访问方法 ==========
    def get_contour(self, contour_type: Union[CriticalContourType, DynamicContourType, str]) -> Optional[ContourBase]:
        """获取指定类型的轮廓"""
        key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
        return self._contours.get(key)
    
    def set_contour(self, contour_type: Union[CriticalContourType, DynamicContourType, str], contour: ContourBase):
        """设置指定类型的轮廓"""
        key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
        self._contours[key] = contour
    
    def has_contour(self, contour_type: Union[CriticalContourType, DynamicContourType, str]) -> bool:
        """检查是否有指定类型的轮廓"""
        key = contour_type.value if hasattr(contour_type, 'value') else str(contour_type)
        return key in self._contours
    
    def get_all_contours(self) -> List[ContourBase]:
        """获取所有已加载的轮廓"""
        return list(self._contours.values())
    
    def get_loaded_contour_types(self) -> List[str]:
        """获取所有已加载的轮廓类型键"""
        return list(self._contours.keys())
    
    def get_multi_level_planes(self) -> List['MultiLevelPlaneContour']:
        """获取所有多层级平面轮廓"""
        planes = []
        for key, contour in self._contours.items():
            if contour.__class__.__name__ == 'MultiLevelPlaneContour':
                planes.append(contour)
        # 按高度排序
        return sorted(planes, key=lambda p: p.height)
    
    def get_multi_level_plane_by_height(self, height: float) -> Optional['MultiLevelPlaneContour']:
        """根据高度获取多层级平面轮廓"""
        plane_type = CriticalContourType.create_multi_level_plane_type(height)
        contour = self.get_contour(plane_type)
        return contour if contour.__class__.__name__ == 'MultiLevelPlaneContour' else None
    
    def get_available_plane_heights(self) -> List[float]:
        """获取所有可用的平面高度"""
        heights = []
        for contour in self._contours.values():
            if contour.__class__.__name__ == 'MultiLevelPlaneContour':
                heights.append(contour.height)
        return sorted(heights)
    
    def load_multi_level_planes_from_measurement_data(self, measurement_data: Dict[str, Any], 
                                                    available_heights: List[float]) -> int:
        """
        专门加载多层级平面的便利方法（保持向后兼容）
        
        Args:
            measurement_data: 测量数据字典
            available_heights: 可用的高度列表
            
        Returns:
            int: 成功加载的平面数量
        """
        loaded_count = 0
        
        # 发现所有多层级平面类型
        discovered_plane_types = []
        for contour_type in ContourFactory.discover_contour_types_from_data(measurement_data):
            if hasattr(contour_type, 'height') and contour_type.height is not None:
                discovered_plane_types.append(contour_type)
        
        # 如果没有找到动态平面，尝试从可用高度创建
        if not discovered_plane_types:
            for height in available_heights:
                plane_type = CriticalContourType.create_multi_level_plane_type(height)
                if plane_type.value in measurement_data:
                    discovered_plane_types.append(plane_type)
        
        # 加载发现的平面
        for plane_type in discovered_plane_types:
            if self._load_contour_dynamic(measurement_data, plane_type):
                loaded_count += 1
        
        self.logger.info(f"专门加载了 {loaded_count} 个多层级平面")
        return loaded_count
    
    def set_valve_level_mappings(self, manufacturer: str, model: str, valve_config=None):
        """
        为多层级平面设置瓣膜级别映射
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号  
            valve_config: 瓣膜配置对象
        """
        if not valve_config:
            self.logger.warning("瓣膜配置未提供，无法进行级别映射")
            return
        
        try:
            # 获取瓣膜特定的高度配置
            valve_plane_config = valve_config.get_valve_plane_config(manufacturer, model)
            
            # 为每个多层级平面设置级别类型
            for contour in self.get_multi_level_planes():
                height = contour.height
                if abs(height - valve_plane_config.inflow) < 0.01:
                    contour.level_type = ValvePlaneLevel.INFLOW.value
                elif abs(height - valve_plane_config.nadir) < 0.01:
                    contour.level_type = ValvePlaneLevel.NADIR.value
                elif abs(height - valve_plane_config.commissure) < 0.01:
                    contour.level_type = ValvePlaneLevel.COMMISSURE.value
                else:
                    contour.level_type = None  # 其他高度不设置级别
            
            self.logger.info(f"完成瓣膜 {manufacturer} {model} 的级别映射")
            
        except Exception as e:
            self.logger.error(f"设置级别映射失败: {e}")
    
    def get_level_planes(self) -> Dict[str, Optional['MultiLevelPlaneContour']]:
        """获取各级别对应的平面"""
        result = {}
        for level in [ValvePlaneLevel.INFLOW.value, ValvePlaneLevel.NADIR.value, ValvePlaneLevel.COMMISSURE.value]:
            result[level] = None
            for plane in self.get_multi_level_planes():
                if plane.level_type == level:
                    result[level] = plane
                    break
        return result
    
    # 业务访问方法（现在使用动态访问）
    def get_valve_stent_bottom(self) -> Optional[ValveStentBottomContour]:
        """获取瓣膜支架底部轮廓"""
        contour = self.get_contour(CriticalContourType.VALVE_STENT_BOTTOM)
        return contour if isinstance(contour, ValveStentBottomContour) else None
    
    def get_sinus_of_valsalva(self) -> Optional[SinusOfValsalvaContour]:
        """获取Sinus Of Valsalva轮廓"""
        contour = self.get_contour(CriticalContourType.SINUS_OF_VALSALVA)
        return contour if isinstance(contour, SinusOfValsalvaContour) else None
    
    # 已移除：StentBestFitContour 相关访问方法
    
    def has_critical_contours(self) -> bool:
        """检查是否已加载关键轮廓"""
        return len(self._contours) > 0
    
    def get_loaded_contours_summary(self) -> Dict[str, bool]:
        """获取已加载轮廓的摘要"""
        return {
            'valve_stent_bottom_loaded': self.has_contour(CriticalContourType.VALVE_STENT_BOTTOM),
            'sinus_of_valsalva_loaded': self.has_contour(CriticalContourType.SINUS_OF_VALSALVA),
            'has_any_critical_contour': self.has_critical_contours()
        }
    
    def get_all_measurements(self) -> Dict[str, Any]:
        """获取所有轮廓的测量数据"""
        measurements = {}
        
        for contour_key, contour in self._contours.items():
            try:
                result = contour.get_measurements()
                measurements[contour_key] = result
                # 诊断：打印每个轮廓的测量摘要
                try:
                    if contour.__class__.__name__ == 'MultiLevelPlaneContour':
                        # 对多层级平面，重点标注缺失项
                        missing = [k for k, v in (result or {}).items() if (v is None) or (isinstance(v, (int, float)) and v <= 0)]
                        logging.info(f"[Measurements] plane_key={contour_key} phase={getattr(contour, 'cardiac_phase', None)} height={getattr(contour, 'height', None)} level={getattr(contour, 'level_type', None)} values={result} missing_or_zero={missing}")
                    else:
                        logging.info(f"[Measurements] key={contour_key} values={result}")
                except Exception:
                    pass
            except Exception as e:
                self.logger.error(f"获取{contour_key}测量数据失败: {e}")
        
        return measurements
    
    def clear(self):
        """清空所有轮廓数据"""
        # 先移除可视化节点
        self.remove_all_visualizations()
        
        self._contours.clear()
        self._raw_data.clear()
        self.logger.info("已清空所有轮廓数据")
    
    def clear_all(self):
        """清空所有轮廓数据（兼容性方法）"""
        self.clear()
    
    # 可视化管理方法
    def create_all_visualizations(self) -> Dict[str, bool]:
        """为所有已加载的轮廓创建可视化"""
        results = {}
        
        for contour_key, contour in self._contours.items():
            try:
                results[contour_key] = contour.create_visualization()
            except Exception as e:
                self.logger.error(f"创建{contour_key}可视化失败: {e}")
                results[contour_key] = False
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"可视化创建结果: {success_count}/{len(results)}个成功")
        return results
    
    def remove_all_visualizations(self):
        """移除所有轮廓的可视化节点"""
        for contour_key, contour in self._contours.items():
            try:
                contour.remove_slicer_node()
            except Exception as e:
                self.logger.error(f"移除{contour_key}可视化失败: {e}")
        
        self.logger.info("已移除所有轮廓可视化节点")
    
    def get_visualization_status(self) -> Dict[str, bool]:
        """获取各轮廓的可视化状态"""
        status = {}
        
        for contour_key, contour in self._contours.items():
            try:
                status[contour_key] = contour.get_slicer_node() is not None
            except:
                status[contour_key] = False
        
        return status
    
    def get_business_summary(self) -> Dict[str, Any]:
        """获取完整的业务摘要信息"""
        summary = {
            'loaded_contours': self.get_loaded_contours_summary(),
            'measurements': self.get_all_measurements(),
            'visualization_status': self.get_visualization_status(),
            'contour_details': {}
        }
        
        # 添加详细的轮廓信息
        valve_stent_bottom = self.get_valve_stent_bottom()
        if valve_stent_bottom:
            summary['contour_details']['valve_stent_bottom'] = {
                'description': valve_stent_bottom.description,
                'point_count': len(valve_stent_bottom.points),
                'area': valve_stent_bottom.area,
                'perimeter': valve_stent_bottom.perimeter
            }
        
        sinus_of_valsalva = self.get_sinus_of_valsalva()
        if sinus_of_valsalva:
            summary['contour_details']['sinus_of_valsalva'] = {
                'description': sinus_of_valsalva.description,
                'point_count': len(sinus_of_valsalva.points),
                'area': sinus_of_valsalva.area,
                'perimeter': sinus_of_valsalva.perimeter
            }
        
    # 已移除：stent_best_fit 相关业务摘要
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """将轮廓管理器数据转换为字典格式"""
        data = {
            'raw_data': self._raw_data,
            'cardiac_phase': self.cardiac_phase,
            'contours': {}
        }
        
        # 动态序列化所有轮廓
        for contour_key, contour in self._contours.items():
            try:
                data['contours'][contour_key] = contour.to_dict()
            except Exception as e:
                self.logger.error(f"序列化{contour_key}轮廓失败: {e}")
        
        # 为了向后兼容，也包含旧的字段名（如果存在对应的轮廓）
        for standard_type in CriticalContourType:
            if standard_type.value in self._contours:
                # 使用枚举名作为兼容字段名
                legacy_name = standard_type.name.lower()
                data[legacy_name] = data['contours'][standard_type.value]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContourDataManager':
        """从字典创建轮廓管理器对象"""
        # 恢复期像信息
        cardiac_phase = data.get('cardiac_phase')
        manager = cls(cardiac_phase=cardiac_phase)
        manager._raw_data = data.get('raw_data', {})
        
        # 首先尝试从新的contours字段加载
        contours_data = data.get('contours', {})
        for contour_key, contour_data in contours_data.items():
            try:
                # 尝试确定轮廓类型
                contour_type_obj = None
                
                # 检查是否为标准轮廓类型
                for ct in CriticalContourType:
                    if ct.value == contour_key:
                        contour_type_obj = ct
                        break
                
                # 检查是否为多层级平面类型
                if not contour_type_obj and CriticalContourType.is_multi_level_plane_type(contour_key):
                    height = CriticalContourType.parse_multi_level_height(contour_key)
                    if height is not None:
                        contour_type_obj = CriticalContourType.create_multi_level_plane_type(height)
                
                if contour_type_obj:
                    contour = ContourFactory.load_contour_from_data(contour_type_obj, contour_data, cardiac_phase)
                    if contour:
                        manager._contours[contour_key] = contour
                        
            except Exception as e:
                manager.logger.error(f"恢复{contour_key}轮廓失败: {e}")
        
        # 向后兼容：从旧字段名加载（如果新格式没有数据）
        if not manager._contours:
            legacy_mappings = [
                (CriticalContourType.VALVE_STENT_BOTTOM, 'valve_stent_bottom', ValveStentBottomContour),
                (CriticalContourType.SINUS_OF_VALSALVA, 'sinus_of_valsalva', SinusOfValsalvaContour)
            ]
            
            for contour_type, field_name, contour_class in legacy_mappings:
                contour_data = data.get(field_name)
                if contour_data:
                    try:
                        contour = contour_class.from_dict(contour_data)
                        if contour:
                            contour.cardiac_phase = cardiac_phase
                            manager._contours[contour_type.value] = contour
                    except Exception as e:
                        manager.logger.error(f"恢复{field_name}轮廓失败: {e}")
        
        return manager


# ========== Phase-aware wrapper (非破坏性新增API) ==========
@dataclass
class PhaseContourRepository:
    """按期像归类的轮廓仓库

    - 使用两个内部ContourDataManager分别管理舒张末期与收缩末期的轮廓
    - 不改变既有ContourDataManager API，作为上层聚合器存在
    """
    diastole: ContourDataManager
    systole: ContourDataManager

    @classmethod
    def create_default(cls) -> 'PhaseContourRepository':
        return cls(
            diastole=ContourDataManager(cardiac_phase=CardiacPhase.END_DIASTOLE.value), 
            systole=ContourDataManager(cardiac_phase=CardiacPhase.END_SYSTOLE.value)
        )

    def get_manager(self, phase: Union[str, CardiacPhase]) -> ContourDataManager:
        key = phase.value if isinstance(phase, CardiacPhase) else str(phase)
        if key == CardiacPhase.END_SYSTOLE.value:
            return self.systole
        # 默认回退到舒张末期
        return self.diastole

    def clear(self):
        self.diastole.clear()
        self.systole.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'diastole': self.diastole.to_dict(),
            'systole': self.systole.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseContourRepository':
        di = ContourDataManager.from_dict(data.get('diastole', {})) if data.get('diastole') else ContourDataManager(cardiac_phase=CardiacPhase.END_DIASTOLE.value)
        sy = ContourDataManager.from_dict(data.get('systole', {})) if data.get('systole') else ContourDataManager(cardiac_phase=CardiacPhase.END_SYSTOLE.value)
        # 确保期像信息正确设置
        di.cardiac_phase = CardiacPhase.END_DIASTOLE.value
        sy.cardiac_phase = CardiacPhase.END_SYSTOLE.value
        return cls(diastole=di, systole=sy)

    def get_loaded_summary(self) -> Dict[str, Any]:
        return {
            CardiacPhase.END_DIASTOLE.value: self.diastole.get_loaded_contours_summary(),
            CardiacPhase.END_SYSTOLE.value: self.systole.get_loaded_contours_summary(),
        }


@dataclass
class MultiLevelPlaneContour(ContourGeometry, ContourBase):
    """多层级瓣膜平面轮廓
    
    用于处理从支架底部向上不同高度的平面轮廓数据，
    支持瓣膜特定的 inflow、nadir、commissure level 映射。
    """
    
    height: float = 0.0  # 平面高度 (cm)
    level_type: Optional[str] = None  # 级别类型 (inflow/nadir/commissure)
    
    def __init__(self, height=0.0, level_type=None, name="", points=None, plane_params=None, 
                 less_points=None, perimeter=0.0, area=0.0, PED=0.0, AED=0.0, 
                 max_dist_pair=None, max_dist=0.0, min_dist_pair=None, min_dist=0.0, 
                 average_dist=0.0, cardiac_phase=None):
        # 初始化ContourGeometry的数据
        super().__init__(
            name=name,
            points=points or [],
            plane_params=plane_params or [],
            less_points=less_points or [],
            perimeter=perimeter,
            area=area,
            PED=PED,
            AED=AED,
            max_dist_pair=max_dist_pair or [],
            max_dist=max_dist,
            min_dist_pair=min_dist_pair or [],
            min_dist=min_dist,
            average_dist=average_dist
        )
        # 初始化ContourBase
        ContourBase.__init__(self, cardiac_phase)
        
        # 多层级平面特有属性
        self.height = height
        self.level_type = level_type
    
    @property
    def contour_type(self) -> Union[CriticalContourType, DynamicContourType]:
        """轮廓类型"""
        # 为多层级平面返回动态类型
        return CriticalContourType.create_multi_level_plane_type(self.height)
    
    @property
    def json_field_name(self) -> str:
        """获取对应的JSON字段名"""
        return f"Stent_Frame_base_up_{self.height}_plane"
    
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据字典加载轮廓数据"""
        try:
            # 设置ContourGeometry的标准字段
            self.name = data.get('name', '')
            self.points = data.get('points', [])
            self.less_points = data.get('less_points', [])
            self.plane_params = data.get('plane_params', [])
            self.perimeter = data.get('perimeter', 0.0)
            self.area = data.get('area', 0.0)
            # 标准字段名：PED/AED（兼容各种变体）
            self.PED = data.get('PED', data.get('ped', data.get('perimeter_derived_diameter', 0.0)))
            self.AED = data.get('AED', data.get('aed', data.get('area_derived_diameter', 0.0)))
            # 标准字段名：max_dist_pair, max_dist, min_dist_pair, min_dist, average_dist
            self.max_dist_pair = data.get('max_dist_pair', [])
            self.max_dist = data.get('max_dist', data.get('max_diameter', data.get('longest_diameter', 0.0)))
            self.min_dist_pair = data.get('min_dist_pair', [])
            self.min_dist = data.get('min_dist', data.get('min_diameter', data.get('shortest_diameter', 0.0)))
            self.average_dist = data.get('average_dist', data.get('average_diameter', 0.0))
            self._slicer_node_id = data.get('_slicer_node_id')
            
            # 调试/诊断：记录加载键与测量参数概览
            present_keys = sorted(list(data.keys())) if isinstance(data, dict) else []
            logging.info(
                f"[MultiLevelPlane] phase={self.cardiac_phase} height={self.height}cm level={self.level_type} keys={present_keys} "
                f"perimeter={self.perimeter}, area={self.area}, PED={self.PED}, AED={self.AED}, "
                f"longest(max)={self.max_dist}, shortest(min)={self.min_dist}, average={self.average_dist}"
            )
            # 专门提示：除周长/面积外的派生字段是否缺失
            if (
                (self.PED or 0) <= 0 and (self.AED or 0) <= 0 and 
                (self.max_dist or 0) <= 0 and (self.min_dist or 0) <= 0 and (self.average_dist or 0) <= 0
            ):
                logging.warning(
                    f"[MultiLevelPlane] phase={self.cardiac_phase} height={self.height}cm 仅发现周长/面积，其他直径类字段缺失或为0"
                )
            
            return True
        except Exception as e:
            logging.error(f"加载多层级平面轮廓数据失败: {e}")
            return False
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_plane_measurements()
    
    @property
    def description(self) -> str:
        level_desc = f" ({self.level_type})" if self.level_type else ""
        return f"支架底部上方 {self.height}cm 平面{level_desc}"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像和高度信息的标准节点名称"""
        base_name = f"StentPlane_{self.height}cm"
        if self.level_type:
            base_name += f"_{self.level_type.title()}"
        if self.cardiac_phase:
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    def get_plane_measurements(self) -> Dict[str, float]:
        """获取平面相关测量"""
        measurements = {
            'perimeter': self.perimeter,
            'area': self.area,
            'longest_diameter': self.max_dist,
            'shortest_diameter': self.min_dist,
            'perimeter_derived_diameter': self.PED,
            'area_derived_diameter': self.AED,
            'average_diameter': self.average_dist
        }
        # 诊断：输出测量字典与缺失字段
        try:
            missing = [k for k, v in measurements.items() if (v is None) or (isinstance(v, (int, float)) and v <= 0)]
            logging.info(
                f"[MultiLevelPlane] phase={self.cardiac_phase} height={self.height}cm level={self.level_type} measurements={measurements} missing_or_zero={missing}"
            )
        except Exception:
            pass
        return measurements
    
    def create_visualization(self) -> bool:
        """创建可视化节点"""
        # 为多层级平面使用特殊的可视化配置
        node_id = self.create_slicer_curve_node(self.standard_node_name, CriticalContourType.VALVE_STENT_BOTTOM)
        return node_id is not None
    
    def get_extra_dict_fields(self) -> Dict[str, Any]:
        """返回额外字段"""
        return {
            'height': self.height,
            'level_type': self.level_type,
            'json_field_name': self.json_field_name
        }
    


class MultiLevelPlaneManager:
    """多层级平面管理器
    
    管理多个高度的瓣膜平面轮廓，提供基于瓣膜类型的
    inflow、nadir、commissure level 映射功能。
    """
    
    def __init__(self, cardiac_phase: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.cardiac_phase = cardiac_phase
        self._planes: Dict[float, MultiLevelPlaneContour] = {}
        self._valve_config: Optional[Any] = None  # 瓣膜配置，避免循环导入
    
    def set_valve_config(self, valve_config):
        """设置瓣膜配置（由外部注入以避免循环导入）"""
        self._valve_config = valve_config
    
    def load_planes_from_measurement_data(self, measurement_data: Dict[str, Any], 
                                        available_heights: List[float]) -> int:
        """
        从measurement.json数据中加载多个高度的平面
        
        Args:
            measurement_data: 测量数据字典
            available_heights: 可用的高度列表
            
        Returns:
            int: 成功加载的平面数量
        """
        loaded_count = 0

        # 优先从measurement_data中动态发现所有可用高度（更健壮，不依赖配置）
        try:
            import re
            dynamic_heights: List[float] = []
            pattern = re.compile(r"^Stent_Frame_base_up_([0-9]+(?:\.[0-9]+)?)_plane$")
            for key in list(measurement_data.keys()):
                m = pattern.match(key)
                if m:
                    try:
                        dynamic_heights.append(float(m.group(1)))
                    except Exception:
                        pass
            # 合并配置高度与动态高度，去重并排序
            if dynamic_heights:
                heights = sorted(set(dynamic_heights + list(available_heights)))
            else:
                heights = list(available_heights)
        except Exception:
            heights = list(available_heights)

        # 尝试加载多层级平面数据
        for height in heights:
            field_name = f"Stent_Frame_base_up_{height}_plane"
            
            if field_name in measurement_data:
                try:
                    plane_data = measurement_data[field_name]
                    plane_contour = MultiLevelPlaneContour(
                        height=height,
                        cardiac_phase=self.cardiac_phase
                    )
                    
                    if plane_contour.load_from_data(plane_data):
                        self._planes[height] = plane_contour
                        loaded_count += 1
                        self.logger.info(f"成功加载 {height}cm 平面数据")
                    else:
                        self.logger.warning(f"加载 {height}cm 平面数据失败")
                        
                except Exception as e:
                    self.logger.error(f"处理 {height}cm 平面数据时出错: {e}")
            else:
                self.logger.debug(f"未找到 {height}cm 平面数据: {field_name}")
        
        # 如果没有找到多层级平面数据，尝试从现有的单层轮廓数据中创建平面
        if loaded_count == 0:
            loaded_count = self._load_from_contour_data(measurement_data, available_heights)
        
        self.logger.info(f"共加载 {loaded_count} 个多层级平面")
        return loaded_count

    def _load_from_contour_data(self, measurement_data: Dict[str, Any], 
                               available_heights: List[float]) -> int:
        """
        从现有的单层轮廓数据中创建多层级平面
        
        Args:
            measurement_data: 测量数据字典
            available_heights: 可用的高度列表
            
        Returns:
            int: 成功创建的平面数量
        """
        loaded_count = 0
        
        # 检查是否有可用的轮廓数据
        contour_mappings = {
            CriticalContourType.VALVE_STENT_BOTTOM.value: "瓣膜支架底部",
            CriticalContourType.SINUS_OF_VALSALVA.value: "Sinus Of Valsalva"
        }
        
        for contour_type, description in contour_mappings.items():
            if contour_type in measurement_data:
                try:
                    contour_data = measurement_data[contour_type]
                    if isinstance(contour_data, dict) and contour_data:
                        # 为每个可用高度创建平面，使用相同的轮廓数据
                        for height in available_heights:
                            plane_contour = MultiLevelPlaneContour(
                                height=height,
                                cardiac_phase=self.cardiac_phase
                            )
                            
                            # 复制轮廓数据并设置高度信息
                            adapted_data = contour_data.copy()
                            adapted_data['height'] = height
                            adapted_data['description'] = f"{description} (高度: {height}cm)"
                            
                            # 调试：记录原始数据的键
                            self.logger.debug(f"原始轮廓数据键: {list(contour_data.keys())}")
                            self.logger.debug(f"测量参数: perimeter={contour_data.get('perimeter', 'N/A')}, area={contour_data.get('area', 'N/A')}")
                            
                            # 严格从原始数据读取测量值：不生成模拟/默认数值
                            if not adapted_data.get('perimeter') or not adapted_data.get('area'):
                                self.logger.warning(
                                    f"{description} 高度{height}cm 缺少周长或面积等测量参数，保持为空以反映原始数据"
                                )
                            
                            if plane_contour.load_from_data(adapted_data):
                                self._planes[height] = plane_contour
                                loaded_count += 1
                                self.logger.info(f"从{description}轮廓创建 {height}cm 平面")
                        
                        # 找到一个有效的轮廓数据就足够了，避免重复创建
                        break
                        
                except Exception as e:
                    self.logger.error(f"从{description}轮廓创建平面失败: {e}")
        
        if loaded_count == 0:
            self.logger.warning(f"未找到可用的轮廓数据来创建{self.cardiac_phase}期像的平面")
        
        return loaded_count
    
    def set_level_mappings(self, manufacturer: str, model: str):
        """
        根据瓣膜类型设置级别映射
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
        """
        if not self._valve_config:
            self.logger.warning("瓣膜配置未设置，无法进行级别映射")
            return
        
        try:
            # 获取瓣膜特定的高度配置
            valve_config = self._valve_config.get_valve_plane_config(manufacturer, model)
            
            # 为每个平面设置级别类型
            for height, plane in self._planes.items():
                if abs(height - valve_config.inflow) < 0.01:
                    plane.level_type = ValvePlaneLevel.INFLOW.value
                elif abs(height - valve_config.nadir) < 0.01:
                    plane.level_type = ValvePlaneLevel.NADIR.value
                elif abs(height - valve_config.commissure) < 0.01:
                    plane.level_type = ValvePlaneLevel.COMMISSURE.value
                else:
                    plane.level_type = None  # 其他高度不设置级别
            
            self.logger.info(f"完成瓣膜 {manufacturer} {model} 的级别映射")
            
        except Exception as e:
            self.logger.error(f"设置级别映射失败: {e}")
    
    def get_plane_by_height(self, height: float) -> Optional[MultiLevelPlaneContour]:
        """根据高度获取平面"""
        return self._planes.get(height)
    
    def get_plane_by_level(self, level: str) -> Optional[MultiLevelPlaneContour]:
        """根据级别获取平面"""
        for plane in self._planes.values():
            if plane.level_type == level:
                return plane
        return None
    
    def get_all_planes(self) -> List[MultiLevelPlaneContour]:
        """获取所有平面"""
        return list(self._planes.values())
    
    def get_available_heights(self) -> List[float]:
        """获取已加载的高度列表"""
        return sorted(self._planes.keys())
    
    def get_level_planes(self) -> Dict[str, Optional[MultiLevelPlaneContour]]:
        """获取各级别对应的平面"""
        return {
            ValvePlaneLevel.INFLOW.value: self.get_plane_by_level(ValvePlaneLevel.INFLOW.value),
            ValvePlaneLevel.NADIR.value: self.get_plane_by_level(ValvePlaneLevel.NADIR.value),
            ValvePlaneLevel.COMMISSURE.value: self.get_plane_by_level(ValvePlaneLevel.COMMISSURE.value)
        }
    
    def create_all_visualizations(self) -> Dict[float, bool]:
        """为所有平面创建可视化"""
        results = {}
        for height, plane in self._planes.items():
            try:
                results[height] = plane.create_visualization()
            except Exception as e:
                self.logger.error(f"创建 {height}cm 平面可视化失败: {e}")
                results[height] = False
        return results
    
    def remove_all_visualizations(self):
        """移除所有平面的可视化"""
        for plane in self._planes.values():
            try:
                plane.remove_slicer_node()
            except Exception as e:
                self.logger.error(f"移除平面可视化失败: {e}")
    
    def clear(self):
        """清理所有数据"""
        self.remove_all_visualizations()
        self._planes.clear()
        self.logger.info("已清理所有多层级平面数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'cardiac_phase': self.cardiac_phase,
            'planes': {str(height): plane.to_dict() for height, plane in self._planes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], valve_config=None) -> 'MultiLevelPlaneManager':
        """从字典创建实例"""
        manager = cls(cardiac_phase=data.get('cardiac_phase'))
        if valve_config:
            manager.set_valve_config(valve_config)
        
        planes_data = data.get('planes', {})
        for height_str, plane_data in planes_data.items():
            try:
                height = float(height_str)
                plane = MultiLevelPlaneContour.from_dict(plane_data)
                manager._planes[height] = plane
            except Exception as e:
                manager.logger.error(f"恢复平面数据失败: {e}")
        
        return manager


# ========== 轮廓工厂注册 ==========
# 注册所有轮廓类型到工厂
ContourFactory.register(CriticalContourType.VALVE_STENT_BOTTOM, ValveStentBottomContour)
ContourFactory.register(CriticalContourType.SINUS_OF_VALSALVA, SinusOfValsalvaContour)

# 注意：MultiLevelPlaneContour 通过工厂的动态创建机制处理，无需显式注册
