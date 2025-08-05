"""
心动周期管理组件

该模块提供心动周期时间轴管理和时相标记功能，包括：
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
    from ..ui.styles import ComponentStyleFactory
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ui.styles import ComponentStyleFactory


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
        
        # 创建紧凑的心动周期控制界面
        self._create_compact_cardiac_cycle_ui(layout)
    
    def _create_compact_cardiac_cycle_ui(self, parent_layout):
        """创建紧凑的心动周期控制界面"""
        
        # 获取样式集合
        styles = ComponentStyleFactory.get_cardiac_cycle_styles()
        
        # === 第一行：当前信息 ===
        info_layout = LayoutManager.create_horizontal_layout(LayoutType.INFO_DISPLAY)
        
        # 帧信息（左侧）
        self.frame_info_label = qt.QLabel("帧: 0/0")
        self.frame_info_label.setAlignment(qt.Qt.AlignCenter)
        self.frame_info_label.setStyleSheet(styles["frame_info_label"])
        self.frame_info_label.setMinimumWidth(80)
        info_layout.addWidget(self.frame_info_label, 0)
        
        # 序列描述（右侧，可伸缩）
        self.series_description_label = qt.QLabel("序列: 未加载")
        self.series_description_label.setAlignment(qt.Qt.AlignLeft | qt.Qt.AlignVCenter)
        self.series_description_label.setStyleSheet(styles["series_description_label"])
        self.series_description_label.setWordWrap(True)
        self.series_description_label.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Preferred)
        info_layout.addWidget(self.series_description_label, 1)
        
        parent_layout.addLayout(info_layout, 0)
        
        # === 第二行：时间轴滑块 ===
        timeline_layout = LayoutManager.create_horizontal_layout(LayoutType.SECTION_CONTAINER)
        
        # 上一帧按钮
        self.prev_button = qt.QPushButton("◀")
        self.prev_button.setEnabled(False)
        self.prev_button.setFixedSize(30, 30)
        self.prev_button.setStyleSheet(styles["control_button"])
        self.prev_button.setToolTip("上一帧")
        timeline_layout.addWidget(self.prev_button, 0)
        
        # 时间轴滑块（主要部分）
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.setMinimumHeight(25)
        self.timeline_slider.setStyleSheet(styles["slider"])
        timeline_layout.addWidget(self.timeline_slider, 1)
        
        # 下一帧按钮
        self.next_button = qt.QPushButton("▶")
        self.next_button.setEnabled(False)
        self.next_button.setFixedSize(30, 30)
        self.next_button.setStyleSheet(styles["control_button"])
        self.next_button.setToolTip("下一帧")
        timeline_layout.addWidget(self.next_button, 0)
        
        parent_layout.addLayout(timeline_layout, 0)
        
        # === 第三行：时相标记和已标记时相（合并显示）===
        phase_layout = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        
        # 左侧：舒张末期
        diastole_container = qt.QVBoxLayout()
        diastole_container.setSpacing(4)
        
        self.mark_end_diastole_button = qt.QPushButton("标记舒张末期")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setMinimumHeight(35)
        self.mark_end_diastole_button.setStyleSheet(styles["mark_button"])
        diastole_container.addWidget(self.mark_end_diastole_button)
        
        self.end_diastole_label = qt.QLabel("舒张末期: 未标记")
        self.end_diastole_label.setStyleSheet(styles["marked_phase_label"])
        self.end_diastole_label.setWordWrap(True)
        self.end_diastole_label.setCursor(qt.Qt.PointingHandCursor)
        self.end_diastole_label.setToolTip("双击跳转到舒张末期")
        diastole_container.addWidget(self.end_diastole_label)
        
        phase_layout.addLayout(diastole_container, 1)
        
        # 中间：分隔符
        separator = qt.QFrame()
        separator.setFrameShape(qt.QFrame.VLine)
        separator.setFrameShadow(qt.QFrame.Sunken)
        separator.setStyleSheet(styles["section_separator"])
        phase_layout.addWidget(separator, 0)
        
        # 右侧：收缩末期
        systole_container = qt.QVBoxLayout()
        systole_container.setSpacing(4)
        
        self.mark_end_systole_button = qt.QPushButton("标记收缩末期")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setMinimumHeight(35)
        self.mark_end_systole_button.setStyleSheet(styles["mark_button"])
        systole_container.addWidget(self.mark_end_systole_button)
        
        self.end_systole_label = qt.QLabel("收缩末期: 未标记")
        self.end_systole_label.setStyleSheet(styles["marked_phase_label"])
        self.end_systole_label.setWordWrap(True)
        self.end_systole_label.setCursor(qt.Qt.PointingHandCursor)
        self.end_systole_label.setToolTip("双击跳转到收缩末期")
        systole_container.addWidget(self.end_systole_label)
        
        phase_layout.addLayout(systole_container, 1)
        
        parent_layout.addLayout(phase_layout, 0)
        
        # === 第三行：滑块范围信息 ===
        self.slider_range_label = qt.QLabel("范围: 0 - 0 (0 帧)")
        self.slider_range_label.setAlignment(qt.Qt.AlignCenter)
        self.slider_range_label.setStyleSheet(styles["range_label"])
        parent_layout.addWidget(self.slider_range_label, 0)
        
    def _setup_connections(self):
        """设置信号连接"""
        self.timeline_slider.valueChanged.connect(self._on_timeline_slider_changed)
        self.mark_end_diastole_button.clicked.connect(
            lambda: self._mark_phase('end_diastole')
        )
        self.mark_end_systole_button.clicked.connect(
            lambda: self._mark_phase('end_systole')
        )
        
        # 新增的前后帧按钮连接
        self.prev_button.clicked.connect(self._previous_frame)
        self.next_button.clicked.connect(self._next_frame)
    
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
            current_value = self.timeline_slider.value
            if current_value > self.timeline_slider.minimum:
                self.timeline_slider.setValue(current_value - 1)
    
    def _next_frame(self):
        """切换到下一帧"""
        if self.timeline_slider.isEnabled():
            current_value = self.timeline_slider.value
            if current_value < self.timeline_slider.maximum:
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
            
            # 启用所有控制按钮
            self.mark_end_diastole_button.setEnabled(True)
            self.mark_end_systole_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            
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
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.setVisible(False)
        
        # 重置显示
        self.frame_info_label.setText("帧: 0/0")
        self.series_description_label.setText("序列: 未加载")
        self.slider_range_label.setText("范围: 0 - 0 (0 帧)")
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
            
            # 显示帧信息
            total_frames = sequence_node.GetNumberOfDataNodes()
            self.frame_info_label.setText(f"帧: {value + 1}/{total_frames}")
                
            # 获取并显示Series Description
            series_desc = self.session.get_current_frame_series_description()
            if series_desc and series_desc != "未知":
                # 截断过长的描述
                if len(series_desc) > 30:
                    series_desc = series_desc[:27] + "..."
                self.series_description_label.setText(f"序列: {series_desc}")
            else:
                self.series_description_label.setText("序列: 未知")
            
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
            frame_idx = end_diastole['frame_index']
            phase_pct = end_diastole['phase_percent']
            self.end_diastole_label.setText(f"舒张末期: 帧{frame_idx + 1} ({phase_pct:.1f}%)")
        else:
            self.end_diastole_label.setText("舒张末期: 未标记")
            
        # 更新收缩末期显示
        if end_systole and end_systole['frame_index'] is not None:
            frame_idx = end_systole['frame_index']
            phase_pct = end_systole['phase_percent']
            self.end_systole_label.setText(f"收缩末期: 帧{frame_idx + 1} ({phase_pct:.1f}%)")
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
