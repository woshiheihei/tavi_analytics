"""
模块二：全自动分析

负责一键全自动地导出并上传影像至远程算法进行推理，
监控任务状态，下载并导入分割与测量结果，完成可视化与展示。
"""

# 模块二组件导入
from .module2_widget import Module2Widget
from .module2_logic import Module2Logic
from .module2_adapter import Module2Adapter

__all__ = [
    "Module2Widget",
    "Module2Logic",
    "Module2Adapter"
]
