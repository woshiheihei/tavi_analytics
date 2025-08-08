import logging
import datetime
import os
from typing import Optional, Dict, Any

import qt
import slicer
import ctk

# 导入重构后的核心模块
try:
    # 尝试相对导入（用于包内导入）
    from ..core.data_models import PatientData
    from ..core.enums import ImageQuality, FollowUpTimepoint
    from ..core.session import TAVRStudySession
    from ..utils.dicom_utils import DicomUtils
    from ..utils.config_manager import ConfigManager
    from ..utils.qt_utils import QtUtils
    from ..utils.logging_utils import LoggingUtils
except ImportError:
    # 回退到绝对导入（用于3D Slicer直接加载）
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.data_models import PatientData
    from core.enums import ImageQuality, FollowUpTimepoint
    from core.session import TAVRStudySession
    from utils.dicom_utils import DicomUtils
    from utils.config_manager import ConfigManager
    from utils.qt_utils import QtUtils
    from utils.logging_utils import LoggingUtils


class DataLoadingDialog(qt.QDialog):
    """数据加载和配置对话框
    
    要修改瓣膜品牌和型号的默认值，请修改以下类属性：
    - DEFAULT_VALVE_BRAND: 默认选择的瓣膜品牌
    - DEFAULT_VALVE_MODELS: 每个品牌对应的默认型号字典
    """
    
    # 信号定义
    dataLoaded = qt.Signal()  # 数据加载完成信号
    
    # 瓣膜品牌和型号的默认值配置
    DEFAULT_VALVE_BRAND = "Medtronic"
    DEFAULT_VALVE_MODELS = {
        "Medtronic": "Evolut R/PRO",
        "Edwards Lifesciences": "SAPIEN 3",
        "Venus Medtech": "VenusA-Valve",
        "MicroPort": "VitaFlow",
        "Peijia Medical": "TaurusOne"
    }
    
    def __init__(self, parent=None, session=None, valve_config=None, logic=None):
        """初始化数据加载对话框
        
        Args:
            parent: 父窗口
            session: TAVRStudySession实例
            valve_config: 瓣膜配置字典
            logic: 业务逻辑实例
        """
        super().__init__(parent)
        self.session = session or TAVRStudySession()
        self.valve_config = valve_config or {}
        self.logic = logic
        
        # DICOM相关组件
        self.dicom_browser = None
        self.dicom_panel_visible = False
        
        self.setWindowTitle("数据加载与配置")
        self.setModal(True)
        self.setMinimumSize(800, 700)  # 增加最小宽度以容纳DICOM面板
        
        self.setup_ui()
        self.setup_connections()
        
    def _get_widget_text(self, widget, method_name='text'):
        """安全获取Qt部件的文本，兼容属性和方法访问方式"""
        return QtUtils.get_widget_text(widget, method_name)
    
    def _get_widget_value(self, widget, method_name='value'):
        """安全获取Qt部件的值，兼容属性和方法访问方式"""
        return QtUtils.get_widget_value(widget, method_name)
        
    def setup_ui(self):
        """设置对话框界面"""
        # 创建主水平布局
        main_layout = qt.QHBoxLayout(self)
        
        # 左侧：原有的配置面板
        left_panel = qt.QWidget()
        left_layout = qt.QVBoxLayout(left_panel)
        
        # 标题
        title_label = qt.QLabel("TAVR-Analytics 数据导入与配置")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; margin: 10px; }")
        left_layout.addWidget(title_label)
        
        # 数据加载区域
        self.create_data_loading_section(left_layout)
        
        # 患者信息区域
        self.create_patient_info_section(left_layout)
        
        # 按钮区域
        self.create_button_section(left_layout)
        
        # 设置左侧面板最小宽度
        left_panel.setMinimumWidth(400)
        left_panel.setMaximumWidth(500)
        
        # 右侧：DICOM面板
        self.right_panel = qt.QWidget()
        self.right_panel.setVisible(False)  # 初始隐藏
        right_layout = qt.QVBoxLayout(self.right_panel)
        
        # DICOM面板标题
        dicom_title = qt.QLabel("DICOM 数据库")
        dicom_title.setAlignment(qt.Qt.AlignCenter)
        dicom_title.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 5px; }")
        right_layout.addWidget(dicom_title)
        
        # DICOM浏览器容器
        self.dicom_container = qt.QWidget()
        container_layout = qt.QVBoxLayout(self.dicom_container)
        right_layout.addWidget(self.dicom_container)
        
        # 设置右侧面板最小宽度
        self.right_panel.setMinimumWidth(600)
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.right_panel)
        
    def create_data_loading_section(self, parent_layout):
        """创建数据加载区域"""
        group_box = qt.QGroupBox("数据加载")
        layout = qt.QVBoxLayout(group_box)
        
        # 加载按钮
        self.load_button = qt.QPushButton("加载4D DICOM序列")
        self.load_button.setStyleSheet("QPushButton { font-size: 14px; padding: 10px; }")
        self.load_button.clicked.connect(self.on_load_data)
        layout.addWidget(self.load_button)
        
        # 显示DICOM数据库按钮
        self.show_dicom_button = qt.QPushButton("显示 DICOM 数据库")
        self.show_dicom_button.setStyleSheet("QPushButton { font-size: 12px; padding: 8px; background-color: #2196F3; color: white; }")
        self.show_dicom_button.clicked.connect(self.toggle_dicom_panel)
        layout.addWidget(self.show_dicom_button)
        
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
        if self.logic is None:
            logging.error("Logic instance is None. Cannot load data.")
            return
            
        success = self.logic.wait_and_validate_loaded_sequence()
        
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
            DicomUtils.parse_dicom_metadata(self.session)
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
        
        # 发出数据加载完成信号
        self.dataLoaded.emit()
        
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
        
    def toggle_dicom_panel(self):
        """切换DICOM面板的显示状态"""
        try:
            if self.dicom_panel_visible:
                self.hide_dicom_panel()
            else:
                self.show_dicom_panel()
        except Exception as e:
            logging.error(f"Failed to toggle DICOM panel: {e}")
            qt.QMessageBox.warning(self, "错误", f"无法切换DICOM面板: {str(e)}")
    
    def show_dicom_panel(self):
        """显示DICOM数据库面板"""
        try:
            if not self.dicom_browser:
                self.create_dicom_browser()
            
            # 显示右侧面板
            self.right_panel.setVisible(True)
            self.dicom_panel_visible = True
            
            # 更新按钮文本
            self.show_dicom_button.setText("隐藏 DICOM 数据库")
            self.show_dicom_button.setStyleSheet("QPushButton { font-size: 12px; padding: 8px; background-color: #f44336; color: white; }")
            
            # 调整对话框大小
            self.resize(1400, 700)
            
            logging.info("DICOM数据库面板已显示")
            
        except Exception as e:
            logging.error(f"Failed to show DICOM panel: {e}")
            qt.QMessageBox.warning(self, "错误", f"无法显示DICOM面板: {str(e)}")
    
    def hide_dicom_panel(self):
        """隐藏DICOM数据库面板"""
        try:
            # 隐藏右侧面板
            self.right_panel.setVisible(False)
            self.dicom_panel_visible = False
            
            # 更新按钮文本
            self.show_dicom_button.setText("显示 DICOM 数据库")
            self.show_dicom_button.setStyleSheet("QPushButton { font-size: 12px; padding: 8px; background-color: #2196F3; color: white; }")
            
            # 调整对话框大小
            self.resize(800, 700)
            
            logging.info("DICOM数据库面板已隐藏")
            
        except Exception as e:
            logging.error(f"Failed to hide DICOM panel: {e}")
    
    def create_dicom_browser(self):
        """创建DICOM浏览器"""
        try:
            # 创建完整的Slicer DICOM数据库浏览器
            import DICOMLib
            self.dicom_browser = DICOMLib.SlicerDICOMBrowser()
            
            # 设置浏览器的一些属性
            self.dicom_browser.setMinimumSize(580, 600)
            
            # 将浏览器添加到容器中
            container_layout = self.dicom_container.layout()
            if container_layout is None:
                container_layout = qt.QVBoxLayout(self.dicom_container)
            
            container_layout.addWidget(self.dicom_browser)
            
            # 添加说明标签
            info_label = qt.QLabel("使用上方完整的DICOM数据库面板导入和加载4D心脏CT序列。\n该面板包含Import、Load等完整功能，加载完成后数据将自动在左侧显示。")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("QLabel { font-size: 11px; color: #333; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; }")
            container_layout.addWidget(info_label)
            
            # 监听DICOM数据库变化和场景变化
            self.setup_dicom_monitoring()
            
            logging.info("完整的Slicer DICOM浏览器创建成功")
            
        except Exception as e:
            logging.error(f"Failed to create DICOM browser: {e}")
            raise
    
    def setup_dicom_monitoring(self):
        """设置DICOM数据监听"""
        try:
            # 监听DICOM数据库变化
            if slicer.dicomDatabase:
                slicer.dicomDatabase.databaseChanged.connect(self.on_dicom_database_changed)
            
            # 监听3D Slicer场景中节点的添加
            if slicer.mrmlScene:
                slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.on_node_added)
            
            logging.info("DICOM监听设置完成")
            
        except Exception as e:
            logging.warning(f"Failed to setup DICOM monitoring: {e}")
    
    def on_dicom_database_changed(self):
        """DICOM数据库变化时的处理"""
        try:
            logging.info("DICOM数据库发生变化")
            # 延迟检查，给3D Slicer时间处理加载
            qt.QTimer.singleShot(1000, self.check_for_new_sequences)
        except Exception as e:
            logging.warning(f"Error handling DICOM database change: {e}")
    
    def on_node_added(self, caller, event):
        """当3D Slicer场景中添加新节点时的处理"""
        try:
            # 延迟检查，避免在节点创建过程中检查
            qt.QTimer.singleShot(500, self.check_for_new_sequences)
        except Exception as e:
            logging.warning(f"Error handling node added: {e}")
    
    def check_for_new_sequences(self):
        """检查是否有新的序列被加载"""
        try:
            # 检查是否有新的序列节点
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            volume_nodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
            
            if sequence_nodes:
                # 如果有序列节点，优先使用序列节点
                for seq_node in sequence_nodes:
                    if seq_node.GetNumberOfDataNodes() > 1:  # 确保是多帧序列
                        if not self.session.volume_sequence_node_id or self.session.volume_sequence_node_id != seq_node.GetID():
                            self.session.volume_sequence_node_id = seq_node.GetID()
                            self.update_sequence_info()
                            self.parse_dicom_metadata()
                            self.check_confirm_button_state()
                            logging.info(f"检测到新的序列节点: {seq_node.GetName()}")
                            break
            elif len(volume_nodes) > 1:
                # 如果有多个容积节点但没有序列节点，询问用户是否创建序列
                self.offer_sequence_creation_from_volumes()
            elif len(volume_nodes) == 1:
                # 如果只有一个容积节点，也更新信息
                volume_node = volume_nodes[0]
                if not self.session.volume_sequence_node_id:
                    # 为单个容积节点创建一个临时的"序列"标识
                    logging.info(f"检测到新的容积节点: {volume_node.GetName()}")
                    self.update_volume_info(volume_node)
                    self.parse_dicom_metadata()
                    self.check_confirm_button_state()
                    
        except Exception as e:
            logging.warning(f"Error checking for new sequences: {e}")
    
    def offer_sequence_creation_from_volumes(self):
        """询问用户是否要从多个容积创建序列"""
        try:
            volume_nodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
            
            # 避免重复询问
            if hasattr(self, '_sequence_creation_offered'):
                return
            self._sequence_creation_offered = True
            
            reply = qt.QMessageBox.question(
                self, "创建4D序列", 
                f"检测到{len(volume_nodes)}个容积节点。\n这些可能是4D心脏CT的不同时相。\n\n是否要将它们组合成4D序列？",
                qt.QMessageBox.Yes | qt.QMessageBox.No,
                qt.QMessageBox.Yes
            )
            
            if reply == qt.QMessageBox.Yes and self.logic:
                success = self.logic.create_sequence_from_volumes()
                if success:
                    logging.info("从容积节点成功创建4D序列")
                    # 重新检查序列
                    qt.QTimer.singleShot(500, self.check_for_new_sequences)
                    
        except Exception as e:
            logging.warning(f"Failed to offer sequence creation: {e}")
    
    def update_volume_info(self, volume_node):
        """更新单个容积节点的信息显示"""
        try:
            node_name = volume_node.GetName()
            self.sequence_info_label.setText(f"已加载容积: {node_name}")
            self.sequence_info_label.setStyleSheet("QLabel { background-color: #fff3cd; padding: 5px; border: 1px solid #ffeaa7; }")
        except Exception as e:
            logging.warning(f"Failed to update volume info: {e}")
    
    def on_dicom_series_selected(self):
        """当DICOM序列被选择时的处理（保留用于将来扩展）"""
        try:
            if self.dicom_browser:
                # 完整的SlicerDICOMBrowser已经包含所有必要的功能
                # 这里可以添加额外的选择处理逻辑
                logging.debug("DICOM序列选择事件")
        except Exception as e:
            logging.debug(f"Error handling DICOM series selection: {e}")
    
    def create_sequence_from_loaded_volumes(self):
        """从已加载的容积创建序列（由自动监听调用）"""
        try:
            if self.logic:
                success = self.logic.create_sequence_from_volumes()
                if success:
                    logging.info("从容积节点成功创建4D序列")
                    # 重置标记，允许下次询问
                    if hasattr(self, '_sequence_creation_offered'):
                        delattr(self, '_sequence_creation_offered')
        except Exception as e:
            logging.warning(f"Failed to create sequence from loaded volumes: {e}")
    
    def cleanup_dicom_monitoring(self):
        """清理DICOM监听"""
        try:
            # 断开信号连接
            if slicer.dicomDatabase:
                slicer.dicomDatabase.databaseChanged.disconnect(self.on_dicom_database_changed)
            
            if slicer.mrmlScene:
                slicer.mrmlScene.RemoveObserver(slicer.mrmlScene.NodeAddedEvent)
                
        except Exception as e:
            logging.debug(f"Error cleaning up DICOM monitoring: {e}")
    
    def closeEvent(self, event):
        """对话框关闭时清理资源"""
        try:
            self.cleanup_dicom_monitoring()
        except:
            pass
        super().closeEvent(event)
