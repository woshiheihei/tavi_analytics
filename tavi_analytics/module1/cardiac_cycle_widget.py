"""
心动周期管理组件

该模块提供心动周期时间轴管理和时相标记功能，包括：
- 时相百分比显示
- 序列描述显示  
- 时间轴滑块控制
- 关键时相标记（舒张末期、收缩末期）
- 已标记时相显示

作者：TAVR Research Team
创建时间：2024
"""

import qt
import slicer
from typing import Optional, Callable
import logging

try:
    from ..core.session import TAVRStudySession
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession


class CardiacCycleWidget(qt.QGroupBox):
    """心动周期管理组件
    
    提供4D心脏CT序列的时间轴管理和关键时相标记功能
    """
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """初始化心动周期管理组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父窗口对象
        """
        super().__init__("心动周期管理", parent)
        self.session = session
        self.setVisible(False)  # 初始隐藏
        
        # 初始化UI组件
        self._init_ui()
        self._setup_connections()
        
    def _init_ui(self):
        """初始化用户界面"""
        layout = qt.QVBoxLayout(self)
        
        # 时相百分比显示
        self.phase_percent_label = qt.QLabel("当前时相: 0.0%")
        self.phase_percent_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_percent_label.setStyleSheet(
            "QLabel { font-size: 16px; font-weight: bold; margin: 10px; }"
        )
        layout.addWidget(self.phase_percent_label)
        
        # Series Description 显示
        self.series_description_label = qt.QLabel("序列描述: 未加载")
        self.series_description_label.setAlignment(qt.Qt.AlignCenter)
        self.series_description_label.setStyleSheet(
            "QLabel { "
            "font-size: 14px; margin: 5px; padding: 8px; "
            "background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; "
            "}"
        )
        self.series_description_label.setWordWrap(True)
        layout.addWidget(self.series_description_label)
        
        # 心动周期时间轴滑块
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        layout.addWidget(self.timeline_slider)
        
        # 时相标记按钮
        self._create_phase_marking_buttons(layout)
        
        # 已标记时相显示
        self._create_marked_phases_display(layout)
        
    def _create_phase_marking_buttons(self, parent_layout):
        """创建时相标记按钮"""
        button_layout = qt.QHBoxLayout()
        
        self.mark_end_diastole_button = qt.QPushButton("标记舒张末期")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setStyleSheet(
            "QPushButton { padding: 8px; background-color: #FF9800; color: white; }"
        )
        button_layout.addWidget(self.mark_end_diastole_button)
        
        self.mark_end_systole_button = qt.QPushButton("标记收缩末期")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setStyleSheet(
            "QPushButton { padding: 8px; background-color: #9C27B0; color: white; }"
        )
        button_layout.addWidget(self.mark_end_systole_button)
        
        parent_layout.addLayout(button_layout)
        
    def _create_marked_phases_display(self, parent_layout):
        """创建已标记时相显示"""
        marked_phases_layout = qt.QVBoxLayout()
        
        self.end_diastole_label = qt.QLabel("舒张末期: 未标记")
        self.end_diastole_label.setStyleSheet(
            "QLabel { padding: 5px; background-color: #fff3e0; border: 1px solid #ff9800; }"
        )
        self.end_diastole_label.setWordWrap(True)
        
        self.end_systole_label = qt.QLabel("收缩末期: 未标记")
        self.end_systole_label.setStyleSheet(
            "QLabel { padding: 5px; background-color: #f3e5f5; border: 1px solid #9c27b0; }"
        )
        self.end_systole_label.setWordWrap(True)
        
        marked_phases_layout.addWidget(self.end_diastole_label)
        marked_phases_layout.addWidget(self.end_systole_label)
        parent_layout.addLayout(marked_phases_layout)
        
    def _setup_connections(self):
        """设置信号连接"""
        self.timeline_slider.valueChanged.connect(self._on_timeline_slider_changed)
        self.mark_end_diastole_button.clicked.connect(
            lambda: self._mark_phase('end_diastole')
        )
        self.mark_end_systole_button.clicked.connect(
            lambda: self._mark_phase('end_systole')
        )
        
    def activate(self):
        """激活心动周期管理
        
        当序列数据加载完成后调用此方法来激活心动周期管理功能
        """
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
            self.setVisible(True)
            
            # 初始化当前帧
            self._on_timeline_slider_changed(0)
            
            logging.info("心动周期管理已激活")
            return True
        else:
            logging.warning("无法激活心动周期管理：缺少序列节点或浏览器节点")
            return False
            
    def deactivate(self):
        """停用心动周期管理"""
        self.timeline_slider.setEnabled(False)
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_systole_button.setEnabled(False)
        self.setVisible(False)
        
        # 重置显示
        self.phase_percent_label.setText("当前时相: 0.0%")
        self.series_description_label.setText("序列描述: 未加载")
        self._update_phase_labels()
        
        logging.info("心动周期管理已停用")
        
    def _on_timeline_slider_changed(self, value: int):
        """处理时间轴滑块变化
        
        Args:
            value: 滑块当前值（帧索引）
        """
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
            except (ValueError, TypeError):
                self.phase_percent_label.setText(f"当前时相: 帧 {value}")
                
            # 获取并显示Series Description
            series_desc = self.session.get_current_frame_series_description()
            self.series_description_label.setText(f"序列描述: {series_desc}")
            
    def _mark_phase(self, phase_name: str):
        """标记关键时相
        
        Args:
            phase_name: 时相名称 ('end_diastole' 或 'end_systole')
        """
        browser_node = self.session.get_sequence_browser_node()
        sequence_node = self.session.get_volume_sequence_node()
        
        if browser_node and sequence_node:
            frame_index = browser_node.GetSelectedItemNumber()
            
            try:
                index_value = sequence_node.GetNthIndexValue(frame_index)
                phase_percent = float(index_value)
            except (ValueError, TypeError):
                phase_percent = 0.0
                
            # 获取当前帧的序列描述信息
            series_description = self.session.get_current_frame_series_description()
            
            # 保存到会话
            self.session.mark_phase(phase_name, frame_index, phase_percent, series_description)
            
            # 更新界面显示
            self._update_phase_labels()
            
            phase_display_name = "舒张末期" if phase_name == 'end_diastole' else "收缩末期"
            logging.info(f"已标记{phase_display_name}: 帧{frame_index}, {phase_percent:.1f}%")
            
    def _update_phase_labels(self):
        """更新时相标记显示"""
        end_diastole = self.session.get_marked_phase('end_diastole')
        end_systole = self.session.get_marked_phase('end_systole')
        
        # 更新舒张末期显示
        if end_diastole and end_diastole['frame_index'] is not None:
            phase_text = f"舒张末期: 已标记 @ {end_diastole['phase_percent']:.1f}%"
            if end_diastole.get('series_description'):
                phase_text += f"\n序列描述: {end_diastole['series_description']}"
            self.end_diastole_label.setText(phase_text)
        else:
            self.end_diastole_label.setText("舒张末期: 未标记")
            
        # 更新收缩末期显示
        if end_systole and end_systole['frame_index'] is not None:
            phase_text = f"收缩末期: 已标记 @ {end_systole['phase_percent']:.1f}%"
            if end_systole.get('series_description'):
                phase_text += f"\n序列描述: {end_systole['series_description']}"
            self.end_systole_label.setText(phase_text)
        else:
            self.end_systole_label.setText("收缩末期: 未标记")
            
    def refresh_display(self):
        """刷新显示内容
        
        当会话数据发生变化时调用此方法更新显示
        """
        if self.session.is_ready():
            self._update_phase_labels()
            # 如果有当前帧，更新当前帧信息
            browser_node = self.session.get_sequence_browser_node()
            if browser_node:
                current_frame = browser_node.GetSelectedItemNumber()
                self._on_timeline_slider_changed(current_frame)
        else:
            self.deactivate()
            
    def get_current_frame_index(self) -> Optional[int]:
        """获取当前帧索引
        
        Returns:
            当前帧索引，如果未激活则返回None
        """
        browser_node = self.session.get_sequence_browser_node()
        if browser_node:
            return browser_node.GetSelectedItemNumber()
        return None
        
    def set_current_frame_index(self, frame_index: int) -> bool:
        """设置当前帧索引
        
        Args:
            frame_index: 要设置的帧索引
            
        Returns:
            设置是否成功
        """
        sequence_node = self.session.get_volume_sequence_node()
        if sequence_node:
            num_frames = sequence_node.GetNumberOfDataNodes()
            if 0 <= frame_index < num_frames:
                self.timeline_slider.setValue(frame_index)
                return True
        return False
