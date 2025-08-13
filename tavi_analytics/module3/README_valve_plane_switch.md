# 模块三ValveStent_Bottom_Plane平面切换功能使用说明

## 功能概述

模块三新增了一键将当前MPR视图切换到ValveStent_Bottom_Plane平面的功能，能够：

- 保持现有MPR布局（不切换到2x2布局）
- 将轴状面切换到ValveStent_Bottom_Plane平面
- 矢状面和冠状面与ValveStent_Bottom_Plane平面两两垂直
- 中心点定位在ValveStent_Bottom_Plane闭合曲线的平均中心点
- 通过点云几何算法计算平面法向量

## 使用方法

### 前提条件

1. 确保3D Slicer场景中存在名为`ValveStent_Bottom_Plane`的曲线节点
2. 该曲线节点包含足够的控制点（至少3个点）
3. 当前处于MPR布局模式

### 操作步骤

1. **启动模块三**
   - 在TAVI Analytics插件中切换到"模块三：自动化测量"

2. **选择期像**（可选）
   - 在期像选择区域选择要分析的心动周期期像（舒张末期或收缩末期）

3. **执行平面切换**
   - 在"平面视图控制"区域找到按钮："🎯 切换到ValveStent_Bottom_Plane平面"
   - 点击按钮执行切换

4. **查看结果**
   - 红色切片（轴状面）：现在显示ValveStent_Bottom_Plane平面
   - 绿色切片（冠状面）：与ValveStent_Bottom_Plane平面垂直
   - 黄色切片（矢状面）：与ValveStent_Bottom_Plane平面垂直
   - 所有视图的中心点位于ValveStent_Bottom_Plane的平均中心

## 技术实现

### 算法流程

1. **获取点云数据**
   - 从ValveStent_Bottom_Plane曲线节点提取所有控制点坐标（RAS坐标系）

2. **计算平面中心点**
   - 计算所有点的算术平均值作为平面中心点

3. **计算平面法向量**
   - 使用奇异值分解(SVD)最小二乘法拟合平面
   - 法向量为最小奇异值对应的方向
   - 确保法向量指向正Z方向（向上）

4. **设置切片方向**
   - 使用`SetSliceToRASByNTP`方法设置切片节点方向
   - 计算与主平面垂直的两个正交切线向量
   - 所有切片设置为"Reformat"模式

### 坐标系统

- 使用Slicer的RAS坐标系统（Right-Anterior-Superior）
- R（右）：正X方向指向患者右侧
- A（前）：正Y方向指向患者前方
- S（上）：正Z方向指向患者头部

### 按钮状态反馈

- **正常状态**：🎯 切换到ValveStent_Bottom_Plane平面
- **执行中**：🔄 正在切换...
- **成功**：✅ 切换完成（2秒后恢复）
- **失败**：❌ 切换失败（2秒后恢复）

## 故障排除

### 常见问题

1. **"未找到ValveStent_Bottom_Plane节点"**
   - 确认场景中存在该节点
   - 检查节点名称是否完全匹配（区分大小写）

2. **"点数不足"**
   - 确认ValveStent_Bottom_Plane节点包含至少3个控制点
   - 检查控制点坐标是否有效

3. **"切换失败"**
   - 检查当前是否在MPR布局模式
   - 确认有活动的体数据节点
   - 查看Slicer控制台的详细错误信息

### 调试功能

可以使用以下代码在Slicer Python控制台中测试：

```python
# 检查ValveStent_Bottom_Plane节点
valve_node = slicer.mrmlScene.GetFirstNodeByName("ValveStent_Bottom_Plane")
if valve_node:
    print(f"节点存在，包含 {valve_node.GetNumberOfControlPoints()} 个点")
else:
    print("节点不存在")

# 测试切换功能
import sys
sys.path.append(r"c:\code\python\slicer\tavi_analytics\tavi_analytics")
from module3.module3_logic import Module3Logic

logic = Module3Logic()
success = logic.switch_to_valve_stent_bottom_plane()
print(f"切换结果: {'成功' if success else '失败'}")
```

## 相关文件

- **逻辑实现**：`tavi_analytics/module3/module3_logic.py`
- **UI界面**：`tavi_analytics/module3/module3_widget.py`
- **演示脚本**：`demo_module3_valve_plane_switch.py`

## 未来扩展

1. **多平面支持**：扩展到支持其他关键平面（如SinusOfValsalva_Plane）
2. **自定义角度**：允许用户微调切片角度
3. **预设视图**：保存和恢复常用的平面配置
4. **动画过渡**：平滑的视图切换动画效果
