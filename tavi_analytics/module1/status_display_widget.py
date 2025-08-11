"""
状态显示组件

该模块提供TAVR分析状态显示功能，包括：
- 当前分析状态显示
- 患者信息显示
- 序列数据状态显示
- 分析进度显示

作者：TAVR Research Team
创建时间：2024
"""

import qt
import slicer
from typing import Optional
import logging

try:
    from ..core.session import TAVRStudySession
    from ..core.data_models import PatientData
    from ..core.enums import ImageQuality, FollowUpTimepoint
    from ..utils.layout_manager import LayoutManager, LayoutType
    from .step_checklist_widget import StepChecklistWidget
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from core.data_models import PatientData
    from core.enums import ImageQuality, FollowUpTimepoint
    from utils.layout_manager import LayoutManager, LayoutType
    from step_checklist_widget import StepChecklistWidget


class StatusDisplayWidget(qt.QGroupBox):
    """状态显示组件
    
    显示当前TAVR分析的状态信息，包括患者信息、序列状态和分析进度
    """
    
    # 进度变更信号：completed, total
    progressChanged = qt.Signal(int, int)
    
    def __init__(self, session: TAVRStudySession, parent=None, compact: bool = False):
        """初始化状态显示组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父窗口对象
            compact: 是否启用紧凑模式（仅显示摘要，详细信息可展开）
        """
        super().__init__("当前状态", parent)
        self.session = session
        self._compact = compact
        self._details_visible = not compact
        
        # 初始化UI组件
        self._init_ui()
        
        # 初始更新状态
        self.update_status()
        
        # 应用紧凑模式
        self.set_compact_mode(compact)
        
    def _init_ui(self):
        """初始化用户界面"""
        # 使用标准化布局管理器
        layout = LayoutManager.create_layout(LayoutType.INFO_DISPLAY, self)
        
        # 顶部摘要 + 展开按钮
        header_layout = LayoutManager.create_horizontal_layout(LayoutType.INFO_DISPLAY)
        
        self.status_label = qt.QLabel("未配置数据")
        self.status_label.setWordWrap(False)  # 摘要行尽量一行
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 8px; background-color: #f0f0f0; "
            "border: 1px solid #ccc; border-radius: 4px; "
            "}"
        )
        header_layout.addWidget(self.status_label, 1)
        
        self.toggle_btn = qt.QToolButton()
        self.toggle_btn.setText("详细信息")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self._details_visible)
        self.toggle_btn.setArrowType(qt.Qt.DownArrow if self._details_visible else qt.Qt.RightArrow)
        self.toggle_btn.setToolButtonStyle(qt.Qt.ToolButtonTextBesideIcon)
        self.toggle_btn.toggled.connect(self._on_toggle_details)
        header_layout.addWidget(self.toggle_btn, 0)
        
        layout.addLayout(header_layout)
        
        # 任务进度（常显，紧凑不拉伸）
        self.step_checklist = StepChecklistWidget(self)
        self.step_checklist.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
        layout.addWidget(self.step_checklist, 0)
        
        # 详细信息面板（自管可见性）
        self.details_group = qt.QGroupBox("详细信息")
        self.details_group.setCheckable(False)
        
        # 使用标准化布局管理器为详细信息组
        details_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, self.details_group)
        
        # 患者信息显示 - 使用更紧凑的样式
        self.patient_info_label = qt.QLabel("患者信息: 未加载")
        self.patient_info_label.setWordWrap(True)
        self.patient_info_label.setStyleSheet(
            "QLabel { "
            "padding: 6px 8px; "
            "background-color: #f8fafc; "
            "border: 1px solid #e2e8f0; "
            "border-radius: 4px; "
            "font-size: 12px; "
            "line-height: 1.3; "
            "}"
        )
        details_layout.addWidget(self.patient_info_label)
        
        # 序列信息显示 - 使用更紧凑的样式
        self.sequence_info_label = qt.QLabel("序列信息: 未加载")
        self.sequence_info_label.setWordWrap(True)
        self.sequence_info_label.setStyleSheet(
            "QLabel { "
            "padding: 6px 8px; "
            "background-color: #f0fdf4; "
            "border: 1px solid #bbf7d0; "
            "border-radius: 4px; "
            "font-size: 12px; "
            "line-height: 1.3; "
            "}"
        )
        details_layout.addWidget(self.sequence_info_label)
        
        layout.addWidget(self.details_group)
        self.details_group.setVisible(self._details_visible)
        
    def set_compact_mode(self, compact: bool):
        """切换紧凑模式"""
        self._compact = compact
        if compact:
            # 紧凑模式始终收起详情
            self.toggle_btn.setChecked(False)
            self.details_group.setVisible(False)
            self.toggle_btn.setArrowType(qt.Qt.RightArrow)
            self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
            self.status_label.setWordWrap(False)
            self.status_label.setMaximumHeight(40)
        else:
            self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
            self.status_label.setWordWrap(True)
            self.status_label.setMaximumHeight(16777215)
        
        self.updateGeometry()
        self.adjustSize()
    
    def _on_toggle_details(self, checked: bool):
        self.details_group.setVisible(checked)
        self.toggle_btn.setArrowType(qt.Qt.DownArrow if checked else qt.Qt.RightArrow)
        self.updateGeometry()
        self.adjustSize()
    
    def update_status(self):
        """统一更新：摘要、任务进度、详情"""
        # 先更新摘要文本（依赖 session.is_ready）
        if self.session.is_ready():
            self._update_ready_status()
        else:
            self._update_not_ready_status()
        
        # 更新任务进度（合并计算，发信号）
        self._update_progress()
        
        # 更新详细信息
        self._update_patient_info()
        self._update_sequence_info()
    
    def _compute_step_status(self) -> dict:
        """计算四项任务的完成状态"""
        status = {"data_imported": False, "patient_info": False, "phase_ed": False, "phase_es": False}
        try:
            # 数据导入状态：只检查序列数据是否已加载
            status["data_imported"] = bool(self.session.volume_sequence_node_id is not None)
            
            # 患者信息状态：检查患者ID和瓣膜信息是否完整
            patient_data = getattr(self.session, 'patient_data', None)
            has_patient_id = bool(patient_data and getattr(patient_data, 'patientID', None))
            has_valve_info = bool(patient_data and 
                                getattr(patient_data, 'valveBrand', None) and 
                                getattr(patient_data, 'valveModel', None))
            status["patient_info"] = has_patient_id and has_valve_info
            
            # 时相标记状态
            ed = self.session.get_marked_phase('end_diastole')
            es = self.session.get_marked_phase('end_systole')
            status["phase_ed"] = ed.get('frame_index') is not None if isinstance(ed, dict) else False
            status["phase_es"] = es.get('frame_index') is not None if isinstance(es, dict) else False
            
            # 记录详细状态用于调试
            logging.info(f"步骤状态计算: 数据导入={status['data_imported']} (序列节点ID={self.session.volume_sequence_node_id}), "
                        f"患者信息={status['patient_info']} (患者ID={has_patient_id}, 瓣膜信息={has_valve_info}), "
                        f"舒张末期={status['phase_ed']}, 收缩末期={status['phase_es']}")
            
        except Exception as e:
            logging.error(f"计算步骤状态时出错: {e}")
        return status
    
    def _update_progress(self):
        """更新任务进度UI并发出进度信号"""
        try:
            status = self._compute_step_status()
            if hasattr(self, 'step_checklist') and self.step_checklist:
                self.step_checklist.update_steps(status)
            completed = sum(1 for v in status.values() if v)
            total = 4
            self.progressChanged.emit(completed, total)
        except Exception:
            # 静默失败以免影响主流程
            pass
    
    def _update_ready_status(self):
        """更新就绪状态显示"""
        patient_data = self.session.patient_data
        sequence_node = self.session.get_volume_sequence_node()
        
        # 先生成摘要用于工具提示
        summary = self.get_summary_text()
        
        # 紧凑模式：显示简短摘要
        if self._compact:
            self.status_label.setText("数据已配置 - " + summary)
            self.status_label.setToolTip("数据已配置 - " + summary)
            self.status_label.setStyleSheet(
                "QLabel { "
                "padding: 6px; background-color: #e8f5e8; "
                "border: 1px solid #4caf50; border-radius: 4px; "
                "font-size: 12px; "
                "}"
            )
            return
        
        status_parts = []
        
        # 患者信息状态
        if patient_data and patient_data.patientID:
            status_parts.append(f"✓ 患者: {patient_data.patientID}")
        else:
            status_parts.append("⚠ 患者信息不完整")
            
        # 序列状态
        if sequence_node:
            num_frames = sequence_node.GetNumberOfDataNodes()
            status_parts.append(f"✓ 序列: {num_frames} 帧")
        else:
            status_parts.append("✗ 序列未加载")
            
        # 时相标记状态
        marked_phases = []
        if self.session.get_marked_phase('end_diastole').get('frame_index') is not None:
            marked_phases.append("舒张末期")
        if self.session.get_marked_phase('end_systole').get('frame_index') is not None:
            marked_phases.append("收缩末期")
            
        if marked_phases:
            status_parts.append(f"✓ 已标记: {', '.join(marked_phases)}")
        else:
            status_parts.append("⚠ 未标记关键时相")
            
        main_status = "数据已配置 - " + " | ".join(status_parts)
        self.status_label.setText(main_status)
        self.status_label.setToolTip("数据已配置 - " + summary)
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 10px; background-color: #e8f5e8; "
            "border: 1px solid #4caf50; border-radius: 4px; "
            "}"
        )
        
    def _update_not_ready_status(self):
        """更新未就绪状态显示"""
        text = "未配置数据 - 请点击'数据导入与配置'按钮开始分析"
        tooltip = "未配置数据：请先导入4D心脏CT并完善患者信息"
        if self._compact:
            text = "未配置数据"
        self.status_label.setText(text)
        self.status_label.setToolTip(tooltip)
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 6px; background-color: #ffebee; "
            "border: 1px solid #f44336; border-radius: 4px; "
            "font-size: 12px; "
            "}"
        )
        
    def _update_patient_info(self):
        """更新患者信息显示"""
        patient_data = self.session.patient_data
        
        if patient_data and patient_data.patientID:
            # 只显示核心信息，更紧凑
            core_info = [
                f"ID: {patient_data.patientID}",
                f"姓名: {patient_data.patientName or '未知'}",
                f"性别: {patient_data.patientSex or '未知'}",
                f"年龄: {patient_data.patientAge or '未知'}"
            ]
            
            # 检查日期信息
            if patient_data.ctScanDate:
                core_info.append(f"检查日期: {patient_data.ctScanDate}")
                
            # 瓣膜信息（如果有）
            valve_info = []
            if patient_data.valveBrand:
                valve_info.append(f"瓣膜: {patient_data.valveBrand}")
            if patient_data.valveModel:
                valve_info.append(f"型号: {patient_data.valveModel}")
            
            if valve_info:
                core_info.append(" | ".join(valve_info))
            
            # 附加信息（如果有）
            additional_info = []
            if patient_data.followUpTimepoint:
                timepoint_name = patient_data.followUpTimepoint.value if hasattr(patient_data.followUpTimepoint, 'value') else str(patient_data.followUpTimepoint)
                additional_info.append(f"随访: {timepoint_name}")
                
            if patient_data.imageQuality:
                quality_name = patient_data.imageQuality.value if hasattr(patient_data.imageQuality, 'value') else str(patient_data.imageQuality)
                additional_info.append(f"质量: {quality_name}")
                
            if additional_info:
                core_info.append(" | ".join(additional_info))
            
            self.patient_info_label.setText("患者信息: " + " • ".join(core_info))
        else:
            self.patient_info_label.setText("患者信息: 未加载")
            
    def _update_sequence_info(self):
        """更新序列信息显示"""
        sequence_node = self.session.get_volume_sequence_node()
        browser_node = self.session.get_sequence_browser_node()
        
        if sequence_node and browser_node:
            # 紧凑显示核心信息
            info_parts = [
                f"序列: {sequence_node.GetName()}",
                f"帧数: {sequence_node.GetNumberOfDataNodes()}",
                f"当前: {browser_node.GetSelectedItemNumber() + 1}"
            ]
            
            # 时相范围信息（如果有）
            if sequence_node.GetNumberOfDataNodes() > 0:
                first_index = sequence_node.GetNthIndexValue(0)
                last_index = sequence_node.GetNthIndexValue(sequence_node.GetNumberOfDataNodes() - 1)
                info_parts.append(f"范围: {first_index}-{last_index}")
                
            # 索引信息
            if sequence_node.GetIndexName() and sequence_node.GetIndexUnit():
                index_info = f"{sequence_node.GetIndexName()}({sequence_node.GetIndexUnit()})"
                info_parts.append(f"索引: {index_info}")
                
            # Series Description信息（如果有且不是默认值）
            series_desc = self.session.get_current_frame_series_description()
            if series_desc and series_desc != "Unknown":
                # 截断过长的描述
                if len(series_desc) > 30:
                    series_desc = series_desc[:27] + "..."
                info_parts.append(f"描述: {series_desc}")
            
            self.sequence_info_label.setText("序列信息: " + " • ".join(info_parts))
        else:
            self.sequence_info_label.setText("序列信息: 未加载")
            
    def set_status_message(self, message: str, status_type: str = "info"):
        """设置自定义状态消息
        
        Args:
            message: 状态消息
            status_type: 状态类型 ("info", "success", "warning", "error")
        """
        color_map = {
            "info": ("#e3f2fd", "#2196f3"),
            "success": ("#e8f5e8", "#4caf50"),
            "warning": ("#fff3e0", "#ff9800"),
            "error": ("#ffebee", "#f44336")
        }
        
        bg_color, border_color = color_map.get(status_type, color_map["info"])
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"QLabel {{ "
            f"padding: 10px; background-color: {bg_color}; "
            f"border: 1px solid {border_color}; border-radius: 4px; "
            f"}}"
        )
        
    def get_summary_text(self) -> str:
        """获取状态摘要文本
        
        Returns:
            状态摘要文本
        """
        if not self.session.is_ready():
            return "未配置数据"
        
        patient_data = self.session.patient_data
        sequence_node = self.session.get_volume_sequence_node()
        
        summary_parts = []
        
        if patient_data and patient_data.patientID:
            summary_parts.append(f"患者: {patient_data.patientID}")
            
        if sequence_node:
            summary_parts.append(f"序列: {sequence_node.GetNumberOfDataNodes()}帧")
            
        # 时相标记统计
        marked_count = 0
        if self.session.get_marked_phase('end_diastole').get('frame_index') is not None:
            marked_count += 1
        if self.session.get_marked_phase('end_systole').get('frame_index') is not None:
            marked_count += 1
            
        if marked_count > 0:
            summary_parts.append(f"已标记: {marked_count}/2")
            
        return " | ".join(summary_parts) if summary_parts else "数据已配置"
