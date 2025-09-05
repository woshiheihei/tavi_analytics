"""
瓣膜叠加组件 - Valve Overlay Widget

提供一键将瓣膜支架（valve）叠加到Red切片视图的功能，支持：
- 瓣膜支架自动对齐到当前Red切片位置
- 透明度调节功能
- 叠加状态显示与控制
- 变换微调选项

作者：TAVR Research Team
创建时间：2025年9月
"""

import logging
import os
import sys
from typing import Optional, Callable
import qt

# 轻量依赖，仅在需要时注入
try:
    from ..core.session import TAVRStudySession
    from ..widgets.section_card import SectionCard
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from widgets.section_card import SectionCard


class ValveOverlayWidget(qt.QWidget):
    """
    瓣膜叠加组件
    
    提供瓣膜支架到Red切片视图的一键叠加功能，包括：
    - 自动检测瓣膜数据
    - 一键叠加/取消叠加
    - 透明度实时调节
    - 变换微调选项
    - 状态指示与反馈
    """
    
    # 定义信号
    overlayEnabled = qt.Signal(bool)      # 叠加启用/禁用信号
    opacityChanged = qt.Signal(float)     # 透明度改变信号
    rotationChanged = qt.Signal(int)      # 旋转角度改变信号
    statusUpdated = qt.Signal(str)        # 状态更新信号
    
    def __init__(self, session: Optional[TAVRStudySession] = None, parent=None, compact: bool = True):
        """
        初始化瓣膜叠加组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父组件
        """
        super().__init__(parent)

        # 基本状态
        self.session = session
        self.valve_node = None
        self.transform_node = None
        self.is_overlay_active = False
        self.current_opacity = 0.6
        self.current_rotation = 0  # 当前旋转角度
        self.base_transform_matrix = None  # 基础叠加矩阵（不含旋转）
        self.cumulative_offset = [0.0, 0.0]  # 累计平面内偏移量 [x, y] in mm
        self._compact = bool(compact)

        # 设置组件属性
        self.setObjectName("ValveOverlayWidget")

        # 回调函数列表
        self.overlay_callbacks = []
        self.opacity_callbacks = []
        self.rotation_callbacks = []  # 旋转回调函数列表

        # 创建界面
        self._setup_ui()

        # 初始化检查瓣膜数据
        self._check_valve_availability()

        logging.info("ValveOverlayWidget 初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4 if self._compact else 8)

        # 使用SectionCard包装
        # 紧凑：改用更素的样式并缩小标题栏
        variant = "neutral" if self._compact else "blue"
        self.section_card = SectionCard(
            title="瓣膜支架叠加",
            icon_text="🩺",
            variant=variant,
            parent=self,
            header_compact=True
        )

        # 进一步压缩卡片的内边距与行间距
        try:
            self.section_card._root_layout.setContentsMargins(12, 10, 12, 12)
            self.section_card._root_layout.setSpacing(8 if self._compact else 12)
            self.section_card.body_layout.setSpacing(6 if self._compact else 8)
        except Exception:
            pass

        # 在卡片内容区创建控件
        self._create_controls()

        main_layout.addWidget(self.section_card)
    
    def _create_controls(self):
        """创建控制组件"""
        # 主操作按钮区域（常显）
        self._create_action_section()

        # 透明度调节区域（常显）
        self._create_opacity_section()

        # 高级区域（旋转/微调/更多） -> 容器，可折叠
        self.advanced_container = qt.QWidget()
        adv_v = qt.QVBoxLayout(self.advanced_container)
        adv_v.setContentsMargins(0, 0, 0, 0)
        adv_v.setSpacing(6 if self._compact else 8)

        rot = self._create_rotation_section(return_widget=True)
        if rot is not None:
            adv_v.addWidget(rot)

        pos = self._create_position_adjust_section(return_widget=True)
        if pos is not None:
            adv_v.addWidget(pos)

        more = self._create_advanced_section(return_widget=True)
        if more is not None:
            adv_v.addWidget(more)

        self.section_card.add_widget(self.advanced_container)

        # 紧凑模式下默认收起高级区域，并在标题栏放置一个小型切换按钮
        self.advanced_container.setVisible(not self._compact)
        self._install_header_toggle()

    def _install_header_toggle(self):
        try:
            toggle = qt.QToolButton()
            toggle.setText("高级")
            toggle.setCheckable(True)
            toggle.setChecked(not self._compact)
            toggle.setAutoRaise(True)
            toggle.setToolTip("显示/隐藏高级控制")
            toggle.setStyleSheet("QToolButton{font-size:11px; padding:2px 6px; color:#2563eb;} QToolButton:checked{color:#1f2937;}")
            toggle.toggled.connect(self.advanced_container.setVisible)
            self.section_card.add_header_widget(toggle, align_right=True)
            self._advanced_toggle = toggle
        except Exception:
            pass
    
    def _create_action_section(self):
        """创建主操作按钮区域"""
        action_layout = qt.QHBoxLayout()
        action_layout.setSpacing(8 if self._compact else 12)

        # 主操作按钮
        self.overlay_btn = qt.QPushButton("🔄 启用叠加")
        self.overlay_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 10px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                min-width: 96px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.overlay_btn.clicked.connect(self._toggle_overlay)
        self.overlay_btn.setEnabled(False)

        action_layout.addWidget(self.overlay_btn)
        action_layout.addStretch()

        self.section_card.add_layout(action_layout)
    
    def _create_opacity_section(self):
        """创建透明度调节区域"""
        opacity_frame = qt.QFrame()
        opacity_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        opacity_layout = qt.QVBoxLayout(opacity_frame)
        opacity_layout.setSpacing(4 if self._compact else 6)

        # 透明度标签
        opacity_header = qt.QHBoxLayout()
        opacity_label = qt.QLabel("透明度")
        opacity_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #495057;
                background: transparent;
            }
        """)

        self.opacity_value_label = qt.QLabel("60%")
        self.opacity_value_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #2563eb;
                background: transparent;
                font-weight: bold;
            }
        """)

        opacity_header.addWidget(opacity_label)
        opacity_header.addStretch()
        opacity_header.addWidget(self.opacity_value_label)

        opacity_layout.addLayout(opacity_header)

        # 透明度滑块
        self.opacity_slider = qt.QSlider(qt.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(60)  # 默认60%
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #2563eb;
                border: 1px solid #2563eb;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #dee2e6;
                border: 1px solid #dee2e6;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #2563eb;
                border: 1px solid #2563eb;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.opacity_slider.setEnabled(False)

        opacity_layout.addWidget(self.opacity_slider)

        self.section_card.add_widget(opacity_frame)
    
    def _create_rotation_section(self, return_widget: bool = False):
        """创建旋转控制区域"""
        rotation_frame = qt.QFrame()
        rotation_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        rotation_layout = qt.QVBoxLayout(rotation_frame)
        rotation_layout.setSpacing(4 if self._compact else 6)

        # 旋转标签和角度显示
        rotation_header = qt.QHBoxLayout()
        rotation_label = qt.QLabel("支架旋转")
        rotation_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
            }
        """)

        self.rotation_value_label = qt.QLabel("0°")
        self.rotation_value_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #6c757d;
                font-weight: bold;
            }
        """)

        rotation_header.addWidget(rotation_label)
        rotation_header.addStretch()
        rotation_header.addWidget(self.rotation_value_label)

        rotation_layout.addLayout(rotation_header)

        # 旋转滑块
        self.rotation_slider = qt.QSlider(qt.Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)  # 默认0度
        self.rotation_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #16a34a;
                border: 1px solid #16a34a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #dee2e6;
                border: 1px solid #dee2e6;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #16a34a;
                border: 1px solid #16a34a;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
        """)
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)
        self.rotation_slider.setEnabled(False)

        rotation_layout.addWidget(self.rotation_slider)

        # 紧凑模式不显示说明行，使用 tooltip 替代
        if not self._compact:
            info_label = qt.QLabel("围绕当前切片法线方向旋转支架 (-180° ~ +180°)")
            info_label.setStyleSheet("""
                QLabel { font-size: 10px; color: #6c757d; font-style: italic; }
            """)
            rotation_layout.addWidget(info_label)
        else:
            rotation_frame.setToolTip("围绕切片法线旋转支架 (-180°~+180°)")

        if return_widget:
            return rotation_frame
        else:
            self.section_card.add_widget(rotation_frame)

    def _create_position_adjust_section(self, return_widget: bool = False):
        """创建方向键微调区域"""
        adjust_frame = qt.QFrame()
        adjust_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        adjust_layout = qt.QVBoxLayout(adjust_frame)
        adjust_layout.setSpacing(6 if self._compact else 8)

        # 标题和步长设置
        header_layout = qt.QHBoxLayout()
        adjust_label = qt.QLabel("平面内微调")
        adjust_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
            }
        """)

        # 步长选择
        step_label = qt.QLabel("步长:")
        step_label.setStyleSheet("font-size: 10px; color: #6c757d;")

        self.step_combo = qt.QComboBox()
        self.step_combo.addItems(["0.5mm", "1.0mm", "2.0mm", "5.0mm"])
        self.step_combo.setCurrentText("1.0mm")
        self.step_combo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 1px 6px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: white;
                min-width: 60px;
            }
        """)

        header_layout.addWidget(adjust_label)
        header_layout.addStretch()
        header_layout.addWidget(step_label)
        header_layout.addWidget(self.step_combo)

        adjust_layout.addLayout(header_layout)

        # 游戏手柄式方向键布局
        dpad_layout = qt.QGridLayout()
        dpad_layout.setSpacing(2 if self._compact else 4)

        # 创建方向按钮
        button_style = """
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #007bff;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                color: #007bff;
                width: 28px;
                height: 28px;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #007bff;
                color: white;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                border-color: #dee2e6;
                color: #6c757d;
            }
        """

        # 上键 (向上移动)
        self.up_btn = qt.QPushButton("▲")
        self.up_btn.setStyleSheet(button_style)
        self.up_btn.setToolTip("向上微调")
        self.up_btn.clicked.connect(lambda: self._adjust_position('up'))
        self.up_btn.setEnabled(False)

        # 下键 (向下移动)
        self.down_btn = qt.QPushButton("▼")
        self.down_btn.setStyleSheet(button_style)
        self.down_btn.setToolTip("向下微调")
        self.down_btn.clicked.connect(lambda: self._adjust_position('down'))
        self.down_btn.setEnabled(False)

        # 左键 (向左移动)
        self.left_btn = qt.QPushButton("◀")
        self.left_btn.setStyleSheet(button_style)
        self.left_btn.setToolTip("向左微调")
        self.left_btn.clicked.connect(lambda: self._adjust_position('left'))
        self.left_btn.setEnabled(False)

        # 右键 (向右移动)
        self.right_btn = qt.QPushButton("▶")
        self.right_btn.setStyleSheet(button_style)
        self.right_btn.setToolTip("向右微调")
        self.right_btn.clicked.connect(lambda: self._adjust_position('right'))
        self.right_btn.setEnabled(False)

        # 中心重置按钮
        self.center_btn = qt.QPushButton("●")
        self.center_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #28a745;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                color: #28a745;
                width: 28px;
                height: 28px;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #e8f5e8;
                border-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #28a745;
                color: white;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                border-color: #dee2e6;
                color: #6c757d;
            }
        """)
        self.center_btn.setToolTip("重置到中心位置")
        self.center_btn.clicked.connect(self._reset_position_adjustment)
        self.center_btn.setEnabled(False)

        # 菱形布局：上下左右+中心
        dpad_layout.addWidget(self.up_btn, 0, 1, qt.Qt.AlignCenter)     # 上
        dpad_layout.addWidget(self.left_btn, 1, 0, qt.Qt.AlignCenter)   # 左
        dpad_layout.addWidget(self.center_btn, 1, 1, qt.Qt.AlignCenter) # 中心
        dpad_layout.addWidget(self.right_btn, 1, 2, qt.Qt.AlignCenter)  # 右
        dpad_layout.addWidget(self.down_btn, 2, 1, qt.Qt.AlignCenter)   # 下

        # 设置列和行的拉伸，确保按钮居中
        dpad_layout.setColumnStretch(0, 1)
        dpad_layout.setColumnStretch(1, 0)  # 中间列不拉伸
        dpad_layout.setColumnStretch(2, 1)

        # 添加方向键到主布局
        dpad_container = qt.QWidget()
        dpad_container.setLayout(dpad_layout)
        adjust_layout.addWidget(dpad_container, qt.Qt.AlignCenter)

        # 说明文字
        info_label = qt.QLabel("在当前切片平面内进行精确位置调整")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 9px;
                color: #6c757d;
                font-style: italic;
                margin-top: 2px;
            }
        """)
        info_label.setAlignment(qt.Qt.AlignCenter)
        adjust_layout.addWidget(info_label)

        # 累计位移显示
        self.offset_label = qt.QLabel("偏移: (0.0, 0.0) mm")
        self.offset_label.setStyleSheet("""
            QLabel {
                font-size: 9px;
                color: #495057;
                background-color: #eef2f7;
                border-radius: 3px;
                padding: 2px 6px;
                margin-top: 2px;
            }
        """)
        self.offset_label.setAlignment(qt.Qt.AlignCenter)
        adjust_layout.addWidget(self.offset_label)

        if return_widget:
            return adjust_frame
        else:
            self.section_card.add_widget(adjust_frame)

        # 初始化累计偏移量
        self.cumulative_offset = [0.0, 0.0]  # [x_offset, y_offset] in mm

    def _create_advanced_section(self, return_widget: bool = False):
        """创建高级选项区域"""
        advanced_layout = qt.QHBoxLayout()
        advanced_layout.setSpacing(6 if self._compact else 8)

        # 微调变换按钮
        adjust_btn = qt.QPushButton("⚙️ 微调")
        adjust_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        adjust_btn.setToolTip("打开Transforms模块进行精细位置调整")
        adjust_btn.clicked.connect(self._open_transforms_module)
        self.adjust_btn = adjust_btn
        adjust_btn.setEnabled(False)

        # 重置按钮
        reset_btn = qt.QPushButton("🔄 重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        reset_btn.setToolTip("重置瓣膜叠加到初始状态")
        reset_btn.clicked.connect(self._reset_overlay)
        self.reset_btn = reset_btn
        reset_btn.setEnabled(False)

        advanced_layout.addWidget(adjust_btn)
        advanced_layout.addWidget(reset_btn)
        advanced_layout.addStretch()

        if return_widget:
            container = qt.QWidget()
            c_layout = qt.QHBoxLayout(container)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(6 if self._compact else 8)
            c_layout.addLayout(advanced_layout)
            c_layout.addStretch()
            return container
        else:
            self.section_card.add_layout(advanced_layout)
    
    def _check_valve_availability(self):
        """检查瓣膜数据可用性 - 后台检测，只输出日志"""
        try:
            # 尝试在Slicer中查找valve节点
            import slicer
            
            def find_volume_by_name(class_name, target_name):
                nodes = slicer.util.getNodesByClass(class_name)
                exact = [n for n in nodes if n.GetName() == target_name]
                if exact:
                    return exact[0]
                lower = target_name.lower()
                partial = [n for n in nodes if lower in n.GetName().lower()]
                return partial[0] if partial else None
            
            # 查找valve节点
            valve_node = find_volume_by_name('vtkMRMLVectorVolumeNode', 'valve')
            if valve_node is None:
                valve_node = find_volume_by_name('vtkMRMLScalarVolumeNode', 'valve')
            
            if valve_node:
                self.valve_node = valve_node
                logging.info(f"已找到瓣膜数据: {valve_node.GetName()}")
                self.overlay_btn.setEnabled(True)
                
                # 检查是否已有叠加状态
                self._check_overlay_status()
                
            else:
                self.valve_node = None
                logging.warning("未找到瓣膜数据 (名称: valve)")
                self.overlay_btn.setEnabled(False)
                self._update_overlay_status(False)
            
        except Exception as e:
            logging.error(f"检查瓣膜数据时出错: {e}")
            self.valve_node = None
            self.overlay_btn.setEnabled(False)
    
    def _check_overlay_status(self):
        """检查当前叠加状态"""
        try:
            import slicer
            
            # 检查变换节点是否存在
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', 'ValveToRedSlice')
            
            # 检查Red视图前景设置
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if red_widget:
                comp_node = red_widget.mrmlSliceCompositeNode()
                foreground_id = comp_node.GetForegroundVolumeID()
                
                # 判断是否已经叠加
                is_active = (transform_node is not None and 
                           self.valve_node is not None and 
                           foreground_id == self.valve_node.GetID())
                
                self._update_overlay_status(is_active)
                
                if is_active:
                    # 更新透明度显示
                    opacity = comp_node.GetForegroundOpacity()
                    self.current_opacity = opacity
                    self.opacity_slider.setValue(int(opacity * 100))
                    self.opacity_value_label.setText(f"{int(opacity * 100)}%")
                
        except Exception as e:
            logging.error(f"检查叠加状态时出错: {e}")
    
    def _toggle_overlay(self):
        """切换叠加状态"""
        if self.is_overlay_active:
            self._disable_overlay()
        else:
            self._enable_overlay()
    
    def _enable_overlay(self):
        """启用瓣膜叠加"""
        try:
            import slicer
            import vtk
            
            if not self.valve_node:
                self.statusUpdated.emit("错误: 瓣膜数据不可用")
                return
            
            # 显示进度反馈
            self.overlay_btn.setText("🔄 正在叠加...")
            self.overlay_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 执行叠加脚本（基于文档中的逻辑）
            success = self._execute_valve_overlay()
            
            if success:
                self._update_overlay_status(True)
                self.statusUpdated.emit("瓣膜叠加已启用")
                self.overlayEnabled.emit(True)
                
                # 调用回调函数
                for callback in self.overlay_callbacks:
                    try:
                        callback(True)
                    except Exception as e:
                        logging.error(f"执行叠加回调失败: {e}")
            else:
                self.overlay_btn.setText("🔄 启用叠加")
                self.overlay_btn.setEnabled(True)
                self.statusUpdated.emit("瓣膜叠加失败")
                
        except Exception as e:
            logging.error(f"启用瓣膜叠加时出错: {e}")
            self.overlay_btn.setText("🔄 启用叠加")
            self.overlay_btn.setEnabled(True)
            self.statusUpdated.emit(f"叠加错误: {str(e)}")
    
    def _disable_overlay(self):
        """禁用瓣膜叠加"""
        try:
            import slicer
            
            # 获取Red视图
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if red_widget:
                comp_node = red_widget.mrmlSliceCompositeNode()
                
                # 清除前景设置
                comp_node.SetForegroundVolumeID("")
                comp_node.SetForegroundOpacity(0.0)
                
                # 移除变换（可选）
                if self.valve_node:
                    self.valve_node.SetAndObserveTransformNodeID("")
                
                red_widget.sliceView().scheduleRender()
            
            # 重置位置微调状态
            self.cumulative_offset = [0.0, 0.0]
            self.offset_label.setText("偏移: (0.0, 0.0) mm")
            
            self._update_overlay_status(False)
            self.statusUpdated.emit("瓣膜叠加已禁用")
            self.overlayEnabled.emit(False)
            
            # 调用回调函数
            for callback in self.overlay_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    logging.error(f"执行禁用回调失败: {e}")
                    
        except Exception as e:
            logging.error(f"禁用瓣膜叠加时出错: {e}")
            self.statusUpdated.emit(f"禁用错误: {str(e)}")
    
    def _execute_valve_overlay(self) -> bool:
        """执行瓣膜叠加（基于文档逻辑）"""
        try:
            import slicer
            import vtk
            
            # 获取Red切片方向
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if not red_widget:
                logging.error('未找到 Red 视图')
                return False
            
            red_slice_node = red_widget.mrmlSliceNode()
            slice_to_ras = red_slice_node.GetSliceToRAS()
            
            # 构建中心化+缩放矩阵
            img = self.valve_node.GetImageData()
            if not img:
                logging.error('valve 体数据没有 ImageData')
                return False
            
            width, height, depth = img.GetDimensions()
            spx, spy, spz = self.valve_node.GetSpacing()
            
            S = vtk.vtkMatrix4x4()
            S.Identity()
            S.SetElement(0, 0, float(spx) if spx else 1.0)
            S.SetElement(1, 1, float(spy) if spy else 1.0)
            S.SetElement(2, 2, 1.0)
            
            cx = (width - 1) * 0.5
            cy = (height - 1) * 0.5
            S.SetElement(0, 3, -cx * (float(spx) if spx else 1.0))
            S.SetElement(1, 3, -cy * (float(spy) if spy else 1.0))
            
            # 获取valve IJK->RAS并求逆
            M_ijkToRas = vtk.vtkMatrix4x4()
            self.valve_node.GetIJKToRASMatrix(M_ijkToRas)
            M_ijkToRas_inv = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(M_ijkToRas, M_ijkToRas_inv)
            
            # 计算父变换: P = SliceToRAS * S * (IJKToRAS)^-1
            P_tmp = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(S, M_ijkToRas_inv, P_tmp)
            P = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(slice_to_ras, P_tmp, P)
            
            # 创建/应用变换节点
            transform_name = 'ValveToRedSlice'
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', transform_name)
            if not transform_node:
                transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', transform_name)
            
            transform_node.SetMatrixTransformToParent(P)
            self.valve_node.SetAndObserveTransformNodeID(transform_node.GetID())
            self.transform_node = transform_node
            # 记录基础矩阵，旋转滑块以此为基准叠加
            self.base_transform_matrix = vtk.vtkMatrix4x4()
            self.base_transform_matrix.DeepCopy(P)
            
            # 配置Red切片叠加
            comp_node = red_widget.mrmlSliceCompositeNode()
            comp_node.SetForegroundVolumeID(self.valve_node.GetID())
            comp_node.SetForegroundOpacity(self.current_opacity)
            
            # 显示优化
            valve_display = self.valve_node.GetDisplayNode()
            if valve_display:
                try:
                    valve_display.SetInterpolate(False)
                except Exception:
                    pass
            
            red_widget.sliceView().scheduleRender()
            
            logging.info(f"瓣膜叠加成功: {self.valve_node.GetName()}")
            return True
            
        except Exception as e:
            logging.error(f"执行瓣膜叠加失败: {e}")
            return False
    
    def _update_overlay_status(self, is_active: bool):
        """更新叠加状态UI"""
        self.is_overlay_active = is_active
        
        if is_active:
            self.overlay_btn.setText("❌ 禁用叠加")
            self.overlay_btn.setStyleSheet("""
                QPushButton {
            padding: 6px 10px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
            font-size: 12px;
                    font-weight: bold;
            min-width: 96px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.opacity_slider.setEnabled(True)
            self.rotation_slider.setEnabled(True)
            # 启用方向键微调按钮
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(True)
            self.left_btn.setEnabled(True)
            self.right_btn.setEnabled(True)
            self.center_btn.setEnabled(True)
            self.adjust_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
        else:
            self.overlay_btn.setText("🔄 启用叠加")
            self.overlay_btn.setStyleSheet("""
                QPushButton {
            padding: 6px 10px;
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
            font-size: 12px;
                    font-weight: bold;
            min-width: 96px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.opacity_slider.setEnabled(False)
            self.rotation_slider.setEnabled(False)
            # 禁用方向键微调按钮
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(False)
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
            self.center_btn.setEnabled(False)
            self.adjust_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
        
        self.overlay_btn.setEnabled(True)
    
    def _apply_rotation_transform(self, angle_degrees: int):
        """应用旋转：围绕当前切片法线，旋转中心采用“平面内微调后的中心”。"""
        try:
            mat = self._compose_final_transform(angle_degrees)
            if mat is None:
                return
            # 应用变换
            self.transform_node.SetMatrixTransformToParent(mat)
            # 刷新视图
            import slicer
            slicer.app.layoutManager().sliceWidget('Red').sliceView().scheduleRender()
        except Exception as e:
            logging.error(f"应用旋转变换失败: {e}")

    def _compose_final_transform(self, angle_degrees: int, offset_xy: Optional[list] = None):
        """组合最终变换矩阵 = Rot(adjustedCenter, normal, angle) * T(offsetRAS) * Base

        offset_xy: [x_mm, y_mm] 为切片平面内的偏移，默认取 self.cumulative_offset。
        返回 vtkMatrix4x4，失败时返回 None。
        """
        try:
            import slicer
            import vtk
            import math

            if not hasattr(self, 'transform_node') or not self.transform_node:
                logging.warning("无法组合变换: 变换节点不存在")
                return None
            if self.base_transform_matrix is None:
                # 若无基础矩阵，使用当前矩阵作为基础
                self.base_transform_matrix = vtk.vtkMatrix4x4()
                self.transform_node.GetMatrixTransformToParent(self.base_transform_matrix)

            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if not red_widget:
                logging.error("无法获取Red slice widget")
                return None
            slice_node = red_widget.mrmlSliceNode()
            slice_to_ras = slice_node.GetSliceToRAS()

            # Slice 基向量与中心
            xdir = [slice_to_ras.GetElement(0, 0), slice_to_ras.GetElement(1, 0), slice_to_ras.GetElement(2, 0)]
            ydir = [slice_to_ras.GetElement(0, 1), slice_to_ras.GetElement(1, 1), slice_to_ras.GetElement(2, 1)]
            normal = [slice_to_ras.GetElement(0, 2), slice_to_ras.GetElement(1, 2), slice_to_ras.GetElement(2, 2)]
            center = [slice_to_ras.GetElement(0, 3), slice_to_ras.GetElement(1, 3), slice_to_ras.GetElement(2, 3)]

            # 偏移（默认取当前累计）
            if offset_xy is None:
                offset_xy = getattr(self, 'cumulative_offset', [0.0, 0.0])
            xoff, yoff = float(offset_xy[0]), float(offset_xy[1])
            ras_offset = [xoff * xdir[0] + yoff * ydir[0],
                          xoff * xdir[1] + yoff * ydir[1],
                          xoff * xdir[2] + yoff * ydir[2]]

            # 旋转角度（弧度）
            angle_radians = math.radians(angle_degrees)
            c, s = math.cos(angle_radians), math.sin(angle_radians)

            # 规范化法线
            nlen = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
            if nlen == 0:
                logging.error("法线向量长度为0")
                return None
            nx, ny, nz = normal[0]/nlen, normal[1]/nlen, normal[2]/nlen

            # Rodrigues 旋转矩阵
            R = vtk.vtkMatrix4x4(); R.Identity()
            R.SetElement(0,0, c+nx*nx*(1-c)); R.SetElement(0,1, nx*ny*(1-c)-nz*s); R.SetElement(0,2, nx*nz*(1-c)+ny*s)
            R.SetElement(1,0, ny*nx*(1-c)+nz*s); R.SetElement(1,1, c+ny*ny*(1-c)); R.SetElement(1,2, ny*nz*(1-c)-nx*s)
            R.SetElement(2,0, nz*nx*(1-c)-ny*s); R.SetElement(2,1, nz*ny*(1-c)+nx*s); R.SetElement(2,2, c+nz*nz*(1-c))

            # 旋转中心 = slice中心 + 偏移
            adj_center = [center[0] + ras_offset[0], center[1] + ras_offset[1], center[2] + ras_offset[2]]
            T1 = vtk.vtkMatrix4x4(); T1.Identity()
            T1.SetElement(0,3, -adj_center[0]); T1.SetElement(1,3, -adj_center[1]); T1.SetElement(2,3, -adj_center[2])
            T2 = vtk.vtkMatrix4x4(); T2.Identity()
            T2.SetElement(0,3,  adj_center[0]); T2.SetElement(1,3,  adj_center[1]); T2.SetElement(2,3,  adj_center[2])

            # 平移矩阵（将对象从 slice 中心移动到调整后的中心）
            Toff = vtk.vtkMatrix4x4(); Toff.Identity()
            Toff.SetElement(0,3, ras_offset[0]); Toff.SetElement(1,3, ras_offset[1]); Toff.SetElement(2,3, ras_offset[2])

            # 组合：Rot(adjustedCenter) * T(offset) * Base
            tmp = vtk.vtkMatrix4x4()
            rot_about = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(R, T1, tmp)
            vtk.vtkMatrix4x4.Multiply4x4(T2, tmp, rot_about)

            tmp2 = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(Toff, self.base_transform_matrix, tmp2)
            final_m = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(rot_about, tmp2, final_m)

            return final_m
        except Exception as e:
            logging.error(f"组合最终变换失败: {e}")
            return None

    def _adjust_position(self, direction: str):
        """在当前切片平面内进行位置微调"""
        try:
            # 获取步长
            # Support both method and property forms across Qt wrappers
            current_text_attr = getattr(self.step_combo, 'currentText', '')
            step_text = current_text_attr() if callable(current_text_attr) else str(current_text_attr)
            step_size = float(step_text.replace('mm', ''))
            
            # 更新累计偏移量
            if direction == 'up':
                self.cumulative_offset[1] += step_size
            elif direction == 'down':
                self.cumulative_offset[1] -= step_size
            elif direction == 'left':
                self.cumulative_offset[0] -= step_size
            elif direction == 'right':
                self.cumulative_offset[0] += step_size
            
            # 更新显示
            self.offset_label.setText(
                f"偏移: ({self.cumulative_offset[0]:.1f}, {self.cumulative_offset[1]:.1f}) mm"
            )
            
            # 应用位置调整（基于当前旋转 + 偏移的统一公式）
            if self.is_overlay_active and hasattr(self, 'transform_node') and self.transform_node:
                mat = self._compose_final_transform(self.current_rotation)
                if mat is not None:
                    self.transform_node.SetMatrixTransformToParent(mat)
                    import slicer
                    slicer.app.layoutManager().sliceWidget('Red').sliceView().scheduleRender()
                
        except Exception as e:
            logging.error(f"位置微调失败: {e}")
    
    def _apply_position_adjustment(self):
        """已由统一组合方法替代，保留占位以兼容旧调用。"""
        try:
            mat = self._compose_final_transform(self.current_rotation)
            if mat is not None:
                self.transform_node.SetMatrixTransformToParent(mat)
                import slicer
                slicer.app.layoutManager().sliceWidget('Red').sliceView().scheduleRender()
                logging.info(f"应用位置微调: {self.cumulative_offset}")
        except Exception as e:
            logging.error(f"应用位置调整失败: {e}")
    
    def _get_rotated_base_matrix(self, output_matrix):
        """已由统一组合方法替代，保留以兼容旧调用。"""
        try:
            mat = self._compose_final_transform(self.current_rotation, [0.0, 0.0])
            if mat is None:
                return
            output_matrix.DeepCopy(mat)
        except Exception as e:
            logging.error(f"获取旋转基础矩阵失败: {e}")
    
    def _reset_position_adjustment(self):
        """重置位置微调"""
        try:
            # 重置累计偏移量
            self.cumulative_offset = [0.0, 0.0]
            self.offset_label.setText("偏移: (0.0, 0.0) mm")
            
            # 重新应用变换（只包含旋转，不包含位置偏移）
            if self.is_overlay_active and hasattr(self, 'transform_node') and self.transform_node:
                if self.current_rotation != 0:
                    # 有旋转时，重新应用旋转变换
                    self._apply_rotation_transform(self.current_rotation)
                else:
                    # 没有旋转时，直接使用基础矩阵
                    if self.base_transform_matrix is not None:
                        self.transform_node.SetMatrixTransformToParent(self.base_transform_matrix)
                
                # 刷新视图
                import slicer
                lm = slicer.app.layoutManager()
                red_widget = lm.sliceWidget('Red')
                if red_widget:
                    red_widget.sliceView().scheduleRender()
            
            logging.info("位置微调已重置")
            
        except Exception as e:
            logging.error(f"重置位置微调失败: {e}")

    def _on_opacity_changed(self, value: int):
        """透明度改变时的回调"""
        opacity = value / 100.0
        self.current_opacity = opacity
        self.opacity_value_label.setText(f"{value}%")
        
        # 如果叠加已激活，立即应用透明度变化
        if self.is_overlay_active:
            try:
                import slicer
                lm = slicer.app.layoutManager()
                red_widget = lm.sliceWidget('Red')
                if red_widget:
                    comp_node = red_widget.mrmlSliceCompositeNode()
                    comp_node.SetForegroundOpacity(opacity)
                    red_widget.sliceView().scheduleRender()
            except Exception as e:
                logging.error(f"应用透明度变化失败: {e}")
        
        # 发出信号
        self.opacityChanged.emit(opacity)
        
        # 调用回调函数
        for callback in self.opacity_callbacks:
            try:
                callback(opacity)
            except Exception as e:
                logging.error(f"执行透明度回调失败: {e}")
    
    def _on_rotation_changed(self, value: int):
        """旋转角度改变时的回调"""
        self.current_rotation = value
        self.rotation_value_label.setText(f"{value}°")
        
        # 如果叠加已激活，立即应用旋转变化
        if self.is_overlay_active and hasattr(self, 'transform_node') and self.transform_node:
            try:
                self._apply_rotation_transform(value)
            except Exception as e:
                logging.error(f"应用旋转变化失败: {e}")
        
        # 发出信号
        self.rotationChanged.emit(value)
        
        # 调用回调函数
        for callback in self.rotation_callbacks:
            try:
                callback(value)
            except Exception as e:
                logging.error(f"执行旋转回调失败: {e}")

    def _open_transforms_module(self):
        """打开Transforms模块进行微调"""
        try:
            import slicer
            
            # 切换到Transforms模块
            slicer.util.selectModule('Transforms')
            
            # 如果有变换节点，选择它
            if self.transform_node:
                slicer.mrmlScene.SetActiveID("vtkMRMLLinearTransformNode", self.transform_node.GetID())
            
            self.statusUpdated.emit("已打开Transforms模块进行微调")
            
        except Exception as e:
            logging.error(f"打开Transforms模块失败: {e}")
            self.statusUpdated.emit("打开Transforms模块失败")
    
    def _reset_overlay(self):
        """重置瓣膜叠加"""
        try:
            if self.is_overlay_active:
                self._disable_overlay()
            
            # 重置透明度
            self.current_opacity = 0.6
            self.opacity_slider.setValue(60)
            self.opacity_value_label.setText("60%")
            
            # 重置旋转
            self.current_rotation = 0
            self.rotation_slider.setValue(0)
            self.rotation_value_label.setText("0°")
            
            # 重置位置微调
            self.cumulative_offset = [0.0, 0.0]
            self.offset_label.setText("偏移: (0.0, 0.0) mm")
            
            # 删除变换节点
            import slicer
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', 'ValveToRedSlice')
            if transform_node:
                slicer.mrmlScene.RemoveNode(transform_node)
                self.transform_node = None
            
            self.statusUpdated.emit("瓣膜叠加已重置")
            
        except Exception as e:
            logging.error(f"重置瓣膜叠加失败: {e}")
            self.statusUpdated.emit(f"重置失败: {str(e)}")
    
    # 公共接口方法
    def add_overlay_callback(self, callback: Callable[[bool], None]):
        """添加叠加状态变化回调函数"""
        self.overlay_callbacks.append(callback)
    
    def add_opacity_callback(self, callback: Callable[[float], None]):
        """添加透明度变化回调函数"""
        self.opacity_callbacks.append(callback)
    
    def add_rotation_callback(self, callback: Callable[[int], None]):
        """添加旋转变化回调函数"""
        self.rotation_callbacks.append(callback)
    
    def get_overlay_status(self) -> bool:
        """获取当前叠加状态"""
        return self.is_overlay_active
    
    def get_current_opacity(self) -> float:
        """获取当前透明度"""
        return self.current_opacity
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        opacity = max(0.0, min(1.0, opacity))  # 限制范围[0,1]
        self.opacity_slider.setValue(int(opacity * 100))
    
    def get_current_rotation(self) -> int:
        """获取当前旋转角度"""
        return self.current_rotation
    
    def set_rotation(self, angle: int):
        """设置旋转角度"""
        angle = max(-180, min(180, angle))  # 限制范围[-180,180]
        self.rotation_slider.setValue(angle)
    
    def force_enable_overlay(self):
        """强制启用叠加（外部调用）"""
        if not self.is_overlay_active and self.valve_node:
            self._enable_overlay()
    
    def force_disable_overlay(self):
        """强制禁用叠加（外部调用）"""
        if self.is_overlay_active:
            self._disable_overlay()
    
    def refresh_valve_data(self):
        """刷新瓣膜数据检查（外部调用）"""
        self._check_valve_availability()
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
    
    def cleanup(self):
        """清理资源"""
        # 清理回调函数列表
        self.overlay_callbacks.clear()
        self.opacity_callbacks.clear()
        
        # 如果叠加处于激活状态，先禁用
        if self.is_overlay_active:
            try:
                self._disable_overlay()
            except Exception as e:
                logging.error(f"清理时禁用叠加失败: {e}")
        
        logging.info("ValveOverlayWidget 清理完成")


# 工厂函数，方便创建组件
def create_valve_overlay_widget(session: Optional[TAVRStudySession] = None, parent=None) -> ValveOverlayWidget:
    """
    创建瓣膜叠加组件的工厂函数
    
    Args:
        session: 会话对象
        parent: 父组件
        
    Returns:
        ValveOverlayWidget: 瓣膜叠加组件实例
    """
    return ValveOverlayWidget(session, parent)
