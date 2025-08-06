"""
TAVR Analytics - 会话管理模块

本模块包含TAVRStudySession类，用于管理TAVR研究会话的全局状态和数据。
该类实现了单例模式，确保整个应用程序中只有一个会话实例。

主要功能：
- 管理患者数据和研究会话状态
- 维护4D CT序列节点引用
- 管理心动周期时相标记
- 提供DICOM元数据访问
- 维护数据加载和处理状态

作者：TAVR Analytics Team
创建日期：2025年
"""

import logging
import os
from typing import Optional, Dict, Any

import slicer
from slicer import vtkMRMLSequenceNode, vtkMRMLSequenceBrowserNode

# 导入数据模型
try:
    # 尝试相对导入
    from .data_models import PatientData
except ImportError:
    # 回退到绝对导入
    from data_models import PatientData


class TAVRStudySession:
    """
    TAVR研究会话管理类
    
    该类实现单例模式，用于管理整个TAVR分析会话的状态和数据。
    会话包含患者信息、4D CT数据引用、心动周期标记等关键信息。
    
    单例模式确保：
    - 整个应用程序只有一个会话实例
    - 数据在不同模块间共享
    - 状态一致性得到保证
    
    主要职责：
    1. 患者数据管理
    2. 4D CT序列节点管理
    3. 心动周期时相标记管理
    4. DICOM元数据访问
    5. 会话状态验证
    
    使用示例：
        session = TAVRStudySession()
        patient_data = session.get_patient_data()
        session.mark_phase('end_diastole', frame_index=10, phase_percent=30.0)
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        单例模式实现
        
        确保类只能有一个实例。如果实例不存在，创建新实例；
        如果已存在，返回现有实例。
        
        Returns:
            TAVRStudySession: 单例实例
        """
        if cls._instance is None:
            cls._instance = super(TAVRStudySession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化会话实例
        
        只在第一次创建实例时执行初始化。
        后续调用将跳过初始化过程。
        """
        if not self._initialized:
            # 初始化患者数据
            self.patient_data = PatientData()
            
            # 4D CT数据节点引用
            self.volume_sequence_node_id = None
            self.sequence_browser_node_id = None
            
            # 心动周期时相标记
            self.marked_phases = {
                'end_diastole': {
                    'frame_index': None, 
                    'phase_percent': None,
                    'series_description': None
                },
                'end_systole': {
                    'frame_index': None, 
                    'phase_percent': None,
                    'series_description': None
                }
            }
            
            # 几何数据存储
            self.segmentation_node_id = None  # 主分割节点ID
            self.landmark_node_ids = {}  # 标志点节点ID字典
            self.reconstructed_planes = {}  # 重建平面存储
            
            # 标记已初始化
            self._initialized = True
            
            # 设置日志
            self.logger = logging.getLogger(__name__)
    
    def get_patient_data(self) -> PatientData:
        """
        获取患者数据对象
        
        Returns:
            PatientData: 当前会话的患者数据对象
        """
        return self.patient_data
    
    def set_volume_sequence_data(self, volume_sequence_node_id: str, sequence_browser_node_id: str):
        """
        设置4D CT序列数据节点引用
        
        Args:
            volume_sequence_node_id (str): 体数据序列节点ID
            sequence_browser_node_id (str): 序列浏览器节点ID
        """
        self.volume_sequence_node_id = volume_sequence_node_id
        self.sequence_browser_node_id = sequence_browser_node_id
        self.logger.info(f"设置序列数据节点: volume={volume_sequence_node_id}, browser={sequence_browser_node_id}")
    
    def get_volume_sequence_node(self) -> Optional[vtkMRMLSequenceNode]:
        """
        获取4D CT数据的序列节点
        
        Returns:
            Optional[vtkMRMLSequenceNode]: 序列节点，如果不存在返回None
        """
        if self.volume_sequence_node_id:
            node = slicer.mrmlScene.GetNodeByID(self.volume_sequence_node_id)
            if node is None:
                self.logger.warning(f"序列节点不存在: {self.volume_sequence_node_id}")
            return node
        return None
    
    def get_sequence_browser_node(self) -> Optional[vtkMRMLSequenceBrowserNode]:
        """
        获取序列浏览器节点
        
        Returns:
            Optional[vtkMRMLSequenceBrowserNode]: 序列浏览器节点，如果不存在返回None
        """
        if self.sequence_browser_node_id:
            node = slicer.mrmlScene.GetNodeByID(self.sequence_browser_node_id)
            if node is None:
                self.logger.warning(f"序列浏览器节点不存在: {self.sequence_browser_node_id}")
            return node
        return None
    
    def get_selected_valve(self) -> Dict[str, str]:
        """
        获取选择的瓣膜信息
        
        Returns:
            Dict[str, str]: 包含品牌和型号的字典
                - brand: 瓣膜品牌
                - model: 瓣膜型号
        """
        return {
            'brand': self.patient_data.valveBrand,
            'model': self.patient_data.valveModel
        }
    
    def set_segmentation_node(self, node_id: str):
        """
        设置主分割节点ID
        
        Args:
            node_id (str): 分割节点ID
        """
        self.segmentation_node_id = node_id
        self.logger.info(f"设置分割节点: {node_id}")
    
    def get_segmentation_node(self):
        """
        获取主分割节点
        
        Returns:
            vtkMRMLSegmentationNode: 分割节点，如果不存在返回None
        """
        if self.segmentation_node_id:
            node = slicer.mrmlScene.GetNodeByID(self.segmentation_node_id)
            if node is None:
                self.logger.warning(f"分割节点不存在: {self.segmentation_node_id}")
            return node
        return None
    
    def set_landmark_node(self, landmark_name: str, node_id: str):
        """
        设置标志点节点ID
        
        Args:
            landmark_name (str): 标志点名称
            node_id (str): 节点ID
        """
        self.landmark_node_ids[landmark_name] = node_id
        self.logger.info(f"设置标志点节点 {landmark_name}: {node_id}")
    
    def get_landmark_node(self, landmark_name: str):
        """
        获取标志点节点
        
        Args:
            landmark_name (str): 标志点名称
            
        Returns:
            vtkMRMLMarkupsFiducialNode: 标志点节点，如果不存在返回None
        """
        node_id = self.landmark_node_ids.get(landmark_name)
        if node_id:
            node = slicer.mrmlScene.GetNodeByID(node_id)
            if node is None:
                self.logger.warning(f"标志点节点不存在: {landmark_name} -> {node_id}")
            return node
        return None
    
    def set_reconstructed_plane(self, plane_name: str, plane_data: Dict[str, Any]):
        """
        存储重建的平面数据
        
        Args:
            plane_name (str): 平面名称
            plane_data (Dict[str, Any]): 平面数据，包含原点和法向量
        """
        self.reconstructed_planes[plane_name] = plane_data
        self.logger.info(f"存储重建平面 {plane_name}")
    
    def get_reconstructed_plane(self, plane_name: str) -> Optional[Dict[str, Any]]:
        """
        获取重建的平面数据
        
        Args:
            plane_name (str): 平面名称
            
        Returns:
            Optional[Dict[str, Any]]: 平面数据，如果不存在返回None
        """
        return self.reconstructed_planes.get(plane_name)
    
    def get_landmark_coordinates(self, landmark_name: str) -> Optional[tuple]:
        """
        获取指定标志点的坐标
        
        Args:
            landmark_name (str): 标志点名称
            
        Returns:
            Optional[tuple]: 三维坐标(x, y, z)，如果未找到返回None
        """
        node = self.get_landmark_node(landmark_name)
        if node and node.GetNumberOfFiducials() > 0:
            coords = [0.0, 0.0, 0.0]
            node.GetNthFiducialPosition(0, coords)
            return tuple(coords)
        return None
    
    def are_geometries_defined(self) -> bool:
        """
        检查几何数据是否已定义
        
        Returns:
            bool: 如果所有必需的几何数据都已定义返回True
        """
        # 检查是否有分割节点
        has_segmentation = self.segmentation_node_id is not None
        
        # 检查是否有原生瓣环平面
        has_native_annulus_plane = 'native_annulus' in self.reconstructed_planes
        
        return has_segmentation and has_native_annulus_plane
    
    def mark_phase(self, phase_name: str, frame_index: int, phase_percent: float, series_description: str = ""):
        """
        标记心动周期关键时相
        
        Args:
            phase_name (str): 时相名称（'end_diastole' 或 'end_systole'）
            frame_index (int): 帧索引
            phase_percent (float): 时相百分比
            series_description (str, optional): 序列描述
        
        Raises:
            ValueError: 如果时相名称无效
        """
        if phase_name not in self.marked_phases:
            raise ValueError(f"无效的时相名称: {phase_name}")
        
        self.marked_phases[phase_name] = {
            'frame_index': frame_index,
            'phase_percent': phase_percent,
            'series_description': series_description
        }
        
        self.logger.info(f"标记时相 {phase_name}: 帧={frame_index}, 百分比={phase_percent}%")
    
    def get_marked_phase(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """
        获取标记的时相信息
        
        Args:
            phase_name (str): 时相名称
            
        Returns:
            Optional[Dict[str, Any]]: 时相信息字典，如果未标记返回None
        """
        return self.marked_phases.get(phase_name)
    
    def get_current_frame_series_description(self) -> str:
        """
        获取当前帧的Series Description
        
        该方法尝试多种策略来获取当前帧的DICOM Series Description：
        1. 从节点属性获取
        2. 从DICOM数据库获取
        3. 从DICOM文件直接读取
        4. 从序列索引构建描述
        5. 从存储节点文件路径获取
        
        Returns:
            str: 当前帧的序列描述
        """
        sequence_node = self.get_volume_sequence_node()
        browser_node = self.get_sequence_browser_node()
        
        if not sequence_node or not browser_node:
            self.logger.debug("没有找到序列节点或浏览器节点")
            return "未知序列"
        
        try:
            # 获取当前选中的帧索引
            current_frame_index = browser_node.GetSelectedItemNumber()
            self.logger.debug(f"当前帧索引: {current_frame_index}")
            
            # 获取当前帧对应的数据节点
            current_data_node = sequence_node.GetNthDataNode(current_frame_index)
            
            if current_data_node:
                self.logger.debug(f"当前数据节点名称: {current_data_node.GetName()}")
                
                # 策略1: 尝试从节点属性中获取Series Description
                series_desc = self._get_dicom_series_description_from_node(current_data_node)
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    self.logger.debug(f"从节点属性获取Series Description: {series_desc}")
                    return series_desc
                
                # 策略2: 尝试从DICOM数据库中获取
                series_desc = self._get_dicom_series_description_from_database(current_data_node)
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    self.logger.debug(f"从数据库获取Series Description: {series_desc}")
                    return series_desc
                
                # 策略3: 直接从DICOM文件读取
                series_desc = self._read_series_description_from_file(current_data_node)
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    self.logger.debug(f"从文件直接读取Series Description: {series_desc}")
                    return series_desc
                
                # 策略4: 尝试从序列节点的索引值获取
                series_desc = self._get_series_description_from_sequence_index(sequence_node, current_frame_index)
                if series_desc:
                    self.logger.debug(f"从序列索引获取描述: {series_desc}")
                    return series_desc
                
                # 策略5: 从存储节点的文件路径获取信息
                series_desc = self._get_series_description_from_storage_node(current_data_node)
                if series_desc:
                    self.logger.debug(f"从存储节点获取描述: {series_desc}")
                    return series_desc
                
                # 如果都没有找到，返回帧信息
                time_value = sequence_node.GetNthIndexValue(current_frame_index)
                if time_value:
                    result = f"Phase {time_value}% (帧 {current_frame_index + 1})"
                    self.logger.debug(f"返回时间值描述: {result}")
                    return result
                else:
                    result = f"帧 {current_frame_index + 1}/{sequence_node.GetNumberOfDataNodes()}"
                    self.logger.debug(f"返回帧数描述: {result}")
                    return result
            
            return f"帧 {current_frame_index + 1}"
            
        except Exception as e:
            self.logger.error(f"获取Series Description时出错: {e}")
            return "未知序列"
    
    def _get_dicom_series_description_from_node(self, node) -> Optional[str]:
        """
        从节点属性获取DICOM Series Description
        
        Args:
            node: MRML节点
            
        Returns:
            Optional[str]: Series Description，如果未找到返回None
        """
        if not hasattr(node, 'GetAttribute'):
            self.logger.debug("节点没有GetAttribute方法")
            return None
            
        # 尝试常见的DICOM属性名
        dicom_attributes = [
            'DICOM.0008,103E',  # Series Description的DICOM标签（优先）
            'DICOM.0008,103e',  # 小写e版本
            'DICOM.SeriesDescription',
            'SeriesDescription', 
            'vtkMRMLSubjectHierarchyConstants.GetDICOMSeriesDescriptionAttributeName()',
        ]
        
        for attr in dicom_attributes:
            value = node.GetAttribute(attr)
            if value and value.strip():
                self.logger.debug(f"在节点属性 {attr} 中找到Series Description: {value}")
                return value.strip()
        
        self.logger.debug("在节点属性中未找到Series Description")
        return None
    
    def _get_dicom_series_description_from_database(self, node) -> Optional[str]:
        """
        从DICOM数据库获取Series Description
        
        Args:
            node: MRML节点
            
        Returns:
            Optional[str]: Series Description，如果未找到返回None
        """
        try:
            db = slicer.dicomDatabase
            if not db or not db.isOpen:
                return None
            
            # 策略1: 直接通过Series UID获取
            series_uid = node.GetAttribute('DICOM.SeriesInstanceUID')
            if not series_uid:
                series_uid = node.GetAttribute('DICOM.0020,000E')
            
            if series_uid:
                try:
                    series_desc = db.seriesDescription(series_uid)
                    if series_desc and series_desc.strip():
                        return series_desc.strip()
                except Exception:
                    pass
            
            # 策略2: 通过实例UID查找
            instance_uids = node.GetAttribute('DICOM.instanceUIDs')
            if instance_uids:
                first_instance_uid = instance_uids.split()[0] if instance_uids else None
                if first_instance_uid:
                    try:
                        # 遍历数据库查找包含此实例的系列
                        patients = db.patients()
                        for patient in patients:
                            studies = db.studiesForPatient(patient)
                            for study in studies:
                                series_list = db.seriesForStudy(study)
                                for series_id in series_list:
                                    try:
                                        instances = db.instancesForSeries(series_id)
                                        if first_instance_uid in instances:
                                            series_desc = db.seriesDescription(series_id)
                                            if series_desc and series_desc.strip():
                                                return series_desc.strip()
                                    except Exception:
                                        continue
                    except Exception:
                        pass
            
        except Exception as e:
            self.logger.error(f"从DICOM数据库获取Series Description时出错: {e}")
            
        return None
    
    def _read_series_description_from_file(self, node) -> Optional[str]:
        """
        直接从DICOM文件读取Series Description
        
        Args:
            node: MRML节点
            
        Returns:
            Optional[str]: Series Description，如果未找到返回None
        """
        try:
            # 尝试通过logic实例调用方法
            logic = slicer.modules.tavi_analytics.widgetRepresentation().self().logic
            if logic and hasattr(logic, '_read_series_description_from_file'):
                series_desc = logic._read_series_description_from_file(node)
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    return series_desc
        except Exception as e:
            self.logger.debug(f"从DICOM文件读取时出错: {e}")
        
        return None
    
    def _get_series_description_from_sequence_index(self, sequence_node, frame_index) -> Optional[str]:
        """
        从序列索引值构建描述
        
        Args:
            sequence_node: 序列节点
            frame_index (int): 帧索引
            
        Returns:
            Optional[str]: 构建的描述，如果无法构建返回None
        """
        try:
            index_name = sequence_node.GetIndexName()
            index_unit = sequence_node.GetIndexUnit()
            index_value = sequence_node.GetNthIndexValue(frame_index)
            
            if index_name and index_value:
                if index_unit:
                    return f"{index_name}: {index_value}{index_unit}"
                else:
                    return f"{index_name}: {index_value}"
                    
        except Exception:
            pass
            
        return None
    
    def _get_series_description_from_storage_node(self, node) -> Optional[str]:
        """
        从存储节点文件路径提取系列信息
        
        Args:
            node: MRML节点
            
        Returns:
            Optional[str]: 提取的描述，如果无法提取返回None
        """
        try:
            if hasattr(node, 'GetStorageNode'):
                storage_node = node.GetStorageNode()
                if storage_node and hasattr(storage_node, 'GetFileName'):
                    file_path = storage_node.GetFileName()
                    if file_path:
                        filename = os.path.basename(file_path)
                        # 移除常见的文件扩展名
                        name_without_ext = os.path.splitext(filename)[0]
                        # 如果文件名包含有意义的信息，返回它
                        if len(name_without_ext) > 5 and not name_without_ext.startswith("IM"):
                            return name_without_ext
                            
        except Exception:
            pass
            
        return None
    
    def is_ready(self) -> bool:
        """
        检查会话是否准备完成
        
        检查以下条件：
        - 4D CT数据已加载
        - 瓣膜品牌已选择
        - 瓣膜型号已选择
        
        Returns:
            bool: 如果会话准备完成返回True，否则返回False
        """
        ready = (
            self.volume_sequence_node_id is not None and 
            self.patient_data.valveBrand != "" and 
            self.patient_data.valveModel != ""
        )
        
        if not ready:
            self.logger.debug("会话未准备完成")
            if self.volume_sequence_node_id is None:
                self.logger.debug("- 缺少4D CT数据")
            if self.patient_data.valveBrand == "":
                self.logger.debug("- 缺少瓣膜品牌")
            if self.patient_data.valveModel == "":
                self.logger.debug("- 缺少瓣膜型号")
        
        return ready
    
    def has_marked_phases(self) -> bool:
        """
        检查是否已标记心动周期时相
        
        Returns:
            bool: 如果已标记舒张末期和收缩末期返回True，否则返回False
        """
        end_diastole = self.marked_phases.get('end_diastole', {})
        end_systole = self.marked_phases.get('end_systole', {})
        
        return (
            end_diastole.get('frame_index') is not None and
            end_systole.get('frame_index') is not None
        )
    
    def get_phase_summary(self) -> Dict[str, Any]:
        """
        获取时相标记摘要
        
        Returns:
            Dict[str, Any]: 包含时相标记摘要的字典
        """
        return {
            'end_diastole_marked': self.marked_phases['end_diastole']['frame_index'] is not None,
            'end_systole_marked': self.marked_phases['end_systole']['frame_index'] is not None,
            'marked_phases': self.marked_phases.copy()
        }
    
    def reset(self):
        """
        重置会话
        
        清除所有数据和状态，重新初始化会话。
        用于开始新的分析或清除当前会话。
        """
        self.logger.info("重置TAVR研究会话")
        
        # 重置患者数据
        self.patient_data = PatientData()
        
        # 清除节点引用
        self.volume_sequence_node_id = None
        self.sequence_browser_node_id = None
        
        # 重置时相标记
        self.marked_phases = {
            'end_diastole': {
                'frame_index': None, 
                'phase_percent': None, 
                'series_description': None
            },
            'end_systole': {
                'frame_index': None, 
                'phase_percent': None, 
                'series_description': None
            }
        }
        
        # 重置几何数据
        self.segmentation_node_id = None
        self.landmark_node_ids = {}
        self.reconstructed_planes = {}
        
        # 重置几何数据
        self.segmentation_node_id = None
        self.landmark_node_ids = {}
        self.reconstructed_planes = {}
        
        self.logger.info("会话重置完成")
    
    def set_landmark_node(self, landmark_name: str, node_id: str):
        """
        设置标志点节点ID
        
        Args:
            landmark_name (str): 标志点名称
            node_id (str): 节点ID
        """
        self.landmark_node_ids[landmark_name] = node_id
        self.logger.info(f"设置标志点节点: {landmark_name} -> {node_id}")
    
    def get_landmark_node(self, landmark_name: str):
        """
        获取标志点节点
        
        Args:
            landmark_name (str): 标志点名称
            
        Returns:
            标志点节点，如果不存在返回None
        """
        node_id = self.landmark_node_ids.get(landmark_name)
        if node_id:
            node = slicer.mrmlScene.GetNodeByID(node_id)
            if node is None:
                self.logger.warning(f"标志点节点不存在: {landmark_name} ({node_id})")
            return node
        return None
    
    def set_reconstructed_plane(self, plane_name: str, plane_data: Dict[str, Any]):
        """
        设置重建平面数据
        
        Args:
            plane_name (str): 平面名称
            plane_data (Dict[str, Any]): 平面数据，包含origin、normal等
        """
        self.reconstructed_planes[plane_name] = plane_data
        self.logger.info(f"设置重建平面: {plane_name}")
    
    def get_reconstructed_plane(self, plane_name: str) -> Optional[Dict[str, Any]]:
        """
        获取重建平面数据
        
        Args:
            plane_name (str): 平面名称
            
        Returns:
            平面数据字典，如果不存在返回None
        """
        return self.reconstructed_planes.get(plane_name)
    
    def set_segmentation_node(self, node_id: str):
        """
        设置主分割节点ID
        
        Args:
            node_id (str): 分割节点ID
        """
        self.segmentation_node_id = node_id
        self.logger.info(f"设置分割节点: {node_id}")
    
    def get_segmentation_node(self):
        """
        获取主分割节点
        
        Returns:
            分割节点，如果不存在返回None
        """
        if self.segmentation_node_id:
            node = slicer.mrmlScene.GetNodeByID(self.segmentation_node_id)
            if node is None:
                self.logger.warning(f"分割节点不存在: {self.segmentation_node_id}")
            return node
        return None

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息摘要
        
        Returns:
            Dict[str, Any]: 包含会话状态和数据的摘要
        """
        return {
            'patient_id': self.patient_data.patientID,
            'patient_name': self.patient_data.patientName,
            'valve_brand': self.patient_data.valveBrand,
            'valve_model': self.patient_data.valveModel,
            'has_sequence_data': self.volume_sequence_node_id is not None,
            'is_ready': self.is_ready(),
            'has_marked_phases': self.has_marked_phases(),
            'phase_summary': self.get_phase_summary()
        }
    
    @classmethod
    def get_instance(cls) -> 'TAVRStudySession':
        """
        获取单例实例的类方法
        
        这是获取会话实例的推荐方式，提供了更明确的API。
        
        Returns:
            TAVRStudySession: 单例实例
        """
        return cls()
