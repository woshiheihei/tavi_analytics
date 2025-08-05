"""
模块管理器 - 负责管理TAVR Analytics插件的各个功能模块
"""
import logging
from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod

import qt
import slicer
from slicer.util import VTKObservationMixin


class ModuleInterface(ABC):
    """模块接口定义"""
    
    @abstractmethod
    def get_module_name(self) -> str:
        """获取模块名称"""
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """获取显示名称"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查模块是否可用"""
        pass
    
    @abstractmethod
    def create_widget(self, session, parent=None):
        """创建模块组件"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取模块依赖"""
        pass


class ModuleInfo:
    """模块信息类"""
    
    def __init__(self, name: str, display_name: str, module_class: Type[ModuleInterface], 
                 dependencies: List[str] = None, enabled: bool = True):
        self.name = name
        self.display_name = display_name
        self.module_class = module_class
        self.dependencies = dependencies or []
        self.enabled = enabled
        self.widget_instance = None
        self.loaded = False


class ModuleManager(VTKObservationMixin):
    """模块管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            VTKObservationMixin.__init__(self)
            self._modules: Dict[str, ModuleInfo] = {}
            self._active_module: Optional[str] = None
            self._session = None
            self._main_widget = None
            self._logger = logging.getLogger(__name__)
            ModuleManager._initialized = True
    
    def set_session(self, session):
        """设置全局会话对象"""
        self._session = session
        self._logger.info("会话对象已设置")
    
    def set_main_widget(self, widget):
        """设置主界面组件"""
        self._main_widget = widget
        self._logger.info("主界面组件已设置")
    
    def register_module(self, module_info: ModuleInfo):
        """注册模块"""
        if module_info.name in self._modules:
            self._logger.warning(f"模块 {module_info.name} 已存在，将被覆盖")
        
        self._modules[module_info.name] = module_info
        self._logger.info(f"注册模块: {module_info.display_name} ({module_info.name})")
    
    def unregister_module(self, module_name: str):
        """注销模块"""
        if module_name in self._modules:
            module_info = self._modules[module_name]
            
            # 清理模块实例
            if module_info.widget_instance:
                if hasattr(module_info.widget_instance, 'cleanup'):
                    module_info.widget_instance.cleanup()
                module_info.widget_instance = None
            
            del self._modules[module_name]
            self._logger.info(f"注销模块: {module_name}")
        else:
            self._logger.warning(f"尝试注销不存在的模块: {module_name}")
    
    def get_available_modules(self) -> List[str]:
        """获取可用的模块列表"""
        available = []
        for name, info in self._modules.items():
            if info.enabled and self._check_dependencies(info):
                try:
                    # 尝试创建模块实例来检查可用性
                    temp_instance = info.module_class()
                    if temp_instance.is_available():
                        available.append(name)
                except Exception as e:
                    self._logger.error(f"检查模块 {name} 可用性时出错: {e}")
        
        return available
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self._modules.get(module_name)
    
    def load_module(self, module_name: str) -> bool:
        """加载模块"""
        if module_name not in self._modules:
            self._logger.error(f"模块 {module_name} 未注册")
            return False
        
        module_info = self._modules[module_name]
        
        if module_info.loaded:
            self._logger.info(f"模块 {module_name} 已加载")
            return True
        
        # 检查依赖
        if not self._check_dependencies(module_info):
            self._logger.error(f"模块 {module_name} 依赖不满足")
            return False
        
        try:
            # 创建模块实例
            module_instance = module_info.module_class()
            
            # 检查模块可用性
            if not module_instance.is_available():
                self._logger.error(f"模块 {module_name} 当前不可用")
                return False
            
            # 创建组件
            if self._session:
                # 不传递父组件，让模块自己处理界面层次结构
                widget = module_instance.create_widget(self._session, None)
                module_info.widget_instance = widget
                module_info.loaded = True
                
                self._logger.info(f"模块 {module_name} 加载成功")
                return True
            else:
                self._logger.error("会话对象未设置，无法加载模块")
                return False
                
        except Exception as e:
            self._logger.error(f"加载模块 {module_name} 时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_module(self, module_name: str):
        """卸载模块"""
        if module_name in self._modules:
            module_info = self._modules[module_name]
            
            if module_info.widget_instance:
                if hasattr(module_info.widget_instance, 'cleanup'):
                    module_info.widget_instance.cleanup()
                module_info.widget_instance = None
            
            module_info.loaded = False
            
            # 如果是当前活动模块，清除活动状态
            if self._active_module == module_name:
                self._active_module = None
            
            self._logger.info(f"模块 {module_name} 已卸载")
    
    def activate_module(self, module_name: str) -> bool:
        """激活模块"""
        if module_name not in self._modules:
            self._logger.error(f"模块 {module_name} 未注册")
            return False
        
        # 先加载模块（如果未加载）
        if not self.load_module(module_name):
            return False
        
        # 停用当前活动模块
        if self._active_module and self._active_module != module_name:
            self.deactivate_module(self._active_module)
        
        self._active_module = module_name
        self._logger.info(f"模块 {module_name} 已激活")
        
        # 发出模块激活信号
        self._emit_module_activated(module_name)
        return True
    
    def deactivate_module(self, module_name: str):
        """停用模块"""
        if self._active_module == module_name:
            self._active_module = None
            self._logger.info(f"模块 {module_name} 已停用")
            
            # 发出模块停用信号
            self._emit_module_deactivated(module_name)
    
    def get_active_module(self) -> Optional[str]:
        """获取当前活动模块"""
        return self._active_module
    
    def get_module_widget(self, module_name: str):
        """获取模块组件实例"""
        if module_name in self._modules:
            return self._modules[module_name].widget_instance
        return None
    
    def cleanup_all_modules(self):
        """清理所有模块"""
        for module_name in list(self._modules.keys()):
            self.unload_module(module_name)
        
        self._active_module = None
        self._logger.info("所有模块已清理")
    
    def _check_dependencies(self, module_info: ModuleInfo) -> bool:
        """检查模块依赖"""
        for dep_name in module_info.dependencies:
            if dep_name not in self._modules:
                self._logger.error(f"依赖模块 {dep_name} 未注册")
                return False
            
            if not self._modules[dep_name].enabled:
                self._logger.error(f"依赖模块 {dep_name} 未启用")
                return False
        
        return True
    
    def _emit_module_activated(self, module_name: str):
        """发出模块激活信号"""
        # 这里可以实现信号发送机制
        pass
    
    def _emit_module_deactivated(self, module_name: str):
        """发出模块停用信号"""
        # 这里可以实现信号发送机制
        pass
    
    def get_modules_status(self) -> Dict[str, Any]:
        """获取所有模块状态"""
        status = {}
        for name, info in self._modules.items():
            status[name] = {
                'display_name': info.display_name,
                'enabled': info.enabled,
                'loaded': info.loaded,
                'active': self._active_module == name,
                'dependencies': info.dependencies
            }
        return status
    
    def reset(self):
        """重置模块管理器"""
        self.cleanup_all_modules()
        self._session = None
        self._main_widget = None
        self._logger.info("模块管理器已重置")
