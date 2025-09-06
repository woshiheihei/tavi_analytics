"""
模块六界面 - 报告生成页面（重构为卡片化、专业风格，无右侧预览）

设计要点：
- 参考模块三的 SectionCard 风格，采用卡片式分区，清晰、简洁、专业
- 单列布局，顶部为动作区，下面依次为各 Section（基本情况 / 对齐角度 / 支架评估 / 报告摘要）
- 不使用右侧预览；改为底部“报告摘要”卡片，以便快速总览（可选）
"""
import logging
from typing import Optional
import qt

from core.session import TAVRStudySession
from utils.layout_manager import LayoutManager, LayoutType
from ui.styles import StyleManager
from widgets.section_card import SectionCard
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

        # 顶部动作区（工具栏风格按钮）
        actions = qt.QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        refresh_btn = LayoutManager.create_button_with_style("刷新", button_type="toolbar", size="sm", min_height=28)
        export_btn = LayoutManager.create_button_with_style("导出HTML", button_type="toolbar", size="sm", min_height=28)
        actions.addWidget(refresh_btn)
        actions.addStretch(1)
        actions.addWidget(export_btn)
        layout.addLayout(actions)

        # 审核表单（全宽）
        form_container = qt.QWidget()
        form_layout = qt.QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # Section A: 基本情况（只读） - SectionCard（逐行展示）
        base_card = SectionCard(title="一、基本情况", icon_text="🧾", variant="dashed", parent=self)
        base_form = qt.QFormLayout()
        base_form.setContentsMargins(0, 0, 0, 0)
        base_form.setSpacing(6)
        # 值标签
        self.lbl_patient_id = qt.QLabel(); self.lbl_patient_id.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_patient_name = qt.QLabel(); self.lbl_patient_name.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_sex = qt.QLabel(); self.lbl_sex.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_age = qt.QLabel(); self.lbl_age.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_surgery_date = qt.QLabel(); self.lbl_surgery_date.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_ct_date = qt.QLabel(); self.lbl_ct_date.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_valve_brand = qt.QLabel(); self.lbl_valve_brand.setStyleSheet(StyleManager.get_label_style("default"))
        self.lbl_valve_model = qt.QLabel(); self.lbl_valve_model.setStyleSheet(StyleManager.get_label_style("default"))

        # 逐行添加
        base_form.addRow(qt.QLabel("受试者编号"), self.lbl_patient_id)
        base_form.addRow(qt.QLabel("姓名"), self.lbl_patient_name)
        base_form.addRow(qt.QLabel("性别"), self.lbl_sex)
        base_form.addRow(qt.QLabel("年龄"), self.lbl_age)
        base_form.addRow(qt.QLabel("手术日期"), self.lbl_surgery_date)
        base_form.addRow(qt.QLabel("CT日期"), self.lbl_ct_date)
        base_form.addRow(qt.QLabel("瓣膜品牌"), self.lbl_valve_brand)
        base_form.addRow(qt.QLabel("瓣膜型号"), self.lbl_valve_model)
        base_card.add_layout(base_form)
        form_layout.addWidget(base_card)

        # Section B: 瓣膜功能评估（只读） - SectionCard（统一两列排版：每行两组“标签-数值”对）
        valve_func_card = SectionCard(title="二、瓣膜功能评估", variant="dashed", parent=self)
        valve_func_layout = qt.QVBoxLayout()
        valve_func_layout.setSpacing(16)

        # 统一字段样式
        label_style = "QLabel { font-weight: 500; color: #495057; min-width: 88px; }"
        data_field_style = """
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """

        # HALT分析
        halt_container = qt.QWidget()
        halt_main_layout = qt.QVBoxLayout(halt_container)
        halt_main_layout.setContentsMargins(16, 12, 16, 12)
        halt_main_layout.setSpacing(10)

        halt_title = qt.QLabel("HALT (高度衰减瓣叶增厚)")
        halt_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                padding: 6px 0px;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 10px;
            }
        """)
        halt_main_layout.addWidget(halt_title)

        halt_grid = qt.QGridLayout()
        halt_grid.setSpacing(10)
        halt_grid.setColumnStretch(1, 1)
        halt_grid.setColumnStretch(3, 1)

        # 整体状态（仅一组，右侧留空以保持两组对齐）
        overall_lbl = qt.QLabel("整体状态"); overall_lbl.setStyleSheet(label_style)
        self.lbl_halt_overall = qt.QLabel(); self.lbl_halt_overall.setStyleSheet(data_field_style)
        halt_grid.addWidget(overall_lbl, 0, 0)
        halt_grid.addWidget(self.lbl_halt_overall, 0, 1)
        halt_grid.addWidget(qt.QLabel(""), 0, 2)
        halt_grid.addWidget(qt.QLabel(""), 0, 3)

        # 瓣叶分级（两组一行）
        lc_lbl = qt.QLabel("左冠 (LC)"); lc_lbl.setStyleSheet(label_style)
        self.lbl_halt_lc = qt.QLabel(); self.lbl_halt_lc.setStyleSheet(data_field_style)
        rc_lbl = qt.QLabel("右冠 (RC)"); rc_lbl.setStyleSheet(label_style)
        self.lbl_halt_rc = qt.QLabel(); self.lbl_halt_rc.setStyleSheet(data_field_style)
        nc_lbl = qt.QLabel("无冠 (NC)"); nc_lbl.setStyleSheet(label_style)
        self.lbl_halt_nc = qt.QLabel(); self.lbl_halt_nc.setStyleSheet(data_field_style)

        halt_grid.addWidget(lc_lbl, 1, 0)
        halt_grid.addWidget(self.lbl_halt_lc, 1, 1)
        halt_grid.addWidget(rc_lbl, 1, 2)
        halt_grid.addWidget(self.lbl_halt_rc, 1, 3)
        halt_grid.addWidget(nc_lbl, 2, 0)
        halt_grid.addWidget(self.lbl_halt_nc, 2, 1)
        halt_grid.addWidget(qt.QLabel(""), 2, 2)
        halt_grid.addWidget(qt.QLabel(""), 2, 3)

        halt_main_layout.addLayout(halt_grid)
        valve_func_layout.addWidget(halt_container)

        # RELM分析（同样采用两组一行）
        relm_container = qt.QWidget()
        relm_main_layout = qt.QVBoxLayout(relm_container)
        relm_main_layout.setContentsMargins(16, 12, 16, 12)
        relm_main_layout.setSpacing(10)

        relm_title = qt.QLabel("RELM (瓣叶活动度减退)")
        relm_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                padding: 6px 0px;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 10px;
            }
        """)
        relm_main_layout.addWidget(relm_title)

        relm_grid = qt.QGridLayout()
        relm_grid.setSpacing(10)
        relm_grid.setColumnStretch(1, 1)
        relm_grid.setColumnStretch(3, 1)

        relm_status_lbl = qt.QLabel("状态"); relm_status_lbl.setStyleSheet(label_style)
        self.lbl_relm_status = qt.QLabel(); self.lbl_relm_status.setStyleSheet(data_field_style)
        relm_leaflet_lbl = qt.QLabel("受累瓣叶"); relm_leaflet_lbl.setStyleSheet(label_style)
        self.lbl_relm_leaflet = qt.QLabel(); self.lbl_relm_leaflet.setStyleSheet(data_field_style)

        relm_grid.addWidget(relm_status_lbl, 0, 0)
        relm_grid.addWidget(self.lbl_relm_status, 0, 1)
        relm_grid.addWidget(relm_leaflet_lbl, 0, 2)
        relm_grid.addWidget(self.lbl_relm_leaflet, 0, 3)

        relm_main_layout.addLayout(relm_grid)
        valve_func_layout.addWidget(relm_container)

        # 充盈缺损分析（两行，每行两组）
        filling_container = qt.QWidget()
        filling_main_layout = qt.QVBoxLayout(filling_container)
        filling_main_layout.setContentsMargins(16, 12, 16, 12)
        filling_main_layout.setSpacing(10)

        filling_title = qt.QLabel("充盈缺损分析")
        filling_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                padding: 6px 0px;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 10px;
            }
        """)
        filling_main_layout.addWidget(filling_title)

        filling_grid = qt.QGridLayout()
        filling_grid.setSpacing(10)
        filling_grid.setColumnStretch(1, 1)
        filling_grid.setColumnStretch(3, 1)

        # 第1行：SFD状态 & PFD状态
        sfd_status_lbl = qt.QLabel("SFD 状态"); sfd_status_lbl.setStyleSheet(label_style)
        self.lbl_sfd_status = qt.QLabel(); self.lbl_sfd_status.setStyleSheet(data_field_style)
        pfd_status_lbl = qt.QLabel("PFD 状态"); pfd_status_lbl.setStyleSheet(label_style)
        self.lbl_pfd_status = qt.QLabel(); self.lbl_pfd_status.setStyleSheet(data_field_style)

        filling_grid.addWidget(sfd_status_lbl, 0, 0)
        filling_grid.addWidget(self.lbl_sfd_status, 0, 1)
        filling_grid.addWidget(pfd_status_lbl, 0, 2)
        filling_grid.addWidget(self.lbl_pfd_status, 0, 3)

        # 第2行：SFD受累窦 & PFD最大厚度
        sfd_sinuses_lbl = qt.QLabel("SFD 受累窦"); sfd_sinuses_lbl.setStyleSheet(label_style)
        self.lbl_sfd_sinuses = qt.QLabel(); self.lbl_sfd_sinuses.setStyleSheet(data_field_style)
        pfd_thickness_lbl = qt.QLabel("PFD 最大厚度"); pfd_thickness_lbl.setStyleSheet(label_style)
        self.lbl_pfd_thickness = qt.QLabel(); self.lbl_pfd_thickness.setStyleSheet(data_field_style)

        filling_grid.addWidget(sfd_sinuses_lbl, 1, 0)
        filling_grid.addWidget(self.lbl_sfd_sinuses, 1, 1)
        filling_grid.addWidget(pfd_thickness_lbl, 1, 2)
        filling_grid.addWidget(self.lbl_pfd_thickness, 1, 3)

        filling_main_layout.addLayout(filling_grid)
        valve_func_layout.addWidget(filling_container)

        valve_func_card.add_layout(valve_func_layout)
        form_layout.addWidget(valve_func_card)

        # Section C: 人工瓣膜支架评估（可编辑） - SectionCard
        stent_card = SectionCard(title="三、人工瓣膜支架评估", icon_text="🫀", variant="dashed", parent=self)
        stent_layout = qt.QVBoxLayout()

        # 形态改变评估
        morph_group = qt.QGroupBox("形态改变评估")
        morph_layout = qt.QFormLayout(morph_group)
        morph_layout.setSpacing(8)
        self.sel_morph = qt.QComboBox()
        self.sel_morph.addItems(["未填写", "无形态改变", "存在形态改变"])
        morph_layout.addRow(qt.QLabel("人工瓣膜形态是否改变:"), self.sel_morph)
        stent_layout.addWidget(morph_group)

        # 测量数据编辑：两期像
        measurement_group = qt.QGroupBox("测量数据")
        measurement_layout = qt.QVBoxLayout(measurement_group)
        self._phase_tabs = qt.QTabWidget()

        for phase_key, phase_label in (("end_diastole","舒张末期"),("end_systole","收缩末期")):
            tab = qt.QWidget()
            tab_layout = qt.QVBoxLayout(tab)
            tab_layout.setSpacing(12)

            # 为四种平面创建行（按Sapien3规则由刷新时控制显示）
            def mk_measurement_section(plane_key, plane_label):
                # 创建平面分组
                plane_group = qt.QGroupBox(plane_label)
                plane_layout = qt.QGridLayout(plane_group)
                plane_layout.setSpacing(8)

                # 创建测量值输入框
                ped = qt.QDoubleSpinBox()
                ped.setRange(0, 200)
                ped.setDecimals(3)
                ped.setSuffix(" mm")
                ped.setObjectName("ped")

                aed = qt.QDoubleSpinBox()
                aed.setRange(0, 200)
                aed.setDecimals(3)
                aed.setSuffix(" mm")
                aed.setObjectName("aed")

                dmax = qt.QDoubleSpinBox()
                dmax.setRange(0, 200)
                dmax.setDecimals(3)
                dmax.setSuffix(" mm")
                dmax.setObjectName("dmax")

                dmin = qt.QDoubleSpinBox()
                dmin.setRange(0, 200)
                dmin.setDecimals(3)
                dmin.setSuffix(" mm")
                dmin.setObjectName("dmin")

                # 使用网格布局，2列4行
                plane_layout.addWidget(qt.QLabel("周长衍生直径 (PED):"), 0, 0)
                plane_layout.addWidget(ped, 0, 1)
                plane_layout.addWidget(qt.QLabel("面积衍生直径 (AED):"), 1, 0)
                plane_layout.addWidget(aed, 1, 1)
                plane_layout.addWidget(qt.QLabel("最大直径 (Dmax):"), 2, 0)
                plane_layout.addWidget(dmax, 2, 1)
                plane_layout.addWidget(qt.QLabel("最小直径 (Dmin):"), 3, 0)
                plane_layout.addWidget(dmin, 3, 1)

                return plane_group

            self.rows = getattr(self, 'rows', {})
            for plane_key, plane_label in (
                ("inflow","支架低端 (Inflow)"),
                ("nadir","窦底 (Nadir)"),
                ("outerskirt","外裙边 (Outerskirt)"),
                ("commissure","对合平面 (Commissure)")
            ):
                plane_widget = mk_measurement_section(plane_key, plane_label)
                tab_layout.addWidget(plane_widget)
                self.rows[(phase_key, plane_key)] = plane_widget

            tab_layout.addStretch(1)
            self._phase_tabs.addTab(tab, phase_label)

        measurement_layout.addWidget(self._phase_tabs)
        stent_layout.addWidget(measurement_group)

        stent_card.add_layout(stent_layout)
        form_layout.addWidget(stent_card)

        # Section D: 交接对齐角度（可编辑） - SectionCard（移动至最后）
        angles_card = SectionCard(title="四、交接对齐角度（°）", icon_text="🧭", variant="dashed", parent=self)
        ang_form = qt.QFormLayout()
        ang_form.setContentsMargins(0, 0, 0, 0)
        ang_form.setSpacing(6)
        self.inp_angle_rcc_lcc = qt.QDoubleSpinBox(); self.inp_angle_rcc_lcc.setRange(0,360); self.inp_angle_rcc_lcc.setDecimals(1); self.inp_angle_rcc_lcc.setSuffix(" °")
        self.inp_angle_lcc_ncc = qt.QDoubleSpinBox(); self.inp_angle_lcc_ncc.setRange(0,360); self.inp_angle_lcc_ncc.setDecimals(1); self.inp_angle_lcc_ncc.setSuffix(" °")
        self.inp_angle_ncc_rcc = qt.QDoubleSpinBox(); self.inp_angle_ncc_rcc.setRange(0,360); self.inp_angle_ncc_rcc.setDecimals(1); self.inp_angle_ncc_rcc.setSuffix(" °")
        ang_form.addRow(qt.QLabel("RCA→RCC/LCC"), self.inp_angle_rcc_lcc)
        ang_form.addRow(qt.QLabel("RCA→LCC/NCC"), self.inp_angle_lcc_ncc)
        ang_form.addRow(qt.QLabel("RCA→NCC/RCC"), self.inp_angle_ncc_rcc)
        angles_card.add_layout(ang_form)
        form_layout.addWidget(angles_card)

        # 底部操作区：与交接对齐角度统一，放置“应用修改 / 清空覆盖”
        sep = qt.QFrame(); sep.setFrameShape(qt.QFrame.HLine); sep.setFrameShadow(qt.QFrame.Sunken)
        form_layout.addWidget(sep)
        bottom_actions = qt.QHBoxLayout()
        bottom_actions.setSpacing(8)
        self.btn_apply = LayoutManager.create_button_with_style("应用修改", button_type="toolbar", size="sm", min_height=28)
        self.btn_clear_overrides = LayoutManager.create_button_with_style("清空覆盖", button_type="toolbar", size="sm", min_height=28)
        bottom_actions.addWidget(self.btn_apply)
        bottom_actions.addWidget(self.btn_clear_overrides)
        bottom_actions.addStretch(1)
        form_layout.addLayout(bottom_actions)

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

            # 填充基本情况（逐行）
            self.lbl_patient_id.setText(f"{base.get('patientID','')}")
            self.lbl_patient_name.setText(f"{base.get('patientName','')}")
            self.lbl_sex.setText(f"{base.get('sex','')}")
            self.lbl_age.setText(f"{base.get('age','')}")
            self.lbl_surgery_date.setText(f"{base.get('surgeryDate','')}")
            self.lbl_ct_date.setText(f"{base.get('ctScanDate','')}")
            self.lbl_valve_brand.setText(f"{base.get('valveBrand','')}")
            self.lbl_valve_model.setText(f"{base.get('valveModel','')}")

            # 角度填充
            self.inp_angle_rcc_lcc.setValue(float(angles.get('RCA_to_RCC_LCC', 0.0) or 0.0))
            self.inp_angle_lcc_ncc.setValue(float(angles.get('RCA_to_LCC_NCC', 0.0) or 0.0))
            self.inp_angle_ncc_rcc.setValue(float(angles.get('RCA_to_NCC_RCC', 0.0) or 0.0))

            # 瓣膜功能评估（模块三结果）
            module3 = summary.get('module3', {}) or {}
            
            # HALT分析结果
            halt = module3.get('halt', {}) or {}
            self.lbl_halt_overall.setText(halt.get('overall_status', ''))
            halt_grades = halt.get('leaflet_grades', {}) or {}
            self.lbl_halt_lc.setText(halt_grades.get('LC', ''))
            self.lbl_halt_rc.setText(halt_grades.get('RC', ''))
            self.lbl_halt_nc.setText(halt_grades.get('NC', ''))

            # RELM分析结果
            relm = module3.get('relm', {}) or {}
            self.lbl_relm_status.setText(relm.get('status', ''))
            self.lbl_relm_leaflet.setText(relm.get('leaflet', ''))

            # SFD分析结果
            sfd = module3.get('sfd', {}) or {}
            self.lbl_sfd_status.setText(sfd.get('status', ''))
            sfd_sinuses = sfd.get('affected_sinuses', [])
            if isinstance(sfd_sinuses, list):
                self.lbl_sfd_sinuses.setText(', '.join(sfd_sinuses))
            else:
                self.lbl_sfd_sinuses.setText(str(sfd_sinuses) if sfd_sinuses else '')

            # PFD分析结果  
            pfd = module3.get('pfd', {}) or {}
            self.lbl_pfd_status.setText(pfd.get('status', ''))
            pfd_thickness = pfd.get('max_thickness')
            if pfd_thickness is not None:
                self.lbl_pfd_thickness.setText(f"{pfd_thickness} mm")
            else:
                self.lbl_pfd_thickness.setText('')

            # 形态改变
            morph = stent.get('morphology_changed')
            if morph is None:
                self.sel_morph.setCurrentIndex(0)  # 未填写
            elif morph:
                self.sel_morph.setCurrentIndex(2)  # 存在形态改变
            else:
                self.sel_morph.setCurrentIndex(1)  # 无形态改变

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

            # 移除报告摘要生成与显示（不保留右侧或底部预览）
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
            if idx == 0:
                self.session.set_stent_morphology_changed(None)  # 未填写
            elif idx == 1:
                self.session.set_stent_morphology_changed(False)  # 无形态改变
            else:
                self.session.set_stent_morphology_changed(True)  # 存在形态改变
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
