"""
模块管理器 - 负责管理TAVR Analytics插件的各个功能模块
"""
import logging
from typing import Dict, List, Optional, Type, Any, Callable
from abc import ABC, abstractmethod
from enum import Enum

import qt
import slicer
from slicer.util import VTKObservationMixin


class ModuleEvent(Enum):
    """模块事件类型"""
    MODULE_REGISTERED = "module_registered"
    MODULE_UNREGISTERED = "module_unregistered" 
    MODULE_LOADED = "module_loaded"
    MODULE_UNLOADED = "module_unloaded"
    MODULE_ACTIVATED = "module_activated"
    MODULE_DEACTIVATED = "module_deactivated"
    SESSION_CHANGED = "session_changed"
    DATA_UPDATED = "data_updated"


class ModuleMessage:
    """模块间消息"""
    
    def __init__(self, sender: str, target: Optional[str], event: ModuleEvent, 
                 data: Optional[Dict[str, Any]] = None):
        self.sender = sender
        self.target = target  # None表示广播
        self.event = event
        self.data = data or {}
        self.timestamp = None
        
        # 自动设置时间戳
        import time
        self.timestamp = time.time()


class ModuleEventBus:
    """模块事件总线 - 处理模块间通信"""
    
    def __init__(self):
        self._subscribers: Dict[ModuleEvent, List[Callable]] = {}
        self._module_subscribers: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
    
    def subscribe(self, event: ModuleEvent, callback: Callable, module_name: Optional[str] = None):
        """订阅事件"""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        
        # 如果指定了模块名，也记录模块级订阅
        if module_name:
            if module_name not in self._module_subscribers:
                self._module_subscribers[module_name] = []
            self._module_subscribers[module_name].append(callback)
        
        self._logger.debug(f"模块 {module_name} 订阅事件: {event.value}")
    
    def unsubscribe(self, event: ModuleEvent, callback: Callable):
        """取消订阅事件"""
        if event in self._subscribers:
            try:
                self._subscribers[event].remove(callback)
                self._logger.debug(f"取消订阅事件: {event.value}")
            except ValueError:
                pass
    
    def unsubscribe_all_for_module(self, module_name: str):
        """取消模块的所有订阅"""
        if module_name in self._module_subscribers:
            callbacks = self._module_subscribers[module_name]
            for callback in callbacks:
                # 从所有事件中移除这些回调
                for event_callbacks in self._subscribers.values():
                    try:
                        event_callbacks.remove(callback)
                    except ValueError:
                        pass
            del self._module_subscribers[module_name]
            self._logger.debug(f"取消模块 {module_name} 的所有订阅")
    
    def publish(self, message: ModuleMessage):
        """发布消息"""
        try:
            # 如果是定向消息，只发送给特定模块
            if message.target:
                target_callbacks = self._module_subscribers.get(message.target, [])
                for callback in target_callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        self._logger.error(f"执行回调时出错: {e}")
            else:
                # 广播消息
                if message.event in self._subscribers:
                    for callback in self._subscribers[message.event]:
                        try:
                            callback(message)
                        except Exception as e:
                            self._logger.error(f"执行回调时出错: {e}")
            
            self._logger.debug(f"发布消息: {message.event.value} from {message.sender}")
            
        except Exception as e:
            self._logger.error(f"发布消息时出错: {e}")
    
    def clear_all(self):
        """清除所有订阅"""
        self._subscribers.clear()
        self._module_subscribers.clear()
        self._logger.debug("清除所有事件订阅")


class ModuleInterface(ABC):
    """模块接口定义"""
    
    def __init__(self):
        self._event_bus: Optional[ModuleEventBus] = None
        self._module_name = self.get_module_name()
    
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
    
    def set_event_bus(self, event_bus: ModuleEventBus):
        """设置事件总线"""
        self._event_bus = event_bus
    
    def publish_event(self, event: ModuleEvent, target: Optional[str] = None, 
                     data: Optional[Dict[str, Any]] = None):
        """发布事件"""
        if self._event_bus:
            message = ModuleMessage(self._module_name, target, event, data)
            self._event_bus.publish(message)
    
    def subscribe_event(self, event: ModuleEvent, callback: Callable):
        """订阅事件"""
        if self._event_bus:
            self._event_bus.subscribe(event, callback, self._module_name)
    
    def on_module_loaded(self):
        """模块加载完成回调"""
        pass
    
    def on_module_unloaded(self):
        """模块卸载回调"""
        pass
    
    def on_module_activated(self):
        """模块激活回调"""
        pass
    
    def on_module_deactivated(self):
        """模块停用回调"""
        pass
    
    def on_session_changed(self, session):
        """会话变更回调"""
        pass
    
    def cleanup(self):
        """清理资源"""
        if self._event_bus:
            self._event_bus.unsubscribe_all_for_module(self._module_name)


class ModuleState(Enum):
    """模块状态枚举"""
    REGISTERED = "registered"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    UNLOADING = "unloading"
    ERROR = "error"


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
        self.module_instance = None
        self.state = ModuleState.REGISTERED
        self.last_error: Optional[str] = None
        self.load_time: Optional[float] = None
        self.activation_count = 0
        
        # 添加时间戳
        import time
        self.created_time = time.time()
    
    def set_state(self, state: ModuleState, error: Optional[str] = None):
        """设置模块状态"""
        self.state = state
        if error:
            self.last_error = error
        elif state != ModuleState.ERROR:
            self.last_error = None
    
    def is_loaded(self) -> bool:
        """检查模块是否已加载"""
        return self.state in [ModuleState.LOADED, ModuleState.ACTIVATING, 
                             ModuleState.ACTIVE, ModuleState.DEACTIVATING]
    
    def is_active(self) -> bool:
        """检查模块是否处于激活状态"""
        return self.state == ModuleState.ACTIVE
    
    def increment_activation(self):
        """增加激活计数"""
        self.activation_count += 1


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
            self._event_bus = ModuleEventBus()
            self._loading_modules: set = set()  # 正在加载的模块
            ModuleManager._initialized = True
    
    def get_event_bus(self) -> ModuleEventBus:
        """获取事件总线"""
        return self._event_bus
    
    def set_session(self, session):
        """设置全局会话对象"""
        old_session = self._session
        self._session = session
        self._logger.info("会话对象已设置")
        
        # 通知所有模块会话已变更
        if old_session != session:
            self._notify_session_changed(session)
    
    def _notify_session_changed(self, session):
        """通知所有模块会话已变更"""
        message = ModuleMessage(
            sender="module_manager",
            target=None,  # 广播
            event=ModuleEvent.SESSION_CHANGED,
            data={"session": session}
        )
        self._event_bus.publish(message)
        
        # 直接调用模块实例的回调
        for module_info in self._modules.values():
            if module_info.module_instance:
                try:
                    module_info.module_instance.on_session_changed(session)
                except Exception as e:
                    self._logger.error(f"通知模块 {module_info.name} 会话变更时出错: {e}")
    
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
        
        # 发布模块注册事件
        message = ModuleMessage(
            sender="module_manager",
            target=None,
            event=ModuleEvent.MODULE_REGISTERED,
            data={
                "module_name": module_info.name,
                "display_name": module_info.display_name,
                "dependencies": module_info.dependencies
            }
        )
        self._event_bus.publish(message)
    
    def unregister_module(self, module_name: str):
        """注销模块"""
        if module_name in self._modules:
            module_info = self._modules[module_name]
            
            # 先卸载模块
            if module_info.is_loaded():
                self.unload_module(module_name)
            
            # 清理模块实例
            if module_info.module_instance:
                module_info.module_instance.cleanup()
                module_info.module_instance = None
            
            del self._modules[module_name]
            self._logger.info(f"注销模块: {module_name}")
            
            # 发布模块注销事件
            message = ModuleMessage(
                sender="module_manager",
                target=None,
                event=ModuleEvent.MODULE_UNREGISTERED,
                data={"module_name": module_name}
            )
            self._event_bus.publish(message)
            
        else:
            self._logger.warning(f"尝试注销不存在的模块: {module_name}")
    
    def get_available_modules(self) -> List[str]:
        """获取可用的模块列表"""
        available = []
        for name, info in self._modules.items():
            if info.enabled and self._check_dependencies(info):
                try:
                    # 如果模块已实例化，直接检查
                    if info.module_instance:
                        if info.module_instance.is_available():
                            available.append(name)
                    else:
                        # 尝试创建临时实例来检查可用性
                        temp_instance = info.module_class()
                        if temp_instance.is_available():
                            available.append(name)
                except Exception as e:
                    self._logger.error(f"检查模块 {name} 可用性时出错: {e}")
                    info.set_state(ModuleState.ERROR, str(e))
        
        return available
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self._modules.get(module_name)
    
    def get_module_adapter(self, module_name: str) -> Optional[ModuleInterface]:
        """
        获取模块适配器实例
        
        Args:
            module_name: 模块名称
            
        Returns:
            模块适配器实例，如果模块不存在或未加载返回None
        """
        module_info = self._modules.get(module_name)
        if module_info and module_info.module_instance:
            return module_info.module_instance
        return None
    
    def load_module(self, module_name: str) -> bool:
        """加载模块"""
        if module_name not in self._modules:
            self._logger.error(f"模块 {module_name} 未注册")
            return False
        
        module_info = self._modules[module_name]
        
        if module_info.is_loaded():
            self._logger.info(f"模块 {module_name} 已加载")
            return True
        
        # 防止重复加载
        if module_name in self._loading_modules:
            self._logger.warning(f"模块 {module_name} 正在加载中")
            return False
        
        try:
            self._loading_modules.add(module_name)
            module_info.set_state(ModuleState.LOADING)
            
            # 检查依赖
            if not self._check_dependencies(module_info):
                error_msg = f"模块 {module_name} 依赖不满足"
                self._logger.error(error_msg)
                module_info.set_state(ModuleState.ERROR, error_msg)
                return False
            
            # 创建模块实例
            if not module_info.module_instance:
                module_info.module_instance = module_info.module_class()
                # 设置事件总线
                module_info.module_instance.set_event_bus(self._event_bus)
            
            # 检查模块可用性
            if not module_info.module_instance.is_available():
                error_msg = f"模块 {module_name} 当前不可用"
                self._logger.error(error_msg)
                module_info.set_state(ModuleState.ERROR, error_msg)
                return False
            
            # 创建组件
            if self._session:
                widget = module_info.module_instance.create_widget(self._session, None)
                module_info.widget_instance = widget
                
                # 设置加载时间
                import time
                module_info.load_time = time.time()
                module_info.set_state(ModuleState.LOADED)
                
                # 调用模块回调
                module_info.module_instance.on_module_loaded()
                
                self._logger.info(f"模块 {module_name} 加载成功")
                
                # 发布模块加载事件
                message = ModuleMessage(
                    sender="module_manager",
                    target=None,
                    event=ModuleEvent.MODULE_LOADED,
                    data={"module_name": module_name}
                )
                self._event_bus.publish(message)
                
                return True
            else:
                error_msg = "会话对象未设置，无法加载模块"
                self._logger.error(error_msg)
                module_info.set_state(ModuleState.ERROR, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"加载模块 {module_name} 时出错: {e}"
            self._logger.error(error_msg)
            module_info.set_state(ModuleState.ERROR, error_msg)
            import traceback
            traceback.print_exc()
            return False
        finally:
            self._loading_modules.discard(module_name)
    
    def unload_module(self, module_name: str):
        """卸载模块"""
        if module_name in self._modules:
            module_info = self._modules[module_name]
            
            if not module_info.is_loaded():
                self._logger.info(f"模块 {module_name} 未加载，无需卸载")
                return
            
            try:
                module_info.set_state(ModuleState.UNLOADING)
                
                # 如果是当前活动模块，先停用
                if self._active_module == module_name:
                    self.deactivate_module(module_name)
                
                # 调用模块回调
                if module_info.module_instance:
                    module_info.module_instance.on_module_unloaded()
                
                # 清理组件
                if module_info.widget_instance:
                    if hasattr(module_info.widget_instance, 'cleanup'):
                        module_info.widget_instance.cleanup()
                    module_info.widget_instance = None
                
                module_info.set_state(ModuleState.REGISTERED)
                
                self._logger.info(f"模块 {module_name} 已卸载")
                
                # 发布模块卸载事件
                message = ModuleMessage(
                    sender="module_manager",
                    target=None,
                    event=ModuleEvent.MODULE_UNLOADED,
                    data={"module_name": module_name}
                )
                self._event_bus.publish(message)
                
            except Exception as e:
                error_msg = f"卸载模块 {module_name} 时出错: {e}"
                self._logger.error(error_msg)
                module_info.set_state(ModuleState.ERROR, error_msg)
    
    def activate_module(self, module_name: str, auto_start_analysis: bool = False) -> bool:
        """激活模块
        
        Args:
            module_name: 模块名称
            auto_start_analysis: 是否自动启动分析（传递给模块）
        """
        if module_name not in self._modules:
            self._logger.error(f"模块 {module_name} 未注册")
            return False
        
        module_info = self._modules[module_name]
        
        # 先加载模块（如果未加载）
        if not self.load_module(module_name):
            return False
        
        try:
            module_info.set_state(ModuleState.ACTIVATING)
            
            # 停用当前活动模块
            if self._active_module and self._active_module != module_name:
                self.deactivate_module(self._active_module)
            
            self._active_module = module_name
            module_info.set_state(ModuleState.ACTIVE)
            module_info.increment_activation()
            
            # 调用模块回调，传递自动启动参数
            if module_info.module_instance:
                try:
                    # 尝试传递auto_start_analysis参数
                    module_info.module_instance.on_module_activated(auto_start_analysis=auto_start_analysis)
                except TypeError:
                    # 如果模块不支持该参数，回退到原始调用
                    module_info.module_instance.on_module_activated()
            
            self._logger.info(f"模块 {module_name} 已激活")
            
            # 发布模块激活事件
            message = ModuleMessage(
                sender="module_manager",
                target=None,
                event=ModuleEvent.MODULE_ACTIVATED,
                data={"module_name": module_name}
            )
            self._event_bus.publish(message)
            
            return True
            
        except Exception as e:
            error_msg = f"激活模块 {module_name} 时出错: {e}"
            self._logger.error(error_msg)
            module_info.set_state(ModuleState.ERROR, error_msg)
            return False
    
    def deactivate_module(self, module_name: str):
        """停用模块"""
        if self._active_module == module_name and module_name in self._modules:
            module_info = self._modules[module_name]
            
            try:
                module_info.set_state(ModuleState.DEACTIVATING)
                
                # 调用模块回调
                if module_info.module_instance:
                    module_info.module_instance.on_module_deactivated()
                
                self._active_module = None
                module_info.set_state(ModuleState.LOADED)
                
                self._logger.info(f"模块 {module_name} 已停用")
                
                # 发布模块停用事件
                message = ModuleMessage(
                    sender="module_manager",
                    target=None,
                    event=ModuleEvent.MODULE_DEACTIVATED,
                    data={"module_name": module_name}
                )
                self._event_bus.publish(message)
                
            except Exception as e:
                error_msg = f"停用模块 {module_name} 时出错: {e}"
                self._logger.error(error_msg)
                module_info.set_state(ModuleState.ERROR, error_msg)
    
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
        self._event_bus.clear_all()
        self._loading_modules.clear()
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
                'state': info.state.value,
                'loaded': info.is_loaded(),
                'active': info.is_active(),
                'dependencies': info.dependencies,
                'last_error': info.last_error,
                'activation_count': info.activation_count,
                'load_time': info.load_time,
                'created_time': info.created_time
            }
        return status
    
    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """获取特定模块的状态"""
        if module_name in self._modules:
            return self._modules[module_name].state
        return None
    
    def reset(self):
        """重置模块管理器"""
        self.cleanup_all_modules()
        self._session = None
        self._main_widget = None
        self._event_bus.clear_all()
        self._loading_modules.clear()
        self._logger.info("模块管理器已重置")
    
    def send_message_to_module(self, target_module: str, event: ModuleEvent, 
                              data: Optional[Dict[str, Any]] = None):
        """发送消息给特定模块"""
        message = ModuleMessage(
            sender="module_manager",
            target=target_module,
            event=event,
            data=data
        )
        self._event_bus.publish(message)
    
    def broadcast_message(self, event: ModuleEvent, data: Optional[Dict[str, Any]] = None):
        """广播消息给所有模块"""
        message = ModuleMessage(
            sender="module_manager",
            target=None,  # 广播
            event=event,
            data=data
        )
        self._event_bus.publish(message)
