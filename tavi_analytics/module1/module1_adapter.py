"""
模块一适配器 - 实现模块接口
"""
import sys
import os

# 确保能够导入核心模块
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from typing import List
from core.module_manager import ModuleInterface, ModuleEvent
from core.session import TAVRStudySession
from module1.module1_widget import Module1Widget
from module1.module1_logic import Module1Logic


class Module1Adapter(ModuleInterface):
    """模块一适配器 - 实现标准模块接口"""
    
    def __init__(self):
        super().__init__()
        self._logic = None
        self._widget = None
    
    def get_module_name(self) -> str:
        """获取模块名称"""
        return "module1"
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return "数据导入与场景准备"
    
    def is_available(self) -> bool:
        """检查模块是否可用"""
        try:
            # 检查必要的依赖
            import slicer
            
            # 检查Sequences模块是否可用
            sequences_module = slicer.modules.sequences
            if not sequences_module:
                return False
            
            # 检查必要的MRML节点类型
            from slicer import vtkMRMLSequenceNode, vtkMRMLSequenceBrowserNode
            
            return True
        except Exception:
            return False
    
    def create_widget(self, session: TAVRStudySession, parent=None):
        """创建模块组件"""
        # 创建逻辑实例（如果还没有）
        if self._logic is None:
            self._logic = Module1Logic()
        
        # 创建并返回组件
        self._widget = Module1Widget(session, logic=self._logic, parent=parent)
        return self._widget
    
    def get_dependencies(self) -> List[str]:
        """获取模块依赖"""
        return []  # 模块一没有依赖其他模块
    
    def on_module_loaded(self):
        """模块加载完成回调"""
        print(f"模块 {self.get_display_name()} 加载完成")
        # 可以在这里发布自定义事件
        self.publish_event(ModuleEvent.DATA_UPDATED, data={"status": "ready"})
    
    def on_module_activated(self):
        """模块激活回调"""
        print(f"模块 {self.get_display_name()} 已激活")
        # 可以在这里执行激活后的初始化
        if self._widget and hasattr(self._widget, 'on_activated'):
            self._widget.on_activated()
    
    def on_module_deactivated(self):
        """模块停用回调"""
        print(f"模块 {self.get_display_name()} 已停用")
        # 可以在这里执行停用后的清理
        if self._widget and hasattr(self._widget, 'on_deactivated'):
            self._widget.on_deactivated()
    
    def on_session_changed(self, session):
        """会话变更回调"""
        print(f"模块 {self.get_display_name()} 收到会话变更通知")
        # 更新组件的会话引用
        if self._widget and hasattr(self._widget, 'set_session'):
            self._widget.set_session(session)
    
    def cleanup(self):
        """清理资源"""
        super().cleanup()
        if self._widget and hasattr(self._widget, 'cleanup'):
            self._widget.cleanup()
        self._widget = None
        self._logic = None
