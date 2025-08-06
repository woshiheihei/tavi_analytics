"""
模块二界面组件
负责引导式分割与解剖标志点定义的用户界面
"""

import logging
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
        logging.info("模块二已激活，开始自动时相切换")
        
        try:
            # 尝试切换到舒张末期
            if self._auto_switch_to_end_diastole():
                logging.info("成功切换到舒张末期时相")
                self._update_status("已切换到舒张末期，准备开始分割...")
            else:
                logging.warning("未能自动切换到舒张末期时相")
                self._update_status("请先在模块一中标记舒张末期时相")
                
        except Exception as e:
            logging.error(f"自动时相切换失败: {e}")
            self._update_status("时相切换失败，请检查时相标记")

    def _auto_switch_to_end_diastole(self) -> bool:
        """
        自动切换到舒张末期时相
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        # 1. 从session获取舒张末期时相信息
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        if not end_diastole_info:
            logging.warning("未找到舒张末期标记")
            return False
        
        frame_index = end_diastole_info.get('frame_index')
        if frame_index is None:
            logging.warning("舒张末期标记中缺少帧索引信息")
            return False
        
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

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        self._create_title_section(layout)
        
        # 添加分割工具区域 (Segmentation)
        self._create_segmentation_section(layout)
        
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
        title_label = qt.QLabel("模块二：引导式分割与解剖标志点定义")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title_label)
        
        # 添加描述
        description_label = qt.QLabel(
            "本模块提供主动脉根部和瓣膜支架的半自动分割功能，\n"
            "以及关键解剖标志点的定义和管理工具。"
        )
        description_label.setAlignment(qt.Qt.AlignCenter)
        description_label.setStyleSheet(StyleManager.get_label_style("muted"))
        layout.addWidget(description_label)

    def _create_segmentation_section(self, layout):
        """创建分割工具区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        segmentation_group = LayoutManager.create_section_frame("分割工具 (Segmentation)")
        segmentation_layout = qt.QVBoxLayout(segmentation_group)
        
        # 按照详细设计文档和开发计划任务2的要求，添加三个分割按钮
        # 使用推荐的LayoutManager.create_button_with_style()方法创建按钮
        
        # 1. 开始主动脉根部分割按钮 - 主要操作
        aortic_root_button = LayoutManager.create_button_with_style(
            text="开始主动脉根部分割",
            button_type="primary",
            size="default",
            min_height=40
        )
        aortic_root_button.setObjectName("aorticRootSegmentationButton")
        aortic_root_button.clicked.connect(lambda: self._on_button_clicked("开始主动脉根部分割"))
        segmentation_layout.addWidget(aortic_root_button)
        
        # 2. 开始瓣膜支架分割按钮 - 次要操作
        valve_stent_button = LayoutManager.create_button_with_style(
            text="开始瓣膜支架分割",
            button_type="secondary",
            size="default",
            min_height=40
        )
        valve_stent_button.setObjectName("valveStentSegmentationButton")
        valve_stent_button.clicked.connect(lambda: self._on_button_clicked("开始瓣膜支架分割"))
        segmentation_layout.addWidget(valve_stent_button)
        
        # 3. 验证分割结果按钮 - 轮廓按钮
        validate_button = LayoutManager.create_button_with_style(
            text="验证分割结果",
            button_type="outline",
            size="default",
            min_height=35
        )
        validate_button.setObjectName("validateSegmentationButton")
        validate_button.clicked.connect(lambda: self._on_button_clicked("验证分割结果"))
        segmentation_layout.addWidget(validate_button)
        
        layout.addWidget(segmentation_group)

    def _create_landmark_placement_section(self, layout):
        """创建解剖标志点定义区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        landmark_group = LayoutManager.create_section_frame("解剖标志点定义 (Landmark Placement)")
        landmark_layout = qt.QVBoxLayout(landmark_group)
        
        # 按照详细设计文档和开发计划任务3的要求，添加四个标志点定义按钮
        # 使用推荐的LayoutManager.create_button_with_style()方法创建按钮
        
        # 1. 定义原生瓣环按钮 - 主要操作
        native_annulus_button = LayoutManager.create_button_with_style(
            text="定义原生瓣环",
            button_type="primary",
            size="default",
            min_height=40
        )
        native_annulus_button.setObjectName("defineNativeAnnulusButton")
        native_annulus_button.clicked.connect(lambda: self._on_button_clicked("定义原生瓣环"))
        landmark_layout.addWidget(native_annulus_button)
        
        # 2. 定义原生连合按钮 - 次要操作
        native_commissure_button = LayoutManager.create_button_with_style(
            text="定义原生连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        native_commissure_button.setObjectName("defineNativeCommissureButton")
        native_commissure_button.clicked.connect(lambda: self._on_button_clicked("定义原生连合"))
        landmark_layout.addWidget(native_commissure_button)
        
        # 3. 定义新连合按钮 - 次要操作
        neo_commissure_button = LayoutManager.create_button_with_style(
            text="定义新连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        neo_commissure_button.setObjectName("defineNeoCommissureButton")
        neo_commissure_button.clicked.connect(lambda: self._on_button_clicked("定义新连合"))
        landmark_layout.addWidget(neo_commissure_button)
        
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

    def on_activated(self):
        """模块激活时调用"""
        logging.info("模块二已激活")

    def on_deactivated(self):
        """模块停用时调用"""
        logging.info("模块二已停用")

    def cleanup(self):
        """清理资源"""
        logging.info("模块二界面清理完成")
