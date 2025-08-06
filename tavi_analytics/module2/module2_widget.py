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
        # 创建分组框 - 根据详细设计文档要求
        segmentation_group = qt.QGroupBox("分割工具 (Segmentation)")
        segmentation_group.setStyleSheet(StyleManager.get_card_style())
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
        segmentation_layout.addWidget(aortic_root_button)
        
        # 2. 开始瓣膜支架分割按钮 - 次要操作
        valve_stent_button = LayoutManager.create_button_with_style(
            text="开始瓣膜支架分割",
            button_type="secondary",
            size="default",
            min_height=40
        )
        valve_stent_button.setObjectName("valveStentSegmentationButton")
        segmentation_layout.addWidget(valve_stent_button)
        
        # 3. 验证分割结果按钮 - 轮廓按钮
        validate_button = LayoutManager.create_button_with_style(
            text="验证分割结果",
            button_type="outline",
            size="default",
            min_height=35
        )
        validate_button.setObjectName("validateSegmentationButton")
        segmentation_layout.addWidget(validate_button)
        
        layout.addWidget(segmentation_group)

    def _create_landmark_placement_section(self, layout):
        """创建解剖标志点定义区域"""
        # 创建分组框 - 根据详细设计文档要求
        landmark_group = qt.QGroupBox("解剖标志点定义 (Landmark Placement)")
        landmark_group.setStyleSheet(StyleManager.get_card_style())
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
        landmark_layout.addWidget(native_annulus_button)
        
        # 2. 定义原生连合按钮 - 次要操作
        native_commissure_button = LayoutManager.create_button_with_style(
            text="定义原生连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        native_commissure_button.setObjectName("defineNativeCommissureButton")
        landmark_layout.addWidget(native_commissure_button)
        
        # 3. 定义新连合按钮 - 次要操作
        neo_commissure_button = LayoutManager.create_button_with_style(
            text="定义新连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        neo_commissure_button.setObjectName("defineNeoCommissureButton")
        landmark_layout.addWidget(neo_commissure_button)
        
        # 4. 定义冠脉开口按钮 - 轮廓按钮
        coronary_ostia_button = LayoutManager.create_button_with_style(
            text="定义冠脉开口",
            button_type="outline",
            size="default",
            min_height=35
        )
        coronary_ostia_button.setObjectName("defineCoronaryOstiaButton")
        landmark_layout.addWidget(coronary_ostia_button)
        
        layout.addWidget(landmark_group)

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
