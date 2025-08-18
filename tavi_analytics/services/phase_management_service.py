"""
期像管理服务

提供集中化的期像状态管理和事件发布，解决多个PhaseSelectionWidget实例之间
的同步问题。采用单例模式确保全局状态一致性。

主要功能：
- 全局期像状态管理
- 期像切换API
- 期像变更事件发布
- 与TAVRStudySession集成

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
from typing import Optional, Dict, Any, Callable, List
import qt

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession


class PhaseManagementService(qt.QObject):
    """
    期像管理服务 - 单例模式
    
    负责协调所有期像选择组件的状态同步，提供集中化的期像管理。
    """
    
    # 期像变更信号 - 全局事件
    phaseChanged = qt.Signal(str, str)  # (old_phase, new_phase)
    phaseSwitchRequested = qt.Signal(str, str)  # (phase, source_component)
    phaseStatusUpdated = qt.Signal(str)  # (status_message)
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, session: Optional[TAVRStudySession] = None):
        """
        初始化期像管理服务
        
        Args:
            session: TAVR研究会话对象
        """
        if self._initialized:
            return
        
        super().__init__()
        self.session = session
        self.current_phase: Optional[str] = None  # 当前激活的期像
        self.available_phases = ['diastole', 'systole']  # 可用期像
        
        # 期像相关节点命名模式（与PhaseSelectionWidget保持一致）
        self.phase_suffixes = {
            'diastole': 'End_Diastole',
            'systole': 'End_Systole'
        }
        
        # 领域模型使用的期像键
        self.phase_domain_keys = {
            'diastole': 'end_diastole',
            'systole': 'end_systole',
        }
        
        # 订阅者列表 - 期像选择组件的回调函数
        self._phase_sync_callbacks: List[Callable[[str], None]] = []
        
        self._initialized = True
        logging.info("PhaseManagementService 初始化完成（单例模式）")
    
    def set_session(self, session: TAVRStudySession):
        """
        设置会话对象
        
        Args:
            session: TAVR研究会话对象
        """
        self.session = session
        logging.info("PhaseManagementService 设置session")
    
    def register_phase_sync_callback(self, callback: Callable[[str], None]):
        """
        注册期像同步回调函数
        
        期像选择组件可以注册回调函数，当期像发生变化时会被调用
        
        Args:
            callback: 回调函数，参数为新的期像
        """
        if callback not in self._phase_sync_callbacks:
            self._phase_sync_callbacks.append(callback)
            logging.debug(f"注册期像同步回调，当前回调数量: {len(self._phase_sync_callbacks)}")
    
    def unregister_phase_sync_callback(self, callback: Callable[[str], None]):
        """
        取消注册期像同步回调函数
        
        Args:
            callback: 要取消注册的回调函数
        """
        if callback in self._phase_sync_callbacks:
            self._phase_sync_callbacks.remove(callback)
            logging.debug(f"取消注册期像同步回调，当前回调数量: {len(self._phase_sync_callbacks)}")
    
    def get_current_phase(self) -> Optional[str]:
        """
        获取当前期像
        
        Returns:
            str: 当前期像 ('diastole' 或 'systole')，未设置时返回None
        """
        return self.current_phase
    
    def set_current_phase(self, phase: str, source_component: str = "unknown") -> bool:
        """
        设置当前期像并触发全局同步
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
            source_component: 触发期像切换的组件名称
            
        Returns:
            bool: 设置成功返回True
        """
        if phase not in self.available_phases:
            logging.warning(f"无效的期像类型: {phase}")
            return False
        
        old_phase = self.current_phase
        
        # 如果期像没有变化，仍然触发同步（用于修复UI状态不一致的情况）
        self.current_phase = phase
        
        # 发出期像变更信号
        self.phaseChanged.emit(old_phase or "", phase)
        
        # 通知所有注册的回调函数进行同步
        self._notify_phase_sync_callbacks(phase)
        
        logging.info(f"期像管理服务：期像从 {old_phase} 切换到 {phase}（来源：{source_component}）")
        return True
    
    def switch_to_diastole(self, source_component: str = "unknown") -> bool:
        """
        切换到舒张末期
        
        Args:
            source_component: 触发切换的组件名称
            
        Returns:
            bool: 切换成功返回True
        """
        if not self.session:
            logging.error("期像管理服务：未设置session，无法切换期像")
            return False
        
        try:
            # 发出期像切换请求信号
            self.phaseSwitchRequested.emit('diastole', source_component)
            
            # 获取舒张末期时相信息
            end_diastole_info = self.session.get_marked_phase('end_diastole')
            if not end_diastole_info:
                logging.info("期像管理服务：未找到舒张末期标记，跳过时相切换")
                self.set_current_phase('diastole', source_component)
                return True
            
            frame_index = end_diastole_info.get('frame_index')
            if frame_index is None:
                logging.info("期像管理服务：舒张末期标记中缺少帧索引信息，跳过时相切换")
                self.set_current_phase('diastole', source_component)
                return True
            
            # 获取序列浏览器节点并切换帧
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("期像管理服务：未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新期像状态
            self.set_current_phase('diastole', source_component)
            
            # 发出状态更新信号
            self.phaseStatusUpdated.emit("已切换到舒张末期")
            
            logging.info(f"期像管理服务：成功切换到帧 {frame_index} (舒张末期)")
            return True
            
        except Exception as e:
            logging.error(f"期像管理服务：切换到舒张末期失败: {e}")
            return False
    
    def switch_to_systole(self, source_component: str = "unknown") -> bool:
        """
        切换到收缩末期
        
        Args:
            source_component: 触发切换的组件名称
            
        Returns:
            bool: 切换成功返回True
        """
        if not self.session:
            logging.error("期像管理服务：未设置session，无法切换期像")
            return False
        
        try:
            # 发出期像切换请求信号
            self.phaseSwitchRequested.emit('systole', source_component)
            
            # 获取收缩末期时相信息
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info:
                logging.warning("期像管理服务：未找到收缩末期标记")
                return False
            
            frame_index = end_systole_info.get('frame_index')
            if frame_index is None:
                logging.warning("期像管理服务：收缩末期标记中缺少帧索引信息")
                return False
            
            # 获取序列浏览器节点并切换帧
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("期像管理服务：未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新期像状态
            self.set_current_phase('systole', source_component)
            
            # 发出状态更新信号
            self.phaseStatusUpdated.emit("已切换到收缩末期")
            
            logging.info(f"期像管理服务：成功切换到帧 {frame_index} (收缩末期)")
            return True
            
        except Exception as e:
            logging.error(f"期像管理服务：切换到收缩末期失败: {e}")
            return False
    
    def _notify_phase_sync_callbacks(self, phase: str):
        """
        通知所有注册的期像同步回调函数
        
        Args:
            phase: 新的期像
        """
        for callback in self._phase_sync_callbacks:
            try:
                callback(phase)
            except Exception as e:
                logging.error(f"期像同步回调执行失败: {e}")
    
    def get_available_phases(self) -> List[str]:
        """
        获取可用的期像列表
        
        Returns:
            List[str]: 可用期像列表
        """
        return self.available_phases.copy()
    
    def get_phase_info(self) -> Dict[str, Any]:
        """
        获取期像管理服务的状态信息
        
        Returns:
            dict: 包含当前期像、可用期像等信息的字典
        """
        return {
            'current_phase': self.current_phase,
            'available_phases': self.available_phases.copy(),
            'callback_count': len(self._phase_sync_callbacks),
            'has_session': self.session is not None
        }
    
    def cleanup(self):
        """清理资源"""
        self._phase_sync_callbacks.clear()
        logging.info("期像管理服务：清理完成")


# 全局服务实例获取函数
_phase_management_service_instance = None

def get_phase_management_service(session: Optional[TAVRStudySession] = None) -> PhaseManagementService:
    """
    获取期像管理服务单例实例
    
    Args:
        session: TAVR研究会话对象（首次调用时需要提供）
        
    Returns:
        PhaseManagementService: 期像管理服务实例
    """
    global _phase_management_service_instance
    
    if _phase_management_service_instance is None:
        _phase_management_service_instance = PhaseManagementService(session)
    elif session is not None:
        _phase_management_service_instance.set_session(session)
    
    return _phase_management_service_instance