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

try:
    from ..core.session import TAVRStudySession
    from ..core.data_models import PatientData
    from ..core.enums import ImageQuality, FollowUpTimepoint
    from .data_loading_dialog import DataLoadingDialog
    from .cardiac_cycle_widget import CardiacCycleWidget
    from .status_display_widget import StatusDisplayWidget
    from .step_checklist_widget import StepChecklistWidget
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
    from step_checklist_widget import StepChecklistWidget
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
        self.step_checklist = None
        
        # 初始化界面
        self._init_ui()
        self._setup_connections()
        
        # 检查现有数据
        self._check_existing_data()
        
        logging.info("模块一界面初始化完成")
        
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局 - 使用标准化布局管理器
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)
        
        # 状态显示组件
        self.status_display_widget = StatusDisplayWidget(self.session, self)
        LayoutManager.setup_widget_size_policy(self.status_display_widget, LayoutType.INFO_DISPLAY, SizePolicy.PREFERRED)
        main_layout.addWidget(self.status_display_widget, 0)  # 固定大小

        # 步骤清单组件（实时进度）
        self.step_checklist = StepChecklistWidget(self)
        LayoutManager.setup_widget_size_policy(self.step_checklist, LayoutType.INFO_DISPLAY, SizePolicy.PREFERRED)
        main_layout.addWidget(self.step_checklist, 0)
        
        # 数据导入按钮区域
        self._create_data_import_section(main_layout)
        
        # 心动周期管理组件 - 主要内容区域
        self.cardiac_cycle_widget = CardiacCycleWidget(self.session, self)
        LayoutManager.setup_widget_size_policy(self.cardiac_cycle_widget, LayoutType.CONTROL_PANEL, SizePolicy.EXPANDING)
        main_layout.addWidget(self.cardiac_cycle_widget, 2)  # 获得最多空间
        
        # 操作按钮区域
        self._create_action_buttons_section(main_layout)
        
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
        
        # 刷新状态按钮 - 使用统一的按钮创建方法
        self.refresh_button = LayoutManager.create_button_with_style(
            text="刷新状态", 
            button_type="secondary", 
            size="default", 
            min_height=35
        )
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
        
        # 进入下一模块按钮 - 单独一行，使用统一的按钮创建方法
        self.next_module_button = LayoutManager.create_button_with_style(
            text="进入模块二：瓣膜分割", 
            button_type="primary", 
            size="default", 
            min_height=40
        )
        self.next_module_button.setEnabled(False)
        actions_layout.addWidget(self.next_module_button)
        
        parent_layout.addWidget(actions_group, 0)  # 固定大小
        
    def _setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.load_data_button.clicked.connect(self._on_load_data_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.next_module_button.clicked.connect(self._on_next_module_clicked)
        
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
        """处理刷新按钮点击"""
        try:
            logging.info("刷新模块一状态")
            
            # 刷新状态显示
            self.status_display_widget.update_status()
            
            # 刷新心动周期显示
            self.cardiac_cycle_widget.refresh_display()
            
            # 更新界面状态
            self._update_interface_state()
            
        except Exception as e:
            logging.error(f"刷新状态时发生错误: {str(e)}")
            
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
                self.readyForNextModule.emit()
            else:
                # 显示未满足条件的提示
                missing_items = self._get_missing_requirements()
                qt.QMessageBox.information(
                    self, "未满足条件", 
                    "进入下一模块需要完成以下步骤：\n" + "\n".join(missing_items)
                )
                
        except Exception as e:
            logging.error(f"检查下一模块条件时发生错误: {str(e)}")
            
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
            status["data_imported"] = bool(self.session.is_ready())
            patient_data = self.session.patient_data
            status["patient_info"] = bool(patient_data and getattr(patient_data, 'patientID', None))
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
            # 更新状态显示
            self.status_display_widget.update_status()

            # 更新步骤清单
            if self.step_checklist:
                self.step_checklist.update_steps(self._get_step_status())
            
            # 检查是否可以进入下一模块
            ready_for_next = self._check_ready_for_next_module()
            self.next_module_button.setEnabled(ready_for_next)
            
            if ready_for_next:
                self.next_module_button.setText("进入模块二：瓣膜分割")
                # 使用统一的样式更新方法
                self._update_button_style(self.next_module_button, "primary", "default")
            else:
                self.next_module_button.setText("等待数据配置完成...")
                # 使用统一的样式更新方法，secondary样式表示未就绪
                self._update_button_style(self.next_module_button, "secondary", "default")
                
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
            # 清理子组件
            if self.cardiac_cycle_widget:
                self.cardiac_cycle_widget.deactivate()
                
            if self.data_loading_dialog:
                self.data_loading_dialog.close()
                
            logging.info("模块一界面清理完成")
            
        except Exception as e:
            logging.error(f"清理模块一界面时发生错误: {str(e)}")
