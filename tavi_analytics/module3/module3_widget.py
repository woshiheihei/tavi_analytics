"""
模块三界面组件（骨架）

仅展示一个 Mock 标题，支持在主导航中切换到本页面。
"""
import logging
from typing import Optional
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from .module3_logic import Module3Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from module3.module3_logic import Module3Logic


class Module3Widget(qt.QWidget):
    """模块三界面（仅Mock标题）"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module3Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module3Logic()
        self.setObjectName("Module3Widget")
        self._setup_ui()
        logging.info("Module3Widget 初始化完成 (skeleton)")

    def _setup_ui(self):
        # 使用统一布局与样式体系，和模块1、2保持一致
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 标题区（Mock）
        title = qt.QLabel("模块三：自动化测量（Mock 页面）")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))

        desc = qt.QLabel("此处为占位页面，用于确认导航切换与框架搭建是否正常。")
        desc.setAlignment(qt.Qt.AlignCenter)
        desc.setStyleSheet(StyleManager.get_label_style("muted"))

        # 容器
        container = LayoutManager.create_section_frame("模块三")
        container_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, container)
        container_layout.addWidget(title)
        container_layout.addWidget(desc)

        main_layout.addWidget(container, 1)
        LayoutManager.add_stretch_with_ratio(main_layout, 1)

    def set_session(self, session: TAVRStudySession):
        self.session = session

    def on_activated(self):
        logging.info("模块三已激活")

    def on_deactivated(self):
        logging.info("模块三已停用")

    def cleanup(self):
        if self.logic:
            self.logic.cleanup()
        logging.info("模块三界面清理完成")
