"""
关键视图管理器组件 - 公共UI组件

提供MPR视图标记、管理和恢复的标准化用户界面，可在多个分析模块中复用：
- HALT分析
- RELM分析
- SFD分析  
- PFD分析

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List, Callable
import qt

# 轻量依赖，仅在需要时注入
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..services.view_marking_service import get_view_marking_service
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from services.view_marking_service import get_view_marking_service


class KeyViewManagerWidget(qt.QWidget):
    """
    关键视图管理器组件
    
    提供标准化的视图标记和管理界面，包括：
    - 视图标记功能（支持快捷键）
    - 已标记视图列表显示
    - 视图恢复和删除操作
    - 视图导入导出功能
    - 自定义样式和主题
    """
    
    # 定义信号
    viewMarked = qt.Signal(str)      # 视图被标记时发出，参数为视图名称
    viewRestored = qt.Signal(str)    # 视图被恢复时发出，参数为视图名称
    viewDeleted = qt.Signal(str)     # 视图被删除时发出，参数为视图名称
    statusUpdated = qt.Signal(str)   # 状态更新信号，参数为状态消息
    
    def __init__(self, 
                 analysis_type: str = "GENERAL", 
                 session: Optional[TAVRStudySession] = None, 
                 compact_mode: bool = False,
                 parent=None,
                 use_external_header: bool = False):
        """
        初始化关键视图管理器组件
        
        Args:
            analysis_type: 分析类型（HALT, RELM, SFD, PFD等）
            session: TAVR研究会话对象
            compact_mode: 是否使用紧凑模式
            parent: 父组件
        """
        super().__init__(parent)

        self.analysis_type = analysis_type
        self.session = session
        self.compact_mode = compact_mode
        self.use_external_header = use_external_header

        # 获取视图标记服务
        self.view_service = get_view_marking_service(analysis_type, session)

        # 设置组件属性
        self.setObjectName(f"KeyViewManagerWidget_{analysis_type}")

        # 回调函数列表
        self.mark_callbacks = []
        self.restore_callbacks = []
        self.delete_callbacks = []
        
        # 创建界面
        self._setup_ui()
        
        # 初始化视图列表
        self._refresh_marked_views_list()
        
        logging.info(f"KeyViewManagerWidget 初始化完成 - 分析类型: {analysis_type}, 紧凑模式: {compact_mode}")
    
    def _setup_ui(self):
        """设置用户界面（作为纯内容组件，由父级 SectionCard 包裹）"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6 if self.compact_mode else 8)

        # 顶部工具行（可外置到父级 SectionCard 的 header）
        header_layout = qt.QHBoxLayout()
        header_layout.setSpacing(6 if self.compact_mode else 8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        if not self.use_external_header:
            if not self.compact_mode:
                title = qt.QLabel(f"关键视图 - {self.analysis_type}")
                title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
                header_layout.addWidget(title)
            header_layout.addStretch()

        mark_text = "📌 标记 " if self.compact_mode else "📌 标记 (Ctrl+M)"
        self.mark_btn = qt.QPushButton(mark_text)
        if self.compact_mode:
            self.mark_btn.setStyleSheet("""
                QPushButton { padding: 4px 8px; background-color: #28a745; color: white; border: none; border-radius: 3px; font-weight: 500; font-size: 10px; }
                QPushButton:hover { background-color: #218838; }
            """)
        else:
            self.mark_btn.setStyleSheet("""
                QPushButton { padding: 6px 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; font-weight: 500; font-size: 11px; }
                QPushButton:hover { background-color: #218838; }
            """)
        self.mark_btn.clicked.connect(self._show_mark_view_dialog)
        self.mark_btn.setToolTip(f"标记当前MPR视图位置 ({self.analysis_type}分析)")
        mark_shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+M"), self)
        mark_shortcut.activated.connect(self._show_mark_view_dialog)
        if not self.use_external_header:
            header_layout.addWidget(self.mark_btn)
            main_layout.addLayout(header_layout)

        # 已标记视图列表
        self._create_views_list_section(main_layout)

        # 操作按钮（仅在非紧凑模式下显示）
        if not self.compact_mode:
            self._create_actions_section(main_layout)
    
    # 旧的主框/标题构建逻辑（卡片化样式）已移除，由父级 SectionCard 统一提供
    
    def _create_views_list_section(self, parent_layout):
        """创建已标记视图列表区域"""
        # 滚动区域用于视图列表
        scroll_area = qt.QScrollArea()
        
        if self.compact_mode:
            scroll_area.setMaximumHeight(100)
        else:
            scroll_area.setMaximumHeight(120)
        
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(qt.QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 视图列表容器
        self.views_container = qt.QWidget()
        self.views_layout = qt.QVBoxLayout(self.views_container)
        self.views_layout.setSpacing(2)
        self.views_layout.setContentsMargins(0, 0, 0, 0)
        
        # 空状态提示
        self.empty_hint = qt.QLabel("暂无标记")
        self.empty_hint.setAlignment(qt.Qt.AlignCenter)
        
        if self.compact_mode:
            self.empty_hint.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-style: italic;
                    font-size: 9px;
                    padding: 10px;
                }
            """)
        else:
            self.empty_hint.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-style: italic;
                    font-size: 10px;
                    padding: 15px;
                }
            """)
        
        self.views_layout.addWidget(self.empty_hint)
        self.views_layout.addStretch()
        
        scroll_area.setWidget(self.views_container)
        parent_layout.addWidget(scroll_area)
    
    def _create_actions_section(self, parent_layout):
        """创建操作按钮区域（仅在标准模式下）"""
        actions_layout = qt.QHBoxLayout()
        actions_layout.setSpacing(6)
        
        # 清除所有按钮
        clear_btn = qt.QPushButton("清除所有")
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 10px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        clear_btn.clicked.connect(self._clear_all_views)
        
        # 导出按钮
        export_btn = qt.QPushButton("导出")
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 10px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        export_btn.clicked.connect(self._export_views)
        
        # 统计按钮
        stats_btn = qt.QPushButton("统计")
        stats_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 10px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        stats_btn.clicked.connect(self._show_statistics)
        
        actions_layout.addWidget(clear_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(stats_btn)
        actions_layout.addStretch()
        
        parent_layout.addLayout(actions_layout)
    
    def _show_mark_view_dialog(self):
        """显示标记视图对话框"""
        dialog = qt.QDialog(self)
        dialog.setWindowTitle(f"标记当前视图 - {self.analysis_type}")
        dialog.setModal(True)
        dialog.resize(350, 150)
        
        layout = qt.QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # 获取当前期像信息
        current_phase_info = None
        if self.session:
            try:
                current_phase_info = self.session.get_current_phase_info()
            except Exception as e:
                logging.warning(f"获取当前期像信息失败: {e}")
        
        # 说明文本
        info_text = f"为当前MPR视图位置添加一个{self.analysis_type}分析的标记名称："
        info_label = qt.QLabel(info_text)
        info_label.setStyleSheet("font-size: 13px; color: #495057;")
        layout.addWidget(info_label)
        
        # 当前期像状态显示
        if current_phase_info and current_phase_info.get('phase'):
            phase_icon = current_phase_info.get('icon', '❓')
            phase_display = current_phase_info.get('display_name', '未知期像')
            
            phase_info_label = qt.QLabel(f"当前期像：{phase_icon} {phase_display}")
            phase_info_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #007bff;
                    font-weight: bold;
                    padding: 4px 8px;
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 4px;
                }
            """)
            layout.addWidget(phase_info_label)
        else:
            phase_info_label = qt.QLabel("当前期像：❓ 未知期像（将不记录期像信息）")
            phase_info_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #f57c00;
                    font-weight: bold;
                    padding: 4px 8px;
                    background-color: #fff3e0;
                    border: 1px solid #ffcc02;
                    border-radius: 4px;
                }
            """)
            layout.addWidget(phase_info_label)
        
        # 输入框
        name_input = qt.QLineEdit()
        name_input.setPlaceholderText("例如：最佳显示角度、重要病变位置...")
        name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        
        # 生成默认名称（包含期像信息）
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if current_phase_info and current_phase_info.get('phase'):
            phase_display = current_phase_info.get('display_name', '未知期像')
            default_name = f"{self.analysis_type}视图_{phase_display}_{timestamp}"
        else:
            default_name = f"{self.analysis_type}视图_{timestamp}"
        
        name_input.setText(default_name)
        name_input.selectAll()
        
        layout.addWidget(name_input)
        
        # 按钮区域
        buttons_layout = qt.QHBoxLayout()
        
        cancel_btn = qt.QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        confirm_btn = qt.QPushButton("标记")
        confirm_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        confirm_btn.setDefault(True)
        
        def on_confirm():
            # 兼容不同Qt绑定：QLineEdit.text 在某些环境是属性(str)，在部分环境是可调用方法
            text_attr = getattr(name_input, "text", "")
            view_name = text_attr().strip() if callable(text_attr) else str(text_attr).strip()
            if not view_name:
                qt.QMessageBox.warning(dialog, "警告", "请输入视图名称！")
                return
            
            success = self._mark_current_view(view_name)
            if success:
                dialog.accept()
            else:
                qt.QMessageBox.warning(
                    dialog,
                    "标记失败", 
                    "标记当前视图失败，请检查MPR视图状态。"
                )
        
        confirm_btn.clicked.connect(on_confirm)
        name_input.returnPressed.connect(on_confirm)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(confirm_btn)
        
        layout.addLayout(buttons_layout)
        
        # 聚焦输入框
        name_input.setFocus()
        
        dialog.exec_()
    
    def _mark_current_view(self, view_name: str) -> bool:
        """标记当前视图"""
        success = self.view_service.mark_current_view(view_name)
        
        if success:
            self._refresh_marked_views_list()
            self.viewMarked.emit(view_name)
            self.statusUpdated.emit(f"已标记视图: {view_name}")
            
            # 调用回调函数
            for callback in self.mark_callbacks:
                try:
                    callback(view_name)
                except Exception as e:
                    logging.error(f"执行标记回调失败: {e}")
            
            # 显示成功提示
            qt.QMessageBox.information(
                self,
                "标记成功",
                f"视图已标记为：{view_name}"
            )
        
        return success
    
    def _refresh_marked_views_list(self):
        """刷新已标记视图列表"""
        # 清除现有的视图项
        for i in reversed(range(self.views_layout.count())):
            child = self.views_layout.itemAt(i).widget()
            if child and child != self.empty_hint:
                child.setParent(None)
        
        marked_views = self.view_service.get_marked_views()
        
        if not marked_views:
            # 显示空状态
            self.empty_hint.setVisible(True)
        else:
            # 隐藏空状态提示
            self.empty_hint.setVisible(False)
            
            # 为每个标记的视图创建条目
            for view_name, description in marked_views.items():
                # 获取视图详细信息（包含期像数据）
                view_details = self.view_service.get_view_details(view_name)
                view_item = self._create_view_item(view_name, description, view_details)
                # 插入到stretch之前
                self.views_layout.insertWidget(self.views_layout.count() - 1, view_item)
    
    def _create_view_item(self, view_name: str, description: str, view_details: Optional[Dict[str, Any]] = None) -> qt.QWidget:
        """创建单个视图条目"""
        item_frame = qt.QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
                margin: 1px 0;
            }
            QFrame:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)
        
        item_layout = qt.QHBoxLayout(item_frame)
        item_layout.setContentsMargins(6, 3, 6, 3)
        item_layout.setSpacing(4 if self.compact_mode else 6)
        
        # 期像图标（如果有期像信息）
        phase_icon = '❓'  # 默认未知期像
        phase_display = '未知期像'
        tooltip_text = f"视图: {view_name}"
        
        if view_details:
            phase = view_details.get('phase')
            phase_display = view_details.get('phase_display', '未知期像')
            phase_icon = view_details.get('phase_icon', '❓')
            
            if phase:
                tooltip_text = f"视图: {view_name}\n期像: {phase_display}"
            else:
                tooltip_text = f"视图: {view_name}\n期像: 未知期像（旧版本数据）"
        
        phase_icon_label = qt.QLabel(phase_icon)
        phase_icon_label.setStyleSheet("font-size: 10px;" if self.compact_mode else "font-size: 12px;")
        phase_icon_label.setToolTip(tooltip_text)
        item_layout.addWidget(phase_icon_label)
        
        # 视图信息容器
        info_container = qt.QWidget()
        info_layout = qt.QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(1)
        
        # 视图名称
        name_label = qt.QLabel(view_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                font-size: {'9px' if self.compact_mode else '10px'};
                font-weight: bold;
                color: #212529;
            }}
        """)
        info_layout.addWidget(name_label)
        
        # 期像信息（仅在非紧凑模式下显示）
        if not self.compact_mode and view_details and view_details.get('phase'):
            phase_label = qt.QLabel(phase_display)
            phase_label.setStyleSheet("""
                QLabel {
                    font-size: 8px;
                    color: #6c757d;
                    font-style: italic;
                }
            """)
            info_layout.addWidget(phase_label)
        
        item_layout.addWidget(info_container)
        item_layout.addStretch()
        
        # 操作按钮
        button_size = 18 if self.compact_mode else 20
        
        # 恢复按钮
        restore_btn = qt.QPushButton("🔄")
        restore_btn.setToolTip(f"恢复到视图: {view_name}")
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 2px 4px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: {'8px' if self.compact_mode else '9px'};
                font-weight: bold;
                min-width: {button_size}px;
                max-width: {button_size}px;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        restore_btn.clicked.connect(lambda: self._restore_view(view_name))
        item_layout.addWidget(restore_btn)
        
        # 删除按钮
        delete_btn = qt.QPushButton("🗑️")
        delete_btn.setToolTip("删除此视图标记")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 2px 4px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: {'8px' if self.compact_mode else '9px'};
                min-width: {button_size}px;
                max-width: {button_size}px;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """)
        delete_btn.clicked.connect(lambda: self._delete_view(view_name))
        item_layout.addWidget(delete_btn)
        
        return item_frame
    
    def _restore_view(self, view_name: str):
        """恢复指定视图"""
        original_text = None  # 初始化变量
        try:
            # 先检查视图数据是否存在
            view_details = self.view_service.get_view_details(view_name)
            if not view_details:
                qt.QMessageBox.warning(
                    self,
                    "视图不存在",
                    f"视图标记 '{view_name}' 已不存在，可能已被删除。"
                )
                self._refresh_marked_views_list()
                return
            
            # 获取期像信息用于反馈显示
            view_phase = view_details.get('phase')
            phase_display = view_details.get('phase_display', '未知期像')
            has_phase_info = view_phase is not None
            
            # 提供视觉反馈
            # 兼容不同Qt绑定的text访问（方法或属性）
            _btn_text_attr = getattr(self.mark_btn, "text", "")
            original_text = _btn_text_attr() if callable(_btn_text_attr) else str(_btn_text_attr)
            self.mark_btn.setEnabled(False)
            
            # 阶段1：如果有期像信息，显示期像恢复状态
            if has_phase_info:
                self.mark_btn.setText(f"🔄 正在恢复期像...")
                self.statusUpdated.emit(f"正在恢复期像: {phase_display}")
                qt.QApplication.processEvents()
                
                # 短暂延迟以显示期像恢复状态
                qt.QTimer.singleShot(300, lambda: self._continue_restore_mpr_position(view_name, original_text, has_phase_info))
            else:
                # 直接进入MPR恢复阶段
                self._continue_restore_mpr_position(view_name, original_text, has_phase_info)
                
        except Exception as e:
            logging.error(f"恢复视图失败: {e}")
            # 确保original_text有值，避免UnboundLocalError
            if original_text is None:
                original_text = "📌 标记 (Ctrl+M)" if not self.compact_mode else "📌 标记"
            self._on_view_restore_error(str(e), original_text)
    
    def _continue_restore_mpr_position(self, view_name: str, original_text: str, has_phase_info: bool):
        """继续恢复MPR位置的阶段"""
        try:
            # 阶段2：显示MPR位置恢复状态
            self.mark_btn.setText("🔄 正在定位视图...")
            self.statusUpdated.emit("正在定位MPR视图位置...")
            qt.QApplication.processEvents()
            
            # 调用服务恢复视图（包含期像恢复和MPR定位）
            success = self.view_service.restore_view(view_name)
            
            if success:
                self.viewRestored.emit(view_name)
                
                # 调用回调函数
                for callback in self.restore_callbacks:
                    try:
                        callback(view_name)
                    except Exception as e:
                        logging.error(f"执行恢复回调失败: {e}")
                
                # 根据是否有期像信息生成不同的成功消息
                if has_phase_info:
                    view_details = self.view_service.get_view_details(view_name)
                    phase_display = view_details.get('phase_display', '未知期像') if view_details else '未知期像'
                    self.statusUpdated.emit(f"已恢复视图: {view_name} ({phase_display})")
                else:
                    self.statusUpdated.emit(f"已恢复视图: {view_name} (仅MPR位置)")
                
                # 成功恢复后稍作延迟
                qt.QTimer.singleShot(500, lambda: self._on_view_restore_success(original_text, has_phase_info))
                logging.info(f"成功恢复视图: {view_name}")
            else:
                self._on_view_restore_failed(view_name, original_text)
                
        except Exception as e:
            logging.error(f"MPR位置恢复失败: {e}")
            self._on_view_restore_error(str(e), original_text)
    
    def _on_view_restore_success(self, original_text: str, has_phase_info: bool = False):
        """视图恢复成功的回调"""
        if has_phase_info:
            self.mark_btn.setText("✅ 完整恢复")
        else:
            self.mark_btn.setText("✅ 已恢复")
        self.mark_btn.setEnabled(True)
        # 2秒后恢复原始文本
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText(original_text))
    
    def _on_view_restore_failed(self, view_name: str, original_text: str):
        """视图恢复失败的回调"""
        self.mark_btn.setText("❌ 恢复失败")
        self.mark_btn.setEnabled(True)
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText(original_text))
        
        qt.QMessageBox.warning(
            self,
            "恢复失败",
            f"无法恢复视图 '{view_name}'。\n\n"
            "可能的原因：\n"
            "• 视图数据已损坏\n"
            "• MPR系统状态异常\n"
            "• 几何参数超出有效范围"
        )
    
    def _on_view_restore_error(self, error_msg: str, original_text: str):
        """视图恢复异常的回调"""
        self.mark_btn.setText("❌ 恢复失败")
        self.mark_btn.setEnabled(True)
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText(original_text))
        
        qt.QMessageBox.critical(
            self,
            "恢复错误",
            f"恢复视图时发生严重错误：\n\n{error_msg}\n\n"
            "请检查系统状态后重试。"
        )
    
    def _delete_view(self, view_name: str):
        """删除指定视图标记"""
        reply = qt.QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除视图标记 '{view_name}' 吗？",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            success = self.view_service.clear_view_mark(view_name)
            if success:
                self._refresh_marked_views_list()
                self.viewDeleted.emit(view_name)
                self.statusUpdated.emit(f"已删除视图: {view_name}")
                
                # 调用回调函数
                for callback in self.delete_callbacks:
                    try:
                        callback(view_name)
                    except Exception as e:
                        logging.error(f"执行删除回调失败: {e}")
                
                logging.info(f"已删除视图标记: {view_name}")
    
    def _clear_all_views(self):
        """清除所有视图标记"""
        stats = self.view_service.get_statistics()
        count = stats['total_count']
        
        if count == 0:
            qt.QMessageBox.information(self, "提示", "当前没有已标记的视图。")
            return
        
        reply = qt.QMessageBox.question(
            self,
            "确认清除",
            f"确定要清除所有 {count} 个视图标记吗？\n\n此操作不可撤销。",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            success = self.view_service.clear_all_marks()
            if success:
                self._refresh_marked_views_list()
                self.statusUpdated.emit(f"已清除所有视图标记 ({count}个)")
                qt.QMessageBox.information(self, "清除完成", f"已清除所有 {count} 个视图标记。")
    
    def _export_views(self):
        """导出视图标记"""
        stats = self.view_service.get_statistics()
        count = stats['total_count']
        
        if count == 0:
            qt.QMessageBox.information(self, "提示", "当前没有已标记的视图可以导出。")
            return
        
        export_path = self.view_service.export_views()
        if export_path:
            qt.QMessageBox.information(
                self,
                "导出成功",
                f"已导出 {count} 个视图标记到：\n\n{export_path}"
            )
        else:
            qt.QMessageBox.warning(self, "导出失败", "导出视图标记时发生错误。")
    
    def _show_statistics(self):
        """显示统计信息"""
        # 获取基础统计和期像统计
        basic_stats = self.view_service.get_statistics()
        phase_stats = self.view_service.get_phase_statistics()
        
        stats_text = f"分析类型：{basic_stats['analysis_type']}\n"
        stats_text += f"视图总数：{basic_stats['total_count']}\n"
        
        if basic_stats['total_count'] > 0:
            stats_text += f"最早标记：{basic_stats['oldest_mark']}\n"
            stats_text += f"最新标记：{basic_stats['newest_mark']}\n"
            
            # 期像分布统计
            stats_text += "\n📊 期像分布：\n"
            phase_distribution = phase_stats['phase_distribution']
            
            for phase_key, phase_info in phase_distribution.items():
                icon = phase_info['icon']
                display_name = phase_info['display_name']
                count = phase_info['count']
                
                if count > 0:
                    stats_text += f"  {icon} {display_name}：{count} 个视图\n"
            
            # 分期像详细列表
            stats_text += "\n📋 详细列表：\n"
            
            # 舒张末期视图
            diastole_views = phase_distribution['diastole']['views']
            if diastole_views:
                stats_text += f"  🫀 舒张末期 ({len(diastole_views)} 个)：\n"
                for i, name in enumerate(diastole_views, 1):
                    stats_text += f"    {i}. {name}\n"
            
            # 收缩末期视图
            systole_views = phase_distribution['systole']['views']
            if systole_views:
                stats_text += f"  ❤️ 收缩末期 ({len(systole_views)} 个)：\n"
                for i, name in enumerate(systole_views, 1):
                    stats_text += f"    {i}. {name}\n"
                    
            # 未知期像视图
            unknown_views = phase_distribution['unknown']['views']
            if unknown_views:
                stats_text += f"  ❓ 未知期像 ({len(unknown_views)} 个)：\n"
                for i, name in enumerate(unknown_views, 1):
                    stats_text += f"    {i}. {name}\n"
        else:
            stats_text += "\n当前没有已标记的视图。"
        
        qt.QMessageBox.information(self, f"{self.analysis_type}分析 - 视图统计", stats_text)
    
    # 公共接口方法
    def add_mark_callback(self, callback: Callable[[str], None]):
        """添加视图标记回调函数"""
        self.mark_callbacks.append(callback)
    
    def add_restore_callback(self, callback: Callable[[str], None]):
        """添加视图恢复回调函数"""
        self.restore_callbacks.append(callback)
    
    def add_delete_callback(self, callback: Callable[[str], None]):
        """添加视图删除回调函数"""
        self.delete_callbacks.append(callback)
    
    def get_marked_views_count(self) -> int:
        """获取已标记视图的数量"""
        return self.view_service.get_statistics()['total_count']
    
    def get_marked_view_names(self) -> List[str]:
        """获取所有已标记视图的名称列表"""
        return list(self.view_service.get_marked_views().keys())
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        self.view_service.set_session(session)
        self._refresh_marked_views_list()
    
    def refresh(self):
        """刷新界面显示"""
        self._refresh_marked_views_list()
    
    def cleanup(self):
        """清理资源"""
        # 清理回调函数列表
        self.mark_callbacks.clear()
        self.restore_callbacks.clear()
        self.delete_callbacks.clear()
        
        # 清理服务
        if hasattr(self, 'view_service'):
            self.view_service.cleanup()
        
        logging.info(f"KeyViewManagerWidget 清理完成 - {self.analysis_type}")


# 工厂函数，方便创建不同样式的组件
def create_key_view_manager(
    analysis_type: str,
    session: Optional[TAVRStudySession] = None,
    compact: bool = False,
    parent=None
) -> KeyViewManagerWidget:
    """
    创建关键视图管理器组件的工厂函数
    
    Args:
        analysis_type: 分析类型
        session: 会话对象
        compact: 是否使用紧凑模式
        parent: 父组件
        
    Returns:
        KeyViewManagerWidget: 关键视图管理器组件实例
    """
    return KeyViewManagerWidget(analysis_type, session, compact, parent)
