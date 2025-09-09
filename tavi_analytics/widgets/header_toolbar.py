"""
Unified header toolbar for modules: includes compact phase toggle, right-side action area,
and an optional "next module" navigation button.
"""
import logging
from typing import Optional
import qt

try:
    from ..utils.layout_manager import LayoutManager
    from .compact_phase_toggle import CompactPhaseToggle
except ImportError:
    from utils.layout_manager import LayoutManager
    from compact_phase_toggle import CompactPhaseToggle


class HeaderToolbar(qt.QWidget):
    phaseChanged = qt.Signal(str)  # re-emit from CompactPhaseToggle

    def __init__(self, session=None, next_module_name: Optional[str] = None, parent=None,
                 show_phase_toggle: bool = True, show_next_button: bool = True):
        super().__init__(parent)
        self.session = session
        self.next_module_name = next_module_name
        self.setObjectName("HeaderToolbar")

        # Layout: align with modules (margins 8,8,8,8; spacing 20)
        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(20)

        # Left: Phase toggle (optional)
        self.compact_phase_toggle = None
        if show_phase_toggle:
            try:
                self.compact_phase_toggle = CompactPhaseToggle(self.session, self)
                # bridge signal
                self.compact_phase_toggle.phaseChanged.connect(lambda p: self.phaseChanged.emit(p))
                layout.addWidget(self.compact_phase_toggle)
            except Exception as e:
                logging.warning(f"创建紧凑期像切换器失败: {e}")

        layout.addStretch()

        # Right action area container
        self._right_container = qt.QWidget()
        self._right_layout = qt.QHBoxLayout(self._right_container)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(8)

        # Next module button (optional)
        self.next_btn = None
        if show_next_button:
            try:
                label = self._build_next_label()
                # 使用更现代的toolbar-tonal风格
                self.next_btn = LayoutManager.create_button_with_style(label, "toolbar-tonal", "default", 32)
                self.next_btn.setMinimumWidth(112)
                self.next_btn.clicked.connect(self._on_next_clicked)
                self._right_layout.addWidget(self.next_btn)
            except Exception as e:
                logging.warning(f"创建下一模块按钮失败: {e}")

        layout.addWidget(self._right_container)

    def add_right_widget(self, widget: qt.QWidget):
        """添加组件到右侧区域，并自动应用工具条样式"""
        try:
            # 自动为右侧区域新增的QPushButton应用工具条样式
            self._right_layout.insertWidget(0, widget)
            try:
                if isinstance(widget, qt.QPushButton):
                    # 使用新的 toolbar-tonal 样式
                    from ..ui.styles import StyleManager  # 局部导入以避免循环
                    widget.setMinimumHeight(32)
                    widget.setStyleSheet(StyleManager.get_button_style("toolbar-tonal", "default"))
            except Exception:
                # Fallback 通过LayoutManager更新（若样式模块不可用）
                try:
                    widget.setMinimumHeight(32)
                    # 基础样式作为fallback
                    if isinstance(widget, qt.QPushButton):
                        widget.setStyleSheet("""
                            QPushButton {
                                background-color: #f1f5f9;
                                color: #475569;
                                border: 1px solid #e2e8f0;
                                border-radius: 8px;
                                padding: 8px 16px;
                                font-size: 12px;
                                font-weight: 500;
                            }
                            QPushButton:hover {
                                background-color: #e2e8f0;
                            }
                        """)
                except Exception:
                    pass
        except Exception:
            pass

    def set_session(self, session):
        self.session = session
        if self.compact_phase_toggle:
            try:
                self.compact_phase_toggle.session = session
            except Exception:
                pass

    def set_next_module(self, next_module_name: Optional[str]):
        self.next_module_name = next_module_name
        if self.next_btn:
            try:
                self.next_btn.setText(self._build_next_label())
                self.next_btn.setEnabled(bool(next_module_name))
            except Exception:
                pass

    # Helpers
    def _build_next_label(self) -> str:
        display = self._resolve_module_display_name(self.next_module_name) if self.next_module_name else None
        return f"前往 {display}" if display else "下一模块"

    def _resolve_module_display_name(self, module_name: Optional[str]) -> Optional[str]:
        if not module_name:
            return None
        # Best-effort: try to ask ModuleManager via plugin
        try:
            import slicer
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            if plugin and hasattr(plugin, 'module_manager'):
                mi = plugin.module_manager.get_module_info(module_name)
                if mi and getattr(mi, 'display_name', None):
                    return mi.display_name
        except Exception:
            pass
        return module_name

    def _on_next_clicked(self):
        try:
            if not self.next_module_name:
                return
            import slicer
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            # Prefer MainUI for consistent UX (loading state, nav highlight)
            if plugin and hasattr(plugin, 'main_ui') and plugin.main_ui:
                plugin.main_ui.switch_to_module(self.next_module_name)
                return
            # Fallback to ModuleManager
            if plugin and hasattr(plugin, 'module_manager') and plugin.module_manager:
                plugin.module_manager.activate_module(self.next_module_name)
        except Exception as e:
            logging.error(f"切换到下一模块失败: {e}")
