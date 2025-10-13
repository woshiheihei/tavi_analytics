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
        self.dicom_section = None
        
        self.setWindowTitle("TAVR 数据导入向导")
        self.setModal(True)
        self.setMinimumSize(950, 750)
        
        self.setup_ui()
        self.setup_connections()
        
    def _get_widget_text(self, widget, method_name='text'):
        """安全获取Qt部件的文本，兼容属性和方法访问方式"""
        return QtUtils.get_widget_text(widget, method_name)
    
    def _get_widget_value(self, widget, method_name='value'):
        """安全获取Qt部件的值，兼容属性和方法访问方式"""
        return QtUtils.get_widget_value(widget, method_name)
        
    def setup_ui(self):
        """设置对话框界面 - 现代化垂直布局"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域以支持小屏幕
        scroll_area = qt.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(qt.QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        
        scroll_content = qt.QWidget()
        scroll_layout = qt.QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 标题栏
        self.create_header_section(scroll_layout)
        
        # 2. DICOM 导入区域（可折叠）
        self.create_dicom_section(scroll_layout)
        
        # 3. 患者信息区域
        self.create_patient_info_section_modern(scroll_layout)
        
        # 添加弹性空间
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 4. 底部操作按钮（固定在底部）
        self.create_action_buttons(main_layout)
        
        # 默认创建DICOM浏览器
        self.create_dicom_browser()
        
    def create_header_section(self, parent_layout):
        """创建优化的标题栏 - 现代简洁版本"""
        header_widget = qt.QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #1565C0;
                border-radius: 0px;
            }
        """)
        header_layout = qt.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 24, 32, 24)
        header_layout.setSpacing(20)
        
        # 左侧：标题和副标题
        title_container = qt.QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_layout = qt.QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        
        # 主标题
        title_label = qt.QLabel("TAVR 数据导入")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: white;
                background: transparent;
                letter-spacing: 0.5px;
            }
        """)
        title_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = qt.QLabel("导入 4D 心脏 CT 序列并配置患者信息")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: rgba(255, 255, 255, 0.85);
                background: transparent;
            }
        """)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_container, 1)
        
        # 右侧：步骤指示器
        steps_container = qt.QWidget()
        steps_container.setStyleSheet("background: transparent;")
        steps_layout = qt.QHBoxLayout(steps_container)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(16)
        
        # 步骤指示器
        self.step_indicators = []
        steps_info = [
            ("1", "导入数据"),
            ("2", "配置信息")
        ]
        
        for i, (number, label) in enumerate(steps_info):
            step_widget = self.create_step_indicator(number, label, i == 0)
            steps_layout.addWidget(step_widget)
            self.step_indicators.append(step_widget)
        
        header_layout.addWidget(steps_container)
        
        parent_layout.addWidget(header_widget)
    
    def create_step_indicator(self, number, label, is_active=False):
        """创建步骤指示器"""
        step_widget = qt.QWidget()
        step_widget.setStyleSheet("background: transparent;")
        step_layout = qt.QVBoxLayout(step_widget)
        step_layout.setContentsMargins(0, 0, 0, 0)
        step_layout.setSpacing(4)
        step_layout.setAlignment(qt.Qt.AlignCenter)
        
        # 圆形数字
        number_label = qt.QLabel(number)
        if is_active:
            number_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    color: #1565C0;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 32px;
                    max-width: 32px;
                    min-height: 32px;
                    max-height: 32px;
                    padding: 0px;
                    qproperty-alignment: AlignCenter;
                }
            """)
        else:
            number_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.3);
                    color: white;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 32px;
                    max-width: 32px;
                    min-height: 32px;
                    max-height: 32px;
                    padding: 0px;
                    qproperty-alignment: AlignCenter;
                }
            """)
        number_label.setAlignment(qt.Qt.AlignCenter)
        step_layout.addWidget(number_label, 0, qt.Qt.AlignCenter)
        
        # 步骤标签
        text_label = qt.QLabel(label)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
                background: transparent;
                font-weight: normal;
            }
        """)
        text_label.setAlignment(qt.Qt.AlignCenter)
        step_layout.addWidget(text_label, 0, qt.Qt.AlignCenter)
        
        return step_widget
    
    def create_dicom_section(self, parent_layout):
        """创建DICOM导入区域"""
        dicom_section = ctk.ctkCollapsibleButton()
        dicom_section.text = "📁 第一步：导入 DICOM 数据"
        dicom_section.collapsed = False
        dicom_section.setStyleSheet("""
            ctkCollapsibleButton {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
                color: #424242;
            }
            ctkCollapsibleButton:hover {
                border-color: #1976D2;
            }
        """)
        
        dicom_layout = qt.QVBoxLayout(dicom_section)
        dicom_layout.setSpacing(12)
        dicom_layout.setContentsMargins(16, 8, 16, 16)
        
        # 操作栏：导入按钮 + 序列状态
        action_bar = qt.QWidget()
        action_bar_layout = qt.QHBoxLayout(action_bar)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(12)
        
        # 导入按钮
        self.import_dicom_button = qt.QPushButton("📁 导入 DICOM 文件")
        self.import_dicom_button.setFixedHeight(40)
        self.import_dicom_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 0 24px;
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.import_dicom_button.setCursor(qt.Qt.PointingHandCursor)
        self.import_dicom_button.clicked.connect(self.on_import_dicom_files)
        action_bar_layout.addWidget(self.import_dicom_button)
        
        # 序列状态标签
        self.sequence_info_label = qt.QLabel("⏳ 等待导入 DICOM 序列...")
        self.sequence_info_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 10px 16px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 13px;
                color: #666;
            }
        """)
        action_bar_layout.addWidget(self.sequence_info_label, 1)
        
        dicom_layout.addWidget(action_bar)
        
        # DICOM 浏览器容器
        self.dicom_container = qt.QWidget()
        self.dicom_container.setVisible(True)
        container_layout = qt.QVBoxLayout(self.dicom_container)
        container_layout.setContentsMargins(0, 8, 0, 0)
        container_layout.setSpacing(0)
        
        dicom_layout.addWidget(self.dicom_container)
        
        parent_layout.addWidget(dicom_section)
    
    def create_patient_info_section_modern(self, parent_layout):
        """创建现代化的患者信息区域"""
        # 主容器
        info_section = ctk.ctkCollapsibleButton()
        info_section.text = "📋 第二步：配置患者信息"
        info_section.collapsed = False
        info_section.setStyleSheet("""
            ctkCollapsibleButton {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
                color: #424242;
            }
            ctkCollapsibleButton:hover {
                border-color: #1976D2;
            }
        """)
        
        section_layout = qt.QVBoxLayout(info_section)
        section_layout.setSpacing(16)
        section_layout.setContentsMargins(16, 12, 16, 16)
        
        # 基本信息卡片
        basic_card = self.create_info_card("基本信息", self.create_basic_info_form())
        section_layout.addWidget(basic_card)
        
        # 临床信息卡片
        clinical_card = self.create_info_card("临床信息", self.create_clinical_info_form())
        section_layout.addWidget(clinical_card)
        
        parent_layout.addWidget(info_section)
    
    def create_info_card(self, title, content_widget):
        """创建信息卡片"""
        card = qt.QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #424242;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                background-color: #fafafa;
            }
        """)
        
        card_layout = qt.QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 12)
        card_layout.addWidget(content_widget)
        
        return card
    
    def create_basic_info_form(self):
        """创建基本信息表单"""
        form_widget = qt.QWidget()
        form_layout = qt.QFormLayout(form_widget)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setFieldGrowthPolicy(qt.QFormLayout.ExpandingFieldsGrow)
        
        # 通用样式
        label_style = "QLabel { font-size: 13px; color: #424242; min-width: 140px; }"
        required_style = "QLabel { font-size: 13px; color: #f44336; font-weight: bold; }"
        input_style = """
            QLineEdit, QSpinBox, QComboBox, QDateEdit {
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border-color: #2196F3;
            }
        """
        
        # 受试者编号（必填）
        id_container = qt.QWidget()
        id_layout = qt.QHBoxLayout(id_container)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(4)
        
        id_label = qt.QLabel("受试者编号")
        id_label.setStyleSheet(label_style)
        id_required = qt.QLabel("*")
        id_required.setStyleSheet(required_style)
        id_layout.addWidget(id_label)
        id_layout.addWidget(id_required)
        id_layout.addStretch()
        
        self.patient_id_edit = qt.QLineEdit()
        self.patient_id_edit.setPlaceholderText("请输入受试者编号")
        self.patient_id_edit.setStyleSheet(input_style)
        form_layout.addRow(id_container, self.patient_id_edit)
        
        # 患者姓名
        name_label = qt.QLabel("患者姓名")
        name_label.setStyleSheet(label_style)
        self.patient_name_edit = qt.QLineEdit()
        self.patient_name_edit.setPlaceholderText("选填")
        self.patient_name_edit.setStyleSheet(input_style)
        form_layout.addRow(name_label, self.patient_name_edit)
        
        # 年龄和性别（同一行）
        age_sex_widget = qt.QWidget()
        age_sex_layout = qt.QHBoxLayout(age_sex_widget)
        age_sex_layout.setContentsMargins(0, 0, 0, 0)
        age_sex_layout.setSpacing(12)
        
        self.patient_age_edit = qt.QSpinBox()
        self.patient_age_edit.setMaximum(150)
        self.patient_age_edit.setSpecialValueText("未知")
        self.patient_age_edit.setStyleSheet(input_style)
        age_sex_layout.addWidget(self.patient_age_edit, 1)
        
        self.patient_sex_combo = qt.QComboBox()
        self.patient_sex_combo.addItems(["未知", "男", "女"])
        self.patient_sex_combo.setStyleSheet(input_style)
        age_sex_layout.addWidget(self.patient_sex_combo, 1)
        
        age_sex_label = qt.QLabel("年龄 / 性别")
        age_sex_label.setStyleSheet(label_style)
        form_layout.addRow(age_sex_label, age_sex_widget)
        
        # 手术时间和CT扫描时间（同一行）
        date_widget = qt.QWidget()
        date_layout = qt.QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(12)
        
        self.surgery_date_edit = qt.QDateEdit()
        self.surgery_date_edit.setCalendarPopup(True)
        self.surgery_date_edit.setDate(qt.QDate.currentDate())
        self.surgery_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.surgery_date_edit.setStyleSheet(input_style)
        date_layout.addWidget(self.surgery_date_edit, 1)
        
        self.ct_scan_date_edit = qt.QDateEdit()
        self.ct_scan_date_edit.setCalendarPopup(True)
        self.ct_scan_date_edit.setDate(qt.QDate.currentDate())
        self.ct_scan_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.ct_scan_date_edit.setStyleSheet(input_style)
        date_layout.addWidget(self.ct_scan_date_edit, 1)
        
        date_label = qt.QLabel("手术时间 / CT 扫描时间")
        date_label.setStyleSheet(label_style)
        form_layout.addRow(date_label, date_widget)
        
        return form_widget
    
    def create_clinical_info_form(self):
        """创建临床信息表单"""
        form_widget = qt.QWidget()
        form_layout = qt.QFormLayout(form_widget)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setFieldGrowthPolicy(qt.QFormLayout.ExpandingFieldsGrow)
        
        label_style = "QLabel { font-size: 13px; color: #424242; min-width: 140px; }"
        required_style = "QLabel { font-size: 13px; color: #f44336; font-weight: bold; }"
        input_style = """
            QLineEdit, QSpinBox, QComboBox, QDateEdit, QDoubleSpinBox {
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border-color: #2196F3;
            }
        """
        
        # 瓣膜品牌和型号（同一行，必填）
        valve_label_container = qt.QWidget()
        valve_label_layout = qt.QHBoxLayout(valve_label_container)
        valve_label_layout.setContentsMargins(0, 0, 0, 0)
        valve_label_layout.setSpacing(4)
        
        valve_label = qt.QLabel("瓣膜品牌 / 型号")
        valve_label.setStyleSheet(label_style)
        valve_required = qt.QLabel("*")
        valve_required.setStyleSheet(required_style)
        valve_label_layout.addWidget(valve_label)
        valve_label_layout.addWidget(valve_required)
        valve_label_layout.addStretch()
        
        valve_widget = qt.QWidget()
        valve_layout = qt.QHBoxLayout(valve_widget)
        valve_layout.setContentsMargins(0, 0, 0, 0)
        valve_layout.setSpacing(12)
        
        self.valve_brand_combo = qt.QComboBox()
        self.valve_brand_combo.addItem("请选择...")
        self.valve_brand_combo.addItems(list(self.valve_config.keys()))
        self.valve_brand_combo.setStyleSheet(input_style)
        valve_layout.addWidget(self.valve_brand_combo, 1)
        
        self.valve_model_combo = qt.QComboBox()
        self.valve_model_combo.setStyleSheet(input_style)
        valve_layout.addWidget(self.valve_model_combo, 1)
        
        # 设置瓣膜品牌预设值
        if self.valve_config:
            default_brand = self.DEFAULT_VALVE_BRAND if self.DEFAULT_VALVE_BRAND in self.valve_config else list(self.valve_config.keys())[0]
            brand_index = self.valve_brand_combo.findText(default_brand)
            if brand_index >= 0:
                self.valve_brand_combo.setCurrentIndex(brand_index)
        
        form_layout.addRow(valve_label_container, valve_widget)
        
        # 初始化瓣膜型号选项
        self.initialize_valve_model_combo()
        
        # 图像质量和随访时间点（同一行）
        quality_followup_widget = qt.QWidget()
        quality_followup_layout = qt.QHBoxLayout(quality_followup_widget)
        quality_followup_layout.setContentsMargins(0, 0, 0, 0)
        quality_followup_layout.setSpacing(12)
        
        self.image_quality_combo = qt.QComboBox()
        self.image_quality_combo.addItems([q.value for q in ImageQuality])
        self.image_quality_combo.setStyleSheet(input_style)
        quality_followup_layout.addWidget(self.image_quality_combo, 1)
        
        self.followup_timepoint_combo = qt.QComboBox()
        self.followup_timepoint_combo.addItems([t.value for t in FollowUpTimepoint])
        self.followup_timepoint_combo.setStyleSheet(input_style)
        quality_followup_layout.addWidget(self.followup_timepoint_combo, 1)
        
        quality_label = qt.QLabel("图像质量 / 随访时间点")
        quality_label.setStyleSheet(label_style)
        form_layout.addRow(quality_label, quality_followup_widget)
        
        # STS评分和EuroScore（同一行）
        score_widget = qt.QWidget()
        score_layout = qt.QHBoxLayout(score_widget)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(12)
        
        self.sts_score_edit = qt.QDoubleSpinBox()
        self.sts_score_edit.setDecimals(2)
        self.sts_score_edit.setMaximum(100)
        self.sts_score_edit.setSpecialValueText("未评估")
        self.sts_score_edit.setStyleSheet(input_style)
        score_layout.addWidget(self.sts_score_edit, 1)
        
        self.euro_score_edit = qt.QDoubleSpinBox()
        self.euro_score_edit.setDecimals(2)
        self.euro_score_edit.setMaximum(100)
        self.euro_score_edit.setSpecialValueText("未评估")
        self.euro_score_edit.setStyleSheet(input_style)
        score_layout.addWidget(self.euro_score_edit, 1)
        
        score_label = qt.QLabel("STS 评分 / EuroScore II")
        score_label.setStyleSheet(label_style)
        form_layout.addRow(score_label, score_widget)
        
        return form_widget
    
    def create_action_buttons(self, parent_layout):
        """创建底部操作按钮"""
        button_container = qt.QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
        """)
        button_layout = qt.QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 16, 20, 16)
        button_layout.setSpacing(12)
        
        # 取消按钮
        self.cancel_button = qt.QPushButton("取消")
        self.cancel_button.setFixedSize(100, 40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: white;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #999;
            }
        """)
        self.cancel_button.setCursor(qt.Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        # 必填项提示
        self.required_hint_label = qt.QLabel("* 表示必填项")
        self.required_hint_label.setStyleSheet("QLabel { font-size: 12px; color: #999; background: transparent; }")
        button_layout.addWidget(self.required_hint_label)
        
        button_layout.addStretch()
        
        # 确认按钮
        self.confirm_button = qt.QPushButton("✓ 确认并继续")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setFixedSize(150, 40)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:pressed:enabled {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #999;
            }
        """)
        self.confirm_button.setCursor(qt.Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        
        parent_layout.addWidget(button_container)
        
    def initialize_valve_model_combo(self):
        """初始化瓣膜型号下拉菜单，包括设置默认值"""
        current_brand = self._get_widget_text(self.valve_brand_combo, 'currentText')
        self.valve_model_combo.clear()
        
        if current_brand and current_brand != "请选择..." and current_brand in self.valve_config:
            self.valve_model_combo.addItem("请选择...")
            models = self.valve_config[current_brand]
            self.valve_model_combo.addItems(models)
            
            # 设置默认型号
            if current_brand in self.DEFAULT_VALVE_MODELS and self.DEFAULT_VALVE_MODELS[current_brand] in models:
                model_index = self.valve_model_combo.findText(self.DEFAULT_VALVE_MODELS[current_brand])
                if model_index >= 0:
                    self.valve_model_combo.setCurrentIndex(model_index)
        
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
    
    def on_import_dicom_files(self):
        """导入DICOM文件"""
        try:
            import DICOMLib
            
            # 使用文件对话框选择DICOM文件夹
            file_dialog = qt.QFileDialog(self)
            file_dialog.setFileMode(qt.QFileDialog.Directory)
            file_dialog.setWindowTitle("选择包含DICOM文件的文件夹")
            file_dialog.setOption(qt.QFileDialog.ShowDirsOnly, True)
            
            if file_dialog.exec_():
                import_dir = file_dialog.selectedFiles()[0]
                
                # 显示进度对话框
                progress = qt.QProgressDialog("正在导入DICOM文件...", "取消", 0, 0, self)
                progress.setWindowModality(qt.Qt.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                qt.QApplication.processEvents()
                
                try:
                    # 使用 DICOMLib.importDicom 导入文件
                    # 这是Slicer推荐的标准方式
                    DICOMLib.importDicom(import_dir, slicer.dicomDatabase)
                    
                    progress.close()
                    
                    # 刷新DICOM浏览器显示
                    if self.dicom_browser:
                        try:
                            # 方法1: 尝试使用 setDatabaseDirectory 刷新
                            if hasattr(self.dicom_browser, 'setDatabaseDirectory'):
                                current_db = slicer.dicomDatabase.databaseDirectory
                                self.dicom_browser.setDatabaseDirectory(current_db)
                                logging.info("DICOM浏览器已刷新")
                        except Exception as refresh_error:
                            logging.warning(f"Failed to refresh DICOM browser: {refresh_error}")
                    
                    # 记录导入成功
                    logging.info(f"Successfully imported DICOM files from: {import_dir}")
                    
                    qt.QMessageBox.information(self, "导入成功", 
                        f"DICOM文件已成功导入到数据库。\n\n请在DICOM浏览器中选择并加载序列。")
                        
                except Exception as import_error:
                    progress.close()
                    logging.error(f"Failed to import DICOM directory: {import_error}")
                    qt.QMessageBox.warning(self, "导入失败", 
                        f"导入DICOM文件时出错:\n{str(import_error)}\n\n请检查文件夹中是否包含有效的DICOM文件。")
                    
        except Exception as e:
            logging.error(f"Failed to open import dialog: {e}")
            qt.QMessageBox.warning(self, "错误", 
                f"无法打开导入对话框:\n{str(e)}\n\n请使用右侧DICOM浏览器的Import按钮手动导入。")
            
    def update_sequence_info(self):
        """更新序列信息显示"""
        sequence_node = self.session.get_volume_sequence_node()
        if sequence_node:
            num_frames = sequence_node.GetNumberOfDataNodes()
            node_name = sequence_node.GetName()
            self.sequence_info_label.setText(f"✅ 已加载: {node_name} ({num_frames} 帧)")
            self.sequence_info_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e9;
                    padding: 10px 16px;
                    border: 1px solid #4CAF50;
                    border-radius: 6px;
                    font-size: 13px;
                    color: #2e7d32;
                }
            """)
            # 更新步骤指示器：激活第二步
            self.update_step_indicator(1)
        else:
            self.sequence_info_label.setText("⏳ 等待导入 DICOM 序列...")
            self.sequence_info_label.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    padding: 10px 16px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    font-size: 13px;
                    color: #666;
                }
            """)
            # 更新步骤指示器：激活第一步
            self.update_step_indicator(0)
    
    def update_step_indicator(self, active_step_index):
        """更新步骤指示器状态
        
        Args:
            active_step_index: 当前激活步骤的索引 (0-based)
        """
        if not hasattr(self, 'step_indicators') or not self.step_indicators:
            return
            
        for i, step_widget in enumerate(self.step_indicators):
            # 获取步骤中的圆形数字标签（第一个子widget）
            step_layout = step_widget.layout()
            if step_layout and step_layout.count() > 0:
                number_label = step_layout.itemAt(0).widget()
                if number_label:
                    if i == active_step_index:
                        # 激活状态
                        number_label.setStyleSheet("""
                            QLabel {
                                background-color: white;
                                color: #1565C0;
                                border-radius: 16px;
                                font-size: 13px;
                                font-weight: bold;
                                min-width: 32px;
                                max-width: 32px;
                                min-height: 32px;
                                max-height: 32px;
                                padding: 0px;
                                qproperty-alignment: AlignCenter;
                            }
                        """)
                    elif i < active_step_index:
                        # 已完成状态
                        number_label.setStyleSheet("""
                            QLabel {
                                background-color: rgba(76, 175, 80, 0.9);
                                color: white;
                                border-radius: 16px;
                                font-size: 13px;
                                font-weight: bold;
                                min-width: 32px;
                                max-width: 32px;
                                min-height: 32px;
                                max-height: 32px;
                                padding: 0px;
                                qproperty-alignment: AlignCenter;
                            }
                        """)
                    else:
                        # 未激活状态
                        number_label.setStyleSheet("""
                            QLabel {
                                background-color: rgba(255, 255, 255, 0.3);
                                color: white;
                                border-radius: 16px;
                                font-size: 13px;
                                font-weight: bold;
                                min-width: 32px;
                                max-width: 32px;
                                min-height: 32px;
                                max-height: 32px;
                                padding: 0px;
                                qproperty-alignment: AlignCenter;
                            }
                        """)
    
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
        
        # 记录保存的数据用于调试
        logging.info(f"保存患者数据到session: ID='{data.patientID}', 瓣膜品牌='{data.valveBrand}', 瓣膜型号='{data.valveModel}'")
        logging.info(f"保存后session状态: 序列节点ID={self.session.volume_sequence_node_id}, is_ready={self.session.is_ready()}")
        
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
                            # 查找对应的序列浏览器节点
                            browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
                            browser_node_id = None
                            for browser_node in browser_nodes:
                                if browser_node.GetMasterSequenceNode() == seq_node:
                                    browser_node_id = browser_node.GetID()
                                    break
                            
                            # 使用session的标准方法设置序列数据
                            if browser_node_id:
                                self.session.set_volume_sequence_data(seq_node.GetID(), browser_node_id)
                                logging.info(f"检测到新的序列节点: {seq_node.GetName()}, 浏览器节点: {browser_node_id}")
                            else:
                                # 如果没有找到浏览器节点，仍设置序列节点ID
                                self.session.volume_sequence_node_id = seq_node.GetID()
                                logging.warning(f"检测到新的序列节点: {seq_node.GetName()}, 但未找到对应的浏览器节点")
                                # 尝试创建浏览器节点
                                try:
                                    browser_logic = slicer.modules.sequences.logic()
                                    browser_node = browser_logic.AddSynchronizedNode(seq_node, None, None)
                                    if browser_node:
                                        browser_node_id = browser_node.GetID()
                                        self.session.set_volume_sequence_data(seq_node.GetID(), browser_node_id)
                                        logging.info(f"已为序列节点创建浏览器节点: {browser_node_id}")
                                except Exception as e:
                                    logging.warning(f"创建浏览器节点失败: {e}")
                            
                            # 记录当前session状态用于调试
                            logging.info(f"Session状态 - 序列节点ID: {self.session.volume_sequence_node_id}, 浏览器节点ID: {self.session.sequence_browser_node_id}")
                            logging.info(f"Session is_ready: {self.session.is_ready()}")
                            
                            self.update_sequence_info()
                            self.parse_dicom_metadata()
                            self.check_confirm_button_state()
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
