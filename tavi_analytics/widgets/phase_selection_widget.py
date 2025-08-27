"""
期像选择组件 - 公共UI组件

提供舒张末期和收缩末期的切换功能，可在多个模块中复用。
"""

import logging
from typing import Optional, Dict, Any, Callable
import qt

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager


class PhaseSelectionWidget(qt.QWidget):
    """
    期像选择组件
    
    提供舒张末期和收缩末期的切换界面和功能，包括：
    - 期像切换按钮
    - 自动期像切换
    - 期像状态检查
    - 状态更新回调
    - 分割和平面的显示/隐藏管理
    """
    
    # 定义信号
    phaseChanged = qt.Signal(str)  # 期像改变信号，参数为期像类型 ('diastole' 或 'systole')
    statusUpdated = qt.Signal(str)  # 状态更新信号，参数为状态消息
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """
        初始化期像选择组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.current_phase = None  # 当前选择的期像
        
        # 期像相关节点命名模式
        self.phase_suffixes = {
            'diastole': 'End_Diastole',
            'systole': 'End_Systole'
        }
        # 领域模型使用的期像键（与CardiacPhase保持一致）
        self.phase_domain_keys = {
            'diastole': 'end_diastole',
            'systole': 'end_systole',
        }
        
        # 设置组件属性
        self.setObjectName("PhaseSelectionWidget")
        
        # 期像管理服务集成
        self._phase_service = None
        self._is_syncing_from_external = False  # 防止无限循环的标志
        
        # 创建界面
        self._setup_ui()
        
        # 连接到期像管理服务
        self._connect_to_phase_service()
        
        logging.info("PhaseSelectionWidget 初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建期像控制框架
        phase_frame = LayoutManager.create_section_frame("期像选择")
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(phase_frame)
        
        phase_layout = qt.QVBoxLayout(phase_frame)
        
        # 期像切换按钮组
        switch_layout = qt.QHBoxLayout()
        switch_layout.setSpacing(8)
        
        # 切换到舒张末期按钮
        self.switch_to_diastole_button = LayoutManager.create_button_with_style(
            text="🫀 舒张末期",
            button_type="primary",
            size="small",
            min_height=32
        )
        self.switch_to_diastole_button.setObjectName("switchToDiastoleButton")
        self.switch_to_diastole_button.clicked.connect(self._on_switch_to_diastole)
        self.switch_to_diastole_button.setToolTip("切换到舒张末期进行分析（推荐用于全自动分析）")
        switch_layout.addWidget(self.switch_to_diastole_button)
        
        # 切换到收缩末期按钮
        self.switch_to_systole_button = LayoutManager.create_button_with_style(
            text="💓 收缩末期",
            button_type="secondary",
            size="small",
            min_height=32
        )
        self.switch_to_systole_button.setObjectName("switchToSystoleButton")
        self.switch_to_systole_button.clicked.connect(self._on_switch_to_systole)
        self.switch_to_systole_button.setToolTip("切换到收缩末期进行分析（用于动态分析）")
        switch_layout.addWidget(self.switch_to_systole_button)
        
        phase_layout.addLayout(switch_layout)
        
        # 添加说明文本
        self.phase_info_label = qt.QLabel(
            "💡 提示：请确保在模块一中已正确标记相应期像，然后点击上方按钮切换。"
        )
        self.phase_info_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                font-style: italic;
                padding: 4px;
                margin: 2px;
            }
        """)
        self.phase_info_label.setWordWrap(True)
        phase_layout.addWidget(self.phase_info_label)
        
        # 状态显示标签
        self.status_label = qt.QLabel("准备进行期像切换...")
        self.status_label.setAlignment(qt.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                margin: 2px 0px;
            }
        """)
        self.status_label.setWordWrap(True)
        phase_layout.addWidget(self.status_label)
    
    def set_info_text(self, text: str):
        """
        设置说明文本
        
        Args:
            text: 说明文本内容
        """
        if hasattr(self, 'phase_info_label'):
            self.phase_info_label.setText(text)
    
    def get_current_phase(self) -> Optional[str]:
        """
        获取当前选择的期像
        
        Returns:
            str: 当前期像 ('diastole' 或 'systole')，未选择时返回None
        """
        return self.current_phase
    
    def set_current_phase(self, phase: str):
        """
        设置当前期像并更新按钮状态
        
        重构后：只负责UI状态更新，不处理数据可视化
        数据可视化由PhaseManagementService统一管理
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
        """
        if phase in ['diastole', 'systole']:
            old_phase = self.current_phase
            self.current_phase = phase
            self._update_phase_button_states(active_phase=phase)
            
            logging.info(f"期像设置为: {phase} (数据可视化由服务层管理)")
    
    def auto_activate(self, preferred_phase: str = 'diastole'):
        """
        自动激活期像选择
        
        尝试切换到指定的期像，通常在模块激活时调用
        
        Args:
            preferred_phase: 首选期像 ('diastole' 或 'systole')
        """
        logging.info(f"期像选择组件激活，首选期像: {preferred_phase}")
        
        try:
            # 检查标记的期像状态
            phase_status = self._check_marked_phases()
            
            # 尝试切换到首选期像
            if preferred_phase == 'diastole':
                if self._auto_switch_to_end_diastole():
                    self._update_status("已切换到舒张末期")
                    self.set_current_phase('diastole')
                    self.phaseChanged.emit('diastole')
                else:
                    self._update_status("请先在模块一中标记舒张末期时相")
            elif preferred_phase == 'systole':
                if self._switch_to_end_systole():
                    self._update_status("已切换到收缩末期")
                    self.set_current_phase('systole')
                    self.phaseChanged.emit('systole')
                else:
                    self._update_status("请先在模块一中标记收缩末期时相")
                    
        except Exception as e:
            logging.error(f"自动期像切换失败: {e}")
            self._update_status("自动期像切换失败，请手动切换")
    
    def _check_marked_phases(self) -> Dict[str, Any]:
        """
        检查已标记的期像状态
        
        Returns:
            dict: 期像标记状态信息
        """
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        end_systole_info = self.session.get_marked_phase('end_systole')
        
        # 记录期像标记状态
        diastole_marked = end_diastole_info is not None and end_diastole_info.get('frame_index') is not None
        systole_marked = end_systole_info is not None and end_systole_info.get('frame_index') is not None
        
        if diastole_marked and systole_marked:
            logging.info("✓ 舒张末期和收缩末期均已标记")
        elif diastole_marked:
            logging.info("✓ 舒张末期已标记，收缩末期未标记")
        elif systole_marked:
            logging.warning("⚠ 收缩末期已标记，但舒张末期未标记（建议先标记舒张末期）")
        else:
            logging.warning("⚠ 舒张末期和收缩末期均未标记")
        
        return {
            'end_diastole_marked': diastole_marked,
            'end_systole_marked': systole_marked,
            'end_diastole_info': end_diastole_info,
            'end_systole_info': end_systole_info
        }
    
    def _auto_switch_to_end_diastole(self) -> bool:
        """
        自动切换到舒张末期时相
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        # 1. 从session获取舒张末期时相信息
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        if not end_diastole_info:
            logging.info("未找到舒张末期标记，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        frame_index = end_diastole_info.get('frame_index')
        if frame_index is None:
            logging.info("舒张末期标记中缺少帧索引信息，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        # 2. 获取序列浏览器节点
        browser_node = self.session.get_sequence_browser_node()
        if not browser_node:
            logging.warning("未找到序列浏览器节点")
            return False
        
        # 3. 切换到指定帧
        try:
            browser_node.SetSelectedItemNumber(frame_index)
            logging.info(f"成功切换到帧 {frame_index} (舒张末期)")
            return True
        except Exception as e:
            logging.error(f"切换帧失败: {e}")
            return False
    
    def _switch_to_end_systole(self) -> bool:
        """
        切换到收缩末期
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        try:
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info:
                logging.warning("未找到收缩末期标记")
                return False
            
            frame_index = end_systole_info.get('frame_index')
            if frame_index is None:
                logging.warning("收缩末期标记中缺少帧索引信息")
                return False
            
            # 获取序列浏览器节点
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新状态显示
            phase_percent = end_systole_info.get('phase_percent', 0.0)
            logging.info(f"成功切换到帧 {frame_index} (收缩末期)")
            return True
            
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False
    
    def _on_switch_to_diastole(self):
        """处理切换到舒张末期按钮点击"""
        logging.info("用户要求切换到舒张末期")
        
        try:
            # 使用期像管理服务进行切换，这样会自动同步所有相关组件
            if self._phase_service:
                success = self._phase_service.switch_to_diastole("PhaseSelectionWidget")
                if success:
                    logging.info("通过期像管理服务切换到舒张末期成功")
                    # 不需要手动更新UI，期像管理服务会通过回调自动同步
                else:
                    self._update_status("切换到舒张末期失败，请检查模块一中的期像标记")
                    logging.warning("通过期像管理服务切换到舒张末期失败")
            else:
                # 回退到原来的逻辑（用于兼容性）
                if self._auto_switch_to_end_diastole():
                    self.set_current_phase('diastole')
                    self._update_status("已切换到舒张末期")
                    self.phaseChanged.emit('diastole')
                    logging.info("手动切换到舒张末期成功")
                else:
                    self._update_status("切换到舒张末期失败，请检查模块一中的期像标记")
                    logging.warning("手动切换到舒张末期失败")
                
        except Exception as e:
            logging.error(f"切换到舒张末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")
    
    def _on_switch_to_systole(self):
        """处理切换到收缩末期按钮点击"""
        logging.info("用户要求切换到收缩末期")
        
        try:
            # 使用期像管理服务进行切换，这样会自动同步所有相关组件
            if self._phase_service:
                success = self._phase_service.switch_to_systole("PhaseSelectionWidget")
                if success:
                    logging.info("通过期像管理服务切换到收缩末期成功")
                    # 不需要手动更新UI，期像管理服务会通过回调自动同步
                else:
                    self._update_status("切换到收缩末期失败，请检查模块一中的期像标记")
                    logging.warning("通过期像管理服务切换到收缩末期失败")
            else:
                # 回退到原来的逻辑（用于兼容性）
                if self._switch_to_end_systole():
                    self.set_current_phase('systole')
                    self._update_status("已切换到收缩末期")
                    self.phaseChanged.emit('systole')
                    logging.info("手动切换到收缩末期成功")
                else:
                    self._update_status("切换到收缩末期失败，请检查模块一中的期像标记")
                    logging.warning("手动切换到收缩末期失败")
                
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")
    
    def _update_phase_button_states(self, active_phase: str):
        """
        更新期像切换按钮的状态
        
        Args:
            active_phase: 当前激活的期像 ('diastole' 或 'systole')
        """
        if active_phase == 'diastole':
            # 舒张末期激活
            if hasattr(self, 'switch_to_diastole_button'):
                self.switch_to_diastole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: 2px solid #1e7e34;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
            if hasattr(self, 'switch_to_systole_button'):
                # 恢复次要样式
                self.switch_to_systole_button.setStyleSheet("")  # 重置为默认次要样式
                
        elif active_phase == 'systole':
            # 收缩末期激活
            if hasattr(self, 'switch_to_systole_button'):
                self.switch_to_systole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 2px solid #bd2130;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
            if hasattr(self, 'switch_to_diastole_button'):
                # 恢复主要样式  
                self.switch_to_diastole_button.setStyleSheet("")  # 重置为默认主要样式
    
    def _update_status(self, message: str):
        """
        更新状态显示
        
        Args:
            message: 状态消息
        """
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
            logging.info(f"期像选择状态更新: {message}")
        
        # 发送状态更新信号
        self.statusUpdated.emit(message)
    
    def set_session(self, session: TAVRStudySession):
        """
        设置会话对象
        
        Args:
            session: TAVR研究会话对象
        """
        self.session = session
    
    # ====== 期像管理服务集成 ======
    def _connect_to_phase_service(self):
        """连接到期像管理服务"""
        try:
            self._phase_service = self.session.get_phase_management_service()
            
            # 注册同步回调
            self._phase_service.register_phase_sync_callback(self._on_external_phase_changed)
            
            # 连接状态更新信号
            self._phase_service.phaseStatusUpdated.connect(self._update_status)
            
            logging.info("PhaseSelectionWidget 已连接到期像管理服务")
            
            # 同步当前期像状态
            current_phase = self._phase_service.get_current_phase()
            if current_phase:
                self._sync_phase_ui(current_phase)
                
        except Exception as e:
            logging.error(f"连接期像管理服务失败: {e}")
    
    def _on_external_phase_changed(self, new_phase: str):
        """
        外部期像变更的回调函数
        
        当其他组件通过期像管理服务切换期像时，此方法会被调用
        
        Args:
            new_phase: 新的期像 ('diastole' 或 'systole')
        """
        if self._is_syncing_from_external:
            return  # 防止无限循环
        
        self._is_syncing_from_external = True
        try:
            logging.info(f"PhaseSelectionWidget 接收到外部期像变更: {new_phase}")
            self._sync_phase_ui(new_phase)
        finally:
            self._is_syncing_from_external = False
    
    def _sync_phase_ui(self, phase: str):
        """
        同步期像UI状态
        
        重构后：只负责UI状态同步，不处理数据可视化
        数据可视化由PhaseManagementService统一管理
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
        """
        if phase not in ['diastole', 'systole']:
            logging.warning(f"无效的期像类型: {phase}")
            return
        
        try:
            # 更新内部状态
            old_phase = self.current_phase
            self.current_phase = phase
            
            # 更新按钮状态
            self._update_phase_button_states(active_phase=phase)
            
            # 如果不是从外部同步，发出期像改变信号
            if not self._is_syncing_from_external:
                self.phaseChanged.emit(phase)
            
            logging.info(f"PhaseSelectionWidget UI已同步到期像: {phase} (数据可视化由服务层统一管理)")
            
        except Exception as e:
            logging.error(f"同步期像UI失败: {e}")
    
    def sync_phase_from_external(self, phase: str):
        """
        从外部同步期像状态
        
        公共API，供其他组件直接调用以同步期像状态
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
        """
        if self._is_syncing_from_external:
            return  # 防止重复同步
        
        self._is_syncing_from_external = True
        try:
            logging.info(f"PhaseSelectionWidget 外部同步期像: {phase}")
            self._sync_phase_ui(phase)
        finally:
            self._is_syncing_from_external = False
    
    def _disconnect_from_phase_service(self):
        """断开与期像管理服务的连接"""
        try:
            if self._phase_service:
                # 取消注册同步回调
                self._phase_service.unregister_phase_sync_callback(self._on_external_phase_changed)
                
                # 断开信号连接
                try:
                    self._phase_service.phaseStatusUpdated.disconnect(self._update_status)
                except:
                    pass  # 信号可能已经断开
                
                logging.info("PhaseSelectionWidget 已断开期像管理服务连接")
        except Exception as e:
            logging.error(f"断开期像管理服务连接失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        # 断开期像管理服务连接
        self._disconnect_from_phase_service()
        logging.info("期像选择组件清理完成")
