# 瓣膜体数据 Red 视图叠加复现指南

本指南说明如何在 3D Slicer 中，将 2D 的瓣膜体数据（valve）叠加到 CTA 原始影像（source）的 Red 切片视图上，使人工瓣膜精确贴合到已通过 MPR 调整好的主动脉瓣环位置。

---

## 目标

- 背景：Red 视图显示 CTA（source）。
- 前景：valve（瓣膜 2D 体数据），半透明叠加。
- 通过一个线性变换（ValveToRedSlice）将 valve 对齐到当前 Red 切片平面的位置与朝向。

## 前提条件

- 已加载两个体数据：
  - CTA 标量体数据：名称为 `source`（vtkMRMLScalarVolumeNode）。
  - 瓣膜体数据：名称为 `valve`（优先 VectorVolume，或 ScalarVolume）。
- 已通过 MPR 操作把 Red 视图中心调整到主动脉瓣环切面。

> 如果数据命名不同，可在脚本中修改目标名称，或用“部分匹配”找到对应节点。

---

## 快速复现（推荐）

将以下脚本粘贴到 Slicer 的 Python Console 并执行：

```python
import slicer, vtk

def find_volume_by_name(class_name, target_name):
    # Prefer exact match, else fallback to contains
    nodes = slicer.util.getNodesByClass(class_name)
    exact = [n for n in nodes if n.GetName() == target_name]
    if exact:
        return exact[0]
    lower = target_name.lower()
    partial = [n for n in nodes if lower in n.GetName().lower()]
    return partial[0] if partial else None

# 1) Locate CTA (background) and valve (foreground) volumes
valveNode = find_volume_by_name('vtkMRMLVectorVolumeNode', 'valve')
if valveNode is None:
    valveNode = find_volume_by_name('vtkMRMLScalarVolumeNode', 'valve')
sourceNode = find_volume_by_name('vtkMRMLScalarVolumeNode', 'source')

if valveNode is None:
    raise RuntimeError('未找到名为 "valve" 的体数据 (Vector/ScalarVolume)。')
if sourceNode is None:
    raise RuntimeError('未找到名为 "source" 的CTA体数据 (ScalarVolume)。')

# 2) Get Red slice orientation (SliceToRAS)
lm = slicer.app.layoutManager()
redWidget = lm.sliceWidget('Red')
if redWidget is None:
    raise RuntimeError('未找到 Red 视图。')
redSliceNode = redWidget.mrmlSliceNode()
sliceToRAS = redSliceNode.GetSliceToRAS()  # vtkMatrix4x4

# 3) Build centering+scaling matrix S: 将 valve 图像中心对齐到切片中心，并按其像素间距缩放
img = valveNode.GetImageData()
if img is None:
    raise RuntimeError('valve 体数据没有 ImageData。')
width, height, depth = img.GetDimensions()
spx, spy, spz = valveNode.GetSpacing()

S = vtk.vtkMatrix4x4()
S.Identity()
# 从像素索引到 mm 的比例（使用 valve 自身的 spacing）
S.SetElement(0, 0, float(spx) if spx else 1.0)
S.SetElement(1, 1, float(spy) if spy else 1.0)
S.SetElement(2, 2, 1.0)
# 平移使图像中心落在 (0,0)
cx = (width - 1) * 0.5
cy = (height - 1) * 0.5
S.SetElement(0, 3, -cx * (float(spx) if spx else 1.0))
S.SetElement(1, 3, -cy * (float(spy) if spy else 1.0))

# 4) Get valve IJK->RAS and invert
M_ijkToRas = vtk.vtkMatrix4x4()
valveNode.GetIJKToRASMatrix(M_ijkToRas)
M_ijkToRas_inv = vtk.vtkMatrix4x4()
vtk.vtkMatrix4x4.Invert(M_ijkToRas, M_ijkToRas_inv)

# 5) Compute parent transform: P = SliceToRAS * S * (IJKToRAS)^-1
P_tmp = vtk.vtkMatrix4x4()
vtk.vtkMatrix4x4.Multiply4x4(S, M_ijkToRas_inv, P_tmp)
P = vtk.vtkMatrix4x4()
vtk.vtkMatrix4x4.Multiply4x4(sliceToRAS, P_tmp, P)

# 6) Create/apply transform node
transformName = 'ValveToRedSlice'
transformNode = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', transformName)
if transformNode is None:
    transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', transformName)
transformNode.SetMatrixTransformToParent(P)
valveNode.SetAndObserveTransformNodeID(transformNode.GetID())

# 7) Configure Red slice compositing: CTA为背景，valve为前景
compNode = redWidget.mrmlSliceCompositeNode()
if sourceNode:
    compNode.SetBackgroundVolumeID(sourceNode.GetID())
compNode.SetForegroundVolumeID(valveNode.GetID())
compNode.SetForegroundOpacity(0.6)

# 8) 显示优化
valveDisplay = valveNode.GetDisplayNode()
if valveDisplay:
    try:
        valveDisplay.SetInterpolate(False)
    except Exception:
        pass

redWidget.sliceView().scheduleRender()

print({'valve': valveNode.GetName(), 'transform': transformNode.GetName(), 'dims': (width, height, depth), 'spacing': (spx, spy, spz)})
```

执行完成后：

- 在 Red 视图中，CTA（source）为背景，valve 为半透明前景叠加。
- 变换节点 `ValveToRedSlice` 已创建并应用于 valve。

---

## 工作原理简述（核心矩阵）

- `SliceToRAS`：Red 切片的位姿（切片坐标到 RAS 世界坐标）。
- `IJKToRAS`：valve 体数据从体素索引坐标到 RAS 的物理变换。
- `S`：将 valve 图像中心移到原点并按其自身 spacing 缩放到毫米尺度。

最终父变换：

```text
P = SliceToRAS × S × (IJKToRAS)^-1
```

把 P 作为 valve 的父变换后，valve 几何中心会落在当前 Red 切片中心，方向与切片一致。

---

## 交互微调建议

- 选择 Transforms 模块 -> `ValveToRedSlice`：
  - 轻微调整 Translation/Rotation，使人工瓣膜边缘与环部位贴合。
- Red 视图前景透明度：在 Slice Controller 调整 Foreground Opacity（脚本默认 0.6）。
- 清晰度：已关闭前景插值（更利于边界判读）。
- 如果方向颠倒/镜像：尝试绕切片法向轴旋转 180° 或对 X/Y 小角度修正。

---

## 常见问题排查

- 找不到节点：
  - 确认 CTA 命名为 `source`，瓣膜体数据命名为 `valve`。
  - 或在脚本中把目标名称改成你的实际名称；脚本已支持部分匹配。
- valve 不是 VectorVolume：
  - 脚本会回退寻找 ScalarVolume；若仍失败，检查数据类型。
- 前景不显示：
  - 检查 Red 视图 Slice Controller 的 Foreground 是否设置为 valve，Opacity 是否非 0。
  - 确认 valve 处于 `ValveToRedSlice` 变换之下（Data 模块查看 Transform tree）。
- 叠加偏移：
  - 通过 `ValveToRedSlice` 的 Translation 进行毫米级别微调。

---

## 撤销 / 重置

- 取消叠加：在 Slice Controller 清空 Foreground 或把 Foreground Opacity 设为 0。
- 移除变换：在 Data/Transforms 模块中把 valve 的 Transform 清空，或删除 `ValveToRedSlice` 节点。

---

## 可选：实时跟随当前 Red 切片（高级）

如果希望在移动 Red 切片时，valve 叠加位置自动跟随更新，可添加一个观察器，实时重算 P 矩阵（逻辑与上文相同）。以下示例仅作参考：

```python
import slicer, vtk

obsTag = None
transformName = 'ValveToRedSlice'

# 复用上文的查找逻辑
valveNode = slicer.util.getFirstNodeByClassByName('vtkMRMLVectorVolumeNode', 'valve') or \
            slicer.util.getFirstNodeByClassByName('vtkMRMLScalarVolumeNode', 'valve')
sourceNode = slicer.util.getFirstNodeByClassByName('vtkMRMLScalarVolumeNode', 'source')

if not valveNode or not sourceNode:
    raise RuntimeError('请先准备好 valve 与 source 节点。')

transformNode = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', transformName) or \
                slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', transformName)
valveNode.SetAndObserveTransformNodeID(transformNode.GetID())

lm = slicer.app.layoutManager()
redSliceNode = lm.sliceWidget('Red').mrmlSliceNode()

img = valveNode.GetImageData()
width, height, depth = img.GetDimensions()
spx, spy, spz = valveNode.GetSpacing()

# 预计算常量部分
S = vtk.vtkMatrix4x4(); S.Identity()
S.SetElement(0, 0, float(spx) if spx else 1.0)
S.SetElement(1, 1, float(spy) if spy else 1.0)
S.SetElement(2, 2, 1.0)
S.SetElement(0, 3, -((width - 1) * 0.5) * (float(spx) if spx else 1.0))
S.SetElement(1, 3, -((height - 1) * 0.5) * (float(spy) if spy else 1.0))

M_ijkToRas = vtk.vtkMatrix4x4(); valveNode.GetIJKToRASMatrix(M_ijkToRas)
M_ijkToRas_inv = vtk.vtkMatrix4x4(); vtk.vtkMatrix4x4.Invert(M_ijkToRas, M_ijkToRas_inv)

P_tmp = vtk.vtkMatrix4x4(); P = vtk.vtkMatrix4x4()

def updateTransform(caller=None, event=None):
    sliceToRAS = redSliceNode.GetSliceToRAS()
    vtk.vtkMatrix4x4.Multiply4x4(S, M_ijkToRas_inv, P_tmp)
    vtk.vtkMatrix4x4.Multiply4x4(sliceToRAS, P_tmp, P)
    transformNode.SetMatrixTransformToParent(P)

# 初次计算
updateTransform()

# 监听切片变更
obsTag = redSliceNode.AddObserver(redSliceNode.ModifiedEvent, updateTransform)
print('ValveToRedSlice 已绑定 Red 切片变化，obsTag=', obsTag)

# 取消监听（需要时执行）
# if obsTag is not None:
#     redSliceNode.RemoveObserver(obsTag)
#     obsTag = None
```

---

## 术语与 API 速查

- SliceToRAS（切片 -> RAS）：`sliceNode.GetSliceToRAS()`
- IJKToRAS（体素 -> RAS）：`volumeNode.GetIJKToRASMatrix(mat)`
- 线性变换节点：`vtkMRMLLinearTransformNode`
- 复合叠加设置（Red）：`sliceWidget.mrmlSliceCompositeNode()` 背景/前景/透明度

---

如需将该能力集成到插件模块，建议把“矩阵计算 + 变换应用 + 叠加配置”封装为一个函数，并支持命名参数（背景/前景节点名、透明度、是否关闭插值、是否实时跟随等）。
