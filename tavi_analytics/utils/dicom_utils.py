"""
DICOM处理工具模块

提供DICOM数据解析、元数据提取、患者信息处理等功能。
"""

import os
import logging
import datetime
from typing import Optional, Dict, Any

try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

import slicer
from slicer import vtkMRMLSequenceNode, vtkMRMLScalarVolumeNode


class DicomUtils:
    """DICOM处理工具类"""

    @staticmethod
    def read_dicom_file_info(file_path: str) -> Optional[Any]:
        """读取DICOM文件信息
        
        Args:
            file_path: DICOM文件路径
            
        Returns:
            pydicom数据集对象，失败时返回None
        """
        try:
            if not PYDICOM_AVAILABLE:
                logging.warning("pydicom not available, cannot read DICOM file")
                return None
                
            dcm = pydicom.dcmread(file_path, stop_before_pixels=True)
            return dcm
        except Exception as e:
            logging.warning(f"Failed to read DICOM file {file_path}: {e}")
            return None

    @staticmethod
    def get_series_description_by_instance_uid(data_node) -> Optional[str]:
        """通过实例UID从DICOM数据库获取Series Description
        
        Args:
            data_node: 3D Slicer数据节点
            
        Returns:
            序列描述字符串，失败时返回None
        """
        try:
            # 获取DICOM数据库
            dicom_db = slicer.dicomDatabase
            if not dicom_db or not dicom_db.isOpen:
                return None
            
            # 获取实例UID
            instance_uids = data_node.GetAttribute("DICOM.instanceUIDs")
            if not instance_uids:
                return None
            
            # 分割为单个实例UID
            uid_list = instance_uids.split()
            if not uid_list:
                return None
                
            # 获取第一个实例UID
            first_instance_uid = uid_list[0]
            
            # 从DICOM数据库获取文件路径
            file_path = dicom_db.fileForInstance(first_instance_uid)
            
            if file_path and os.path.exists(file_path):
                # 使用pydicom直接读取文件
                if PYDICOM_AVAILABLE:
                    dcm = pydicom.dcmread(file_path, stop_before_pixels=True)
                    
                    # 通过标签(0008,103e)访问SeriesDescription
                    if (0x0008, 0x103e) in dcm:
                        series_desc = str(dcm[0x0008, 0x103e].value).strip()
                        if series_desc:
                            return series_desc
            
            return None
        except Exception as e:
            logging.debug(f"Error in get_series_description_by_instance_uid: {e}")
            return None

    @staticmethod
    def read_series_description_from_file(data_node) -> Optional[str]:
        """直接从DICOM文件读取Series Description
        
        Args:
            data_node: 3D Slicer数据节点
            
        Returns:
            序列描述字符串，失败时返回None
        """
        try:
            if not hasattr(data_node, 'GetStorageNode'):
                return None
                
            storage_node = data_node.GetStorageNode()
            if not storage_node or not hasattr(storage_node, 'GetFileName'):
                return None
                
            file_path = storage_node.GetFileName()
            if not file_path or not PYDICOM_AVAILABLE:
                return None
            
            dcm = pydicom.dcmread(file_path, stop_before_pixels=True)
            
            # 直接通过标签 (0008,103e) 访问 SeriesDescription
            if (0x0008, 0x103e) in dcm:
                series_desc = str(dcm[0x0008, 0x103e].value).strip()
                if series_desc:
                    logging.info(f"Found Series Description from tag (0008,103e): {series_desc}")
                    return series_desc
            # 备选：通过属性名称访问
            elif hasattr(dcm, 'SeriesDescription'):
                series_desc = str(dcm.SeriesDescription).strip()
                if series_desc:
                    logging.info(f"Found Series Description from attribute: {series_desc}")
                    return series_desc
                    
        except Exception as e:
            logging.debug(f"Error in read_series_description_from_file: {e}")
            
        return None

    @staticmethod
    def extract_series_description_from_dicom_sources(data_node) -> Optional[str]:
        """从各种DICOM源提取Series Description
        
        Args:
            data_node: 3D Slicer数据节点
            
        Returns:
            序列描述字符串，失败时返回None
        """
        # 策略1: 检查是否已经有Series Description属性
        existing_desc = data_node.GetAttribute('DICOM.SeriesDescription')
        if existing_desc and existing_desc.strip():
            return existing_desc.strip()
        
        # 策略2: 通过实例UID从DICOM数据库直接读取（最可靠的方法）
        series_desc = DicomUtils.get_series_description_by_instance_uid(data_node)
        if series_desc:
            return series_desc
        
        # 策略3: 直接从DICOM文件读取
        series_desc = DicomUtils.read_series_description_from_file(data_node)
        if series_desc:
            return series_desc
        
        # 策略4: 从Subject Hierarchy获取
        try:
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            if shNode:
                item_id = shNode.GetItemByDataNode(data_node)
                if item_id:
                    # 检查多种可能的属性名
                    series_desc_attrs = [
                        'DICOM.SeriesDescription',
                        'SeriesDescription',
                        'DICOM.0008,103E',
                        'DICOM.0008,103e'
                    ]
                    for attr in series_desc_attrs:
                        series_desc = shNode.GetItemAttribute(item_id, attr)
                        if series_desc and series_desc.strip():
                            return series_desc.strip()
        except Exception:
            pass
        
        # 策略5: 从DICOM数据库查询（如果可用的话）
        try:
            db = slicer.dicomDatabase
            if db and db.isOpen:
                # 直接尝试Series UID（如果数据库支持seriesDescription方法）
                series_uid = data_node.GetAttribute('DICOM.SeriesInstanceUID')
                if series_uid and hasattr(db, 'seriesDescription'):
                    try:
                        series_desc = db.seriesDescription(series_uid)
                        if series_desc and series_desc.strip():
                            return series_desc.strip()
                    except Exception:
                        pass
        except Exception:
            pass
        
        return None

    @staticmethod
    def preserve_dicom_metadata(data_node):
        """保存DICOM元数据
        
        Args:
            data_node: 3D Slicer数据节点
        """
        try:
            # 尝试提取并保存Series Description
            series_desc = DicomUtils.extract_series_description_from_dicom_sources(data_node)
            if series_desc:
                data_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                logging.info(f"Preserved Series Description: {series_desc}")
            
            # 保存其他重要的DICOM属性
            DicomUtils.preserve_other_dicom_attributes(data_node)
            
        except Exception as e:
            logging.warning(f"Failed to preserve DICOM metadata: {e}")

    @staticmethod
    def preserve_other_dicom_attributes(data_node):
        """保存其他重要的DICOM属性
        
        Args:
            data_node: 3D Slicer数据节点
        """
        try:
            # 保存常用的DICOM标签
            important_tags = [
                'DICOM.PatientID',
                'DICOM.PatientName', 
                'DICOM.StudyDate',
                'DICOM.SeriesDate',
                'DICOM.AcquisitionTime',
                'DICOM.SeriesTime',
                'DICOM.StudyDescription',
                'DICOM.SeriesNumber',
                'DICOM.SliceThickness',
                'DICOM.SpacingBetweenSlices'
            ]
            
            # 如果节点有存储节点，尝试从DICOM文件读取这些属性
            if not hasattr(data_node, 'GetStorageNode'):
                return
                
            storage_node = data_node.GetStorageNode()
            if not storage_node or not hasattr(storage_node, 'GetFileName'):
                return
                
            file_path = storage_node.GetFileName()
            if not file_path or not PYDICOM_AVAILABLE:
                return
            
            dcm = pydicom.dcmread(file_path, stop_before_pixels=True)
            
            # 映射pydicom属性名到DICOM标签
            tag_mapping = {
                'DICOM.PatientID': 'PatientID',
                'DICOM.PatientName': 'PatientName',
                'DICOM.StudyDate': 'StudyDate',
                'DICOM.SeriesDate': 'SeriesDate',
                'DICOM.AcquisitionTime': 'AcquisitionTime',
                'DICOM.SeriesTime': 'SeriesTime',
                'DICOM.StudyDescription': 'StudyDescription',
                'DICOM.SeriesNumber': 'SeriesNumber',
                'DICOM.SliceThickness': 'SliceThickness',
                'DICOM.SpacingBetweenSlices': 'SpacingBetweenSlices'
            }
            
            for dicom_tag, pydicom_attr in tag_mapping.items():
                if hasattr(dcm, pydicom_attr):
                    value = str(getattr(dcm, pydicom_attr))
                    if value and value.strip():
                        data_node.SetAttribute(dicom_tag, value.strip())
                        
        except Exception as e:
            logging.warning(f"Failed to preserve other DICOM attributes: {e}")

    @staticmethod
    def extract_dicom_info_from_database(volume_node, patient_data):
        """从DICOM数据库提取患者信息
        
        Args:
            volume_node: 容积节点
            patient_data: 患者数据对象
        """
        try:
            # 获取实例UID
            instance_uid = volume_node.GetAttribute("DICOM.instanceUIDs")
            if not instance_uid:
                return
                
            # 获取第一个实例UID
            instance_uids = instance_uid.split()
            if not instance_uids:
                return
                
            first_instance_uid = instance_uids[0]
            
            # 从DICOM数据库查询
            dicom_db = slicer.dicomDatabase
            if not dicom_db:
                return
                
            # 查询患者信息
            try:
                # 尝试直接从实例ID获取文件
                file_path = dicom_db.fileForInstance(first_instance_uid)
                if file_path:
                    dicom_info = DicomUtils.read_dicom_file_info(file_path)
                    if dicom_info:
                        DicomUtils.populate_patient_data_from_dicom(dicom_info, patient_data)
            except:
                # 如果上述方法失败，尝试通过系列查询
                try:
                    series_uid = volume_node.GetAttribute("DICOM.series_uid")
                    if series_uid:
                        files = dicom_db.filesForSeries(series_uid)
                        if files:
                            file_path = files[0]
                            dicom_info = DicomUtils.read_dicom_file_info(file_path)
                            if dicom_info:
                                DicomUtils.populate_patient_data_from_dicom(dicom_info, patient_data)
                except:
                    pass
                    
        except Exception as e:
            logging.warning(f"Failed to extract DICOM info from database: {e}")

    @staticmethod
    def populate_patient_data_from_dicom(dicom_info, patient_data):
        """从DICOM信息填充患者数据
        
        Args:
            dicom_info: DICOM数据集
            patient_data: 患者数据对象
        """
        try:
            # 患者ID (0010,0020)
            if hasattr(dicom_info, 'PatientID'):
                patient_data.patientID = str(dicom_info.PatientID)
                
            # 患者姓名 (0010,0010)
            if hasattr(dicom_info, 'PatientName'):
                patient_data.patientName = str(dicom_info.PatientName)
                
            # 患者性别 (0010,0040)
            if hasattr(dicom_info, 'PatientSex'):
                sex = str(dicom_info.PatientSex).upper()
                patient_data.patientSex = "男" if sex == "M" else "女" if sex == "F" else ""
                
            # 患者出生日期 (0010,0030)
            if hasattr(dicom_info, 'PatientBirthDate'):
                try:
                    birth_date_str = str(dicom_info.PatientBirthDate)
                    birth_date = datetime.datetime.strptime(birth_date_str, "%Y%m%d").date()
                    
                    # 检查日期 (0008,0020)
                    if hasattr(dicom_info, 'StudyDate'):
                        study_date_str = str(dicom_info.StudyDate)
                        study_date = datetime.datetime.strptime(study_date_str, "%Y%m%d").date()
                        
                        # 计算年龄
                        age = (study_date - birth_date).days // 365
                        patient_data.patientAge = age
                        patient_data.ctScanDate = study_date
                except:
                    pass
                    
        except Exception as e:
            logging.warning(f"Failed to populate patient data from DICOM: {e}")

    @staticmethod
    def get_dicom_tag_value(volume_node, tag: str) -> Optional[str]:
        """获取DICOM标签值
        
        Args:
            volume_node: 容积节点
            tag: DICOM标签名
            
        Returns:
            标签值，失败时返回None
        """
        try:
            # 尝试从节点属性获取DICOM标签
            dicom_tag_name = f"DICOM.{tag}"
            value = volume_node.GetAttribute(dicom_tag_name)
            return value
        except:
            return None

    @staticmethod
    def validate_sequence_node(node) -> bool:
        """验证节点是否为有效的4D序列
        
        Args:
            node: 序列节点
            
        Returns:
            验证结果
        """
        if not isinstance(node, vtkMRMLSequenceNode):
            return False
        
        num_frames = node.GetNumberOfDataNodes()
        if num_frames < 2:
            return False
            
        # 验证第一个数据节点是否为容积数据
        first_data_node = node.GetNthDataNode(0)
        if not isinstance(first_data_node, vtkMRMLScalarVolumeNode):
            return False
            
        return True

    @staticmethod
    def parse_dicom_metadata(session):
        """解析DICOM元数据并填充患者信息
        
        Args:
            session: TAVR研究会话对象
        """
        sequence_node = session.get_volume_sequence_node()
        if not sequence_node:
            return
            
        try:
            # 获取第一帧的容积数据
            first_volume = sequence_node.GetNthDataNode(0)
            if not first_volume:
                return
                
            patient_data = session.patient_data
            
            # 尝试从VTK ImageData的标量范围推断一些基本信息
            image_data = first_volume.GetImageData()
            if image_data:
                scalar_range = image_data.GetScalarRange()
                logging.info(f"Image scalar range: {scalar_range}")
            
            # 尝试从节点名称推断信息
            node_name = first_volume.GetName()
            if node_name:
                # 简单的名称解析逻辑
                if "CT" in node_name.upper():
                    logging.info("Detected CT data from node name")
                    
            # 尝试获取DICOM数据库中的信息
            DicomUtils.extract_dicom_info_from_database(first_volume, patient_data)
            
            # 如果无法从DICOM获取信息，设置默认值
            if not patient_data.patientID:
                # 生成临时ID
                import uuid
                patient_data.patientID = f"TEMP_{str(uuid.uuid4())[:8]}"
                
            if not patient_data.ctScanDate:
                patient_data.ctScanDate = datetime.date.today()
                
        except Exception as e:
            logging.warning(f"Failed to parse DICOM metadata: {e}")
