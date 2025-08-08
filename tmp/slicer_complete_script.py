#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终兼容版本：3D Slicer绘制plane曲线脚本
适用于所有版本的3D Slicer

功能说明：
- 自动识别JSON文件中所有包含"plane"的字段
- 优先使用"less_points"数据，如果点数不足3个则使用完整的"points"数据
- 针对plane_mid_zg_yg, plane_top等字段，当less_points只有1个点时自动切换到完整points
- 自动闭合曲线（添加第一个点作为最后一个点）
- 坐标自动转换：[x, y, z] → [-x, -y, z]

使用方法：
直接复制以下代码到3D Slicer的Python控制台中执行

"""

import json
import slicer

def draw_all_plane_curves():
    """绘制所有plane曲线的主函数"""
    
    # JSON文件路径（请根据实际情况修改）
    json_file_path = r"C:\Users\13167\Desktop\halt\data\dianxing\measurement.json"
    
    print("=" * 50)
    print("3D Slicer Plane曲线绘制脚本 (增强版)")
    print("支持plane_mid_zg_yg, plane_top等特殊字段")
    print("=" * 50)
    
    try:
        # 1. 清理现有的plane节点
        print("1. 清理现有的plane节点...")
        all_nodes = slicer.mrmlScene.GetNodes()
        nodes_to_remove = []
        for i in range(all_nodes.GetNumberOfItems()):
            node = all_nodes.GetItemAsObject(i)
            if node and hasattr(node, 'GetName') and node.GetName():
                if 'plane' in node.GetName().lower():
                    nodes_to_remove.append(node)
        for node in nodes_to_remove:
            slicer.mrmlScene.RemoveNode(node)
        print(f"   清理了 {len(nodes_to_remove)} 个节点")
        
        # 2. 读取JSON文件
        print("2. 读取JSON文件...")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   文件读取成功，共 {len(data)} 个字段")
        
        # 3. 查找plane字段
        print("3. 查找plane字段...")
        plane_fields = {}
        for key, value in data.items():
            if "plane" in key.lower():
                if isinstance(value, dict):
                    points = None
                    points_source = ""
                    
                    # 优先使用less_points，如果点数不够则使用完整的points
                    if "less_points" in value:
                        less_points = value["less_points"]
                        if isinstance(less_points, list) and len(less_points) >= 3:
                            points = less_points
                            points_source = "less_points"
                    
                    # 如果less_points不够，尝试使用完整的points
                    if points is None and "points" in value:
                        full_points = value["points"]
                        if isinstance(full_points, list) and len(full_points) >= 3:
                            points = full_points
                            points_source = "points"
                    
                    if points is not None:
                        plane_fields[key] = points
                        print(f"   找到: {key} ({len(points)} 个点，来源: {points_source})")
        
        print(f"   总共找到 {len(plane_fields)} 个有效字段")
        
        # 4. 定义颜色
        colors = [
            [1.0, 0.0, 0.0],   # 红色
            [0.0, 1.0, 0.0],   # 绿色
            [0.0, 0.0, 1.0],   # 蓝色
            [1.0, 1.0, 0.0],   # 黄色
            [1.0, 0.0, 1.0],   # 洋红
            [0.0, 1.0, 1.0],   # 青色
            [1.0, 0.5, 0.0],   # 橙色
            [0.5, 0.0, 1.0],   # 紫色
            [0.0, 0.5, 0.0],   # 深绿
            [0.5, 0.5, 0.5],   # 灰色
            [0.8, 0.2, 0.2],   # 深红
            [0.2, 0.8, 0.2],   # 浅绿
            [0.2, 0.2, 0.8],   # 深蓝
        ]
        
        # 5. 创建曲线
        print("4. 创建闭合曲线...")
        created_count = 0
        curve_info = []  # 存储曲线信息
        
        for idx, (plane_name, points) in enumerate(plane_fields.items()):
            try:
                # 确定数据源类型
                points_source = "less_points"
                if isinstance(data[plane_name].get("less_points"), list):
                    if len(data[plane_name]["less_points"]) < 3:
                        points_source = "points (less_points不足)"
                else:
                    points_source = "points"
                
                # 创建曲线节点
                curveNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode")
                curveNode.SetName(plane_name)
                
                # 添加控制点（坐标转换：前两个坐标取相反数）
                valid_points = 0
                for point in points:
                    if isinstance(point, list) and len(point) >= 3:
                        x = -float(point[0])  # X坐标取相反数
                        y = -float(point[1])  # Y坐标取相反数
                        z = float(point[2])   # Z坐标不变
                        curveNode.AddControlPoint(x, y, z)
                        valid_points += 1
                
                # 添加第一个点作为最后一个点以形成闭合曲线
                if valid_points > 0:
                    first_point = points[0]
                    x = -float(first_point[0])
                    y = -float(first_point[1])
                    z = float(first_point[2])
                    curveNode.AddControlPoint(x, y, z)
                
                # 设置显示属性
                displayNode = curveNode.GetDisplayNode()
                if displayNode:
                    color = colors[idx % len(colors)]
                    displayNode.SetColor(color)
                    displayNode.SetSelectedColor(color)
                    displayNode.SetLineWidth(3)
                    displayNode.SetOpacity(0.9)
                
                created_count += 1
                curve_info.append(f"{plane_name}: {valid_points} 个点 ({points_source})")
                print(f"   ✓ {plane_name}: {valid_points} 个点 ({points_source})")
                
            except Exception as e:
                print(f"   ✗ {plane_name}: {str(e)}")
        
        # 6. 结果报告
        print("=" * 50)
        print(f"🎉 完成！成功创建了 {created_count} 条闭合曲线")
        
        if created_count > 0:
            print("\n创建的曲线列表:")
            for i, info in enumerate(curve_info, 1):
                print(f"  {i:2d}. {info}")
        
        print("\n坐标转换说明:")
        print("  原始坐标 [x, y, z] → 转换为 [-x, -y, z]")
        print("  每条曲线自动闭合（添加第一个点作为最后一个点）")
        print("\n数据源优先级:")
        print("  1. 优先使用 less_points (≥3个点)")
        print("  2. 不足时自动切换到完整的 points 数据")
        print("=" * 50)
        
        return created_count
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        return 0

# 便捷函数
def run():
    """快速运行函数"""
    return draw_all_plane_curves()

def clear_planes():
    """清理所有plane曲线"""
    all_nodes = slicer.mrmlScene.GetNodes()
    count = 0
    for i in range(all_nodes.GetNumberOfItems()):
        node = all_nodes.GetItemAsObject(i)
        if node and hasattr(node, 'GetName') and node.GetName():
            if 'plane' in node.GetName().lower():
                slicer.mrmlScene.RemoveNode(node)
                count += 1
    print(f"清理了 {count} 个plane曲线")

def show_planes():
    """显示当前的plane曲线信息"""
    all_nodes = slicer.mrmlScene.GetNodes()
    plane_nodes = []
    for i in range(all_nodes.GetNumberOfItems()):
        node = all_nodes.GetItemAsObject(i)
        if node and hasattr(node, 'GetName') and node.GetName():
            if 'plane' in node.GetName().lower():
                points = 'N/A'
                if hasattr(node, 'GetNumberOfControlPoints'):
                    points = node.GetNumberOfControlPoints()
                plane_nodes.append(f"{node.GetName()}: {points} 个控制点")
    
    print(f"当前场景中的plane曲线 ({len(plane_nodes)} 个):")
    for node_info in plane_nodes:
        print(f"  - {node_info}")

# 自动执行
if __name__ == "__main__":
    draw_all_plane_curves()
else:
    print("""
=== 使用说明 ===
1. run() - 执行主程序，绘制所有plane曲线
2. clear_planes() - 清理所有plane曲线
3. show_planes() - 显示当前plane曲线信息

快速开始：直接执行 run()
""")

# 如果在控制台中直接执行，自动运行
try:
    # 检查是否在Slicer环境中
    if 'slicer' in globals():
        result = draw_all_plane_curves()
        if result > 0:
            print(f"\n✨ 脚本执行成功！已创建 {result} 条闭合曲线")
        else:
            print("\n❌ 脚本执行完成，但没有创建任何曲线")
except:
    pass
