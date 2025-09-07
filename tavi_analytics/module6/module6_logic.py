"""
模块六逻辑 - 报告生成（干净重建）

职责：从会话收集数据，生成报告HTML，并导出为HTML或PDF（本地Qt或服务器端渲染）。
数值展示统一保留两位小数。
"""
from __future__ import annotations

import os
import json
import base64
import datetime
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

import qt

from core.session import TAVRStudySession

# Feature flag: temporarily hide RELM presentation across report outputs
SHOW_RELM: bool = False


class Module6Logic:
    def __init__(self, session: TAVRStudySession):
        self._session = session

    def set_session(self, session: TAVRStudySession):
        self._session = session

    # ============== 汇总数据收集 ==============
    def collect_summary(self) -> Dict[str, Any]:
        s = self._session
        patient = s.get_patient_data()

        base = {
            "patientID": patient.patientID,
            "patientName": patient.patientName,
            "age": patient.patientAge,
            "sex": patient.patientSex,
            "surgeryDate": self._fmt_date(patient.surgeryDate),
            "ctScanDate": self._fmt_date(patient.ctScanDate),
            "imageQuality": getattr(patient.imageQuality, 'value', str(patient.imageQuality)),
            "followUp": getattr(patient.followUpTimepoint, 'value', str(patient.followUpTimepoint)),
            "valveBrand": patient.valveBrand,
            "valveModel": patient.valveModel,
        }

        phases = s.get_phase_summary()  # {'marked_phases': {...}, ...}
        angles = s.get_commissure_alignment_angles()  # dict 3 angles

        # 支架评估期像测量（含覆盖）
        per_phase = {}
        for phase in ("end_diastole", "end_systole"):
            mgr = None
            try:
                mgr = s.get_phase_contour_manager(phase)
            except Exception:
                mgr = None
            packed = {"phase_percent": (phases.get("marked_phases", {}).get(phase, {}) or {}).get("phase_percent")}
            if mgr:
                level_planes = {}
                try:
                    level_planes = mgr.get_level_planes()  # dict of planes (or None)
                except Exception:
                    level_planes = {}
                def pack_plane(plane):
                    if not plane:
                        return None
                    m = plane.get_measurements() or {}
                    return {
                        'perimeter': m.get('perimeter'),
                        'area': m.get('area'),
                        'perimeter_derived_diameter': m.get('perimeter_derived_diameter'),
                        'area_derived_diameter': m.get('area_derived_diameter'),
                        'longest_diameter': m.get('longest_diameter'),
                        'shortest_diameter': m.get('shortest_diameter'),
                        'average_diameter': m.get('average_diameter'),
                    }
                packed.update({
                    'inflow': pack_plane(level_planes.get('inflow')),
                    'nadir': pack_plane(level_planes.get('nadir')),
                    'commissure': pack_plane(level_planes.get('commissure')),
                })
            per_phase[phase] = packed

        stent_assessment = {
            'morphology_changed': s.get_stent_morphology_changed(),
            'per_phase': per_phase,
        }

        # 模块三汇总
        module3 = s.get_module3_results() or {}

        # 可选：measurement.json 兼容展示（如存在）
        measurements = None
        try:
            root = self._guess_repo_root()
            if root:
                path = os.path.join(root, 'data', 'measurement.json')
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        measurements = json.load(f)
        except Exception:
            measurements = None

        return {
            'base': base,
            'phases': phases,
            'angles': angles,
            'stent_assessment': stent_assessment,
            'module3': module3,
            'measurements': measurements,
        }

    # ============== 导出 ==============
    def export_html(self, out_path: str) -> Dict[str, Any]:
        try:
            data = self.collect_summary()
            # HTML导出保留“几何测量摘要”
            html = self._render_html(data, include_geometry=True)
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            return {"success": True, "path": out_path}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def export_pdf(self, out_path: str) -> Dict[str, Any]:
        try:
            data = self.collect_summary()
            # PDF导出不展示“几何测量摘要”
            html = self._render_html(data, include_geometry=False, include_phases=False, group_leaflet_eval=True)
            doc = qt.QTextDocument(); doc.setHtml(html)
            printer = qt.QPrinter(); printer.setOutputFormat(qt.QPrinter.PdfFormat); printer.setOutputFileName(out_path)
            try:
                printer.setPaperSize(qt.QPrinter.A4)
                printer.setPageMargins(12, 12, 12, 12, qt.QPrinter.Millimeter)
            except Exception:
                pass
            doc.print(printer)
            return {"success": True, "path": out_path}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def export_pdf_via_server(self, out_path: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            server_url = self._get_pdf_server_url_from_config()
            if not server_url:
                return {"success": False, "message": "未配置PDF渲染服务"}
            data = self.collect_summary()
            # 服务器端PDF不展示“几何测量摘要”，并将HALT/RELM/SFD/PFD归入“人工瓣膜瓣叶评估”；同时移除“时相标记”
            html = self._render_html(data, include_geometry=False, include_phases=False, group_leaflet_eval=True)
            req = urllib.request.Request(
                url=server_url.rstrip('/') + '/render/pdf',
                data=json.dumps({
                    'html': html,
                    'format': 'A4',
                    'margin_top': '12mm', 'margin_right': '12mm', 'margin_bottom': '12mm', 'margin_left': '12mm',
                    'print_background': True,
                    'prefer_css_page_size': True,
                    'inline_base64': True,
                }).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode(); body = resp.read()
            if status >= 400:
                return {"success": False, "message": f"渲染服务错误 HTTP {status}"}
            try:
                res = json.loads(body.decode('utf-8'))
            except Exception:
                return {"success": False, "message": "渲染服务返回无法解析"}
            if not res.get('success'):
                return {"success": False, "message": res.get('message', '渲染失败')}
            b64 = res.get('base64')
            if not b64:
                return {"success": False, "message": "渲染服务未返回PDF数据"}
            pdf_bytes = base64.b64decode(b64)
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(pdf_bytes)
            return {"success": True, "path": out_path, "size": len(pdf_bytes)}
        except urllib.error.HTTPError as e:
            return {"success": False, "message": f"HTTP错误: {e.code} {e.reason}"}
        except urllib.error.URLError as e:
            return {"success": False, "message": f"无法连接渲染服务: {e.reason}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ============== HTML渲染 ==============
    def _render_html(self, data: Dict[str, Any], *, include_geometry: bool = True, include_phases: bool = True, group_leaflet_eval: bool = False) -> str:
        b = data.get('base', {})
        phases = data.get('phases', {})
        angles = data.get('angles', {})
        module3 = data.get('module3', {}) or {}
        stent = data.get('stent_assessment') or {}
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        def val(x):
            return "" if x is None else str(x)

        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 16px; }
        h1 { font-size: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
        th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
        th { background: #f9fafb; }
        .section { margin-top: 18px; }
        small { color: #6b7280; }
        .toolbar { display: flex; gap: 8px; align-items: center; margin: 8px 0 16px; }
        .btn { border: 1px solid #e5e7eb; background: #f9fafb; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 13px; }
        .btn-primary { background: #2563eb; color: #fff; border-color: #1d4ed8; }
        .btn:hover { filter: brightness(0.98); }
        @page { size: A4; margin: 12mm; }
        @media print { .no-print { display: none !important; } body { padding: 0; } th { background: #f0f0f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
        """

        base_html = f"""
        <table>
          <tr><th colspan=4>一、基本情况</th></tr>
          <tr><td>受试者编号</td><td>{val(b.get('patientID'))}</td><td>姓名</td><td>{val(b.get('patientName'))}</td></tr>
          <tr><td>年龄</td><td>{val(b.get('age'))}</td><td>性别</td><td>{val(b.get('sex'))}</td></tr>
          <tr><td>手术日期</td><td>{val(b.get('surgeryDate'))}</td><td>CT扫描日期</td><td>{val(b.get('ctScanDate'))}</td></tr>
          <tr><td>图像质量</td><td>{val(b.get('imageQuality'))}</td><td>随访时间点</td><td>{val(b.get('followUp'))}</td></tr>
          <tr><td>瓣膜品牌</td><td>{val(b.get('valveBrand'))}</td><td>瓣膜型号</td><td>{val(b.get('valveModel'))}</td></tr>
        </table>
        """

        angles_html = f"""
        <table>
          <tr><th colspan=4>四、交接对齐（commissure alignment）</th></tr>
          <tr><td>RCA→RCC/LCC</td><td>{self._fmt2(angles.get('RCA_to_RCC_LCC'))} °</td>
              <td>RCA→LCC/NCC</td><td>{self._fmt2(angles.get('RCA_to_LCC_NCC'))} °</td></tr>
          <tr><td>RCA→NCC/RCC</td><td>{self._fmt2(angles.get('RCA_to_NCC_RCC'))} °</td><td></td><td></td></tr>
        </table>
        """

        mp = phases.get('marked_phases', {}) if isinstance(phases, dict) else {}

        def _phase_row(name_key, label):
            p = mp.get(name_key, {})
            return f"<tr><td>{label}帧索引</td><td>{val(p.get('frame_index'))}</td><td>{label}相位%</td><td>{self._fmt2(p.get('phase_percent'))}</td></tr>"

        phase_html = ""
        if include_phases:
            phase_html = f"""
            <table>
              <tr><th colspan=4>二、时相标记</th></tr>
              {_phase_row('end_diastole', '舒张末期')}
              {_phase_row('end_systole', '收缩末期')}
            </table>
            """

        # measurement.json 摘要（可选）
        geo_html = ""
        if include_geometry:
            meas = data.get('measurements') or {}
            if isinstance(meas, dict) and meas:
                rows = []
                for key, m in meas.items():
                    if not isinstance(m, dict):
                        continue
                    rows.append(
                        f"<tr><td>{key}</td><td>{self._fmt2(m.get('perimeter'))}</td><td>{self._fmt2(m.get('area'))}</td>"
                        f"<td>{self._fmt2(m.get('average_diameter'))}</td><td>{self._fmt2(m.get('longest_diameter'))}</td><td>{self._fmt2(m.get('shortest_diameter'))}</td></tr>"
                    )
                geo_html = f"""
                <table>
                  <tr><th colspan=6>三、几何测量摘要</th></tr>
                  <tr><th>平面</th><th>周长(mm)</th><th>面积(mm²)</th><th>平均径(mm)</th><th>最长径(mm)</th><th>最短径(mm)</th></tr>
                  {''.join(rows)}
                </table>
                """

        # PDF路径下（group_leaflet_eval=True且include_phases=False）需要二、三标题
        if group_leaflet_eval and not include_phases:
            module3_html = self._render_leaflet_evaluation(module3, title_prefix="二、")
            stent_html = self._render_stent_assessment_section(stent, b, section_prefix="三、")
        else:
            module3_html = self._render_leaflet_evaluation(module3) if group_leaflet_eval else self._render_module3(module3)
            stent_html = self._render_stent_assessment_section(stent, b)

        return f"""
        <html><head><meta charset='utf-8'><style>{css}</style></head>
        <body>
        <h1>TAVR Analytics 报告 <small>{now}</small></h1>
        <div class='toolbar no-print'>
            <button class='btn btn-primary' onclick=\"window.print()\">下载 PDF</button>
        </div>
        {base_html}
        {phase_html}
        {geo_html}
        {module3_html}
        {stent_html}
        {angles_html}
        </body></html>
        """

    # ============== 子区块渲染 ==============
    def _render_module3(self, m3: Dict[str, Any]) -> str:
        if not m3:
            return ""
        halt = m3.get('halt') or {}
        relm = m3.get('relm') or {}
        sfd = m3.get('sfd') or {}
        pfd = m3.get('pfd') or {}

        halt_rows: list[str] = []
        if halt:
            halt_rows.append(f"<tr><td>HALT整体</td><td colspan=3>{halt.get('overall_status','')}</td></tr>")
            grades = halt.get('leaflet_grades') or {}
            for leaflet in ('LC','RC','NC'):
                if leaflet in grades:
                    halt_rows.append(f"<tr><td>HALT分级 {leaflet}</td><td colspan=3>{grades.get(leaflet)}</td></tr>")

        relm_rows: list[str] = []
        if SHOW_RELM and relm:
            relm_rows.append(f"<tr><td>RELM状态</td><td colspan=3>{relm.get('status','')}</td></tr>")
            if relm.get('leaflet'):
                relm_rows.append(f"<tr><td>RELM瓣叶</td><td colspan=3>{relm.get('leaflet')}</td></tr>")

        sfd_rows: list[str] = []
        if sfd:
            sfd_rows.append(f"<tr><td>SFD状态</td><td colspan=3>{sfd.get('status','')}</td></tr>")
            sinuses = sfd.get('affected_sinuses') or []
            if sinuses:
                sfd_rows.append(f"<tr><td>SFD受累窦</td><td colspan=3>{', '.join(sinuses)}</td></tr>")

        pfd_rows: list[str] = []
        if pfd:
            pfd_rows.append(f"<tr><td>PFD状态</td><td colspan=3>{pfd.get('status','')}</td></tr>")
            if pfd.get('max_thickness') is not None:
                pfd_rows.append(f"<tr><td>PFD最大厚度</td><td colspan=3>{self._fmt2(pfd.get('max_thickness'))} mm</td></tr>")

        blocks: list[str] = []
        if halt_rows:
            blocks.append("<tr><th colspan=4>五、HALT</th></tr>" + ''.join(halt_rows))
        if relm_rows:
            blocks.append("<tr><th colspan=4>六、RELM</th></tr>" + ''.join(relm_rows))
        if sfd_rows:
            blocks.append("<tr><th colspan=4>七、SFD</th></tr>" + ''.join(sfd_rows))
        if pfd_rows:
            blocks.append("<tr><th colspan=4>八、PFD</th></tr>" + ''.join(pfd_rows))
        if not blocks:
            return ""
        return f"<table>{''.join(blocks)}</table>"

    def _render_leaflet_evaluation(self, m3: Dict[str, Any], title_prefix: str = "") -> str:
        """将 HALT/RELM/SFD/PFD 归为一个章节：人工瓣膜瓣叶评估（用于PDF）。"""
        if not m3:
            return ""
        halt = m3.get('halt') or {}
        relm = m3.get('relm') or {}
        sfd = m3.get('sfd') or {}
        pfd = m3.get('pfd') or {}

        rows: list[str] = []

        # HALT
        if halt:
            rows.append("<tr><th colspan=4>HALT</th></tr>")
            rows.append(f"<tr><td>整体</td><td colspan=3>{halt.get('overall_status','')}</td></tr>")
            grades = halt.get('leaflet_grades') or {}
            for leaflet in ('LC','RC','NC'):
                if leaflet in grades:
                    rows.append(f"<tr><td>分级 {leaflet}</td><td colspan=3>{grades.get(leaflet)}</td></tr>")

        # RELM（按开关控制是否渲染）
        if SHOW_RELM and relm:
            rows.append("<tr><th colspan=4>RELM</th></tr>")
            rows.append(f"<tr><td>状态</td><td colspan=3>{relm.get('status','')}</td></tr>")
            if relm.get('leaflet'):
                rows.append(f"<tr><td>受累瓣叶</td><td colspan=3>{relm.get('leaflet')}</td></tr>")

        # SFD
        if sfd:
            rows.append("<tr><th colspan=4>SFD</th></tr>")
            rows.append(f"<tr><td>状态</td><td colspan=3>{sfd.get('status','')}</td></tr>")
            sinuses = sfd.get('affected_sinuses') or []
            if sinuses:
                rows.append(f"<tr><td>受累窦</td><td colspan=3>{', '.join(sinuses)}</td></tr>")

        # PFD
        if pfd:
            rows.append("<tr><th colspan=4>PFD</th></tr>")
            rows.append(f"<tr><td>状态</td><td colspan=3>{pfd.get('status','')}</td></tr>")
            if pfd.get('max_thickness') is not None:
                rows.append(f"<tr><td>最大厚度</td><td colspan=3>{self._fmt2(pfd.get('max_thickness'))} mm</td></tr>")

        if not rows:
            return ""
        title = f"{title_prefix}人工瓣膜瓣叶评估" if title_prefix else "人工瓣膜瓣叶评估"
        return "<table>" \
               f"<tr><th colspan=4>{title}</th></tr>" \
               + ''.join(rows) + "</table>"

    def _render_stent_assessment_section(self, stent: Dict[str, Any], base: Dict[str, Any], section_prefix: str = "") -> str:
        if not stent or not isinstance(stent, dict):
            return ""
        def val(x):
            return "" if x is None else str(x)
        brand = (base or {}).get('valveBrand', '').strip()
        model = (base or {}).get('valveModel', '').strip()
        is_sapien3 = ('sapien' in model.lower()) or ('sapien' in brand.lower())
        morph = stent.get('morphology_changed')
        morph_txt = '有' if morph is True else ('无' if morph is False else '')
        per_phase = stent.get('per_phase') or {}
        header_html = f"<table><tr><th colspan=7>{section_prefix}人工瓣膜支架评估</th></tr></table>" if section_prefix else ""
        def render_phase_table(phase_key: str, phase_label: str) -> str:
            p = per_phase.get(phase_key) or {}
            phase_percent = p.get('phase_percent')
            planes = {
                'inflow': ('支架低端平面 (inflow)', not is_sapien3),
                'nadir': ('支架瓣叶窦底平面 (nadir)', True),
                'outerskirt': ('外裙边平面 (outerskirt)', is_sapien3),
                'commissure': ('支架瓣叶对合平面 (commissure level)', True),
            }
            plane_data = dict(p)
            if 'outerskirt' not in plane_data:
                plane_data['outerskirt'] = None
            rows = []
            header = (
                "<tr><th>平面</th><th>周长(mm)</th><th>周长平均径(mm)</th><th>面积(mm²)</th>"
                "<th>面积平均径(mm)</th><th>最长径(mm)</th><th>最短径(mm)</th></tr>"
            )
            for key, (label, show) in planes.items():
                if not show:
                    continue
                m = plane_data.get(key)
                if not m:
                    rows.append(f"<tr><td>{label}</td><td colspan=6></td></tr>")
                else:
                    rows.append(
                        "<tr>"
                        f"<td>{label}</td>"
                        f"<td>{self._fmt2(m.get('perimeter'))}</td>"
                        f"<td>{self._fmt2(m.get('perimeter_derived_diameter'))}</td>"
                        f"<td>{self._fmt2(m.get('area'))}</td>"
                        f"<td>{self._fmt2(m.get('area_derived_diameter'))}</td>"
                        f"<td>{self._fmt2(m.get('longest_diameter'))}</td>"
                        f"<td>{self._fmt2(m.get('shortest_diameter'))}</td>"
                        "</tr>"
                    )
            title = f"人工瓣膜支架评估（{phase_label}，测量期相: {self._fmt2(phase_percent)}%）"
            morph_line = f"<tr><td>是否存在人工瓣膜形态改变</td><td colspan=6>{morph_txt}</td></tr>" if morph_txt else ""
            return (
                "<table>"
                f"<tr><th colspan=7>{title}</th></tr>"
                f"{morph_line}"
                f"{header}{''.join(rows)}"
                "</table>"
            )
        parts = [
            render_phase_table('end_diastole', '舒张末期'),
            render_phase_table('end_systole', '收缩末期'),
        ]
        return header_html + ''.join(parts)

    # ============== 工具方法 ==============
    def _fmt_date(self, d):
        try:
            if d:
                return d.strftime('%Y-%m-%d')
        except Exception:
            pass
        return ""

    def _fmt2(self, x: Any) -> str:
        if x is None:
            return ""
        try:
            if isinstance(x, (int, float)):
                return f"{x:.2f}"
            xs = str(x).strip()
            return f"{float(xs):.2f}"
        except Exception:
            return str(x)

    def _guess_repo_root(self) -> Optional[str]:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    def _get_pdf_server_url_from_config(self) -> Optional[str]:
        try:
            root = self._guess_repo_root()
            if not root:
                return None
            cfg_path = os.path.join(root, 'tavi_analytics', 'config.json')
            if not os.path.exists(cfg_path):
                return None
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            return (
                (cfg.get('services') or {}).get('pdf_server_url')
                or (cfg.get('server') or {}).get('pdf_server_url')
                or None
            )
        except Exception:
            return None
