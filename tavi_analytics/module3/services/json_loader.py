import json
import os
import logging
from typing import Dict, List, Tuple, Optional


class JSONCurveLoader:
    """
    职责：
    - 读取并校验 JSON 文件
    - 提取 plane 字段与点集（优先 less_points）
    - 对外提供纯数据结构，便于上层逻辑消费
    """

    def __init__(self) -> None:
        pass

    def load(self, json_path: str) -> Dict[str, List[List[float]]]:
        if not json_path or not os.path.isfile(json_path):
            raise FileNotFoundError(f"文件不存在: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("JSON内容不是对象类型")

        plane_fields: Dict[str, List[List[float]]] = {}

        for key, value in data.items():
            if not (isinstance(key, str) and isinstance(value, dict)):
                continue
            if 'plane' not in key.lower():
                continue

            points: Optional[List[List[float]]] = None

            if 'less_points' in value:
                lp = value['less_points']
                if isinstance(lp, list) and len(lp) >= 3:
                    points = lp

            if points is None and 'points' in value:
                pp = value['points']
                if isinstance(pp, list) and len(pp) >= 3:
                    points = pp

            if points is not None:
                plane_fields[key] = points

        logging.info(f"JSON解析完成，找到 {len(plane_fields)} 个 plane 字段")
        return plane_fields
