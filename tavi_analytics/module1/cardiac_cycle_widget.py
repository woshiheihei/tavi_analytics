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
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy


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
        
        # 设置大小策略 - 使用标准化布局管理器
        LayoutManager.setup_widget_size_policy(self, LayoutType.CONTROL_PANEL, SizePolicy.EXPANDING)
        
        # 初始化UI组件
        self._init_ui()
        self._setup_connections()
        
        # 设置标签点击事件
        self._setup_label_click_events()
        
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局 - 使用标准化布局管理器
        layout = LayoutManager.create_layout(LayoutType.CONTROL_PANEL, self)
        
        # 创建时相信息显示区域
        self._create_phase_info_section(layout)
        
        # 创建时间轴控制区域
        self._create_timeline_section(layout)
        
        # 创建时相标记按钮区域
        self._create_phase_marking_buttons(layout)
        
        # 创建已标记时相显示区域
        self._create_marked_phases_display(layout)
    
    def _create_phase_info_section(self, parent_layout):
        """创建时相信息显示区域"""
        info_frame = LayoutManager.create_section_frame("当前时相信息", LayoutType.INFO_DISPLAY)
        info_layout = LayoutManager.create_layout(LayoutType.INFO_DISPLAY, info_frame)
        
        # 时相百分比显示
        self.phase_percent_label = qt.QLabel("当前时相: 0.0%")
        self.phase_percent_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_percent_label.setStyleSheet(
            "QLabel { "
            "font-size: 18px; font-weight: bold; color: #2c3e50; "
            "padding: 8px; margin: 2px; background-color: white; "
            "border-radius: 4px; border: 1px solid #bdc3c7; "
            "}"
        )
        info_layout.addWidget(self.phase_percent_label)
        
        # 帧信息显示
        self.frame_info_label = qt.QLabel("帧信息: - / -")
        self.frame_info_label.setAlignment(qt.Qt.AlignCenter)
        self.frame_info_label.setStyleSheet(
            "QLabel { font-size: 12px; color: #6c757d; margin: 2px; }"
        )
        info_layout.addWidget(self.frame_info_label)
        
        # Series Description 显示
        self.series_description_label = qt.QLabel("序列描述: 未加载")
        self.series_description_label.setAlignment(qt.Qt.AlignCenter)
        self.series_description_label.setStyleSheet(
            "QLabel { "
            "font-size: 11px; color: #495057; padding: 4px; "
            "background-color: #e9ecef; border-radius: 3px; "
            "}"
        )
        self.series_description_label.setWordWrap(True)
        info_layout.addWidget(self.series_description_label)
        
        parent_layout.addWidget(info_frame, 0)  # 固定大小
    
    def _create_timeline_section(self, parent_layout):
        """创建时间轴控制区域"""
        timeline_frame = LayoutManager.create_section_frame("心动周期时间轴", LayoutType.SECTION_CONTAINER)
        timeline_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, timeline_frame)
        
        # 滑块
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.setMinimumHeight(30)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #f0f0f0;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5dade2;
            }
            QSlider::handle:horizontal:pressed {
                background: #2980b9;
            }
        """)
        timeline_layout.addWidget(self.timeline_slider)
        
        # 滑块标签（显示范围）
        self.slider_range_label = qt.QLabel("范围: 0 - 0")
        self.slider_range_label.setAlignment(qt.Qt.AlignCenter)
        self.slider_range_label.setStyleSheet(
            "QLabel { font-size: 10px; color: #6c757d; margin-top: 2px; }"
        )
        timeline_layout.addWidget(self.slider_range_label)
        
        parent_layout.addWidget(timeline_frame, 0)  # 固定大小
        
    def _create_phase_marking_buttons(self, parent_layout):
        """创建时相标记按钮"""
        button_frame = LayoutManager.create_section_frame("关键时相标记", LayoutType.BUTTON_GROUP)
        
        # 创建按钮容器布局
        button_container_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, button_frame)
        
        # 创建按钮水平布局
        button_layout = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        
        self.mark_end_diastole_button = LayoutManager.create_button_with_style("标记舒张末期", "warning")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setMinimumHeight(40)
        button_layout.addWidget(self.mark_end_diastole_button)
        
        self.mark_end_systole_button = LayoutManager.create_button_with_style("标记收缩末期", "primary")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setMinimumHeight(40)
        button_layout.addWidget(self.mark_end_systole_button)
        
        # 将按钮布局添加到容器布局
        button_container_layout.addLayout(button_layout)
        
        parent_layout.addWidget(button_frame, 0)  # 固定大小
        
    def _create_marked_phases_display(self, parent_layout):
        """创建已标记时相显示"""
        marked_frame = LayoutManager.create_section_frame("已标记时相", LayoutType.INFO_DISPLAY)
        marked_layout = LayoutManager.create_layout(LayoutType.INFO_DISPLAY, marked_frame)
        
        self.end_diastole_label = qt.QLabel("舒张末期: 未标记")
        self.end_diastole_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 4px;
                font-size: 11px;
                color: #e65100;
            }
        """)
        self.end_diastole_label.setWordWrap(True)
        self.end_diastole_label.setMinimumHeight(30)
        self.end_diastole_label.setCursor(qt.Qt.PointingHandCursor)
        self.end_diastole_label.setToolTip("双击跳转到舒张末期")
        marked_layout.addWidget(self.end_diastole_label)
        
        self.end_systole_label = qt.QLabel("收缩末期: 未标记")
        self.end_systole_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f3e5f5;
                border: 1px solid #9c27b0;
                border-radius: 4px;
                font-size: 11px;
                color: #4a148c;
                margin-top: 4px;
            }
        """)
        self.end_systole_label.setWordWrap(True)
        self.end_systole_label.setMinimumHeight(30)
        self.end_systole_label.setCursor(qt.Qt.PointingHandCursor)
        self.end_systole_label.setToolTip("双击跳转到收缩末期")
        marked_layout.addWidget(self.end_systole_label)
        
        parent_layout.addWidget(marked_frame, 1)  # 可扩展
        
    def _setup_connections(self):
        """设置信号连接"""
        self.timeline_slider.valueChanged.connect(self._on_timeline_slider_changed)
        self.mark_end_diastole_button.clicked.connect(
            lambda: self._mark_phase('end_diastole')
        )
        self.mark_end_systole_button.clicked.connect(
            lambda: self._mark_phase('end_systole')
        )
    
    def _setup_label_click_events(self):
        """设置标签点击事件"""
        # 为标签安装事件过滤器
        self.end_diastole_label.installEventFilter(self)
        self.end_systole_label.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理标签的双击事件"""
        if event.type() == qt.QEvent.MouseButtonDblClick:
            if obj == self.end_diastole_label:
                self.jump_to_marked_phase('end_diastole')
                return True
            elif obj == self.end_systole_label:
                self.jump_to_marked_phase('end_systole')
                return True
        # QGroupBox没有eventFilter方法，直接返回False让事件继续传播
        return False
    
    def _previous_frame(self):
        """切换到上一帧"""
        if self.timeline_slider.isEnabled():
            current_value = self.timeline_slider.value()
            if current_value > self.timeline_slider.minimum():
                self.timeline_slider.setValue(current_value - 1)
    
    def _next_frame(self):
        """切换到下一帧"""
        if self.timeline_slider.isEnabled():
            current_value = self.timeline_slider.value()
            if current_value < self.timeline_slider.maximum():
                self.timeline_slider.setValue(current_value + 1)
    
    def jump_to_marked_phase(self, phase_name: str):
        """跳转到已标记的时相"""
        marked_phase = self.session.get_marked_phase(phase_name)
        if marked_phase and marked_phase.get('frame_index') is not None:
            frame_index = marked_phase['frame_index']
            if self.set_current_frame_index(frame_index):
                phase_display_name = "舒张末期" if phase_name == 'end_diastole' else "收缩末期"
                logging.info(f"已跳转到{phase_display_name}: 帧 {frame_index}")
                return True
        return False
        
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
            
            # 更新滑块范围显示
            self.slider_range_label.setText(f"范围: 0 - {num_frames - 1} ({num_frames} 帧)")
            
            # 启用标记按钮
            self.mark_end_diastole_button.setEnabled(True)
            self.mark_end_systole_button.setEnabled(True)
            
            # 显示管理面板
            self.setVisible(True)
            
            # 初始化当前帧
            current_frame = browser_node.GetSelectedItemNumber()
            self.timeline_slider.setValue(current_frame)
            self._on_timeline_slider_changed(current_frame)
            
            # 更新已标记时相显示
            self._update_phase_labels()
            
            logging.info(f"心动周期管理已激活，共 {num_frames} 帧")
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
