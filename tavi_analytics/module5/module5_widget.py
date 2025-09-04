"""
模块五界面组件（占位）

页面标题：交接对齐
"""
import logging
from typing import Optional
import qt

try:
    from ..core.session import TAVRStudySession
    from ..utils.layout_manager import LayoutManager, LayoutType
    from ..ui.styles import ComponentStyleFactory
    from .module5_logic import Module5Logic
    from ..widgets.valve_overlay_widget import create_valve_overlay_widget
except ImportError:
    # 兼容直接运行
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from utils.layout_manager import LayoutManager, LayoutType
    from ui.styles import ComponentStyleFactory
    from module5_logic import Module5Logic
    from widgets.valve_overlay_widget import create_valve_overlay_widget


class Module5Widget(qt.QWidget):
    """模块五界面 - 交接对齐（占位仅展示标题）"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module5Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module5Logic(session)
        self.setObjectName("Module5Widget")
        self._setup_ui()
        logging.info("Module5Widget 初始化完成")

    def _setup_ui(self):
        # 统一布局容器（与其他模块一致，由主界面提供滚动）
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 顶部标题（占位）
        container = qt.QWidget()
        v = qt.QVBoxLayout(container)
        v.setContentsMargins(0, 40, 0, 40)
        v.setSpacing(16)
        v.setAlignment(qt.Qt.AlignTop | qt.Qt.AlignHCenter)

        styles = ComponentStyleFactory.get_main_ui_styles()
        title = qt.QLabel("交接对齐")
        try:
            title.setStyleSheet(styles.get("welcome_label", ""))
        except Exception:
            pass
        title.setAlignment(qt.Qt.AlignCenter)
        v.addWidget(title)

        # 瓣膜叠加组件（从模块四迁移）
        try:
            self.valve_overlay_widget = create_valve_overlay_widget(session=self.session, parent=self)
            v.addWidget(self.valve_overlay_widget)
            self._connect_valve_overlay_signals()
        except Exception as e:
            logging.warning(f"创建瓣膜叠加组件失败: {e}")

        main_layout.addWidget(container)
        main_layout.addStretch()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if self.logic:
            self.logic.set_session(session)
        if hasattr(self, 'valve_overlay_widget') and self.valve_overlay_widget:
            try:
                self.valve_overlay_widget.set_session(session)
            except Exception:
                pass

    def on_activated(self):
        logging.info("模块五已激活")

    def on_deactivated(self):
        logging.info("模块五已停用")

    def cleanup(self):
        if hasattr(self, 'valve_overlay_widget') and self.valve_overlay_widget:
            try:
                self.valve_overlay_widget.cleanup()
            except Exception:
                pass
        if self.logic:
            self.logic.cleanup()
        logging.info("模块五界面清理完成")

    # ====== 瓣膜叠加信号与回调（从模块四迁移） ======
    def _connect_valve_overlay_signals(self):
        if not getattr(self, 'valve_overlay_widget', None):
            return
        w = self.valve_overlay_widget
        try:
            w.overlayEnabled.connect(self._on_valve_overlay_changed)
            w.opacityChanged.connect(self._on_valve_opacity_changed)
            w.statusUpdated.connect(self._on_valve_status_updated)
            # 额外回调
            w.add_overlay_callback(self._valve_overlay_callback)
            w.add_opacity_callback(self._valve_opacity_callback)
        except Exception as e:
            logging.warning(f"绑定瓣膜叠加信号失败: {e}")

    def _on_valve_overlay_changed(self, is_enabled: bool):
        status = "启用" if is_enabled else "禁用"
        logging.info(f"模块五响应：瓣膜叠加已{status}")

    def _on_valve_opacity_changed(self, opacity: float):
        logging.info(f"模块五响应：瓣膜透明度调整为 {opacity:.2f}")

    def _on_valve_status_updated(self, status: str):
        logging.info(f"模块五收到瓣膜状态更新: {status}")

    def _valve_overlay_callback(self, is_enabled: bool):
        status = "启用" if is_enabled else "禁用"
        logging.debug(f"模块五回调：瓣膜叠加{status}回调被触发")

    def _valve_opacity_callback(self, opacity: float):
        logging.debug(f"模块五回调：透明度回调 {opacity:.2f}")
