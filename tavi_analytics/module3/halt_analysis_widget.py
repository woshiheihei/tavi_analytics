"""
HALT分析界面组件

瓣叶功能评估中的HALT (低密度瓣叶增厚) 分析的专门用户界面实现，包含：
- 引导式分析流程（自动切换到舒张末期 + MPR定位到支架底部）
- 三个瓣叶的HALT状态记录表单
- 关键视图标记功能（使用公共组件）
- 测量工具集成

重构更新：
- 移除内部的ViewMarkingManager，改用公共的ViewMarkingService
- 使用通用的KeyViewManagerWidget组件
- 保持所有原有功能的兼容性

作者：TAVR Research Team
创建时间：2025年8月
重构时间：2025年8月
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.phase_selection_widget import PhaseSelectionWidget
    from ..widgets.key_view_manager_widget import KeyViewManagerWidget  # 使用公共组件
    from ..services.contour_positioning_service import get_contour_position_service
    from ..services.view_marking_service import get_view_marking_service  # 使用公共服务
    from ..utils.mpr_positioning.plane_position_manager import get_plane_position_manager
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    # 添加父目录和当前目录到sys.path
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from widgets.phase_selection_widget import PhaseSelectionWidget
    from widgets.key_view_manager_widget import KeyViewManagerWidget
    from services.contour_positioning_service import get_contour_position_service
    from services.view_marking_service import get_view_marking_service
    from utils.mpr_positioning.plane_position_manager import get_plane_position_manager


class LeafletGradeRow(qt.QWidget):
    """单个瓣叶的HALT分级行"""
    
    # 信号：当分级改变时发出
    gradeChanged = qt.Signal(str, str)  # (leaflet_name, grade)
    
    def __init__(self, leaflet_name: str, parent=None):
        super().__init__(parent)
        self.leaflet_name = leaflet_name
        self.setObjectName(f"LeafletGradeRow_{leaflet_name}")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置瓣叶分级行界面"""
        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # 增加水平边距，保持垂直紧凑
        layout.setSpacing(8)  # 增加组件间距
        
        # 瓣叶名称标签 - 极简版本
        name_label = qt.QLabel(f"{self.leaflet_name}")
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 32px;
                text-align: center;
            }
        """)
        name_label.setAlignment(qt.Qt.AlignCenter)
        layout.addWidget(name_label)
        
        # 分级按钮组
        self.grade_group = qt.QButtonGroup()
        self.grade_buttons = {}
        
        # 更规范的分级标签和颜色
        grade_configs = [
            ("0", "#e8f5e8", "#28a745"),      # 绿色系 - 无HALT
            ("≤25%", "#fff3cd", "#ffc107"),   # 黄色系 - 轻度
            ("25-50%", "#ffeaa7", "#fd7e14"), # 橙色系 - 中度  
            ("50%-75%", "#fadbd8", "#dc3545"), # 红色系 - 重度
            (">75%", "#f8d7da", "#721c24")     # 深红系 - 极重度
        ]
        
        for i, (grade_value, bg_color, border_color) in enumerate(grade_configs):
            button = qt.QRadioButton(grade_value)
            
            # 设置按钮样式 - 动态弹性布局
            button.setStyleSheet(f"""
                QRadioButton {{
                    background-color: {bg_color};
                    border: 1px solid {bg_color};
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-size: 9px;
                    font-weight: 500;
                    text-align: center;
                    min-width: 48px;
                    min-height: 26px;
                    color: #2c3e50;
                }}
                QRadioButton:checked {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    font-weight: bold;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }}
                QRadioButton:hover {{
                    border: 1px solid {border_color};
                    box-shadow: 0 0px 1px rgba(0,0,0,0.08);
                }}
                QRadioButton::indicator {{
                    width: 0px;
                    height: 0px;
                }}
            """)
            
            self.grade_group.addButton(button, i)
            self.grade_buttons[grade_value] = button
            layout.addWidget(button)
        
        # 默认选择"0"
        self.grade_buttons["0"].setChecked(True)
        
        # 连接信号
        self.grade_group.buttonClicked.connect(self._on_grade_changed)
        
        layout.addStretch()
    
    def _on_grade_changed(self, button):
        """分级改变时的回调"""
        grade = button.text
        self.gradeChanged.emit(self.leaflet_name, grade)
    
    def get_grade(self) -> str:
        """获取当前分级"""
        checked_button = self.grade_group.checkedButton()
        return checked_button.text if checked_button else "0"
    
    def set_grade(self, grade: str):
        """设置分级"""
        if grade in self.grade_buttons:
            self.grade_buttons[grade].setChecked(True)


class HaltAnalysisWidget(qt.QWidget):
    """HALT分析主界面 - 使用公共关键视图组件"""
    
    # 信号：状态改变
    statusChanged = qt.Signal(dict)  # 发出完整的HALT分析状态
    
    def __init__(self, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.session = session
        
        # 服务组件
        self.contour_service = get_contour_position_service()
        self.view_marking_service = get_view_marking_service("HALT", session)  # 使用公共服务
        
        # 期像选择组件 - 复用已有的期像切换逻辑
        self.phase_widget = PhaseSelectionWidget(session, parent=self)
        self.phase_widget.setVisible(False)  # 隐藏，仅用于逻辑复用
        
        # 分析状态
        self.analysis_started = False
        self.overall_halt_status = "无"  # 无/有/难以判定
        self.leaflet_grades: Dict[str, str] = {"LC": "0", "RC": "0", "NC": "0"}
        
        self.setObjectName("HaltAnalysisWidget")
        self._setup_ui()
        logging.info("HaltAnalysisWidget 初始化完成（重构版本）")
    
    def _setup_ui(self):
        """设置HALT分析主界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 减小边距
        main_layout.setSpacing(8)  # 减小间距
        
        # 主标题 - 更简洁紧凑的样式
        title = qt.QLabel("HALT 瓣叶低密度增厚评估")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 6px 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 创建滚动区域容纳主要内容
        scroll_area = qt.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(qt.QFrame.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        
        # 滚动区域内容容器
        scroll_content = qt.QWidget()
        content_layout = qt.QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(4, 4, 4, 4)  # 减小边距
        content_layout.setSpacing(6)  # 减小间距
        
        # 0. 分析控制区域（开始HALT分析）
        self._create_analysis_control_section(content_layout)
        
        # 1. 整体HALT状态选择
        self._create_overall_status_section(content_layout)
        
        # 2. 瓣叶分级表格（条件显示）
        self._create_grading_section(content_layout)
        
        # 3. 统计信息（条件显示）
        self._create_summary_section(content_layout)
        
        # 4. 关键视图管理 - 使用公共组件
        self._create_key_view_section(content_layout)
        
        # 添加弹性空间
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # 占据大部分空间
        
        # 5. 操作按钮 - 固定在底部
        self._create_action_buttons_section(main_layout)
        
        # 初始状态更新
        self._update_visibility()
        self._update_analysis_control_visibility()
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域（简化版）"""
        self.control_frame = qt.QFrame()
        self.control_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        control_layout = qt.QHBoxLayout(self.control_frame)
        control_layout.setSpacing(6)  # 减小间距
        control_layout.setContentsMargins(6, 6, 6, 6)  # 减小边距
        
        # 简化的说明
        instruction_label = qt.QLabel("💡 准备分析环境")
        instruction_label.setStyleSheet("font-size: 10px; color: #495057; font-weight: 500;")
        control_layout.addWidget(instruction_label)
        
        # 开始分析按钮（更紧凑版）
        self.start_analysis_btn = qt.QPushButton("开始分析")
        self.start_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        
        # 跳过按钮（更小）
        self.skip_analysis_btn = qt.QPushButton("跳过")
        self.skip_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 6px;
                font-size: 10px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_analysis_btn.clicked.connect(self._on_skip_analysis)
        control_layout.addWidget(self.skip_analysis_btn)
        
        # 状态显示（内联）
        self.analysis_status_label = qt.QLabel("等待开始")
        self.analysis_status_label.setStyleSheet("font-size: 9px; color: #868e96; font-style: italic;")
        control_layout.addWidget(self.analysis_status_label)
        
        control_layout.addStretch()
        
        parent_layout.addWidget(self.control_frame)
    
    def _create_overall_status_section(self, parent_layout):
        """创建整体HALT状态选择区域"""
        status_frame = qt.QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        status_layout = qt.QVBoxLayout(status_frame)
        status_layout.setSpacing(6)  # 减小间距
        
        # 标题 - 更紧凑
        status_title = qt.QLabel("1. HALT状态")
        status_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        status_layout.addWidget(status_title)
        
        # 选项按钮 - 更紧凑布局
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(6)  # 减小间距
        
        self.overall_status_group = qt.QButtonGroup()
        
        # 样式定义 - 更简洁的设计
        button_configs = [
            ("无", "#d4f6d4", "#28a745"),
            ("有", "#fdeaea", "#dc3545"),
            ("难以判定", "#fff8dc", "#ffc107")
        ]
        
        self.status_buttons = {}
        for i, (status, bg_color, border_color) in enumerate(button_configs):
            button = qt.QRadioButton(status)
            button.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 12px;
                    margin: 1px;
                    background-color: {bg_color};
                    border: 2px solid {bg_color};
                    border-radius: 4px;
                }}
                QRadioButton:checked {{
                    border: 2px solid {border_color};
                    font-weight: bold;
                    background-color: white;
                }}
                QRadioButton:hover {{
                    border: 2px solid {border_color};
                }}
            """)
            
            self.overall_status_group.addButton(button, i)
            self.status_buttons[status] = button
            buttons_layout.addWidget(button)
        
        # 默认选择"无"
        self.status_buttons["无"].setChecked(True)
        
        # 连接信号
        self.overall_status_group.buttonClicked.connect(self._on_overall_status_changed)
        
        buttons_layout.addStretch()
        status_layout.addLayout(buttons_layout)
        
        parent_layout.addWidget(status_frame)
    
    def _create_grading_section(self, parent_layout):
        """创建瓣叶分级区域"""
        self.grading_frame = qt.QFrame()
        self.grading_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #007bff;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
        """)
        
        grading_layout = qt.QVBoxLayout(self.grading_frame)
        grading_layout.setSpacing(4)  # 更小间距
        
        # 紧凑的标题和说明 - 合并到一行
        header_layout = qt.QHBoxLayout()
        header_layout.setSpacing(8)
        
        grading_title = qt.QLabel("2. HALT分级")
        grading_title.setStyleSheet("""
            QLabel {
                font-size: 12px; 
                font-weight: bold; 
                color: #2c3e50; 
                padding: 2px 0px;
            }
        """)
        header_layout.addWidget(grading_title)
        
        # 内联说明和图例
        info_legend = qt.QLabel("(选择分级: 0 → ≤25% → 25-50% → 50%-75% → >75%)")
        info_legend.setStyleSheet("""
            QLabel {
                font-size: 9px;
                color: #6c757d;
                font-style: italic;
            }
        """)
        header_layout.addWidget(info_legend)
        header_layout.addStretch()
        
        grading_layout.addLayout(header_layout)
        
        # 分级表格 - 更紧凑布局
        self.leaflet_grade_rows = {}
        for leaflet in ["LC", "RC", "NC"]:
            row = LeafletGradeRow(leaflet)
            row.gradeChanged.connect(self._on_leaflet_grade_changed)
            self.leaflet_grade_rows[leaflet] = row
            grading_layout.addWidget(row)
        
        parent_layout.addWidget(self.grading_frame)
    
    def _create_summary_section(self, parent_layout):
        """创建统计信息区域"""
        self.summary_frame = qt.QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 8px;
            }
        """)
        
        summary_layout = qt.QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(6, 3, 6, 3)  # 减小边距
        summary_layout.setSpacing(12)  # 减小间距
        
        # 受累瓣叶个数 - 更紧凑
        self.affected_count_label = qt.QLabel("受累瓣叶: 0个")
        self.affected_count_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #28a745;")
        summary_layout.addWidget(self.affected_count_label)
        
        summary_layout.addStretch()
        
        # 最高分级 - 更紧凑
        self.max_grade_label = qt.QLabel("最高分级: 0")
        self.max_grade_label.setStyleSheet("font-size: 10px; color: #495057; font-weight: 500;")
        summary_layout.addWidget(self.max_grade_label)
        
        parent_layout.addWidget(self.summary_frame)
    
    def _create_key_view_section(self, parent_layout):
        """创建关键视图管理区域 - 使用公共组件"""
        # 创建关键视图管理器组件
        self.key_view_manager = KeyViewManagerWidget(
            analysis_type="HALT",
            session=self.session,
            compact_mode=True,  # 使用紧凑模式
            parent=self
        )
        
        # 连接信号
        self.key_view_manager.viewMarked.connect(self._on_view_marked)
        self.key_view_manager.viewRestored.connect(self._on_view_restored)
        self.key_view_manager.viewDeleted.connect(self._on_view_deleted)
        self.key_view_manager.statusUpdated.connect(self._on_view_status_updated)
        
        parent_layout.addWidget(self.key_view_manager)
    
    def _create_action_buttons_section(self, parent_layout):
        """创建操作按钮区域"""
        actions_layout = qt.QHBoxLayout()
        actions_layout.setSpacing(6)  # 减小间距
        actions_layout.setContentsMargins(2, 6, 2, 2)  # 减小边距
        
        # 重置按钮 - 更紧凑
        reset_btn = qt.QPushButton("重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_btn.clicked.connect(self._reset_analysis)
        
        # 导出结果按钮 - 更紧凑
        export_btn = qt.QPushButton("导出结果")
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        export_btn.clicked.connect(self._export_results)
        
        actions_layout.addWidget(reset_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(export_btn)
        
        parent_layout.addLayout(actions_layout)
    
    # 关键视图相关的回调函数
    def _on_view_marked(self, view_name: str):
        """视图被标记时的回调"""
        logging.info(f"HALT分析 - 视图已标记: {view_name}")
    
    def _on_view_restored(self, view_name: str):
        """视图被恢复时的回调"""
        logging.info(f"HALT分析 - 视图已恢复: {view_name}")
        # 恢复视图后可能需要刷新3D视图
        self._refresh_3d_view()
    
    def _on_view_deleted(self, view_name: str):
        """视图被删除时的回调"""
        logging.info(f"HALT分析 - 视图已删除: {view_name}")
    
    def _on_view_status_updated(self, status: str):
        """关键视图状态更新时的回调"""
        logging.debug(f"HALT分析 - 关键视图状态: {status}")
    
    def _on_overall_status_changed(self, button):
        """整体HALT状态改变时的回调"""
        self.overall_halt_status = button.text
        self._update_visibility()
        self._update_summary()
        self._emit_status_changed()
        
        logging.info(f"整体HALT状态更新为: {self.overall_halt_status}")
    
    def _on_start_analysis(self):
        """开始HALT分析"""
        try:
            logging.info("用户开始HALT分析")
            
            # 更新状态
            self.analysis_status_label.setText("准备中...")
            self.start_analysis_btn.setEnabled(False)
            self.skip_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 1. 切换到舒张末期
            self.analysis_status_label.setText("切换期相...")
            qt.QApplication.processEvents()
            
            # 检查是否有舒张末期标记
            end_diastole_info = self.session.get_marked_phase('end_diastole')
            if not end_diastole_info or end_diastole_info.get('frame_index') is None:
                qt.QMessageBox.warning(
                    self,
                    "警告",
                    "未找到舒张末期标记！\n\n"
                    "请先在模块一中标记舒张末期时相。"
                )
                self._reset_analysis_buttons()
                return
            
            # 切换到舒张末期
            success = self._switch_to_end_diastole()
            if not success:
                qt.QMessageBox.warning(
                    self,
                    "错误",
                    "切换到舒张末期失败！请检查模块一中的期像标记。"
                )
                self._reset_analysis_buttons()
                return
            
            # 2. MPR定位到支架底部平面
            self.analysis_status_label.setText("定位平面...")
            qt.QApplication.processEvents()
            
            success = self._position_to_stent_bottom()
            if not success:
                # 简化警告信息
                qt.QMessageBox.information(
                    self,
                    "提示",
                    "自动定位失败，请手动调整MPR视图到合适位置。\n分析可以继续进行。"
                )
            
            # 3. 完成准备
            self._complete_analysis_preparation()
            
            logging.info("HALT分析环境准备完成")
            
        except Exception as e:
            logging.error(f"开始HALT分析失败: {e}")
            qt.QMessageBox.critical(
                self,
                "错误", 
                f"分析启动失败：\n{e}"
            )
            self._reset_analysis_buttons()
    
    def _on_skip_analysis(self):
        """跳过自动分析，直接进入评估"""
        reply = qt.QMessageBox.question(
            self,
            "跳过自动分析",
            "跳过自动分析，直接开始评估？",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self._complete_analysis_preparation()
            logging.info("用户选择跳过自动分析")
    
    def _complete_analysis_preparation(self):
        """完成分析准备"""
        self.analysis_started = True
        self.analysis_status_label.setText("已就绪")
        
        # 隐藏分析控制区域
        self.control_frame.setVisible(False)
        
        # 默认显示axial切片在3D视图中
        self._show_axial_slice_in_3d()
        
        # 更新其他区域的可见性
        self._update_analysis_control_visibility()
        
        logging.info("HALT分析准备完成")
    
    def _reset_analysis_buttons(self):
        """重置分析按钮状态"""
        self.start_analysis_btn.setEnabled(True)
        self.skip_analysis_btn.setEnabled(True)
        self.analysis_status_label.setText("等待开始")
    
    def _switch_to_end_diastole(self) -> bool:
        """切换到舒张末期 - 复用PhaseSelectionWidget的逻辑"""
        try:
            # 使用PhaseSelectionWidget的自动切换逻辑
            success = self.phase_widget._auto_switch_to_end_diastole()
            
            if success:
                # 同步更新轮廓服务的期像设置
                self.contour_service.set_current_phase('end_diastole')
                
                # 设置当前期像并触发显示管理
                self.phase_widget.set_current_phase('diastole')
                
                logging.info("成功切换到舒张末期（复用PhaseSelectionWidget逻辑）")
                return True
            else:
                logging.error("使用PhaseSelectionWidget切换到舒张末期失败")
                return False
            
        except Exception as e:
            logging.error(f"切换到舒张末期失败: {e}")
            return False
    
    def _position_to_stent_bottom(self) -> bool:
        """MPR定位到支架底部平面"""
        try:
            # 首先检查并记录场景中所有可能相关的轮廓节点
            self._log_available_contour_nodes()
            
            # 尝试使用轮廓定位服务
            success = self.contour_service.switch_to_contour('valve_stent_bottom', phase='end_diastole')
            
            if success:
                logging.info("成功定位到支架底部平面")
                return True
            
            # 如果失败，尝试使用ContourPositionManager作为后备方案
            logging.warning("轮廓定位服务失败，尝试后备方案...")
            
            try:
                from ..utils.contour_position.contour_position_manager import ContourPositionManager
                contour_manager = ContourPositionManager()
                contour_manager.set_current_phase('end_diastole')
                
                # 尝试使用ContourPositionManager
                success = contour_manager.switch_to_contour('valve_stent_bottom', phase='end_diastole')
                
                if success:
                    logging.info("使用后备方案成功定位到支架底部平面")
                    return True
                else:
                    logging.warning("后备方案也失败，但分析可以继续")
                    return False
                    
            except Exception as fallback_error:
                logging.error(f"后备方案失败: {fallback_error}")
                logging.warning("定位到支架底部平面失败，但分析可以继续")
                return False
            
        except Exception as e:
            logging.error(f"定位到支架底部平面失败: {e}")
            return False
    
    def _log_available_contour_nodes(self):
        """记录场景中所有可能的轮廓节点，用于调试"""
        try:
            import slicer
            
            # 查找所有可能的轮廓相关节点
            keywords = ['contour', 'stent', 'valve', 'bottom', 'diastole', 'ValveStent']
            found_nodes = []
            
            # 获取所有节点
            scene = slicer.mrmlScene
            for i in range(scene.GetNumberOfNodes()):
                node = scene.GetNthNode(i)
                if node and hasattr(node, 'GetName'):
                    node_name = node.GetName()
                    # 检查是否包含任何关键词
                    if any(keyword.lower() in node_name.lower() for keyword in keywords):
                        found_nodes.append({
                            'name': node_name,
                            'type': node.GetClassName(),
                            'id': node.GetID()
                        })
            
            if found_nodes:
                logging.info("场景中发现的可能相关轮廓节点:")
                for node_info in found_nodes:
                    logging.info(f"  - {node_info['name']} ({node_info['type']})")
            else:
                logging.warning("场景中未发现任何轮廓相关节点")
                logging.info("提示：请确认模块二已运行并成功生成轮廓数据")
                
        except Exception as e:
            logging.error(f"记录可用轮廓节点时出错: {e}")
    
    def _show_axial_slice_in_3d(self):
        """在3D视图中显示axial切片"""
        try:
            import slicer
            
            # 获取axial切片节点（Red切片）
            axial_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed")
            
            if axial_slice_node:
                # 设置axial切片在3D视图中可见
                axial_slice_node.SetSliceVisible(True)
                
                # 确保其他切片在3D视图中不可见（保持focus在axial）
                green_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen")
                yellow_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow")
                
                if green_slice_node:
                    green_slice_node.SetSliceVisible(False)
                if yellow_slice_node:
                    yellow_slice_node.SetSliceVisible(False)
                
                # 刷新3D视图以确保变更生效
                self._refresh_3d_view()
                
                logging.info("已在3D视图中显示axial切片")
                
            else:
                logging.warning("无法找到axial切片节点")
                
        except Exception as e:
            logging.error(f"在3D视图中显示axial切片失败: {e}")
    
    def _update_analysis_control_visibility(self):
        """根据分析状态更新分析控制区域的可见性"""
        # 如果分析已经开始，隐藏控制区域
        if hasattr(self, 'control_frame'):
            self.control_frame.setVisible(not self.analysis_started)
    
    
    
    
    
    
    
    
    
    def _refresh_3d_view(self):
        """刷新3D视图"""
        try:
            import slicer
            
            layout_manager = slicer.app.layoutManager()
            if layout_manager:
                # 刷新主3D视图
                threeDWidget = layout_manager.threeDWidget(0)
                if threeDWidget:
                    threeDView = threeDWidget.threeDView()
                    if threeDView:
                        threeDView.forceRender()
                
                # 如果有多个3D视图，也一并刷新
                for i in range(layout_manager.threeDViewCount):
                    widget = layout_manager.threeDWidget(i)
                    if widget:
                        view = widget.threeDView()
                        if view:
                            view.forceRender()
                
                logging.debug("3D视图刷新完成")
                
        except Exception as e:
            logging.error(f"刷新3D视图时出错: {e}")
    
    
    def _on_leaflet_grade_changed(self, leaflet_name: str, grade: str):
        """瓣叶分级改变时的回调"""
        self.leaflet_grades[leaflet_name] = grade
        self._update_summary()
        self._emit_status_changed()
        
        logging.info(f"瓣叶 {leaflet_name} 分级更新为: {grade}")
    
    def _update_visibility(self):
        """根据整体HALT状态更新界面可见性"""
        has_halt = self.overall_halt_status == "有"
        
        self.grading_frame.setVisible(has_halt)
        self.summary_frame.setVisible(has_halt)
        
        if not has_halt:
            # 重置所有瓣叶分级为0
            for leaflet_name, row in self.leaflet_grade_rows.items():
                row.set_grade("0")
                self.leaflet_grades[leaflet_name] = "0"
            self._update_summary()
    
    
    def _update_summary(self):
        """更新统计信息"""
        if self.overall_halt_status != "有":
            self.affected_count_label.setText("受累瓣叶: 0个")
            self.max_grade_label.setText("最高分级: 0")
            return
        
        # 计算受累瓣叶个数（分级不为"0"的瓣叶）
        affected_count = sum(1 for grade in self.leaflet_grades.values() if grade != "0")
        
        # 找出最高分级
        grade_order = ["0", "≤25%", "25-50%", "50%-75%", ">75%"]
        max_grade = "0"
        for grade in reversed(grade_order):
            if grade in self.leaflet_grades.values():
                max_grade = grade
                break
        
        # 更新标签
        self.affected_count_label.setText(f"受累瓣叶: {affected_count}个")
        self.max_grade_label.setText(f"最高分级: {max_grade}")
        
        # 更新颜色
        if affected_count == 0:
            color = "#28a745"  # 绿色
        elif affected_count <= 2:
            color = "#ffc107"  # 黄色
        else:
            color = "#dc3545"  # 红色
        
        self.affected_count_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")
    
    def _reset_analysis(self):
        """重置分析"""
        reply = qt.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置HALT分析吗？\n\n这将清除所有输入的数据并返回到初始状态。",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            # 重置分析状态
            self.analysis_started = False
            
            # 重置整体状态
            self.status_buttons["无"].setChecked(True)
            self.overall_halt_status = "无"
            
            # 重置所有瓣叶分级
            for leaflet_name, row in self.leaflet_grade_rows.items():
                row.set_grade("0")
                self.leaflet_grades[leaflet_name] = "0"
            
            # 重置分析控制区域
            if hasattr(self, 'control_frame'):
                self.control_frame.setVisible(True)
                self.start_analysis_btn.setEnabled(True)
                self.skip_analysis_btn.setEnabled(True)
                self.analysis_status_label.setText("等待开始")
            
            # 更新界面
            self._update_visibility()
            self._update_analysis_control_visibility()
            self._emit_status_changed()
            
            # 重新显示axial切片
            self._show_axial_slice_in_3d()
            
            logging.info("HALT分析已重置")
    
    def _export_results(self):
        """导出结果"""
        try:
            results = self.get_analysis_results()
            
            # 生成可读的分析报告
            report = self._generate_analysis_report(results)
            
            # 简单的文本导出
            from pathlib import Path
            import json
            
            export_dir = Path.home() / "TAVR_Analytics_Exports"
            export_dir.mkdir(exist_ok=True)
            
            timestamp = qt.QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
            
            # 导出JSON数据
            json_file = export_dir / f"HALT_Analysis_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 导出可读报告
            report_file = export_dir / f"HALT_Report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            qt.QMessageBox.information(
                self,
                "导出成功",
                f"HALT分析结果已导出：\n\n"
                f"数据文件：{json_file}\n"
                f"报告文件：{report_file}"
            )
            
        except Exception as e:
            logging.error(f"导出HALT分析结果失败: {e}")
            qt.QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中出现错误：\n{e}"
            )
    
    def _generate_analysis_report(self, results: Dict[str, Any]) -> str:
        """生成可读的分析报告"""
        report = []
        report.append("=== HALT分析报告 ===")
        report.append(f"生成时间：{results['analysis_timestamp']}")
        report.append("")
        
        # 整体状态
        report.append(f"瓣叶低密度增厚（HALT）：{results['overall_status']}")
        
        if results['overall_status'] == "有":
            report.append(f"受累瓣叶个数：{results['affected_leaflets_count']}")
            report.append("")
            
            # 各瓣叶分级
            report.append("HALT分级：")
            for leaflet, grade in results['leaflet_grades'].items():
                if grade != "0":
                    report.append(f"  {leaflet}瓣叶：{grade}")
                else:
                    report.append(f"  {leaflet}瓣叶：无HALT")
            
            report.append("")
            report.append(f"最高分级：{results['max_grade']}")
        
        # 关键视图标记
        view_count = results.get('key_views_count', 0)
        if view_count > 0:
            report.append("")
            report.append(f"关键视图标记：{view_count}个")
        
        return "\n".join(report)
    
    def _emit_status_changed(self):
        """发出状态改变信号"""
        self.statusChanged.emit(self.get_analysis_results())
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取完整的分析结果"""
        # 计算受累瓣叶个数
        affected_count = sum(1 for grade in self.leaflet_grades.values() if grade != "0")
        
        # 找出最高分级
        grade_order = ["0", "≤25%", "25-50%", "50%-75%", ">75%"]
        max_grade = "0"
        for grade in reversed(grade_order):
            if grade in self.leaflet_grades.values():
                max_grade = grade
                break
        
        # 获取关键视图统计
        key_views_count = self.key_view_manager.get_marked_views_count()
        key_view_names = self.key_view_manager.get_marked_view_names()
        
        return {
            'analysis_type': 'HALT',
            'overall_status': self.overall_halt_status,
            'leaflet_grades': dict(self.leaflet_grades),
            'affected_leaflets_count': affected_count,
            'max_grade': max_grade,
            'key_views_count': key_views_count,
            'key_view_names': key_view_names,
            'analysis_timestamp': qt.QDateTime.currentDateTime().toString(),
            'session_info': {
                'study_name': getattr(self.session, 'study_name', 'Unknown'),
                'patient_id': getattr(self.session, 'patient_id', 'Unknown')
            }
        }
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.set_session(session)
    
    def on_activated(self):
        """模块激活时调用"""
        logging.info("HALT分析界面激活")
        
        # 默认显示axial切片在3D视图中
        self._show_axial_slice_in_3d()
    
    def on_deactivated(self):
        """模块取消激活时调用"""
        logging.info("HALT分析界面取消激活")
        
        # 可选：恢复所有切片的默认显示状态
        self._restore_default_slice_visibility()
    
    def cleanup(self):
        """清理资源"""
        # 清理phase_widget
        if hasattr(self, 'phase_widget'):
            self.phase_widget.cleanup()
        
        # 清理关键视图管理器
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.cleanup()
        
        logging.info("HALT分析界面清理资源")
    
    def _restore_default_slice_visibility(self):
        """恢复默认的切片显示状态"""
        try:
            import slicer
            
            # 获取所有切片节点
            slice_nodes = {
                'Red': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed"),
                'Green': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen"), 
                'Yellow': slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow")
            }
            
            # 恢复所有切片的默认显示状态（通常是可见的）
            for name, node in slice_nodes.items():
                if node:
                    node.SetSliceVisible(True)
            
            # 刷新3D视图
            self._refresh_3d_view()
            
            logging.info("已恢复默认切片显示状态")
            
        except Exception as e:
            logging.error(f"恢复默认切片显示状态失败: {e}")