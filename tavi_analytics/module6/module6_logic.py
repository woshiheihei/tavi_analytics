"""
模块六逻辑 - 报告生成

负责从会话中收集信息，汇总 measurement.json/几何测量结果、瓣膜品牌型号、期像标记、
以及模块五中的交接对齐角度，生成可预览/导出的HTML报告。
"""
from __future__ import annotations

import json
import os
import datetime
from typing import Dict, Any, Optional

from core.session import TAVRStudySession


class Module6Logic:
    """报告生成逻辑

    Contract:
    - Input: TAVRStudySession (singleton)
    - Output: dict summary for UI preview; HTML export file
    - Error modes: missing session fields handled gracefully
    """

    def __init__(self, session: TAVRStudySession):
        self._session = session

    def set_session(self, session: TAVRStudySession):
        self._session = session

    # 数据收集
    def collect_summary(self) -> Dict[str, Any]:
        s = self._session
        patient = s.get_patient_data()

        # 基本信息
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

        # 时相标记
        phases = s.get_phase_summary()

        # 几何测量（来自各期像的多层级平面管理器）：按期像汇总 inflow/nadir/commissure
        planes_summary = s.get_planes_summary()
        per_phase = {}
        try:
            # 遍历两期像
            for phase in ('end_diastole', 'end_systole'):
                try:
                    mgr = s.get_phase_contour_manager(phase)
                    if not mgr:
                        per_phase[phase] = None
                        continue
                    level_planes = mgr.get_level_planes()  # {'inflow': plane|None, 'nadir': plane|None, 'commissure': plane|None}
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
                            'height': getattr(plane, 'height', None),
                            'level_type': getattr(plane, 'level_type', None),
                        }
                    per_phase[phase] = {
                        'inflow': pack_plane(level_planes.get('inflow')),
                        'nadir': pack_plane(level_planes.get('nadir')),
                        'commissure': pack_plane(level_planes.get('commissure')),
                        # 期相百分比（若有）
                        'phase_percent': (s.get_marked_phase(phase) or {}).get('phase_percent')
                    }
                except Exception:
                    per_phase[phase] = None
        except Exception:
            per_phase = {}

        # 兼容旧接口：保留全部测量平面聚合（如有）
        all_measurements = s.get_all_plane_measurements() or {}

        # 交接对齐角度（模块五保存于session）
        commissure_angles = s.get_commissure_alignment_angles()

        # 模块三分析结果（HALT/RELM/SFD/PFD）
        module3 = {}
        try:
            if hasattr(s, 'get_module3_results'):
                module3 = s.get_module3_results() or {}
        except Exception:
            module3 = {}

        # 度量JSON若存在于项目 data/measurement.json，加载一次（可为空）
        measurement_json: Optional[Dict[str, Any]] = None
        try:
            # 尝试从仓库 data 目录读取（供离线报告演示）
            repo_root = self._guess_repo_root()
            if repo_root:
                path = os.path.join(repo_root, 'data', 'measurement.json')
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        measurement_json = json.load(f)
        except Exception:
            measurement_json = None

        return {
            "base": base,
            "phases": phases,
            "planes": planes_summary,
            "measurements": all_measurements,
            "stent_assessment": {
                "per_phase": per_phase,
                "morphology_changed": s.get_stent_morphology_changed(),
            },
            "angles": commissure_angles,
            "module3": module3,
            "raw_measurement_json": measurement_json,
        }

    def export_html(self, out_path: str) -> Dict[str, Any]:
        """导出HTML报告。

        模板为简约表格，字段参考用户提供的样例表单；若某些数据缺失则留空。
        """
        data = self.collect_summary()
        html = self._render_html(data)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return {"success": True, "path": out_path}

    # ------- 内部帮助 ------
    def _fmt_date(self, d):
        try:
            if d:
                return d.strftime('%Y-%m-%d')
        except Exception:
            pass
        return ""

    def _guess_repo_root(self) -> Optional[str]:
        # 以本文件向上两级为仓库根
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    def _safe_get(self, obj: Dict[str, Any], *keys, default: Any = ""):
        cur = obj
        try:
            for k in keys:
                cur = cur.get(k, {})
            if isinstance(cur, dict):
                return default
            return cur
        except Exception:
            return default

    def _render_html(self, data: Dict[str, Any]) -> str:
        b = data.get('base', {})
        phases = data.get('phases', {})
        angles = data.get('angles', {})
        module3 = data.get('module3', {}) or {}
        stent = data.get('stent_assessment') or {}
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        # 辅助函数
        def val(x):
            return "" if x is None else str(x)

        # 简洁CSS
        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 16px; }
        h1 { font-size: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
        th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
        th { background: #f9fafb; }
        .section { margin-top: 18px; }
        small { color: #6b7280; }
        """

        # 基本信息
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

        # 交接对齐角度
        angles_html = f"""
        <table>
          <tr><th colspan=4>四、交接对齐 (Commissure alignment)</th></tr>
          <tr><td>RCA→RCC/LCC</td><td>{val(angles.get('RCA_to_RCC_LCC'))} °</td>
              <td>RCA→LCC/NCC</td><td>{val(angles.get('RCA_to_LCC_NCC'))} °</td></tr>
          <tr><td>RCA→NCC/RCC</td><td>{val(angles.get('RCA_to_NCC_RCC'))} °</td><td></td><td></td></tr>
        </table>
        """

        # 期像信息
        mp = phases.get('marked_phases', {}) if isinstance(phases, dict) else {}

        def _phase_row(name_key, label):
            p = mp.get(name_key, {})
            return f"<tr><td>{label}帧索引</td><td>{val(p.get('frame_index'))}</td><td>{label}相位%</td><td>{val(p.get('phase_percent'))}</td></tr>"

        phase_html = f"""
        <table>
          <tr><th colspan=4>二、时相标记</th></tr>
          {_phase_row('end_diastole', '舒张末期')}
          {_phase_row('end_systole', '收缩末期')}
        </table>
        """

        # 简要几何汇总（若已加载）
        geo_html = ""
        meas = data.get('measurements') or {}
        if meas:
            # 展示常用平面字段
            rows = []
            for key, m in meas.items():
                if not isinstance(m, dict):
                    continue
                rows.append(
                    f"<tr><td>{key}</td><td>{val(m.get('perimeter'))}</td><td>{val(m.get('area'))}</td>"
                    f"<td>{val(m.get('average_diameter'))}</td><td>{val(m.get('longest_diameter'))}</td><td>{val(m.get('shortest_diameter'))}</td></tr>"
                )
            geo_html = f"""
            <table>
              <tr><th colspan=6>三、几何测量摘要</th></tr>
              <tr><th>平面</th><th>周长(mm)</th><th>面积(mm²)</th><th>平均径(mm)</th><th>最长径(mm)</th><th>最短径(mm)</th></tr>
              {''.join(rows)}
            </table>
            """

        # 模块三（HALT/RELM/SFD/PFD）
        def _render_module3(m3: dict) -> str:
            if not m3:
                return ""
            halt = m3.get('halt') or {}
            relm = m3.get('relm') or {}
            sfd = m3.get('sfd') or {}
            pfd = m3.get('pfd') or {}

            # HALT
            halt_rows = []
            if halt:
                halt_rows.append(f"<tr><td>HALT整体</td><td colspan=3>{halt.get('overall_status','')}</td></tr>")
                grades = halt.get('leaflet_grades') or {}
                for leaflet in ('LC','RC','NC'):
                    if leaflet in grades:
                        halt_rows.append(f"<tr><td>HALT分级 {leaflet}</td><td colspan=3>{grades.get(leaflet)}</td></tr>")

            # RELM
            relm_rows = []
            if relm:
                relm_rows.append(f"<tr><td>RELM状态</td><td colspan=3>{relm.get('status','')}</td></tr>")
                if relm.get('leaflet'):
                    relm_rows.append(f"<tr><td>RELM瓣叶</td><td colspan=3>{relm.get('leaflet')}</td></tr>")

            # SFD
            sfd_rows = []
            if sfd:
                sfd_rows.append(f"<tr><td>SFD状态</td><td colspan=3>{sfd.get('status','')}</td></tr>")
                sinuses = sfd.get('affected_sinuses') or []
                if sinuses:
                    sfd_rows.append(f"<tr><td>SFD受累窦</td><td colspan=3>{', '.join(sinuses)}</td></tr>")

            # PFD
            pfd_rows = []
            if pfd:
                pfd_rows.append(f"<tr><td>PFD状态</td><td colspan=3>{pfd.get('status','')}</td></tr>")
                if pfd.get('max_thickness') is not None:
                    pfd_rows.append(f"<tr><td>PFD最大厚度</td><td colspan=3>{pfd.get('max_thickness')} mm</td></tr>")

            blocks = []
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

        module3_html = _render_module3(module3)

        return f"""
        <html><head><meta charset='utf-8'><style>{css}</style></head>
        <body>
        <h1>TAVR Analytics 报告 <small>{now}</small></h1>
        {base_html}
        {phase_html}
        {geo_html}
        {self._render_stent_assessment_section(stent, b)}
        {module3_html}
        {angles_html}
        </body></html>
        """

    def _render_stent_assessment_section(self, stent: Dict[str, Any], base: Dict[str, Any]) -> str:
        """渲染“人工瓣膜支架评估” 区块。

        规则：
        - 记录两个期像（舒张末期/收缩末期）的各平面(inflow/nadir/commissure)测量；
        - Sapien3 额外显示 outerskirt plane；而 inflow plane 对于 Sapien3 可省略（按用户要求：inflow plane，Sapien3无需填写；outerskirt plane，仅Sapien3填写）。
        - 等效径：周长平均径=PED，面积平均径=AED。
        """
        if not stent or not isinstance(stent, dict):
            return ""

        def val(x):
            return "" if x is None else str(x)

        brand = (base or {}).get('valveBrand', '').strip()
        model = (base or {}).get('valveModel', '').strip()
        is_sapien3 = ('sapien' in model.lower()) or ('sapien' in brand.lower())

        morph = stent.get('morphology_changed')
        morph_txt = ''
        if morph is True:
            morph_txt = '有'
        elif morph is False:
            morph_txt = '无'
        else:
            morph_txt = ''

        per_phase = stent.get('per_phase') or {}

        # 渲染一个期像的表格
        def render_phase_table(phase_key: str, phase_label: str) -> str:
            p = per_phase.get(phase_key) or {}
            phase_percent = p.get('phase_percent')
            planes = {
                'inflow': ('支架低端平面 (inflow)', not is_sapien3),  # Sapien3无需填写 -> 隐藏
                'nadir': ('支架瓣叶窦底平面 (nadir)', True),
                'outerskirt': ('外裙边平面 (outerskirt)', is_sapien3),  # 仅Sapien3填写
                'commissure': ('支架瓣叶对合平面 (commissure level)', True),
            }

            # 合成outerskirt数据：当前数据模型未明确提供，尝试从nadir或相邻高度代替为空占位
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
                    rows.append(
                        f"<tr><td>{label}</td><td colspan=6></td></tr>"
                    )
                else:
                    rows.append(
                        "<tr>"
                        f"<td>{label}</td>"
                        f"<td>{val(m.get('perimeter'))}</td>"
                        f"<td>{val(m.get('perimeter_derived_diameter'))}</td>"
                        f"<td>{val(m.get('area'))}</td>"
                        f"<td>{val(m.get('area_derived_diameter'))}</td>"
                        f"<td>{val(m.get('longest_diameter'))}</td>"
                        f"<td>{val(m.get('shortest_diameter'))}</td>"
                        "</tr>"
                    )

            title = f"人工瓣膜支架评估（{phase_label}，测量期相: {val(phase_percent)}%）"
            morph_line = f"<tr><td>是否存在人工瓣膜形态改变</td><td colspan=6>{morph_txt}</td></tr>" if morph_txt else ""

            return (
                "<table>"
                f"<tr><th colspan=7>{title}</th></tr>"
                f"{morph_line}"
                f"{header}{''.join(rows)}"
                "</table>"
            )

        parts = []
        parts.append(render_phase_table('end_diastole', '舒张末期'))
        parts.append(render_phase_table('end_systole', '收缩末期'))
        return ''.join(parts)
