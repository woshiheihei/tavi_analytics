"""
HALT分析界面组件

瓣叶功能评估中的HALT (低密度瓣叶增厚) 分析的专门用户界面实现，包含：
- 引导式分析流程（自动切换到舒张末期 + MPR定位到支架底部）
- 三个瓣叶的HALT状态记录表单
- 关键视图标记功能
- 测量工具集成

作者：TAVR Research Team
创建时间：2025年8月
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
    from ..services.contour_positioning_service import get_contour_position_service
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
    from services.contour_positioning_service import get_contour_position_service
    from utils.mpr_positioning.plane_position_manager import get_plane_position_manager


class ViewMarkingManager:
    """视图标记管理器 - 保存和恢复MPR视图状态"""
    
    def __init__(self):
        self.marked_views: Dict[str, Dict[str, Any]] = {}
        self.plane_manager = get_plane_position_manager()
    
    def mark_current_view(self, view_name: str) -> bool:
        """
        标记当前MPR视图状态
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 标记成功返回True
        """
        try:
            # 获取当前MPR平面参数
            plane_params = self.plane_manager.get_current_plane_parameters()
            if not plane_params:
                logging.error("无法获取当前MPR平面参数")
                return False
            
            center_point, normal_vector = plane_params
            
            # 保存视图状态
            self.marked_views[view_name] = {
                'center_point': center_point.tolist(),
                'normal_vector': normal_vector.tolist(),
                'timestamp': qt.QDateTime.currentDateTime().toString(),
                'description': f"HALT分析关键视图 - {view_name}"
            }
            
            logging.info(f"已标记视图: {view_name}")
            return True
            
        except Exception as e:
            logging.error(f"标记视图失败: {e}")
            return False
    
    def restore_view(self, view_name: str) -> bool:
        """
        恢复指定的视图标记
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 恢复成功返回True
        """
        try:
            if view_name not in self.marked_views:
                logging.error(f"未找到视图标记: {view_name}")
                return False
            
            view_data = self.marked_views[view_name]
            import numpy as np
            center_point = np.array(view_data['center_point'])
            normal_vector = np.array(view_data['normal_vector'])
            
            # 恢复MPR视图
            success = self.plane_manager.position_to_plane(center_point, normal_vector)
            
            if success:
                logging.info(f"已恢复视图: {view_name}")
            else:
                logging.error(f"恢复视图失败: {view_name}")
            
            return success
            
        except Exception as e:
            logging.error(f"恢复视图失败: {e}")
            return False
    
    def get_marked_views(self) -> Dict[str, str]:
        """
        获取所有已标记的视图
        
        Returns:
            Dict[str, str]: 视图名称到描述的映射
        """
        return {name: data['description'] for name, data in self.marked_views.items()}
    
    def clear_view_mark(self, view_name: str) -> bool:
        """
        清除指定的视图标记
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 清除成功返回True
        """
        try:
            if view_name in self.marked_views:
                del self.marked_views[view_name]
                logging.info(f"已清除视图标记: {view_name}")
                return True
            else:
                logging.warning(f"视图标记不存在: {view_name}")
                return False
        except Exception as e:
            logging.error(f"清除视图标记失败: {e}")
            return False


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
        layout.setContentsMargins(6, 3, 6, 3)  # 减小边距
        layout.setSpacing(8)  # 减小间距
        
        # 瓣叶名称标签 - 更紧凑
        name_label = qt.QLabel(f"{self.leaflet_name}:")
        name_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")  # 减小字体
        name_label.setMinimumWidth(30)  # 减小宽度
        layout.addWidget(name_label)
        
        # 分级按钮组
        self.grade_group = qt.QButtonGroup()
        self.grade_buttons = {}
        
        grades = ["0", "≤25%", "25-50%", "50%-75%", ">75%"]
        colors = ["#e8f5e8", "#fff3cd", "#ffeaa7", "#fab1a0", "#e17055"]
        
        for i, grade in enumerate(grades):
            button = qt.QRadioButton(grade)
            button.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 11px;
                    padding: 4px 8px;
                    margin: 1px;
                    background-color: {colors[i]};
                    border: 1px solid transparent;
                    border-radius: 4px;
                    min-width: 50px;
                    max-width: 50px;
                }}
                QRadioButton:checked {{
                    background-color: {colors[i]};
                    border: 2px solid #007bff;
                    font-weight: bold;
                }}
                QRadioButton:hover {{
                    border: 1px solid #adb5bd;
                }}
            """)
            
            self.grade_group.addButton(button, i)
            self.grade_buttons[grade] = button
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
    """HALT分析主界面 - 重新设计为更符合医生需求的表单"""
    
    # 信号：状态改变
    statusChanged = qt.Signal(dict)  # 发出完整的HALT分析状态
    
    def __init__(self, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.session = session
        
        # 服务组件
        self.contour_service = get_contour_position_service()
        self.view_marking_manager = ViewMarkingManager()
        
        # 期像选择组件 - 复用已有的期像切换逻辑
        self.phase_widget = PhaseSelectionWidget(session, parent=self)
        self.phase_widget.setVisible(False)  # 隐藏，仅用于逻辑复用
        
        # 分析状态
        self.analysis_started = False
        self.overall_halt_status = "无"  # 无/有/难以判定
        self.measurement_phase = "舒张末期"  # 测量期相
        self.leaflet_grades: Dict[str, str] = {"LC": "0", "RC": "0", "NC": "0"}
        
        self.setObjectName("HaltAnalysisWidget")
        self._setup_ui()
        logging.info("HaltAnalysisWidget 初始化完成")
    
    def _setup_ui(self):
        """设置HALT分析主界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # 主标题 - 更简洁的样式
        title = qt.QLabel("HALT 瓣叶低密度增厚评估")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 8px 16px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-bottom: 5px;
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
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)
        
        # 0. 分析控制区域（开始HALT分析）
        self._create_analysis_control_section(content_layout)
        
        # 1. 整体HALT状态选择
        self._create_overall_status_section(content_layout)
        
        # 2. 测量期相选择（条件显示）
        self._create_phase_section(content_layout)
        
        # 3. 瓣叶分级表格（条件显示）
        self._create_grading_section(content_layout)
        
        # 4. 统计信息（条件显示）
        self._create_summary_section(content_layout)
        
        # 5. 视图标记（简化版）
        self._create_view_marking_section(content_layout)
        
        # 添加弹性空间
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # 占据大部分空间
        
        # 6. 操作按钮 - 固定在底部
        self._create_action_buttons_section(main_layout)
        
        # 初始状态更新
        self._update_visibility()
        self._update_analysis_control_visibility()
        
        # 初始化视图列表
        self._refresh_marked_views_list()
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域（简化版）"""
        self.control_frame = qt.QFrame()
        self.control_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border: 1px solid #bee5eb;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        control_layout = qt.QHBoxLayout(self.control_frame)
        control_layout.setSpacing(8)
        control_layout.setContentsMargins(8, 8, 8, 8)
        
        # 简化的说明
        instruction_label = qt.QLabel("💡 准备分析环境")
        instruction_label.setStyleSheet("font-size: 11px; color: #495057; font-weight: 500;")
        control_layout.addWidget(instruction_label)
        
        # 开始分析按钮（紧凑版）
        self.start_analysis_btn = qt.QPushButton("开始分析")
        self.start_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 70px;
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
                padding: 6px 10px;
                font-size: 11px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_analysis_btn.clicked.connect(self._on_skip_analysis)
        control_layout.addWidget(self.skip_analysis_btn)
        
        # 状态显示（内联）
        self.analysis_status_label = qt.QLabel("等待开始")
        self.analysis_status_label.setStyleSheet("font-size: 10px; color: #868e96; font-style: italic;")
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
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        status_layout = qt.QVBoxLayout(status_frame)
        status_layout.setSpacing(8)
        
        # 标题
        status_title = qt.QLabel("1. HALT状态")
        status_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #343a40; margin-bottom: 5px;")
        status_layout.addWidget(status_title)
        
        # 选项按钮 - 紧凑布局
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(8)
        
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
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px 16px;
                    margin: 2px;
                    background-color: {bg_color};
                    border: 2px solid {bg_color};
                    border-radius: 6px;
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
    
    def _create_phase_section(self, parent_layout):
        """创建测量期相选择区域"""
        self.phase_frame = qt.QFrame()
        self.phase_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #b8daff;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        phase_layout = qt.QVBoxLayout(self.phase_frame)
        phase_layout.setSpacing(6)
        
        # 标题
        phase_title = qt.QLabel("2. 测量期相")
        phase_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        phase_layout.addWidget(phase_title)
        
        # 期相选择 - 紧凑布局
        phase_buttons_layout = qt.QHBoxLayout()
        phase_buttons_layout.setSpacing(8)
        
        self.phase_group = qt.QButtonGroup()
        
        self.phase_buttons = {}
        for i, phase in enumerate(["舒张末期", "收缩末期"]):
            button = qt.QRadioButton(phase)
            button.setStyleSheet("""
                QRadioButton {
                    font-size: 12px;
                    font-weight: 500;
                    padding: 6px 12px;
                    margin: 2px;
                    background-color: white;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                }
                QRadioButton:checked {
                    border: 2px solid #007bff;
                    background-color: #e3f2fd;
                    font-weight: bold;
                }
                QRadioButton:hover {
                    border: 1px solid #007bff;
                }
            """)
            
            self.phase_group.addButton(button, i)
            self.phase_buttons[phase] = button
            phase_buttons_layout.addWidget(button)
        
        # 默认选择舒张末期
        self.phase_buttons["舒张末期"].setChecked(True)
        
        # 连接信号
        self.phase_group.buttonClicked.connect(self._on_phase_changed)
        
        phase_buttons_layout.addStretch()
        phase_layout.addLayout(phase_buttons_layout)
        
        parent_layout.addWidget(self.phase_frame)
    
    def _create_grading_section(self, parent_layout):
        """创建瓣叶分级区域"""
        self.grading_frame = qt.QFrame()
        self.grading_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #007bff;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        grading_layout = qt.QVBoxLayout(self.grading_frame)
        grading_layout.setSpacing(8)
        
        # 标题和快速操作
        header_layout = qt.QHBoxLayout()
        header_layout.setSpacing(8)
        
        grading_title = qt.QLabel("3. HALT分级")
        grading_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #343a40;")
        header_layout.addWidget(grading_title)
        
        header_layout.addStretch()
        
        # 快速设置提示和按钮 - 更紧凑
        quick_label = qt.QLabel("快速设置:")
        quick_label.setStyleSheet("font-size: 10px; color: #6c757d; margin-right: 3px;")
        header_layout.addWidget(quick_label)
        
        quick_grades = ["0", "≤25%", "25-50%", "50%-75%", ">75%"]
        for grade in quick_grades:
            quick_btn = qt.QPushButton(grade)
            quick_btn.setStyleSheet("""
                QPushButton {
                    font-size: 9px;
                    padding: 2px 6px;
                    margin: 0px 1px;
                    border: 1px solid #ced4da;
                    border-radius: 3px;
                    background-color: #f8f9fa;
                    min-width: 35px;
                    max-width: 35px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #007bff;
                }
            """)
            quick_btn.clicked.connect(lambda checked, g=grade: self._set_all_grades(g))
            header_layout.addWidget(quick_btn)
        
        grading_layout.addLayout(header_layout)
        
        # 分级表格 - 更紧凑的布局
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
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        
        summary_layout = qt.QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(8, 4, 8, 4)
        summary_layout.setSpacing(16)
        
        # 受累瓣叶个数
        self.affected_count_label = qt.QLabel("受累瓣叶: 0个")
        self.affected_count_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #28a745;")
        summary_layout.addWidget(self.affected_count_label)
        
        summary_layout.addStretch()
        
        # 最高分级
        self.max_grade_label = qt.QLabel("最高分级: 0")
        self.max_grade_label.setStyleSheet("font-size: 12px; color: #495057; font-weight: 500;")
        summary_layout.addWidget(self.max_grade_label)
        
        parent_layout.addWidget(self.summary_frame)
    
    def _create_view_marking_section(self, parent_layout):
        """创建视图标记与管理区域（简化版）"""
        self.view_frame = qt.QFrame()
        self.view_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fff8;
                border: 1px solid #c3e6cb;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        view_layout = qt.QVBoxLayout(self.view_frame)
        view_layout.setSpacing(8)
        
        # 标题和操作区域 - 紧凑布局
        header_layout = qt.QHBoxLayout()
        header_layout.setSpacing(8)
        
        view_title = qt.QLabel("关键视图")
        view_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(view_title)
        
        header_layout.addStretch()
        
        # 标记当前视图按钮 - 更紧凑
        self.mark_btn = qt.QPushButton("📌 标记 (Ctrl+M)")
        self.mark_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 10px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.mark_btn.clicked.connect(self._show_mark_view_dialog)
        
        # 添加快捷键
        mark_shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+M"), self)
        mark_shortcut.activated.connect(self._show_mark_view_dialog)
        
        header_layout.addWidget(self.mark_btn)
        
        view_layout.addLayout(header_layout)
        
        # 已标记视图列表 - 紧凑版本
        self._create_marked_views_list(view_layout)
        
        parent_layout.addWidget(self.view_frame)
    
    def _create_marked_views_list(self, parent_layout):
        """创建已标记视图列表"""
        # 列表标题 - 紧凑版
        list_header = qt.QHBoxLayout()
        list_header.setSpacing(8)
        
        list_title = qt.QLabel("已标记:")
        list_title.setStyleSheet("font-size: 12px; font-weight: 500; color: #495057;")
        list_header.addWidget(list_title)
        
        list_header.addStretch()
        
        # 清除所有按钮 - 更小
        self.clear_all_btn = qt.QPushButton("🗑️ 清除")
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                padding: 2px 6px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.clear_all_btn.clicked.connect(self._clear_all_views)
        self.clear_all_btn.setVisible(False)  # 初始隐藏
        list_header.addWidget(self.clear_all_btn)
        
        parent_layout.addLayout(list_header)
        
        # 滚动区域用于视图列表 - 更紧凑
        scroll_area = qt.QScrollArea()
        scroll_area.setMaximumHeight(80)  # 减小高度
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
        self.views_layout.setSpacing(2)  # 减小间距
        self.views_layout.setContentsMargins(0, 0, 0, 0)
        
        # 空状态提示 - 更小
        self.empty_hint = qt.QLabel("暂无标记")
        self.empty_hint.setAlignment(qt.Qt.AlignCenter)
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
    
    def _create_action_buttons_section(self, parent_layout):
        """创建操作按钮区域"""
        actions_layout = qt.QHBoxLayout()
        actions_layout.setSpacing(8)
        actions_layout.setContentsMargins(4, 8, 4, 4)
        
        # 重置按钮 - 更紧凑
        reset_btn = qt.QPushButton("重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                min-width: 60px;
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
                padding: 8px 16px;
                font-size: 12px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                min-width: 80px;
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
    
    def _on_overall_status_changed(self, button):
        """整体HALT状态改变时的回调"""
        self.overall_halt_status = button.text
        self._update_visibility()
        self._update_summary()
        self._emit_status_changed()
        
        logging.info(f"整体HALT状态更新为: {self.overall_halt_status}")
    
    def _on_phase_changed(self, button):
        """测量期相改变时的回调"""
        self.measurement_phase = button.text
        self._emit_status_changed()
        
        logging.info(f"测量期相更新为: {self.measurement_phase}")
    
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
    
    def _on_leaflet_grade_changed(self, leaflet_name: str, grade: str):
        """瓣叶分级改变时的回调"""
        self.leaflet_grades[leaflet_name] = grade
        self._update_summary()
        self._emit_status_changed()
        
        logging.info(f"瓣叶 {leaflet_name} 分级更新为: {grade}")
    
    def _set_all_grades(self, grade: str):
        """快速设置所有瓣叶为同一分级"""
        for leaflet_name, row in self.leaflet_grade_rows.items():
            row.set_grade(grade)
            self.leaflet_grades[leaflet_name] = grade
        
        self._update_summary()
        self._emit_status_changed()
        
        logging.info(f"所有瓣叶分级设置为: {grade}")
    
    def _update_visibility(self):
        """根据整体HALT状态更新界面可见性"""
        has_halt = self.overall_halt_status == "有"
        
        self.phase_frame.setVisible(has_halt)
        self.grading_frame.setVisible(has_halt)
        self.summary_frame.setVisible(has_halt)
        
        if not has_halt:
            # 重置所有瓣叶分级为0
            for leaflet_name, row in self.leaflet_grade_rows.items():
                row.set_grade("0")
                self.leaflet_grades[leaflet_name] = "0"
            self._update_summary()
    
    def _update_analysis_control_visibility(self):
        """根据分析状态更新分析控制区域的可见性"""
        # 如果分析已经开始，隐藏控制区域
        if hasattr(self, 'control_frame'):
            self.control_frame.setVisible(not self.analysis_started)
    
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
    
    def _show_mark_view_dialog(self):
        """显示标记视图对话框"""
        dialog = qt.QDialog(self)
        dialog.setWindowTitle("标记当前视图")
        dialog.setModal(True)
        dialog.resize(350, 150)
        
        layout = qt.QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # 说明文本
        info_label = qt.QLabel("为当前MPR视图位置添加一个有意义的标记名称：")
        info_label.setStyleSheet("font-size: 13px; color: #495057;")
        layout.addWidget(info_label)
        
        # 输入框
        name_input = qt.QLineEdit()
        name_input.setPlaceholderText("例如：支架底部平面、瓣叶最佳显示...")
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
        
        # 生成默认名称
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        default_name = f"HALT视图_{timestamp}"
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
            view_name = name_input.text.strip()
            if not view_name:
                qt.QMessageBox.warning(dialog, "警告", "请输入视图名称！")
                return
            
            success = self.view_marking_manager.mark_current_view(view_name)
            if success:
                self._refresh_marked_views_list()
                dialog.accept()
                
                # 显示成功提示
                qt.QMessageBox.information(
                    self,
                    "标记成功",
                    f"视图已标记为：{view_name}"
                )
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
    
    def _refresh_marked_views_list(self):
        """刷新已标记视图列表"""
        # 清除现有的视图项
        for i in reversed(range(self.views_layout.count())):
            child = self.views_layout.itemAt(i).widget()
            if child and child != self.empty_hint:
                child.setParent(None)
        
        marked_views = self.view_marking_manager.get_marked_views()
        
        if not marked_views:
            # 显示空状态
            self.empty_hint.setVisible(True)
            self.clear_all_btn.setVisible(False)
        else:
            # 隐藏空状态提示
            self.empty_hint.setVisible(False)
            self.clear_all_btn.setVisible(True)
            
            # 为每个标记的视图创建条目
            for view_name, description in marked_views.items():
                view_item = self._create_view_item(view_name, description)
                # 插入到stretch之前
                self.views_layout.insertWidget(self.views_layout.count() - 1, view_item)
    
    def _create_view_item(self, view_name: str, description: str):
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
        item_layout.setSpacing(6)
        
        # 视图图标 - 更小
        icon_label = qt.QLabel("👁️")
        icon_label.setStyleSheet("font-size: 12px;")
        item_layout.addWidget(icon_label)
        
        # 视图信息 - 紧凑显示
        name_label = qt.QLabel(view_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #212529;
            }
        """)
        item_layout.addWidget(name_label)
        item_layout.addStretch()
        
        # 操作按钮 - 更小
        # 恢复按钮
        restore_btn = qt.QPushButton("🔄")
        restore_btn.setToolTip(f"恢复到视图: {view_name}")
        restore_btn.setStyleSheet("""
            QPushButton {
                padding: 2px 4px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 9px;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        restore_btn.clicked.connect(lambda: self._restore_view(view_name))
        item_layout.addWidget(restore_btn)
        
        # 删除按钮
        delete_btn = qt.QPushButton("🗑️")
        delete_btn.setToolTip("删除此视图标记")
        delete_btn.setStyleSheet("""
            QPushButton {
                padding: 2px 4px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 9px;
                min-width: 20px;
                max-width: 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_view(view_name))
        item_layout.addWidget(delete_btn)
        
        return item_frame
    
    def _restore_view(self, view_name: str):
        """恢复指定视图 - 参考快速定位功能的稳定性"""
        try:
            # 先检查视图数据是否存在
            if view_name not in self.view_marking_manager.marked_views:
                qt.QMessageBox.warning(
                    self,
                    "视图不存在",
                    f"视图标记 '{view_name}' 已不存在，可能已被删除。"
                )
                self._refresh_marked_views_list()  # 刷新列表
                return
            
            # 提供视觉反馈
            self.mark_btn.setText("🔄 正在恢复...")
            self.mark_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 调用视图管理器恢复视图
            success = self.view_marking_manager.restore_view(view_name)
            
            if success:
                # 成功恢复后稍作延迟，让用户看到变化
                qt.QTimer.singleShot(500, self._on_view_restore_success)
                logging.info(f"成功恢复视图: {view_name}")
                
                # 可选：刷新视图以确保显示正确
                self._refresh_3d_view()
                
            else:
                self._on_view_restore_failed(view_name)
                
        except Exception as e:
            logging.error(f"恢复视图失败: {e}")
            self._on_view_restore_error(str(e))
    
    def _on_view_restore_success(self):
        """视图恢复成功的回调"""
        self.mark_btn.setText("✅ 视图已恢复")
        self.mark_btn.setEnabled(True)
        # 2秒后恢复原始文本
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText("📌 标记当前视图"))
    
    def _on_view_restore_failed(self, view_name: str):
        """视图恢复失败的回调"""
        self.mark_btn.setText("❌ 恢复失败")
        self.mark_btn.setEnabled(True)
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText("📌 标记当前视图"))
        
        qt.QMessageBox.warning(
            self,
            "恢复失败",
            f"无法恢复视图 '{view_name}'。\n\n"
            "可能的原因：\n"
            "• 视图数据已损坏\n"
            "• MPR系统状态异常\n"
            "• 几何参数超出有效范围"
        )
    
    def _on_view_restore_error(self, error_msg: str):
        """视图恢复异常的回调"""
        self.mark_btn.setText("❌ 恢复失败")
        self.mark_btn.setEnabled(True)
        qt.QTimer.singleShot(2000, lambda: self.mark_btn.setText("📌 标记当前视图"))
        
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
            success = self.view_marking_manager.clear_view_mark(view_name)
            if success:
                self._refresh_marked_views_list()
                logging.info(f"已删除视图标记: {view_name}")
    
    def _clear_all_views(self):
        """清除所有视图标记"""
        reply = qt.QMessageBox.question(
            self,
            "确认清除",
            "确定要清除所有视图标记吗？\n\n此操作无法撤销。",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self.view_marking_manager.marked_views.clear()
            self._refresh_marked_views_list()
            logging.info("已清除所有视图标记")
    
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
            
            # 重置期相
            self.phase_buttons["舒张末期"].setChecked(True)
            self.measurement_phase = "舒张末期"
            
            # 重置所有瓣叶分级
            for leaflet_name, row in self.leaflet_grade_rows.items():
                row.set_grade("0")
                self.leaflet_grades[leaflet_name] = "0"
            
            # 清除视图标记
            self.view_marking_manager.marked_views.clear()
            
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
            report.append(f"测量期相：{results['measurement_phase']}")
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
        
        # 视图标记
        marked_views = results.get('marked_views', {})
        if marked_views:
            report.append("")
            report.append(f"关键视图标记：{len(marked_views)}个")
            for view_name in marked_views.keys():
                report.append(f"  - {view_name}")
        
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
        
        return {
            'analysis_type': 'HALT',
            'overall_status': self.overall_halt_status,
            'measurement_phase': self.measurement_phase if self.overall_halt_status == "有" else None,
            'leaflet_grades': dict(self.leaflet_grades),
            'affected_leaflets_count': affected_count,
            'max_grade': max_grade,
            'marked_views': self.view_marking_manager.marked_views,
            'analysis_timestamp': qt.QDateTime.currentDateTime().toString(),
            'session_info': {
                'study_name': getattr(self.session, 'study_name', 'Unknown'),
                'patient_id': getattr(self.session, 'patient_id', 'Unknown')
            }
        }
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        # 同步更新phase_widget的session
        if hasattr(self, 'phase_widget'):
            self.phase_widget.set_session(session)
    
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
        
        logging.info("HALT分析界面清理资源")
