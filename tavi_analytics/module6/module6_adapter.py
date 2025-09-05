"""
模块六适配器 - 报告生成

提供一个与模块管理器兼容的适配器，创建逻辑与界面组件。
"""
from typing import List
import os
import sys

# 兼容导入路径
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.module_manager import ModuleInterface, ModuleEvent
from core.session import TAVRStudySession
from .module6_logic import Module6Logic
from .module6_widget import Module6Widget


class Module6Adapter(ModuleInterface):
    """报告生成模块适配器"""

    def __init__(self):
        super().__init__()
        self._logic = None
        self._widget = None

    def get_module_name(self) -> str:
        return "module6"

    def get_display_name(self) -> str:
        return "报告生成"

    def is_available(self) -> bool:
        try:
            import slicer  # 需要在Slicer环境下运行
            return True
        except Exception:
            return True  # 允许在测试环境下创建

    def create_widget(self, session: TAVRStudySession, parent=None):
        if self._logic is None:
            self._logic = Module6Logic(session)
        else:
            self._logic.set_session(session)
        self._widget = Module6Widget(session, logic=self._logic, parent=parent)
        return self._widget

    def get_dependencies(self) -> List[str]:
        # 依赖模块一（会话数据与DICOM等基本状态），以及模块四/五可选
        return ["module1"]

    def on_module_loaded(self):
        self.publish_event(ModuleEvent.DATA_UPDATED, data={"status": "ready"})

    def on_module_activated(self, **kwargs):
        if self._widget and hasattr(self._widget, 'on_activated'):
            self._widget.on_activated()

    def on_module_deactivated(self):
        if self._widget and hasattr(self._widget, 'on_deactivated'):
            self._widget.on_deactivated()

    def on_session_changed(self, session):
        if self._logic:
            self._logic.set_session(session)
        if self._widget and hasattr(self._widget, 'set_session'):
            self._widget.set_session(session)

    def cleanup(self):
        super().cleanup()
        if self._widget and hasattr(self._widget, 'cleanup'):
            self._widget.cleanup()
        self._widget = None
        self._logic = None
