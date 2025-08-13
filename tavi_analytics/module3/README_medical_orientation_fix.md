# MPR视图医学方向修正文档

## 问题描述
原来的MPR三个视图角度不符合医生的习惯，看起来像是镜像了，不符合标准的医学影像显示约定。

## 医学标准要求

### RAS坐标系
3D Slicer使用RAS坐标系：
- **R (Right)**: X轴正方向指向患者右侧
- **A (Anterior)**: Y轴正方向指向患者前方  
- **S (Superior)**: Z轴正方向指向患者头部

### 标准MPR视图方向

#### 1. 轴状面 (Axial) - Red切片
- **视角**: 从上往下看的横截面（从头看向脚）
- **X轴方向**: 指向患者左侧（图像显示中患者右侧在左边，符合放射学约定）
- **Y轴方向**: 指向患者前方
- **Z轴方向**: 沿着切片法向量（通常指向头部方向）

#### 2. 冠状面 (Coronal) - Green切片  
- **视角**: 从前往后看的截面
- **X轴方向**: 指向患者左侧
- **Y轴方向**: 指向患者头部
- **Z轴方向**: 沿着切片法向量（通常指向前方）

#### 3. 矢状面 (Sagittal) - Yellow切片
- **视角**: 从右侧看向左侧的截面
- **X轴方向**: 指向患者前方  
- **Y轴方向**: 指向患者头部
- **Z轴方向**: 沿着切片法向量（通常指向右侧）

## 修正实现

### 核心修改
修改了 `module3_logic.py` 中的 `_set_slice_by_direct_matrix` 方法，添加了针对不同切片类型的医学标准方向设置：

```python
def _set_slice_by_direct_matrix(self, slice_node, center_point, normal_vector, orientation_name):
    """通过直接构建变换矩阵设置切片方向和位置（符合医学标准）"""
    slice_name = slice_node.GetName()
    
    if "Red" in slice_name:
        # 轴状面：从上往下看的横截面
        self._set_axial_orientation(slice_node, center_point, normal_vector, orientation_name)
    elif "Green" in slice_name:
        # 冠状面：从前往后看的截面  
        self._set_coronal_orientation(slice_node, center_point, normal_vector, orientation_name)
    elif "Yellow" in slice_name:
        # 矢状面：从右侧看向左侧的截面
        self._set_sagittal_orientation(slice_node, center_point, normal_vector, orientation_name)
```

### 具体方法

#### 轴状面方向设置
```python
def _set_axial_orientation(self, slice_node, center_point, normal_vector, orientation_name):
    """设置轴状面的医学标准方向"""
    # X轴：指向患者左侧（-R方向）
    x_axis = np.array([-1, 0, 0])  # 指向Left
    # Y轴：通过叉积计算，指向前方
    # Z轴：法向量方向
```

#### 冠状面方向设置
```python
def _set_coronal_orientation(self, slice_node, center_point, normal_vector, orientation_name):
    """设置冠状面的医学标准方向"""
    # X轴：指向患者左侧
    # Y轴：指向头部方向，确保Y轴指向Superior方向
    # Z轴：法向量方向
```

#### 矢状面方向设置
```python
def _set_sagittal_orientation(self, slice_node, center_point, normal_vector, orientation_name):
    """设置矢状面的医学标准方向"""
    # X轴：指向患者前方
    # Y轴：指向头部方向
    # Z轴：法向量方向
```

## 测试验证

### 测试脚本
创建了 `demo_medical_orientation_test.py` 用于验证医学方向设置：

1. **执行方向切换**: 调用修正后的切换功能
2. **分析切片方向**: 检查每个切片的X、Y、Z轴方向
3. **医学标准验证**: 计算轴向量与标准医学方向的对齐度
4. **结果评估**: 提供符合性评分

### 验证标准
- **对齐度 > 0.8**: ✅ 符合医学标准
- **对齐度 > 0.5**: ⚠️ 基本符合，但可能需要微调  
- **对齐度 ≤ 0.5**: ❌ 不符合医学标准

## 使用方法

### 1. 在3D Slicer中测试
```python
# 在3D Slicer的Python控制台中执行
exec(open(r'c:\code\python\slicer\tavi_analytics\demo_medical_orientation_test.py').read())
```

### 2. 通过模块界面
1. 打开TAVI Analytics模块
2. 切换到模块三
3. 点击"切换到瓣膜支架底平面"按钮
4. 观察MPR视图是否符合医学标准

## 预期效果

### 修正前的问题
- 图像可能左右镜像（患者右侧显示在图像右侧）
- 上下方向可能颠倒
- 前后方向可能错误

### 修正后的效果
- ✅ 符合放射学标准的左右显示（患者右侧在图像左侧）
- ✅ 正确的头部-足部方向
- ✅ 正确的前方-后方方向
- ✅ 医生习惯的解剖视角

## 技术细节

### 坐标变换
- 保持RAS坐标系不变
- 仅调整切片的显示方向矩阵
- 确保中心点定位精度不受影响

### 兼容性
- 保持与现有代码的兼容性
- 不影响其他模块功能
- 维持切片间的垂直关系

### 错误处理
- 添加了完整的异常捕获
- 提供详细的日志记录
- 支持回退到通用方向设置

## 相关文件
- `tavi_analytics/module3/module3_logic.py` - 核心修正逻辑
- `demo_medical_orientation_test.py` - 测试验证脚本
- `README_valve_plane_switch.md` - 原功能文档

## 注意事项
1. 修正后的方向设置专门针对ValveStent_Bottom_Plane功能
2. 需要确保3D Slicer场景中包含ValveStent_Bottom_Plane标记点
3. 建议在实际使用前先用测试脚本验证效果
4. 如果遇到问题，可以通过日志查看详细的错误信息
