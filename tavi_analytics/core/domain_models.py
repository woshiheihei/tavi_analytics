"""
TAVI Analytics 领域模型
定义关键的业务领域对象和数据结构
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Type
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class CriticalPlaneType(Enum):
    """关键平面类型枚举"""
    VALVE_STENT_BOTTOM = "plane_bootom"  # 瓣膜支架的最底端闭合曲线
    SINUS_OF_VALSALVA = "plane_max"     # Sinus Of Valsalva的位置
    STENT_BEST_FIT = "plane_0"          # 支架的best fit plane


class CardiacPhase(Enum):
    """心动周期时相（用于对分割与平面进行“期像”归类）"""
    END_DIASTOLE = "end_diastole"   # 舒张末期
    END_SYSTOLE = "end_systole"     # 收缩末期


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


class PlaneBase(ABC):
    """平面基类 - 定义所有平面的通用接口"""
    
    def __init__(self, cardiac_phase: Optional[str] = None):
        self.cardiac_phase = cardiac_phase
        self._slicer_node_id: Optional[str] = None
    
    @property
    @abstractmethod
    def plane_type(self) -> CriticalPlaneType:
        """平面类型"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """平面描述"""
        pass
    
    @property
    @abstractmethod
    def standard_node_name(self) -> str:
        """标准节点名称"""
        pass
    
    @abstractmethod
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据加载平面"""
        pass
    
    @abstractmethod
    def create_visualization(self) -> bool:
        """创建可视化"""
        pass
    
    @abstractmethod
    def get_measurements(self) -> Dict[str, Any]:
        """获取测量数据"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaneBase':
        """从字典创建实例"""
        pass
    
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


class PlaneFactory:
    """平面工厂 - 负责创建和注册平面类型"""
    
    _registry: Dict[CriticalPlaneType, Type[PlaneBase]] = {}
    
    @classmethod
    def register(cls, plane_type: CriticalPlaneType, plane_class: Type[PlaneBase]):
        """注册平面类型"""
        cls._registry[plane_type] = plane_class
        logging.info(f"注册平面类型: {plane_type.value} -> {plane_class.__name__}")
    
    @classmethod
    def create_plane(cls, plane_type: CriticalPlaneType, cardiac_phase: Optional[str] = None) -> Optional[PlaneBase]:
        """创建平面实例"""
        if plane_type not in cls._registry:
            logging.warning(f"未注册的平面类型: {plane_type}")
            return None
        
        plane_class = cls._registry[plane_type]
        return plane_class(cardiac_phase=cardiac_phase)
    
    @classmethod
    def get_registered_types(cls) -> List[CriticalPlaneType]:
        """获取所有已注册的平面类型"""
        return list(cls._registry.keys())
    
    @classmethod
    def load_plane_from_data(cls, plane_type: CriticalPlaneType, data: Dict[str, Any], cardiac_phase: Optional[str] = None) -> Optional[PlaneBase]:
        """从数据创建并加载平面"""
        plane = cls.create_plane(plane_type, cardiac_phase)
        if plane and plane.load_from_data(data):
            return plane
        return None


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
    # 期像信息，用于生成包含期像的节点名称
    cardiac_phase: Optional[str] = None  # 'end_diastole' 或 'end_systole'
    
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
            '_slicer_node_id': slicer_node_id,  # 安全的节点ID
            'cardiac_phase': self.cardiac_phase
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
        instance.cardiac_phase = data.get('cardiac_phase')
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
class ValveStentBottomPlane(PlaneGeometry, PlaneBase):
    """瓣膜支架最底端平面"""
    
    def __init__(self, points=None, less_points=None, plane_params=None, perimeter=0.0, area=0.0, 
                 ped=0.0, aed=0.0, max_dist=0.0, min_dist=0.0, average_dist=0.0, 
                 max_dist_pair=None, min_dist_pair=None, cardiac_phase=None):
        # 初始化PlaneGeometry的数据
        super().__init__(
            points=points or [],
            less_points=less_points or [],
            plane_params=plane_params or [],
            perimeter=perimeter,
            area=area,
            ped=ped,
            aed=aed,
            max_dist=max_dist,
            min_dist=min_dist,
            average_dist=average_dist,
            max_dist_pair=max_dist_pair or [],
            min_dist_pair=min_dist_pair or []
        )
        # 初始化PlaneBase
        PlaneBase.__init__(self, cardiac_phase)
    
    @property
    def plane_type(self) -> CriticalPlaneType:
        return CriticalPlaneType.VALVE_STENT_BOTTOM
    
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据字典加载平面数据"""
        try:
            # 设置PlaneGeometry的属性
            self.points = data.get('points', [])
            self.less_points = data.get('less_points', [])
            self.plane_params = data.get('plane_params', [])
            self.perimeter = data.get('perimeter', 0.0)
            self.area = data.get('area', 0.0)
            self.ped = data.get('PED', 0.0)
            self.aed = data.get('AED', 0.0)
            self.max_dist = data.get('max_dist', 0.0)
            self.min_dist = data.get('min_dist', 0.0)
            self.average_dist = data.get('average_dist', 0.0)
            self.max_dist_pair = data.get('max_dist_pair', [])
            self.min_dist_pair = data.get('min_dist_pair', [])
            self._slicer_node_id = data.get('_slicer_node_id')
            return True
        except Exception as e:
            logging.error(f"加载瓣膜支架底部平面数据失败: {e}")
            return False
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_stent_diameter()
    
    @property
    def description(self) -> str:
        return "瓣膜支架最底端闭合曲线"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像信息的标准节点名称"""
        base_name = "ValveStent_Bottom_Plane"
        if self.cardiac_phase:
            # 将期像转换为显示友好的名称
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    def _get_phase_suffix(self, phase: str) -> str:
        """将期像转换为显示友好的后缀"""
        if phase == 'end_diastole':
            return 'End_Diastole'
        elif phase == 'end_systole':
            return 'End_Systole'
        else:
            return phase  # 回退到原始名称
    
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
class SinusOfValsalvaPlane(PlaneGeometry, PlaneBase):
    """Sinus Of Valsalva平面"""
    
    def __init__(self, points=None, less_points=None, plane_params=None, perimeter=0.0, area=0.0, 
                 ped=0.0, aed=0.0, max_dist=0.0, min_dist=0.0, average_dist=0.0, 
                 max_dist_pair=None, min_dist_pair=None, cardiac_phase=None):
        # 初始化PlaneGeometry的数据
        super().__init__(
            points=points or [],
            less_points=less_points or [],
            plane_params=plane_params or [],
            perimeter=perimeter,
            area=area,
            ped=ped,
            aed=aed,
            max_dist=max_dist,
            min_dist=min_dist,
            average_dist=average_dist,
            max_dist_pair=max_dist_pair or [],
            min_dist_pair=min_dist_pair or []
        )
        # 初始化PlaneBase
        PlaneBase.__init__(self, cardiac_phase)
    
    @property
    def plane_type(self) -> CriticalPlaneType:
        return CriticalPlaneType.SINUS_OF_VALSALVA
    
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据字典加载平面数据"""
        try:
            # 设置PlaneGeometry的属性
            self.points = data.get('points', [])
            self.less_points = data.get('less_points', [])
            self.plane_params = data.get('plane_params', [])
            self.perimeter = data.get('perimeter', 0.0)
            self.area = data.get('area', 0.0)
            self.ped = data.get('PED', 0.0)
            self.aed = data.get('AED', 0.0)
            self.max_dist = data.get('max_dist', 0.0)
            self.min_dist = data.get('min_dist', 0.0)
            self.average_dist = data.get('average_dist', 0.0)
            self.max_dist_pair = data.get('max_dist_pair', [])
            self.min_dist_pair = data.get('min_dist_pair', [])
            self._slicer_node_id = data.get('_slicer_node_id')
            return True
        except Exception as e:
            logging.error(f"加载Sinus Of Valsalva平面数据失败: {e}")
            return False
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_sinus_measurements()
    
    @property
    def description(self) -> str:
        return "Sinus Of Valsalva位置平面"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像信息的标准节点名称"""
        base_name = "SinusOfValsalva_Plane"
        if self.cardiac_phase:
            # 将期像转换为显示友好的名称
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    def _get_phase_suffix(self, phase: str) -> str:
        """将期像转换为显示友好的后缀"""
        if phase == 'end_diastole':
            return 'End_Diastole'
        elif phase == 'end_systole':
            return 'End_Systole'
        else:
            return phase  # 回退到原始名称
    
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
class StentBestFitPlane(PlaneBase):
    """支架最佳拟合平面"""
    
    def __init__(self, name="", plane_params=None, distance_to_zjd=0.0, points=None, cardiac_phase=None):
        super().__init__(cardiac_phase)
        self.name = name
        self.plane_params = plane_params  # 可能为空字符串
        self.distance_to_zjd = distance_to_zjd  # 到某个参考点的距离
        self.points = points  # 添加点数据支持
        
        # Slicer节点管理（对于这个平面，可能不创建曲线，而是创建平面节点）
        self._slicer_node_id: Optional[str] = None
    
    @property
    def plane_type(self) -> CriticalPlaneType:
        return CriticalPlaneType.STENT_BEST_FIT
    
    def load_from_data(self, data: Dict[str, Any]) -> bool:
        """从数据字典加载平面数据"""
        try:
            self.name = data.get('name', '')
            self.plane_params = data.get('plane_params')
            self.distance_to_zjd = data.get('distance_to_zjd', 0.0)
            self.points = data.get('points')
            self._slicer_node_id = data.get('_slicer_node_id')
            return True
        except Exception as e:
            logging.error(f"加载支架拟合平面数据失败: {e}")
            return False
    
    def get_measurements(self) -> Dict[str, float]:
        """获取测量数据"""
        return self.get_distance_measurement()
    
    def to_dict(self) -> Dict[str, Any]:
        """将支架最佳拟合平面数据转换为字典格式"""
        return {
            'plane_type': 'StentBestFitPlane',
            'name': self.name,
            'plane_params': self.plane_params,
            'distance_to_zjd': self.distance_to_zjd,
            'points': self.points,
            '_slicer_node_id': self._slicer_node_id,
            'cardiac_phase': self.cardiac_phase
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StentBestFitPlane':
        """从字典创建支架最佳拟合平面对象"""
        instance = cls(
            name=data.get('name', ''),
            plane_params=data.get('plane_params'),
            distance_to_zjd=data.get('distance_to_zjd', 0.0),
            points=data.get('points'),
            cardiac_phase=data.get('cardiac_phase')
        )
        instance._slicer_node_id = data.get('_slicer_node_id')
        return instance
    
    @property
    def description(self) -> str:
        return "支架最佳拟合平面"
    
    @property
    def standard_node_name(self) -> str:
        """生成包含期像信息的标准节点名称"""
        base_name = "StentBestFit_Plane"
        if self.cardiac_phase:
            # 将期像转换为显示友好的名称
            phase_suffix = self._get_phase_suffix(self.cardiac_phase)
            return f"{base_name}_{phase_suffix}"
        return base_name
    
    def _get_phase_suffix(self, phase: str) -> str:
        """将期像转换为显示友好的后缀"""
        if phase == 'end_diastole':
            return 'End_Diastole'
        elif phase == 'end_systole':
            return 'End_Systole'
        else:
            return phase  # 回退到原始名称
    
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
            '_slicer_node_id': self._slicer_node_id,
            'cardiac_phase': self.cardiac_phase
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
        instance.cardiac_phase = data.get('cardiac_phase')
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
    
    def __init__(self, cardiac_phase: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # 使用动态字典存储平面，替代硬编码字段
        self._planes: Dict[CriticalPlaneType, PlaneBase] = {}
        self._raw_data: Dict[str, Any] = {}
        self.cardiac_phase = cardiac_phase  # 期像信息：'end_diastole' 或 'end_systole'
    
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
            
            # 动态加载所有注册的平面类型
            for plane_type in PlaneFactory.get_registered_types():
                if self._load_plane_dynamic(measurement_data, plane_type):
                    success_count += 1
            
            self.logger.info(f"成功加载 {success_count}/{len(PlaneFactory.get_registered_types())} 个关键平面")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"加载平面数据失败: {e}")
            return False
    
    def _load_plane_dynamic(self, data: Dict[str, Any], plane_type: CriticalPlaneType) -> bool:
        """动态加载指定类型的平面"""
        try:
            plane_key = plane_type.value
            if plane_key not in data:
                self.logger.warning(f"未找到 {plane_key} 数据")
                return False
            
            plane_data = data[plane_key]
            
            # 使用工厂创建平面实例
            plane = PlaneFactory.load_plane_from_data(plane_type, plane_data, self.cardiac_phase)
            if plane:
                self._planes[plane_type] = plane
                self.logger.info(f"成功加载{plane.description}")
                return True
            else:
                self.logger.error(f"创建{plane_type.value}平面失败")
                return False
                
        except Exception as e:
            self.logger.error(f"加载{plane_type.value}平面失败: {e}")
            return False
    
    # ========== 动态平面访问方法 ==========
    def get_plane(self, plane_type: CriticalPlaneType) -> Optional[PlaneBase]:
        """获取指定类型的平面"""
        return self._planes.get(plane_type)
    
    def set_plane(self, plane_type: CriticalPlaneType, plane: PlaneBase):
        """设置指定类型的平面"""
        self._planes[plane_type] = plane
    
    def has_plane(self, plane_type: CriticalPlaneType) -> bool:
        """检查是否有指定类型的平面"""
        return plane_type in self._planes
    
    def get_all_planes(self) -> List[PlaneBase]:
        """获取所有已加载的平面"""
        return list(self._planes.values())
    
    def get_loaded_plane_types(self) -> List[CriticalPlaneType]:
        """获取所有已加载的平面类型"""
        return list(self._planes.keys())
    
    # 业务访问方法（现在使用动态访问）
    def get_valve_stent_bottom(self) -> Optional[ValveStentBottomPlane]:
        """获取瓣膜支架底部平面"""
        plane = self.get_plane(CriticalPlaneType.VALVE_STENT_BOTTOM)
        return plane if isinstance(plane, ValveStentBottomPlane) else None
    
    def get_sinus_of_valsalva(self) -> Optional[SinusOfValsalvaPlane]:
        """获取Sinus Of Valsalva平面"""
        plane = self.get_plane(CriticalPlaneType.SINUS_OF_VALSALVA)
        return plane if isinstance(plane, SinusOfValsalvaPlane) else None
    
    def get_stent_best_fit(self) -> Optional[StentBestFitPlane]:
        """获取支架最佳拟合平面"""
        plane = self.get_plane(CriticalPlaneType.STENT_BEST_FIT)
        return plane if isinstance(plane, StentBestFitPlane) else None
    
    def has_critical_planes(self) -> bool:
        """检查是否已加载关键平面"""
        return len(self._planes) > 0
    
    def get_loaded_planes_summary(self) -> Dict[str, bool]:
        """获取已加载平面的摘要"""
        return {
            'valve_stent_bottom_loaded': self.has_plane(CriticalPlaneType.VALVE_STENT_BOTTOM),
            'sinus_of_valsalva_loaded': self.has_plane(CriticalPlaneType.SINUS_OF_VALSALVA),
            'stent_best_fit_loaded': self.has_plane(CriticalPlaneType.STENT_BEST_FIT),
            'has_any_critical_plane': self.has_critical_planes()
        }
    
    def get_all_measurements(self) -> Dict[str, Any]:
        """获取所有平面的测量数据"""
        measurements = {}
        
        for plane_type, plane in self._planes.items():
            try:
                measurements[plane_type.value] = plane.get_measurements()
            except Exception as e:
                self.logger.error(f"获取{plane_type.value}测量数据失败: {e}")
        
        return measurements
    
    def clear(self):
        """清空所有平面数据"""
        # 先移除可视化节点
        self.remove_all_visualizations()
        
        self._planes.clear()
        self._raw_data.clear()
        self.logger.info("已清空所有平面数据")
    
    def clear_all(self):
        """清空所有平面数据（兼容性方法）"""
        self.clear()
    
    # 可视化管理方法
    def create_all_visualizations(self) -> Dict[str, bool]:
        """为所有已加载的平面创建可视化"""
        results = {}
        
        for plane_type, plane in self._planes.items():
            try:
                results[plane_type.value] = plane.create_visualization()
            except Exception as e:
                self.logger.error(f"创建{plane_type.value}可视化失败: {e}")
                results[plane_type.value] = False
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"可视化创建结果: {success_count}/{len(results)}个成功")
        return results
    
    def remove_all_visualizations(self):
        """移除所有平面的可视化节点"""
        for plane_type, plane in self._planes.items():
            try:
                plane.remove_slicer_node()
            except Exception as e:
                self.logger.error(f"移除{plane_type.value}可视化失败: {e}")
        
        self.logger.info("已移除所有平面可视化节点")
    
    def get_visualization_status(self) -> Dict[str, bool]:
        """获取各平面的可视化状态"""
        status = {}
        
        for plane_type, plane in self._planes.items():
            try:
                status[plane_type.value] = plane.get_slicer_node() is not None
            except:
                status[plane_type.value] = False
        
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
        valve_stent_bottom = self.get_valve_stent_bottom()
        if valve_stent_bottom:
            summary['plane_details']['valve_stent_bottom'] = {
                'description': valve_stent_bottom.description,
                'point_count': len(valve_stent_bottom.points),
                'area': valve_stent_bottom.area,
                'perimeter': valve_stent_bottom.perimeter
            }
        
        sinus_of_valsalva = self.get_sinus_of_valsalva()
        if sinus_of_valsalva:
            summary['plane_details']['sinus_of_valsalva'] = {
                'description': sinus_of_valsalva.description,
                'point_count': len(sinus_of_valsalva.points),
                'area': sinus_of_valsalva.area,
                'perimeter': sinus_of_valsalva.perimeter
            }
        
        stent_best_fit = self.get_stent_best_fit()
        if stent_best_fit:
            summary['plane_details']['stent_best_fit'] = {
                'description': stent_best_fit.description,
                'has_valid_params': stent_best_fit.has_valid_params,
                'distance_to_zjd': stent_best_fit.distance_to_zjd
            }
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """将平面管理器数据转换为字典格式"""
        data = {
            'raw_data': self._raw_data,
            'cardiac_phase': self.cardiac_phase,
            'planes': {}
        }
        
        # 动态序列化所有平面
        for plane_type, plane in self._planes.items():
            try:
                data['planes'][plane_type.value] = plane.to_dict()
            except Exception as e:
                self.logger.error(f"序列化{plane_type.value}平面失败: {e}")
        
        # 为了向后兼容，也包含旧的字段名
        data['valve_stent_bottom'] = data['planes'].get(CriticalPlaneType.VALVE_STENT_BOTTOM.value)
        data['sinus_of_valsalva'] = data['planes'].get(CriticalPlaneType.SINUS_OF_VALSALVA.value)
        data['stent_best_fit'] = data['planes'].get(CriticalPlaneType.STENT_BEST_FIT.value)
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaneDataManager':
        """从字典创建平面管理器对象"""
        # 恢复期像信息
        cardiac_phase = data.get('cardiac_phase')
        manager = cls(cardiac_phase=cardiac_phase)
        manager._raw_data = data.get('raw_data', {})
        
        # 首先尝试从新的planes字段加载
        planes_data = data.get('planes', {})
        for plane_type_str, plane_data in planes_data.items():
            try:
                # 查找对应的平面类型枚举
                plane_type = None
                for pt in CriticalPlaneType:
                    if pt.value == plane_type_str:
                        plane_type = pt
                        break
                
                if plane_type:
                    plane = PlaneFactory.load_plane_from_data(plane_type, plane_data, cardiac_phase)
                    if plane:
                        manager._planes[plane_type] = plane
            except Exception as e:
                manager.logger.error(f"恢复{plane_type_str}平面失败: {e}")
        
        # 向后兼容：从旧字段名加载（如果新格式没有数据）
        if not manager._planes:
            legacy_mappings = [
                (CriticalPlaneType.VALVE_STENT_BOTTOM, 'valve_stent_bottom', ValveStentBottomPlane),
                (CriticalPlaneType.SINUS_OF_VALSALVA, 'sinus_of_valsalva', SinusOfValsalvaPlane),
                (CriticalPlaneType.STENT_BEST_FIT, 'stent_best_fit', StentBestFitPlane)
            ]
            
            for plane_type, field_name, plane_class in legacy_mappings:
                plane_data = data.get(field_name)
                if plane_data:
                    try:
                        plane = plane_class.from_dict(plane_data)
                        if plane:
                            plane.cardiac_phase = cardiac_phase
                            manager._planes[plane_type] = plane
                    except Exception as e:
                        manager.logger.error(f"恢复{field_name}平面失败: {e}")
        
        return manager


# ========== Phase-aware wrapper (非破坏性新增API) ==========
@dataclass
class PhasePlaneRepository:
    """按期像归类的平面仓库

    - 使用两个内部PlaneDataManager分别管理舒张末期与收缩末期的平面
    - 不改变既有PlaneDataManager API，作为上层聚合器存在
    """
    diastole: PlaneDataManager
    systole: PlaneDataManager

    @classmethod
    def create_default(cls) -> 'PhasePlaneRepository':
        return cls(
            diastole=PlaneDataManager(cardiac_phase=CardiacPhase.END_DIASTOLE.value), 
            systole=PlaneDataManager(cardiac_phase=CardiacPhase.END_SYSTOLE.value)
        )

    def get_manager(self, phase: Union[str, CardiacPhase]) -> PlaneDataManager:
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
    def from_dict(cls, data: Dict[str, Any]) -> 'PhasePlaneRepository':
        di = PlaneDataManager.from_dict(data.get('diastole', {})) if data.get('diastole') else PlaneDataManager(cardiac_phase=CardiacPhase.END_DIASTOLE.value)
        sy = PlaneDataManager.from_dict(data.get('systole', {})) if data.get('systole') else PlaneDataManager(cardiac_phase=CardiacPhase.END_SYSTOLE.value)
        # 确保期像信息正确设置
        di.cardiac_phase = CardiacPhase.END_DIASTOLE.value
        sy.cardiac_phase = CardiacPhase.END_SYSTOLE.value
        return cls(diastole=di, systole=sy)

    def get_loaded_summary(self) -> Dict[str, Any]:
        return {
            CardiacPhase.END_DIASTOLE.value: self.diastole.get_loaded_planes_summary(),
            CardiacPhase.END_SYSTOLE.value: self.systole.get_loaded_planes_summary(),
        }


# ========== 平面工厂注册 ==========
# 注册所有平面类型到工厂
PlaneFactory.register(CriticalPlaneType.VALVE_STENT_BOTTOM, ValveStentBottomPlane)
PlaneFactory.register(CriticalPlaneType.SINUS_OF_VALSALVA, SinusOfValsalvaPlane)
PlaneFactory.register(CriticalPlaneType.STENT_BEST_FIT, StentBestFitPlane)
