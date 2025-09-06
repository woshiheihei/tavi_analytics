"""
模块六界面 - 报告生成页面

功能:
- 预览关键字段（与样例表单一致的分区）
- 一键导出HTML报告到用户选择的文件
"""
import os
import logging
from typing import Optional
import qt

from core.session import TAVRStudySession
from utils.layout_manager import LayoutManager, LayoutType
from ui.styles import StyleManager
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

            # 预览文本（简单显示关键摘要）
            self.preview = qt.QTextEdit()
            self.preview.setReadOnly(True)
            # 使用输入框样式作为代码/文本预览的基础样式
            self.preview.setStyleSheet(StyleManager.get_input_style())
            layout.addWidget(self.preview)
            layout.addStretch()

            # 连接
            refresh_btn.clicked.connect(self._refresh_preview)
            export_btn.clicked.connect(self._export_html)

            # 初次加载
            self._refresh_preview()

    def _refresh_preview(self):
        try:
            summary = self.logic.collect_summary()
            # 以更友好的排版渲染到预览（只做文本预览，导出用HTML模板）
            base = summary.get('base', {})
            angles = summary.get('angles', {})
            m3 = summary.get('module3') or {}
            stent = summary.get('stent_assessment') or {}
            lines = []
            lines.append("一、基本情况")
            lines.append(f"  • 受试者编号: {base.get('patientID','')}")
            lines.append(f"  • 姓名/性别/年龄: {base.get('patientName','')} / {base.get('sex','')} / {base.get('age','')}")
            lines.append(f"  • 手术/CT日期: {base.get('surgeryDate','')} / {base.get('ctScanDate','')}")
            lines.append(f"  • 瓣膜: {base.get('valveBrand','')} {base.get('valveModel','')}")
            lines.append("")
            lines.append("二、交接对齐角度")
            lines.append(f"  • RCA→RCC/LCC: {angles.get('RCA_to_RCC_LCC', '')}°")
            lines.append(f"  • RCA→LCC/NCC: {angles.get('RCA_to_LCC_NCC', '')}°")
            lines.append(f"  • RCA→NCC/RCC: {angles.get('RCA_to_NCC_RCC', '')}°")
            # 模块三概览
            if any(m3.get(k) for k in ('halt','relm','sfd','pfd')):
                lines.append("")
                lines.append("三、模块三（瓣叶功能评估）")
                halt = m3.get('halt') or {}
                if halt:
                    lines.append(f"  • HALT整体: {halt.get('overall_status','')}")
                    lg = halt.get('leaflet_grades') or {}
                    if lg:
                        lines.append(f"    - LC/RC/NC: {lg.get('LC','-')} / {lg.get('RC','-')} / {lg.get('NC','-')}")
                relm = m3.get('relm') or {}
                if relm:
                    lines.append(f"  • RELM: {relm.get('status','')}, 瓣叶: {relm.get('leaflet','')}")
                sfd = m3.get('sfd') or {}
                if sfd:
                    lines.append(f"  • SFD: {sfd.get('status','')}, 受累窦: {', '.join(sfd.get('affected_sinuses') or [])}")
                pfd = m3.get('pfd') or {}
                if pfd:
                    lines.append(f"  • PFD: {pfd.get('status','')}, 最大厚度: {pfd.get('max_thickness') if pfd.get('max_thickness') is not None else '-'} mm")

            # 简要：人工瓣膜支架评估（新增预览）
            try:
                lines.append("")
                lines.append("四、人工瓣膜支架评估（简要）")
                morph = stent.get('morphology_changed')
                morph_txt = '有' if morph is True else ('无' if morph is False else '未填写')
                lines.append(f"  • 是否存在人工瓣膜形态改变: {morph_txt}")
                per_phase = stent.get('per_phase') or {}
                brand = (base.get('valveBrand') or '').strip()
                model = (base.get('valveModel') or '').strip()
                is_sapien3 = ('sapien' in model.lower()) or ('sapien' in brand.lower())

                def add_phase_block(key: str, label: str):
                    p = per_phase.get(key) or {}
                    pp = p.get('phase_percent')
                    lines.append(f"  • {label} (测量期相: {pp if pp is not None else '-'}%)")
                    # 平面依次：inflow(非Sapien3显示)、nadir、outerskirt(Sapien3显示)、commissure
                    plane_defs = [
                        ('inflow', '支架低端(inflow)', (not is_sapien3)),
                        ('nadir', '窦底(nadir)', True),
                        ('outerskirt', '外裙边(outerskirt)', is_sapien3),
                        ('commissure', '对合平面(commissure)', True),
                    ]
                    for k, label_cn, show in plane_defs:
                        if not show:
                            continue
                        m = p.get(k)
                        if not m:
                            continue
                        ped = m.get('perimeter_derived_diameter')
                        aed = m.get('area_derived_diameter')
                        dmax = m.get('longest_diameter')
                        dmin = m.get('shortest_diameter')
                        lines.append(
                            f"    - {label_cn}: PED {ped if ped is not None else '-'} mm, "
                            f"AED {aed if aed is not None else '-'} mm, Dmax {dmax if dmax is not None else '-'} mm, Dmin {dmin if dmin is not None else '-'} mm"
                        )

                add_phase_block('end_diastole', '舒张末期')
                add_phase_block('end_systole', '收缩末期')
            except Exception:
                pass
            self.preview.setPlainText("\n".join(lines))
        except Exception as e:
            logging.error(f"刷新报告预览失败: {e}")
            self.preview.setPlainText(f"刷新失败: {e}")

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
