"""
模块三逻辑组件（骨架）

目前仅提供最小实现以支撑界面与导航切换。
后续会在此处实现自动化测量相关算法与流程。
"""
import logging
from typing import Dict
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
from .services.json_loader import JSONCurveLoader
from .services.slicer_curve_service import SlicerCurveService


class Module3Logic(ScriptedLoadableModuleLogic):
    """模块三业务逻辑（占位实现 + JSON曲线加载）"""

    def __init__(self) -> None:
        super().__init__()
        logging.info("Module3Logic 初始化完成 (skeleton)")
        self._json_loader = JSONCurveLoader()
        self._slicer_curve = SlicerCurveService()

    def load_plane_curves_from_json(self, json_file_path: str, clear_existing: bool = True) -> Dict:
        """
        从给定JSON路径读取所有包含"plane"的字段，并在Slicer中创建闭合曲线。
        规则：
        - 优先使用 less_points (>=3)，否则使用 points (>=3)
        - 自动闭合曲线（重复第一个点）
        - 坐标转换 [x, y, z] -> [-x, -y, z]
        - 可选清理现有名称包含"plane"的节点
        
        Returns: { created_count: int, curve_info: List[str] }
        """
        try:
            # 解析 JSON -> plane -> points
            plane_fields = self._json_loader.load(json_file_path)

            # 可选清理
            if clear_existing:
                cleared = self._slicer_curve.clear_plane_nodes()
                logging.info(f"清理了 {cleared} 个现有 plane 节点")

            # 在 Slicer 中创建曲线
            return self._slicer_curve.create_closed_curves(plane_fields)
        except Exception as e:
            logging.error(f"加载JSON并创建曲线失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {"created_count": 0, "curve_info": [], "error": str(e)}

    # 保留对外兼容的清理方法（如果有其它模块直接调用）
    def _clear_plane_nodes(self) -> int:
        return self._slicer_curve.clear_plane_nodes()

    def cleanup(self):
        """清理资源"""
        try:
            logging.info("Module3Logic 清理完成")
        except Exception as e:
            logging.error(f"Module3Logic 清理失败: {e}")
