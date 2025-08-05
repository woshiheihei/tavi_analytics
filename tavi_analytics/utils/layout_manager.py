"""
布局管理器工具类

该模块提供统一的UI布局管理功能，包括：
- 标准化的大小策略设置
- 统一的间距和边距管理
- 响应式布局支持
- 组件层级管理

作者：TAVR Research Team
创建时间：2024
"""

import qt
from typing import Optional, Tuple, Dict, Any
from enum import Enum


class LayoutType(Enum):
    """布局类型枚举"""
    MAIN_CONTAINER = "main_container"      # 主容器
    MODULE_CONTAINER = "module_container"   # 模块容器
    SECTION_CONTAINER = "section_container" # 区域容器
    BUTTON_GROUP = "button_group"          # 按钮组
    INFO_DISPLAY = "info_display"          # 信息显示
    CONTROL_PANEL = "control_panel"        # 控制面板


class SizePolicy(Enum):
    """大小策略枚举"""
    FIXED = "fixed"                        # 固定大小
    EXPANDING = "expanding"                # 可扩展
    PREFERRED = "preferred"                # 首选大小
    MINIMUM_EXPANDING = "minimum_expanding" # 最小可扩展


class LayoutManager:
    """布局管理器
    
    提供统一的UI布局管理功能
    """
    
    # 标准间距配置
    SPACING_CONFIG = {
        LayoutType.MAIN_CONTAINER: 12,
        LayoutType.MODULE_CONTAINER: 10,
        LayoutType.SECTION_CONTAINER: 8,
        LayoutType.BUTTON_GROUP: 6,
        LayoutType.INFO_DISPLAY: 4,
        LayoutType.CONTROL_PANEL: 8,
    }
    
    # 标准边距配置 (top, right, bottom, left)
    MARGINS_CONFIG = {
        LayoutType.MAIN_CONTAINER: (10, 10, 10, 10),
        LayoutType.MODULE_CONTAINER: (8, 8, 8, 8),
        LayoutType.SECTION_CONTAINER: (6, 6, 6, 6),
        LayoutType.BUTTON_GROUP: (4, 4, 4, 4),
        LayoutType.INFO_DISPLAY: (6, 8, 6, 8),
        LayoutType.CONTROL_PANEL: (8, 8, 8, 8),
    }
    
    # 标准最小高度配置
    MIN_HEIGHT_CONFIG = {
        LayoutType.MAIN_CONTAINER: 600,
        LayoutType.MODULE_CONTAINER: 500,
        LayoutType.SECTION_CONTAINER: None,  # 由内容决定
        LayoutType.BUTTON_GROUP: 50,
        LayoutType.INFO_DISPLAY: 80,
        LayoutType.CONTROL_PANEL: 200,
    }
    
    @staticmethod
    def create_layout(layout_type: LayoutType, parent_widget: qt.QWidget) -> qt.QVBoxLayout:
        """创建标准化布局
        
        Args:
            layout_type: 布局类型
            parent_widget: 父组件
            
        Returns:
            配置好的布局对象
        """
        layout = qt.QVBoxLayout(parent_widget)
        
        # 设置间距
        spacing = LayoutManager.SPACING_CONFIG.get(layout_type, 8)
        layout.setSpacing(spacing)
        
        # 设置边距
        margins = LayoutManager.MARGINS_CONFIG.get(layout_type, (8, 8, 8, 8))
        layout.setContentsMargins(*margins)
        
        return layout
    
    @staticmethod
    def create_horizontal_layout(layout_type: LayoutType, parent_widget: Optional[qt.QWidget] = None) -> qt.QHBoxLayout:
        """创建水平布局
        
        Args:
            layout_type: 布局类型
            parent_widget: 父组件（可选）
            
        Returns:
            配置好的水平布局对象
        """
        if parent_widget:
            layout = qt.QHBoxLayout(parent_widget)
        else:
            layout = qt.QHBoxLayout()
        
        # 设置间距
        spacing = LayoutManager.SPACING_CONFIG.get(layout_type, 8)
        layout.setSpacing(spacing)
        
        # 设置边距
        margins = LayoutManager.MARGINS_CONFIG.get(layout_type, (8, 8, 8, 8))
        layout.setContentsMargins(*margins)
        
        return layout
    
    @staticmethod
    def setup_widget_size_policy(widget: qt.QWidget, layout_type: LayoutType, 
                                size_policy: SizePolicy = SizePolicy.PREFERRED):
        """设置组件大小策略
        
        Args:
            widget: 要设置的组件
            layout_type: 布局类型
            size_policy: 大小策略
        """
        # 设置Qt大小策略
        if size_policy == SizePolicy.FIXED:
            qt_policy = qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Fixed)
        elif size_policy == SizePolicy.EXPANDING:
            qt_policy = qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        elif size_policy == SizePolicy.MINIMUM_EXPANDING:
            qt_policy = qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        else:  # PREFERRED
            qt_policy = qt.QSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
        
        widget.setSizePolicy(qt_policy)
        
        # 设置最小高度
        min_height = LayoutManager.MIN_HEIGHT_CONFIG.get(layout_type)
        if min_height:
            widget.setMinimumHeight(min_height)
    
    @staticmethod
    def create_section_frame(title: str, layout_type: LayoutType = LayoutType.SECTION_CONTAINER) -> qt.QGroupBox:
        """创建标准化区域框架
        
        Args:
            title: 区域标题
            layout_type: 布局类型
            
        Returns:
            配置好的GroupBox
        """
        frame = qt.QGroupBox(title)
        
        # 设置基本样式
        frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        
        # 设置大小策略
        LayoutManager.setup_widget_size_policy(frame, layout_type, SizePolicy.PREFERRED)
        
        return frame
    
    @staticmethod
    def create_button_with_style(text: str, button_type: str = "primary") -> qt.QPushButton:
        """创建标准化按钮
        
        Args:
            text: 按钮文本
            button_type: 按钮类型 ("primary", "secondary", "success", "warning", "danger")
            
        Returns:
            配置好的按钮
        """
        button = qt.QPushButton(text)
        
        # 按钮样式配置
        styles = {
            "primary": {
                "bg_color": "#3498db",
                "hover_color": "#2980b9",
                "text_color": "white"
            },
            "secondary": {
                "bg_color": "#95a5a6",
                "hover_color": "#7f8c8d",
                "text_color": "white"
            },
            "success": {
                "bg_color": "#27ae60",
                "hover_color": "#229954",
                "text_color": "white"
            },
            "warning": {
                "bg_color": "#f39c12",
                "hover_color": "#e67e22",
                "text_color": "white"
            },
            "danger": {
                "bg_color": "#e74c3c",
                "hover_color": "#c0392b",
                "text_color": "white"
            }
        }
        
        style_config = styles.get(button_type, styles["primary"])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {style_config["bg_color"]};
                color: {style_config["text_color"]};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 30px;
            }}
            QPushButton:hover:enabled {{
                background-color: {style_config["hover_color"]};
            }}
            QPushButton:pressed:enabled {{
                background-color: {style_config["hover_color"]};
                border: 1px solid rgba(0,0,0,0.2);
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """)
        
        return button
    
    @staticmethod
    def add_stretch_with_ratio(layout: qt.QLayout, stretch_ratio: int = 1):
        """添加弹性空间
        
        Args:
            layout: 布局对象
            stretch_ratio: 弹性比例
        """
        if isinstance(layout, qt.QVBoxLayout) or isinstance(layout, qt.QHBoxLayout):
            layout.addStretch(stretch_ratio)
    
    @staticmethod
    def set_layout_alignment(layout: qt.QLayout, alignment: qt.Qt.Alignment):
        """设置布局对齐方式
        
        Args:
            layout: 布局对象
            alignment: 对齐方式
        """
        layout.setAlignment(alignment)
    
    @staticmethod
    def create_scrollable_container(layout_type: LayoutType = LayoutType.MODULE_CONTAINER) -> Tuple[qt.QScrollArea, qt.QWidget]:
        """创建可滚动容器
        
        Args:
            layout_type: 布局类型
            
        Returns:
            (滚动区域, 内容组件)
        """
        scroll_area = qt.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        
        # 创建内容组件
        content_widget = qt.QWidget()
        
        # 设置大小策略
        LayoutManager.setup_widget_size_policy(content_widget, layout_type, SizePolicy.EXPANDING)
        
        # 设置滚动区域样式
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #999999;
            }
        """)
        
        scroll_area.setWidget(content_widget)
        
        return scroll_area, content_widget
    
    @staticmethod
    def apply_responsive_layout(widget: qt.QWidget, min_width: int = 800, min_height: int = 600):
        """应用响应式布局
        
        Args:
            widget: 要应用的组件
            min_width: 最小宽度
            min_height: 最小高度
        """
        widget.setMinimumSize(min_width, min_height)
        widget.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
