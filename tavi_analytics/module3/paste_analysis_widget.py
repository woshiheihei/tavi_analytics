"""
PASTE分析界面组件

瓣叶功能评估（PASTE Analysis）的用户界面实现，包含：
- HALT (低密度瓣叶增厚) 分析
- RELM (瓣叶活动度减退) 分析  
- SFD (窦内充盈缺损) 分析
- PFD (瓣叶下充盈缺损) 分析
"""
import logging
from typing import Optional, Dict, Any
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from .paste_analysis_logic import PasteAnalysisLogic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    # 添加父目录和当前目录到sys.path
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from paste_analysis_logic import PasteAnalysisLogic


class HaltAnalysisSection(qt.QWidget):
    """HALT (低密度瓣叶增厚) 分析区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HaltAnalysisSection")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置HALT分析界面"""
        main_layout = LayoutManager.create_layout(LayoutType.FORM_CONTAINER, self)
        
        # 瓣叶选择
        self.leaflet_combo = qt.QComboBox()
        self.leaflet_combo.addItems(["选择瓣叶...", "LC", "RC", "NC"])
        self.leaflet_combo.currentTextChanged.connect(self._on_leaflet_changed)
        main_layout.addRow("瓣叶:", self.leaflet_combo)
        
        # 分割控制
        self.start_segment_btn = LayoutManager.create_button_with_style(
            "开始标记", "primary", "default", 40
        )
        self.start_segment_btn.clicked.connect(self._on_start_segmentation)
        self.start_segment_btn.setEnabled(False)
        
        self.finish_segment_btn = LayoutManager.create_button_with_style(
            "完成", "success", "default", 40
        )
        self.finish_segment_btn.clicked.connect(self._on_finish_segmentation)
        self.finish_segment_btn.setEnabled(False)
        
        segment_buttons_layout = qt.QHBoxLayout()
        segment_buttons_layout.addWidget(self.start_segment_btn)
        segment_buttons_layout.addWidget(self.finish_segment_btn)
        main_layout.addRow("区域标记:", segment_buttons_layout)
        
        # 结果显示
        self.area_label = qt.QLabel("--")
        self.area_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.percentage_label = qt.QLabel("--")
        self.percentage_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.grade_label = qt.QLabel("--")
        self.grade_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        main_layout.addRow("面积:", self.area_label)
        main_layout.addRow("占比:", self.percentage_label)
        main_layout.addRow("分级:", self.grade_label)
        
        # 手动调整
        self.manual_grade_combo = qt.QComboBox()
        self.manual_grade_combo.addItems([
            "自动", "≤25%", "25-50%", "50%-75%", ">75%"
        ])
        self.manual_grade_combo.currentTextChanged.connect(self._on_manual_grade_changed)
        
        main_layout.addRow("调整分级:", self.manual_grade_combo)
    
    def _on_leaflet_changed(self, leaflet: str):
        """瓣叶选择改变时的回调"""
        if leaflet and not leaflet.startswith("选择"):
            self.start_segment_btn.setEnabled(True)
            logging.info(f"选择了瓣叶: {leaflet}")
        else:
            self.start_segment_btn.setEnabled(False)
    
    def _on_start_segmentation(self):
        """开始分割标记"""
        self.start_segment_btn.setEnabled(False)
        self.finish_segment_btn.setEnabled(True)
        logging.info("开始HALT区域标记")
        # TODO: 实现分割逻辑
    
    def _on_finish_segmentation(self):
        """完成分割标记"""
        self.finish_segment_btn.setEnabled(False)
        self.start_segment_btn.setEnabled(True)
        logging.info("完成HALT区域标记")
        # TODO: 实现计算逻辑
        # 临时显示示例结果
        self.area_label.setText("15.2 mm²")
        self.percentage_label.setText("35.8%")
        self.grade_label.setText("25-50%")
    
    def _on_manual_grade_changed(self, grade: str):
        """手动分级调整"""
        if grade != "使用自动分级":
            self.grade_label.setText(grade)
            logging.info(f"手动调整HALT分级为: {grade}")


class RelmAnalysisSection(qt.QWidget):
    """RELM (瓣叶活动度减退) 分析区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RelmAnalysisSection")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置RELM分析界面"""
        main_layout = LayoutManager.create_layout(LayoutType.FORM_CONTAINER, self)
        
        # 瓣叶选择
        self.leaflet_combo = qt.QComboBox()
        self.leaflet_combo.addItems(["选择瓣叶...", "LC", "RC", "NC"])
        self.leaflet_combo.currentTextChanged.connect(self._on_leaflet_changed)
        main_layout.addRow("瓣叶:", self.leaflet_combo)
        
        # 测量控制
        self.measure_width_btn = LayoutManager.create_button_with_style(
            "测量宽度 (W)", "primary", "default", 40
        )
        self.measure_width_btn.clicked.connect(self._on_measure_width)
        self.measure_width_btn.setEnabled(False)
        
        self.measure_diameter_btn = LayoutManager.create_button_with_style(
            "测量内径 (D)", "secondary", "default", 40
        )
        self.measure_diameter_btn.clicked.connect(self._on_measure_diameter)
        self.measure_diameter_btn.setEnabled(False)
        
        self.calculate_relm_btn = LayoutManager.create_button_with_style(
            "计算RELM", "accent", "default", 40
        )
        self.calculate_relm_btn.clicked.connect(self._on_calculate_relm)
        self.calculate_relm_btn.setEnabled(False)
        
        measure_buttons_layout = qt.QHBoxLayout()
        measure_buttons_layout.addWidget(self.measure_width_btn)
        measure_buttons_layout.addWidget(self.measure_diameter_btn)
        
        main_layout.addRow("测量:", measure_buttons_layout)
        main_layout.addRow("计算:", self.calculate_relm_btn)
        
        # 测量结果
        self.width_label = qt.QLabel("--")
        self.width_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.diameter_label = qt.QLabel("--")
        self.diameter_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.relm_value_label = qt.QLabel("--")
        self.relm_value_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.relm_grade_label = qt.QLabel("--")
        self.relm_grade_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        main_layout.addRow("宽度 (W):", self.width_label)
        main_layout.addRow("内径 (D):", self.diameter_label)
        main_layout.addRow("RELM值:", self.relm_value_label)
        main_layout.addRow("分级:", self.relm_grade_label)
        
        # 手动调整
        self.manual_grade_combo = qt.QComboBox()
        self.manual_grade_combo.addItems([
            "自动", "正常", "轻度", "中度", "重度"
        ])
        self.manual_grade_combo.currentTextChanged.connect(self._on_manual_grade_changed)
        
        main_layout.addRow("调整分级:", self.manual_grade_combo)
    
    def _on_leaflet_changed(self, leaflet: str):
        """瓣叶选择改变时的回调"""
        if leaflet and not leaflet.startswith("选择"):
            self.measure_width_btn.setEnabled(True)
            self.measure_diameter_btn.setEnabled(True)
            logging.info(f"选择了瓣叶: {leaflet}")
        else:
            self.measure_width_btn.setEnabled(False)
            self.measure_diameter_btn.setEnabled(False)
            self.calculate_relm_btn.setEnabled(False)
    
    def _on_measure_width(self):
        """测量增厚宽度"""
        logging.info("开始测量增厚宽度")
        # TODO: 实现测量逻辑
        self.width_label.setText("3.2 mm")
        self._check_calculate_ready()
    
    def _on_measure_diameter(self):
        """测量支架内径"""
        logging.info("开始测量支架内径")
        # TODO: 实现测量逻辑
        self.diameter_label.setText("22.5 mm")
        self._check_calculate_ready()
    
    def _check_calculate_ready(self):
        """检查是否可以计算RELM"""
        if (self.width_label.text() != "--" and 
            self.diameter_label.text() != "--"):
            self.calculate_relm_btn.setEnabled(True)
    
    def _on_calculate_relm(self):
        """计算RELM"""
        logging.info("计算RELM值")
        # TODO: 实现RELM计算
        self.relm_value_label.setText("28.4%")
        self.relm_grade_label.setText("轻度")
    
    def _on_manual_grade_changed(self, grade: str):
        """手动分级调整"""
        if grade != "使用自动分级":
            self.relm_grade_label.setText(grade)
            logging.info(f"手动调整RELM分级为: {grade}")


class SfdAnalysisSection(qt.QWidget):
    """SFD (窦内充盈缺损) 分析区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SfdAnalysisSection")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置SFD分析界面"""
        main_layout = LayoutManager.create_layout(LayoutType.FORM_CONTAINER, self)
        
        # SFD存在性评估
        self.sfd_status_group = qt.QButtonGroup()
        self.sfd_none_radio = qt.QRadioButton("无")
        self.sfd_present_radio = qt.QRadioButton("有")
        self.sfd_indeterminate_radio = qt.QRadioButton("难以判定")
        
        self.sfd_status_group.addButton(self.sfd_none_radio, 0)
        self.sfd_status_group.addButton(self.sfd_present_radio, 1)
        self.sfd_status_group.addButton(self.sfd_indeterminate_radio, 2)
        
        # 默认选择"无"
        self.sfd_none_radio.setChecked(True)
        
        self.sfd_status_group.buttonClicked.connect(self._on_sfd_status_changed)
        
        status_layout = qt.QHBoxLayout()
        status_layout.addWidget(self.sfd_none_radio)
        status_layout.addWidget(self.sfd_present_radio)
        status_layout.addWidget(self.sfd_indeterminate_radio)
        
        main_layout.addRow("状态:", status_layout)
        
        # 受累主动脉窦选择
        self.lc_sinus_checkbox = qt.QCheckBox("LC")
        self.rc_sinus_checkbox = qt.QCheckBox("RC")
        self.nc_sinus_checkbox = qt.QCheckBox("NC")
        
        # 初始状态禁用
        self.lc_sinus_checkbox.setEnabled(False)
        self.rc_sinus_checkbox.setEnabled(False)
        self.nc_sinus_checkbox.setEnabled(False)
        
        self.lc_sinus_checkbox.stateChanged.connect(self._on_sinus_selection_changed)
        self.rc_sinus_checkbox.stateChanged.connect(self._on_sinus_selection_changed)
        self.nc_sinus_checkbox.stateChanged.connect(self._on_sinus_selection_changed)
        
        sinus_layout = qt.QHBoxLayout()
        sinus_layout.addWidget(self.lc_sinus_checkbox)
        sinus_layout.addWidget(self.rc_sinus_checkbox)
        sinus_layout.addWidget(self.nc_sinus_checkbox)
        
        main_layout.addRow("受累窦部:", sinus_layout)
        
        # 分析结果
        self.sfd_result_label = qt.QLabel("无SFD")
        self.sfd_result_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.affected_sinuses_label = qt.QLabel("无")
        self.affected_sinuses_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        main_layout.addRow("SFD:", self.sfd_result_label)
        main_layout.addRow("受累窦部:", self.affected_sinuses_label)
    
    def _on_sfd_status_changed(self, button):
        """SFD状态改变时的回调"""
        button_id = self.sfd_status_group.id(button)
        
        if button_id == 1:  # "有"被选中
            self.lc_sinus_checkbox.setEnabled(True)
            self.rc_sinus_checkbox.setEnabled(True)
            self.nc_sinus_checkbox.setEnabled(True)
            self.sfd_result_label.setText("存在SFD")
            logging.info("SFD状态: 存在")
        else:
            # "无"或"难以判定"被选中
            self.lc_sinus_checkbox.setEnabled(False)
            self.rc_sinus_checkbox.setEnabled(False)
            self.nc_sinus_checkbox.setEnabled(False)
            
            # 清除选择
            self.lc_sinus_checkbox.setChecked(False)
            self.rc_sinus_checkbox.setChecked(False)
            self.nc_sinus_checkbox.setChecked(False)
            
            if button_id == 0:
                self.sfd_result_label.setText("无SFD")
                self.affected_sinuses_label.setText("无")
                logging.info("SFD状态: 无")
            else:
                self.sfd_result_label.setText("难以判定")
                self.affected_sinuses_label.setText("难以判定")
                logging.info("SFD状态: 难以判定")
    
    def _on_sinus_selection_changed(self):
        """受累窦部选择改变时的回调"""
        affected = []
        if self.lc_sinus_checkbox.isChecked():
            affected.append("LC")
        if self.rc_sinus_checkbox.isChecked():
            affected.append("RC")
        if self.nc_sinus_checkbox.isChecked():
            affected.append("NC")
        
        if affected:
            self.affected_sinuses_label.setText(", ".join(affected))
        else:
            self.affected_sinuses_label.setText("无")
        
        logging.info(f"受累窦部: {affected}")


class PfdAnalysisSection(qt.QWidget):
    """PFD (瓣叶下充盈缺损) 分析区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PfdAnalysisSection")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置PFD分析界面"""
        main_layout = LayoutManager.create_layout(LayoutType.FORM_CONTAINER, self)
        
        # PFD存在性评估
        self.pfd_status_group = qt.QButtonGroup()
        self.pfd_none_radio = qt.QRadioButton("无")
        self.pfd_present_radio = qt.QRadioButton("有")
        self.pfd_indeterminate_radio = qt.QRadioButton("难以判定")
        
        self.pfd_status_group.addButton(self.pfd_none_radio, 0)
        self.pfd_status_group.addButton(self.pfd_present_radio, 1)
        self.pfd_status_group.addButton(self.pfd_indeterminate_radio, 2)
        
        # 默认选择"无"
        self.pfd_none_radio.setChecked(True)
        
        self.pfd_status_group.buttonClicked.connect(self._on_pfd_status_changed)
        
        status_layout = qt.QHBoxLayout()
        status_layout.addWidget(self.pfd_none_radio)
        status_layout.addWidget(self.pfd_present_radio)
        status_layout.addWidget(self.pfd_indeterminate_radio)
        
        main_layout.addRow("状态:", status_layout)
        
        # PFD测量
        self.measure_thickness_btn = LayoutManager.create_button_with_style(
            "测量厚度", "primary", "default", 40
        )
        self.measure_thickness_btn.clicked.connect(self._on_measure_thickness)
        self.measure_thickness_btn.setEnabled(False)
        
        main_layout.addRow("测量:", self.measure_thickness_btn)
        
        # 测量结果
        self.pfd_result_label = qt.QLabel("无PFD")
        self.pfd_result_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        self.thickness_label = qt.QLabel("--")
        self.thickness_label.setStyleSheet(StyleManager.get_label_style("data"))
        
        main_layout.addRow("PFD:", self.pfd_result_label)
        main_layout.addRow("厚度:", self.thickness_label)
        
        # 手动输入
        self.thickness_spinbox = qt.QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.0, 50.0)
        self.thickness_spinbox.setDecimals(1)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.setEnabled(False)
        self.thickness_spinbox.valueChanged.connect(self._on_manual_thickness_changed)
        
        main_layout.addRow("手动厚度:", self.thickness_spinbox)
    
    def _on_pfd_status_changed(self, button):
        """PFD状态改变时的回调"""
        button_id = self.pfd_status_group.id(button)
        
        if button_id == 1:  # "有"被选中
            self.measure_thickness_btn.setEnabled(True)
            self.thickness_spinbox.setEnabled(True)
            self.pfd_result_label.setText("存在PFD")
            self.thickness_label.setText("--")
        else:
            # "无"或"难以判定"被选中
            self.measure_thickness_btn.setEnabled(False)
            self.thickness_spinbox.setEnabled(False)
            self.thickness_spinbox.setValue(0.0)
            
            if button_id == 0:
                self.pfd_result_label.setText("无PFD")
                self.thickness_label.setText("--")
            else:
                self.pfd_result_label.setText("难以判定")
                self.thickness_label.setText("--")
    
    def _on_measure_thickness(self):
        """测量充盈缺损厚度"""
        # TODO: 实现测量逻辑
        self.thickness_label.setText("2.3 mm")
        self.thickness_spinbox.setValue(2.3)
    
    def _on_manual_thickness_changed(self, value):
        """手动厚度输入改变时的回调"""
        if value > 0:
            self.thickness_label.setText(f"{value:.1f} mm")


class PasteAnalysisWidget(qt.QWidget):
    """PASTE分析主界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[PasteAnalysisLogic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or PasteAnalysisLogic()
        
        self.setObjectName("PasteAnalysisWidget")
        self._setup_ui()
        logging.info("PasteAnalysisWidget 初始化完成")
    
    def _setup_ui(self):
        """设置PASTE分析主界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 主标题
        title = qt.QLabel("瓣叶功能评估 (PASTE分析)")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        
        # 创建可滚动区域
        scroll_area = qt.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(qt.QFrame.NoFrame)  # 移除边框
        scroll_area.setMinimumHeight(400)  # 设置最小高度确保滚动条出现
        
        # 设置滚动区域样式，美化滚动条
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f1f1f1;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # 创建滚动内容容器
        scroll_content = qt.QWidget()
        scroll_content.setMinimumSize(400, 800)  # 设置最小尺寸确保内容足够大
        scroll_layout = qt.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(10)
        
        # 创建四个分析区域，直接作为section frame
        halt_frame = LayoutManager.create_section_frame("HALT Analysis")
        halt_layout = qt.QVBoxLayout(halt_frame)
        halt_layout.addWidget(HaltAnalysisSection())
        
        relm_frame = LayoutManager.create_section_frame("RELM Analysis")
        relm_layout = qt.QVBoxLayout(relm_frame)
        relm_layout.addWidget(RelmAnalysisSection())
        
        sfd_frame = LayoutManager.create_section_frame("SFD Analysis")
        sfd_layout = qt.QVBoxLayout(sfd_frame)
        sfd_layout.addWidget(SfdAnalysisSection())
        
        pfd_frame = LayoutManager.create_section_frame("PFD Analysis")
        pfd_layout = qt.QVBoxLayout(pfd_frame)
        pfd_layout.addWidget(PfdAnalysisSection())
        
        # 添加到滚动布局
        scroll_layout.addWidget(halt_frame)
        scroll_layout.addWidget(relm_frame)
        scroll_layout.addWidget(sfd_frame)
        scroll_layout.addWidget(pfd_frame)
        
        # 添加弹性空间，确保内容顶部对齐
        scroll_layout.addStretch()
        
        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        
        # 操作按钮区域 - 直接使用水平布局
        self.reset_all_btn = LayoutManager.create_button_with_style(
            "重置所有分析", "warning", "default", 40
        )
        self.reset_all_btn.clicked.connect(self._on_reset_all)
        
        self.export_results_btn = LayoutManager.create_button_with_style(
            "导出分析结果", "info", "default", 40
        )
        self.export_results_btn.clicked.connect(self._on_export_results)
        
        self.save_session_btn = LayoutManager.create_button_with_style(
            "保存到会话", "success", "default", 40
        )
        self.save_session_btn.clicked.connect(self._on_save_session)
        
        actions_buttons_layout = qt.QHBoxLayout()
        actions_buttons_layout.addWidget(self.reset_all_btn)
        actions_buttons_layout.addWidget(self.export_results_btn)
        actions_buttons_layout.addWidget(self.save_session_btn)
        
        # 组装主布局
        main_layout.addWidget(title)
        main_layout.addWidget(scroll_area, 1)  # 占据大部分空间
        main_layout.addLayout(actions_buttons_layout)
    
    def _on_reset_all(self):
        """重置所有分析"""
        # TODO: 实现重置逻辑
        qt.QMessageBox.information(self, "重置", "所有PASTE分析已重置")
    
    def _on_export_results(self):
        """导出分析结果"""
        # TODO: 实现导出逻辑
        qt.QMessageBox.information(self, "导出", "PASTE分析结果已导出")
    
    def _on_save_session(self):
        """保存到会话"""
        # TODO: 实现保存逻辑
        qt.QMessageBox.information(self, "保存", "PASTE分析结果已保存到会话")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话"""
        self.session = session
        if self.logic:
            # TODO: 将session传递给logic
            pass
    
    def on_activated(self):
        """激活时的回调"""
        pass
    
    def on_deactivated(self):
        """停用时的回调"""
        pass
    
    def cleanup(self):
        """清理资源"""
        if self.logic:
            self.logic.cleanup()

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取所有分析结果"""
        results = {
            'halt': self._get_halt_results(),
            'relm': self._get_relm_results(),
            'sfd': self._get_sfd_results(),
            'pfd': self._get_pfd_results()
        }
        return results
    
    def _get_halt_results(self) -> Dict[str, Any]:
        """获取HALT分析结果"""
        # TODO: 从halt_section获取实际结果
        return {
            'leaflet': 'LC',
            'area': '15.2 mm²',
            'percentage': '35.8%',
            'grade': '25-50%'
        }
    
    def _get_relm_results(self) -> Dict[str, Any]:
        """获取RELM分析结果"""
        # TODO: 从relm_section获取实际结果
        return {
            'leaflet': 'LC',
            'width': '3.2 mm',
            'diameter': '22.5 mm',
            'value': '28.4%',
            'grade': '轻度'
        }
    
    def _get_sfd_results(self) -> Dict[str, Any]:
        """获取SFD分析结果"""
        # TODO: 从sfd_section获取实际结果
        return {
            'status': '无SFD',
            'affected_sinuses': []
        }
    
    def _get_pfd_results(self) -> Dict[str, Any]:
        """获取PFD分析结果"""
        # TODO: 从pfd_section获取实际结果
        return {
            'status': '无PFD',
            'thickness': None
        }
