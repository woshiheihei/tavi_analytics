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
from ui.navigation_bar import NavigationBar
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

        # 成员初始化
        self._session = session
        self._module_manager = module_manager
        self._current_module = None
        self._module_widgets = {}  # 缓存模块组件
        self._dev_panel = None     # 开发者面板（可隐藏）
        self._main_layout = None   # 主布局引用，便于动态插入开发者面板
        # 导航栏组件引用
        self._navigation_bar = None

        # 设置主界面
        self._setup_ui()
        self._setup_connections()

        logging.info("主界面组件初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局 - 使用标准化布局管理器
        main_layout = LayoutManager.create_layout(LayoutType.MAIN_CONTAINER, self)
        self._main_layout = main_layout
        
        # 设置主界面响应式布局
        LayoutManager.apply_responsive_layout(self, min_width=400, min_height=700)
        
        # 创建导航栏组件
        self._create_navigation_bar(main_layout)
        
        # 创建内容区域（模块内容）- 使用可滚动容器
        self._create_content_area(main_layout)
        
        # 设置导航栏连接（必须在导航栏创建后进行）
        self._setup_navigation_connections()

        # 开发者面板：按偏好/环境显示（可用快捷键随时切换）
        try:
            settings = qt.QSettings()
            pref = settings.value("TAVRAnalytics/DeveloperPanelVisible", None)
            if pref is None:
                # 默认遵循环境变量（默认开启）
                flag = str(os.environ.get("TAVI_DEBUG", "1")).strip().lower()
                show_dev = flag not in ("0", "false", "off")
            else:
                show_dev = str(pref).strip().lower() in ("1", "true", "on", "yes")

            if show_dev:
                self._create_developer_panel(main_layout)
        except Exception as e:
            logging.warning(f"检查开发者模式失败: {e}")
    
    def _create_navigation_bar(self, parent_layout):
        """创建导航栏组件"""
        self._navigation_bar = NavigationBar(self._module_manager, self)
        parent_layout.addWidget(self._navigation_bar, 0)
    
    def _create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建可滚动的内容容器
        self._content_scroll, self._content_container = LayoutManager.create_scrollable_container(LayoutType.MODULE_CONTAINER)
        try:
            # 由主界面统一管理滚动条
            self._content_scroll.setWidgetResizable(True)
            self._content_scroll.setFrameShape(qt.QFrame.NoFrame)
            self._content_scroll.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
            self._content_scroll.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        except Exception:
            pass
        
        # 创建堆叠组件来管理不同模块的界面
        self._content_stack = qt.QStackedWidget()
        # 使用内容驱动的高度，在外层滚动
        try:
            self._content_stack.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
        except Exception:
            pass
        
        # 创建默认页面（无模块选中时显示）
        default_page = self._create_default_page()
        self._content_stack.addWidget(default_page)
        
        # 将堆叠组件添加到容器布局中
        container_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self._content_container)
        try:
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(8)
            container_layout.setSizeConstraint(qt.QLayout.SetMinimumSize)
            self._content_container.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
        except Exception:
            pass
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
                if self._navigation_bar:
                    self._navigation_bar.set_current_module(None)
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
    
    def _setup_navigation_connections(self):
        """设置导航栏信号连接"""
        if self._navigation_bar:
            self._navigation_bar.moduleRequested.connect(self.switch_to_module)
            self._navigation_bar.moduleInfoRequested.connect(self._show_module_info)
            self._navigation_bar.moduleRefreshRequested.connect(
                lambda module_name: self.switch_to_module(module_name, force=True)
            )
    
    def _setup_connections(self):
        """设置信号连接"""
        # 开发者面板快捷键（Ctrl+Alt+D）
        try:
            self._dev_toggle_shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+Alt+D"), self)
            self._dev_toggle_shortcut.activated.connect(self._on_toggle_dev_panel)
        except Exception as e:
            logging.warning(f"注册开发者面板快捷键失败: {e}")
        
        # 监听会话变化（如果需要的话）
        # TODO: 实现会话状态监听
    
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
                if self._navigation_bar:
                    self._navigation_bar.set_current_module(None)
                
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
    
    
    def switch_to_module(self, module_name: str, force: bool = False, auto_start_analysis: bool = False):
        """
        切换到指定模块
        
        Args:
            module_name: 模块名称
            force: 是否强制切换（不显示确认对话框）
            auto_start_analysis: 是否自动启动分析（针对module2）
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
            # 刷新滚动容器以匹配当前模块内容
            self._refresh_content_scroll()
            
            # 更新界面状态
            module_info = self._module_manager.get_module_info(module_name)
            display_name = module_info.display_name if module_info else module_name
            
            self._hide_loading_state()
            self.update_status(f"已加载: {display_name}", "success")
            if self._navigation_bar:
                self._navigation_bar.set_current_module(module_name)
            
            # 发送用户友好的通知
            self._show_success_notification(f"已切换到: {display_name}")
            
            # 如果是module2且需要自动启动分析
            if auto_start_analysis and module_name == "module2":
                self._auto_start_analysis_in_module2(module_widget)
            
            logging.info(f"成功切换到模块: {module_name}")
            
        except Exception as e:
            logging.error(f"切换模块时出错: {e}")
            self._hide_loading_state()
            self.update_status("切换失败", "error")
            self._show_error_message("切换失败", f"切换到模块 {module_name} 时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def _refresh_content_scroll(self):
        """在模块切换后刷新滚动区域，使滚动条只在主容器中出现"""
        try:
            def _do_adjust():
                try:
                    current = self._content_stack.currentWidget()
                    if current is not None:
                        current.adjustSize()
                    self._content_stack.adjustSize()
                    self._content_container.adjustSize()
                    self._content_scroll.updateGeometry()
                    # 重置滚动位置到顶部
                    try:
                        self._content_scroll.verticalScrollBar().setValue(0)
                    except Exception:
                        pass
                except Exception:
                    pass
            # 让布局先完成再调整
            qt.QTimer.singleShot(0, _do_adjust)
        except Exception:
            pass
    
    def _auto_start_analysis_in_module2(self, module_widget):
        """在module2中自动启动分析"""
        try:
            # 延迟200ms启动，确保界面完全加载
            qt.QTimer.singleShot(200, lambda: self._trigger_module2_analysis(module_widget))
            logging.info("已安排module2自动启动分析")
        except Exception as e:
            logging.error(f"安排自动启动分析失败: {e}")
    
    def _trigger_module2_analysis(self, module_widget):
        """触发module2的分析"""
        try:
            if hasattr(module_widget, '_on_start_auto_analysis'):
                logging.info("自动触发module2全自动分析")
                module_widget._on_start_auto_analysis()
            else:
                logging.warning("module2组件没有_on_start_auto_analysis方法")
        except Exception as e:
            logging.error(f"自动启动module2分析失败: {e}")
    
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
        if self._navigation_bar:
            self._navigation_bar.set_buttons_enabled(False)
    
    def _hide_loading_state(self):
        """隐藏加载状态"""
        # 重新启用按钮
        if self._navigation_bar:
            self._navigation_bar.set_buttons_enabled(True)
    
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

    def _on_toggle_dev_panel(self):
        """快捷键回调：显示/隐藏开发者面板（如未创建则按需创建）"""
        try:
            # 若面板尚未创建，则尝试创建并显示
            if self._dev_panel is None:
                if self._main_layout is None:
                    self._main_layout = self.layout() or LayoutManager.create_layout(LayoutType.MAIN_CONTAINER, self)
                self._create_developer_panel(self._main_layout)
                self._dev_panel.setVisible(True)
            else:
                self._dev_panel.setVisible(not self._dev_panel.isVisible())

            # 持久化可见性
            try:
                settings = qt.QSettings()
                settings.setValue("TAVRAnalytics/DeveloperPanelVisible", self._dev_panel.isVisible())
            except Exception:
                pass

            state = "显示" if self._dev_panel.isVisible() else "隐藏"
            self.update_status(f"开发者面板已{state}", "success")
        except Exception as e:
            logging.warning(f"切换开发者面板可见性失败: {e}")

    def toggle_developer_panel(self, show: Optional[bool] = None):
        """编程方式切换开发者面板可见性。
        show 为 None 时取反，否则按传入布尔值设置。
        """
        try:
            if self._dev_panel is None:
                if self._main_layout is None:
                    self._main_layout = self.layout() or LayoutManager.create_layout(LayoutType.MAIN_CONTAINER, self)
                self._create_developer_panel(self._main_layout)
            if show is None:
                self._dev_panel.setVisible(not self._dev_panel.isVisible())
            else:
                self._dev_panel.setVisible(bool(show))
            try:
                settings = qt.QSettings()
                settings.setValue("TAVRAnalytics/DeveloperPanelVisible", self._dev_panel.isVisible())
            except Exception:
                pass
        except Exception as e:
            logging.warning(f"toggle_developer_panel 执行失败: {e}")
        
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
            # 切换到模块一
            self.switch_to_module("module1")
    
    def refresh_navigation(self):
        """刷新导航区域（当模块注册状态改变时）"""
        if self._navigation_bar:
            self._navigation_bar.refresh_navigation()
    
    def enable_module_button(self, module_name: str, enabled: bool = True):
        """
        启用或禁用指定模块的按钮
        
        Args:
            module_name: 模块名称
            enabled: 是否启用
        """
        if self._navigation_bar:
            self._navigation_bar.enable_module_button(module_name, enabled)
    
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
