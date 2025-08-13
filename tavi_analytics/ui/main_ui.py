"""
主界面组件 - TAVR Analytics 主界面管理
"""

import logging
import os
from typing import Optional, Dict, Any
import qt
import slicer
import traceback
from core.session import TAVRStudySession
from core.module_manager import ModuleManager
from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
from ui.styles import ComponentStyleFactory
from utils.dev_utils import DevUtils


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
        LayoutManager.apply_responsive_layout(self, min_width=400, min_height=700)
        
        # 创建导航区域（模块切换和状态显示）
        self._create_navigation_area(main_layout)
        
        # 创建内容区域（模块内容）- 使用可滚动容器
        self._create_content_area(main_layout)

        # 如果处于开发者模式（默认开启），添加开发者面板
        try:
            flag = str(os.environ.get("TAVI_DEBUG", "1")).strip().lower()
            if flag not in ("0", "false", "off"):
                self._create_developer_panel(main_layout)
        except Exception as e:
            logging.warning(f"检查开发者模式失败: {e}")
    
    def _create_navigation_area(self, parent_layout):
        """创建导航区域（模块切换按钮）"""
        nav_frame = LayoutManager.create_section_frame("模块导航", LayoutType.BUTTON_GROUP)
        nav_frame.setMaximumHeight(60)  # 降低高度，只需要容纳按钮行
        
        nav_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, nav_frame)
        
        # 获取样式集合
        styles = ComponentStyleFactory.get_main_ui_styles()
        
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
                button = qt.QPushButton(module_info.display_name)
                button.setCheckable(True)
                button.setMinimumWidth(120)
                button.setMinimumHeight(40)
                button.setProperty("module_name", module_name)
                
                # 应用新的shadcn/ui样式
                button.setStyleSheet(styles["module_button"])
                
                # 连接点击事件  <--- START: 删除下面这一行
                # button.clicked.connect(self._on_module_button_clicked)
                # <--- END: 删除上面这一行
                
                self._module_buttons.addButton(button)
                button_layout.addWidget(button)
        
        # 添加弹性空间
        LayoutManager.add_stretch_with_ratio(button_layout, 1)
        
        nav_layout.addLayout(button_layout)
        
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
        
        # 将滚动区域添加到主布局，并设置最大的伸缩因子
        parent_layout.addWidget(self._content_scroll, 1)  # 内容区域占用所有剩余空间

    def _create_developer_panel(self, parent_layout):
        """创建开发者工具面板（仅在TAVI_DEBUG启用时显示）"""
        try:
            # 使用标准化的区域框架，避免自定义样式覆盖造成标题排版问题
            frame = LayoutManager.create_section_frame("开发者工具", LayoutType.SECTION_CONTAINER)
            
            # 为开发者面板添加特殊的背景色来突出显示
            frame.setStyleSheet("""
                QGroupBox {
                    background-color: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 8px;
                    margin-top: 1ex;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    background-color: #fef3c7;
                }
            """)

            # 水平按钮行，减小边距让按钮更紧凑
            layout = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
            layout.setContentsMargins(8, 4, 8, 4)  # 更紧凑的边距

            # 直接使用LayoutManager统一的按钮工厂创建现代化样式的按钮
            save_btn = LayoutManager.create_button_with_style("保存会话", button_type="outline", size="sm", min_height=36)
            load_btn = LayoutManager.create_button_with_style("加载会话", button_type="outline", size="sm", min_height=36)

            # 设置按钮最小宽度以获得更好的外观
            save_btn.setMinimumWidth(80)
            load_btn.setMinimumWidth(80)

            layout.addWidget(save_btn)
            layout.addWidget(load_btn)
            LayoutManager.add_stretch_with_ratio(layout, 1)

            frame.setLayout(layout)
            parent_layout.insertWidget(0, frame)  # 放在最上方

            # 绑定事件
            save_btn.clicked.connect(self._save_debug_session)
            load_btn.clicked.connect(self._load_debug_session)

            self._dev_panel = frame
        except Exception as e:
            logging.warning(f"创建开发者面板失败: {e}")

    def _save_debug_session(self):
        """保存调试会话快照"""
        try:
            # QInputDialog.getText 也可能有类似的返回值问题
            result = qt.QInputDialog.getText(self, "保存会话", "请输入会话名称:")
            
            if isinstance(result, tuple) and len(result) == 2:
                # 标准 (text, ok) 格式
                name, ok = result
                if not ok:
                    return
                name = str(name).strip()
            elif isinstance(result, str):
                # 直接返回输入的文本
                name = str(result).strip()
            else:
                # 未知格式或用户取消
                return
            
            if not name:
                self._show_error_message("输入错误", "会话名称不能为空")
                return
            
            result = DevUtils.save_debug_session(self._session, name)
            if result.get("success"):
                self._show_info_message("保存成功", f"已保存到: {result.get('path')}")
            else:
                self._show_error_message("保存失败", result.get("message", "未知错误"))
        except Exception as e:
            logging.exception("保存调试会话异常")
            self._show_error_message("保存失败", str(e))

    def _load_debug_session(self):
        """加载调试会话快照"""
        try:
            sessions = DevUtils.list_sessions()
            if not sessions:
                self._show_info_message("加载会话", "未发现已保存的会话")
                return

            try:
                # QInputDialog.getItem 在不同环境下返回值不同
                # 标准Qt: (item, ok) tuple
                # Slicer环境: 可能只返回 item string 或者其他格式
                result = qt.QInputDialog.getItem(self, "加载会话", "选择会话:", sessions, 0, False)
                
                if isinstance(result, tuple) and len(result) == 2:
                    # 标准 (item, ok) 格式
                    item, ok = result
                    if not ok:
                        return
                    name = str(item)
                elif isinstance(result, str):
                    # 直接返回选中的字符串
                    name = result
                    if not name or name not in sessions:
                        return
                else:
                    # 未知格式，尝试转换为字符串
                    name = str(result)
                    if not name or name not in sessions:
                        return
            except Exception as e:
                logging.error(f"加载会话对话框出错: {e}")
                self._show_error_message("对话框错误", f"无法显示会话选择对话框: {str(e)}")
                return

            # 加载
            result = DevUtils.load_debug_session(self._session, name)
            if result.get("success"):
                # 刷新UI：回到默认页并提示
                if self._content_stack and self._content_stack.count > 0:
                    self._content_stack.setCurrentIndex(0)
                self._current_module = None
                self._update_module_button_state(None)
                self.update_status("会话已加载，UI已刷新", "success")
                self._show_info_message("加载成功", f"已加载会话: {name}")
            else:
                self._show_error_message("加载失败", result.get("message", "未知错误"))
        except Exception as e:
            logging.exception("加载调试会话异常")
            self._show_error_message("加载失败", str(e))
    
    def _create_default_page(self):
        """创建默认页面"""
        default_widget = qt.QWidget()
        layout = qt.QVBoxLayout(default_widget)
        layout.setAlignment(qt.Qt.AlignCenter)
        
        # 获取样式集合
        styles = ComponentStyleFactory.get_main_ui_styles()
        
        # 欢迎信息
        welcome_label = qt.QLabel("欢迎使用 TAVR Analytics")
        welcome_label.setStyleSheet(styles["welcome_label"])
        welcome_label.setAlignment(qt.Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # 说明文字
        desc_label = qt.QLabel("请选择上方的模块开始分析工作流")
        desc_label.setStyleSheet(styles["description_label"])
        desc_label.setAlignment(qt.Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        return default_widget
    
    def _setup_connections(self):
        """设置信号连接"""
        # <--- START: 用下面这行代码替换掉之前删除的 for 循环
        self._module_buttons.buttonClicked.connect(self._on_module_button_clicked)
        # <--- END: 完成替换
        
        # 监听会话变化（如果需要的话）
        # TODO: 实现会话状态监听
        
        # 设置工具提示
        self._setup_tooltips()
        
        # 设置右键菜单
        self._setup_context_menus()
    
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
                refresh_action.triggered.connect(lambda: self.switch_to_module(module_name, force=True))
            
            # 显示菜单
            menu.exec_(button.mapToGlobal(pos))
            
        except Exception as e:
            logging.error(f"显示右键菜单时出错: {e}")
    
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
                
                logging.info("界面已重置")
                
        except Exception as e:
            logging.error(f"重置界面时出错: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
TAVR Analytics 帮助

操作:
• 点击上方按钮切换模块
• 右键点击按钮查看更多选项
• 关键操作信息会在控制台中显示

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
            # 为模块按钮添加工具提示
            for button in self._module_buttons.buttons():
                module_name = button.property("module_name")
                module_info = self._module_manager.get_module_info(module_name)
                if module_info:
                    tooltip = f"{module_info.display_name}\n点击切换到此模块"
                    if module_info.dependencies:
                        tooltip += f"\n依赖: {', '.join(module_info.dependencies)}"
                    button.setToolTip(tooltip)
                
        except Exception as e:
            logging.warning(f"设置工具提示时出错: {e}")
    
    # <--- START: 修改这个方法的定义
    def _on_module_button_clicked(self, button):
        """处理模块按钮点击"""
        if button:
            module_name = button.property("module_name")
            if module_name:
                self.switch_to_module(module_name)
    # <--- END: 方法修改完成
    
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
        logging.info(f"加载状态: {message}")
        # 禁用按钮防止重复操作
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
        记录状态到控制台日志
        
        Args:
            message: 状态消息
            status_type: 状态类型 ("normal", "warning", "error", "success")
        """
        # 根据状态类型选择日志级别
        if status_type == "error":
            logging.error(f"状态更新: {message}")
        elif status_type == "warning":
            logging.warning(f"状态更新: {message}")
        elif status_type == "success":
            logging.info(f"状态更新: {message}")
        else:
            logging.info(f"状态更新: {message}")

    def update_patient_info(self):
        """更新患者信息显示（场景关闭时清空）"""
        # 这个方法目前只是占位符，因为患者信息显示逻辑
        # 主要在各个模块中处理，主界面暂时不需要特殊的患者信息显示
        logging.info("患者信息已清空")

    def update_session_status(self, status: str):
        """更新会话状态"""
        # 这个方法也是占位符，会话状态主要通过update_status方法显示
        self.update_status(f"会话状态: {status}")
    
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
                    if isinstance(widget, qt.QFrame) and widget.maximumHeight() == 60:
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
                        styles = ComponentStyleFactory.get_main_ui_styles()
                        button.setStyleSheet(styles["module_button"])
                        
                        # 不需要单独连接信号，使用按钮组统一处理
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
        # 清理模块组件缓存
        for widget in self._module_widgets.values():
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
        
        self._module_widgets.clear()
        
        logging.info("主界面组件清理完成")
