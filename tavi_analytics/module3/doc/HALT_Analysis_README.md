# HALT分析功能说明

## 概述

HALT分析功能是TAVR Analytics项目中模块三的重要组成部分，专门用于评估瓣叶低密度增厚（Hypoattenuated Leaflet Thickening）情况。

## 功能特性

### 🚀 引导式分析流程
- **自动环境准备**：点击"开始HALT分析"自动执行以下操作：
  1. 切换到舒张末期时相
  2. MPR自动定位到支架底部平面
  3. 启用分析界面

### 📊 瓣叶状态记录
- **三瓣叶独立评估**：分别记录LC、RC、NC三个瓣叶的HALT状态
- **详细参数记录**：
  - HALT存在性（无HALT/有HALT/难以判定）
  - 面积测量（mm²）
  - 占比计算（%）
  - 分级评估（≤25%/25-50%/50%-75%/>75%）
  - 备注信息

### 🔍 关键视图标记
- **视图状态保存**：标记当前MPR视图状态（中心点+法向量）
- **快速恢复**：双击列表项快速恢复到已标记的视图
- **多视图管理**：支持标记多个关键视图并进行管理

### 📋 分析结果管理
- **实时状态跟踪**：实时显示分析进度和状态
- **结果导出**：支持将分析结果导出为JSON格式
- **会话保存**：分析结果可保存到当前研究会话中

## 使用流程

### 1. 启动分析
1. 在模块三界面中选择"HALT专项分析"选项卡
2. 点击"开始HALT分析"按钮
3. 系统自动：
   - 切换到舒张末期
   - 定位到支架底部平面
   - 启用分析界面

### 2. 瓣叶评估
1. 观察MPR视图中的三个瓣叶
2. 为每个瓣叶填写HALT状态表单：
   - 选择HALT存在性
   - 如有HALT，记录面积、占比和分级
   - 添加必要的备注信息

### 3. 视图标记
1. 调节MPR视图到关键观察角度
2. 在"视图名称"框中输入描述性名称
3. 点击"标记当前视图"保存视图状态
4. 需要时双击列表中的视图名称快速恢复

### 4. 完成分析
1. 确认所有瓣叶状态已记录
2. 点击"完成分析"查看结果摘要
3. 可选择"导出结果"保存到文件

## 技术实现

### 核心组件

#### HaltAnalysisWidget
- **主界面控制器**
- **功能**：
  - 分析流程管理
  - 界面状态控制
  - 结果汇总和导出

#### LeafletHaltForm
- **单瓣叶状态表单**
- **功能**：
  - 独立的瓣叶状态记录
  - 实时数据验证
  - 状态变更通知

#### ViewMarkingManager
- **视图标记管理器**
- **功能**：
  - MPR视图状态保存/恢复
  - 几何参数计算和存储
  - 视图列表管理

### 服务依赖

- **PhaseSelectionWidget**: 期像切换功能
- **ContourPositionService**: 轮廓定位服务
- **PlanePositionManager**: 平面定位管理器
- **TAVRStudySession**: 会话数据管理

## 与模块集成

HALT分析功能已集成到模块三中，通过选项卡方式与完整PASTE分析并存：

```python
# 在Module3Widget中的集成
analysis_tabs = qt.QTabWidget()
analysis_tabs.addTab(self.paste_analysis, "完整PASTE分析")
analysis_tabs.addTab(self.halt_analysis, "HALT专项分析")
```

## 数据格式

### 分析结果结构
```json
{
  "analysis_type": "HALT",
  "analysis_started": true,
  "leaflets": {
    "LC": {
      "leaflet": "LC",
      "halt_status": "有HALT",
      "area": 15.2,
      "percentage": 35.8,
      "grade": "25-50%",
      "notes": "轻度增厚"
    },
    "RC": {
      "leaflet": "RC",
      "halt_status": "无HALT",
      "area": 0.0,
      "percentage": 0.0,
      "grade": "无HALT",
      "notes": ""
    },
    "NC": {
      "leaflet": "NC",
      "halt_status": "难以判定",
      "area": 0.0,
      "percentage": 0.0,
      "grade": "无HALT",
      "notes": "图像质量影响判断"
    }
  },
  "marked_views": {
    "LC瓣叶正面视图": {
      "center_point": [0.0, 0.0, 50.0],
      "normal_vector": [0.0, 0.0, 1.0],
      "timestamp": "2025-08-15 14:30:00",
      "description": "HALT分析关键视图 - LC瓣叶正面视图"
    }
  },
  "analysis_timestamp": "2025-08-15 14:35:00",
  "session_info": {
    "study_name": "TAVR_Case_001",
    "patient_id": "PAT_001"
  }
}
```

## 错误处理

### 常见问题及解决方案

1. **无法切换到舒张末期**
   - 检查模块一中是否已标记舒张末期
   - 确认序列浏览器节点存在

2. **无法定位到支架底部平面**
   - 检查模块二中是否已完成轮廓重建
   - 确认支架底部轮廓数据完整

3. **视图标记失败**
   - 检查当前MPR视图状态是否有效
   - 确认平面参数计算正确

## 扩展性

### 未来可扩展功能
- 自动HALT区域检测算法集成
- 机器学习辅助分级评估
- 多时相HALT变化对比分析
- 与其他模块的数据关联分析

## 开发说明

### 测试
运行测试文件验证功能：
```bash
python test_halt_analysis.py
```

### 调试
启用详细日志查看执行过程：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 自定义
可通过修改以下文件进行功能扩展：
- `halt_analysis_widget.py`: 主界面逻辑
- `LeafletHaltForm`: 表单组件
- `ViewMarkingManager`: 视图管理逻辑
