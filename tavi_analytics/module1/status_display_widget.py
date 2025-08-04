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


class StatusDisplayWidget(qt.QGroupBox):
    """状态显示组件
    
    显示当前TAVR分析的状态信息，包括患者信息、序列状态和分析进度
    """
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """初始化状态显示组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父窗口对象
        """
        super().__init__("当前状态", parent)
        self.session = session
        
        # 初始化UI组件
        self._init_ui()
        
        # 初始更新状态
        self.update_status()
        
    def _init_ui(self):
        """初始化用户界面"""
        layout = qt.QVBoxLayout(self)
        
        # 主状态标签
        self.status_label = qt.QLabel("未配置数据")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 10px; background-color: #f0f0f0; "
            "border: 1px solid #ccc; border-radius: 4px; "
            "}"
        )
        layout.addWidget(self.status_label)
        
        # 详细信息面板（可折叠）
        self.details_group = qt.QGroupBox("详细信息")
        self.details_group.setCheckable(True)
        self.details_group.setChecked(False)  # 默认折叠
        
        details_layout = qt.QVBoxLayout(self.details_group)
        
        # 患者信息显示
        self.patient_info_label = qt.QLabel("患者信息: 未加载")
        self.patient_info_label.setWordWrap(True)
        self.patient_info_label.setStyleSheet(
            "QLabel { padding: 8px; background-color: #e3f2fd; border: 1px solid #2196f3; }"
        )
        details_layout.addWidget(self.patient_info_label)
        
        # 序列信息显示
        self.sequence_info_label = qt.QLabel("序列信息: 未加载")
        self.sequence_info_label.setWordWrap(True)
        self.sequence_info_label.setStyleSheet(
            "QLabel { padding: 8px; background-color: #e8f5e8; border: 1px solid #4caf50; }"
        )
        details_layout.addWidget(self.sequence_info_label)
        
        # 分析进度显示
        self.progress_label = qt.QLabel("分析进度: 未开始")
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet(
            "QLabel { padding: 8px; background-color: #fff3e0; border: 1px solid #ff9800; }"
        )
        details_layout.addWidget(self.progress_label)
        
        layout.addWidget(self.details_group)
        
    def update_status(self):
        """更新状态显示"""
        if self.session.is_ready():
            self._update_ready_status()
        else:
            self._update_not_ready_status()
            
        # 更新详细信息
        self._update_patient_info()
        self._update_sequence_info()
        self._update_progress_info()
        
    def _update_ready_status(self):
        """更新就绪状态显示"""
        patient_data = self.session.patient_data
        sequence_node = self.session.get_volume_sequence_node()
        
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
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 10px; background-color: #e8f5e8; "
            "border: 1px solid #4caf50; border-radius: 4px; "
            "}"
        )
        
    def _update_not_ready_status(self):
        """更新未就绪状态显示"""
        self.status_label.setText("未配置数据 - 请点击'数据导入与配置'按钮开始分析")
        self.status_label.setStyleSheet(
            "QLabel { "
            "padding: 10px; background-color: #ffebee; "
            "border: 1px solid #f44336; border-radius: 4px; "
            "}"
        )
        
    def _update_patient_info(self):
        """更新患者信息显示"""
        patient_data = self.session.patient_data
        
        if patient_data and patient_data.patientID:
            info_parts = [
                f"患者ID: {patient_data.patientID}",
                f"姓名: {patient_data.patientName or '未知'}",
                f"性别: {patient_data.patientSex or '未知'}",
                f"年龄: {patient_data.patientAge or '未知'}",
                f"检查日期: {patient_data.ctScanDate or '未知'}",
                f"瓣膜品牌: {patient_data.valveBrand or '未选择'}",
                f"瓣膜型号: {patient_data.valveModel or '未选择'}",
                f"瓣膜尺寸: 未填写"  # 这个字段在PatientData中暂时没有
            ]
            
            # 添加随访时间点和图像质量信息
            if patient_data.followUpTimepoint:
                timepoint_name = patient_data.followUpTimepoint.value if hasattr(patient_data.followUpTimepoint, 'value') else str(patient_data.followUpTimepoint)
                info_parts.append(f"随访时间点: {timepoint_name}")
                
            if patient_data.imageQuality:
                quality_name = patient_data.imageQuality.value if hasattr(patient_data.imageQuality, 'value') else str(patient_data.imageQuality)
                info_parts.append(f"图像质量: {quality_name}")
            
            self.patient_info_label.setText("患者信息:\n" + "\n".join(info_parts))
        else:
            self.patient_info_label.setText("患者信息: 未加载")
            
    def _update_sequence_info(self):
        """更新序列信息显示"""
        sequence_node = self.session.get_volume_sequence_node()
        browser_node = self.session.get_sequence_browser_node()
        
        if sequence_node and browser_node:
            info_parts = [
                f"序列名称: {sequence_node.GetName()}",
                f"数据帧数: {sequence_node.GetNumberOfDataNodes()}",
                f"索引名称: {sequence_node.GetIndexName()}",
                f"索引单位: {sequence_node.GetIndexUnit()}",
                f"当前帧: {browser_node.GetSelectedItemNumber()}"
            ]
            
            # 添加第一帧和最后一帧的索引值
            if sequence_node.GetNumberOfDataNodes() > 0:
                first_index = sequence_node.GetNthIndexValue(0)
                last_index = sequence_node.GetNthIndexValue(sequence_node.GetNumberOfDataNodes() - 1)
                info_parts.append(f"时相范围: {first_index} - {last_index}")
                
            # 添加Series Description信息
            series_desc = self.session.get_current_frame_series_description()
            if series_desc and series_desc != "Unknown":
                info_parts.append(f"当前序列描述: {series_desc}")
            
            self.sequence_info_label.setText("序列信息:\n" + "\n".join(info_parts))
        else:
            self.sequence_info_label.setText("序列信息: 未加载")
            
    def _update_progress_info(self):
        """更新分析进度显示"""
        if not self.session.is_ready():
            self.progress_label.setText("分析进度: 未开始 - 请先配置数据")
            return
            
        progress_parts = []
        
        # 检查数据加载状态
        progress_parts.append("✓ 数据加载完成")
        
        # 检查时相标记状态
        end_diastole = self.session.get_marked_phase('end_diastole')
        end_systole = self.session.get_marked_phase('end_systole')
        
        if end_diastole.get('frame_index') is not None:
            progress_parts.append("✓ 舒张末期已标记")
        else:
            progress_parts.append("⚠ 舒张末期未标记")
            
        if end_systole.get('frame_index') is not None:
            progress_parts.append("✓ 收缩末期已标记")
        else:
            progress_parts.append("⚠ 收缩末期未标记")
            
        # 后续分析步骤（为将来的模块预留）
        progress_parts.append("◯ 瓣膜分割 (模块二)")
        progress_parts.append("◯ 形态学测量 (模块三)")
        progress_parts.append("◯ 功能评估 (模块四)")
        progress_parts.append("◯ 报告生成 (模块五)")
        
        self.progress_label.setText("分析进度:\n" + "\n".join(progress_parts))
        
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
