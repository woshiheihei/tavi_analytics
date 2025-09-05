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

        # 几何测量（来自当前活动/各期像轮廓管理器）
        planes_summary = s.get_planes_summary()
        all_measurements = s.get_all_plane_measurements() or {}

        # 交接对齐角度（模块五保存于session）
        commissure_angles = s.get_commissure_alignment_angles()

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
            "angles": commissure_angles,
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

        return f"""
        <html><head><meta charset='utf-8'><style>{css}</style></head>
        <body>
        <h1>TAVR Analytics 报告 <small>{now}</small></h1>
        {base_html}
        {phase_html}
        {geo_html}
        {angles_html}
        </body></html>
        """
