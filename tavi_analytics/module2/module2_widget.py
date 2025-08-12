"""
模块二界面组件
负责引导式分割与解剖标志点定义的用户界面
"""

import logging
import time
from typing import Optional
import qt
import slicer

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager
    from .module2_logic import Module2Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager
    from module2.module2_logic import Module2Logic


class Module2Widget(qt.QWidget):
    """
    模块二界面组件
    
    提供引导式分割与解剖标志点定义的用户界面，包括：
    - 分割工具界面
    - 标志点定义界面
    - 进度显示
    - 结果预览
    """

    def __init__(self, session: TAVRStudySession, logic: Optional[Module2Logic] = None, parent=None):
        """
        初始化模块二界面组件
        
        Args:
            session: TAVR研究会话对象
            logic: 模块二业务逻辑对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.logic = logic or Module2Logic()
        
        # 设置组件属性
        self.setObjectName("Module2Widget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("Module2Widget 初始化完成")

    def on_activated(self):
        """
        模块激活时的回调方法
        
        自动切换到舒张末期时相，为分割和标志点定义做准备
        """
        logging.info("模块二已激活，开始检查和切换期像")
        
        try:
            # 检查标记的期像状态
            self._check_marked_phases()
            
            # 尝试切换到舒张末期（默认分析期像）
            if self._auto_switch_to_end_diastole():
                logging.info("成功切换到舒张末期时相")
                self._update_status("已切换到舒张末期，准备开始分割...")
                # 设置舒张末期按钮为激活状态
                self._update_phase_button_states(active_phase='diastole')
            else:
                logging.warning("未能自动切换到舒张末期时相")
                self._update_status("请先在模块一中标记舒张末期时相")
                
        except Exception as e:
            logging.error(f"自动时相切换失败: {e}")
            self._update_status("时相切换失败，请检查时相标记")

    def _check_marked_phases(self):
        """
        检查已标记的期像状态
        
        检查模块一中标记的舒张末期和收缩末期状态
        """
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        end_systole_info = self.session.get_marked_phase('end_systole')
        
        # 记录期像标记状态
        diastole_marked = end_diastole_info is not None and end_diastole_info.get('frame_index') is not None
        systole_marked = end_systole_info is not None and end_systole_info.get('frame_index') is not None
        
        if diastole_marked and systole_marked:
            logging.info("✓ 舒张末期和收缩末期均已标记")
        elif diastole_marked:
            logging.info("✓ 舒张末期已标记，收缩末期未标记")
        elif systole_marked:
            logging.warning("⚠ 收缩末期已标记，但舒张末期未标记（建议先标记舒张末期）")
        else:
            logging.warning("⚠ 舒张末期和收缩末期均未标记")
        
        return {
            'end_diastole_marked': diastole_marked,
            'end_systole_marked': systole_marked,
            'end_diastole_info': end_diastole_info,
            'end_systole_info': end_systole_info
        }

    def _auto_switch_to_end_diastole(self) -> bool:
        """
        自动切换到舒张末期时相
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        # 1. 从session获取舒张末期时相信息
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        if not end_diastole_info:
            logging.info("未找到舒张末期标记，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        frame_index = end_diastole_info.get('frame_index')
        if frame_index is None:
            logging.info("舒张末期标记中缺少帧索引信息，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        # 2. 获取序列浏览器节点
        browser_node = self.session.get_sequence_browser_node()
        if not browser_node:
            logging.warning("未找到序列浏览器节点")
            return False
        
        # 3. 切换到指定帧
        try:
            browser_node.SetSelectedItemNumber(frame_index)
            logging.info(f"成功切换到帧 {frame_index} (舒张末期)")
            return True
        except Exception as e:
            logging.error(f"切换帧失败: {e}")
            return False

    def _update_status(self, message: str):
        """更新状态显示"""
        if hasattr(self, 'status_label'):
            self.status_label.text = message
            logging.info(f"状态更新: {message}")

    def _switch_to_end_systole(self):
        """
        切换到收缩末期
        
        用于在需要时切换到收缩末期进行分析
        """
        try:
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info:
                self._update_status("未找到收缩末期标记，请先在模块一中标记")
                return False
            
            frame_index = end_systole_info.get('frame_index')
            if frame_index is None:
                self._update_status("收缩末期标记中缺少帧索引信息")
                return False
            
            # 获取序列浏览器节点
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新状态显示
            phase_percent = end_systole_info.get('phase_percent', 0.0)
            self._update_status(f"已切换到收缩末期 (帧 {frame_index}, {phase_percent:.1f}%)")
            
            logging.info(f"成功切换到帧 {frame_index} (收缩末期)")
            return True
            
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            self._update_status("切换到收缩末期失败")
            return False

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        self._create_title_section(layout)
        
        # 添加全自动分析区域 (Auto Analysis)
        self._create_auto_analysis_section(layout)
        
        # 添加解剖标志点定义区域 (Landmark Placement)
        self._create_landmark_placement_section(layout)
        
        # 添加进度状态区域 (Progress Status)
        self._create_progress_section(layout)
        
        # 添加操作控制区域 (Operations)
        self._create_operations_section(layout)
        
        # 添加弹性空间
        layout.addStretch()

    def _create_title_section(self, layout):
        """创建标题区域"""
        title_label = qt.QLabel("模块二：全自动分析与解剖标志点定义")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title_label)
        
        # 添加描述
        description_label = qt.QLabel(
            "本模块提供一键全自动分析功能，自动完成主动脉根部分割和测量，\n"
            "以及关键解剖标志点的定义和管理工具。"
        )
        description_label.setAlignment(qt.Qt.AlignCenter)
        description_label.setStyleSheet(StyleManager.get_label_style("muted"))
        layout.addWidget(description_label)
        
        # 添加期像状态和控制区域
        self._create_phase_control_section(layout)

    def _create_phase_control_section(self, layout):
        """创建期像控制区域"""
        # 创建期像控制框架
        phase_frame = LayoutManager.create_section_frame("期像选择")
        phase_layout = qt.QVBoxLayout(phase_frame)
        
        # 期像切换按钮组
        switch_layout = qt.QHBoxLayout()
        switch_layout.setSpacing(8)
        
        # 切换到舒张末期按钮
        self.switch_to_diastole_button = LayoutManager.create_button_with_style(
            text="🫀 舒张末期",
            button_type="primary",
            size="small",
            min_height=32
        )
        self.switch_to_diastole_button.setObjectName("switchToDiastoleButton")
        self.switch_to_diastole_button.clicked.connect(self._on_switch_to_diastole)
        self.switch_to_diastole_button.setToolTip("切换到舒张末期进行分析（推荐用于HALT等分析）")
        switch_layout.addWidget(self.switch_to_diastole_button)
        
        # 切换到收缩末期按钮
        self.switch_to_systole_button = LayoutManager.create_button_with_style(
            text="💓 收缩末期",
            button_type="secondary",
            size="small",
            min_height=32
        )
        self.switch_to_systole_button.setObjectName("switchToSystoleButton")
        self.switch_to_systole_button.clicked.connect(self._on_switch_to_systole)
        self.switch_to_systole_button.setToolTip("切换到收缩末期进行分析（用于动态分析）")
        switch_layout.addWidget(self.switch_to_systole_button)
        
        phase_layout.addLayout(switch_layout)
        
        # 添加说明文本
        phase_info_label = qt.QLabel(
            "💡 提示：全自动分析默认使用舒张末期数据进行处理。\n"
            "请确保在模块一中已正确标记舒张末期，然后点击上方按钮切换。"
        )
        phase_info_label.setAlignment(qt.Qt.AlignCenter)
        phase_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                font-style: italic;
                padding: 4px;
                margin: 2px;
            }
        """)
        phase_info_label.setWordWrap(True)
        phase_layout.addWidget(phase_info_label)
        
        layout.addWidget(phase_frame)

    def _create_auto_analysis_section(self, layout):
        """创建全自动分析区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        analysis_group = LayoutManager.create_section_frame("全自动分析 (Auto Analysis)")
        analysis_layout = qt.QVBoxLayout(analysis_group)
        
        # 添加期像相关的分析提示
        phase_hint_label = qt.QLabel(
            "💡 分析提示：全自动分析将使用当前舒张末期的数据进行处理，\n"
            "包括主动脉根部分割、测量分析等，整个过程无需人工干预。"
        )
        phase_hint_label.setStyleSheet("""
            QLabel {
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                margin: 4px 0px;
            }
        """)
        phase_hint_label.setWordWrap(True)
        analysis_layout.addWidget(phase_hint_label)
        
        # 一键分析按钮 - 主要操作
        self.auto_analysis_button = LayoutManager.create_button_with_style(
            text="🚀 开始全自动分析",
            button_type="primary",
            size="large",
            min_height=50
        )
        self.auto_analysis_button.setObjectName("autoAnalysisButton")
        self.auto_analysis_button.clicked.connect(self._on_start_auto_analysis)
        analysis_layout.addWidget(self.auto_analysis_button)
        
        # 分析状态显示
        self.analysis_status_label = qt.QLabel("准备开始全自动分析...")
        self.analysis_status_label.setAlignment(qt.Qt.AlignCenter)
        self.analysis_status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                margin: 4px 0px;
            }
        """)
        self.analysis_status_label.setWordWrap(True)
        analysis_layout.addWidget(self.analysis_status_label)
        
        # 停止分析按钮 - 危险操作，初始隐藏
        self.stop_analysis_button = LayoutManager.create_button_with_style(
            text="⏹ 停止分析",
            button_type="destructive",
            size="default",
            min_height=35
        )
        self.stop_analysis_button.setObjectName("stopAnalysisButton")
        self.stop_analysis_button.clicked.connect(self._on_stop_analysis)
        self.stop_analysis_button.setVisible(False)  # 初始隐藏
        analysis_layout.addWidget(self.stop_analysis_button)
        
        layout.addWidget(analysis_group)

    def _create_landmark_placement_section(self, layout):
        """创建解剖标志点定义区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        landmark_group = LayoutManager.create_section_frame("解剖标志点定义 (Landmark Placement)")
        landmark_layout = qt.QVBoxLayout(landmark_group)
        
        # 添加实时操作提示组件
        self._create_landmark_instruction_panel(landmark_layout)
        
        # 按照详细设计文档和开发计划任务3的要求，添加四个标志点定义按钮
        # 使用推荐的LayoutManager.create_button_with_style()方法创建按钮
        
        # 1. 定义原生瓣环按钮 - 主要操作，连接到第12个任务实现的逻辑方法
        self.native_annulus_button = LayoutManager.create_button_with_style(
            text="定义原生瓣环",
            button_type="primary",
            size="default",
            min_height=40
        )
        self.native_annulus_button.setObjectName("defineNativeAnnulusButton")
        self.native_annulus_button.clicked.connect(self._on_define_native_annulus)
        landmark_layout.addWidget(self.native_annulus_button)
        
        # 2. 定义原生连合按钮 - 次要操作
        self.native_commissure_button = LayoutManager.create_button_with_style(
            text="定义原生连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        self.native_commissure_button.setObjectName("defineNativeCommissureButton")
        self.native_commissure_button.clicked.connect(self._on_define_native_commissure)
        landmark_layout.addWidget(self.native_commissure_button)
        
        # 3. 定义新连合按钮 - 次要操作
        self.neo_commissure_button = LayoutManager.create_button_with_style(
            text="定义新连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        self.neo_commissure_button.setObjectName("defineNeoCommissureButton")
        self.neo_commissure_button.clicked.connect(self._on_define_neo_commissure)
        landmark_layout.addWidget(self.neo_commissure_button)
        
        # 4. 定义冠脉开口按钮 - 轮廓按钮
        coronary_ostia_button = LayoutManager.create_button_with_style(
            text="定义冠脉开口",
            button_type="outline",
            size="default",
            min_height=35
        )
        coronary_ostia_button.setObjectName("defineCoronaryOstiaButton")
        coronary_ostia_button.clicked.connect(lambda: self._on_button_clicked("定义冠脉开口"))
        landmark_layout.addWidget(coronary_ostia_button)
        
        layout.addWidget(landmark_group)

    def _create_progress_section(self, layout):
        """创建进度状态区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        progress_group = LayoutManager.create_section_frame("进度状态")
        progress_layout = qt.QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(StyleManager.get_input_style())
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态文本标签
        self.status_label = qt.QLabel("准备开始分割...")
        self.status_label.setAlignment(qt.Qt.AlignCenter)
        self.status_label.setStyleSheet(StyleManager.get_label_style("muted"))
        self.status_label.setMinimumHeight(30)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)

    def _create_operations_section(self, layout):
        """创建操作控制区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        operations_group = LayoutManager.create_section_frame("操作")
        operations_layout = qt.QHBoxLayout(operations_group)
        
        # 重置按钮 - 使用destructive样式表示危险操作
        reset_button = LayoutManager.create_button_with_style(
            text="重置",
            button_type="destructive",
            size="default",
            min_height=40
        )
        reset_button.setObjectName("resetModuleButton")
        reset_button.clicked.connect(lambda: self._on_button_clicked("重置"))
        operations_layout.addWidget(reset_button)
        
        # 完成模块按钮 - 使用primary样式表示主要操作
        complete_button = LayoutManager.create_button_with_style(
            text="完成模块",
            button_type="primary",
            size="default",
            min_height=40
        )
        complete_button.setObjectName("completeModuleButton")
        complete_button.clicked.connect(lambda: self._on_button_clicked("完成模块"))
        operations_layout.addWidget(complete_button)
        
        layout.addWidget(operations_group)

    def _create_landmark_instruction_panel(self, layout):
        """
        创建实时操作提示面板
        
        提供动态的用户操作指导和状态反馈
        """
        # 创建指令面板容器
        instruction_frame = qt.QFrame()
        instruction_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        instruction_layout = qt.QVBoxLayout(instruction_frame)
        instruction_layout.setSpacing(8)
        instruction_layout.setContentsMargins(12, 12, 12, 12)
        
        # 添加指令标题
        instruction_title = qt.QLabel("📍 操作指导")
        instruction_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #495057;
                font-size: 14px;
                margin-bottom: 4px;
            }
        """)
        instruction_layout.addWidget(instruction_title)
        
        # 添加动态指令文本
        self.instruction_label = qt.QLabel("请选择要定义的解剖标志点类型")
        self.instruction_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 13px;
                line-height: 18px;
                margin: 0px;
            }
        """)
        self.instruction_label.setWordWrap(True)
        instruction_layout.addWidget(self.instruction_label)
        
        # 添加进度状态指示器
        self.landmark_progress_label = qt.QLabel("等待用户操作...")
        self.landmark_progress_label.setStyleSheet("""
            QLabel {
                color: #007bff;
                font-size: 12px;
                font-style: italic;
                margin-top: 4px;
            }
        """)
        instruction_layout.addWidget(self.landmark_progress_label)
        
        # 添加嵌入式标志点控制面板
        self._create_embedded_markups_controls(instruction_layout)
        
        layout.addWidget(instruction_frame)

    def _create_embedded_markups_controls(self, layout):
        """
        创建嵌入式标志点控制面板
        
        在当前模块中直接提供markups相关的控制功能，无需跳转模块
        """
        # 创建控制按钮面板
        controls_frame = qt.QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 8px;
                padding: 8px;
            }
        """)
        controls_layout = qt.QHBoxLayout(controls_frame)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        
        # 标志点操作按钮
        self.place_mode_button = qt.QPushButton("🎯 放置模式")
        self.place_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.place_mode_button.clicked.connect(self._on_toggle_place_mode)
        self.place_mode_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.place_mode_button)
        
        # 删除最后一个点
        self.delete_last_button = qt.QPushButton("↶ 撤销")
        self.delete_last_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        self.delete_last_button.clicked.connect(self._on_delete_last_point)
        self.delete_last_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.delete_last_button)
        
        # 清除所有点
        self.clear_points_button = qt.QPushButton("🗑️ 清除")
        self.clear_points_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.clear_points_button.clicked.connect(self._on_clear_all_points)
        self.clear_points_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.clear_points_button)
        
        # 添加弹性空间
        controls_layout.addStretch()
        
        layout.addWidget(controls_frame)
        
        # 保存控制面板引用
        self.markups_controls_frame = controls_frame

    def _on_define_native_annulus(self):
        """
        处理定义原生瓣环按钮点击事件
        
        连接到第12个任务实现的平面重建算法
        """
        logging.info("用户点击了'定义原生瓣环'按钮")
        
        try:
            # 确保在舒张末期进行瓣环定义（更准确）
            if not self._ensure_diastolic_phase():
                self._update_instruction("❌ 请先确保已切换到舒张末期时相")
                self._update_landmark_progress("⚠️ 需要舒张末期时相")
                return
            
            # 更新UI状态
            self._update_instruction("正在创建原生瓣环标志点节点...")
            self._update_landmark_progress("⏳ 初始化中...")
            
            # 禁用按钮，防止重复点击
            self.native_annulus_button.setEnabled(False)
            self.native_annulus_button.setText("正在初始化...")
            
            # 调用逻辑层的平面重建方法
            result = self.logic.reconstruct_native_annulus_plane()
            
            if result:
                self._update_instruction(
                    "✅ 标志点节点已创建！（舒张末期）\n"
                    "请在3D视图中依次放置3个原生瓣环上的点：\n"
                    "1️⃣ 第一个点：右冠状动脉小叶对应的瓣环点\n"
                    "2️⃣ 第二个点：左冠状动脉小叶对应的瓣环点\n" 
                    "3️⃣ 第三个点：无冠状动脉小叶对应的瓣环点"
                )
                self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
                
                # 显示嵌入式标志点控制面板
                self._show_markups_controls()
                
                # 启动定时器监控标志点放置进度
                self._start_landmark_monitoring()
                
                # 更新状态栏
                self._update_status("Native_Annulus_Points节点已激活（舒张末期），请开始放置标志点")
                
                logging.info("原生瓣环平面重建流程已启动")
                
            else:
                self._update_instruction("❌ 标志点节点创建失败，请重试")
                self._update_landmark_progress("❌ 创建失败")
                self._enable_native_annulus_button()
                self._update_status("原生瓣环标志点创建失败")
                logging.error("原生瓣环平面重建流程启动失败")
                
        except Exception as e:
            logging.error(f"定义原生瓣环失败: {e}")
            self._update_instruction(f"❌ 发生错误: {str(e)}")
            self._update_landmark_progress("❌ 操作失败")
            self._enable_native_annulus_button()
            self._update_status("原生瓣环定义失败，请检查日志")

    def _ensure_diastolic_phase(self) -> bool:
        """
        确保当前处于舒张末期
        
        如果当前不在舒张末期，尝试自动切换
        
        Returns:
            bool: 是否成功确保在舒张末期
        """
        try:
            # 检查当前是否已经在舒张末期
            end_diastole_info = self.session.get_marked_phase('end_diastole')
            if not end_diastole_info:
                logging.warning("未找到舒张末期标记")
                return False
                
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("未找到序列浏览器节点")
                return False
                
            current_frame = browser_node.GetSelectedItemNumber()
            diastole_frame = end_diastole_info.get('frame_index')
            
            if current_frame == diastole_frame:
                # 已经在舒张末期
                return True
            else:
                # 需要切换到舒张末期
                logging.info(f"当前帧 {current_frame}，需要切换到舒张末期帧 {diastole_frame}")
                return self._auto_switch_to_end_diastole()
                
        except Exception as e:
            logging.error(f"检查/切换舒张末期失败: {e}")
            return False

    def _start_landmark_monitoring(self):
        """
        启动标志点放置监控
        
        定期检查用户放置的标志点数量，并在达到3个点时自动触发平面计算
        """
        # 创建定时器
        self.landmark_timer = qt.QTimer()
        self.landmark_timer.timeout.connect(self._check_landmark_progress)
        self.landmark_timer.start(1000)  # 每秒检查一次
        
        logging.info("标志点监控定时器已启动")

    def _check_landmark_progress(self):
        """
        检查标志点放置进度
        
        监控用户在3D视图中放置的标志点数量，并提供实时反馈
        """
        try:
            # 获取状态信息
            status = self.logic.get_native_annulus_plane_status()
            
            if not status['node_exists']:
                # 节点不存在，停止监控
                self._stop_landmark_monitoring()
                self._enable_native_annulus_button()
                return
            
            points_placed = status['points_placed']
            points_needed = status['points_needed']
            
            # 更新进度显示
            if points_placed == 0:
                self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
            elif points_placed == 1:
                self._update_landmark_progress("📍 已放置1个点，还需要2个点 (1/3)")
                self._update_instruction(
                    "✅ 第一个点已放置！\n"
                    "请继续放置第二个瓣环点（左冠状动脉小叶对应位置）"
                )
            elif points_placed == 2:
                self._update_landmark_progress("📍 已放置2个点，还需要1个点 (2/3)")
                self._update_instruction(
                    "✅ 前两个点已放置！\n"
                    "请放置第三个瓣环点（无冠状动脉小叶对应位置）"
                )
            elif points_placed >= 3:
                # 检查是否已经计算了平面
                if status['plane_computed']:
                    # 平面已计算完成
                    self._on_plane_calculation_completed()
                elif status['ready_to_compute']:
                    # 可以计算平面
                    self._trigger_plane_calculation()
                
        except Exception as e:
            logging.error(f"检查标志点进度失败: {e}")

    def _trigger_plane_calculation(self):
        """
        触发平面计算
        
        当用户放置了3个点后，自动触发平面计算
        """
        logging.info("触发平面计算...")
        
        try:
            self._update_landmark_progress("🔄 正在计算平面...")
            self._update_instruction("⏳ 正在计算最佳拟合平面，请稍候...")
            
            # 调用平面计算
            result = self.logic.check_and_compute_plane_if_ready("Native_Annulus_Points")
            
            if result:
                logging.info("平面计算成功")
                # 计算完成的处理在 _on_plane_calculation_completed 中进行
            else:
                logging.error("平面计算失败")
                self._update_instruction("❌ 平面计算失败，请检查标志点位置")
                self._update_landmark_progress("❌ 计算失败")
                self._stop_landmark_monitoring()
                self._enable_native_annulus_button()
                
        except Exception as e:
            logging.error(f"平面计算触发失败: {e}")
            self._update_instruction(f"❌ 平面计算失败: {str(e)}")
            self._update_landmark_progress("❌ 计算错误")
            self._stop_landmark_monitoring()
            self._enable_native_annulus_button()

    def _on_plane_calculation_completed(self):
        """
        平面计算完成的处理
        
        显示计算结果并提供下一步操作指导
        """
        logging.info("平面计算完成")
        
        try:
            # 停止监控
            self._stop_landmark_monitoring()
            
            # 获取计算结果
            plane_data = self.session.get_reconstructed_plane("native_annulus")
            
            if plane_data:
                # 显示成功信息
                origin = plane_data['origin']
                normal = plane_data['normal']
                
                self._update_instruction(
                    "🎉 原生瓣环平面重建完成！\n"
                    f"平面原点: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})\n"
                    f"法向量: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})\n"
                    "您可以继续定义其他解剖标志点。"
                )
                self._update_landmark_progress("✅ 平面重建完成")
                self._update_status("原生瓣环平面重建成功完成")
                
                # 刷新视图并对准新创建的平面Model
                self._refresh_3d_view()
                self._center_view_on_model("Native_Annulus_Plane")
                
                # 重新启用按钮，允许重新定义
                self._enable_native_annulus_button()
                
                # 隐藏嵌入式控制面板
                self._hide_markups_controls()
                
                # 刷新3D视图以显示新创建的平面
                self._refresh_3d_view()
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(25)  # 假设原生瓣环完成后进度为25%
                
                logging.info("原生瓣环平面重建流程完成")
                
            else:
                self._update_instruction("❌ 未能获取平面计算结果")
                self._update_landmark_progress("❌ 结果获取失败")
                self._enable_native_annulus_button()
                
        except Exception as e:
            logging.error(f"平面计算完成处理失败: {e}")
            self._update_instruction(f"❌ 处理结果时发生错误: {str(e)}")
            self._update_landmark_progress("❌ 处理失败")
            self._enable_native_annulus_button()

    def _on_define_native_commissure(self):
        """
        处理定义原生连合按钮点击事件
        
        启动原生连合标志点定义流程
        """
        logging.info("用户点击了'定义原生连合'按钮")
        
        try:
            # 更新UI状态
            self._update_instruction("正在创建原生连合标志点节点...")
            self._update_landmark_progress("⏳ 初始化连合定义...")
            
            # 禁用按钮，防止重复点击
            self.native_commissure_button.setEnabled(False)
            self.native_commissure_button.setText("正在初始化...")
            
            # 调用逻辑层的连合定义方法
            result = self.logic.define_native_commissure_points()
            
            if result:
                self._update_instruction(
                    "✅ 原生连合标志点节点已创建！\n"
                    "请在3D视图中依次放置3个原生连合点：\n"
                    "1️⃣ 第一个点：右冠-左冠连合位置\n"
                    "2️⃣ 第二个点：左冠-无冠连合位置\n" 
                    "3️⃣ 第三个点：无冠-右冠连合位置"
                )
                self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
                
                # 显示嵌入式标志点控制面板
                self._show_markups_controls()
                
                # 启动定时器监控连合点放置进度
                self._start_commissure_monitoring()
                
                # 更新状态栏
                self._update_status("Native_Commissure_Points节点已激活，请开始放置连合点")
                
                logging.info("原生连合定义流程已启动")
                
            else:
                self._update_instruction("❌ 连合标志点节点创建失败，请重试")
                self._update_landmark_progress("❌ 创建失败")
                self._enable_native_commissure_button()
                self._update_status("原生连合标志点创建失败")
                logging.error("原生连合定义流程启动失败")
                
        except Exception as e:
            logging.error(f"定义原生连合失败: {e}")
            self._update_instruction(f"❌ 发生错误: {str(e)}")
            self._update_landmark_progress("❌ 操作失败")
            self._enable_native_commissure_button()
            self._update_status("原生连合定义失败，请检查日志")

    def _on_define_neo_commissure(self):
        """
        处理定义新连合按钮点击事件
        
        启动新连合标志点定义流程
        """
        logging.info("用户点击了'定义新连合'按钮")
        
        try:
            # 更新UI状态
            self._update_instruction("正在创建新连合标志点节点...")
            self._update_landmark_progress("⏳ 初始化新连合定义...")
            
            # 禁用按钮，防止重复点击
            self.neo_commissure_button.setEnabled(False)
            self.neo_commissure_button.setText("正在初始化...")
            
            # 调用逻辑层的新连合定义方法
            result = self.logic.define_neo_commissure_points()
            
            if result:
                self._update_instruction(
                    "✅ 新连合标志点节点已创建！\n"
                    "请在3D视图中依次放置3个新连合点：\n"
                    "1️⃣ 第一个点：新右冠-左冠连合位置\n"
                    "2️⃣ 第二个点：新左冠-无冠连合位置\n" 
                    "3️⃣ 第三个点：新无冠-右冠连合位置"
                )
                self._update_landmark_progress("📍 请在3D视图中放置3个新连合点 (0/3)")
                
                # 启动监控
                self._start_neo_commissure_monitoring()
                
                # 更新状态栏
                self._update_status("Neo_Commissure_Points节点已激活，请开始放置新连合点")
                
                logging.info("新连合定义流程已启动")
                
            else:
                self._update_instruction("❌ 新连合标志点节点创建失败，请重试")
                self._update_landmark_progress("❌ 创建失败")
                self._enable_neo_commissure_button()
                self._update_status("新连合标志点创建失败")
                logging.error("新连合定义流程启动失败")
                
        except Exception as e:
            logging.error(f"定义新连合失败: {e}")
            self._update_instruction(f"❌ 发生错误: {str(e)}")
            self._update_landmark_progress("❌ 操作失败")
            self._enable_neo_commissure_button()
            self._update_status("新连合定义失败，请检查日志")

    def _start_commissure_monitoring(self):
        """
        启动连合点放置监控
        
        定期检查用户放置的连合点数量，并在达到3个点时自动处理
        """
        # 创建定时器（如果还没有的话）
        if not hasattr(self, 'commissure_timer'):
            self.commissure_timer = qt.QTimer()
            self.commissure_timer.timeout.connect(self._check_commissure_progress)
        
        self.commissure_timer.start(1000)  # 每秒检查一次
        
        logging.info("连合点监控定时器已启动")

    def _check_commissure_progress(self):
        """
        检查连合点放置进度
        
        监控用户在3D视图中放置的连合点数量，并提供实时反馈
        """
        try:
            # 获取状态信息
            status = self.logic.get_native_commissure_status()
            
            if not status['node_exists']:
                # 节点不存在，停止监控
                self._stop_commissure_monitoring()
                self._enable_native_commissure_button()
                return
            
            points_placed = status['points_placed']
            points_needed = status['points_needed']
            
            # 更新进度显示
            if points_placed == 0:
                self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
            elif points_placed == 1:
                self._update_landmark_progress("📍 已放置1个连合点，还需要2个点 (1/3)")
                self._update_instruction(
                    "✅ 第一个连合点已放置！\n"
                    "请继续放置第二个连合点（左冠-无冠连合位置）"
                )
            elif points_placed == 2:
                self._update_landmark_progress("📍 已放置2个连合点，还需要1个点 (2/3)")
                self._update_instruction(
                    "✅ 前两个连合点已放置！\n"
                    "请放置第三个连合点（无冠-右冠连合位置）"
                )
            elif points_placed >= 3:
                # 检查是否已经完成定义
                if status['points_complete']:
                    self._on_commissure_definition_completed()
                
        except Exception as e:
            logging.error(f"检查连合点进度失败: {e}")

    def _on_commissure_definition_completed(self):
        """
        连合点定义完成的处理
        
        显示完成结果并提供后续操作指导
        """
        logging.info("连合点定义完成")
        
        try:
            # 停止监控
            self._stop_commissure_monitoring()
            
            # 获取连合点信息
            landmark_node = self.session.get_landmark_node("Native_Commissure_Points")
            
            if landmark_node:
                # 显示成功信息
                self._update_instruction(
                    "🎉 原生连合点定义完成！\n"
                    "✅ 已自动命名3个连合点：\n"
                    "• RCC_LCC: 右冠-左冠连合\n"
                    "• LCC_NCC: 左冠-无冠连合\n"
                    "• NCC_RCC: 无冠-右冠连合\n"
                    "您可以继续定义其他解剖标志点。"
                )
                self._update_landmark_progress("✅ 连合点定义完成")
                self._update_status("原生连合点定义成功完成")
                
                # 刷新视图
                self._refresh_3d_view()
                self._center_view_on_markups("Native_Commissure_Points")
                
                # 重新启用按钮，允许重新定义
                self._enable_native_commissure_button()
                
                # 隐藏嵌入式控制面板
                self._hide_markups_controls()
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(50)  # 假设连合点完成后进度为50%
                
                logging.info("原生连合点定义流程完成")
                
            else:
                self._update_instruction("❌ 未能获取连合点信息")
                self._update_landmark_progress("❌ 获取信息失败")
                self._enable_native_commissure_button()
                
        except Exception as e:
            logging.error(f"连合定义完成处理失败: {e}")
            self._update_instruction(f"❌ 处理结果时发生错误: {str(e)}")
            self._update_landmark_progress("❌ 处理失败")
            self._enable_native_commissure_button()

    def _stop_commissure_monitoring(self):
        """停止连合点监控定时器"""
        if hasattr(self, 'commissure_timer') and self.commissure_timer:
            self.commissure_timer.stop()
            self.commissure_timer = None
            logging.info("连合点监控定时器已停止")
        
        # 同时隐藏控制面板
        self._hide_markups_controls()

    def _enable_native_commissure_button(self):
        """重新启用原生连合按钮"""
        if hasattr(self, 'native_commissure_button'):
            self.native_commissure_button.setEnabled(True)
            self.native_commissure_button.setText("定义原生连合")

    def _start_neo_commissure_monitoring(self):
        """
        启动新连合点放置监控
        
        定期检查用户放置的新连合点数量，并在达到3个点时自动处理
        """
        # 创建定时器（如果还没有的话）
        if not hasattr(self, 'neo_commissure_timer'):
            self.neo_commissure_timer = qt.QTimer()
            self.neo_commissure_timer.timeout.connect(self._check_neo_commissure_progress)
        
        # 启动定时器，每500ms检查一次
        self.neo_commissure_timer.start(500)
        logging.info("新连合点监控定时器已启动")
        
        # 显示控制面板
        self._show_markups_controls()

    def _check_neo_commissure_progress(self):
        """
        检查新连合点放置进度
        
        定期调用，监控用户的新连合点放置进度
        """
        try:
            # 获取新连合状态
            status = self.logic.get_neo_commissure_status()
            
            if not status['node_exists']:
                # 节点不存在，停止监控
                self._stop_neo_commissure_monitoring()
                return
                
            points_placed = status['points_placed']
            points_needed = status['points_needed']
            
            # 更新进度显示
            progress_text = f"📍 请在3D视图中放置3个新连合点 ({points_placed}/{points_needed})"
            
            if points_placed < points_needed:
                progress_text += f"\n当前需要放置第 {points_placed + 1} 个新连合点"
                self._update_landmark_progress(progress_text)
            elif points_placed >= points_needed and not status['points_complete']:
                # 达到所需数量但还未完成
                self._update_landmark_progress("⏳ 正在处理新连合点...")
            elif status['points_complete']:
                # 新连合点已完成
                self._on_neo_commissure_definition_completed()
                
        except Exception as e:
            logging.error(f"检查新连合进度失败: {e}")

    def _on_neo_commissure_definition_completed(self):
        """
        新连合定义完成的回调
        
        当检测到新连合点定义已完成时调用
        """
        try:
            logging.info("新连合点定义已完成，开始处理结果")
            
            # 停止监控
            self._stop_neo_commissure_monitoring()
            
            # 获取新连合点信息
            landmark_node = self.session.get_landmark_node("Neo_Commissure_Points")
            
            if landmark_node:
                # 显示成功信息
                self._update_instruction(
                    "🎉 新连合点定义完成！\n"
                    "✅ 已自动命名3个新连合点：\n"
                    "• Neo_RCC_LCC: 新右冠-左冠连合\n"
                    "• Neo_LCC_NCC: 新左冠-无冠连合\n"
                    "• Neo_NCC_RCC: 新无冠-右冠连合\n"
                    "您可以继续定义其他解剖标志点。"
                )
                self._update_landmark_progress("✅ 新连合点定义完成")
                self._update_status("新连合点定义成功完成")
                
                # 刷新视图
                self._refresh_3d_view()
                self._center_view_on_markups("Neo_Commissure_Points")
                
                # 重新启用按钮
                self._enable_neo_commissure_button()
                
                logging.info("新连合定义完成处理成功")
            else:
                logging.error("无法获取新连合点节点")
                self._update_instruction("❌ 无法获取新连合点信息")
                self._update_landmark_progress("❌ 处理失败")
                self._enable_neo_commissure_button()
                
        except Exception as e:
            logging.error(f"新连合定义完成处理失败: {e}")
            self._update_instruction(f"❌ 处理结果时发生错误: {str(e)}")
            self._update_landmark_progress("❌ 处理失败")
            self._enable_neo_commissure_button()

    def _stop_neo_commissure_monitoring(self):
        """停止新连合点监控定时器"""
        if hasattr(self, 'neo_commissure_timer') and self.neo_commissure_timer:
            self.neo_commissure_timer.stop()
            self.neo_commissure_timer = None
            logging.info("新连合点监控定时器已停止")
        
        # 同时隐藏控制面板
        self._hide_markups_controls()

    def _enable_neo_commissure_button(self):
        """重新启用新连合按钮"""
        if hasattr(self, 'neo_commissure_button'):
            self.neo_commissure_button.setEnabled(True)
            self.neo_commissure_button.setText("定义新连合")

    def _stop_landmark_monitoring(self):
        """停止标志点监控定时器"""
        if hasattr(self, 'landmark_timer') and self.landmark_timer:
            self.landmark_timer.stop()
            self.landmark_timer = None
            logging.info("标志点监控定时器已停止")
        
        # 同时隐藏控制面板
        self._hide_markups_controls()



    def _enable_native_annulus_button(self):
        """重新启用原生瓣环按钮"""
        if hasattr(self, 'native_annulus_button'):
            self.native_annulus_button.setEnabled(True)
            self.native_annulus_button.setText("定义原生瓣环")

    def _update_instruction(self, message: str):
        """更新操作指导文本"""
        if hasattr(self, 'instruction_label'):
            self.instruction_label.setText(message)
            logging.debug(f"指导更新: {message}")

    def _update_landmark_progress(self, message: str):
        """更新标志点进度状态"""
        if hasattr(self, 'landmark_progress_label'):
            self.landmark_progress_label.setText(message)
            logging.debug(f"进度更新: {message}")

    def _show_markups_controls(self):
        """显示嵌入式标志点控制面板"""
        if hasattr(self, 'place_mode_button'):
            self.place_mode_button.setVisible(True)
        if hasattr(self, 'delete_last_button'):
            self.delete_last_button.setVisible(True)
        if hasattr(self, 'clear_points_button'):
            self.clear_points_button.setVisible(True)
        logging.info("标志点控制面板已显示")

    def _hide_markups_controls(self):
        """隐藏嵌入式标志点控制面板"""
        if hasattr(self, 'place_mode_button'):
            self.place_mode_button.setVisible(False)
        if hasattr(self, 'delete_last_button'):
            self.delete_last_button.setVisible(False)
        if hasattr(self, 'clear_points_button'):
            self.clear_points_button.setVisible(False)
        logging.info("标志点控制面板已隐藏")

    def _on_toggle_place_mode(self):
        """切换标志点放置模式"""
        try:
            interaction_node = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interaction_node:
                current_mode = interaction_node.GetCurrentInteractionMode()
                if current_mode == interaction_node.Place:
                    # 当前是放置模式，切换到查看模式
                    interaction_node.SetCurrentInteractionMode(interaction_node.ViewTransform)
                    self.place_mode_button.setText("🎯 放置模式")
                    # 设置为灰色（查看模式）
                    self.place_mode_button.setStyleSheet("""
                        QPushButton {
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 11px;
                            min-width: 80px;
                        }
                        QPushButton:hover {
                            background-color: #5a6268;
                        }
                        QPushButton:pressed {
                            background-color: #545b62;
                        }
                    """)
                    logging.info("切换到查看模式")
                else:
                    # 当前不是放置模式，切换到放置模式
                    interaction_node.SetCurrentInteractionMode(interaction_node.Place)
                    self.place_mode_button.setText("👁️ 查看模式")
                    # 设置为绿色（放置模式）
                    self.place_mode_button.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 11px;
                            min-width: 80px;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                        QPushButton:pressed {
                            background-color: #1e7e34;
                        }
                    """)
                    logging.info("切换到放置模式")
        except Exception as e:
            logging.error(f"切换放置模式失败: {e}")

    def _on_delete_last_point(self):
        """删除最后放置的标志点"""
        try:
            # 确定当前活动的标志点节点
            active_landmark_node = None
            active_node_name = ""
            
            # 检查瓣环点
            annulus_node = self.session.get_landmark_node("Native_Annulus_Points")
            if annulus_node and hasattr(self, 'landmark_timer') and self.landmark_timer and self.landmark_timer.isActive():
                active_landmark_node = annulus_node
                active_node_name = "Native_Annulus_Points"
            
            # 检查连合点
            commissure_node = self.session.get_landmark_node("Native_Commissure_Points")
            if commissure_node and hasattr(self, 'commissure_timer') and self.commissure_timer and self.commissure_timer.isActive():
                active_landmark_node = commissure_node
                active_node_name = "Native_Commissure_Points"
            
            if active_landmark_node and active_landmark_node.GetNumberOfControlPoints() > 0:
                last_index = active_landmark_node.GetNumberOfControlPoints() - 1
                active_landmark_node.RemoveNthControlPoint(last_index)
                logging.info(f"删除了{active_node_name}的第 {last_index + 1} 个标志点")
                
                # 更新进度显示
                remaining_points = active_landmark_node.GetNumberOfControlPoints()
                if active_node_name == "Native_Annulus_Points":
                    self._update_landmark_progress(f"📍 已放置 {remaining_points} 个点，还需要 {3 - remaining_points} 个点 ({remaining_points}/3)")
                elif active_node_name == "Native_Commissure_Points":
                    self._update_landmark_progress(f"📍 已放置 {remaining_points} 个连合点，还需要 {3 - remaining_points} 个点 ({remaining_points}/3)")
                
            else:
                logging.warning("没有可删除的标志点或没有活动的标志点节点")
                
        except Exception as e:
            logging.error(f"删除标志点失败: {e}")

    def _on_clear_all_points(self):
        """清除所有标志点"""
        try:
            # 确定当前活动的标志点节点
            active_landmark_node = None
            active_node_name = ""
            
            # 检查瓣环点
            annulus_node = self.session.get_landmark_node("Native_Annulus_Points")
            if annulus_node and hasattr(self, 'landmark_timer') and self.landmark_timer and self.landmark_timer.isActive():
                active_landmark_node = annulus_node
                active_node_name = "Native_Annulus_Points"
            
            # 检查连合点
            commissure_node = self.session.get_landmark_node("Native_Commissure_Points")
            if commissure_node and hasattr(self, 'commissure_timer') and self.commissure_timer and self.commissure_timer.isActive():
                active_landmark_node = commissure_node
                active_node_name = "Native_Commissure_Points"
            
            if active_landmark_node:
                active_landmark_node.RemoveAllControlPoints()
                logging.info(f"清除了{active_node_name}的所有标志点")
                
                # 重置进度显示
                if active_node_name == "Native_Annulus_Points":
                    self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
                    self._update_instruction(
                        "🔄 已清除所有瓣环标志点\n"
                        "请重新在3D视图中依次放置3个原生瓣环上的点"
                    )
                elif active_node_name == "Native_Commissure_Points":
                    self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
                    self._update_instruction(
                        "🔄 已清除所有连合标志点\n"
                        "请重新在3D视图中依次放置3个原生连合点"
                    )
            else:
                logging.warning("未找到活动的标志点节点")
                
        except Exception as e:
            logging.error(f"清除标志点失败: {e}")

    def _on_switch_to_diastole(self):
        """处理切换到舒张末期按钮点击"""
        logging.info("用户要求切换到舒张末期")
        
        try:
            if self._auto_switch_to_end_diastole():
                # 更新按钮状态 - 舒张末期为激活状态
                self._update_phase_button_states(active_phase='diastole')
                self._update_status("已切换到舒张末期，适合进行HALT和分割分析")
                logging.info("手动切换到舒张末期成功")
            else:
                self._update_status("切换到舒张末期失败，请检查模块一中的期像标记")
                logging.warning("手动切换到舒张末期失败")
                
        except Exception as e:
            logging.error(f"手动切换到舒张末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")

    def _on_switch_to_systole(self):
        """处理切换到收缩末期按钮点击"""
        logging.info("用户要求切换到收缩末期")
        
        try:
            if self._switch_to_end_systole():
                # 更新按钮状态 - 收缩末期为激活状态
                self._update_phase_button_states(active_phase='systole')
                self._update_status("已切换到收缩末期，适合进行动态分析")
                logging.info("手动切换到收缩末期成功")
            else:
                self._update_status("切换到收缩末期失败，请检查模块一中的期像标记")
                logging.warning("手动切换到收缩末期失败")
                
        except Exception as e:
            logging.error(f"手动切换到收缩末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")

    def _on_start_auto_analysis(self):
        """
        处理开始全自动分析按钮点击事件
        
        执行一键全自动分析流程：
        1. 检查舒张末期是否已标记
        2. 检查服务器连接
        3. 获取当前舒张末期的nrrd文件
        4. 上传到远程分析服务器
        5. 监控分析状态
        6. 下载并导入分析结果
        """
        logging.info("用户点击了'开始全自动分析'按钮")
        
        try:
            # 确保在舒张末期进行分析
            if not self._ensure_diastolic_phase():
                self._update_analysis_status("❌ 请先确保已切换到舒张末期时相", "error")
                return
            
            # 更新UI状态
            self._update_analysis_status("🔍 正在检查分析条件和服务器连接...", "info")
            self._disable_analysis_button()
            
            # 调用逻辑层开始自动分析
            result = self.logic.start_auto_analysis()
            
            if result:
                self._update_analysis_status("📤 分析已启动，正在上传数据...", "processing")
                self._show_stop_button()
                
                # 启动状态监控定时器
                self._start_analysis_monitoring()
                
                logging.info("全自动分析流程已启动")
                
            else:
                self._update_analysis_status("❌ 分析启动失败，请检查数据和网络连接", "error")
                self._enable_analysis_button()
                logging.error("全自动分析流程启动失败")
                
        except Exception as e:
            logging.error(f"开始全自动分析失败: {e}")
            self._update_analysis_status(f"❌ 发生错误: {str(e)}", "error")
            self._enable_analysis_button()

    def _on_stop_analysis(self):
        """
        处理停止分析按钮点击事件
        """
        logging.info("用户要求停止分析")
        
        try:
            # 停止分析监控
            self._stop_analysis_monitoring()
            
            # 调用逻辑层停止分析
            self.logic.stop_auto_analysis()
            
            # 重置UI状态
            self._update_analysis_status("⏹ 分析已停止", "warning")
            self._enable_analysis_button()
            self._hide_stop_button()
            
            logging.info("分析已被用户停止")
            
        except Exception as e:
            logging.error(f"停止分析失败: {e}")
            self._update_analysis_status(f"❌ 停止分析时发生错误: {str(e)}", "error")

    def _start_analysis_monitoring(self):
        """
        启动分析状态监控
        
        定期检查远程分析的状态，并在完成时处理结果
        """
        # 创建定时器
        if not hasattr(self, 'analysis_timer'):
            self.analysis_timer = qt.QTimer()
            self.analysis_timer.timeout.connect(self._check_analysis_progress)
        
        self.analysis_timer.start(3000)  # 每3秒检查一次
        logging.info("分析状态监控定时器已启动")

    def _stop_analysis_monitoring(self):
        """停止分析状态监控定时器"""
        if hasattr(self, 'analysis_timer') and self.analysis_timer:
            self.analysis_timer.stop()
            self.analysis_timer = None
            logging.info("分析状态监控定时器已停止")

    def _check_analysis_progress(self):
        """
        检查分析进度
        
        定期调用，监控远程分析的进度并更新UI
        """
        try:
            # 获取分析状态
            status = self.logic.get_analysis_status()
            
            if not status:
                # 状态获取失败，停止监控
                self._stop_analysis_monitoring()
                self._update_analysis_status("❌ 无法获取分析状态，请检查网络连接", "error")
                self._enable_analysis_button()
                return
            
            analysis_status = status.get('status', 'unknown')
            progress = status.get('progress', 0)
            message = status.get('message', '')
            
            # 更新进度显示
            if analysis_status == 'uploading':
                self._update_analysis_status("📤 正在上传数据到分析服务器...", "processing")
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(progress)
            elif analysis_status == 'processing':
                if progress < 100:
                    # 启动阶段或远程处理阶段
                    if progress < 70:
                        self._update_analysis_status(f"⚙️ {message}", "processing")
                    else:
                        self._update_analysis_status(f"🔄 正在进行自动分析... ({min(progress-60, 40)}%)", "processing")
                else:
                    self._update_analysis_status("🔄 正在进行自动分析...", "processing")
                
                if hasattr(self, 'progress_bar'):
                    # 启动完成后，进度条显示远程分析进度
                    if progress >= 100:
                        # 启动完成，远程分析进行中，显示伪进度
                        current_time = time.time()
                        if not hasattr(self, 'remote_analysis_start_time'):
                            self.remote_analysis_start_time = current_time
                        
                        # 根据时间计算伪进度（假设分析需要2-5分钟）
                        elapsed = current_time - self.remote_analysis_start_time
                        fake_progress = min(20 + elapsed / 300 * 60, 85)  # 20%-85%之间
                        self.progress_bar.setValue(int(fake_progress))
                    else:
                        self.progress_bar.setValue(progress)
                        
            elif analysis_status == 'downloading':
                self._update_analysis_status("📥 正在下载分析结果...", "processing")
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(85)
            elif analysis_status == 'completed':
                # 分析完成
                self._on_analysis_completed()
            elif analysis_status == 'failed':
                # 分析失败
                error_msg = status.get('error', '未知错误')
                self._on_analysis_failed(error_msg)
            
            # 如果有额外消息，显示它
            if message and analysis_status in ['uploading', 'processing']:
                logging.info(f"分析状态更新: {message}")
                
        except Exception as e:
            logging.error(f"检查分析进度失败: {e}")
            self._stop_analysis_monitoring()
            self._update_analysis_status("❌ 监控分析进度时发生错误", "error")
            self._enable_analysis_button()

    def _on_analysis_completed(self):
        """
        分析完成的处理
        
        当远程分析完成时，下载结果并导入到Slicer中
        """
        logging.info("全自动分析已完成")
        
        try:
            # 停止监控
            self._stop_analysis_monitoring()
            
            # 更新状态
            self._update_analysis_status("🎉 分析完成！正在导入结果...", "success")
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(90)
            
            # 调用逻辑层导入结果
            import_result = self.logic.import_analysis_results()
            
            if import_result:
                # 显示导入成功信息
                imported_files = import_result.get('imported_files', [])
                curves_count = import_result.get('curves_count', 0)
                
                success_msg = (
                    f"✅ 全自动分析完成！\n"
                    f"• 已导入 {len(imported_files)} 个分析文件\n"
                    f"• 已创建 {curves_count} 条测量曲线\n"
                    f"您可以继续定义解剖标志点或查看分析结果。"
                )
                
                self._update_analysis_status(success_msg, "success")
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(100)
                
                # 重新启用分析按钮
                self._enable_analysis_button()
                self._hide_stop_button()
                
                logging.info("全自动分析结果导入成功")
                
            else:
                self._update_analysis_status("❌ 分析完成但结果导入失败", "error")
                self._enable_analysis_button()
                self._hide_stop_button()
                
        except Exception as e:
            logging.error(f"处理分析完成事件失败: {e}")
            self._update_analysis_status(f"❌ 处理分析结果时发生错误: {str(e)}", "error")
            self._enable_analysis_button()
            self._hide_stop_button()

    def _on_analysis_failed(self, error_message: str):
        """
        分析失败的处理
        
        Args:
            error_message: 错误信息
        """
        logging.error(f"全自动分析失败: {error_message}")
        
        try:
            # 停止监控
            self._stop_analysis_monitoring()
            
            # 显示失败信息
            self._update_analysis_status(f"❌ 分析失败: {error_message}", "error")
            
            # 重新启用分析按钮
            self._enable_analysis_button()
            self._hide_stop_button()
            
            # 重置进度条
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(0)
                
        except Exception as e:
            logging.error(f"处理分析失败事件失败: {e}")

    def _update_analysis_status(self, message: str, status_type: str = "info"):
        """
        更新分析状态显示
        
        Args:
            message: 状态消息
            status_type: 状态类型 ('info', 'processing', 'success', 'error', 'warning')
        """
        if hasattr(self, 'analysis_status_label'):
            self.analysis_status_label.setText(message)
            
            # 根据状态类型设置不同的样式
            if status_type == "error":
                style = """
                    QLabel {
                        background-color: #f8d7da;
                        color: #721c24;
                        border: 1px solid #f5c6cb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "success":
                style = """
                    QLabel {
                        background-color: #d4edda;
                        color: #155724;
                        border: 1px solid #c3e6cb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "processing":
                style = """
                    QLabel {
                        background-color: #d1ecf1;
                        color: #0c5460;
                        border: 1px solid #bee5eb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "warning":
                style = """
                    QLabel {
                        background-color: #fff3cd;
                        color: #856404;
                        border: 1px solid #ffeeba;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            else:  # info
                style = """
                    QLabel {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            
            self.analysis_status_label.setStyleSheet(style)
            logging.debug(f"分析状态更新: {message}")

    def _disable_analysis_button(self):
        """禁用分析按钮"""
        if hasattr(self, 'auto_analysis_button'):
            self.auto_analysis_button.setEnabled(False)
            self.auto_analysis_button.setText("⏳ 分析进行中...")

    def _enable_analysis_button(self):
        """重新启用分析按钮"""
        if hasattr(self, 'auto_analysis_button'):
            self.auto_analysis_button.setEnabled(True)
            self.auto_analysis_button.setText("🚀 开始全自动分析")

    def _show_stop_button(self):
        """显示停止分析按钮"""
        if hasattr(self, 'stop_analysis_button'):
            self.stop_analysis_button.setVisible(True)

    def _hide_stop_button(self):
        """隐藏停止分析按钮"""
        if hasattr(self, 'stop_analysis_button'):
            self.stop_analysis_button.setVisible(False)

    def _update_phase_button_states(self, active_phase: str):
        """
        更新期像切换按钮的状态
        
        Args:
            active_phase: 当前激活的期像 ('diastole' 或 'systole')
        """
        if active_phase == 'diastole':
            # 舒张末期激活
            if hasattr(self, 'switch_to_diastole_button'):
                self.switch_to_diastole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: 2px solid #1e7e34;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
            if hasattr(self, 'switch_to_systole_button'):
                # 恢复次要样式
                self.switch_to_systole_button.setStyleSheet("")  # 重置为默认次要样式
                
        elif active_phase == 'systole':
            # 收缩末期激活
            if hasattr(self, 'switch_to_systole_button'):
                self.switch_to_systole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 2px solid #bd2130;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
            if hasattr(self, 'switch_to_diastole_button'):
                # 恢复主要样式  
                self.switch_to_diastole_button.setStyleSheet("")  # 重置为默认主要样式

    def _refresh_3d_view(self):
        """
        刷新3D视图以显示新创建的markups
        """
        try:
            # 获取3D视图
            threeDWidget = slicer.app.layoutManager().threeDWidget(0)
            if threeDWidget:
                threeDView = threeDWidget.threeDView()
                threeDView.resetFocalPoint()
                
            # 强制渲染更新
            slicer.app.processEvents()
            
            # 确保markups模块的工具栏可见
            markupsToolBar = slicer.util.findChild(slicer.util.mainWindow(), 'MarkupsToolBar')
            if markupsToolBar:
                markupsToolBar.setVisible(True)
            
            logging.info("3D视图已刷新，markups可见")
            
        except Exception as e:
            logging.error(f"刷新3D视图失败: {e}")

    def _center_view_on_model(self, node_name: str):
        """将视图中心对准指定的Model节点"""
        try:
            node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if node and hasattr(node, 'GetPolyData'):
                polydata = node.GetPolyData()
                if polydata:
                    bounds = [0.0] * 6
                    polydata.GetBounds(bounds)
                    
                    # 计算中心点
                    center = [(bounds[0] + bounds[1])/2, 
                             (bounds[2] + bounds[3])/2, 
                             (bounds[4] + bounds[5])/2]
                    
                    # 设置3D视图的焦点
                    threeDWidget = slicer.app.layoutManager().threeDWidget(0)
                    if threeDWidget:
                        threeDView = threeDWidget.threeDView()
                        camera = threeDView.camera()
                        camera.SetFocalPoint(center)
                        camera.SetPosition(center[0], center[1] - 100, center[2] + 50)
                        camera.SetViewUp(0, 0, 1)
                        threeDView.forceRender()
                        
                    logging.info(f"视图已对准Model {node_name}")
                    
        except Exception as e:
            logging.error(f"对准Model视图失败: {e}")

    def _center_view_on_markups(self, node_name: str):
        """将视图中心对准指定的markups节点"""
        try:
            node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if node and hasattr(node, 'GetBounds'):
                bounds = [0.0] * 6
                node.GetBounds(bounds)
                
                # 计算中心点
                center = [(bounds[0] + bounds[1])/2, 
                         (bounds[2] + bounds[3])/2, 
                         (bounds[4] + bounds[5])/2]
                
                # 设置3D视图的焦点
                threeDWidget = slicer.app.layoutManager().threeDWidget(0)
                if threeDWidget:
                    threeDView = threeDWidget.threeDView()
                    camera = threeDView.camera()
                    camera.SetFocalPoint(center)
                    camera.SetPosition(center[0], center[1] - 100, center[2] + 50)
                    camera.SetViewUp(0, 0, 1)
                    threeDView.forceRender()
                    
                logging.info(f"视图已对准 {node_name}")
                
        except Exception as e:
            logging.error(f"对准视图失败: {e}")

    def _on_button_clicked(self, button_name: str):
        """
        通用按钮点击槽函数 - 任务5要求
        
        Args:
            button_name: 被点击按钮的名称
        """
        logging.info(f"{button_name} clicked")
        
        # 同时更新状态显示，提供用户反馈
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"用户点击了: {button_name}")

    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if self.logic:
            self.logic.session = session

    def on_deactivated(self):
        """模块停用时调用"""
        logging.info("模块二已停用")
        # 停止所有监控定时器
        self._stop_all_monitoring()

    def cleanup(self):
        """清理资源"""
        # 停止所有监控定时器
        self._stop_all_monitoring()
        
        # 清理逻辑层资源
        if self.logic:
            self.logic.cleanup()
        
        logging.info("模块二界面清理完成")

    def _stop_all_monitoring(self):
        """停止所有监控定时器"""
        # 停止瓣环监控
        self._stop_landmark_monitoring()
        
        # 停止连合点监控
        self._stop_commissure_monitoring()
        
        # 停止新连合点监控
        self._stop_neo_commissure_monitoring()
        
        # 停止分析监控
        self._stop_analysis_monitoring()
        
        logging.info("所有监控定时器已停止")
