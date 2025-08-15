# 3D Slicer 交互式切片相交线功能开启方法

## 功能简介
在医学影像分析中，3D Slicer 提供了“切片相交线”功能，用于在各个切片视图中显示其它切片的交线。通过 Python API，可以不仅开启相交线显示，还能支持交互式拖动、平移和旋转切片。

## 需求目标
- 启用切片相交线可见性
- 支持交互（拖动、平移、旋转）
- 可回读当前状态

## 方法说明
### 1. 获取 Application Logic
```python
appLogic = slicer.app.applicationLogic()
```

### 2. 枚举标志位
```python
flag = slicer.vtkMRMLApplicationLogic
```

### 3. 启用各项功能
```python
# 开启切片相交线可见性
appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesVisibility, True)
# 支持交互式拖动
appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesInteractive, True)
# 支持平移
appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesTranslation, True)
# 支持旋转
appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesRotation, True)
```

### 4. 检查功能状态
```python
states = {
    'Visibility': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesVisibility)),
    'Interactive': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesInteractive)),
    'Translation': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesTranslation)),
    'Rotation': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesRotation)),
}
print(states)
```

## 典型输出
```
{'Visibility': True, 'Interactive': True, 'Translation': True, 'Rotation': True}
```

## 进阶用法
- 若只需显示交线但不允许交互，将 Interactive/Translation/Rotation 设为 False。
- 可进一步设置线宽、交线颜色、交线显示模式等参数。

## 参考
- Slicer Python Interactor
- vtkMRMLApplicationLogic API 文档
