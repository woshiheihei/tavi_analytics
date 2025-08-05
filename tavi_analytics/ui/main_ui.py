"""
主界面组件 - TAVR Analytics 主界面管理
"""

import logging
from typing import Optional, Dict, Any
import qt
import slicer
from core.session import TAVRStudySession
from core.module_manager import ModuleManager
from utils.layout_manager import LayoutManager, LayoutType, SizePolicy


class MainUI(qt.QWidget):
    """主界面组件 - 负责整体界面布局和模块协调"""
    
    def __init__(self, session: TAVRStudySession, module_manager: ModuleManager, parent=None):
        """
        初始化主界面
        
        Args:
            session: TAVR研究会话实例
            module_manager: 模块管理器实例
            parent: 父组件
        """
        # 确保正确处理parent参数，避免Qt构造函数匹配问题
        if parent is not None:
            # 确保parent是Qt可以识别的类型
            if hasattr(parent, 'qt_metacast'):
                # 这是一个Qt对象，直接使用
                qt_parent = parent
            else:
                # 不是标准Qt对象，使用None作为安全选择
                qt_parent = None
        else:
            qt_parent = None
            
        # 调用Qt基类构造函数
        super().__init__(qt_parent)
        
        self._session = session
        self._module_manager = module_manager
        self._current_module = None
        self._module_widgets = {}  # 缓存模块组件
        
        # 设置主界面
        self._setup_ui()
        self._setup_connections()
        
        logging.info("主界面组件初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局 - 使用标准化布局管理器
        main_layout = LayoutManager.create_layout(LayoutType.MAIN_CONTAINER, self)
        
        # 设置主界面响应式布局
        LayoutManager.apply_responsive_layout(self, min_width=1000, min_height=700)
        
        # 创建头部区域（标题和全局状态）
        self._create_header_area(main_layout)
        
        # 创建导航区域（模块切换）
        self._create_navigation_area(main_layout)
        
        # 创建内容区域（模块内容）- 使用可滚动容器
        self._create_content_area(main_layout)
        
        # 创建状态栏区域
        self._create_status_area(main_layout)
    
    def _create_header_area(self, parent_layout):
        """创建头部区域"""
        header_frame = qt.QFrame()
        header_frame.setFrameStyle(qt.QFrame.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }
        """)
        
        header_layout = qt.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # 应用标题
        title_label = qt.QLabel("TAVR Analytics - 经导管主动脉瓣置换术分析工作流")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        
        # 添加弹性空间
        header_layout.addStretch()
        
        # 全局状态指示器
        self._status_indicator = qt.QLabel("就绪")
        self._status_indicator.setStyleSheet("""
            QLabel {
                background-color: #27ae60;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self._status_indicator)
        
        parent_layout.addWidget(header_frame)
    
    def _create_navigation_area(self, parent_layout):
        """创建导航区域"""
        nav_frame = LayoutManager.create_section_frame("模块导航", LayoutType.BUTTON_GROUP)
        nav_frame.setMaximumHeight(100)  # 固定导航区域高度
        
        nav_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, nav_frame)
        
        # 创建按钮行
        button_layout = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        
        # 模块切换按钮组
        self._module_buttons = qt.QButtonGroup()
        self._module_buttons.setExclusive(True)
        
        # 获取可用模块并创建按钮
        available_modules = self._module_manager.get_available_modules()
        
        for module_name in available_modules:
            module_info = self._module_manager.get_module_info(module_name)
            if module_info:
                button = LayoutManager.create_button_with_style(module_info.display_name, "primary")
                button.setCheckable(True)
                button.setMinimumWidth(120)
                button.setMinimumHeight(40)
                button.setProperty("module_name", module_name)
                
                self._module_buttons.addButton(button)
                button_layout.addWidget(button)
        
        # 添加弹性空间
        LayoutManager.add_stretch_with_ratio(button_layout, 1)
        
        # 添加导航提示
        nav_hint = qt.QLabel("点击上方按钮切换模块")
        nav_hint.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        nav_hint.setAlignment(qt.Qt.AlignCenter)
        
        nav_layout.addLayout(button_layout)
        nav_layout.addWidget(nav_hint)
        
        # 添加到主布局，固定高度
        parent_layout.addWidget(nav_frame, 0)  # 0 表示固定大小
    
    def _create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建可滚动的内容容器
        self._content_scroll, self._content_container = LayoutManager.create_scrollable_container(LayoutType.MODULE_CONTAINER)
        
        # 创建堆叠组件来管理不同模块的界面
        self._content_stack = qt.QStackedWidget()
        LayoutManager.setup_widget_size_policy(self._content_stack, LayoutType.MODULE_CONTAINER, SizePolicy.EXPANDING)
        
        # 创建默认页面（无模块选中时显示）
        default_page = self._create_default_page()
        self._content_stack.addWidget(default_page)
        
        # 将堆叠组件添加到容器布局中
        container_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self._content_container)
        container_layout.addWidget(self._content_stack)
        
        # 将滚动区域添加到主布局，并设置较大的伸缩因子
        parent_layout.addWidget(self._content_scroll, 3)  # 给内容区域更多空间
    
    def _create_default_page(self):
        """创建默认页面"""
        default_widget = qt.QWidget()
        layout = qt.QVBoxLayout(default_widget)
        layout.setAlignment(qt.Qt.AlignCenter)
        
        # 欢迎信息
        welcome_label = qt.QLabel("欢迎使用 TAVR Analytics")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #34495e;")
        welcome_label.setAlignment(qt.Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # 说明文字
        desc_label = qt.QLabel("请选择上方的模块开始分析工作流")
        desc_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-top: 10px;")
        desc_label.setAlignment(qt.Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        return default_widget
    
    def _create_status_area(self, parent_layout):
        """创建状态栏区域"""
        status_frame = qt.QFrame()
        status_frame.setMaximumHeight(50)  # 增加高度
        status_frame.setFrameStyle(qt.QFrame.StyledPanel)
        
        status_layout = qt.QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # 左侧状态信息组
        left_status_layout = qt.QVBoxLayout()
        
        # 当前患者信息
        self._patient_label = qt.QLabel("患者: 未加载")
        self._patient_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        left_status_layout.addWidget(self._patient_label)
        
        # 数据加载状态
        self._data_status_label = qt.QLabel("数据: 未加载")
        self._data_status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        left_status_layout.addWidget(self._data_status_label)
        
        status_layout.addLayout(left_status_layout)
        
        # 中间弹性空间
        status_layout.addStretch()
        
        # 中间状态信息组  
        center_status_layout = qt.QVBoxLayout()
        
        # 会话状态
        self._session_label = qt.QLabel("会话: 空闲")
        self._session_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        center_status_layout.addWidget(self._session_label)
        
        # 处理进度
        self._progress_label = qt.QLabel("进度: 等待开始")
        self._progress_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        center_status_layout.addWidget(self._progress_label)
        
        status_layout.addLayout(center_status_layout)
        
        # 右侧弹性空间
        status_layout.addStretch()
        
        # 右侧状态信息组
        right_status_layout = qt.QVBoxLayout()
        
        # 系统状态
        self._system_status_label = qt.QLabel("系统: 正常")
        self._system_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        right_status_layout.addWidget(self._system_status_label)
        
        # 时间戳
        import datetime
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self._timestamp_label = qt.QLabel(f"时间: {current_time}")
        self._timestamp_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        right_status_layout.addWidget(self._timestamp_label)
        
        status_layout.addLayout(right_status_layout)
        
        parent_layout.addWidget(status_frame)
        
        # 创建定时器用于更新时间戳
        self._timer = qt.QTimer()
        self._timer.timeout.connect(self._update_timestamp)
        self._timer.start(1000)  # 每秒更新一次
    
    def _setup_connections(self):
        """设置信号连接"""
        # 连接模块切换按钮
        for button in self._module_buttons.buttons():
            button.clicked.connect(self._on_module_button_clicked)
        
        # 监听会话变化（如果需要的话）
        # TODO: 实现会话状态监听
        
        # 设置工具提示
        self._setup_tooltips()
        
        # 设置键盘快捷键
        self._setup_shortcuts()
        
        # 设置右键菜单
        self._setup_context_menus()
    
    def _setup_shortcuts(self):
        """设置键盘快捷键"""
        try:
            # F5: 刷新当前模块
            refresh_shortcut = qt.QShortcut(qt.QKeySequence("F5"), self)
            refresh_shortcut.activated.connect(self._refresh_current_module)
            
            # Ctrl+1: 切换到模块一
            module1_shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+1"), self)
            module1_shortcut.activated.connect(lambda: self._switch_to_module_by_shortcut("module1"))
            
            # Ctrl+R: 重置界面
            reset_shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+R"), self)
            reset_shortcut.activated.connect(self._reset_interface)
            
            # F1: 显示帮助
            help_shortcut = qt.QShortcut(qt.QKeySequence("F1"), self)
            help_shortcut.activated.connect(self._show_help)
            
            logging.info("键盘快捷键设置完成")
            
        except Exception as e:
            logging.warning(f"设置键盘快捷键时出错: {e}")
    
    def _setup_context_menus(self):
        """设置右键菜单"""
        try:
            # 为模块按钮设置右键菜单
            for button in self._module_buttons.buttons():
                button.setContextMenuPolicy(qt.Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, btn=button: self._show_module_context_menu(btn, pos)
                )
        except Exception as e:
            logging.warning(f"设置右键菜单时出错: {e}")
    
    def _show_module_context_menu(self, button, pos):
        """显示模块右键菜单"""
        try:
            module_name = button.property("module_name")
            menu = qt.QMenu(self)
            
            # 激活模块
            activate_action = menu.addAction(f"激活 {button.text()}")
            activate_action.triggered.connect(lambda: self.switch_to_module(module_name))
            
            # 模块信息
            info_action = menu.addAction("模块信息")
            info_action.triggered.connect(lambda: self._show_module_info(module_name))
            
            menu.addSeparator()
            
            # 如果是当前模块，添加刷新选项
            if module_name == self._current_module:
                refresh_action = menu.addAction("刷新模块")
                refresh_action.triggered.connect(lambda: self._refresh_current_module())
            
            # 显示菜单
            menu.exec_(button.mapToGlobal(pos))
            
        except Exception as e:
            logging.error(f"显示右键菜单时出错: {e}")
    
    def _switch_to_module_by_shortcut(self, module_name: str):
        """通过快捷键切换模块"""
        if module_name in self._module_manager.get_available_modules():
            self.switch_to_module(module_name, force=True)  # 快捷键切换不显示确认对话框
        else:
            self._show_info_message("模块不可用", f"模块 {module_name} 当前不可用")
    
    def _refresh_current_module(self):
        """刷新当前模块"""
        if self._current_module:
            self._show_info_message("刷新模块", f"正在刷新模块: {self._current_module}")
            # 这里可以添加实际的刷新逻辑
            self.switch_to_module(self._current_module, force=True)
        else:
            self._show_info_message("无模块", "当前没有激活的模块")
    
    def _reset_interface(self):
        """重置界面"""
        try:
            result = qt.QMessageBox.question(
                self, 
                "重置界面", 
                "确定要重置界面吗？这将清除当前的工作状态。",
                qt.QMessageBox.Yes | qt.QMessageBox.No,
                qt.QMessageBox.No
            )
            
            if result == qt.QMessageBox.Yes:
                # 重置到默认页面
                self._content_stack.setCurrentIndex(0)
                self._current_module = None
                self._update_module_button_state(None)
                
                # 重置状态
                self.update_status("界面已重置", "success")
                self.update_session_status("空闲")
                self.update_progress_status("等待开始")
                
                logging.info("界面已重置")
                
        except Exception as e:
            logging.error(f"重置界面时出错: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
TAVR Analytics 帮助

快捷键:
• F1: 显示此帮助
• F5: 刷新当前模块  
• Ctrl+1: 切换到模块一
• Ctrl+R: 重置界面

操作:
• 点击上方按钮切换模块
• 右键点击按钮查看更多选项
• 查看底部状态栏了解当前状态

模块说明:
• 模块一: 数据导入与场景准备
• 其他模块: 正在开发中
        """
        self._show_info_message("TAVR Analytics 帮助", help_text)
    
    def _show_module_info(self, module_name: str):
        """显示模块信息"""
        module_info = self._module_manager.get_module_info(module_name)
        if module_info:
            info_text = f"""
模块名称: {module_info.display_name}
模块ID: {module_info.name}
状态: {'已启用' if module_info.enabled else '已禁用'}
依赖: {', '.join(module_info.dependencies) if module_info.dependencies else '无'}
            """
            self._show_info_message(f"模块信息 - {module_info.display_name}", info_text)
        else:
            self._show_info_message("模块信息", f"无法获取模块 {module_name} 的信息")
    
    def _setup_tooltips(self):
        """设置工具提示"""
        try:
            # 为状态指示器添加工具提示
            if hasattr(self, '_status_indicator'):
                self._status_indicator.setToolTip("显示当前系统状态和操作进度")
            
            # 为模块按钮添加工具提示
            for button in self._module_buttons.buttons():
                module_name = button.property("module_name")
                module_info = self._module_manager.get_module_info(module_name)
                if module_info:
                    tooltip = f"{module_info.display_name}\n点击切换到此模块"
                    if module_info.dependencies:
                        tooltip += f"\n依赖: {', '.join(module_info.dependencies)}"
                    button.setToolTip(tooltip)
            
            # 为状态标签添加工具提示
            if hasattr(self, '_patient_label'):
                self._patient_label.setToolTip("当前分析的患者信息")
            if hasattr(self, '_session_label'):
                self._session_label.setToolTip("当前会话状态")
            if hasattr(self, '_data_status_label'):
                self._data_status_label.setToolTip("数据加载和处理状态")
            if hasattr(self, '_progress_label'):
                self._progress_label.setToolTip("当前操作进度")
            if hasattr(self, '_system_status_label'):
                self._system_status_label.setToolTip("系统运行状态")
                
        except Exception as e:
            logging.warning(f"设置工具提示时出错: {e}")
    
    def _on_module_button_clicked(self):
        """处理模块按钮点击"""
        sender = self.sender()
        if sender:
            module_name = sender.property("module_name")
            self.switch_to_module(module_name)
    
    def switch_to_module(self, module_name: str, force: bool = False):
        """
        切换到指定模块
        
        Args:
            module_name: 模块名称
            force: 是否强制切换（不显示确认对话框）
        """
        try:
            logging.info(f"切换到模块: {module_name}")
            
            # 如果当前已经是该模块，不需要切换
            if self._current_module == module_name:
                self.update_status("模块已激活")
                return
            
            # 如果有当前模块且未完成工作，显示确认对话框
            if not force and self._current_module and self._session:
                if self._should_confirm_switch():
                    if not self._confirm_module_switch(module_name):
                        return
            
            # 更新状态指示器并显示加载动画
            self._show_loading_state("正在切换模块...")
            
            # 停用当前模块（如果有的话）
            if self._current_module:
                self._module_manager.deactivate_module(self._current_module)
            
            # 激活新模块
            success = self._module_manager.activate_module(module_name)
            if not success:
                self._hide_loading_state()
                self.update_status("模块加载失败", "error")
                self._show_error_message("模块切换失败", f"无法激活模块 {module_name}")
                return
            
            # 获取或创建模块组件
            module_widget = self._get_or_create_module_widget(module_name)
            if not module_widget:
                self._hide_loading_state()
                self.update_status("组件创建失败", "error")
                self._show_error_message("组件创建失败", f"无法创建模块 {module_name} 的界面组件")
                return
            
            # 切换到模块组件
            self._content_stack.setCurrentWidget(module_widget)
            self._current_module = module_name
            
            # 更新界面状态
            module_info = self._module_manager.get_module_info(module_name)
            display_name = module_info.display_name if module_info else module_name
            
            self._hide_loading_state()
            self.update_status(f"已加载: {display_name}", "success")
            self._update_module_button_state(module_name)
            
            # 更新会话状态
            self.update_session_status(f"使用{display_name}")
            
            # 发送用户友好的通知
            self._show_success_notification(f"已切换到: {display_name}")
            
            logging.info(f"成功切换到模块: {module_name}")
            
        except Exception as e:
            logging.error(f"切换模块时出错: {e}")
            self._hide_loading_state()
            self.update_status("切换失败", "error")
            self._show_error_message("切换失败", f"切换到模块 {module_name} 时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _should_confirm_switch(self) -> bool:
        """检查是否需要确认切换"""
        # 这里可以添加逻辑来检查当前模块是否有未保存的工作
        # 目前简单返回False，不显示确认对话框
        return False
    
    def _confirm_module_switch(self, new_module: str) -> bool:
        """显示模块切换确认对话框"""
        try:
            msgBox = qt.QMessageBox()
            msgBox.setIcon(qt.QMessageBox.Question)
            msgBox.setWindowTitle("确认切换模块")
            msgBox.setText(f"您确定要切换到 {new_module} 模块吗？")
            msgBox.setInformativeText("当前模块的工作可能会丢失。")
            msgBox.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No)
            msgBox.setDefaultButton(qt.QMessageBox.No)
            
            result = msgBox.exec_()
            return result == qt.QMessageBox.Yes
        except:
            return True  # 如果对话框创建失败，默认允许切换
    
    def _show_loading_state(self, message: str):
        """显示加载状态"""
        self.update_status(message, "normal")
        # 可以在这里添加加载动画或禁用按钮
        for button in self._module_buttons.buttons():
            button.setEnabled(False)
    
    def _hide_loading_state(self):
        """隐藏加载状态"""
        # 重新启用按钮
        for button in self._module_buttons.buttons():
            button.setEnabled(True)
    
    def _show_error_message(self, title: str, message: str):
        """显示错误消息"""
        try:
            msgBox = qt.QMessageBox()
            msgBox.setIcon(qt.QMessageBox.Critical)
            msgBox.setWindowTitle(title)
            msgBox.setText(message)
            msgBox.exec_()
        except:
            logging.error(f"无法显示错误对话框: {title} - {message}")
    
    def _show_success_notification(self, message: str):
        """显示成功通知"""
        # 这里可以实现一个临时的成功通知
        # 目前只记录到日志
        logging.info(f"用户通知: {message}")
        
    def _show_info_message(self, title: str, message: str):
        """显示信息消息"""
        try:
            msgBox = qt.QMessageBox()
            msgBox.setIcon(qt.QMessageBox.Information)
            msgBox.setWindowTitle(title)
            msgBox.setText(message)
            msgBox.exec_()
        except:
            logging.info(f"信息消息: {title} - {message}")
    
    def _get_or_create_module_widget(self, module_name: str):
        """获取或创建模块组件"""
        # 检查缓存
        if module_name in self._module_widgets:
            return self._module_widgets[module_name]
        
        # 从模块管理器获取组件
        module_widget = self._module_manager.get_module_widget(module_name)
        if module_widget:
            # 添加到堆叠组件
            self._content_stack.addWidget(module_widget)
            # 缓存组件引用
            self._module_widgets[module_name] = module_widget
            return module_widget
        
        return None
    
    def _update_module_button_state(self, active_module: str):
        """更新模块按钮状态"""
        for button in self._module_buttons.buttons():
            module_name = button.property("module_name")
            button.setChecked(module_name == active_module)
    
    def update_status(self, message: str, status_type: str = "normal"):
        """
        更新状态指示器
        
        Args:
            message: 状态消息
            status_type: 状态类型 ("normal", "warning", "error", "success")
        """
        self._status_indicator.setText(message)
        
        # 根据状态类型设置不同的颜色
        color_map = {
            "normal": "#3498db",
            "success": "#27ae60", 
            "warning": "#f39c12",
            "error": "#e74c3c"
        }
        
        color = color_map.get(status_type, "#3498db")
        self._status_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }}
        """)
    
    def update_patient_info(self, patient_id: str = None):
        """
        更新患者信息显示
        
        Args:
            patient_id: 患者ID，None表示清除
        """
        if patient_id:
            self._patient_label.setText(f"患者: {patient_id}")
            self._patient_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        else:
            self._patient_label.setText("患者: 未加载")
            self._patient_label.setStyleSheet("color: #7f8c8d;")
    
    def update_session_status(self, status: str):
        """
        更新会话状态显示
        
        Args:
            status: 会话状态描述
        """
        self._session_label.setText(f"会话: {status}")
    
    def update_data_status(self, status: str):
        """
        更新数据状态显示
        
        Args:
            status: 数据状态描述
        """
        if hasattr(self, '_data_status_label'):
            self._data_status_label.setText(f"数据: {status}")
    
    def update_progress_status(self, progress: str):
        """
        更新处理进度显示
        
        Args:
            progress: 进度描述
        """
        if hasattr(self, '_progress_label'):
            self._progress_label.setText(f"进度: {progress}")
    
    def update_system_status(self, status: str, status_type: str = "normal"):
        """
        更新系统状态显示
        
        Args:
            status: 系统状态描述
            status_type: 状态类型 ("normal", "warning", "error", "success")
        """
        if hasattr(self, '_system_status_label'):
            self._system_status_label.setText(f"系统: {status}")
            
            # 根据状态类型设置颜色
            color_map = {
                "normal": "#3498db",
                "success": "#27ae60",
                "warning": "#f39c12", 
                "error": "#e74c3c"
            }
            
            color = color_map.get(status_type, "#3498db")
            self._system_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def _update_timestamp(self):
        """更新时间戳显示"""
        if hasattr(self, '_timestamp_label'):
            import datetime
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self._timestamp_label.setText(f"时间: {current_time}")
    
    def update_comprehensive_status(self, patient_id: str = None, data_status: str = None, 
                                   session_status: str = None, progress: str = None,
                                   system_status: str = None, system_type: str = "normal"):
        """
        一次性更新所有状态显示
        
        Args:
            patient_id: 患者ID
            data_status: 数据状态
            session_status: 会话状态  
            progress: 处理进度
            system_status: 系统状态
            system_type: 系统状态类型
        """
        if patient_id is not None:
            self.update_patient_info(patient_id)
        
        if data_status is not None:
            self.update_data_status(data_status)
        
        if session_status is not None:
            self.update_session_status(session_status)
        
        if progress is not None:
            self.update_progress_status(progress)
        
        if system_status is not None:
            self.update_system_status(system_status, system_type)
    
    def auto_activate_default_module(self):
        """自动激活默认模块（模块一）"""
        if "module1" in self._module_manager.get_available_modules():
            # 设置按钮状态
            for button in self._module_buttons.buttons():
                if button.property("module_name") == "module1":
                    button.setChecked(True)
                    break
            
            # 切换到模块一
            self.switch_to_module("module1")
    
    def refresh_navigation(self):
        """刷新导航区域（当模块注册状态改变时）"""
        try:
            # 清除现有按钮
            for button in self._module_buttons.buttons():
                self._module_buttons.removeButton(button)
                button.setParent(None)
                button.deleteLater()
            
            # 获取当前可用模块
            available_modules = self._module_manager.get_available_modules()
            
            # 重新创建按钮
            button_layout = None
            nav_frame = None
            
            # 找到导航框架和按钮布局
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, qt.QFrame) and widget.maximumHeight() == 80:
                        nav_frame = widget
                        if nav_frame.layout():
                            for j in range(nav_frame.layout().count()):
                                layout_item = nav_frame.layout().itemAt(j)
                                if layout_item and isinstance(layout_item, qt.QHBoxLayout):
                                    button_layout = layout_item
                                    break
                        break
            
            if button_layout:
                # 重新创建按钮
                for module_name in available_modules:
                    module_info = self._module_manager.get_module_info(module_name)
                    if module_info:
                        button = qt.QPushButton(module_info.display_name)
                        button.setCheckable(True)
                        button.setMinimumWidth(120)
                        button.setMinimumHeight(40)
                        button.setProperty("module_name", module_name)
                        
                        # 设置样式和连接
                        button.setStyleSheet("""
                            QPushButton {
                                background-color: #ecf0f1;
                                border: 2px solid #bdc3c7;
                                border-radius: 5px;
                                padding: 8px;
                                font-weight: bold;
                            }
                            QPushButton:checked {
                                background-color: #3498db;
                                color: white;
                                border-color: #2980b9;
                            }
                            QPushButton:hover {
                                background-color: #d5dbdb;
                            }
                            QPushButton:checked:hover {
                                background-color: #5dade2;
                            }
                        """)
                        
                        button.clicked.connect(self._on_module_button_clicked)
                        self._module_buttons.addButton(button)
                        
                        # 在弹性空间之前插入按钮
                        button_layout.insertWidget(button_layout.count() - 1, button)
            
            logging.info("导航区域已刷新")
            
        except Exception as e:
            logging.error(f"刷新导航区域失败: {e}")
    
    def enable_module_button(self, module_name: str, enabled: bool = True):
        """
        启用或禁用指定模块的按钮
        
        Args:
            module_name: 模块名称
            enabled: 是否启用
        """
        for button in self._module_buttons.buttons():
            if button.property("module_name") == module_name:
                button.setEnabled(enabled)
                if not enabled:
                    button.setChecked(False)
                break
    
    def get_current_module(self) -> Optional[str]:
        """获取当前激活的模块名称"""
        return self._current_module
    
    def cleanup(self):
        """清理资源"""
        # 停止定时器
        if hasattr(self, '_timer') and self._timer:
            self._timer.stop()
            self._timer = None
        
        # 清理模块组件缓存
        for widget in self._module_widgets.values():
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
        
        self._module_widgets.clear()
        
        logging.info("主界面组件清理完成")
