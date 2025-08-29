# 创建带纹理贴图的VTK正方形

## 概述

本文档描述了在3D Slicer中创建一个边长为26mm的正方形VTK actor，并应用PNG图片作为纹理贴图的完整实现方法。该功能可用于医学图像处理、3D可视化等场景。

## 需求描述

### 功能需求
1. 创建一个边长为26mm的正方形几何体
2. 将指定的PNG图片作为纹理贴图应用到正方形表面
3. 在3D Slicer的3D窗口中显示带纹理的正方形
4. 支持3D交互操作（旋转、缩放、平移）

### 技术需求
- 使用VTK库进行3D几何体创建
- 支持PNG格式的纹理图片
- 正确的UV纹理坐标映射
- 集成到3D Slicer环境中

## 实现方案

### 技术架构
- **几何体创建**: 使用VTK的vtkPoints和vtkPolygon创建正方形
- **纹理处理**: 使用vtkPNGReader读取图片，vtkTexture应用纹理
- **渲染显示**: 通过vtkActor和vtkPolyDataMapper在3D场景中渲染
- **Slicer集成**: 创建vtkMRMLModelNode节点集成到Slicer场景

### 核心组件
1. **几何体定义**: 4个顶点构成的正方形（边长26mm）
2. **纹理坐标**: UV坐标系统，范围[0,1]×[0,1]
3. **纹理映射**: PNG图片到正方形表面的映射
4. **渲染管线**: VTK渲染管线的完整配置

## 实现代码

### 完整实现脚本

```python
import vtk
import slicer
import os

def create_textured_square(image_path, edge_length=26.0):
    """
    创建带纹理贴图的正方形VTK actor
    
    参数:
        image_path (str): PNG图片的完整路径
        edge_length (float): 正方形边长，单位mm，默认26mm
    
    返回:
        str: 操作结果信息
    """
    
    # 1. 验证输入文件
    if not os.path.exists(image_path):
        return f"错误：找不到图片文件 {image_path}"
    
    try:
        # 2. 读取PNG图片
        reader = vtk.vtkPNGReader()
        reader.SetFileName(image_path)
        reader.Update()
        
        # 3. 创建正方形几何体
        square_points = vtk.vtkPoints()
        square_points.SetNumberOfPoints(4)
        
        half_size = edge_length / 2.0
        # 定义四个顶点坐标（逆时针顺序）
        square_points.SetPoint(0, -half_size, -half_size, 0)  # 左下
        square_points.SetPoint(1,  half_size, -half_size, 0)  # 右下
        square_points.SetPoint(2,  half_size,  half_size, 0)  # 右上
        square_points.SetPoint(3, -half_size,  half_size, 0)  # 左上
        
        # 4. 创建纹理坐标
        texture_coords = vtk.vtkFloatArray()
        texture_coords.SetName("TCoords")
        texture_coords.SetNumberOfComponents(2)
        texture_coords.SetNumberOfTuples(4)
        # UV坐标映射（对应几何体顶点顺序）
        texture_coords.SetTuple2(0, 0.0, 0.0)  # 左下 -> (0,0)
        texture_coords.SetTuple2(1, 1.0, 0.0)  # 右下 -> (1,0)
        texture_coords.SetTuple2(2, 1.0, 1.0)  # 右上 -> (1,1)
        texture_coords.SetTuple2(3, 0.0, 1.0)  # 左上 -> (0,1)
        
        # 5. 创建多边形
        square_polygon = vtk.vtkPolygon()
        square_polygon.GetPointIds().SetNumberOfIds(4)
        for i in range(4):
            square_polygon.GetPointIds().SetId(i, i)
        
        squares = vtk.vtkCellArray()
        squares.InsertNextCell(square_polygon)
        
        # 6. 创建PolyData并设置数据
        square_polydata = vtk.vtkPolyData()
        square_polydata.SetPoints(square_points)
        square_polydata.SetPolys(squares)
        square_polydata.GetPointData().SetTCoords(texture_coords)
        
        # 7. 创建纹理对象
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.InterpolateOn()  # 启用纹理插值
        
        # 8. 创建渲染管线
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(square_polydata)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetTexture(texture)
        
        # 9. 清理之前的模型（可选）
        # 查找并删除可能存在的旧模型
        nodes_to_remove = []
        for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")):
            node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            if node and "Textured_Square" in node.GetName():
                nodes_to_remove.append(node)
        
        for node in nodes_to_remove:
            slicer.mrmlScene.RemoveNode(node)
        
        # 10. 创建Slicer模型节点
        model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "Textured_Square_26mm")
        model_node.SetAndObservePolyData(square_polydata)
        
        # 11. 创建显示节点
        display_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
        display_node.SetRepresentation(1)  # 表面显示模式
        display_node.SetOpacity(1.0)       # 完全不透明
        display_node.SetVisibility(True)    # 设置可见
        
        # 关联显示节点到模型节点
        model_node.SetAndObserveDisplayNodeID(display_node.GetID())
        
        # 12. 添加带纹理的actor到3D渲染器
        threeDViewWidget = slicer.app.layoutManager().threeDWidget(0)
        threeDView = threeDViewWidget.threeDView()
        renderWindow = threeDView.renderWindow()
        renderers = renderWindow.GetRenderers()
        renderer = renderers.GetFirstRenderer()
        
        # 添加actor到渲染器
        renderer.AddActor(actor)
        
        # 13. 刷新3D视图
        renderWindow.Render()
        slicer.util.resetThreeDViews()
        
        return f"成功创建带纹理贴图的正方形，模型节点ID: {model_node.GetID()}"
        
    except Exception as e:
        return f"处理过程中出错: {str(e)}"

# 使用示例
if __name__ == "__main__":
    # 指定PNG图片路径
    image_path = "C:\\Users\\89235\\Downloads\\valve.png"
    
    # 创建带纹理的正方形
    result = create_textured_square(image_path, edge_length=26.0)
    print(result)
```

## 使用方法

### 1. 基本使用
```python
# 在3D Slicer的Python控制台中执行
image_path = "C:\\path\\to\\your\\image.png"
result = create_textured_square(image_path)
print(result)
```

### 2. 自定义边长
```python
# 创建边长为50mm的正方形
result = create_textured_square(image_path, edge_length=50.0)
```

### 3. 批量创建
```python
# 批量创建多个带不同纹理的正方形
image_paths = [
    "C:\\path\\to\\texture1.png",
    "C:\\path\\to\\texture2.png",
    "C:\\path\\to\\texture3.png"
]

for i, path in enumerate(image_paths):
    result = create_textured_square(path)
    print(f"正方形 {i+1}: {result}")
```

## 技术细节

### UV纹理坐标说明
- UV坐标系统：U轴对应图片的水平方向，V轴对应垂直方向
- 坐标范围：[0,1] × [0,1]
- 映射关系：
  - (0,0) -> 图片左下角
  - (1,0) -> 图片右下角
  - (1,1) -> 图片右上角
  - (0,1) -> 图片左上角

### 几何体坐标系
- 正方形位于XY平面（Z=0）
- 中心点位于原点(0,0,0)
- 边长为指定值（默认26mm）

### 渲染属性
- 表面渲染模式
- 完全不透明
- 启用纹理插值
- 支持3D交互操作

## 常见问题

### 1. 图片无法加载
**问题**: "错误：找不到图片文件"
**解决**: 
- 检查文件路径是否正确
- 确保文件存在且可读
- 使用绝对路径

### 2. 纹理显示异常
**问题**: 纹理显示颠倒或拉伸
**解决**:
- 检查UV坐标设置
- 确认图片格式为PNG
- 验证几何体顶点顺序

### 3. 3D视图中看不到模型
**问题**: 模型创建成功但不可见
**解决**:
- 调用 `slicer.util.resetThreeDViews()` 重置视图
- 检查显示节点的可见性设置
- 确认模型在视图范围内

## 扩展功能

### 1. 支持其他图片格式
```python
# 添加JPEG支持
if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
    reader = vtk.vtkJPEGReader()
elif image_path.lower().endswith('.png'):
    reader = vtk.vtkPNGReader()
```

### 2. 动态纹理更新
```python
def update_texture(model_node_id, new_image_path):
    """更新现有模型的纹理"""
    # 实现纹理动态更新逻辑
    pass
```

### 3. 多材质支持
```python
def create_multi_textured_square(image_paths):
    """创建支持多重纹理的正方形"""
    # 实现多材质混合逻辑
    pass
```

## 版本信息

- **创建日期**: 2025年8月29日
- **适用版本**: 3D Slicer 5.x
- **依赖库**: VTK, Slicer
- **测试环境**: Windows 10/11

## 作者信息

- **文档作者**: GitHub Copilot
- **项目**: TAVI Analytics
- **更新记录**: 初始版本
