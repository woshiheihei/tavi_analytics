import logging
import os
import json
import datetime
from typing import Optional, Dict, Any

import vtk
import qt

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleTest
)
from slicer.util import VTKObservationMixin

from slicer import vtkMRMLSequenceNode, vtkMRMLSequenceBrowserNode, vtkMRMLScalarVolumeNode

# 导入重构后的核心模块
try:
    # 尝试相对导入（用于包内导入）
    from .core.data_models import PatientData
    from .core.enums import ImageQuality, FollowUpTimepoint
except ImportError:
    # 回退到绝对导入（用于3D Slicer直接加载）
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from core.data_models import PatientData
    from core.enums import ImageQuality, FollowUpTimepoint



class TAVRStudySession:
    """TAVR研究会话管理类，实现单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TAVRStudySession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.patient_data = PatientData()
            self.volume_sequence_node_id = None
            self.sequence_browser_node_id = None
            self.marked_phases = {
                'end_diastole': {'frame_index': None, 'phase_percent': None},
                'end_systole': {'frame_index': None, 'phase_percent': None}
            }
            self._initialized = True
    
    def get_patient_data(self) -> PatientData:
        """返回患者数据对象"""
        return self.patient_data
    
    def get_volume_sequence_node(self) -> Optional[vtkMRMLSequenceNode]:
        """返回4D CT数据的序列节点"""
        if self.volume_sequence_node_id:
            return slicer.mrmlScene.GetNodeByID(self.volume_sequence_node_id)
        return None
    
    def get_sequence_browser_node(self) -> Optional[vtkMRMLSequenceBrowserNode]:
        """返回序列浏览器节点"""
        if self.sequence_browser_node_id:
            return slicer.mrmlScene.GetNodeByID(self.sequence_browser_node_id)
        return None
    
    def get_selected_valve(self) -> Dict[str, str]:
        """返回选择的瓣膜信息"""
        return {
            'brand': self.patient_data.valveBrand,
            'model': self.patient_data.valveModel
        }
    
    def get_marked_phase(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """获取标记的时相信息"""
        return self.marked_phases.get(phase_name)
    
    def get_current_frame_series_description(self) -> str:
        """获取当前帧的Series Description"""
        sequence_node = self.get_volume_sequence_node()
        browser_node = self.get_sequence_browser_node()
        
        if not sequence_node or not browser_node:
            print("DEBUG: 没有找到序列节点或浏览器节点")
            return "未知序列"
        
        try:
            # 获取当前选中的帧索引
            current_frame_index = browser_node.GetSelectedItemNumber()
            print(f"DEBUG: 当前帧索引: {current_frame_index}")
            
            # 获取当前帧对应的数据节点
            current_data_node = sequence_node.GetNthDataNode(current_frame_index)
            
            if current_data_node:
                print(f"DEBUG: 当前数据节点名称: {current_data_node.GetName()}")
                
                # 策略1: 尝试从节点属性中获取Series Description
                series_desc = self._get_dicom_series_description_from_node(current_data_node)
                print(f"DEBUG: 从节点属性获取的Series Description: {series_desc}")
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    print(f"DEBUG: 返回节点属性中的Series Description: {series_desc}")
                    return series_desc
                
                # 策略2: 尝试从DICOM数据库中获取
                series_desc = self._get_dicom_series_description_from_database(current_data_node)
                print(f"DEBUG: 从数据库获取的Series Description: {series_desc}")
                if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                    print(f"DEBUG: 返回数据库中的Series Description: {series_desc}")
                    return series_desc
                
                # 策略3: 直接从DICOM文件读取（创建logic实例来调用方法）
                try:
                    import slicer
                    logic = slicer.modules.tavi_analytics.widgetRepresentation().self().logic
                    if logic and hasattr(logic, '_read_series_description_from_file'):
                        series_desc = logic._read_series_description_from_file(current_data_node)
                        print(f"DEBUG: 从DICOM文件直接读取的Series Description: {series_desc}")
                        if series_desc and series_desc not in ["Volume", "Volume_1", "Volume_2"]:
                            print(f"DEBUG: 返回DICOM文件中的Series Description: {series_desc}")
                            return series_desc
                except Exception as e:
                    print(f"DEBUG: 从DICOM文件读取时出错: {e}")
                
                # 策略4: 尝试从序列节点的索引值获取（如果有时间信息）
                series_desc = self._get_series_description_from_sequence_index(sequence_node, current_frame_index)
                print(f"DEBUG: 从序列索引获取的描述: {series_desc}")
                if series_desc:
                    return series_desc
                
                # 策略5: 从存储节点的文件路径获取信息
                series_desc = self._get_series_description_from_storage_node(current_data_node)
                print(f"DEBUG: 从存储节点获取的描述: {series_desc}")
                if series_desc:
                    return series_desc
                
                # 如果都没有找到，返回帧信息
                time_value = sequence_node.GetNthIndexValue(current_frame_index)
                if time_value:
                    result = f"Phase {time_value}% (帧 {current_frame_index + 1})"
                    print(f"DEBUG: 返回时间值描述: {result}")
                    return result
                else:
                    result = f"帧 {current_frame_index + 1}/{sequence_node.GetNumberOfDataNodes()}"
                    print(f"DEBUG: 返回帧数描述: {result}")
                    return result
            
            return f"帧 {current_frame_index + 1}"
            
        except Exception as e:
            print(f"获取Series Description时出错: {e}")
            import traceback
            traceback.print_exc()
            return "未知序列"
    
    def _get_dicom_series_description_from_node(self, node) -> Optional[str]:
        """从节点属性获取DICOM Series Description"""
        if not hasattr(node, 'GetAttribute'):
            print("DEBUG: 节点没有GetAttribute方法")
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
            print(f"DEBUG: 检查属性 {attr}: {value}")
            if value and value.strip():
                print(f"DEBUG: 在节点属性 {attr} 中找到Series Description: {value}")
                return value.strip()
        
        print("DEBUG: 在节点属性中未找到Series Description")
        return None
    
    def _get_dicom_series_description_from_database(self, node) -> Optional[str]:
        """从DICOM数据库获取Series Description"""
        try:
            import slicer
            db = slicer.dicomDatabase
            if not db or not db.isOpen:
                return None
            
            # 策略1: 直接通过Series UID获取（这是最可靠的方法）
            series_uid = node.GetAttribute('DICOM.SeriesInstanceUID')
            if not series_uid:
                # 尝试其他可能的属性名
                series_uid = node.GetAttribute('DICOM.0020,000E')
            
            if series_uid:
                try:
                    series_desc = db.seriesDescription(series_uid)
                    if series_desc and series_desc.strip():
                        return series_desc.strip()
                except Exception:
                    pass
            
            # 策略2: 如果有实例UID，通过遍历数据库查找匹配的系列
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
            print(f"从DICOM数据库获取Series Description时出错: {e}")
            
        return None
    
    def _get_series_description_from_sequence_index(self, sequence_node, frame_index) -> Optional[str]:
        """从序列索引值构建描述"""
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
        """从存储节点文件路径提取系列信息"""
        try:
            if hasattr(node, 'GetStorageNode'):
                storage_node = node.GetStorageNode()
                if storage_node and hasattr(storage_node, 'GetFileName'):
                    file_path = storage_node.GetFileName()
                    if file_path:
                        import os
                        # 从文件名提取可能的系列信息
                        filename = os.path.basename(file_path)
                        # 移除常见的文件扩展名
                        name_without_ext = os.path.splitext(filename)[0]
                        # 如果文件名包含有意义的信息，返回它
                        if len(name_without_ext) > 5 and not name_without_ext.startswith("IM"):
                            return name_without_ext
                            
        except Exception:
            pass
            
        return None
    
    def mark_phase(self, phase_name: str, frame_index: int, phase_percent: float, series_description: str = ""):
        """标记关键时相"""
        if phase_name in self.marked_phases:
            self.marked_phases[phase_name]['frame_index'] = frame_index
            self.marked_phases[phase_name]['phase_percent'] = phase_percent
            self.marked_phases[phase_name]['series_description'] = series_description
    
    def is_ready(self) -> bool:
        """检查模块一是否准备完成"""
        return (self.volume_sequence_node_id is not None and 
                self.patient_data.valveBrand != "" and 
                self.patient_data.valveModel != "")
    
    def reset(self):
        """重置会话"""
        self.patient_data = PatientData()
        self.volume_sequence_node_id = None
        self.sequence_browser_node_id = None
        self.marked_phases = {
            'end_diastole': {'frame_index': None, 'phase_percent': None, 'series_description': None},
            'end_systole': {'frame_index': None, 'phase_percent': None, 'series_description': None}
        }


class DataLoadingDialog(qt.QDialog):
    """数据加载和配置对话框
    
    要修改瓣膜品牌和型号的默认值，请修改以下类属性：
    - DEFAULT_VALVE_BRAND: 默认选择的瓣膜品牌
    - DEFAULT_VALVE_MODELS: 每个品牌对应的默认型号字典
    """
    
    # 瓣膜品牌和型号的默认值配置
    DEFAULT_VALVE_BRAND = "Medtronic"
    DEFAULT_VALVE_MODELS = {
        "Medtronic": "Evolut R/PRO",
        "Edwards Lifesciences": "SAPIEN 3",
        "Venus Medtech": "VenusA-Valve",
        "MicroPort": "VitaFlow",
        "Peijia Medical": "TaurusOne"
    }
    
    def __init__(self, parent=None, session=None, valve_config=None):
        super().__init__(parent)
        self.session = session or TAVRStudySession()
        self.valve_config = valve_config or {}
        self.logic = tavi_analyticsLogic()
        
        self.setWindowTitle("数据加载与配置")
        self.setModal(True)
        self.setMinimumSize(500, 700)
        
        self.setup_ui()
        self.setup_connections()
        
    def _get_widget_text(self, widget, method_name='text'):
        """安全获取Qt部件的文本，兼容属性和方法访问方式"""
        try:
            return getattr(widget, method_name)()
        except TypeError:
            return getattr(widget, method_name)
    
    def _get_widget_value(self, widget, method_name='value'):
        """安全获取Qt部件的值，兼容属性和方法访问方式"""
        try:
            return getattr(widget, method_name)()
        except TypeError:
            return getattr(widget, method_name)
        
    def setup_ui(self):
        """设置对话框界面"""
        layout = qt.QVBoxLayout(self)
        
        # 标题
        title_label = qt.QLabel("TAVR-Analytics 数据导入与配置")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; margin: 10px; }")
        layout.addWidget(title_label)
        
        # 数据加载区域
        self.create_data_loading_section(layout)
        
        # 患者信息区域
        self.create_patient_info_section(layout)
        
        # 按钮区域
        self.create_button_section(layout)
        
    def create_data_loading_section(self, parent_layout):
        """创建数据加载区域"""
        group_box = qt.QGroupBox("数据加载")
        layout = qt.QVBoxLayout(group_box)
        
        # 加载按钮
        self.load_button = qt.QPushButton("加载4D DICOM序列")
        self.load_button.setStyleSheet("QPushButton { font-size: 14px; padding: 10px; }")
        self.load_button.clicked.connect(self.on_load_data)
        layout.addWidget(self.load_button)
        
        # 序列信息显示
        self.sequence_info_label = qt.QLabel("未加载序列")
        self.sequence_info_label.setWordWrap(True)
        self.sequence_info_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        layout.addWidget(self.sequence_info_label)
        
        parent_layout.addWidget(group_box)
        
    def create_patient_info_section(self, parent_layout):
        """创建患者信息区域"""
        group_box = qt.QGroupBox("患者信息")
        layout = qt.QFormLayout(group_box)
        
        # 基本信息
        self.patient_id_edit = qt.QLineEdit()
        self.patient_id_edit.setPlaceholderText("必填项")
        
        self.patient_name_edit = qt.QLineEdit()
        
        self.patient_age_edit = qt.QSpinBox()
        self.patient_age_edit.setMaximum(150)
        
        self.patient_sex_combo = qt.QComboBox()
        self.patient_sex_combo.addItems(["", "男", "女"])
        
        # 日期信息
        self.surgery_date_edit = qt.QDateEdit()
        self.surgery_date_edit.setCalendarPopup(True)
        self.surgery_date_edit.setDate(qt.QDate.currentDate())
        
        self.ct_scan_date_edit = qt.QDateEdit()
        self.ct_scan_date_edit.setCalendarPopup(True)
        self.ct_scan_date_edit.setDate(qt.QDate.currentDate())
        
        # 图像质量和随访时间
        self.image_quality_combo = qt.QComboBox()
        self.image_quality_combo.addItems([q.value for q in ImageQuality])
        
        self.followup_timepoint_combo = qt.QComboBox()
        self.followup_timepoint_combo.addItems([t.value for t in FollowUpTimepoint])
        
        # 瓣膜信息（关键）
        valve_layout = qt.QHBoxLayout()
        self.valve_brand_combo = qt.QComboBox()
        self.valve_brand_combo.addItem("")
        self.valve_brand_combo.addItems(list(self.valve_config.keys()))
        
        # 设置瓣膜品牌预设值
        if self.valve_config:
            # 优先选择默认品牌，如果没有则选择第一个
            default_brand = self.DEFAULT_VALVE_BRAND if self.DEFAULT_VALVE_BRAND in self.valve_config else list(self.valve_config.keys())[0]
            brand_index = self.valve_brand_combo.findText(default_brand)
            if brand_index >= 0:
                self.valve_brand_combo.setCurrentIndex(brand_index)
        
        self.valve_model_combo = qt.QComboBox()
        
        valve_layout.addWidget(self.valve_brand_combo)
        valve_layout.addWidget(self.valve_model_combo)
        
        # 初始化瓣膜型号选项（基于默认品牌）
        self.initialize_valve_model_combo()
        
        # 可选评分
        self.sts_score_edit = qt.QDoubleSpinBox()
        self.sts_score_edit.setDecimals(2)
        self.sts_score_edit.setMaximum(100)
        
        self.euro_score_edit = qt.QDoubleSpinBox()
        self.euro_score_edit.setDecimals(2)
        self.euro_score_edit.setMaximum(100)
        
        # 添加到表单
        layout.addRow("受试者编号*:", self.patient_id_edit)
        layout.addRow("患者姓名:", self.patient_name_edit)
        layout.addRow("年龄:", self.patient_age_edit)
        layout.addRow("性别:", self.patient_sex_combo)
        layout.addRow("手术时间:", self.surgery_date_edit)
        layout.addRow("CT扫描时间:", self.ct_scan_date_edit)
        layout.addRow("图像质量:", self.image_quality_combo)
        layout.addRow("术后随访复查时间节点:", self.followup_timepoint_combo)
        layout.addRow("瓣膜品牌* | 瓣膜型号*:", valve_layout)
        layout.addRow("STS评分:", self.sts_score_edit)
        layout.addRow("EuroScore II:", self.euro_score_edit)
        
        parent_layout.addWidget(group_box)
        
    def initialize_valve_model_combo(self):
        """初始化瓣膜型号下拉菜单，包括设置默认值"""
        current_brand = self._get_widget_text(self.valve_brand_combo, 'currentText')
        self.valve_model_combo.clear()
        
        if current_brand and current_brand in self.valve_config:
            self.valve_model_combo.addItem("")
            models = self.valve_config[current_brand]
            self.valve_model_combo.addItems(models)
            
            # 设置默认型号
            if current_brand in self.DEFAULT_VALVE_MODELS and self.DEFAULT_VALVE_MODELS[current_brand] in models:
                model_index = self.valve_model_combo.findText(self.DEFAULT_VALVE_MODELS[current_brand])
                if model_index >= 0:
                    self.valve_model_combo.setCurrentIndex(model_index)
        
    def create_button_section(self, parent_layout):
        """创建按钮区域"""
        button_layout = qt.QHBoxLayout()
        
        self.cancel_button = qt.QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        self.confirm_button = qt.QPushButton("确认并继续")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14px; padding: 10px; }")
        self.confirm_button.clicked.connect(self.on_confirm)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        
        parent_layout.addLayout(button_layout)
        
    def setup_connections(self):
        """设置信号连接"""
        self.valve_brand_combo.currentTextChanged.connect(self.on_valve_brand_changed)
        
        # 监听必填项变化
        widgets_to_monitor = [
            self.patient_id_edit, self.valve_brand_combo, self.valve_model_combo
        ]
        for widget in widgets_to_monitor:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self.check_confirm_button_state)
            elif hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self.check_confirm_button_state)
                
    def on_load_data(self):
        """加载数据"""
        success = self.logic.wait_and_validate_loaded_sequence(self.session)
        
        if not success:
            success = self.logic.load_dicom_sequence()
            
        if success:
            self.update_sequence_info()
            self.parse_dicom_metadata()
            self.check_confirm_button_state()
            
    def update_sequence_info(self):
        """更新序列信息显示"""
        sequence_node = self.session.get_volume_sequence_node()
        if sequence_node:
            num_frames = sequence_node.GetNumberOfDataNodes()
            node_name = sequence_node.GetName()
            self.sequence_info_label.setText(f"已加载序列: {node_name} ({num_frames} 帧)")
            self.sequence_info_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
        else:
            self.sequence_info_label.setText("未加载序列")
            self.sequence_info_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
            
    def parse_dicom_metadata(self):
        """解析DICOM元数据"""
        try:
            self.logic.parse_dicom_metadata(self.session)
            self.update_patient_info_ui()
        except Exception as e:
            logging.warning(f"Failed to parse DICOM metadata: {e}")
            
    def update_patient_info_ui(self):
        """更新患者信息界面"""
        data = self.session.patient_data
        
        if data.patientID:
            self.patient_id_edit.setText(data.patientID)
        if data.patientName:
            self.patient_name_edit.setText(data.patientName)
        if data.patientAge > 0:
            self.patient_age_edit.setValue(data.patientAge)
        if data.patientSex:
            index = self.patient_sex_combo.findText(data.patientSex)
            if index >= 0:
                self.patient_sex_combo.setCurrentIndex(index)
        if data.ctScanDate:
            self.ct_scan_date_edit.setDate(qt.QDate(data.ctScanDate.year, data.ctScanDate.month, data.ctScanDate.day))
            
    def on_valve_brand_changed(self, brand):
        """瓣膜品牌变化处理"""
        self.valve_model_combo.clear()
        if brand and brand in self.valve_config:
            self.valve_model_combo.addItem("")
            models = self.valve_config[brand]
            self.valve_model_combo.addItems(models)
            
            # 设置默认型号
            if brand in self.DEFAULT_VALVE_MODELS and self.DEFAULT_VALVE_MODELS[brand] in models:
                model_index = self.valve_model_combo.findText(self.DEFAULT_VALVE_MODELS[brand])
                if model_index >= 0:
                    self.valve_model_combo.setCurrentIndex(model_index)
                    
        self.check_confirm_button_state()
        
    def check_confirm_button_state(self):
        """检查确认按钮状态"""
        has_sequence = self.session.volume_sequence_node_id is not None
        # Use utility method for safe text access
        patient_text = self._get_widget_text(self.patient_id_edit, 'text')
        has_patient_id = patient_text.strip() != ""
        
        valve_brand_text = self._get_widget_text(self.valve_brand_combo, 'currentText')
        has_valve_brand = valve_brand_text != ""
        
        valve_model_text = self._get_widget_text(self.valve_model_combo, 'currentText')
        has_valve_model = valve_model_text != ""
        
        enabled = has_sequence and has_patient_id and has_valve_brand and has_valve_model
        self.confirm_button.setEnabled(enabled)
        
        if not enabled:
            missing_items = []
            if not has_sequence:
                missing_items.append("4D DICOM序列")
            if not has_patient_id:
                missing_items.append("受试者编号")
            if not has_valve_brand:
                missing_items.append("瓣膜品牌")
            if not has_valve_model:
                missing_items.append("瓣膜型号")
            tooltip = "请完成以下必填项：\n" + "\n".join(f"- {item}" for item in missing_items)
            self.confirm_button.setToolTip(tooltip)
        else:
            self.confirm_button.setToolTip("确认并继续到心动周期管理")
            
    def on_confirm(self):
        """确认按钮处理"""
        self.save_patient_data_to_session()
        self.accept()
        
    def save_patient_data_to_session(self):
        """保存患者信息到会话"""
        data = self.session.patient_data
        # Use utility method for safe text access
        data.patientID = self._get_widget_text(self.patient_id_edit, 'text')
        data.patientName = self._get_widget_text(self.patient_name_edit, 'text')
        data.patientAge = self._get_widget_value(self.patient_age_edit, 'value')
        data.patientSex = self._get_widget_text(self.patient_sex_combo, 'currentText')
        
        # 修复QDate转换 - 兼容属性和方法两种访问方式
        surgery_qdate = self.surgery_date_edit.date() if callable(self.surgery_date_edit.date) else self.surgery_date_edit.date
        data.surgeryDate = datetime.date(surgery_qdate.year(), surgery_qdate.month(), surgery_qdate.day())
        
        ct_scan_qdate = self.ct_scan_date_edit.date() if callable(self.ct_scan_date_edit.date) else self.ct_scan_date_edit.date
        data.ctScanDate = datetime.date(ct_scan_qdate.year(), ct_scan_qdate.month(), ct_scan_qdate.day())
        
        data.imageQuality = ImageQuality(self._get_widget_text(self.image_quality_combo, 'currentText'))
        data.followUpTimepoint = FollowUpTimepoint(self._get_widget_text(self.followup_timepoint_combo, 'currentText'))
        data.valveBrand = self._get_widget_text(self.valve_brand_combo, 'currentText')
        data.valveModel = self._get_widget_text(self.valve_model_combo, 'currentText')
        sts_value = self._get_widget_value(self.sts_score_edit, 'value')
        data.stsScore = sts_value if sts_value > 0 else None
        euro_value = self._get_widget_value(self.euro_score_edit, 'value')
        data.euroScoreII = euro_value if euro_value > 0 else None


#
# tavi_analytics
#

class tavi_analytics(ScriptedLoadableModule):
    """TAVR-Analytics Workflow 3D Slicer插件主模块"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("TAVR Analytics")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Cardiac")]
        self.parent.dependencies = ["Sequences"]
        self.parent.contributors = ["TAVR Research Team"]
        self.parent.helpText = _("""
TAVR-Analytics Workflow插件用于经导管主动脉瓣置换术（TAVR）术后的四维心脏CT分析。
该插件提供完整的分析工作流，包括数据导入、场景准备、分割、测量和报告生成。
""")
        self.parent.acknowledgementText = _("""
该插件基于杭州方案术后CT核心实验室评估表开发，用于标准化TAVR术后分析流程。
""")


#
# tavi_analyticsWidget
#

class tavi_analyticsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """插件主界面类"""

    def __init__(self, parent=None) -> None:
        """初始化界面"""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self.session = TAVRStudySession()
        self.valve_config = {}
        self.data_loading_dialog = None
        
    def setup(self) -> None:
        """设置界面"""
        ScriptedLoadableModuleWidget.setup(self)
        
        # 加载简单的UI文件作为容器
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/tavi_analytics.ui"))
        self.layout.addWidget(uiWidget)
        
        # 创建逻辑类
        self.logic = tavi_analyticsLogic()
        
        # 加载瓣膜配置
        self.load_valve_config()
        
        # 创建主界面
        self.create_main_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 检查场景中是否已有序列数据，如果有则重新处理DICOM元数据
        self.check_and_process_existing_sequences()

    def load_valve_config(self):
        """加载瓣膜配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "Resources", "valve_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                self.valve_config = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load valve configuration: {e}")
            self.valve_config = {"未知品牌": ["未知型号"]}

    def create_main_ui(self):
        """创建主界面"""
        # 状态显示区域
        status_group = qt.QGroupBox("当前状态")
        status_layout = qt.QVBoxLayout(status_group)
        
        self.status_label = qt.QLabel("未配置数据")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; }")
        status_layout.addWidget(self.status_label)
        
        # 操作按钮区域
        button_layout = qt.QHBoxLayout()
        
        self.setup_data_button = qt.QPushButton("数据导入与配置")
        self.setup_data_button.setStyleSheet("QPushButton { font-size: 16px; padding: 15px; background-color: #2196F3; color: white; }")
        self.setup_data_button.clicked.connect(self.show_data_loading_dialog)
        button_layout.addWidget(self.setup_data_button)
        
        # 心动周期管理面板
        self.create_cardiac_cycle_section()
        
        # 添加到主布局
        self.layout.addWidget(status_group)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.cycle_management_widget)
        self.layout.addStretch()
        
        # 初始更新状态
        self.update_status_display()

    def show_data_loading_dialog(self):
        """显示数据加载对话框"""
        dialog = DataLoadingDialog(parent=self.parent, session=self.session, valve_config=self.valve_config)
        
        if dialog.exec_() == qt.QDialog.Accepted:
            # 用户确认了配置，激活心动周期管理
            self.activate_cardiac_cycle_management()
            self.update_status_display()

    def update_status_display(self):
        """更新状态显示"""
        if self.session.is_ready():
            patient_data = self.session.get_patient_data()
            valve_info = self.session.get_selected_valve()
            
            status_text = f"""
<b>数据已配置完成</b><br/>
<b>患者ID:</b> {patient_data.patientID}<br/>
<b>瓣膜:</b> {valve_info['brand']} - {valve_info['model']}<br/>
<b>序列:</b> {self.session.get_volume_sequence_node().GetName() if self.session.get_volume_sequence_node() else '未知'}
"""
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #e8f5e8; border: 1px solid #4CAF50; }")
            self.setup_data_button.setText("重新配置数据")
        else:
            self.status_label.setText("请点击下方按钮开始数据导入与配置")
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; }")
            self.setup_data_button.setText("数据导入与配置")

    def create_patient_info_section(self, parent_layout):
        """创建患者信息输入区域"""
        # 这个方法已经移动到DataLoadingDialog中，这里保留为空以避免错误
        pass

    def create_cardiac_cycle_section(self):
        """创建心动周期管理区域"""
        # 心动周期管理折叠面板
        self.cycle_management_widget = qt.QGroupBox("心动周期管理")
        self.cycle_management_widget.setVisible(False)  # 初始隐藏
        
        cycle_layout = qt.QVBoxLayout(self.cycle_management_widget)
        
        # 时相百分比显示
        self.phase_percent_label = qt.QLabel("当前时相: 0.0%")
        self.phase_percent_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_percent_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 10px; }")
        cycle_layout.addWidget(self.phase_percent_label)
        
        # Series Description 显示
        self.series_description_label = qt.QLabel("序列描述: 未加载")
        self.series_description_label.setAlignment(qt.Qt.AlignCenter)
        self.series_description_label.setStyleSheet("QLabel { font-size: 14px; margin: 5px; padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; }")
        self.series_description_label.setWordWrap(True)  # 允许文本换行
        cycle_layout.addWidget(self.series_description_label)
        
        # 心动周期时间轴滑块
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.valueChanged.connect(self.on_timeline_slider_changed)
        cycle_layout.addWidget(self.timeline_slider)
        
        # 时相标记按钮
        button_layout = qt.QHBoxLayout()
        
        self.mark_end_diastole_button = qt.QPushButton("标记舒张末期")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setStyleSheet("QPushButton { padding: 8px; background-color: #FF9800; color: white; }")
        self.mark_end_diastole_button.clicked.connect(lambda: self.mark_phase('end_diastole'))
        button_layout.addWidget(self.mark_end_diastole_button)
        
        self.mark_end_systole_button = qt.QPushButton("标记收缩末期")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setStyleSheet("QPushButton { padding: 8px; background-color: #9C27B0; color: white; }")
        self.mark_end_systole_button.clicked.connect(lambda: self.mark_phase('end_systole'))
        button_layout.addWidget(self.mark_end_systole_button)
        
        cycle_layout.addLayout(button_layout)
        
        # 已标记时相显示
        marked_phases_layout = qt.QVBoxLayout()
        self.end_diastole_label = qt.QLabel("舒张末期: 未标记")
        self.end_diastole_label.setStyleSheet("QLabel { padding: 5px; background-color: #fff3e0; border: 1px solid #ff9800; }")
        self.end_diastole_label.setWordWrap(True)  # 允许文本换行
        
        self.end_systole_label = qt.QLabel("收缩末期: 未标记")
        self.end_systole_label.setStyleSheet("QLabel { padding: 5px; background-color: #f3e5f5; border: 1px solid #9c27b0; }")
        self.end_systole_label.setWordWrap(True)  # 允许文本换行
        
        marked_phases_layout.addWidget(self.end_diastole_label)
        marked_phases_layout.addWidget(self.end_systole_label)
        cycle_layout.addLayout(marked_phases_layout)

    def setup_connections(self):
        """设置信号连接"""
        # 监听场景变化
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    def onSceneStartClose(self, caller, event):
        """场景关闭开始时的处理"""
        pass

    def onSceneEndClose(self, caller, event):
        """场景关闭结束时的处理"""
        # 重置会话
        self.session.reset()
        self.update_status_display()
        self.cycle_management_widget.setVisible(False)

    def check_and_process_existing_sequences(self):
        """检查并处理现有的序列数据"""
        try:
            # 查找场景中的序列节点
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
            
            if sequence_nodes and browser_nodes:
                print("DEBUG: 发现现有序列数据，正在重新处理DICOM元数据...")
                
                # 选择第一个序列节点
                sequence_node = sequence_nodes[0]
                browser_node = browser_nodes[0]
                
                # 更新会话
                self.session.volume_sequence_node_id = sequence_node.GetID()
                self.session.sequence_browser_node_id = browser_node.GetID()
                
                # 重新处理DICOM元数据
                self.logic.preserve_dicom_metadata(sequence_node)
                
                # 更新状态显示
                self.update_status_display()
                
                print("DEBUG: 完成现有序列数据的DICOM元数据处理")
                
        except Exception as e:
            print(f"DEBUG: 处理现有序列数据时出错: {e}")
            import traceback
            traceback.print_exc()

    def on_load_data_clicked(self):
        """处理加载数据按钮点击（已废弃，保留用于兼容性）"""
        pass

    def on_valve_brand_changed(self, brand):
        """处理瓣膜品牌选择变化（已废弃，保留用于兼容性）"""
        pass

    def check_confirm_button_state(self):
        """检查确认按钮状态（已废弃，保留用于兼容性）"""
        pass

    def on_confirm_clicked(self):
        """处理确认按钮点击（已废弃，保留用于兼容性）"""
        pass

    def save_patient_data_to_session(self):
        """保存患者信息到会话（已废弃，保留用于兼容性）"""
        pass

    def activate_cardiac_cycle_management(self):
        """激活心动周期管理"""
        sequence_node = self.session.get_volume_sequence_node()
        browser_node = self.session.get_sequence_browser_node()
        
        if sequence_node and browser_node:
            # 设置滑块范围
            num_frames = sequence_node.GetNumberOfDataNodes()
            self.timeline_slider.setMaximum(num_frames - 1)
            self.timeline_slider.setEnabled(True)
            
            # 启用标记按钮
            self.mark_end_diastole_button.setEnabled(True)
            self.mark_end_systole_button.setEnabled(True)
            
            # 显示管理面板
            self.cycle_management_widget.setVisible(True)
            
            # 初始化当前帧
            self.on_timeline_slider_changed(0)

    def update_sequence_info(self):
        """更新序列信息显示（已废弃，保留用于兼容性）"""
        pass

    def parse_dicom_metadata(self):
        """解析DICOM元数据并填充患者信息（已废弃，保留用于兼容性）"""
        pass

    def update_patient_info_ui(self):
        """更新患者信息界面（已废弃，保留用于兼容性）"""
        pass

    def on_timeline_slider_changed(self, value):
        """处理时间轴滑块变化"""
        browser_node = self.session.get_sequence_browser_node()
        sequence_node = self.session.get_volume_sequence_node()
        
        if browser_node and sequence_node:
            # 设置当前帧
            browser_node.SetSelectedItemNumber(value)
            
            # 获取并显示时相百分比
            try:
                index_value = sequence_node.GetNthIndexValue(value)
                phase_percent = float(index_value)
                self.phase_percent_label.setText(f"当前时相: {phase_percent:.1f}%")
            except:
                self.phase_percent_label.setText(f"当前时相: 帧 {value}")

            # 获取并显示Series Description
            series_desc = self.session.get_current_frame_series_description()
            self.series_description_label.setText(f"序列描述: {series_desc}")

    def mark_phase(self, phase_name):
        """标记关键时相"""
        browser_node = self.session.get_sequence_browser_node()
        sequence_node = self.session.get_volume_sequence_node()
        
        if browser_node and sequence_node:
            frame_index = browser_node.GetSelectedItemNumber()
            
            try:
                index_value = sequence_node.GetNthIndexValue(frame_index)
                phase_percent = float(index_value)
            except:
                phase_percent = 0.0
            
            # 获取当前帧的序列描述信息
            series_description = self.session.get_current_frame_series_description()
            
            # 保存到会话
            self.session.mark_phase(phase_name, frame_index, phase_percent, series_description)
            
            # 更新界面显示
            self.update_phase_labels()

    def update_phase_labels(self):
        """更新时相标记显示"""
        end_diastole = self.session.get_marked_phase('end_diastole')
        end_systole = self.session.get_marked_phase('end_systole')
        
        if end_diastole and end_diastole['frame_index'] is not None:
            phase_text = f"舒张末期: 已标记 @ {end_diastole['phase_percent']:.1f}%"
            if end_diastole.get('series_description'):
                phase_text += f"\n序列描述: {end_diastole['series_description']}"
            self.end_diastole_label.setText(phase_text)
        else:
            self.end_diastole_label.setText("舒张末期: 未标记")
            
        if end_systole and end_systole['frame_index'] is not None:
            phase_text = f"收缩末期: 已标记 @ {end_systole['phase_percent']:.1f}%"
            if end_systole.get('series_description'):
                phase_text += f"\n序列描述: {end_systole['series_description']}"
            self.end_systole_label.setText(phase_text)
        else:
            self.end_systole_label.setText("收缩末期: 未标记")

    def cleanup(self) -> None:
        """清理资源"""
        self.removeObservers()

    def enter(self) -> None:
        """进入模块"""
        pass

    def exit(self) -> None:
        """退出模块"""
        pass


#
# tavi_analyticsLogic
#

class tavi_analyticsLogic(ScriptedLoadableModuleLogic):
    """插件逻辑类"""

    def __init__(self) -> None:
        """初始化逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)

    def load_dicom_sequence(self) -> bool:
        """加载4D DICOM序列"""
        try:
            # 清理当前会话
            session = TAVRStudySession()
            session.reset()
            
            # 打开DICOM模块让用户导入和选择数据
            slicer.util.selectModule('DICOM')
            
            # 提示用户
            qt.QMessageBox.information(
                None, "导入DICOM数据", 
                "请在DICOM浏览器中导入并选择4D心脏CT序列数据。\n"
                "选择数据后，请点击'Load'按钮加载数据。\n"
                "加载完成后，请返回TAVR Analytics模块。"
            )
            
            # 等待用户加载数据，然后验证场景中的序列节点
            return self.wait_and_validate_loaded_sequence(session)
            
        except Exception as e:
            logging.error(f"Failed to load DICOM sequence: {e}")
            qt.QMessageBox.critical(None, "错误", f"加载DICOM序列失败: {str(e)}")
            return False

    def wait_and_validate_loaded_sequence(self, session: TAVRStudySession) -> bool:
        """等待并验证加载的序列数据"""
        # 检查场景中是否有序列节点
        sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
        
        if not sequence_nodes:
            # 如果没有序列节点，尝试创建一个对话框让用户选择现有的容积节点来创建序列
            return self.create_sequence_from_volumes(session)
        
        # 如果有多个序列节点，让用户选择
        if len(sequence_nodes) > 1:
            sequence_node = self.select_sequence_node(sequence_nodes)
        else:
            sequence_node = sequence_nodes[0]
            
        if not sequence_node:
            return False
            
        # 验证序列节点
        if not self.validate_sequence_node(sequence_node):
            qt.QMessageBox.warning(
                None, "无效序列", 
                "选择的序列不是有效的4D心脏CT数据。\n"
                "请确保序列包含多个时间点的容积数据。"
            )
            return False
        
        # 创建或获取序列浏览器节点
        browser_node = self.get_or_create_sequence_browser(sequence_node)
        if not browser_node:
            return False
            
        # 保存到会话
        session.volume_sequence_node_id = sequence_node.GetID()
        session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def create_sequence_from_volumes(self, session: TAVRStudySession) -> bool:
        """从现有容积节点创建序列"""
        volume_nodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
        
        if len(volume_nodes) < 2:
            qt.QMessageBox.warning(
                None, "数据不足", 
                "场景中需要至少2个容积节点来创建4D序列。\n"
                "请在DICOM浏览器中加载完整的4D心脏CT数据。"
            )
            return False
        
        # 询问用户是否要从现有容积创建序列
        reply = qt.QMessageBox.question(
            None, "创建序列", 
            f"发现{len(volume_nodes)}个容积节点。\n"
            "是否要将这些容积组合成4D序列？",
            qt.QMessageBox.Yes | qt.QMessageBox.No,
            qt.QMessageBox.Yes
        )
        
        if reply != qt.QMessageBox.Yes:
            return False
            
        # 创建序列节点
        sequence_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSequenceNode')
        sequence_node.SetName("4D_Cardiac_CT_Sequence")
        
        # 添加容积到序列
        for i, volume in enumerate(volume_nodes):
            # 假设时相百分比均匀分布
            phase_percent = (i * 100.0) / (len(volume_nodes) - 1)
            sequence_node.SetDataNodeAtValue(volume, str(phase_percent))
        
        sequence_node.SetIndexName("Phase")
        sequence_node.SetIndexUnit("%")
        
        # 创建序列浏览器
        browser_node = self.get_or_create_sequence_browser(sequence_node)
        if not browser_node:
            return False
            
        # 保存到会话
        session.volume_sequence_node_id = sequence_node.GetID()
        session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def select_sequence_node(self, sequence_nodes):
        """让用户选择序列节点"""
        dialog = qt.QDialog()
        dialog.setWindowTitle("选择4D序列")
        dialog.setModal(True)
        
        layout = qt.QVBoxLayout(dialog)
        
        label = qt.QLabel("发现多个序列，请选择4D心脏CT序列：")
        layout.addWidget(label)
        
        list_widget = qt.QListWidget()
        for node in sequence_nodes:
            item = qt.QListWidgetItem(f"{node.GetName()} ({node.GetNumberOfDataNodes()} 帧)")
            item.setData(qt.Qt.UserRole, node)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        
        button_layout = qt.QHBoxLayout()
        ok_button = qt.QPushButton("确定")
        cancel_button = qt.QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        selected_node = None
        
        def on_ok():
            current_item = list_widget.currentItem()
            if current_item:
                nonlocal selected_node
                selected_node = current_item.data(qt.Qt.UserRole)
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
            
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)
        
        if dialog.exec_() == qt.QDialog.Accepted:
            return selected_node
        return None

    def get_or_create_sequence_browser(self, sequence_node):
        """获取或创建序列浏览器节点"""
        # 检查是否已有浏览器节点
        browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
        
        for browser in browser_nodes:
            if browser.GetMasterSequenceNode() == sequence_node:
                return browser
        
        # 创建新的浏览器节点
        browser_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSequenceBrowserNode')
        browser_node.SetName(f"Browser_{sequence_node.GetName()}")
        browser_node.SetAndObserveMasterSequenceNodeID(sequence_node.GetID())
        
        # 创建代理节点
        proxy_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        proxy_node.SetName(f"Proxy_{sequence_node.GetName()}")
        browser_node.SetAndObserveProxyNode(proxy_node, sequence_node)
        
        # 尝试保存DICOM元数据到序列节点和代理节点
        self.preserve_dicom_metadata(sequence_node)
        
        return browser_node
    
    def preserve_dicom_metadata(self, sequence_node):
        """保存DICOM元数据到序列节点中的各个数据节点"""
        try:
            num_data_nodes = sequence_node.GetNumberOfDataNodes()
            logging.info(f"正在为 {num_data_nodes} 个数据节点保存DICOM元数据")
            
            for i in range(num_data_nodes):
                data_node = sequence_node.GetNthDataNode(i)
                if data_node:
                    # 尝试从原始DICOM源获取Series Description
                    series_desc = self._extract_series_description_from_dicom_sources(data_node)
                    
                    if series_desc:
                        # 保存到节点属性
                        data_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                        data_node.SetAttribute('SeriesDescription', series_desc)
                        data_node.SetAttribute('DICOM.0008,103E', series_desc)
                        data_node.SetAttribute('DICOM.0008,103e', series_desc)
                        
                        # 如果是第一个节点，也设置到序列节点
                        if i == 0:
                            sequence_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                            sequence_node.SetAttribute('SeriesDescription', series_desc)
                            
                        logging.info(f"为第 {i+1} 帧保存了Series Description: {series_desc}")
                    else:
                        # 如果无法获取Series Description，尝试通过实例UID从数据库直接读取
                        series_desc = self._get_series_description_by_instance_uid(data_node)
                        if series_desc:
                            data_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                            data_node.SetAttribute('SeriesDescription', series_desc)
                            data_node.SetAttribute('DICOM.0008,103E', series_desc)
                            data_node.SetAttribute('DICOM.0008,103e', series_desc)
                            if i == 0:
                                sequence_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                                sequence_node.SetAttribute('SeriesDescription', series_desc)
                            logging.info(f"通过实例UID为第 {i+1} 帧获取了Series Description: {series_desc}")
                        else:
                            # 最后尝试直接从DICOM文件读取
                            series_desc = self._read_series_description_from_file(data_node)
                            if series_desc:
                                data_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                                data_node.SetAttribute('SeriesDescription', series_desc)
                                data_node.SetAttribute('DICOM.0008,103E', series_desc)
                                data_node.SetAttribute('DICOM.0008,103e', series_desc)
                                if i == 0:
                                    sequence_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                                    sequence_node.SetAttribute('SeriesDescription', series_desc)
                                logging.info(f"从文件为第 {i+1} 帧读取了Series Description: {series_desc}")
                    
                    # 也尝试保存其他重要的DICOM属性
                    self._preserve_other_dicom_attributes(data_node)
                    
        except Exception as e:
            logging.warning(f"Failed to preserve DICOM metadata: {e}")
    
    def _get_series_description_by_instance_uid(self, data_node):
        """通过实例UID从DICOM数据库获取Series Description"""
        try:
            import slicer
            import os
            
            # 获取DICOM数据库
            dicom_db = slicer.dicomDatabase
            if not dicom_db or not dicom_db.isOpen:
                return None
            
            # 获取实例UID
            instance_uids = data_node.GetAttribute("DICOM.instanceUIDs")
            if instance_uids:
                # 分割为单个实例UID
                uid_list = instance_uids.split()
                
                if uid_list:
                    # 获取第一个实例UID
                    first_instance_uid = uid_list[0]
                    
                    # 从DICOM数据库获取文件路径
                    file_path = dicom_db.fileForInstance(first_instance_uid)
                    
                    if file_path and os.path.exists(file_path):
                        # 使用pydicom直接读取文件
                        try:
                            import pydicom
                            dcm = pydicom.dcmread(file_path, stop_before_pixels=True)
                            
                            # 通过标签(0008,103e)访问SeriesDescription
                            if (0x0008, 0x103e) in dcm:
                                series_desc = str(dcm[0x0008, 0x103e].value).strip()
                                if series_desc:
                                    return series_desc
                        except Exception as e:
                            logging.debug(f"Error reading DICOM file {file_path}: {e}")
            
            return None
        except Exception as e:
            logging.debug(f"Error in _get_series_description_by_instance_uid: {e}")
            return None
    
    def _read_series_description_from_file(self, data_node):
        """直接从DICOM文件读取Series Description"""
        try:
            if hasattr(data_node, 'GetStorageNode'):
                storage_node = data_node.GetStorageNode()
                if storage_node and hasattr(storage_node, 'GetFileName'):
                    file_path = storage_node.GetFileName()
                    if file_path:
                        try:
                            import pydicom
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
                        except ImportError:
                            logging.debug("pydicom not available for reading DICOM file")
                        except Exception as e:
                            logging.debug(f"Error reading DICOM file {file_path}: {e}")
        except Exception as e:
            logging.debug(f"Error in _read_series_description_from_file: {e}")
        return None
    
    def _extract_series_description_from_dicom_sources(self, data_node):
        """从各种DICOM源提取Series Description"""
        # 策略1: 检查是否已经有Series Description属性
        existing_desc = data_node.GetAttribute('DICOM.SeriesDescription')
        if existing_desc and existing_desc.strip():
            return existing_desc.strip()
        
        # 策略2: 通过实例UID从DICOM数据库直接读取（最可靠的方法）
        series_desc = self._get_series_description_by_instance_uid(data_node)
        if series_desc:
            return series_desc
        
        # 策略3: 直接从DICOM文件读取
        series_desc = self._read_series_description_from_file(data_node)
        if series_desc:
            return series_desc
        
        # 策略4: 从Subject Hierarchy获取
        try:
            import slicer
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
            import slicer
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
    
    def _preserve_other_dicom_attributes(self, data_node):
        """保存其他重要的DICOM属性"""
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
            if hasattr(data_node, 'GetStorageNode'):
                storage_node = data_node.GetStorageNode()
                if storage_node and hasattr(storage_node, 'GetFileName'):
                    file_path = storage_node.GetFileName()
                    if file_path:
                        try:
                            import pydicom
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
                                        
                        except ImportError:
                            # pydicom不可用
                            pass
                        except Exception as e:
                            logging.debug(f"Failed to read DICOM attributes from {file_path}: {e}")
                            
        except Exception as e:
            logging.warning(f"Failed to preserve other DICOM attributes: {e}")

    def validate_sequence_node(self, node) -> bool:
        """验证节点是否为有效的4D序列"""
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

    def parse_dicom_metadata(self, session: TAVRStudySession):
        """解析DICOM元数据并填充患者信息"""
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
            self.extract_dicom_info_from_database(first_volume, patient_data)
            
            # 如果无法从DICOM获取信息，设置默认值
            if not patient_data.patientID:
                # 生成临时ID
                import uuid
                patient_data.patientID = f"TEMP_{str(uuid.uuid4())[:8]}"
                
            if not patient_data.ctScanDate:
                patient_data.ctScanDate = datetime.date.today()
                
        except Exception as e:
            logging.warning(f"Failed to parse DICOM metadata: {e}")

    def extract_dicom_info_from_database(self, volume_node, patient_data):
        """从DICOM数据库提取患者信息"""
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
                
            # 查询患者信息 - 修正API调用
            try:
                # 尝试直接从实例ID获取文件
                file_path = dicom_db.fileForInstance(first_instance_uid)
                if file_path:
                    dicom_info = self.read_dicom_file_info(file_path)
                    if dicom_info:
                        self.populate_patient_data_from_dicom(dicom_info, patient_data)
            except:
                # 如果上述方法失败，尝试通过系列查询
                try:
                    series_uid = volume_node.GetAttribute("DICOM.series_uid")
                    if series_uid:
                        files = dicom_db.filesForSeries(series_uid)
                        if files:
                            file_path = files[0]
                            dicom_info = self.read_dicom_file_info(file_path)
                            if dicom_info:
                                self.populate_patient_data_from_dicom(dicom_info, patient_data)
                except:
                    pass
                    
        except Exception as e:
            logging.warning(f"Failed to extract DICOM info from database: {e}")

    def read_dicom_file_info(self, file_path):
        """读取DICOM文件信息"""
        try:
            import pydicom
            dcm = pydicom.dcmread(file_path)
            return dcm
        except ImportError:
            logging.warning("pydicom not available, using basic DICOM reading")
            return None
        except Exception as e:
            logging.warning(f"Failed to read DICOM file {file_path}: {e}")
            return None

    def populate_patient_data_from_dicom(self, dicom_info, patient_data):
        """从DICOM信息填充患者数据"""
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

    def get_dicom_tag_value(self, volume_node, tag):
        """获取DICOM标签值"""
        try:
            # 尝试从节点属性获取DICOM标签
            dicom_tag_name = f"DICOM.{tag}"
            value = volume_node.GetAttribute(dicom_tag_name)
            return value
        except:
            return None


#
# tavi_analyticsTest
#

class tavi_analyticsTest(ScriptedLoadableModuleTest):
    """测试类"""

    def setUp(self):
        """设置测试环境"""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """运行测试"""
        self.setUp()
        self.test_session_singleton()
        self.test_patient_data()

    def test_session_singleton(self):
        """测试会话单例模式"""
        session1 = TAVRStudySession()
        session2 = TAVRStudySession()
        self.assertEqual(session1, session2)

    def test_patient_data(self):
        """测试患者数据"""
        session = TAVRStudySession()
        session.reset()
        
        data = session.get_patient_data()
        self.assertIsInstance(data, PatientData)
        self.assertEqual(data.patientID, "")
        
        data.patientID = "TEST001"
        data.valveBrand = "Medtronic"
        data.valveModel = "Evolut R/PRO"
        
        valve_info = session.get_selected_valve()
        self.assertEqual(valve_info['brand'], "Medtronic")
        self.assertEqual(valve_info['model'], "Evolut R/PRO")

        self.delayDisplay("测试通过")
