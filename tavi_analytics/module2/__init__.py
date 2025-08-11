"""
模块二：引导式分割与解剖标志点定义

负责主动脉根部、瓣膜支架等结构的半自动分割，
以及关键解剖标志点的定义和管理。
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
