"""
模块三分析界面组件

瓣叶功能评估相关分析的标准化用户界面框架，包含：
- RELM (瓣叶活动度减退)
- SFD (窦内充盈缺损)
- PFD (瓣叶下充盈缺损)

注意：HALT分析有独立的实现 (halt_analysis_widget.py)
"""
import logging
from typing import Optional, Dict, Any, List
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager
    from ..widgets.key_view_manager_widget import KeyViewManagerWidget
    from ..services.contour_positioning_service import get_contour_position_service
    from .paste_analysis_logic import (
        Module3AnalysisLogic,
        RelmAnalysisLogic,
        SfdAnalysisLogic,
        PfdAnalysisLogic,
    )
    from ..widgets.section_card import SectionCard
except ImportError:  # pragma: no cover - dev fallback
    import os, sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    from core.session import TAVRStudySession
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager
    from widgets.key_view_manager_widget import KeyViewManagerWidget
    from services.contour_positioning_service import get_contour_position_service
    from paste_analysis_logic import (
        Module3AnalysisLogic,
        RelmAnalysisLogic,
        SfdAnalysisLogic,
        PfdAnalysisLogic,
    )
    from widgets.section_card import SectionCard


class BaseAnalysisWidget(qt.QWidget):
    """分析界面基类 - 标准化接口"""

    statusChanged = qt.Signal(dict)
    # 新增：分析状态改变（not_started | in_progress | completed）
    analysisStateChanged = qt.Signal(str)
    # 新增：请求父组件切换到下一个分析Tab
    nextRequested = qt.Signal()

    def __init__(self, analysis_type: str, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.session = session
        self.setObjectName(f"{analysis_type}AnalysisWidget")
        # 统一分析状态，默认未开始
        self._analysis_state = "not_started"
        # 统一每个选项卡页面的尺寸策略，避免在切换Tab时因sizeHint不同导致父容器高度抖动
        try:
            self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Expanding)
        except Exception:
            pass
        logging.info(f"{analysis_type}分析界面初始化")

    # ---- 生命周期/会话 ----
    def set_session(self, session: TAVRStudySession):
        self.session = session
        if hasattr(self, "key_view_manager") and self.key_view_manager:
            self.key_view_manager.set_session(session)

    def on_activated(self):
        logging.info(f"{self.analysis_type}分析界面激活")

    def on_deactivated(self):
        logging.info(f"{self.analysis_type}分析界面停用")
        # 停用时也持久化一次
        try:
            if self.session and hasattr(self.session, 'update_module3_result'):
                key_map = {'RELM': 'relm', 'SFD': 'sfd', 'PFD': 'pfd'}
                key = key_map.get(self.analysis_type)
                if key:
                    self.session.update_module3_result(key, self.get_analysis_results())
        except Exception:
            pass

    def cleanup(self):
        if hasattr(self, "key_view_manager") and self.key_view_manager:
            self.key_view_manager.cleanup()
        logging.info(f"{self.analysis_type}分析界面清理完成")

    # ---- 结果/事件 ----
    def _emit_status_changed(self):
        results = self.get_analysis_results()
        # 将子类结果存入Session（按analysis_type键）
        try:
            if self.session and hasattr(self.session, 'update_module3_result'):
                key_map = {'RELM': 'relm', 'SFD': 'sfd', 'PFD': 'pfd'}
                key = key_map.get(self.analysis_type)
                if key:
                    self.session.update_module3_result(key, results)
        except Exception:
            pass
        self.statusChanged.emit(results)

    # ---- 分析状态（统一对外发射信号）----
    def set_analysis_state(self, state: str):
        if state not in ("not_started", "in_progress", "completed"):
            return
        if getattr(self, "_analysis_state", None) == state:
            return
        self._analysis_state = state
        try:
            self.analysisStateChanged.emit(state)
        except Exception:
            pass

    def get_analysis_results(self) -> Dict[str, Any]:
        return {"analysis_type": self.analysis_type, "status": "占位符"}

    def reset_analysis(self):
        logging.info(f"{self.analysis_type}分析重置（基类）")

    # ---- 公共UI片段 ----
    def _create_key_view_section(self, parent_layout):
        card = SectionCard(title="关键视图", icon_text="🔖", variant="dashed", parent=self)
        # 使用内容型关键视图组件，并将操作按钮放入卡片Header
        self.key_view_manager = KeyViewManagerWidget(
            analysis_type=self.analysis_type,
            session=self.session,
            compact_mode=True,
            parent=self,
            use_external_header=True,
        )
        # 将“标记”按钮放到右上角，避免内容区出现空白
        card.add_header_widget(self.key_view_manager.mark_btn, align_right=True)
        card.add_widget(self.key_view_manager)
        parent_layout.addWidget(card)

    def _create_action_buttons(self, parent_layout, include_status_btn: bool = True, next_label=None):
        actions = qt.QHBoxLayout()
        actions.setSpacing(8)
        # 与 HALT 页面对齐的边距，减少视觉抖动
        try:
            actions.setContentsMargins(2, 6, 2, 2)
        except Exception:
            pass
        reset_btn = LayoutManager.create_button_with_style("重置", "toolbar", "sm", 28)
        reset_btn.clicked.connect(self.reset_analysis)
        actions.addWidget(reset_btn)
        actions.addStretch()
        # 替换为“分析下一个”按钮
        if include_status_btn:
            label_text = next_label if next_label else "分析下一个"
            next_btn = LayoutManager.create_button_with_style(label_text, "toolbar", "sm", 28)
            next_btn.clicked.connect(self._analyze_next)
            actions.addWidget(next_btn)
        parent_layout.addLayout(actions)

    def _show_status(self):
        results = self.get_analysis_results()
        lines: List[str] = [
            f"分析类型: {results.get('analysis_type', self.analysis_type)}",
            f"状态: {results.get('status', '-')}",
        ]
        for k, v in results.items():
            if k in ("analysis_type", "status"):
                continue
            lines.append(f"{k}: {v}")
        qt.QMessageBox.information(self, f"{self.analysis_type} 分析状态", "\n".join(lines))

    def _analyze_next(self):
        """将当前分析标记为完成后执行后续动作（SFD→PFD，PFD→Module4）"""
        # 标记完成
        try:
            self.set_analysis_state("completed")
        except Exception:
            pass
        # 首选：通过信号请求父组件切换
        try:
            self.nextRequested.emit()
        except Exception:
            pass
        # 备选：父组件旧的回调路径
        parent = self.parent()
        while parent is not None and not hasattr(parent, "on_child_analysis_state_changed"):
            parent = parent.parent() if hasattr(parent, "parent") else None
        if parent is not None:
            try:
                parent.on_child_analysis_state_changed(self, "completed", go_next=True)
            except Exception:
                pass
        # PFD：尝试跳到模块四
        if getattr(self, 'analysis_type', '') == 'PFD':
            try:
                import slicer  # type: ignore
                plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
                if plugin and hasattr(plugin, 'main_ui') and plugin.main_ui:
                    plugin.main_ui.switch_to_module("module4")
                    return
            except Exception:
                pass

    def _find_tab_widget(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, qt.QTabWidget):
                return parent
            parent = parent.parent() if hasattr(parent, "parent") else None
        return None


class RelmAnalysisWidget(BaseAnalysisWidget):
    """RELM (瓣叶活动度减退)"""

    def __init__(self, session: TAVRStudySession, logic: Optional[RelmAnalysisLogic] = None, parent=None):
        super().__init__("RELM", session, parent)
        self.logic = logic or RelmAnalysisLogic()
        self.logic.set_session(session)
        self._setup_ui()

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        try:
            layout.setSizeConstraint(qt.QLayout.SetDefaultConstraint)
        except Exception:
            pass
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = qt.QLabel("RELM 瓣叶活动度减退分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)

        # 参数卡片
        param_card = SectionCard(title="分析参数", icon_text="🎛️", variant="dashed", parent=self)
        form = qt.QHBoxLayout()
        form.setSpacing(8)

        leaflet_label = qt.QLabel("选择瓣叶：")
        leaflet_label.setStyleSheet(StyleManager.get_label_style("small"))
        self.leaflet_combo = qt.QComboBox()
        self.leaflet_combo.addItems(["请选择瓣叶", "LC", "RC", "NC"])
        self.leaflet_combo.setFixedHeight(28)
        self.leaflet_combo.currentTextChanged.connect(self._on_leaflet_changed)

        form.addWidget(leaflet_label)
        form.addWidget(self.leaflet_combo)
        form.addStretch()
        param_card.add_layout(form)
        layout.addWidget(param_card)

        # 关键视图
        self._create_key_view_section(layout)

        # 操作
        self._create_action_buttons(layout)

    def _on_leaflet_changed(self, leaflet: str):
        if leaflet and not leaflet.startswith("请选择"):
            self.logic.set_leaflet(leaflet)
        else:
            self.logic.set_leaflet(None)
        self._emit_status_changed()

    def get_analysis_results(self) -> Dict[str, Any]:
        results = self.logic.get_analysis_results()
        if hasattr(self, "key_view_manager"):
            results["key_views_count"] = self.key_view_manager.get_marked_views_count()
            results["key_view_names"] = self.key_view_manager.get_marked_view_names()
        return results

    def reset_analysis(self):
        self.logic.reset_analysis()
        if hasattr(self, "leaflet_combo"):
            self.leaflet_combo.setCurrentIndex(0)
        self._emit_status_changed()


class SfdAnalysisWidget(BaseAnalysisWidget):
    """SFD (窦内充盈缺损)"""

    def __init__(self, session: TAVRStudySession, logic: Optional[SfdAnalysisLogic] = None, parent=None):
        super().__init__("SFD", session, parent)
        self.logic = logic or SfdAnalysisLogic()
        self.logic.set_session(session)
        self.contour_service = get_contour_position_service()
        self.analysis_started = False
        self.affected_sinuses: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        try:
            layout.setSizeConstraint(qt.QLayout.SetDefaultConstraint)
        except Exception:
            pass
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = qt.QLabel("SFD 窦内充盈缺损分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)

        # 分析准备
        self._create_analysis_control_section(layout)

        # 状态 + 受累窦选择
        card = SectionCard(title="SFD 状态与选择", icon_text="🧪", variant="dashed", parent=self)
        body = qt.QVBoxLayout()
        body.setSpacing(10)

        status_title = qt.QLabel("1. SFD状态")
        status_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        body.addWidget(status_title)

        btns = qt.QHBoxLayout()
        btns.setSpacing(6)
        self.status_group = qt.QButtonGroup()
        button_configs = [("无", "#d4f6d4", "#28a745"), ("有", "#fdeaea", "#dc3545"), ("难以判定", "#fff8dc", "#ffc107")]
        self.status_buttons = {}
        for i, (text, bg, border) in enumerate(button_configs):
            b = qt.QRadioButton(text)
            b.setStyleSheet(
                f"""
                QRadioButton {{
                    font-size: 11px; font-weight: 500; padding: 6px 12px; margin: 1px;
                    background-color: {bg}; border: 2px solid {bg}; border-radius: 4px;
                }}
                QRadioButton:checked {{ border: 2px solid {border}; font-weight: bold; background-color: white; }}
                QRadioButton:hover {{ border: 2px solid {border}; }}
                """
            )
            self.status_group.addButton(b, i)
            self.status_buttons[text] = b
            btns.addWidget(b)

        self.status_buttons["无"].setChecked(True)
        self.status_group.buttonClicked.connect(self._on_status_changed)
        btns.addStretch()
        body.addLayout(btns)

        self._create_sinus_selection_section(body)

        card.add_layout(body)
        layout.addWidget(card)

        # 关键视图 + 操作
        self._create_key_view_section(layout)
        # SFD页：按钮显示为“继续分析PFD”
        self._create_action_buttons(layout, next_label="继续分析PFD")

    def _create_analysis_control_section(self, parent_layout):
        card = SectionCard(title="分析准备", icon_text="🧭", variant="dashed", parent=self)
        control_row = qt.QWidget()
        control_layout = qt.QHBoxLayout(control_row)
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(6, 6, 6, 6)

        self.start_analysis_btn = LayoutManager.create_button_with_style("开始分析", "toolbar", "sm", 28)
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        control_layout.addStretch()
        card.add_widget(control_row)
        parent_layout.addWidget(card)
        self.control_frame = card

    def _create_sinus_selection_section(self, parent_layout):
        sinus_title = qt.QLabel("2. 受累主动脉窦（仅在选择“有”时显示）")
        sinus_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")

        sinus_buttons_layout = qt.QHBoxLayout()
        sinus_buttons_layout.setSpacing(6)
        self.sinus_checkboxes: Dict[str, qt.QCheckBox] = {}

        for name in ["LC", "RC", "NC"]:
            checkbox = qt.QCheckBox(name)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    padding: 6px 12px; margin: 1px; border: 1px solid #dee2e6; border-radius: 4px;
                    background-color: #f8f9fa;
                }
                QCheckBox:checked {
                    border: 2px solid #0d6efd; background-color: white; font-weight: 600;
                }
                QCheckBox:hover { border: 1px solid #0d6efd; }
                """
            )
            checkbox.stateChanged.connect(lambda state, n=name: self._on_sinus_selection_changed(n, state == qt.Qt.Checked))
            self.sinus_checkboxes[name] = checkbox
            sinus_buttons_layout.addWidget(checkbox)
        sinus_buttons_layout.addStretch()

        self.sinus_widget = qt.QWidget()
        sinus_widget_layout = qt.QVBoxLayout(self.sinus_widget)
        sinus_widget_layout.setContentsMargins(0, 0, 0, 0)
        sinus_widget_layout.setSpacing(6)
        sinus_widget_layout.addWidget(sinus_title)
        sinus_widget_layout.addLayout(sinus_buttons_layout)
        self.sinus_widget.setVisible(False)
        parent_layout.addWidget(self.sinus_widget)

    def _on_sinus_selection_changed(self, name: str, checked: bool):
        if checked:
            if name not in self.affected_sinuses:
                self.affected_sinuses.append(name)
        else:
            if name in self.affected_sinuses:
                self.affected_sinuses.remove(name)
        self.logic.set_affected_sinuses(self.affected_sinuses)
        self._emit_status_changed()

    def _on_status_changed(self, button):
        button_id = self.status_group.id(button)
        status_map = {0: "none", 1: "present", 2: "indeterminate"}
        status = status_map.get(button_id, "none")

        self.logic.set_status(status)
        # 仅在present时显示主动脉窦选择
        if hasattr(self, "sinus_widget"):
            self.sinus_widget.setVisible(status == "present")
        if status != "present":
            # 清空选择
            self.affected_sinuses.clear()
            for cb in self.sinus_checkboxes.values():
                cb.setChecked(False)
        self._emit_status_changed()

    def _on_start_analysis(self):
        try:
            logging.info("用户开始SFD分析")
            self.start_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()

            # 检查收缩末期标记
            end_systole_info = self.session.get_marked_phase("end_systole") if self.session else None
            if not end_systole_info or end_systole_info.get("frame_index") is None:
                qt.QMessageBox.warning(self, "警告", "未找到收缩末期标记！\n\n请先在模块一中标记收缩末期时相。")
                self._reset_analysis_buttons()
                return

            # 切换到收缩末期
            if not self._switch_to_end_systole():
                qt.QMessageBox.warning(self, "错误", "切换到收缩末期失败！请检查模块一中的期像标记。")
                self._reset_analysis_buttons()
                return

            # 定位到瓦氏窦
            if not self._position_to_sinus_valsalva():
                qt.QMessageBox.information(self, "提示", "自动定位失败，请手动调整MPR视图到合适位置。\n分析可以继续进行。")

            self._complete_analysis_preparation()
        except Exception as e:
            logging.error(f"开始SFD分析失败: {e}")
            qt.QMessageBox.critical(self, "错误", f"分析启动失败：\n{e}")
            self._reset_analysis_buttons()

    def _complete_analysis_preparation(self):
        self.analysis_started = True
        if hasattr(self, "control_frame"):
            self.control_frame.setVisible(False)
        logging.info("SFD分析准备完成")
        # 更新状态：进行中
        self.set_analysis_state("in_progress")

    def _reset_analysis_buttons(self):
        if hasattr(self, "start_analysis_btn"):
            self.start_analysis_btn.setEnabled(True)

    def _switch_to_end_systole(self) -> bool:
        try:
            success = self.session.switch_to_systole("SFD_Analysis") if self.session else False
            if success:
                self.contour_service.set_current_phase("end_systole")
                return True
            return False
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False

    def _position_to_sinus_valsalva(self) -> bool:
        try:
            return bool(self.contour_service.switch_to_contour("sinus_of_valsalva", phase="end_systole"))
        except Exception as e:
            logging.error(f"定位到瓦氏窦平面失败: {e}")
            return False

    def get_analysis_results(self) -> Dict[str, Any]:
        results = self.logic.get_analysis_results()
        if hasattr(self, "key_view_manager"):
            results["key_views_count"] = self.key_view_manager.get_marked_views_count()
            results["key_view_names"] = self.key_view_manager.get_marked_view_names()
        return results

    def reset_analysis(self):
        self.analysis_started = False
        if hasattr(self, "control_frame"):
            self.control_frame.setVisible(True)
        if hasattr(self, "start_analysis_btn"):
            self.start_analysis_btn.setEnabled(True)
        self.logic.reset_analysis()
        self.status_buttons["无"].setChecked(True)
        # 清理窦选择
        self.affected_sinuses.clear()
        for cb in getattr(self, "sinus_checkboxes", {}).values():
            cb.setChecked(False)
        if hasattr(self, "sinus_widget"):
            self.sinus_widget.setVisible(False)
        self._emit_status_changed()
        # 更新状态：未开始
        self.set_analysis_state("not_started")


class PfdAnalysisWidget(BaseAnalysisWidget):
    """PFD (瓣叶下充盈缺损)"""

    def __init__(self, session: TAVRStudySession, logic: Optional[PfdAnalysisLogic] = None, parent=None):
        super().__init__("PFD", session, parent)
        self.logic = logic or PfdAnalysisLogic()
        self.logic.set_session(session)
        self.contour_service = get_contour_position_service()
        self.analysis_started = False
        self._setup_ui()

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = qt.QLabel("PFD 瓣叶下充盈缺损分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)

        self._create_analysis_control_section(layout)

        card = SectionCard(title="PFD 状态与厚度", icon_text="🧪", variant="dashed", parent=self)
        body = qt.QVBoxLayout()
        body.setSpacing(10)

        status_title = qt.QLabel("1. PFD状态")
        status_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        body.addWidget(status_title)

        btns = qt.QHBoxLayout()
        btns.setSpacing(6)
        self.status_group = qt.QButtonGroup()
        button_configs = [("无", "#d4f6d4", "#28a745"), ("有", "#fdeaea", "#dc3545"), ("难以判定", "#fff8dc", "#ffc107")]
        self.status_buttons = {}
        for i, (text, bg, border) in enumerate(button_configs):
            b = qt.QRadioButton(text)
            b.setStyleSheet(
                f"""
                QRadioButton {{
                    font-size: 11px; font-weight: 500; padding: 6px 12px; margin: 1px;
                    background-color: {bg}; border: 2px solid {bg}; border-radius: 4px;
                }}
                QRadioButton:checked {{ border: 2px solid {border}; font-weight: bold; background-color: white; }}
                QRadioButton:hover {{ border: 2px solid {border}; }}
                """
            )
            self.status_group.addButton(b, i)
            self.status_buttons[text] = b
            btns.addWidget(b)
        self.status_buttons["无"].setChecked(True)
        self.status_group.buttonClicked.connect(self._on_status_changed)
        btns.addStretch()
        body.addLayout(btns)

        self._create_thickness_section(body)

        card.add_layout(body)
        layout.addWidget(card)

        self._create_key_view_section(layout)
        # PFD页：按钮显示为“继续分析瓣膜支架几何形态评估”
        self._create_action_buttons(layout, next_label="继续分析瓣膜支架几何形态评估")

    def _analyze_next(self):
        """PFD页：完成后跳转到模块四；否则退回到基类默认行为"""
        try:
            self.set_analysis_state("completed")
        except Exception:
            pass
        # 更新父Tab文本
        parent = self.parent()
        while parent is not None and not hasattr(parent, "on_child_analysis_state_changed"):
            parent = parent.parent() if hasattr(parent, "parent") else None
        if parent is not None:
            try:
                parent.on_child_analysis_state_changed(self, "completed", go_next=True)
            except Exception:
                pass
        # 尝试切换到模块四（瓣膜支架几何形态评估）
        try:
            import slicer  # type: ignore
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            if plugin and hasattr(plugin, 'main_ui') and plugin.main_ui:
                plugin.main_ui.switch_to_module("module4")
                return
        except Exception:
            pass
        # 兜底：尝试本地Tab切换（若存在）
        tw = self._find_tab_widget()
        if tw:
            idx = tw.indexOf(self)
            if idx >= 0 and (idx + 1) < tw.count():
                tw.setCurrentIndex(idx + 1)

    def _create_analysis_control_section(self, parent_layout):
        card = SectionCard(title="分析准备", icon_text="🧭", variant="dashed", parent=self)
        control_row = qt.QWidget()
        control_layout = qt.QHBoxLayout(control_row)
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(6, 6, 6, 6)
        self.start_analysis_btn = LayoutManager.create_button_with_style("开始分析", "toolbar", "sm", 28)
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        control_layout.addStretch()
        card.add_widget(control_row)
        parent_layout.addWidget(card)
        self.control_frame = card

    def _create_thickness_section(self, parent_layout):
        title = qt.QLabel("2. 最大厚度（仅在选择“有”时显示）")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        row = qt.QHBoxLayout()
        label = qt.QLabel("厚度 (mm):")
        label.setStyleSheet("font-size: 11px; font-weight: 500; color: #495057;")
        self.thickness_spinbox = qt.QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.0, 50.0)
        self.thickness_spinbox.setDecimals(1)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.valueChanged.connect(self._on_thickness_changed)
        row.addWidget(label)
        row.addWidget(self.thickness_spinbox)
        row.addStretch()
        self.thickness_widget = qt.QWidget()
        box = qt.QVBoxLayout(self.thickness_widget)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        box.addWidget(title)
        box.addLayout(row)
        self.thickness_widget.setVisible(False)
        parent_layout.addWidget(self.thickness_widget)

    def _on_status_changed(self, button):
        button_id = self.status_group.id(button)
        status_map = {0: "none", 1: "present", 2: "indeterminate"}
        status = status_map.get(button_id, "none")
        has_pfd = status == "present"
        if hasattr(self, "thickness_widget"):
            self.thickness_widget.setVisible(has_pfd)
            if not has_pfd:
                self.thickness_spinbox.setValue(0.0)
        self.logic.set_status(status)
        self._emit_status_changed()

    def _on_thickness_changed(self, value: float):
        self.logic.set_thickness(value)
        self._emit_status_changed()

    def _on_start_analysis(self):
        try:
            logging.info("用户开始PFD分析")
            self.start_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()

            end_systole_info = self.session.get_marked_phase("end_systole") if self.session else None
            if not end_systole_info or end_systole_info.get("frame_index") is None:
                qt.QMessageBox.warning(self, "警告", "未找到收缩末期标记！\n\n请先在模块一中标记收缩末期时相。")
                self._reset_analysis_buttons()
                return

            if not self._switch_to_end_systole():
                qt.QMessageBox.warning(self, "错误", "切换到收缩末期失败！请检查模块一中的期像标记。")
                self._reset_analysis_buttons()
                return

            if not self._position_to_sinus_valsalva():
                qt.QMessageBox.information(self, "提示", "自动定位失败，请手动调整MPR视图到合适位置。\n分析可以继续进行。")

            self._complete_analysis_preparation()
        except Exception as e:
            logging.error(f"开始PFD分析失败: {e}")
            qt.QMessageBox.critical(self, "错误", f"分析启动失败：\n{e}")
            self._reset_analysis_buttons()

    def _complete_analysis_preparation(self):
        self.analysis_started = True
        if hasattr(self, "control_frame"):
            self.control_frame.setVisible(False)
        logging.info("PFD分析准备完成")
        # 更新状态：进行中
        self.set_analysis_state("in_progress")

    def _reset_analysis_buttons(self):
        if hasattr(self, "start_analysis_btn"):
            self.start_analysis_btn.setEnabled(True)

    def _switch_to_end_systole(self) -> bool:
        try:
            success = self.session.switch_to_systole("PFD_Analysis") if self.session else False
            if success:
                self.contour_service.set_current_phase("end_systole")
                return True
            return False
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False

    def _position_to_sinus_valsalva(self) -> bool:
        try:
            return bool(self.contour_service.switch_to_contour("sinus_of_valsalva", phase="end_systole"))
        except Exception as e:
            logging.error(f"定位到瓦氏窦平面失败: {e}")
            return False

    def get_analysis_results(self) -> Dict[str, Any]:
        results = self.logic.get_analysis_results()
        if hasattr(self, "key_view_manager"):
            results["key_views_count"] = self.key_view_manager.get_marked_views_count()
            results["key_view_names"] = self.key_view_manager.get_marked_view_names()
        return results

    def reset_analysis(self):
        self.analysis_started = False
        if hasattr(self, "control_frame"):
            self.control_frame.setVisible(True)
        if hasattr(self, "start_analysis_btn"):
            self.start_analysis_btn.setEnabled(True)
        self.logic.reset_analysis()
        self.status_buttons["无"].setChecked(True)
        if hasattr(self, "thickness_spinbox"):
            self.thickness_spinbox.setValue(0.0)
        if hasattr(self, "thickness_widget"):
            self.thickness_widget.setVisible(False)
        self._emit_status_changed()
        # 更新状态：未开始
        self.set_analysis_state("not_started")


class Module3AnalysisWidget(qt.QWidget):
    """模块三标准化分析主界面"""

    statusChanged = qt.Signal(dict)

    def __init__(self, session: TAVRStudySession, logic: Optional[Module3AnalysisLogic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module3AnalysisLogic()
        self.logic.set_session(session)
        self.setObjectName("Module3AnalysisWidget")
        self._setup_ui()
        logging.info("模块三分析界面初始化完成")

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        title = qt.QLabel("模块三：瓣叶功能评估分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)

        self.analysis_tabs = qt.QTabWidget()
        self.analysis_tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #dee2e6; border-radius: 4px; background-color: white; }
            QTabBar::tab { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: white; border-bottom-color: white; }
            """
        )

        # 功能开关：临时隐藏 RELM 分析
        SHOW_RELM = False

        if SHOW_RELM:
            self.relm_widget = RelmAnalysisWidget(self.session, self.logic.get_relm_logic(), self)
            self.relm_widget.statusChanged.connect(self._on_child_status_changed)
            self.analysis_tabs.addTab(self.relm_widget, "RELM分析")

        self.sfd_widget = SfdAnalysisWidget(self.session, self.logic.get_sfd_logic(), self)
        self.pfd_widget = PfdAnalysisWidget(self.session, self.logic.get_pfd_logic(), self)

        self.sfd_widget.statusChanged.connect(self._on_child_status_changed)
        self.pfd_widget.statusChanged.connect(self._on_child_status_changed)

        self.analysis_tabs.addTab(self.sfd_widget, "SFD分析")
        self.analysis_tabs.addTab(self.pfd_widget, "PFD分析")

        layout.addWidget(self.analysis_tabs, 1)

        self._create_global_actions(layout)

    def _create_global_actions(self, parent_layout):
        card = SectionCard(title="全局操作", icon_text="⚙️", variant="dashed", parent=self)
        h = qt.QHBoxLayout()
        h.setSpacing(8)
        reset_all_btn = LayoutManager.create_button_with_style("重置所有", "toolbar", "sm", 28)
        reset_all_btn.clicked.connect(self._reset_all_analyses)
        export_btn = LayoutManager.create_button_with_style("导出结果", "toolbar", "sm", 28)
        export_btn.clicked.connect(self._export_results)
        summary_btn = LayoutManager.create_button_with_style("查看摘要", "toolbar", "sm", 28)
        summary_btn.clicked.connect(self._show_summary)
        h.addWidget(reset_all_btn)
        h.addStretch()
        h.addWidget(summary_btn)
        h.addWidget(export_btn)
        card.add_layout(h)
        parent_layout.addWidget(card)

    def _on_child_status_changed(self, _results):
        self.statusChanged.emit(self.get_all_analysis_results())

    def _reset_all_analyses(self):
        reply = qt.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有分析吗？\n\n这将清除所有输入的数据。",
            qt.QMessageBox.Yes | qt.QMessageBox.No,
        )
        if reply == qt.QMessageBox.Yes:
            self.logic.reset_all_analyses()
            if hasattr(self, 'relm_widget'):
                self.relm_widget.reset_analysis()
            self.sfd_widget.reset_analysis()
            self.pfd_widget.reset_analysis()
            logging.info("所有模块三分析已重置")

    def _export_results(self):
        try:
            results = self.get_all_analysis_results()
            from pathlib import Path
            import json

            export_dir = Path.home() / "TAVR_Analytics_Exports"
            export_dir.mkdir(exist_ok=True)
            timestamp = qt.QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
            json_file = export_dir / f"Module3_Analysis_{timestamp}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            summary = self.logic.get_analysis_summary()
            report_file = export_dir / f"Module3_Summary_{timestamp}.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(summary)
            qt.QMessageBox.information(self, "导出成功", f"结果已导出:\n\n数据文件：{json_file}\n摘要文件：{report_file}")
        except Exception as e:
            logging.error(f"导出模块三分析结果失败: {e}")
            qt.QMessageBox.critical(self, "导出失败", f"导出过程中出现错误：\n{e}")

    def _show_summary(self):
        summary = self.logic.get_analysis_summary()
        dialog = qt.QDialog(self)
        dialog.setWindowTitle("模块三分析摘要")
        dialog.setModal(True)
        dialog.resize(420, 320)
        layout = qt.QVBoxLayout(dialog)
        summary_text = qt.QTextEdit()
        summary_text.setPlainText(summary)
        summary_text.setReadOnly(True)
        summary_text.setStyleSheet(
            """
            QTextEdit { font-family: monospace; font-size: 11px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; }
            """
        )
        layout.addWidget(summary_text)
        close_btn = qt.QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()

    def get_all_analysis_results(self) -> Dict[str, Any]:
        return self.logic.get_all_results()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        self.logic.set_session(session)
        if hasattr(self, 'relm_widget'):
            self.relm_widget.set_session(session)
        self.sfd_widget.set_session(session)
        self.pfd_widget.set_session(session)

    def on_activated(self):
        logging.info("模块三分析界面激活")
        if hasattr(self, 'relm_widget'):
            self.relm_widget.on_activated()
        self.sfd_widget.on_activated()
        self.pfd_widget.on_activated()

    def on_deactivated(self):
        logging.info("模块三分析界面停用")
        if hasattr(self, 'relm_widget'):
            self.relm_widget.on_deactivated()
        self.sfd_widget.on_deactivated()
        self.pfd_widget.on_deactivated()

    def cleanup(self):
        if hasattr(self, 'relm_widget'):
            self.relm_widget.cleanup()
        self.sfd_widget.cleanup()
        self.pfd_widget.cleanup()
        self.logic.cleanup()
        logging.info("模块三分析界面清理完成")


PasteAnalysisWidget = Module3AnalysisWidget

__all__ = [
    "BaseAnalysisWidget",
    "RelmAnalysisWidget",
    "SfdAnalysisWidget",
    "PfdAnalysisWidget",
    "Module3AnalysisWidget",
    "PasteAnalysisWidget",
]