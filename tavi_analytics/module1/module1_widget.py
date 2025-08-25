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
    from ..widgets import SectionCard
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
    from widgets import SectionCard
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
        """初始化用户界面（简洁的垂直布局）"""
        # 根布局
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 数据导入section
        self._create_data_import_section(main_layout)
        
        # 添加间隔
        main_layout.addSpacing(20)

        # 心动周期管理section
        self.cardiac_cycle_widget = CardiacCycleWidget(self.session, self)
        main_layout.addWidget(self.cardiac_cycle_widget, 0)  # 固定大小
        
        # 添加间隔
        main_layout.addSpacing(20)

        # 分析流程section
        self._create_action_buttons_section(main_layout)

        # 弹性空间，将内容推到顶部
        main_layout.addStretch(1)

        # 连接相位标记信号以实时刷新
        try:
            self.cardiac_cycle_widget.phaseMarked.connect(lambda _: self._update_interface_state())
        except Exception:
            pass


    def _create_data_import_section(self, parent_layout):
        """创建数据导入区域 - 使用通用SectionCard (蓝色主题)"""
        section = SectionCard(title="1. 数据加载与验证", icon_text="📁", variant="blue", parent=self)
        main_layout = section.body_layout

        # 描述文本
        self.description_label = qt.QLabel("选择TAVR术后4D心脏CT DICOM数据序列")
        self.description_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #424242;
                background: transparent;
                padding: 0px;
                margin-left: 4px;
            }
            """
        )
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.description_label)

        # 按钮容器
        button_container = qt.QWidget()
        button_layout = qt.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(12)

        # 主要操作按钮 - 蓝色风格
        self.primary_action_button = qt.QPushButton("📁 加载4D DICOM序列")
        self.primary_action_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42a5f5, stop:1 #1e88e5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
            }
            QPushButton:disabled {
                background: #e0e0e0;
                color: #9e9e9e;
            }
            """
        )
        button_layout.addWidget(self.primary_action_button)
        button_layout.addStretch()
        main_layout.addWidget(button_container)

        # 状态指示区域（初始隐藏）
        self.status_container = qt.QWidget()
        self.status_container.setVisible(False)
        status_layout = qt.QHBoxLayout(self.status_container)
        status_layout.setContentsMargins(4, 8, 4, 0)
        status_layout.setSpacing(8)

        # 状态图标
        self.status_icon_label = qt.QLabel("")
        self.status_icon_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                color: #4caf50;
                background: transparent;
            }
            """
        )
        status_layout.addWidget(self.status_icon_label)

        # 状态文本
        self.status_text_label = qt.QLabel("")
        self.status_text_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #2e7d32;
                background: transparent;
                font-weight: 500;
            }
            """
        )
        self.status_text_label.setWordWrap(True)
        status_layout.addWidget(self.status_text_label, 1)

        main_layout.addWidget(self.status_container)

        parent_layout.addWidget(section, 0)  # 固定大小，不拉伸
        
    def _create_action_buttons_section(self, parent_layout):
        """创建分析流程操作区域 - 简洁版本"""
        actions_group = LayoutManager.create_section_frame("分析流程", LayoutType.BUTTON_GROUP)
        actions_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, actions_group)
        
        # 设置紧凑的size policy
        actions_group.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
        
        # 主CTA：开始全自动分析
        self.next_module_button = LayoutManager.create_button_with_style(
            text="开始全自动分析", 
            button_type="primary", 
            size="default", 
            min_height=40
        )
        self.next_module_button.setEnabled(False)
        actions_layout.addWidget(self.next_module_button)

        # 状态提示标签
        self.status_info_label = qt.QLabel("请先完成数据导入和时相标记")
        self.status_info_label.setStyleSheet(
            "QLabel { color: #666; font-size: 12px; text-align: center; padding: 8px; }"
        )
        self.status_info_label.setAlignment(qt.Qt.AlignCenter)
        actions_layout.addWidget(self.status_info_label)
        
        parent_layout.addWidget(actions_group, 0)  # 固定大小
        
    def _setup_connections(self):
        """设置信号连接"""
        # 主按钮连接
        self.primary_action_button.clicked.connect(self._on_primary_action_clicked)
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
            
    def _on_primary_action_clicked(self):
        """处理主要操作按钮点击（导入数据或重新导入）"""
        self._on_load_data_clicked()
            
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
            
    def _on_reimport_data_clicked(self):
        """处理重新导入数据菜单项点击"""
        try:
            # 询问用户是否保留患者信息
            reply = qt.QMessageBox.question(
                self, "重新导入数据", 
                "重新导入数据时，是否保留当前的患者信息？\n\n"
                "选择'是'将保留患者基本信息，只重新导入4D CT序列。\n"
                "选择'否'将完全重新开始配置。",
                qt.QMessageBox.Yes | qt.QMessageBox.No | qt.QMessageBox.Cancel,
                qt.QMessageBox.Yes
            )
            
            if reply == qt.QMessageBox.Cancel:
                return
                
            # 保存当前患者信息（如果用户选择保留）
            saved_patient_data = None
            if reply == qt.QMessageBox.Yes:
                saved_patient_data = self.session.patient_data.__dict__.copy()
                
            # 清除序列相关数据
            self.session.clear_sequence_data()
            
            # 停用心动周期管理
            self.cardiac_cycle_widget.deactivate()
            
            # 恢复患者信息（如果需要）
            if saved_patient_data:
                for key, value in saved_patient_data.items():
                    setattr(self.session.patient_data, key, value)
            
            # 更新界面状态
            self._update_interface_state()
            
            # 自动打开数据导入对话框
            self._on_load_data_clicked()
            
            logging.info("重新导入数据流程启动")
                
        except Exception as e:
            logging.error(f"重新导入数据时发生错误: {str(e)}")
            
    def _on_clear_data_clicked(self):
        """处理清除所有数据菜单项点击"""
        try:
            # 确认对话框
            reply = qt.QMessageBox.question(
                self, "确认清除数据", 
                "确定要清除所有数据吗？\n\n这将删除：\n"
                "• 当前导入的4D CT序列\n"
                "• 患者信息和瓣膜配置\n"
                "• 心脏时相标记\n\n此操作无法撤销。",
                qt.QMessageBox.Yes | qt.QMessageBox.No,
                qt.QMessageBox.No
            )
            
            if reply == qt.QMessageBox.Yes:
                logging.info("清除模块一所有数据")
                
                # 重置会话
                self.session.reset()
                
                # 停用心动周期管理
                self.cardiac_cycle_widget.deactivate()
                
                # 更新界面状态
                self._update_interface_state()
                
                # 显示成功提示
                qt.QMessageBox.information(
                    self, "清除完成", 
                    "所有数据已清除，可以重新开始导入数据。"
                )
                
                logging.info("模块一数据清除完成")
                
        except Exception as e:
            logging.error(f"清除数据时发生错误: {str(e)}")
            
    def _on_refresh_status_clicked(self):
        """处理刷新状态菜单项点击（兜底自检）"""
        try:
            logging.info("执行模块一状态刷新：重绑观察者、刷新状态与子组件")
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

            # 重新绑定场景与浏览器观察者，确保自动刷新可用
            try:
                self._detach_scene_observers()
                self._attach_scene_observers()
                self._ensure_browser_observer()
            except Exception as e:
                logging.debug(f"重新绑定观察者时发生问题: {e}")
            
            # 刷新心动周期显示
            self.cardiac_cycle_widget.refresh_display()
            
            # 更新界面状态
            self._update_interface_state()
            
            # 显示成功提示
            qt.QMessageBox.information(
                self, "刷新完成", 
                "界面状态已刷新。"
            )
            
        except Exception as e:
            logging.error(f"刷新状态时发生错误: {str(e)}")
            qt.QMessageBox.warning(
                self, "刷新失败", 
                f"刷新状态时发生错误：{str(e)}"
            )
        finally:
            try:
                qt.QApplication.restoreOverrideCursor()
            except Exception:
                pass
            
    def _on_next_module_clicked(self):
        """处理开始全自动分析按钮点击"""
        try:
            # 检查是否满足启动分析的条件
            if self._check_ready_for_next_module():
                logging.info("准备启动全自动分析流程")
                # 先发出信号，供上层监听（保持兼容）
                self.readyForNextModule.emit()
                # 跳转到模块二并自动启动分析
                self._navigate_to_module2_and_start_analysis()
            else:
                # 显示未满足条件的提示
                missing_items = self._get_missing_requirements()
                qt.QMessageBox.information(
                    self, "未满足条件", 
                    "启动全自动分析需要完成以下步骤：\n" + "\n".join(missing_items)
                )
                
        except Exception as e:
            logging.error(f"检查分析启动条件时发生错误: {str(e)}")

    def _navigate_to_module2_and_start_analysis(self):
        """跳转到模块二并自动启动分析"""
        try:
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            if hasattr(plugin, 'main_ui') and plugin.main_ui:
                # 跳转到模块二并传递自动启动标记
                plugin.main_ui.switch_to_module("module2", auto_start_analysis=True)
            else:
                # 后备：通过插件暴露的模块管理器激活
                if hasattr(plugin, 'module_manager') and plugin.module_manager:
                    plugin.module_manager.activate_module("module2", auto_start_analysis=True)
                else:
                    # 最终后备：直接使用全局单例的ModuleManager
                    try:
                        from ..core.module_manager import ModuleManager as _MM
                    except Exception:
                        from core.module_manager import ModuleManager as _MM
                    _MM().activate_module("module2", auto_start_analysis=True)
            logging.info("已跳转到模块二并启动全自动分析")
        except Exception as e:
            logging.error(f"跳转到模块二并启动分析失败: {e}")
            try:
                qt.QMessageBox.warning(self, "启动失败", "无法启动全自动分析，请稍后重试。")
            except Exception:
                pass

    def _navigate_to_module2(self):
        """跳转到 module2（全自动分析）标签页 - 保留兼容性"""
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
        """更新界面状态 - 简化版本"""
        try:
            # 检查数据状态
            has_data = self.session.is_ready()
            
            # 更新数据导入区域
            self._update_data_import_section(has_data)

            # CTA可用性
            ready_for_next = self._check_ready_for_next_module()
            self.next_module_button.setEnabled(ready_for_next)

            # 状态提示和按钮样式
            if ready_for_next:
                self._update_button_style(self.next_module_button, "primary", "default")
                self.next_module_button.setToolTip("启动全自动分析流程")
                self.status_info_label.setText("✅ 准备就绪，可以开始分析")
                self.status_info_label.setStyleSheet(
                    "QLabel { color: #2d5a3d; font-size: 12px; text-align: center; padding: 8px; "
                    "background-color: #e8f5e8; border-radius: 4px; }"
                )
            else:
                self._update_button_style(self.next_module_button, "secondary", "default")
                missing_items = self._get_missing_requirements()
                self.next_module_button.setToolTip("需要完成：\n" + "\n".join(missing_items))
                if has_data:
                    self.status_info_label.setText("⏳ 请完成心脏时相标记")
                    self.status_info_label.setStyleSheet(
                        "QLabel { color: #8a6d3b; font-size: 12px; text-align: center; padding: 8px; "
                        "background-color: #fcf8e3; border-radius: 4px; }"
                    )
                else:
                    self.status_info_label.setText("📂 请先导入4D心脏CT数据")
                    self.status_info_label.setStyleSheet(
                        "QLabel { color: #666; font-size: 12px; text-align: center; padding: 8px; }"
                    )
                
        except Exception as e:
            logging.error(f"更新界面状态时发生错误: {str(e)}")
            
    def _update_data_import_section(self, has_data: bool):
        """根据数据状态更新数据导入区域 - 适配新的蓝色卡片风格"""
        try:
            if has_data:
                # 有数据状态
                sequence_node = self.session.get_volume_sequence_node()
                if sequence_node:
                    num_frames = sequence_node.GetNumberOfDataNodes()
                    node_name = sequence_node.GetName()
                    
                    # 更新描述文本
                    self.description_label.setText(f"✅ 已成功导入4D序列数据")
                    self.description_label.setStyleSheet("""
                        QLabel {
                            font-size: 14px;
                            color: #2e7d32;
                            background: transparent;
                            padding: 0px;
                            margin-left: 4px;
                            font-weight: 500;
                        }
                    """)
                    
                    # 显示状态容器
                    self.status_container.setVisible(True)
                    self.status_icon_label.setText("✅")
                    self.status_text_label.setText(f"序列名称：{node_name} | 帧数：{num_frames}")
                    
                    # 更新按钮
                    self.primary_action_button.setText("🔄 重新导入序列")
                    self.primary_action_button.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #66bb6a, stop:1 #4caf50);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 12px 24px;
                            font-size: 14px;
                            font-weight: bold;
                            min-height: 20px;
                        }
                        QPushButton:hover {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #81c784, stop:1 #66bb6a);
                        }
                        QPushButton:pressed {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #4caf50, stop:1 #43a047);
                        }
                    """)
                    self.primary_action_button.setToolTip("重新导入4D心脏CT数据")
                    
                else:
                    # 数据异常状态
                    self.description_label.setText("⚠️ 数据状态异常，建议重新导入")
                    self.description_label.setStyleSheet("""
                        QLabel {
                            font-size: 14px;
                            color: #f57c00;
                            background: transparent;
                            padding: 0px;
                            margin-left: 4px;
                            font-weight: 500;
                        }
                    """)
                    
                    self.status_container.setVisible(False)
                    
                    # 更新按钮为重新导入状态
                    self.primary_action_button.setText("🔄 重新导入序列")
                    self.primary_action_button.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #ff9800, stop:1 #f57c00);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 12px 24px;
                            font-size: 14px;
                            font-weight: bold;
                            min-height: 20px;
                        }
                        QPushButton:hover {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #ffb74d, stop:1 #ff9800);
                        }
                        QPushButton:pressed {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #f57c00, stop:1 #ef6c00);
                        }
                    """)
                    self.primary_action_button.setToolTip("重新导入4D心脏CT数据")
                    
                    
            else:
                # 无数据状态
                self.description_label.setText("选择TAVR术后4D心脏CT DICOM数据序列")
                self.description_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #424242;
                        background: transparent;
                        padding: 0px;
                        margin-left: 4px;
                    }
                """)
                
                # 隐藏状态容器
                self.status_container.setVisible(False)
                
                # 更新按钮为初始状态
                self.primary_action_button.setText("📁 加载4D DICOM序列")
                self.primary_action_button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #2196f3, stop:1 #1976d2);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-size: 14px;
                        font-weight: bold;
                        min-height: 20px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #42a5f5, stop:1 #1e88e5);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #1976d2, stop:1 #1565c0);
                    }
                    QPushButton:disabled {
                        background: #e0e0e0;
                        color: #9e9e9e;
                    }
                """)
                self.primary_action_button.setToolTip("导入4D心脏CT数据并配置患者信息")
                
        except Exception as e:
            logging.error(f"更新数据导入区域时发生错误: {str(e)}")
            
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

