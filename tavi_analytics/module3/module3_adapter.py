"""
模块三适配器 - 实现模块接口（骨架）
"""
import os
import sys
from typing import List

# 路径修正，确保可导入核心
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.module_manager import ModuleInterface, ModuleEvent
from core.session import TAVRStudySession
from module3_widget import Module3Widget
from module3_logic import Module3Logic


class Module3Adapter(ModuleInterface):
    """模块三适配器（占位实现）"""

    def __init__(self):
        super().__init__()
        self._logic = None
        self._widget = None

    def get_module_name(self) -> str:
        return "module3"

    def get_display_name(self) -> str:
        return "自动化测量"

    def is_available(self) -> bool:
        try:
            import slicer  # 确认Slicer环境
            return True
        except Exception:
            return False

    def create_widget(self, session: TAVRStudySession, parent=None):
        if self._logic is None:
            self._logic = Module3Logic()
        self._widget = Module3Widget(session, logic=self._logic, parent=parent)
        return self._widget

    def get_dependencies(self) -> List[str]:
        # 参考模块二，模块三通常依赖模块一（数据已就绪）与模块二（完成分割/标志点）
        # 目前仅依赖模块一，便于先搭架子跑通导航
        return ["module1"]

    def on_module_loaded(self):
        self.publish_event(ModuleEvent.DATA_UPDATED, data={"status": "ready"})

    def on_module_activated(self):
        if self._widget and hasattr(self._widget, 'on_activated'):
            self._widget.on_activated()

    def on_module_deactivated(self):
        if self._widget and hasattr(self._widget, 'on_deactivated'):
            self._widget.on_deactivated()

    def on_session_changed(self, session):
        if self._widget and hasattr(self._widget, 'set_session'):
            self._widget.set_session(session)

    def cleanup(self):
        super().cleanup()
        if self._widget and hasattr(self._widget, 'cleanup'):
            self._widget.cleanup()
        self._widget = None
        self._logic = None
