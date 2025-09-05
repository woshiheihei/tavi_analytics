"""
Reusable ValveInfoPanel widget to display and set valve brand/model.
Intended to be used as a shared header in modules (e.g., Module4), instead of
duplicating this section inside each tab.
"""
import logging
import qt

try:
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager
    from ..widgets.section_card import SectionCard
    from ..core.session import TAVRStudySession
    from ..module4.module4_logic import Module4Logic
except ImportError:
    # Fallback for running as a script
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager
    from widgets.section_card import SectionCard
    from core.session import TAVRStudySession
    from module4.module4_logic import Module4Logic


class ValveInfoPanel(qt.QWidget):
    """Shared panel for valve information and selection."""

    def __init__(self, session: TAVRStudySession = None, logic: Module4Logic = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic
        self.logger = logging.getLogger(__name__)

        self.valve_status_icon = None
        self.valve_info_label = None
        self.valve_selector_frame = None
        self.manufacturer_combo = None
        self.model_combo = None
        self.set_valve_btn = None

        self._setup_ui()
        self._setup_valve_selector()
        self._update_valve_info()  # initial display

    def set_session(self, session: TAVRStudySession):
        self.session = session
        # ensure logic gets session if available
        if self.logic:
            self.logic.session = session
        self._setup_valve_selector()
        self._update_valve_info()

    def set_logic(self, logic: Module4Logic):
        self.logic = logic
        self._update_valve_info()

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        card = SectionCard(title="瓣膜信息", icon_text="🫀", variant="neutral", parent=self, header_compact=True)

        # Status row
        status_row = qt.QWidget()
        status_layout = qt.QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)

        self.valve_status_icon = qt.QLabel()
        self.valve_status_icon.setFixedSize(16, 16)
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxInformation)
            self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass

        self.valve_info_label = qt.QLabel("请在下方选择瓣膜品牌和型号")
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("muted"))
        status_layout.addWidget(self.valve_status_icon)
        status_layout.addWidget(self.valve_info_label)
        status_layout.addStretch()
        card.add_widget(status_row)

        # Selector grid
        self.valve_selector_frame = qt.QWidget()
        grid = qt.QGridLayout(self.valve_selector_frame)
        grid.setContentsMargins(0, 8, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        brand_label = qt.QLabel("厂家")
        brand_label.setStyleSheet(StyleManager.get_label_style("small"))
        self.manufacturer_combo = qt.QComboBox()
        self.manufacturer_combo.addItems([
            "Medtronic", "Edwards Lifesciences", "Venus Medtech",
            "MicroPort", "Peijia Medical"
        ])
        self.manufacturer_combo.setFixedHeight(28)
        self.manufacturer_combo.setMinimumWidth(180)

        model_label = qt.QLabel("型号")
        model_label.setStyleSheet(StyleManager.get_label_style("small"))
        self.model_combo = qt.QComboBox()
        self.model_combo.setFixedHeight(28)
        self.model_combo.setMinimumWidth(200)

        self.set_valve_btn = LayoutManager.create_button_with_style(
            "应用", "toolbar", "sm", 28
        )
        self.set_valve_btn.setMinimumWidth(88)

        grid.addWidget(brand_label, 0, 0)
        grid.addWidget(self.manufacturer_combo, 0, 1)
        grid.addWidget(model_label, 0, 2)
        grid.addWidget(self.model_combo, 0, 3)
        grid.addWidget(self.set_valve_btn, 0, 4)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 0)

        card.add_widget(self.valve_selector_frame)

        layout.addWidget(card)

    def _setup_valve_selector(self):
        try:
            if hasattr(self, 'model_combo'):
                self._init_model_combo_safely()
            # delayed signal connection to ensure UI is ready
            qt.QTimer.singleShot(100, self._connect_valve_selector_signals)
        except Exception as e:
            self.logger.error(f"设置瓣膜选择器失败: {e}")

    def _init_model_combo_safely(self):
        try:
            if not hasattr(self, 'model_combo'):
                return
            self.model_combo.clear()
            self.model_combo.addItems(["Evolut R/PRO", "Evolut FX", "CoreValve", "Evolut PRO+"])
        except Exception as e:
            self.logger.error(f"安全初始化型号下拉框失败: {e}")

    def _connect_valve_selector_signals(self):
        try:
            if hasattr(self, 'manufacturer_combo'):
                self.manufacturer_combo.currentTextChanged.connect(lambda: self._update_model_options())
            if hasattr(self, 'set_valve_btn'):
                self.set_valve_btn.clicked.connect(self._on_set_valve)
        except Exception as e:
            self.logger.error(f"连接瓣膜选择器信号失败: {e}")

    def _update_model_options(self):
        try:
            if not hasattr(self, 'manufacturer_combo') or not hasattr(self, 'model_combo'):
                return
            manufacturer = self.manufacturer_combo.currentText
            if callable(manufacturer):
                manufacturer = manufacturer()
            self.model_combo.clear()
            if manufacturer == "Medtronic":
                self.model_combo.addItems(["Evolut R/PRO", "Evolut FX", "CoreValve", "Evolut PRO+"])
            elif manufacturer == "Edwards Lifesciences":
                self.model_combo.addItems(["SAPIEN 3", "SAPIEN 3 Ultra", "SAPIEN XT"])
            elif manufacturer == "Venus Medtech":
                self.model_combo.addItems(["VenusA-Valve", "VenusA-Plus"])
            elif manufacturer == "MicroPort":
                self.model_combo.addItems(["VitaFlow"])
            elif manufacturer == "Peijia Medical":
                self.model_combo.addItems(["TaurusOne"])
            else:
                self.model_combo.addItem("Unknown Model")
        except Exception as e:
            self.logger.error(f"更新型号选项失败: {e}")

    def _on_set_valve(self):
        try:
            if not hasattr(self, 'manufacturer_combo') or not hasattr(self, 'model_combo'):
                return
            manufacturer = self.manufacturer_combo.currentText
            model = self.model_combo.currentText
            if callable(manufacturer):
                manufacturer = manufacturer()
            if callable(model):
                model = model()
            if not manufacturer or not model:
                return
            if self.logic:
                self.logic.set_valve_info(manufacturer, model)
                if self.session:
                    patient_data = self.session.get_patient_data()
                    if patient_data:
                        patient_data.valveBrand = manufacturer
                        patient_data.valveModel = model
            self._update_valve_info()
            self._check_and_hide_valve_selector()
        except Exception as e:
            self.logger.error(f"应用瓣膜设置失败: {e}")

    def _check_and_hide_valve_selector(self):
        try:
            if not hasattr(self, 'valve_selector_frame'):
                return
            if self.logic:
                mapping_summary = self.logic.get_valve_mapping_summary()
                if 'error' not in mapping_summary:
                    self.valve_selector_frame.setVisible(False)
                else:
                    self.valve_selector_frame.setVisible(True)
        except Exception as e:
            self.logger.error(f"检查瓣膜选择器状态失败: {e}")

    def _update_valve_info(self):
        try:
            if not hasattr(self, 'valve_info_label'):
                return
            if not self.logic:
                self._show_valve_info_error("逻辑组件未初始化")
                return
            mapping_summary = self.logic.get_valve_mapping_summary()
            if 'error' in mapping_summary:
                error_msg = mapping_summary['error']
                if '瓣膜信息未设置' in error_msg:
                    self._show_valve_info_warning("请在下方选择瓣膜品牌和型号")
                else:
                    self._show_valve_info_error(error_msg)
            else:
                valve_info = mapping_summary.get('valve_info', {})
                manufacturer = valve_info.get('manufacturer', '')
                model = valve_info.get('model', '')
                self._show_valve_info_success(f"瓣膜: {manufacturer} {model}")
        except Exception as e:
            self._show_valve_info_error(f"更新失败: {e}")

    def _show_valve_info_success(self, message: str):
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_DialogApplyButton)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("success"))

    def _show_valve_info_warning(self, message: str):
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxWarning)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("warning"))

    def _show_valve_info_error(self, message: str):
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxCritical)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("error"))

    def on_activated(self):
        self._update_valve_info()
        self._check_and_hide_valve_selector()

    def cleanup(self):
        pass
