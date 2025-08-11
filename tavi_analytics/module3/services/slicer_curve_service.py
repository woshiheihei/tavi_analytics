import logging
from typing import Dict, List


class SlicerCurveService:
    """
    职责：
    - 与 Slicer 交互，创建/展示曲线
    - 处理样式、闭合等与可视化相关的细节
    """

    def __init__(self) -> None:
        pass

    def clear_plane_nodes(self) -> int:
        try:
            import slicer
            all_nodes = slicer.mrmlScene.GetNodes()
            nodes_to_remove = []
            for i in range(all_nodes.GetNumberOfItems()):
                node = all_nodes.GetItemAsObject(i)
                if node and hasattr(node, 'GetName') and node.GetName():
                    name = node.GetName()
                    if isinstance(name, str) and 'plane' in name.lower():
                        nodes_to_remove.append(node)
            for n in nodes_to_remove:
                slicer.mrmlScene.RemoveNode(n)
            logging.info(f"清理了 {len(nodes_to_remove)} 个 plane 节点")
            return len(nodes_to_remove)
        except Exception as e:
            logging.error(f"清理plane节点失败: {e}")
            return 0

    def create_closed_curves(self, plane_points: Dict[str, List[List[float]]]) -> Dict:
        try:
            import slicer
            created_count = 0
            curve_info: List[str] = []
            colors = [
                [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
                [1.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0],
                [1.0, 0.5, 0.0], [0.5, 0.0, 1.0], [0.0, 0.5, 0.0],
                [0.5, 0.5, 0.5], [0.8, 0.2, 0.2], [0.2, 0.8, 0.2], [0.2, 0.2, 0.8],
            ]

            for idx, (plane_name, points) in enumerate(plane_points.items()):
                try:
                    curveNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode")
                    curveNode.SetName(plane_name)

                    valid_points = 0
                    for p in points:
                        if isinstance(p, list) and len(p) >= 3:
                            x, y, z = -float(p[0]), -float(p[1]), float(p[2])
                            curveNode.AddControlPoint(x, y, z)
                            valid_points += 1

                    if valid_points > 0:
                        first = points[0]
                        curveNode.AddControlPoint(-float(first[0]), -float(first[1]), float(first[2]))

                    displayNode = curveNode.GetDisplayNode()
                    if displayNode:
                        color = colors[idx % len(colors)]
                        displayNode.SetColor(color)
                        displayNode.SetSelectedColor(color)
                        displayNode.SetLineWidth(3)
                        displayNode.SetOpacity(0.9)

                    created_count += 1
                    curve_info.append(f"{plane_name}: {valid_points} 个点")
                    logging.info(f"✓ 创建曲线: {plane_name} ({valid_points} 个点)")
                except Exception as e:
                    logging.error(f"创建曲线失败 {plane_name}: {e}")

            logging.info(f"创建完成: {created_count} 条闭合曲线")
            return {"created_count": created_count, "curve_info": curve_info}
        except Exception as e:
            logging.error(f"创建曲线失败: {e}")
            return {"created_count": 0, "curve_info": [], "error": str(e)}
