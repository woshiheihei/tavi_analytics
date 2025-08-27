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
    from ..widgets import SectionCard
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
    from widgets import SectionCard


class CardiacCycleWidget(qt.QWidget):
    """心动周期管理组件
    
    提供4D心脏CT序列的时间轴管理和关键时相标记功能
    """
    
    # 新增：标记完成信号，参数为相位名 'end_diastole' 或 'end_systole'
    phaseMarked = qt.Signal(str)
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """初始化心动周期管理组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父窗口对象
        """
        super().__init__(parent)
        self.session = session
        self.setVisible(True)  # 默认显示
        
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
        layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)
        try:
            # 去除外边距，保证与其它 section 宽度一致
            layout.setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass
        
        # 创建心动周期管理section
        self._create_cardiac_cycle_section(layout)
    
    def _create_cardiac_cycle_section(self, parent_layout):
        """创建心动周期管理section - 使用通用SectionCard (紫色主题)"""
        section = SectionCard(title="心动周期管理", icon_text="⏱️", variant="purple", parent=self)
        main_layout = section.body_layout

        # 创建紧凑的心动周期控制界面
        self._create_compact_cardiac_cycle_ui(main_layout)

        parent_layout.addWidget(section, 0)  # 固定大小，不拉伸
    
    def _create_compact_cardiac_cycle_ui(self, parent_layout):
        """创建紧凑的心动周期控制界面 - 紫色卡片风格"""

        # 内容区域 - 白色背景，无边框
        content_container = qt.QWidget()
        content_container.setStyleSheet(
            """
            QWidget { background: #ffffff; border-radius: 12px; border: none; }
            """
        )
        content_layout = qt.QVBoxLayout(content_container)
        content_layout.setContentsMargins(12, 8, 12, 10)
        content_layout.setSpacing(8)

        # === 当前时相显示 ===
        phase_info_layout = qt.QHBoxLayout()
        phase_info_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧：当前时相标签
        current_phase_label = qt.QLabel("当前时相:")
        current_phase_label.setStyleSheet(
            """
            QLabel { font-size: 11px; color: #424242; font-weight: 500; background: transparent; border: none; }
            """
        )
        phase_info_layout.addWidget(current_phase_label)

        # 中央：时相百分比显示（已在UI中隐藏，保留对象以兼容后续需要）
        self.phase_percentage_label = qt.QLabel("")
        self.phase_percentage_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_percentage_label.setStyleSheet(
            """
            QLabel { font-size: 14px; font-weight: bold; color: #1976d2; background: transparent; border: none; padding: 4px 8px; border-radius: 5px; }
            """
        )
        # 隐藏R-R间期显示（仅移除UI展示，不影响内部相位百分比计算与存储）
        self.phase_percentage_label.setVisible(False)
        phase_info_layout.addWidget(self.phase_percentage_label, 1)

        content_layout.addLayout(phase_info_layout)

        # === 时间轴滑块区域 ===
        slider_container = qt.QWidget()
        slider_container.setStyleSheet(
            """
            QWidget { background: transparent; border: none; }
            """
        )
        slider_layout = qt.QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 6, 0, 6)
        slider_layout.setSpacing(6)

        # 滑块
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        # 为了避免手柄被裁剪，最小高度需要大于手柄总高度（包含边框）
        self.timeline_slider.setMinimumHeight(26)
        self.timeline_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            /* 圆形手柄：直径18px，半径9px，居中对齐6px槽 */
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196f3, stop:1 #1976d2);
                border: 2px solid #ffffff;
                width: 18px;
                height: 18px;
                margin: -6px 0; /* (手柄直径18 - 槽高6) / 2 */
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #2196f3);
            }
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976d2, stop:1 #1565c0);
            }
            QSlider::handle:horizontal:disabled {
                background: #bdbdbd;
                border: 2px solid #ffffff;
            }
            """
        )
        slider_layout.addWidget(self.timeline_slider)

        # 滑块标签
        labels_layout = qt.QHBoxLayout()
        labels_layout.setContentsMargins(0, 2, 0, 0)

        start_label = qt.QLabel("0% (舒张期开始)")
        start_label.setStyleSheet(
            """
            QLabel { font-size: 10px; color: #999; background: transparent; border: none; padding: 2px; }
            """
        )
        labels_layout.addWidget(start_label)

        mid_label = qt.QLabel("50% (收缩期)")
        mid_label.setAlignment(qt.Qt.AlignCenter)
        mid_label.setStyleSheet(
            """
            QLabel { font-size: 10px; color: #999; background: transparent; border: none; padding: 2px; }
            """
        )
        labels_layout.addWidget(mid_label)

        end_label = qt.QLabel("100% (舒张期结束)")
        end_label.setAlignment(qt.Qt.AlignRight)
        end_label.setStyleSheet(
            """
            QLabel { font-size: 10px; color: #999; background: transparent; border: none; padding: 2px; }
            """
        )
        labels_layout.addWidget(end_label)

        slider_layout.addLayout(labels_layout)
        content_layout.addWidget(slider_container)

        # === 标记按钮区域 ===
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(8)

        # 舒张末期按钮
        self.mark_end_diastole_button = qt.QPushButton("✓ 标记舒张末期")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setMinimumHeight(50)  # 增加高度以容纳两行文本
        self.mark_end_diastole_button.setMaximumHeight(60)  # 设置最大高度
        self.mark_end_diastole_button.setStyleSheet(
            """
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #2e7d32); 
                color: white; 
                border: none; 
                border-radius: 5px; 
                font-size: 11px; 
                font-weight: 600; 
                padding: 8px 10px; 
                text-align: center;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66bb6a, stop:1 #4caf50); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e7d32, stop:1 #1b5e20); }
            QPushButton:disabled { background: #f5f5f5; color: #bdbdbd; border: 1px solid #e0e0e0; }
            """
        )

        # 收缩末期按钮
        self.mark_end_systole_button = qt.QPushButton("✓ 标记收缩末期")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setMinimumHeight(50)  # 增加高度以容纳两行文本
        self.mark_end_systole_button.setMaximumHeight(60)  # 设置最大高度
        self.mark_end_systole_button.setStyleSheet(
            """
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #2e7d32); 
                color: white; 
                border: none; 
                border-radius: 5px; 
                font-size: 11px; 
                font-weight: 600; 
                padding: 8px 10px; 
                text-align: center;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66bb6a, stop:1 #4caf50); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e7d32, stop:1 #1b5e20); }
            QPushButton:disabled { background: #f5f5f5; color: #bdbdbd; border: 1px solid #e0e0e0; }
            """
        )

        buttons_layout.addWidget(self.mark_end_diastole_button)
        buttons_layout.addWidget(self.mark_end_systole_button)
        content_layout.addLayout(buttons_layout)

        # 提示信息
        tip_label = qt.QLabel("💡 拖动滑块查看整个心动周期，点击按钮标记关键时相用于后续测量")
        tip_label.setStyleSheet(
            """
            QLabel { font-size: 11px; color: #ff9800; background: #fff8e1; border: none; border-radius: 6px; padding: 8px 12px; text-align: center; }
            """
        )
        tip_label.setAlignment(qt.Qt.AlignCenter)
        tip_label.setWordWrap(True)
        content_layout.addWidget(tip_label)

        parent_layout.addWidget(content_container)
        
        # 保持原有的帧信息标签（隐藏，仅用于兼容性）
        self.frame_info_label = qt.QLabel()
        self.frame_info_label.setVisible(False)
        self.series_description_label = qt.QLabel()
        self.series_description_label.setVisible(False)
        
        # 保持原有的导航按钮（隐藏，仅用于兼容性）
        self.prev_button = qt.QPushButton()
        self.prev_button.setVisible(False)
        self.next_button = qt.QPushButton()
        self.next_button.setVisible(False)
        
        # 保留旧的标签组件，但设为隐藏（仅用于兼容性）
        self.end_diastole_label = qt.QLabel()
        self.end_diastole_label.setVisible(False)
        self.end_systole_label = qt.QLabel()
        self.end_systole_label.setVisible(False)
        self.slider_range_label = qt.QLabel()
        self.slider_range_label.setVisible(False)
        self.slider_range_label.setAlignment(qt.Qt.AlignCenter)
        self.slider_range_label.setStyleSheet(
            "QLabel { color: #999; font-size: 11px; padding: 2px; }"
        )
        parent_layout.addWidget(self.slider_range_label)
        
    def _setup_connections(self):
        """设置信号连接"""
        self.timeline_slider.valueChanged.connect(self._on_timeline_slider_changed)
        self.mark_end_diastole_button.clicked.connect(
            lambda: self._mark_phase('end_diastole')
        )
        self.mark_end_systole_button.clicked.connect(
            lambda: self._mark_phase('end_systole')
        )
        
        # 隐藏的前后帧按钮连接（仅用于兼容性）
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
            
            # 更新滑块范围显示（隐藏的标签，仅用于兼容性）
            self.slider_range_label.setText(f"范围: 0 - {num_frames - 1} ({num_frames} 帧)")
            
            # 启用所有控制按钮
            self.mark_end_diastole_button.setEnabled(True)
            self.mark_end_systole_button.setEnabled(True)
            
            # 启用隐藏的导航按钮（仅用于兼容性）
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
        # 不再隐藏组件，保持可见以与其它 section 对齐
        self.setVisible(True)
        
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
            
            # 计算并（如需）显示R-R间期百分比
            total_frames = sequence_node.GetNumberOfDataNodes()
            if total_frames > 0 and self.phase_percentage_label.isVisible():
                percentage = (value / (total_frames - 1)) * 100 if total_frames > 1 else 0
                self.phase_percentage_label.setText(f"{percentage:.1f}%")
            
            # 显示帧信息（隐藏的标签，仅用于兼容性）
            self.frame_info_label.setText(f"帧: {value + 1}/{total_frames}")
                
            # 获取并显示Series Description（隐藏的标签，仅用于兼容性）
            series_desc = self.session.get_current_frame_series_description()
            if series_desc and series_desc != "未知":
                # 截断过长的描述
                if len(series_desc) > 30:
                    series_desc = series_desc[:27] + "..."
                self.series_description_label.setText(f"序列: {series_desc}")
            else:
                self.series_description_label.setText("序列: 未知")
            
            # 更新按钮状态以显示已标记的时相
            self._update_button_marked_status()
            
    def _update_button_marked_status(self):
        """更新按钮状态以显示已标记的时相信息"""
        try:
            sequence_node = self.session.get_volume_sequence_node()
            if not sequence_node:
                return
                
            total_frames = sequence_node.GetNumberOfDataNodes()
            
            # 检查舒张末期标记
            ed_phase = self.session.get_marked_phase('end_diastole')
            if ed_phase.get('frame_index') is not None:
                frame_idx = ed_phase['frame_index']
                percentage = (frame_idx / (total_frames - 1)) * 100 if total_frames > 1 else 0
                self.mark_end_diastole_button.setText(f"✓ 标记舒张末期\n已标记 @ {percentage:.1f}%")
            else:
                self.mark_end_diastole_button.setText("✓ 标记舒张末期")
                
            # 检查收缩末期标记
            es_phase = self.session.get_marked_phase('end_systole')
            if es_phase.get('frame_index') is not None:
                frame_idx = es_phase['frame_index']
                percentage = (frame_idx / (total_frames - 1)) * 100 if total_frames > 1 else 0
                self.mark_end_systole_button.setText(f"✓ 标记收缩末期\n已标记 @ {percentage:.1f}%")
            else:
                self.mark_end_systole_button.setText("✓ 标记收缩末期")
                
        except Exception as e:
            logging.debug(f"更新按钮标记状态时发生错误: {e}")
            
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
            
            # 通知外部：相位已标记
            try:
                self.phaseMarked.emit(phase_name)
            except Exception as _:
                pass
            
            phase_display_name = "舒张末期" if phase_name == 'end_diastole' else "收缩末期"
            logging.info(f"已标记{phase_display_name}: 帧{frame_index}, {phase_percent:.1f}%")
            
    def _update_phase_labels(self):
        """更新时相标记显示"""
        end_diastole = self.session.get_marked_phase('end_diastole')
        end_systole = self.session.get_marked_phase('end_systole')
        
        # 更新舒张末期显示（隐藏的标签，仅用于兼容性）
        if end_diastole and end_diastole['frame_index'] is not None:
            frame_idx = end_diastole['frame_index']
            phase_pct = end_diastole['phase_percent']
            self.end_diastole_label.setText(f"舒张末期: 帧{frame_idx + 1} ({phase_pct:.1f}%)")
            self.end_diastole_label.setStyleSheet(
                "QLabel { color: #1976d2; font-size: 11px; padding: 4px 8px; "
                "background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 3px; }"
            )
        else:
            self.end_diastole_label.setText("舒张末期: 未标记")
            self.end_diastole_label.setStyleSheet(
                "QLabel { color: #666; font-size: 11px; padding: 4px 8px; "
                "background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 3px; }"
            )
            
        # 更新收缩末期显示（隐藏的标签，仅用于兼容性）
        if end_systole and end_systole['frame_index'] is not None:
            frame_idx = end_systole['frame_index']
            phase_pct = end_systole['phase_percent']
            self.end_systole_label.setText(f"收缩末期: 帧{frame_idx + 1} ({phase_pct:.1f}%)")
            self.end_systole_label.setStyleSheet(
                "QLabel { color: #f57c00; font-size: 11px; padding: 4px 8px; "
                "background-color: #fff3e0; border: 1px solid #ff9800; border-radius: 3px; }"
            )
        else:
            self.end_systole_label.setText("收缩末期: 未标记")
            self.end_systole_label.setStyleSheet(
                "QLabel { color: #666; font-size: 11px; padding: 4px 8px; "
                "background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 3px; }"
            )
            
        # 更新按钮状态以显示已标记的时相
        self._update_button_marked_status()
            
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
