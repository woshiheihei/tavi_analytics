"""
模块二界面组件
负责全自动分析的用户界面
"""

import logging
import time
from typing import Optional
import qt
import slicer

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType
    from .module2_logic import Module2Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType
    from module2.module2_logic import Module2Logic


class Module2Widget(qt.QWidget):
    """
    模块二界面组件
    
    提供全自动分析的用户界面，包括：
    - 全自动分析工具界面
    - 分析进度显示
    - 结果预览
    """

    def __init__(self, session: TAVRStudySession, logic: Optional[Module2Logic] = None, parent=None):
        """
        初始化模块二界面组件
        
        Args:
            session: TAVR研究会话对象
            logic: 模块二业务逻辑对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.logic = logic or Module2Logic()
        
        # 设置组件属性
        self.setObjectName("Module2Widget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("Module2Widget 初始化完成")

    def on_activated(self, auto_start_analysis: bool = False):
        """
        模块激活时的回调方法
        
        Args:
            auto_start_analysis: 是否自动启动分析
        """
        logging.info("模块二已激活")
        
        # 如果需要自动启动分析
        if auto_start_analysis:
            self._prepare_auto_start_analysis()

    def _prepare_auto_start_analysis(self):
        """准备自动启动分析"""
        try:
            logging.info("准备自动启动全自动分析")
            # 更新状态提示用户即将开始
            self._update_analysis_status("🚀 正在自动启动分析...", "info")
            # 延迟500ms启动，给用户看到状态更新
            qt.QTimer.singleShot(500, self._on_start_auto_analysis)
        except Exception as e:
            logging.error(f"准备自动启动分析失败: {e}")

    # 已移除期像切换组件相关回调与状态恢复逻辑

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局 - 与模块一保持一致的布局管理器
        layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 全自动分析区域 - 主要功能区
        self._create_auto_analysis_section(layout)
        
        # 添加间隔
        layout.addSpacing(20)

        # 导航按钮区域 - 进入下一步
        self._create_navigation_section(layout)

        # 弹性空间，将内容推到顶部
        layout.addStretch(1)

    def _create_auto_analysis_section(self, layout):
        """创建全自动分析区域 - 合并进度显示到主功能区"""
        # 使用标准化的section_frame - 与模块一保持一致
        analysis_group = LayoutManager.create_section_frame("全自动分析", LayoutType.BUTTON_GROUP)
        analysis_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, analysis_group)
        
        # 设置紧凑的size policy - 与模块一保持一致
        analysis_group.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Maximum)
        
        # 一键分析按钮 - 主要操作，使用绿色风格
        self.auto_analysis_button = qt.QPushButton("🚀 开始全自动分析")
        self.auto_analysis_button.setObjectName("autoAnalysisButton")
        self.auto_analysis_button.setMinimumHeight(40)
        self.auto_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)
        self.auto_analysis_button.clicked.connect(self._on_start_auto_analysis)
        analysis_layout.addWidget(self.auto_analysis_button)
        
        # 分析状态显示（初始隐藏，触发后再显示）
        self.analysis_status_label = qt.QLabel("")
        self.analysis_status_label.setAlignment(qt.Qt.AlignCenter)
        self.analysis_status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                margin: 4px 0px;
            }
        """)
        self.analysis_status_label.setWordWrap(True)
        self.analysis_status_label.setVisible(False)
        analysis_layout.addWidget(self.analysis_status_label)
        
        # 进度条 - 集成到主功能区，使用绿色主题
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #28a745;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                background-color: #f8f9fa;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)  # 初始隐藏
        analysis_layout.addWidget(self.progress_bar)
        
        # 停止分析按钮 - 危险操作，初始隐藏，使用红色风格
        self.stop_analysis_button = qt.QPushButton("⏹ 停止分析")
        self.stop_analysis_button.setObjectName("stopAnalysisButton")
        self.stop_analysis_button.setMinimumHeight(32)
        self.stop_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)
        self.stop_analysis_button.clicked.connect(self._on_stop_analysis)
        self.stop_analysis_button.setVisible(False)  # 初始隐藏
        analysis_layout.addWidget(self.stop_analysis_button)
        
        layout.addWidget(analysis_group, 0)  # 固定大小，不拉伸



    def _create_navigation_section(self, layout):
        """创建进入分析页面的导航按钮 - 与模块一风格保持一致"""
        nav_group = LayoutManager.create_section_frame("下一步操作", LayoutType.BUTTON_GROUP)
        nav_layout = LayoutManager.create_layout(LayoutType.BUTTON_GROUP, nav_group)
        
        # 设置紧凑的size policy - 与模块一保持一致
        nav_group.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Maximum)

        # 进入分析页面按钮，使用绿色风格
        self.go_to_analysis_button = qt.QPushButton("进入分析页面")
        self.go_to_analysis_button.setObjectName("enterAnalysisPageButton")
        self.go_to_analysis_button.setMinimumHeight(40)
        self.go_to_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)
        self.go_to_analysis_button.clicked.connect(self._on_enter_analysis_page)
        nav_layout.addWidget(self.go_to_analysis_button)

        # 状态提示标签 - 与模块一风格保持一致
        self.nav_status_label = qt.QLabel("全自动分析完成后可进入详细分析页面")
        self.nav_status_label.setStyleSheet(
            "QLabel { color: #666; font-size: 12px; text-align: center; padding: 8px; }"
        )
        self.nav_status_label.setAlignment(qt.Qt.AlignCenter)
        nav_layout.addWidget(self.nav_status_label)

        layout.addWidget(nav_group, 0)  # 固定大小，不拉伸

    def _on_enter_analysis_page(self):
        """跳转到 module3（瓣叶功能评估）标签页"""
        try:
            plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            if hasattr(plugin, 'main_ui') and plugin.main_ui:
                plugin.main_ui.switch_to_module("module3")
            else:
                # 后备：通过插件暴露的模块管理器激活
                if hasattr(plugin, 'module_manager') and plugin.module_manager:
                    plugin.module_manager.activate_module("module3")
                else:
                    # 最终后备：直接使用全局单例的ModuleManager
                    try:
                        from ..core.module_manager import ModuleManager as _MM
                    except Exception:
                        from core.module_manager import ModuleManager as _MM
                    _MM().activate_module("module3")
            logging.info("已跳转到模块三（瓣叶功能评估）")
        except Exception as e:
            logging.error(f"跳转到分析页面失败: {e}")
            self._update_analysis_status("❌ 跳转失败，请稍后重试", "error")

    def _on_start_auto_analysis(self):
        """
        处理开始全自动分析按钮点击事件
        
        执行一键全自动分析流程：
        1. 检查舒张末期是否已标记
        2. 检查服务器连接
        3. 获取当前舒张末期的nrrd文件
        4. 上传到远程分析服务器
        5. 监控分析状态
        6. 下载并导入分析结果
        """
        logging.info("用户点击了'开始全自动分析'按钮")
        try:
            # 更新UI状态
            self._update_analysis_status("🔍 正在检查分析条件和服务器连接...", "processing")
            self._disable_analysis_button()

            # 调用逻辑层开始自动分析
            result = self.logic.start_auto_analysis()

            if result:
                self._update_analysis_status("📤 上传中...", "processing")
                self._show_stop_button()

                # 启动状态监控定时器
                self._start_analysis_monitoring()

                logging.info("全自动分析流程已启动")
            else:
                self._update_analysis_status("❌ 启动失败，请检查数据与网络", "error")
                self._enable_analysis_button()
                logging.error("全自动分析流程启动失败")

        except Exception as e:
            logging.error(f"开始全自动分析失败: {e}")
            self._update_analysis_status(f"❌ 发生错误: {str(e)}", "error")
            self._enable_analysis_button()

    # 已移除过期的期像强制切换函数

    def _on_stop_analysis(self):
        """
        处理停止分析按钮点击事件
        """
        logging.info("用户要求停止分析")
        
        try:
            # 停止分析监控
            self._stop_analysis_monitoring()
            
            # 调用逻辑层停止分析
            self.logic.stop_auto_analysis()
            
            # 重置UI状态
            self._update_analysis_status("⏹ 分析已停止", "warning")
            self._enable_analysis_button()
            self._hide_stop_button()
            
            logging.info("分析已被用户停止")
            
        except Exception as e:
            logging.error(f"停止分析失败: {e}")
            self._update_analysis_status(f"❌ 停止分析时发生错误: {str(e)}", "error")

    def _start_analysis_monitoring(self):
        """
        启动分析状态监控
        
        定期检查远程分析的状态，并在完成时处理结果
        """
        # 创建定时器
        if not hasattr(self, 'analysis_timer'):
            self.analysis_timer = qt.QTimer()
            self.analysis_timer.timeout.connect(self._check_analysis_progress)
        
        self.analysis_timer.start(3000)  # 每3秒检查一次
        logging.info("分析状态监控定时器已启动")

    def _stop_analysis_monitoring(self):
        """停止分析状态监控定时器"""
        if hasattr(self, 'analysis_timer') and self.analysis_timer:
            self.analysis_timer.stop()
            self.analysis_timer = None
            logging.info("分析状态监控定时器已停止")

    def _check_analysis_progress(self):
        """
        检查分析进度
        
        定期调用，监控远程分析的进度并更新UI
        """
        try:
            # 获取分析状态
            status = self.logic.get_analysis_status()

            if not status:
                # 状态获取失败，停止监控
                self._stop_analysis_monitoring()
                self._update_analysis_status("❌ 无法获取分析状态，请检查网络连接", "error")
                self._enable_analysis_button()
                return

            analysis_status = status.get('status', 'unknown')
            progress = status.get('progress', 0)
            message = status.get('message', '')

            # 更新进度显示
            if analysis_status == 'uploading':
                self._update_analysis_status("📤 上传中...", "processing")
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(int(progress))
            elif analysis_status == 'processing':
                self._update_analysis_status("⚙️ 分析中...", "processing")
                if hasattr(self, 'progress_bar'):
                    # 若无明确进度，则不超过95
                    try:
                        current_value = int(self.progress_bar.value())
                    except Exception:
                        current_value = 0
                    target = int(progress) if progress else min(current_value + 1, 95)
                    self.progress_bar.setValue(min(max(current_value, target), 95))
            elif analysis_status == 'downloading':
                self._update_analysis_status("📥 下载结果中...", "processing")
                if hasattr(self, 'progress_bar'):
                    try:
                        current_value = int(self.progress_bar.value())
                    except Exception:
                        current_value = 90
                    self.progress_bar.setValue(max(current_value, 95))
            elif analysis_status == 'completed':
                # 分析完成
                self._on_analysis_completed()
            elif analysis_status == 'failed':
                # 分析失败
                error_msg = status.get('error', '未知错误')
                self._on_analysis_failed(error_msg)

            # 如果有额外消息，记录它
            if message and analysis_status in ['uploading', 'processing']:
                logging.info(f"分析状态更新: {message}")

        except Exception as e:
            logging.error(f"检查分析进度失败: {e}")
            self._stop_analysis_monitoring()
            self._update_analysis_status("❌ 监控分析进度时发生错误", "error")
            self._enable_analysis_button()

    def _on_analysis_completed(self):
        """
        分析完成的处理
        
        当远程分析完成时，下载结果并导入到Slicer中
        """
        logging.info("全自动分析已完成")
        try:
            # 停止监控
            self._stop_analysis_monitoring()

            # 更新状态
            self._update_analysis_status("🎉 分析完成！正在导入结果...", "success")
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(98)

            # 调用逻辑层导入结果
            import_result = self.logic.import_analysis_results()

            if import_result:
                # 简洁提示
                self._update_analysis_status("✅ 分析完成，结果已导入", "success")

                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(100)

                # 完成后恢复按钮与隐藏停止
                self._enable_analysis_button()
                self._hide_stop_button()

                logging.info("全自动分析结果导入成功")
            else:
                self._update_analysis_status("❌ 分析完成但结果导入失败", "error")
                self._enable_analysis_button()
                self._hide_stop_button()

        except Exception as e:
            logging.error(f"处理分析完成事件失败: {e}")
            self._update_analysis_status(f"❌ 处理分析结果时发生错误: {str(e)}", "error")
            self._enable_analysis_button()
            self._hide_stop_button()

    def _on_analysis_failed(self, error_message: str):
        """
        分析失败的处理

        Args:
            error_message: 错误信息
        """
        logging.error(f"全自动分析失败: {error_message}")

        try:
            # 停止监控
            self._stop_analysis_monitoring()

            # 显示失败信息
            self._update_analysis_status(f"❌ 分析失败: {error_message}", "error")

            # 重新启用分析按钮并隐藏停止按钮
            self._enable_analysis_button()
            self._hide_stop_button()
        except Exception as e:
            logging.error(f"处理分析失败事件失败: {e}")

    def _update_analysis_status(self, message: str, status_type: str = "info"):
        """
        更新分析状态显示
        
        Args:
            message: 状态消息
            status_type: 状态类型 ('info', 'processing', 'success', 'error', 'warning')
        """
        if hasattr(self, 'analysis_status_label'):
            self.analysis_status_label.setText(message)
            self.analysis_status_label.setVisible(True)
            
            # 根据状态类型设置不同的样式
            if status_type == "error":
                style = """
                    QLabel {
                        background-color: #f8d7da;
                        color: #721c24;
                        border: 1px solid #f5c6cb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "success":
                style = """
                    QLabel {
                        background-color: #d4edda;
                        color: #155724;
                        border: 1px solid #c3e6cb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "processing":
                style = """
                    QLabel {
                        background-color: #d1ecf1;
                        color: #0c5460;
                        border: 1px solid #bee5eb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        margin: 4px 0px;
                    }
                """
            elif status_type == "warning":
                style = """
                    QLabel {
                        background-color: #fff3cd;
                        color: #856404;
                        border: 1px solid #ffeeba;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        margin: 4px 0px;
                    }
                """
            else:  # info
                style = """
                    QLabel {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        margin: 4px 0px;
                    }
                """

            self.analysis_status_label.setStyleSheet(style)
            logging.debug(f"分析状态更新: {message}")
            
        # 同时显示进度条（如果正在处理）
        if status_type == "processing" and hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(True)
        elif status_type in ["success", "error"] and hasattr(self, 'progress_bar'):
            # 完成或失败时可以选择隐藏进度条
            pass

    def _disable_analysis_button(self):
        """禁用分析按钮"""
        if hasattr(self, 'auto_analysis_button'):
            self.auto_analysis_button.setEnabled(False)
            self.auto_analysis_button.setText("⏳ 分析进行中...")

    def _enable_analysis_button(self):
        """重新启用分析按钮"""
        if hasattr(self, 'auto_analysis_button'):
            self.auto_analysis_button.setEnabled(True)
            self.auto_analysis_button.setText("🚀 开始全自动分析")

    def _show_stop_button(self):
        """显示停止分析按钮"""
        if hasattr(self, 'stop_analysis_button'):
            self.stop_analysis_button.setVisible(True)

    def _hide_stop_button(self):
        """隐藏停止分析按钮"""
        if hasattr(self, 'stop_analysis_button'):
            self.stop_analysis_button.setVisible(False)

    def _on_button_clicked(self, button_name: str):
        """
        通用按钮点击槽函数
        
        Args:
            button_name: 被点击按钮的名称
        """
        logging.info(f"{button_name} clicked")
        
        # 同时更新状态显示，提供用户反馈
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"用户点击了: {button_name}")

    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if self.logic:
            self.logic.session = session

    def on_deactivated(self):
        """模块停用时调用"""
        logging.info("模块二已停用")
        # 停止所有监控定时器
        self._stop_analysis_monitoring()

    def cleanup(self):
        """清理资源"""
        # 停止所有监控定时器
        self._stop_analysis_monitoring()
        
        # 清理逻辑层资源
        if self.logic:
            self.logic.cleanup()
        
        logging.info("模块二界面清理完成")
