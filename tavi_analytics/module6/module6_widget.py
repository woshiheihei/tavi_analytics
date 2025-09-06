"""
模块六界面 - 报告生成页面（仅保留左侧审核表单，不显示右侧预览）

功能:
- 左侧审核关键字段（与样例表单一致的分区）
- 一键导出HTML报告到用户选择的文件
"""
import logging
from typing import Optional
import qt

from core.session import TAVRStudySession
from utils.layout_manager import LayoutManager, LayoutType
from .module6_logic import Module6Logic


class Module6Widget(qt.QWidget):
    def __init__(self, session: TAVRStudySession, logic: Optional[Module6Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module6Logic(session)

        self.setObjectName("Module6Widget")
        self._setup_ui()

    # UI
    def _setup_ui(self):
        layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 标题与按钮
        header = qt.QHBoxLayout()
        export_btn = LayoutManager.create_button_with_style("导出HTML", button_type="primary", size="sm")
        refresh_btn = LayoutManager.create_button_with_style("刷新", button_type="outline", size="sm")
        header.addWidget(refresh_btn)
        header.addWidget(export_btn)
        header.addStretch(1)
        layout.addLayout(header)

        # 审核表单（全宽）
        form_container = qt.QWidget()
        form_layout = qt.QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # Section A: 基本情况（只读）
        self.base_group = qt.QGroupBox("一、基本情况（只读）")
        base_form = qt.QFormLayout()
        self.lbl_patient = qt.QLabel()
        self.lbl_dates = qt.QLabel()
        self.lbl_valve = qt.QLabel()
        base_form.addRow("受试者/性别/年龄", self.lbl_patient)
        base_form.addRow("手术/CT日期", self.lbl_dates)
        base_form.addRow("瓣膜", self.lbl_valve)
        self.base_group.setLayout(base_form)
        form_layout.addWidget(self.base_group)

        # Section B: 交接对齐角度（可编辑）
        self.angles_group = qt.QGroupBox("二、交接对齐角度（可编辑, °）")
        ang_form = qt.QFormLayout()
        self.inp_angle_rcc_lcc = qt.QDoubleSpinBox(); self.inp_angle_rcc_lcc.setRange(0,360); self.inp_angle_rcc_lcc.setDecimals(1)
        self.inp_angle_lcc_ncc = qt.QDoubleSpinBox(); self.inp_angle_lcc_ncc.setRange(0,360); self.inp_angle_lcc_ncc.setDecimals(1)
        self.inp_angle_ncc_rcc = qt.QDoubleSpinBox(); self.inp_angle_ncc_rcc.setRange(0,360); self.inp_angle_ncc_rcc.setDecimals(1)
        ang_form.addRow("RCA→RCC/LCC", self.inp_angle_rcc_lcc)
        ang_form.addRow("RCA→LCC/NCC", self.inp_angle_lcc_ncc)
        ang_form.addRow("RCA→NCC/RCC", self.inp_angle_ncc_rcc)
        self.angles_group.setLayout(ang_form)
        form_layout.addWidget(self.angles_group)

        # Section C: 人工瓣膜支架评估（可编辑）
        self.stent_group = qt.QGroupBox("三、人工瓣膜支架评估（可编辑）")
        stent_layout = qt.QVBoxLayout()
        # 形态改变
        row_morph = qt.QHBoxLayout()
        row_morph.addWidget(qt.QLabel("是否存在人工瓣膜形态改变:"))
        self.sel_morph = qt.QComboBox(); self.sel_morph.addItems(["未填写","无","有"])
        row_morph.addWidget(self.sel_morph); row_morph.addStretch(1)
        stent_layout.addLayout(row_morph)

        # 平面覆盖编辑：两期像
        self._phase_tabs = qt.QTabWidget()
        for phase_key, phase_label in (("end_diastole","舒张末期"),("end_systole","收缩末期")):
            tab = qt.QWidget(); tab_layout = qt.QFormLayout(tab)
            # 为四种平面创建行（按Sapien3规则由刷新时控制显示）
            def mk_row():
                w = qt.QWidget(); h = qt.QHBoxLayout(w); h.setContentsMargins(0,0,0,0)
                ped = qt.QDoubleSpinBox(); ped.setRange(0, 200); ped.setDecimals(3); ped.setObjectName("ped")
                aed = qt.QDoubleSpinBox(); aed.setRange(0, 200); aed.setDecimals(3); aed.setObjectName("aed")
                dmax = qt.QDoubleSpinBox(); dmax.setRange(0, 200); dmax.setDecimals(3); dmax.setObjectName("dmax")
                dmin = qt.QDoubleSpinBox(); dmin.setRange(0, 200); dmin.setDecimals(3); dmin.setObjectName("dmin")
                for lab, sp in (("PED", ped),("AED", aed),("Dmax", dmax),("Dmin", dmin)):
                    h.addWidget(qt.QLabel(lab)); h.addWidget(sp)
                h.addStretch(1)
                return w
            self.rows = getattr(self, 'rows', {})
            for plane_key, plane_label in (("inflow","支架低端(inflow)"),("nadir","窦底(nadir)"),("outerskirt","外裙边(outerskirt)"),("commissure","对合平面(commissure)")):
                widget = mk_row()
                tab_layout.addRow(plane_label, widget)
                self.rows[(phase_key, plane_key)] = widget
            self._phase_tabs.addTab(tab, phase_label)
        stent_layout.addWidget(self._phase_tabs)

        # 应用覆盖按钮
        btns = qt.QHBoxLayout()
        self.btn_apply = LayoutManager.create_button_with_style("应用修改", button_type="success", size="sm")
        self.btn_clear_overrides = LayoutManager.create_button_with_style("清空覆盖", button_type="outline", size="sm")
        btns.addWidget(self.btn_apply); btns.addWidget(self.btn_clear_overrides); btns.addStretch(1)
        stent_layout.addLayout(btns)
        self.stent_group.setLayout(stent_layout)
        form_layout.addWidget(self.stent_group)

        form_layout.addStretch(1)
        layout.addWidget(form_container, 1)

        # 连接
        refresh_btn.clicked.connect(self._refresh_preview)
        export_btn.clicked.connect(self._export_html)
        self.btn_apply.clicked.connect(self._apply_changes)
        self.btn_clear_overrides.clicked.connect(self._clear_overrides)

        # 初次加载
        self._refresh_preview()

    def _refresh_preview(self):
        try:
            summary = self.logic.collect_summary()
            base = summary.get('base', {})
            angles = summary.get('angles', {})
            stent = summary.get('stent_assessment') or {}

            # 填充左侧基本情况
            self.lbl_patient.setText(f"{base.get('patientName','')} / {base.get('sex','')} / {base.get('age','')}")
            self.lbl_dates.setText(f"{base.get('surgeryDate','')} / {base.get('ctScanDate','')}")
            self.lbl_valve.setText(f"{base.get('valveBrand','')} {base.get('valveModel','')}")

            # 角度填充
            self.inp_angle_rcc_lcc.setValue(float(angles.get('RCA_to_RCC_LCC', 0.0) or 0.0))
            self.inp_angle_lcc_ncc.setValue(float(angles.get('RCA_to_LCC_NCC', 0.0) or 0.0))
            self.inp_angle_ncc_rcc.setValue(float(angles.get('RCA_to_NCC_RCC', 0.0) or 0.0))

            # 形态改变选择
            morph = stent.get('morphology_changed')
            self.sel_morph.setCurrentIndex(0 if morph is None else (2 if morph else 1))

            # 控制平面显示（Sapien3规则）
            brand = (base.get('valveBrand') or '').strip(); model = (base.get('valveModel') or '').strip()
            is_sapien3 = ('sapien' in model.lower()) or ('sapien' in brand.lower())

            def set_row_visible(phase_key, plane_key, visible):
                w = self.rows.get((phase_key, plane_key))
                if w is not None:
                    w.setVisible(visible)

            for phase_key in ('end_diastole','end_systole'):
                set_row_visible(phase_key, 'inflow', not is_sapien3)
                set_row_visible(phase_key, 'outerskirt', is_sapien3)
                set_row_visible(phase_key, 'nadir', True)
                set_row_visible(phase_key, 'commissure', True)

            # 填充测量值（优先覆盖集成后的summary）
            per_phase = stent.get('per_phase') or {}

            def get_spin(widget, name):
                return widget.findChild(qt.QDoubleSpinBox, name)

            for phase_key, pdata in per_phase.items():
                if not isinstance(pdata, dict):
                    continue
                for plane_key in ('inflow','nadir','outerskirt','commissure'):
                    m = pdata.get(plane_key) or {}
                    w = self.rows.get((phase_key, plane_key))
                    if not w:
                        continue
                    if (sp := get_spin(w, 'ped')): sp.setValue(float(m.get('perimeter_derived_diameter') or 0.0))
                    if (sp := get_spin(w, 'aed')): sp.setValue(float(m.get('area_derived_diameter') or 0.0))
                    if (sp := get_spin(w, 'dmax')): sp.setValue(float(m.get('longest_diameter') or 0.0))
                    if (sp := get_spin(w, 'dmin')): sp.setValue(float(m.get('shortest_diameter') or 0.0))
        except Exception as e:
            logging.error(f"刷新表单失败: {e}")

    # 应用左侧编辑修改到Session
    def _apply_changes(self):
        try:
            # 角度
            self.session.set_commissure_alignment_angles({
                'RCA_to_RCC_LCC': self.inp_angle_rcc_lcc.value(),
                'RCA_to_LCC_NCC': self.inp_angle_lcc_ncc.value(),
                'RCA_to_NCC_RCC': self.inp_angle_ncc_rcc.value(),
            })
            # 形态改变
            idx = self.sel_morph.currentIndex()
            self.session.set_stent_morphology_changed(None if idx == 0 else (True if idx == 2 else False))
            # 覆盖值
            def get_spin(widget, name):
                return widget.findChild(qt.QDoubleSpinBox, name)
            for phase_key in ('end_diastole','end_systole'):
                for plane_key in ('inflow','nadir','outerskirt','commissure'):
                    w = self.rows.get((phase_key, plane_key))
                    if not w or not w.isVisible():
                        continue
                    ped = get_spin(w, 'ped').value()
                    aed = get_spin(w, 'aed').value()
                    dmax = get_spin(w, 'dmax').value()
                    dmin = get_spin(w, 'dmin').value()
                    # 写入覆盖（0视为有效值；若想清空请用“清空覆盖”）
                    self.session.set_stent_measurement_override(phase_key, plane_key, 'perimeter_derived_diameter', ped)
                    self.session.set_stent_measurement_override(phase_key, plane_key, 'area_derived_diameter', aed)
                    self.session.set_stent_measurement_override(phase_key, plane_key, 'longest_diameter', dmax)
                    self.session.set_stent_measurement_override(phase_key, plane_key, 'shortest_diameter', dmin)
            # 刷新
            self._refresh_preview()
        except Exception as e:
            logging.exception("应用修改失败")
            try:
                qt.QMessageBox.critical(self, "失败", str(e))
            except Exception:
                pass

    def _clear_overrides(self):
        try:
            self.session.clear_stent_measurement_override()
            self._refresh_preview()
        except Exception as e:
            logging.exception("清空覆盖失败")

    def _export_html(self):
        try:
            # 选择输出路径
            dlg = qt.QFileDialog(self)
            dlg.setAcceptMode(qt.QFileDialog.AcceptSave)
            dlg.setNameFilter("HTML (*.html)")
            dlg.selectFile("tavr_report.html")
            if not dlg.exec_():
                return
            files = dlg.selectedFiles()
            if not files:
                return
            out_path = files[0]

            result = self.logic.export_html(out_path)
            if result.get("success"):
                qt.QMessageBox.information(self, "导出完成", f"已导出到:\n{result.get('path')}")
            else:
                qt.QMessageBox.critical(self, "导出失败", result.get("message", "未知错误"))
        except Exception as e:
            logging.exception("导出HTML失败")
            try:
                qt.QMessageBox.critical(self, "导出失败", str(e))
            except Exception:
                pass

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if self.logic:
            self.logic.set_session(session)
        self._refresh_preview()

    def on_activated(self):
        self._refresh_preview()

    def on_deactivated(self):
        pass

    def cleanup(self):
        pass
