"""
模块一主界面

该模块提供TAVR分析的模块一完整界面，包括：
- 数据导入与配置
- 心动周期管理
- 状态显示
- 患者信息管理

模块一是TAVR分析流程的第一步，负责数据准备和基础配置。

作者：TAVR Research Team
创建时间：2024
"""

import qt
import slicer
from typing import Optional
import logging
import vtk

try:
    from ..core.session import TAVRStudySession
    from ..core.data_models import PatientData
    from ..core.enums import ImageQuality, FollowUpTimepoint
    from .data_loading_dialog import DataLoadingDialog
    from .cardiac_cycle_widget import CardiacCycleWidget
    from .status_display_widget import StatusDisplayWidget
    from ..utils.config_manager import ConfigManager
    from ..utils.qt_utils import QtUtils
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..ui.styles import ComponentStyleFactory, StyleManager
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from core.data_models import PatientData
    from core.enums import ImageQuality, FollowUpTimepoint
    from ui.styles import ComponentStyleFactory, StyleManager
    # 使用当前目录导入
    current_module_dir = os.path.dirname(__file__)
    if current_module_dir not in sys.path:
        sys.path.insert(0, current_module_dir)
    from data_loading_dialog import DataLoadingDialog
    from cardiac_cycle_widget import CardiacCycleWidget
    from status_display_widget import StatusDisplayWidget
    from utils.config_manager import ConfigManager
    from utils.qt_utils import QtUtils
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy


class Module1Widget(qt.QWidget):
    """模块一主界面
    
    提供TAVR分析的第一步功能：数据准备和基础配置
    """
    
    # 信号定义
    dataConfigured = qt.Signal()  # 数据配置完成信号
    phasesMarked = qt.Signal()    # 关键时相标记完成信号
    readyForNextModule = qt.Signal()  # 准备进入下一模块信号
    
    def __init__(self, session: TAVRStudySession, parent=None, logic=None):
        """初始化模块一界面
        
        Args:
            session: TAVR研究会话对象
            parent: 父窗口对象 (可以是None)
            logic: 业务逻辑实例
        """
        # 确保parent参数适用于Qt
        if parent is not None and not isinstance(parent, qt.QWidget):
            # 如果传入的不是QWidget，设为None
            parent = None
        
        super().__init__(parent)
        self.session = session
        self.logic = logic
        self.config_manager = ConfigManager()
        
        # 设置组件大小策略 - 使用标准化布局管理器
        LayoutManager.setup_widget_size_policy(self, LayoutType.MODULE_CONTAINER, SizePolicy.EXPANDING)
        
        # 子组件
        self.data_loading_dialog = None
        self.cardiac_cycle_widget = None
        self.status_display_widget = None

        # 事件监听/去抖
        self._scene_observer_tags = []
        self._browser_observer_tag = None
        self._browser_node_ref = None
        self._refresh_timer = qt.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(120)  # 轻量去抖
        self._refresh_timer.timeout.connect(self._update_interface_state)
        
        # 初始化界面
        self._init_ui()
        self._setup_connections()
        
        # 初始化自动刷新监听
        self._init_auto_refresh()
        
        # 检查现有数据
        self._check_existing_data()
        
        logging.info("模块一界面初始化完成")
        
    def _init_ui(self):
        """初始化用户界面（方案C：右侧信息侧栏）"""
        # 根布局
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 水平分栏：左主区 + 右侧栏
        self._splitter = qt.QSplitter(qt.Qt.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(6)

        # 左侧：主工作区（数据导入 + 心动周期管理）
        left_container = qt.QWidget()
        left_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, left_container)

        # 数据导入区域（置于主区顶部）
        self._create_data_import_section(left_layout)

        # 心动周期管理组件（主要内容，扩展占位）
        self.cardiac_cycle_widget = CardiacCycleWidget(self.session, self)
        LayoutManager.setup_widget_size_policy(self.cardiac_cycle_widget, LayoutType.CONTROL_PANEL, SizePolicy.EXPANDING)
        left_layout.addWidget(self.cardiac_cycle_widget, 1)

        # 右侧：信息侧栏（状态 + 进度 + CTA）
        right_container = qt.QWidget()
        right_container.setMinimumWidth(260)
        right_container.setMaximumWidth(380)
        right_layout = LayoutManager.create_layout(LayoutType.INFO_DISPLAY, right_container)

        # 状态与进度（紧凑展示，默认收起详情）
        self.status_display_widget = StatusDisplayWidget(self.session, self, compact=True)
        LayoutManager.setup_widget_size_policy(self.status_display_widget, LayoutType.INFO_DISPLAY, SizePolicy.PREFERRED)
        self.status_display_widget.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
        # 连接进度变更，更新底部进度标签
        try:
            self.status_display_widget.progressChanged.connect(self._on_progress_changed)
        except Exception:
            pass
        right_layout.addWidget(self.status_display_widget, 0)

        # 使用弹性空白将操作区推到底部
        right_layout.addStretch(1)

        # 操作按钮区域（侧栏底部，包含继续/重置/重新检测/进度）
        self._create_action_buttons_section(right_layout)

        # 装配分栏并设置伸缩比例
        self._splitter.addWidget(left_container)
        self._splitter.addWidget(right_container)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)

        # 将分栏加入根布局
        main_layout.addWidget(self._splitter, 1)

        # 连接相位标记信号以实时刷新
        try:
            self.cardiac_cycle_widget.phaseMarked.connect(lambda _: self._update_interface_state())
        except Exception:
            pass

    def _on_progress_changed(self, completed: int, total: int):
        """侧栏进度变化时更新底部提示"""
        if hasattr(self, 'next_progress_label') and self.next_progress_label:
            self.next_progress_label.setText(f"已完成 {completed}/{total} 项")
        
    def _create_data_import_section(self, parent_layout):
        """创建数据导入区域"""
        import_group = LayoutManager.create_section_frame("数据导入", LayoutType.SECTION_CONTAINER)
        import_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, import_group)
        
        # 说明文本
        instruction_label = qt.QLabel(
            "请点击下方按钮导入4D心脏CT数据并配置患者信息。"
            "支持从DICOM浏览器加载或从现有场景数据创建序列。"
        )
        instruction_label.setWordWrap(True)
        # 使用新的shadcn/ui样式系统
        styles = ComponentStyleFactory.get_module1_styles()
        instruction_label.setStyleSheet(styles["instruction_label"])
        import_layout.addWidget(instruction_label)
        
        # 数据导入按钮 - 使用统一的按钮创建方法
        self.load_data_button = LayoutManager.create_button_with_style(
            text="数据导入与配置", 
            button_type="primary", 
            size="default", 
            min_height=40
        )
        import_layout.addWidget(self.load_data_button)
        
        parent_layout.addWidget(import_group, 0)  # 固定大小
        
    def _create_action_buttons_section(self, parent_layout):
        """创建操作按钮区域"""
        actions_group = LayoutManager.create_section_frame("操作", LayoutType.BUTTON_GROUP)
        actions_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, actions_group)
        
        # 按钮布局
        button_layout = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        
        # 重新检测按钮（原“刷新状态”） - 次要样式，兜底自检入口
        self.refresh_button = LayoutManager.create_button_with_style(
            text="重新检测", 
            button_type="secondary", 
            size="default", 
            min_height=35
        )
        self.refresh_button.setToolTip("手动触发一次完整状态自检并刷新界面（当自动刷新不生效时使用）")
        button_layout.addWidget(self.refresh_button)
        
        # 重置数据按钮 - 使用统一的按钮创建方法
        self.reset_button = LayoutManager.create_button_with_style(
            text="重置数据", 
            button_type="destructive", 
            size="default", 
            min_height=35
        )
        button_layout.addWidget(self.reset_button)
        
        actions_layout.addLayout(button_layout)
        
        # 主CTA：继续（与后续模块解耦）
        self.next_module_button = LayoutManager.create_button_with_style(
            text="继续", 
            button_type="primary", 
            size="default", 
            min_height=40
        )
        self.next_module_button.setEnabled(False)
        actions_layout.addWidget(self.next_module_button)

        # 进度提示（小字）
        self.next_progress_label = qt.QLabel("")
        self.next_progress_label.setStyleSheet(StyleManager.get_label_style("muted"))
        actions_layout.addWidget(self.next_progress_label)
        
        parent_layout.addWidget(actions_group, 0)  # 固定大小
        
    def _setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.load_data_button.clicked.connect(self._on_load_data_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.next_module_button.clicked.connect(self._on_next_module_clicked)
        
    def _init_auto_refresh(self):
        """初始化MRML场景与关键节点的自动刷新监听"""
        try:
            self._attach_scene_observers()
            self._ensure_browser_observer()
        except Exception as e:
            logging.error(f"初始化自动刷新监听失败: {e}")

    def _attach_scene_observers(self):
        """监听场景级别事件，驱动界面状态的自动刷新"""
        self._detach_scene_observers()
        scene = slicer.mrmlScene
        try:
            for ev in [scene.NodeAddedEvent, scene.NodeRemovedEvent, scene.EndBatchProcessEvent]:
                tag = scene.AddObserver(ev, self._on_scene_event)
                self._scene_observer_tags.append(tag)
        except Exception as e:
            logging.error(f"绑定场景事件失败: {e}")

    def _detach_scene_observers(self):
        scene = slicer.mrmlScene
        for tag in self._scene_observer_tags:
            try:
                scene.RemoveObserver(tag)
            except Exception:
                pass
        self._scene_observer_tags = []

    def _on_scene_event(self, caller, event):
        """场景事件回调：节点增删/批处理结束后调度刷新，并确保浏览器监听"""
        try:
            self._ensure_browser_observer()
            self._schedule_interface_refresh()
        except Exception as e:
            logging.debug(f"场景事件回调异常: {e}")

    def _ensure_browser_observer(self):
        """确保监听当前序列浏览器节点的修改事件"""
        try:
            browser = self.session.get_sequence_browser_node()
            # 若节点改变或之前未监听，则重新绑定
            if browser is not self._browser_node_ref:
                self._detach_browser_observer()
                if browser:
                    try:
                        self._browser_observer_tag = browser.AddObserver(vtk.vtkCommand.ModifiedEvent, self._on_browser_modified)
                        self._browser_node_ref = browser
                    except Exception as e:
                        logging.debug(f"绑定浏览器节点事件失败: {e}")
        except Exception as e:
            logging.debug(f"确保浏览器监听失败: {e}")

    def _detach_browser_observer(self):
        if self._browser_node_ref and self._browser_observer_tag:
            try:
                self._browser_node_ref.RemoveObserver(self._browser_observer_tag)
            except Exception:
                pass
        self._browser_observer_tag = None
        self._browser_node_ref = None

    def _on_browser_modified(self, caller, event):
        """浏览器节点修改（如当前帧变化），调度轻量刷新"""
        self._schedule_interface_refresh()

    def _schedule_interface_refresh(self):
        """去抖调度界面刷新，避免频繁事件导致抖动"""
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def _check_existing_data(self):
        """检查现有数据并更新界面状态"""
        try:
            # 检查场景中是否已有序列数据
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            if sequence_nodes:
                logging.info(f"发现 {len(sequence_nodes)} 个序列节点")
                
            # 更新状态显示
            self._update_interface_state()
            
        except Exception as e:
            logging.error(f"检查现有数据时发生错误: {str(e)}")
            
    def _on_load_data_clicked(self):
        """处理数据导入按钮点击"""
        try:
            # 获取瓣膜配置
            valve_config = self.config_manager.load_valve_config()
            
            # 创建并显示数据加载对话框
            # 正确的参数顺序：(parent, session, valve_config, logic)
            self.data_loading_dialog = DataLoadingDialog(
                parent=self, 
                session=self.session, 
                valve_config=valve_config, 
                logic=self.logic
            )
                
            # 连接对话框信号
            self.data_loading_dialog.dataLoaded.connect(self._on_data_loaded)
            
            # 显示对话框
            result = self.data_loading_dialog.exec_()
            
            if result == qt.QDialog.Accepted:
                logging.info("数据导入对话框完成")
            else:
                logging.info("数据导入对话框被取消")
                
        except Exception as e:
            logging.error(f"打开数据导入对话框时发生错误: {str(e)}")
            qt.QMessageBox.critical(
                self, "错误", 
                f"无法打开数据导入对话框：\n{str(e)}"
            )
            
    def _on_data_loaded(self):
        """处理数据加载完成"""
        try:
            logging.info("数据加载完成，激活心动周期管理")
            # 确保刷新监听绑定到新浏览器节点
            self._ensure_browser_observer()
            # 激活心动周期管理
            success = self.cardiac_cycle_widget.activate()
            if success:
                # 更新界面状态
                self._update_interface_state()
                
                # 发出数据配置完成信号
                self.dataConfigured.emit()
                
                logging.info("模块一数据配置完成")
            else:
                logging.warning("激活心动周期管理失败")
                
        except Exception as e:
            logging.error(f"处理数据加载完成时发生错误: {str(e)}")
            
    def _on_refresh_clicked(self):
        """处理重新检测按钮点击（兜底自检）"""
        try:
            logging.info("执行模块一重新检测：重绑观察者、刷新状态与子组件")
            self.refresh_button.setEnabled(False)
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

            # 重新绑定场景与浏览器观察者，确保自动刷新可用
            try:
                self._detach_scene_observers()
                self._attach_scene_observers()
                self._ensure_browser_observer()
            except Exception as e:
                logging.debug(f"重新绑定观察者时发生问题: {e}")
            
            # 刷新状态显示
            self.status_display_widget.update_status()
            
            # 刷新心动周期显示
            self.cardiac_cycle_widget.refresh_display()
            
            # 更新界面状态（含步骤清单、CTA）
            self._update_interface_state()
            
        except Exception as e:
            logging.error(f"重新检测时发生错误: {str(e)}")
        finally:
            try:
                qt.QApplication.restoreOverrideCursor()
            except Exception:
                pass
            self.refresh_button.setEnabled(True)
            
    def _on_reset_clicked(self):
        """处理重置按钮点击"""
        try:
            # 确认对话框
            reply = qt.QMessageBox.question(
                self, "确认重置", 
                "确定要重置所有数据吗？这将清除当前的配置和标记。",
                qt.QMessageBox.Yes | qt.QMessageBox.No,
                qt.QMessageBox.No
            )
            
            if reply == qt.QMessageBox.Yes:
                logging.info("重置模块一数据")
                
                # 重置会话
                self.session.reset()
                
                # 停用心动周期管理
                self.cardiac_cycle_widget.deactivate()
                
                # 更新界面状态
                self._update_interface_state()
                
                logging.info("模块一数据重置完成")
                
        except Exception as e:
            logging.error(f"重置数据时发生错误: {str(e)}")
            
    def _on_next_module_clicked(self):
        """处理进入下一模块按钮点击"""
        try:
            # 检查是否满足进入下一模块的条件
            if self._check_ready_for_next_module():
                logging.info("准备进入模块二")
                # 先发出信号，供上层监听（保持兼容）
                self.readyForNextModule.emit()
                # 直接在插件中导航到模块二（与模块二跳转到模块三的方式一致）
                self._navigate_to_module2()
            else:
                # 显示未满足条件的提示
                missing_items = self._get_missing_requirements()
                qt.QMessageBox.information(
                    self, "未满足条件", 
                    "进入下一模块需要完成以下步骤：\n" + "\n".join(missing_items)
                )
                
        except Exception as e:
            logging.error(f"检查下一模块条件时发生错误: {str(e)}")

    def _navigate_to_module2(self):
        """跳转到 module2（全自动分析）标签页"""
        try:
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            if hasattr(plugin, 'main_ui') and plugin.main_ui:
                plugin.main_ui.switch_to_module("module2")
            else:
                # 后备：通过插件暴露的模块管理器激活
                if hasattr(plugin, 'module_manager') and plugin.module_manager:
                    plugin.module_manager.activate_module("module2")
                else:
                    # 最终后备：直接使用全局单例的ModuleManager
                    try:
                        from ..core.module_manager import ModuleManager as _MM
                    except Exception:
                        from core.module_manager import ModuleManager as _MM
                    _MM().activate_module("module2")
            logging.info("已跳转到模块二（全自动分析）")
        except Exception as e:
            logging.error(f"跳转到模块二失败: {e}")
            try:
                qt.QMessageBox.warning(self, "跳转失败", "无法跳转到模块二，请稍后重试。")
            except Exception:
                pass
            
    def _update_button_style(self, button: qt.QPushButton, button_type: str, size: str = "default"):
        """更新按钮样式的辅助方法
        
        Args:
            button: 要更新样式的按钮
            button_type: 按钮类型
            size: 按钮大小
        """
        # 使用LayoutManager提供的统一样式更新接口
        LayoutManager.update_button_style(button, button_type, size)
    
    def _get_step_status(self) -> dict:
        """计算步骤清单状态"""
        status = {"data_imported": False, "patient_info": False, "phase_ed": False, "phase_es": False}
        try:
            # 数据导入状态：只检查序列数据是否已加载
            status["data_imported"] = bool(self.session.volume_sequence_node_id is not None)
            
            # 患者信息状态：检查患者ID和瓣膜信息是否完整
            patient_data = self.session.patient_data
            has_patient_id = bool(patient_data and getattr(patient_data, 'patientID', None))
            has_valve_info = bool(patient_data and 
                                getattr(patient_data, 'valveBrand', None) and 
                                getattr(patient_data, 'valveModel', None))
            status["patient_info"] = has_patient_id and has_valve_info
            
            # 时相标记状态
            ed = self.session.get_marked_phase('end_diastole')
            es = self.session.get_marked_phase('end_systole')
            status["phase_ed"] = ed.get('frame_index') is not None if isinstance(ed, dict) else False
            status["phase_es"] = es.get('frame_index') is not None if isinstance(es, dict) else False
        except Exception as e:
            logging.error(f"计算步骤状态时发生错误: {str(e)}")
        return status

    def _update_interface_state(self):
        """更新界面状态"""
        try:
            # 统一由状态组件内部更新状态与进度
            self.status_display_widget.update_status()

            # CTA可用性
            ready_for_next = self._check_ready_for_next_module()
            self.next_module_button.setEnabled(ready_for_next)
            self.next_module_button.setText("继续")

            # 样式与提示
            if ready_for_next:
                self._update_button_style(self.next_module_button, "primary", "default")
                self.next_module_button.setToolTip("继续到下一步")
            else:
                self._update_button_style(self.next_module_button, "secondary", "default")
                missing_items = self._get_missing_requirements()
                self.next_module_button.setToolTip("需要完成：\n" + "\n".join(missing_items))
                
        except Exception as e:
            logging.error(f"更新界面状态时发生错误: {str(e)}")
            
    def _check_ready_for_next_module(self) -> bool:
        """检查是否准备好进入下一模块
        
        Returns:
            是否可以进入下一模块
        """
        try:
            # 基本数据检查
            if not self.session.is_ready():
                return False
                
            # 检查关键时相是否已标记
            end_diastole = self.session.get_marked_phase('end_diastole')
            end_systole = self.session.get_marked_phase('end_systole')
            
            phases_marked = (
                end_diastole.get('frame_index') is not None and
                end_systole.get('frame_index') is not None
            )
            
            return phases_marked
            
        except Exception as e:
            logging.error(f"检查下一模块条件时发生错误: {str(e)}")
            return False
            
    def _get_missing_requirements(self) -> list:
        """获取未满足的条件列表
        
        Returns:
            未满足条件的描述列表
        """
        missing = []
        
        try:
            # 检查基本数据
            if not self.session.is_ready():
                missing.append("• 导入并配置4D心脏CT数据")
                
            # 检查患者信息
            patient_data = self.session.patient_data
            if not patient_data or not patient_data.patientID:
                missing.append("• 填写完整的患者信息")
                
            # 检查时相标记
            end_diastole = self.session.get_marked_phase('end_diastole')
            end_systole = self.session.get_marked_phase('end_systole')
            
            if end_diastole.get('frame_index') is None:
                missing.append("• 标记舒张末期时相")
                
            if end_systole.get('frame_index') is None:
                missing.append("• 标记收缩末期时相")
                
        except Exception as e:
            logging.error(f"获取缺失条件时发生错误: {str(e)}")
            missing.append("• 检查系统状态时发生错误")
            
        return missing
        
    def get_session(self) -> TAVRStudySession:
        """获取会话对象
        
        Returns:
            TAVR研究会话对象
        """
        return self.session
        
    def get_cardiac_cycle_widget(self) -> CardiacCycleWidget:
        """获取心动周期管理组件
        
        Returns:
            心动周期管理组件
        """
        return self.cardiac_cycle_widget
        
    def get_status_display_widget(self) -> StatusDisplayWidget:
        """获取状态显示组件
        
        Returns:
            状态显示组件
        """
        return self.status_display_widget
        
    def is_ready_for_next_module(self) -> bool:
        """检查是否准备好进入下一模块
        
        Returns:
            是否可以进入下一模块
        """
        return self._check_ready_for_next_module()
        
    def cleanup(self):
        """清理资源"""
        try:
            # 清理监听
            self._detach_browser_observer()
            self._detach_scene_observers()
            if self._refresh_timer and self._refresh_timer.isActive():
                self._refresh_timer.stop()
            # 清理子组件
            if self.cardiac_cycle_widget:
                self.cardiac_cycle_widget.deactivate()
                
            if self.data_loading_dialog:
                self.data_loading_dialog.close()
                
            logging.info("模块一界面清理完成")
            
        except Exception as e:
            logging.error(f"清理模块一界面时发生错误: {str(e)}")
