"""
模块五界面组件
"""
import logging
from typing import Optional
import qt

try:
    from ..core.session import TAVRStudySession
    from ..utils.layout_manager import LayoutManager, LayoutType
    from .module5_logic import Module5Logic
    from ..widgets.valve_overlay_widget import create_valve_overlay_widget
    from ..widgets.compact_phase_toggle import CompactPhaseToggle
    from ..widgets.section_card import SectionCard
    from ..services.contour_positioning_service import get_contour_position_service
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
    from module5_logic import Module5Logic
    from widgets.valve_overlay_widget import create_valve_overlay_widget
    from widgets.compact_phase_toggle import CompactPhaseToggle
    from widgets.section_card import SectionCard
    from services.contour_positioning_service import get_contour_position_service


class Module5Widget(qt.QWidget):
    """模块五界面 - 交接对齐"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module5Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module5Logic(session)
        self.setObjectName("Module5Widget")
        # 紧凑期像切换组件（与模块3/4一致）
        self.compact_phase_toggle = CompactPhaseToggle(session, self)
        self.compact_phase_toggle.phaseChanged.connect(self._on_phase_changed)
        # 轮廓定位服务
        try:
            self.contour_service = get_contour_position_service()
        except Exception:
            self.contour_service = None
        self._setup_ui()
        logging.info("Module5Widget 初始化完成")

    def _setup_ui(self):
        # 统一布局容器（与其他模块一致，由主界面提供滚动）
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 顶部第一行：期像切换器（与模块3/4保持一致风格与边距）
        title_container = qt.QWidget()
        title_layout = qt.QHBoxLayout(title_container)
        title_layout.setContentsMargins(8, 8, 8, 8)
        title_layout.setSpacing(20)
        title_layout.addWidget(self.compact_phase_toggle)
        title_layout.addStretch()
        main_layout.addWidget(title_container)

        # 第二行：分析准备 Section（风格参考“瓣膜信息”区，非虚线）
        self._create_start_analysis_section(main_layout)

        # 第三行：瓣膜叠加组件（从模块四迁移）
        try:
            self.valve_overlay_widget = create_valve_overlay_widget(session=self.session, parent=self)
            main_layout.addWidget(self.valve_overlay_widget)
            self._connect_valve_overlay_signals()
        except Exception as e:
            logging.warning(f"创建瓣膜叠加组件失败: {e}")

        # 拉伸占位，避免高度变化带来整体抖动
        main_layout.addStretch()

    def _create_start_analysis_section(self, parent_layout):
        card = SectionCard(title="分析准备", icon_text="🧭", variant="neutral", parent=self, header_compact=True)
        row = qt.QWidget()
        h = qt.QHBoxLayout(row)
        h.setSpacing(6)
        h.setContentsMargins(6, 6, 6, 6)
        self.start_analysis_btn = LayoutManager.create_button_with_style("开始分析", "toolbar", "sm", 28)
        self.start_analysis_btn.clicked.connect(self._on_start_alignment)
        h.addWidget(self.start_analysis_btn)
        h.addStretch()
        card.add_widget(row)
        parent_layout.addWidget(card)
        self._start_card = card

    def _on_phase_changed(self, phase: str):
        """
        期像改变时的回调
        Args:
            phase: 'diastole' 或 'systole'
        """
        logging.info(f"模块五期像已切换到: {phase}")
        # 更新逻辑层的当前期像（领域模型键）
        if self.logic:
            domain_phase = 'end_diastole' if phase == 'diastole' else 'end_systole'
            try:
                self.logic.set_current_phase(domain_phase)
            except Exception:
                pass
        # 同步UI（若来自外部变更）
        self._sync_phase_widgets(phase)

    def _sync_phase_widgets(self, phase: str):
        """同步紧凑期像切换组件状态"""
        try:
            if hasattr(self, 'compact_phase_toggle') and self.compact_phase_toggle:
                current_phase = self.compact_phase_toggle.get_current_phase()
                if current_phase != phase:
                    self.compact_phase_toggle.sync_phase_from_external(phase)
        except Exception as e:
            logging.error(f"模块五同步期像组件状态失败: {e}")

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if self.logic:
            self.logic.set_session(session)
        if hasattr(self, 'compact_phase_toggle') and self.compact_phase_toggle:
            self.compact_phase_toggle.session = session
        if hasattr(self, 'valve_overlay_widget') and self.valve_overlay_widget:
            try:
                self.valve_overlay_widget.set_session(session)
            except Exception:
                pass

    def on_activated(self):
        logging.info("模块五已激活")
        # 设置默认期像（与模块3/4一致）
        if hasattr(self, 'compact_phase_toggle') and self.compact_phase_toggle:
            self.compact_phase_toggle.set_current_phase('diastole')

    def on_deactivated(self):
        logging.info("模块五已停用")

    def cleanup(self):
        if hasattr(self, 'compact_phase_toggle') and self.compact_phase_toggle:
            try:
                self.compact_phase_toggle.cleanup()
            except Exception:
                pass
        if hasattr(self, 'valve_overlay_widget') and self.valve_overlay_widget:
            try:
                self.valve_overlay_widget.cleanup()
            except Exception:
                pass
        if self.logic:
            self.logic.cleanup()
        logging.info("模块五界面清理完成")

    # ====== 开始分析：切换到当前期像的瓦氏窦平面 ======
    def _on_start_alignment(self):
        try:
            if hasattr(self, 'start_analysis_btn') and self.start_analysis_btn:
                self.start_analysis_btn.setEnabled(False)
                qt.QApplication.processEvents()

            # 获取当前UI期像并映射到领域键
            ui_phase = None
            try:
                ui_phase = self.compact_phase_toggle.get_current_phase() if hasattr(self, 'compact_phase_toggle') else None
            except Exception:
                pass
            if ui_phase not in ('diastole', 'systole'):
                # 回退：从期像服务获取
                try:
                    phase_service = self.session.get_phase_management_service() if self.session else None
                    ui_phase = phase_service.get_current_phase() if phase_service else 'diastole'
                except Exception:
                    ui_phase = 'diastole'

            domain_phase = 'end_diastole' if ui_phase == 'diastole' else 'end_systole'

            # 校验对应期像是否已标记
            phase_info = self.session.get_marked_phase(domain_phase) if self.session else None
            if not phase_info or phase_info.get('frame_index') is None:
                qt.QMessageBox.warning(self, "警告", f"未找到{ '舒张末期' if domain_phase=='end_diastole' else '收缩末期' }标记！\n\n请先在模块一中完成期像标记。")
                return

            # 切换到瓦氏窦（Sinus of Valsalva）
            if not self.contour_service:
                raise RuntimeError("未能获取轮廓定位服务")
            success = bool(self.contour_service.switch_to_contour('sinus_of_valsalva', phase=domain_phase))
            if success:
                # 同步服务当前期像（便于后续操作）
                try:
                    self.contour_service.set_current_phase(domain_phase)
                except Exception:
                    pass
                qt.QMessageBox.information(self, "已定位", f"已定位到当前期像（{ '舒张末期' if domain_phase=='end_diastole' else '收缩末期' }）的瓦氏窦平面。")
            else:
                qt.QMessageBox.information(self, "提示", "自动定位失败，请手动调整MPR视图到瓦氏窦平面。")
        except Exception as e:
            logging.error(f"开始交接对齐分析失败: {e}")
            try:
                qt.QMessageBox.critical(self, "错误", f"启动失败：\n{e}")
            except Exception:
                pass
        finally:
            if hasattr(self, 'start_analysis_btn') and self.start_analysis_btn:
                self.start_analysis_btn.setEnabled(True)

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
