"""
导航栏组件 - TAVR Analytics 导航栏管理
"""

import logging
from typing import Optional, List
import qt
from core.module_manager import ModuleManager
from utils.layout_manager import LayoutManager, LayoutType


class NavigationBar(qt.QFrame):
    """导航栏组件 - 负责模块切换导航界面"""

    # 信号定义
    moduleRequested = qt.Signal(str)  # 请求切换模块
    moduleInfoRequested = qt.Signal(str)  # 请求显示模块信息
    moduleRefreshRequested = qt.Signal(str)  # 请求刷新模块

    def __init__(self, module_manager: ModuleManager, parent=None):
        """
        初始化导航栏

        Args:
            module_manager: 模块管理器实例
            parent: 父组件
        """
        super().__init__(parent)

        # 成员初始化
        self._module_manager = module_manager
        self._current_module = None

        # 导航相关组件
        self._nav_scroll = None
        self._nav_scroll_content = None
        self._nav_buttons_layout = None
        self._module_buttons = None

        # 设置导航栏
        self._setup_ui()
        self._setup_connections()

        logging.info("导航栏组件初始化完成")

    def _setup_ui(self):
        """设置用户界面"""
        # 设置对象名称和固定高度
        self.setObjectName("TopNav")
        self.setFixedHeight(56)

        # 创建主布局
        main_layout = qt.QHBoxLayout(self)
        main_layout.setContentsMargins(16, 6, 16, 6)
        main_layout.setSpacing(8)

        # 创建可滚动的按钮区域
        self._create_scrollable_button_area(main_layout)

        # 创建模块按钮组
        self._create_module_buttons()

        # 应用样式
        self._apply_styles()

        logging.info("导航栏UI创建完成")

    def _apply_shadow_effect(self):
        """应用阴影效果"""
        try:
            shadow = qt.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(16)
            shadow.setOffset(0, 1)
            try:
                shadow.setColor(qt.QColor(0, 0, 0, 40))
            except Exception:
                pass
            self.setGraphicsEffect(shadow)
        except Exception:
            pass

    def _create_scrollable_button_area(self, parent_layout):
        """创建可滚动的按钮区域"""
        # 中间模块按钮（可横向滚动）
        self._nav_scroll = qt.QScrollArea()
        self._nav_scroll.setFrameShape(qt.QFrame.NoFrame)
        self._nav_scroll.setWidgetResizable(True)
        self._nav_scroll.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        self._nav_scroll.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)

        self._nav_scroll_content = qt.QWidget()
        self._nav_buttons_layout = qt.QHBoxLayout(self._nav_scroll_content)
        self._nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_buttons_layout.setSpacing(8)
        self._nav_scroll.setWidget(self._nav_scroll_content)
        parent_layout.addWidget(self._nav_scroll, 1)

    def _create_module_buttons(self):
        """创建模块按钮"""
        # 模块切换按钮组
        self._module_buttons = qt.QButtonGroup()
        self._module_buttons.setExclusive(True)

        # 获取可用模块并创建按钮
        available_modules = self._module_manager.get_available_modules()
        logging.info(f"NavigationBar 可用模块: {available_modules}")

        for _, module_name in enumerate(available_modules, 1):
            module_info = self._module_manager.get_module_info(module_name)
            if module_info:
                # 极简文本标签风格（去除图标与胶囊外观）
                display_text = module_info.display_name
                btn = qt.QPushButton(display_text)
                btn.setObjectName("NavButton")
                btn.setCheckable(True)
                btn.setMinimumHeight(32)
                btn.setProperty("module_name", module_name)
                btn.setCursor(qt.Qt.PointingHandCursor)
                self._module_buttons.addButton(btn)
                self._nav_buttons_layout.addWidget(btn)

        # 填充剩余空间
        self._nav_buttons_layout.addStretch(1)

    def _apply_styles(self):
        """应用导航栏样式"""
        try:
            self.setStyleSheet(
                """
                /* 顶栏 */
                QFrame#TopNav {
                    background: #ffffff;
                    border-bottom: 1px solid #e5e7eb; /* neutral-200 */
                }
                /* 极简文本标签风格 */
                QFrame#TopNav QPushButton#NavButton {
                    background: transparent;
                    border: none;
                    color: #374151; /* gray-700 */
                    padding: 6px 10px 8px 10px; /* 为下划线留出空间 */
                    font-weight: 600;
                }
                QFrame#TopNav QPushButton#NavButton:hover {
                    color: #111827; /* gray-900 */
                    border-bottom: 2px solid #e5e7eb; /* hover 下轻微指示 */
                }
                QFrame#TopNav QPushButton#NavButton:checked {
                    color: #1d4ed8; /* indigo-700 */
                    border-bottom: 2px solid #2563eb; /* 主色下划线 */
                }
                QFrame#TopNav QPushButton#NavButton:disabled {
                    color: #9ca3af; /* gray-400 */
                }
                """
            )
        except Exception:
            pass

    def _setup_connections(self):
        """设置信号连接"""
        # 连接按钮点击事件
        self._module_buttons.buttonClicked.connect(self._on_module_button_clicked)

        # 设置工具提示
        self._setup_tooltips()

        # 设置右键菜单
        self._setup_context_menus()

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
            activate_action.triggered.connect(
                lambda: self.moduleRequested.emit(module_name)
            )

            # 模块信息
            info_action = menu.addAction("模块信息")
            info_action.triggered.connect(
                lambda: self.moduleInfoRequested.emit(module_name)
            )

            menu.addSeparator()

            # 如果是当前模块，添加刷新选项
            if module_name == self._current_module:
                refresh_action = menu.addAction("刷新模块")
                refresh_action.triggered.connect(
                    lambda: self.moduleRefreshRequested.emit(module_name)
                )

            # 显示菜单
            menu.exec_(button.mapToGlobal(pos))
        except Exception as e:
            logging.error(f"显示右键菜单时出错: {e}")

    def _on_module_button_clicked(self, button):
        """处理模块按钮点击"""
        if button:
            module_name = button.property("module_name")
            if module_name:
                # 发送模块切换请求信号
                self.moduleRequested.emit(module_name)

    def set_current_module(self, module_name: Optional[str]):
        """设置当前激活的模块"""
        self._current_module = module_name
        self._update_button_state(module_name)

    def _update_button_state(self, active_module: Optional[str]):
        """更新按钮状态"""
        for button in self._module_buttons.buttons():
            module_name = button.property("module_name")
            button.setChecked(module_name == active_module)

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

    def refresh_navigation(self):
        """刷新导航区域（当模块注册状态改变时）"""
        try:
            # 清除现有按钮
            for button in list(self._module_buttons.buttons()):
                self._module_buttons.removeButton(button)
                if self._nav_buttons_layout is not None:
                    self._nav_buttons_layout.removeWidget(button)
                button.setParent(None)
                button.deleteLater()

            # 重新创建按钮
            self._create_module_buttons()

            # 重新应用工具提示与右键菜单
            self._setup_tooltips()
            self._setup_context_menus()

            logging.info("导航区域已刷新")
        except Exception as e:
            logging.error(f"刷新导航区域失败: {e}")

    def get_current_module(self) -> Optional[str]:
        """获取当前激活的模块名称"""
        return self._current_module

    def set_buttons_enabled(self, enabled: bool):
        """设置所有按钮的启用状态（用于加载状态）"""
        for button in self._module_buttons.buttons():
            button.setEnabled(enabled)

    def cleanup(self):
        """清理资源"""
        logging.info("导航栏组件清理完成")