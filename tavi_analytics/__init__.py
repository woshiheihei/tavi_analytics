"""
TAVR Analytics - 经导管主动脉瓣置换术后分析插件

这是一个3D Slicer插件，用于TAVR术后4D心脏CT的自动化分析工作流。
包含数据导入、分割、测量和报告生成等功能模块。

Author: TAVR Research Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "TAVR Research Team"

# 导入主要组件
from .tavi_analytics import tavi_analytics, tavi_analyticsWidget, tavi_analyticsLogic, tavi_analyticsTest

__all__ = [
    "tavi_analytics",
    "tavi_analyticsWidget", 
    "tavi_analyticsLogic",
    "tavi_analyticsTest"
]
