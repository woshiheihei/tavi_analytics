"""
紧凑期像切换组件 - 行内切换开关

提供舒张末期和收缩末期的紧凑切换界面，适用于在标题栏等空间受限的区域使用。
"""

import logging
from typing import Optional
import qt

try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager


class CompactPhaseToggle(qt.QWidget):
    """
    紧凑期像切换组件
    
    提供舒张末期和收缩末期的紧凑切换界面，特点：
    - 行内显示，占用空间小
    - 两段式切换开关设计
    - 实时切换，状态可随事件更新
    - 可嵌入到标题区域或工具栏
    """
    
    # 定义信号
    phaseChanged = qt.Signal(str)  # 期像改变信号，参数为期像类型 ('diastole' 或 'systole')
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """
        初始化紧凑期像切换组件
        
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
        # 领域模型使用的期像键
        self.phase_domain_keys = {
            'diastole': 'end_diastole',
            'systole': 'end_systole',
        }
        
        # 设置组件属性
        self.setObjectName("CompactPhaseToggle")
        self.setFixedHeight(32)  # 固定高度以保持紧凑
        
        # 期像管理服务集成
        self._phase_service = None
        self._is_syncing_from_external = False
        
        # 创建界面
        self._setup_ui()
        
        # 连接到期像管理服务
        self._connect_to_phase_service()
        
        logging.info("CompactPhaseToggle 初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局 - 水平布局，紧凑排列
        main_layout = qt.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        
        # 期像标签
        phase_label = qt.QLabel("期像:")
        phase_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        main_layout.addWidget(phase_label)
        
        # 切换开关容器
        toggle_container = qt.QWidget()
        toggle_container.setFixedSize(120, 26)
        toggle_container.setStyleSheet("""
            QWidget {
                background-color: #e9ecef;
                border-radius: 13px;
                border: 1px solid #ced4da;
            }
        """)
        
        # 切换按钮布局
        toggle_layout = qt.QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(2, 2, 2, 2)
        toggle_layout.setSpacing(0)
        
        # 舒张末期按钮
        self.diastole_button = qt.QPushButton("舒张")
        self.diastole_button.setFixedSize(56, 22)
        self.diastole_button.setCheckable(True)
        self.diastole_button.setToolTip("切换到舒张末期 (推荐用于全自动分析)")
        self.diastole_button.clicked.connect(self._on_diastole_clicked)
        
        # 收缩末期按钮
        self.systole_button = qt.QPushButton("收缩")
        self.systole_button.setFixedSize(56, 22)
        self.systole_button.setCheckable(True)
        self.systole_button.setToolTip("切换到收缩末期 (用于动态分析)")
        self.systole_button.clicked.connect(self._on_systole_clicked)
        
        # 设置按钮样式
        self._setup_button_styles()
        
        toggle_layout.addWidget(self.diastole_button)
        toggle_layout.addWidget(self.systole_button)
        
        main_layout.addWidget(toggle_container)
        
        # 状态指示器 - 小圆点
        self.status_indicator = qt.QLabel("●")
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setAlignment(qt.Qt.AlignCenter)
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10px;
            }
        """)
        self.status_indicator.setToolTip("期像状态指示")
        main_layout.addWidget(self.status_indicator)
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def _setup_button_styles(self):
        """设置按钮样式"""
        # 未激活状态样式
        inactive_style = """
            QPushButton {
                background-color: transparent;
                color: #6c757d;
                border: none;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """
        
        # 激活状态样式 - 舒张末期 (绿色)
        diastole_active_style = """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """
        
        # 激活状态样式 - 收缩末期 (红色)
        systole_active_style = """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """
        
        # 存储样式
        self.button_styles = {
            'inactive': inactive_style,
            'diastole_active': diastole_active_style,
            'systole_active': systole_active_style
        }
        
        # 初始化为未激活状态
        self.diastole_button.setStyleSheet(inactive_style)
        self.systole_button.setStyleSheet(inactive_style)
    
    def _on_diastole_clicked(self):
        """处理舒张末期按钮点击"""
        if self.diastole_button.isChecked():
            logging.info("用户切换到舒张末期")
            self._switch_to_phase('diastole')
        else:
            # 防止取消选择
            self.diastole_button.setChecked(True)
    
    def _on_systole_clicked(self):
        """处理收缩末期按钮点击"""
        if self.systole_button.isChecked():
            logging.info("用户切换到收缩末期")
            self._switch_to_phase('systole')
        else:
            # 防止取消选择
            self.systole_button.setChecked(True)
    
    def _switch_to_phase(self, phase: str):
        """切换到指定期像"""
        try:
            # 使用期像管理服务进行切换
            if self._phase_service:
                success = False
                if phase == 'diastole':
                    success = self._phase_service.switch_to_diastole("CompactPhaseToggle")
                elif phase == 'systole':
                    success = self._phase_service.switch_to_systole("CompactPhaseToggle")
                
                if success:
                    logging.info(f"通过期像管理服务切换到{phase}成功")
                else:
                    logging.warning(f"通过期像管理服务切换到{phase}失败")
                    self._reset_button_states()
            else:
                # 回退到直接切换
                success = self._direct_switch_to_phase(phase)
                if success:
                    self.set_current_phase(phase)
                    self.phaseChanged.emit(phase)
                else:
                    self._reset_button_states()
                    
        except Exception as e:
            logging.error(f"切换期像失败: {e}")
            self._reset_button_states()
    
    def _direct_switch_to_phase(self, phase: str) -> bool:
        """直接切换到指定期像"""
        try:
            phase_info = self.session.get_marked_phase(self.phase_domain_keys[phase])
            if not phase_info:
                logging.warning(f"未找到{phase}标记")
                return False
            
            frame_index = phase_info.get('frame_index')
            if frame_index is None:
                logging.warning(f"{phase}标记中缺少帧索引信息")
                return False
            
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("未找到序列浏览器节点")
                return False
            
            browser_node.SetSelectedItemNumber(frame_index)
            logging.info(f"成功切换到帧 {frame_index} ({phase})")
            return True
            
        except Exception as e:
            logging.error(f"直接切换期像失败: {e}")
            return False
    
    def set_current_phase(self, phase: str):
        """
        设置当前期像并更新UI状态
        
        重构后：只负责UI状态更新，不处理数据可视化
        数据可视化由PhaseManagementService统一管理
        """
        if phase not in ['diastole', 'systole']:
            logging.warning(f"无效的期像类型: {phase}")
            return
        
        old_phase = self.current_phase
        self.current_phase = phase
        
        # 更新按钮状态
        self._update_button_states(phase)
        
        # 更新状态指示器
        self._update_status_indicator(phase)
        
        logging.info(f"CompactPhaseToggle 期像设置为: {phase} (数据可视化由服务层管理)")
    
    def _update_button_states(self, active_phase: str):
        """更新按钮状态"""
        # 重置所有按钮的选中状态
        self.diastole_button.setChecked(False)
        self.systole_button.setChecked(False)
        
        if active_phase == 'diastole':
            self.diastole_button.setChecked(True)
            self.diastole_button.setStyleSheet(self.button_styles['diastole_active'])
            self.systole_button.setStyleSheet(self.button_styles['inactive'])
        elif active_phase == 'systole':
            self.systole_button.setChecked(True)
            self.systole_button.setStyleSheet(self.button_styles['systole_active'])
            self.diastole_button.setStyleSheet(self.button_styles['inactive'])
    
    def _reset_button_states(self):
        """重置按钮状态到当前期像"""
        if self.current_phase:
            self._update_button_states(self.current_phase)
        else:
            self.diastole_button.setChecked(False)
            self.systole_button.setChecked(False)
            self.diastole_button.setStyleSheet(self.button_styles['inactive'])
            self.systole_button.setStyleSheet(self.button_styles['inactive'])
    
    def _update_status_indicator(self, phase: str):
        """更新状态指示器"""
        if phase == 'diastole':
            self.status_indicator.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    font-size: 10px;
                }
            """)
            self.status_indicator.setToolTip("当前: 舒张末期")
        elif phase == 'systole':
            self.status_indicator.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    font-size: 10px;
                }
            """)
            self.status_indicator.setToolTip("当前: 收缩末期")
        else:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 10px;
                }
            """)
            self.status_indicator.setToolTip("期像状态指示")
    
    def get_current_phase(self) -> Optional[str]:
        """获取当前选择的期像"""
        return self.current_phase
    
    # ====== 期像管理服务集成 ======
    def _connect_to_phase_service(self):
        """连接到期像管理服务"""
        try:
            self._phase_service = self.session.get_phase_management_service()
            
            # 注册同步回调
            self._phase_service.register_phase_sync_callback(self._on_external_phase_changed)
            
            logging.info("CompactPhaseToggle 已连接到期像管理服务")
            
            # 同步当前期像状态
            current_phase = self._phase_service.get_current_phase()
            if current_phase:
                self._sync_phase_ui(current_phase)
                
        except Exception as e:
            logging.error(f"连接期像管理服务失败: {e}")
    
    def _on_external_phase_changed(self, new_phase: str):
        """外部期像变更的回调函数"""
        if self._is_syncing_from_external:
            return
        
        self._is_syncing_from_external = True
        try:
            logging.info(f"CompactPhaseToggle 接收到外部期像变更: {new_phase}")
            self._sync_phase_ui(new_phase)
        finally:
            self._is_syncing_from_external = False
    
    def _sync_phase_ui(self, phase: str):
        """
        同步期像UI状态
        
        重构后：只负责UI状态同步，不处理数据可视化
        数据可视化由PhaseManagementService统一管理
        """
        if phase not in ['diastole', 'systole']:
            return
        
        try:
            # 更新内部状态
            old_phase = self.current_phase
            self.current_phase = phase
            
            # 更新按钮状态
            self._update_button_states(phase)
            
            # 更新状态指示器
            self._update_status_indicator(phase)
            
            # 如果不是从外部同步，发出期像改变信号
            if not self._is_syncing_from_external:
                self.phaseChanged.emit(phase)
            
            logging.info(f"CompactPhaseToggle UI已同步到期像: {phase} (数据可视化由服务层统一管理)")
            
        except Exception as e:
            logging.error(f"同步期像UI失败: {e}")
    
    def sync_phase_from_external(self, phase: str):
        """从外部同步期像状态"""
        if self._is_syncing_from_external:
            return
        
        self._is_syncing_from_external = True
        try:
            logging.info(f"CompactPhaseToggle 外部同步期像: {phase}")
            self._sync_phase_ui(phase)
        finally:
            self._is_syncing_from_external = False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self._phase_service:
                self._phase_service.unregister_phase_sync_callback(self._on_external_phase_changed)
            logging.info("CompactPhaseToggle 清理完成")
        except Exception as e:
            logging.error(f"CompactPhaseToggle 清理失败: {e}")