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
    from ..utils.layout_manager import LayoutManager
    from ..widgets.phase_selection_widget import PhaseSelectionWidget
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
    from utils.layout_manager import LayoutManager
    from widgets.phase_selection_widget import PhaseSelectionWidget
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
        
        # 创建期像选择组件
        self.phase_selection = PhaseSelectionWidget(session, self)
        self.phase_selection.phaseChanged.connect(self._on_phase_changed)
        self.phase_selection.statusUpdated.connect(self._on_phase_status_updated)
        
        # 设置组件属性
        self.setObjectName("Module2Widget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("Module2Widget 初始化完成")

    def on_activated(self):
        """
        模块激活时的回调方法
        
    自动切换到舒张末期时相（优先），为全自动分析做准备
        """
        logging.info("模块二已激活，开始检查和切换期像")
        
        try:
            # 使用期像选择组件自动激活
            self.phase_selection.auto_activate(preferred_phase='diastole')
            
            # 设置期像选择组件的说明文本
            self.phase_selection.set_info_text(
        "💡 提示：全自动分析将默认同时处理舒张末期与收缩末期。\n"
        "建议在模块一中标记两期像；若未标记，将使用当前帧作为舒张末期来分析。"
            )
            
        except Exception as e:
            logging.error(f"自动时相切换失败: {e}")
            self._update_status("时相切换失败，请检查时相标记")

    def _on_phase_changed(self, phase: str):
        """
        期像改变时的回调
        
        Args:
            phase: 新的期像 ('diastole' 或 'systole')
        """
        logging.info(f"期像已切换到: {phase}")
        
        # 通知逻辑类更新选择的期像
        if self.logic:
            self.logic.set_selected_phase(phase)
        
        # 更新主状态显示
        phase_name = "舒张末期" if phase == 'diastole' else "收缩末期"
        self._update_status(f"已切换到{phase_name}，可以开始分析")
    
    def _on_phase_status_updated(self, status: str):
        """
        期像状态更新时的回调
        
        Args:
            status: 状态消息
        """
        # 这里可以将期像选择组件的状态同步到主界面
        logging.debug(f"期像状态更新: {status}")
    
    def _restore_phase_selection_state(self):
        """恢复期像选择状态"""
        try:
            if self.logic:
                selected_phase = self.logic.get_selected_phase()
                self.phase_selection.set_current_phase(selected_phase)
                logging.info(f"已恢复期像选择状态: {selected_phase}")
        except Exception as e:
            logging.warning(f"恢复期像选择状态失败: {e}")

    def _check_marked_phases(self):
        """
        检查已标记的期像状态（保留用于兼容性）
        
        委托给期像选择组件处理
        """
        if hasattr(self, 'phase_selection'):
            return self.phase_selection._check_marked_phases()
        return {}

    def _update_status(self, message: str):
        """更新状态显示"""
        if hasattr(self, 'status_label'):
            self.status_label.text = message
            logging.info(f"状态更新: {message}")

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        self._create_title_section(layout)
        
        # 添加全自动分析区域 (Auto Analysis)
        self._create_auto_analysis_section(layout)
        
        # 添加进度状态区域 (Progress Status)
        self._create_progress_section(layout)
        
        # 添加操作控制区域 (Operations)
        self._create_operations_section(layout)
        
        # 添加弹性空间
        layout.addStretch()

    def _create_title_section(self, layout):
        """创建标题区域"""
        title_label = qt.QLabel("模块二：全自动分析")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title_label)
        
        # 添加描述
        description_label = qt.QLabel(
            "本模块提供一键全自动分析功能，自动完成主动脉根部分割和测量，\n"
            "整个过程无需人工干预，实现完全自动化的TAVI术前分析。"
        )
        description_label.setAlignment(qt.Qt.AlignCenter)
        description_label.setStyleSheet(StyleManager.get_label_style("muted"))
        layout.addWidget(description_label)
        
        # 添加期像选择组件
        layout.addWidget(self.phase_selection)

    def _create_auto_analysis_section(self, layout):
        """创建全自动分析区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        analysis_group = LayoutManager.create_section_frame("全自动分析 (Auto Analysis)")
        analysis_layout = qt.QVBoxLayout(analysis_group)
        
        # 添加期像相关的分析提示
        phase_hint_label = qt.QLabel(
            "💡 分析提示：全自动分析将默认同时处理舒张末期与收缩末期，\n"
            "包括主动脉根部分割、测量分析等，整个过程无需人工干预。"
        )
        phase_hint_label.setStyleSheet("""
            QLabel {
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                margin: 4px 0px;
            }
        """)
        phase_hint_label.setWordWrap(True)
        analysis_layout.addWidget(phase_hint_label)
        
        # 一键分析按钮 - 主要操作
        self.auto_analysis_button = LayoutManager.create_button_with_style(
            text="🚀 开始全自动分析",
            button_type="primary",
            size="large",
            min_height=50
        )
        self.auto_analysis_button.setObjectName("autoAnalysisButton")
        self.auto_analysis_button.clicked.connect(self._on_start_auto_analysis)
        analysis_layout.addWidget(self.auto_analysis_button)
        
        # 分析状态显示
        self.analysis_status_label = qt.QLabel("准备开始全自动分析...")
        self.analysis_status_label.setAlignment(qt.Qt.AlignCenter)
        self.analysis_status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                margin: 4px 0px;
            }
        """)
        self.analysis_status_label.setWordWrap(True)
        analysis_layout.addWidget(self.analysis_status_label)
        
        # 停止分析按钮 - 危险操作，初始隐藏
        self.stop_analysis_button = LayoutManager.create_button_with_style(
            text="⏹ 停止分析",
            button_type="destructive",
            size="default",
            min_height=35
        )
        self.stop_analysis_button.setObjectName("stopAnalysisButton")
        self.stop_analysis_button.clicked.connect(self._on_stop_analysis)
        self.stop_analysis_button.setVisible(False)  # 初始隐藏
        analysis_layout.addWidget(self.stop_analysis_button)
        
        layout.addWidget(analysis_group)

    def _create_progress_section(self, layout):
        """创建进度状态区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        progress_group = LayoutManager.create_section_frame("进度状态")
        progress_layout = qt.QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(StyleManager.get_input_style())
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态文本标签
        self.status_label = qt.QLabel("准备开始全自动分析...")
        self.status_label.setAlignment(qt.Qt.AlignCenter)
        self.status_label.setStyleSheet(StyleManager.get_label_style("muted"))
        self.status_label.setMinimumHeight(30)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)

    def _create_operations_section(self, layout):
        """创建操作控制区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        operations_group = LayoutManager.create_section_frame("操作")
        operations_layout = qt.QHBoxLayout(operations_group)
        
        # 重置按钮 - 使用destructive样式表示危险操作
        reset_button = LayoutManager.create_button_with_style(
            text="重置",
            button_type="destructive",
            size="default",
            min_height=40
        )
        reset_button.setObjectName("resetModuleButton")
        reset_button.clicked.connect(lambda: self._on_button_clicked("重置"))
        operations_layout.addWidget(reset_button)
        
        # 完成模块按钮 - 使用primary样式表示主要操作
        complete_button = LayoutManager.create_button_with_style(
            text="完成模块",
            button_type="primary",
            size="default",
            min_height=40
        )
        complete_button.setObjectName("completeModuleButton")
        complete_button.clicked.connect(lambda: self._on_button_clicked("完成模块"))
        operations_layout.addWidget(complete_button)
        
        layout.addWidget(operations_group)

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
            self._update_analysis_status("🔍 正在检查分析条件和服务器连接（多期像）...", "info")
            self._disable_analysis_button()
            
            # 调用逻辑层开始自动分析
            result = self.logic.start_auto_analysis()
            
            if result:
                self._update_analysis_status("📤 分析已启动，正在导出并上传两期像数据...", "processing")
                self._show_stop_button()
                
                # 启动状态监控定时器
                self._start_analysis_monitoring()
                
                logging.info("全自动分析流程已启动")
                
            else:
                self._update_analysis_status("❌ 分析启动失败，请检查数据和网络连接", "error")
                self._enable_analysis_button()
                logging.error("全自动分析流程启动失败")
                
        except Exception as e:
            logging.error(f"开始全自动分析失败: {e}")
            self._update_analysis_status(f"❌ 发生错误: {str(e)}", "error")
            self._enable_analysis_button()

    # 过去的强制舒张末期函数不再需要，保留以兼容但不使用
    def _ensure_diastolic_phase(self) -> bool:
        return True

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
                self._update_analysis_status("📤 正在上传数据到分析服务器...", "processing")
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(progress)
            elif analysis_status == 'processing':
                if progress < 100:
                    # 启动阶段或远程处理阶段
                    if progress < 70:
                        self._update_analysis_status(f"⚙️ {message}", "processing")
                    else:
                        self._update_analysis_status(f"🔄 正在进行自动分析... ({min(progress-60, 40)}%)", "processing")
                else:
                    self._update_analysis_status("🔄 正在进行自动分析...", "processing")
                
                if hasattr(self, 'progress_bar'):
                    # 启动完成后，进度条显示远程分析进度
                    if progress >= 100:
                        # 启动完成，远程分析进行中，显示伪进度
                        current_time = time.time()
                        if not hasattr(self, 'remote_analysis_start_time'):
                            self.remote_analysis_start_time = current_time
                        
                        # 根据时间计算伪进度（假设分析需要2-5分钟）
                        elapsed = current_time - self.remote_analysis_start_time
                        fake_progress = min(20 + elapsed / 300 * 60, 85)  # 20%-85%之间
                        self.progress_bar.setValue(int(fake_progress))
                    else:
                        self.progress_bar.setValue(progress)
                        
            elif analysis_status == 'downloading':
                self._update_analysis_status("📥 正在下载分析结果...", "processing")
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(85)
            elif analysis_status == 'completed':
                # 分析完成
                self._on_analysis_completed()
            elif analysis_status == 'failed':
                # 分析失败
                error_msg = status.get('error', '未知错误')
                self._on_analysis_failed(error_msg)
            
            # 如果有额外消息，显示它
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
                self.progress_bar.setValue(90)
            
            # 调用逻辑层导入结果
            import_result = self.logic.import_analysis_results()
            
            if import_result:
                phases = import_result.get('phases', {})
                seg_count = import_result.get('total_segmentations', 0)
                curves_count = import_result.get('total_curves', 0)
                # 汇总每期像
                details = []
                for phase, info in phases.items():
                    name = "舒张末期" if phase == 'diastole' else "收缩末期"
                    seg_ok = info.get('segmentation_imported', False)
                    meas_path = info.get('measurement_path')
                    details.append(f"• {name}: 分割{'已导入' if seg_ok else '未导入'}; 测量文件: {'有' if meas_path else '无'}")
                success_msg = (
                    f"✅ 全自动分析完成！\n"
                    f"• 导入分割: {seg_count} 个期像\n"
                    f"• 创建曲线: {curves_count} 条（基于舒张末期）\n"
                    + "\n".join(details)
                )
                self._update_analysis_status(success_msg, "success")
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(100)
                
                # 重新启用分析按钮
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
            
            # 重新启用分析按钮
            self._enable_analysis_button()
            self._hide_stop_button()
            
            # 重置进度条
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(0)
                
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
            
            # 根据状态类型设置不同的样式
            if status_type == "error":
                style = """
                    QLabel {
                        background-color: #f8d7da;
                        color: #721c24;
                        border: 1px solid #f5c6cb;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
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
                        font-size: 13px;
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
                        font-size: 13px;
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
                        font-size: 13px;
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
                        font-size: 13px;
                        margin: 4px 0px;
                    }
                """
            
            self.analysis_status_label.setStyleSheet(style)
            logging.debug(f"分析状态更新: {message}")

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
        if hasattr(self, 'phase_selection'):
            self.phase_selection.set_session(session)

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
