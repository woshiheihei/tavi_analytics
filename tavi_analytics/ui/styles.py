"""
统一样式系统 - TAVR Analytics UI样式定义

提供应用程序的统一样式、主题和设计规范。
所有UI组件都应使用此模块中定义的样式。

作者：TAVR Research Team
创建时间：2024
"""

from typing import Dict, Any, Optional
from enum import Enum


class ThemeColor(Enum):
    """主题颜色定义"""
    # 主色调（灰色系，简洁专业）
    PRIMARY = "#666"
    PRIMARY_HOVER = "#555"
    PRIMARY_PRESSED = "#444"
    PRIMARY_DISABLED = "#ddd"
    
    # 背景色
    BACKGROUND_LIGHT = "#f5f5f5"
    BACKGROUND_NORMAL = "#f9f9f9"
    BACKGROUND_WHITE = "#ffffff"
    
    # 边框色
    BORDER_LIGHT = "#ddd"
    BORDER_NORMAL = "#ccc"
    BORDER_DARK = "#999"
    
    # 文字色
    TEXT_PRIMARY = "#333"
    TEXT_SECONDARY = "#666"
    TEXT_DISABLED = "#999"
    TEXT_WHITE = "#ffffff"
    
    # 状态色
    SUCCESS = "#27ae60"
    WARNING = "#f39c12"
    ERROR = "#e74c3c"
    INFO = "#3498db"


class FontSize(Enum):
    """字体大小定义"""
    SMALL = "10px"
    NORMAL = "12px"
    MEDIUM = "14px"
    LARGE = "16px"
    TITLE = "18px"
    HEADING = "24px"


class Spacing(Enum):
    """间距定义"""
    XS = "4px"
    SM = "6px"
    MD = "8px"
    LG = "10px"
    XL = "12px"
    XXL = "16px"


class BorderRadius(Enum):
    """圆角定义"""
    SMALL = "3px"
    NORMAL = "4px"
    LARGE = "6px"
    ROUND = "50%"


class StyleManager:
    """样式管理器 - 提供统一的样式生成和管理功能"""
    
    @staticmethod
    def get_button_style(button_type: str = "primary", size: str = "normal") -> str:
        """获取按钮样式
        
        Args:
            button_type: 按钮类型 ("primary", "secondary", "success", "warning", "danger")
            size: 按钮大小 ("small", "normal", "large")
            
        Returns:
            CSS样式字符串
        """
        # 尺寸配置
        size_config = {
            "small": {
                "padding": f"{Spacing.SM.value} {Spacing.MD.value}",
                "font_size": FontSize.SMALL.value,
                "min_height": "28px"
            },
            "normal": {
                "padding": f"{Spacing.MD.value} {Spacing.XL.value}",
                "font_size": FontSize.NORMAL.value,
                "min_height": "35px"
            },
            "large": {
                "padding": f"{Spacing.LG.value} {Spacing.XXL.value}",
                "font_size": FontSize.MEDIUM.value,
                "min_height": "40px"
            }
        }
        
        # 类型配置
        type_config = {
            "primary": {
                "bg_color": ThemeColor.PRIMARY.value,
                "hover_color": ThemeColor.PRIMARY_HOVER.value,
                "pressed_color": ThemeColor.PRIMARY_PRESSED.value,
                "disabled_color": ThemeColor.PRIMARY_DISABLED.value,
                "text_color": ThemeColor.TEXT_WHITE.value,
                "disabled_text": ThemeColor.TEXT_DISABLED.value
            },
            "secondary": {
                "bg_color": ThemeColor.BACKGROUND_LIGHT.value,
                "hover_color": "#e9e9e9",
                "pressed_color": "#e0e0e0",
                "disabled_color": ThemeColor.PRIMARY_DISABLED.value,
                "text_color": ThemeColor.TEXT_PRIMARY.value,
                "disabled_text": ThemeColor.TEXT_DISABLED.value
            },
            "success": {
                "bg_color": ThemeColor.SUCCESS.value,
                "hover_color": "#229954",
                "pressed_color": "#1e8449",
                "disabled_color": ThemeColor.PRIMARY_DISABLED.value,
                "text_color": ThemeColor.TEXT_WHITE.value,
                "disabled_text": ThemeColor.TEXT_DISABLED.value
            },
            "warning": {
                "bg_color": ThemeColor.WARNING.value,
                "hover_color": "#e67e22",
                "pressed_color": "#d35400",
                "disabled_color": ThemeColor.PRIMARY_DISABLED.value,
                "text_color": ThemeColor.TEXT_WHITE.value,
                "disabled_text": ThemeColor.TEXT_DISABLED.value
            },
            "danger": {
                "bg_color": ThemeColor.ERROR.value,
                "hover_color": "#c0392b",
                "pressed_color": "#a93226",
                "disabled_color": ThemeColor.PRIMARY_DISABLED.value,
                "text_color": ThemeColor.TEXT_WHITE.value,
                "disabled_text": ThemeColor.TEXT_DISABLED.value
            }
        }
        
        size_cfg = size_config.get(size, size_config["normal"])
        type_cfg = type_config.get(button_type, type_config["primary"])
        
        return f"""
            QPushButton {{
                background-color: {type_cfg["bg_color"]};
                color: {type_cfg["text_color"]};
                border: none;
                border-radius: {BorderRadius.NORMAL.value};
                padding: {size_cfg["padding"]};
                font-size: {size_cfg["font_size"]};
                font-weight: bold;
                min-height: {size_cfg["min_height"]};
            }}
            QPushButton:hover {{
                background-color: {type_cfg["hover_color"]};
            }}
            QPushButton:pressed {{
                background-color: {type_cfg["pressed_color"]};
            }}
            QPushButton:disabled {{
                background-color: {type_cfg["disabled_color"]};
                color: {type_cfg["disabled_text"]};
            }}
        """
    
    @staticmethod
    def get_label_style(label_type: str = "normal") -> str:
        """获取标签样式
        
        Args:
            label_type: 标签类型 ("normal", "title", "subtitle", "info", "primary", "secondary")
            
        Returns:
            CSS样式字符串
        """
        styles = {
            "normal": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_PRIMARY.value};
                    font-size: {FontSize.NORMAL.value};
                    padding: {Spacing.XS.value};
                }}
            """,
            "title": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_PRIMARY.value};
                    font-size: {FontSize.HEADING.value};
                    font-weight: bold;
                    padding: {Spacing.MD.value};
                }}
            """,
            "subtitle": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_PRIMARY.value};
                    font-size: {FontSize.LARGE.value};
                    font-weight: bold;
                    padding: {Spacing.SM.value};
                }}
            """,
            "info": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_SECONDARY.value};
                    font-size: {FontSize.SMALL.value};
                    padding: {Spacing.XS.value};
                }}
            """,
            "primary": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_PRIMARY.value};
                    font-size: {FontSize.LARGE.value};
                    font-weight: bold;
                    padding: {Spacing.LG.value};
                    background-color: {ThemeColor.BACKGROUND_LIGHT.value};
                    border: 1px solid {ThemeColor.BORDER_LIGHT.value};
                    border-radius: {BorderRadius.NORMAL.value};
                }}
            """,
            "secondary": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_SECONDARY.value};
                    font-size: {FontSize.NORMAL.value};
                    padding: {Spacing.MD.value};
                    background-color: {ThemeColor.BACKGROUND_NORMAL.value};
                    border: 1px solid {ThemeColor.BORDER_LIGHT.value};
                    border-radius: {BorderRadius.NORMAL.value};
                }}
            """
        }
        
        return styles.get(label_type, styles["normal"])
    
    @staticmethod
    def get_status_indicator_style(status_type: str = "normal") -> str:
        """获取状态指示器样式
        
        Args:
            status_type: 状态类型 ("normal", "success", "warning", "error")
            
        Returns:
            CSS样式字符串
        """
        color_map = {
            "normal": ThemeColor.INFO.value,
            "success": ThemeColor.SUCCESS.value,
            "warning": ThemeColor.WARNING.value,
            "error": ThemeColor.ERROR.value
        }
        
        bg_color = color_map.get(status_type, ThemeColor.INFO.value)
        
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: {ThemeColor.TEXT_WHITE.value};
                padding: {Spacing.XS.value} {Spacing.MD.value};
                border-radius: {BorderRadius.SMALL.value};
                font-weight: bold;
                font-size: {FontSize.NORMAL.value};
            }}
        """
    
    @staticmethod
    def get_slider_style() -> str:
        """获取滑块样式
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QSlider::groove:horizontal {{
                border: 1px solid {ThemeColor.BORDER_NORMAL.value};
                background: {ThemeColor.BACKGROUND_LIGHT.value};
                height: 8px;
                border-radius: {BorderRadius.NORMAL.value};
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColor.PRIMARY.value};
                border: 1px solid {ThemeColor.PRIMARY_HOVER.value};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {ThemeColor.PRIMARY_HOVER.value};
            }}
            QSlider::handle:horizontal:pressed {{
                background: {ThemeColor.PRIMARY_PRESSED.value};
            }}
        """
    
    @staticmethod
    def get_input_style() -> str:
        """获取输入框样式
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QLineEdit {{
                padding: {Spacing.MD.value};
                border: 1px solid {ThemeColor.BORDER_LIGHT.value};
                border-radius: {BorderRadius.NORMAL.value};
                background-color: {ThemeColor.BACKGROUND_WHITE.value};
                font-size: {FontSize.NORMAL.value};
            }}
            QLineEdit:focus {{
                border: 2px solid {ThemeColor.PRIMARY.value};
            }}
            QTextEdit {{
                padding: {Spacing.MD.value};
                border: 1px solid {ThemeColor.BORDER_LIGHT.value};
                border-radius: {BorderRadius.NORMAL.value};
                background-color: {ThemeColor.BACKGROUND_WHITE.value};
                font-size: {FontSize.NORMAL.value};
            }}
            QTextEdit:focus {{
                border: 2px solid {ThemeColor.PRIMARY.value};
            }}
        """
    
    @staticmethod
    def get_group_box_style() -> str:
        """获取分组框样式
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QGroupBox {{
                font-size: {FontSize.MEDIUM.value};
                font-weight: bold;
                color: {ThemeColor.TEXT_PRIMARY.value};
                padding-top: {Spacing.XXL.value};
                margin-top: {Spacing.SM.value};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {Spacing.LG.value};
                padding: 0 {Spacing.SM.value} 0 {Spacing.SM.value};
            }}
        """
    
    @staticmethod
    def get_separator_style() -> str:
        """获取分隔符样式
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QFrame[frameShape="4"] {{
                color: {ThemeColor.BORDER_LIGHT.value};
            }}
            QFrame[frameShape="5"] {{
                color: {ThemeColor.BORDER_LIGHT.value};
            }}
        """


class ComponentStyleFactory:
    """组件样式工厂 - 为特定组件提供预设样式组合"""
    
    @staticmethod
    def get_cardiac_cycle_styles() -> Dict[str, str]:
        """获取心动周期组件样式集合"""
        return {
            "phase_percent_label": StyleManager.get_label_style("primary"),
            "frame_info_label": StyleManager.get_label_style("secondary"),
            "series_description_label": StyleManager.get_label_style("info"),
            "control_button": StyleManager.get_button_style("primary", "small"),
            "mark_button": StyleManager.get_button_style("primary", "normal"),
            "marked_phase_label": StyleManager.get_label_style("secondary"),
            "slider": StyleManager.get_slider_style(),
            "range_label": StyleManager.get_label_style("info")
        }
    
    @staticmethod
    def get_main_ui_styles() -> Dict[str, str]:
        """获取主界面组件样式集合"""
        return {
            "app_label": f"""
                QLabel {{
                    font-size: {FontSize.MEDIUM.value};
                    font-weight: bold;
                    color: {ThemeColor.TEXT_PRIMARY.value};
                }}
            """,
            "status_indicator": StyleManager.get_status_indicator_style(),
            "nav_hint": f"""
                QLabel {{
                    color: {ThemeColor.TEXT_SECONDARY.value};
                    font-size: {FontSize.NORMAL.value};
                }}
            """,
            "welcome_label": StyleManager.get_label_style("title"),
            "description_label": f"""
                QLabel {{
                    font-size: {FontSize.MEDIUM.value};
                    color: {ThemeColor.TEXT_SECONDARY.value};
                    margin-top: {Spacing.LG.value};
                }}
            """,
            "module_button": StyleManager.get_button_style("primary", "normal")
        }
    
    @staticmethod
    def apply_styles_to_widget(widget, style_name: str, style_dict: Dict[str, str]):
        """应用样式到控件
        
        Args:
            widget: 要应用样式的控件
            style_name: 样式名称
            style_dict: 样式字典
        """
        if style_name in style_dict:
            widget.setStyleSheet(style_dict[style_name])


# 导出主要类和函数
__all__ = [
    'ThemeColor',
    'FontSize', 
    'Spacing',
    'BorderRadius',
    'StyleManager',
    'ComponentStyleFactory'
]
