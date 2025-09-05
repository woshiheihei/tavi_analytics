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
    """主题颜色定义 - 基于 shadcn/ui 配色方案"""
    
    # === 基础色彩系统 (shadcn/ui 风格) ===
    
    # 中性色 (Neutral/Slate)
    BACKGROUND = "#ffffff"           # 纯白背景
    FOREGROUND = "#0f172a"          # 深色文字 (slate-900)
    
    # 卡片和表面
    CARD = "#ffffff"                # 卡片背景
    CARD_FOREGROUND = "#0f172a"     # 卡片文字
    
    # 弹窗和覆盖层
    POPOVER = "#ffffff"             # 弹窗背景
    POPOVER_FOREGROUND = "#0f172a"  # 弹窗文字
    
    # 主要色彩 (Primary) - 灰色主题
    PRIMARY = "#64748b"             # 主色 (slate-500)  
    PRIMARY_FOREGROUND = "#ffffff"  # 主色文字 (white)

    # 品牌/操作主色（用于工具栏pill按钮激活态，避免影响全局PRIMARY灰主题）
    BRAND_PRIMARY = "#2563eb"       # blue-600
    BRAND_PRIMARY_HOVER = "#1d4ed8" # blue-700
    
    # 次要色彩 (Secondary)
    SECONDARY = "#f1f5f9"           # 次要色 (slate-100)
    SECONDARY_FOREGROUND = "#0f172a" # 次要色文字
    
    # 静音色彩 (Muted)
    MUTED = "#f1f5f9"               # 静音背景 (slate-100)
    MUTED_FOREGROUND = "#64748b"    # 静音文字 (slate-500)
    
    # 强调色彩 (Accent)
    ACCENT = "#f1f5f9"              # 强调背景 (slate-100)
    ACCENT_FOREGROUND = "#0f172a"   # 强调文字
    
    # 破坏性色彩 (Destructive)
    DESTRUCTIVE = "#ef4444"         # 危险色 (red-500)
    DESTRUCTIVE_FOREGROUND = "#fef2f2" # 危险色文字
    
    # 边框
    BORDER = "#e2e8f0"              # 边框色 (slate-200)
    INPUT = "#e2e8f0"               # 输入框边框 (slate-200)
    
    # 圆环/环形
    RING = "#94a3b8"                # 焦点环 (slate-400)
    
    # === 语义化颜色 ===
    
    # 状态色
    SUCCESS = "#22c55e"             # 成功 (green-500)
    SUCCESS_FOREGROUND = "#f0fdf4"  # 成功文字背景
    
    WARNING = "#f59e0b"             # 警告 (amber-500)
    WARNING_FOREGROUND = "#fffbeb"  # 警告文字背景
    
    ERROR = "#ef4444"               # 错误 (red-500)
    ERROR_FOREGROUND = "#fef2f2"    # 错误文字背景
    
    INFO = "#10b981"                # 信息 (emerald-500)
    INFO_FOREGROUND = "#eff6ff"     # 信息文字背景
    
    # === 扩展色彩 ===
    
    # 图表和数据可视化
    CHART_1 = "#10b981"             # 绿色
    CHART_2 = "#10b981"             # 绿色
    CHART_3 = "#f59e0b"             # 琥珀色
    CHART_4 = "#ef4444"             # 红色
    CHART_5 = "#8b5cf6"             # 紫色


class FontSize(Enum):
    """字体大小定义 - 基于 shadcn/ui 字体系统"""
    XS = "0.75rem"      # 12px
    SM = "0.875rem"     # 14px  
    BASE = "1rem"       # 16px
    LG = "1.125rem"     # 18px
    XL = "1.25rem"      # 20px
    XXL = "1.5rem"      # 24px
    XXXL = "1.875rem"   # 30px
    XXXXL = "2.25rem"   # 36px


class FontWeight(Enum):
    """字体粗细定义"""
    NORMAL = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"


class Spacing(Enum):
    """间距定义 - 基于 shadcn/ui 间距系统"""
    XS = "0.25rem"      # 4px
    SM = "0.5rem"       # 8px
    MD = "0.75rem"      # 12px
    LG = "1rem"         # 16px
    XL = "1.25rem"      # 20px
    XXL = "1.5rem"      # 24px
    XXXL = "2rem"       # 32px


class BorderRadius(Enum):
    """圆角定义 - 基于 shadcn/ui 圆角系统"""
    NONE = "0px"
    SM = "2px"          # 小圆角
    DEFAULT = "6px"     # 默认圆角 
    MD = "6px"          # 中等圆角
    LG = "8px"          # 大圆角
    XL = "12px"         # 超大圆角
    XXL = "16px"        # 超超大圆角
    FULL = "9999px"     # 完全圆角


class Shadow(Enum):
    """阴影定义 - 基于 shadcn/ui 阴影系统"""
    SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    DEFAULT = "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)"
    MD = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    LG = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    XL = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"


class StyleManager:
    """样式管理器 - 提供统一的样式生成和管理功能"""
    
    @staticmethod
    def get_button_style(button_type: str = "primary", size: str = "default") -> str:
        """获取按钮样式 - 基于 shadcn/ui 按钮设计
        
        Args:
            button_type: 按钮类型 ("primary", "secondary", "destructive", "outline", "ghost", "link")
            size: 按钮大小 ("sm", "default", "lg", "icon")
            
        Returns:
            CSS样式字符串
        """
        # 尺寸配置（Qt样式表仅支持px等少量单位，且不支持height/width属性，改用min-*）
        size_config = {
            "sm": {"min_h": 28, "pad_x": 10, "pad_y": 4, "font_px": 12},
            "default": {"min_h": 30, "pad_x": 12, "pad_y": 5, "font_px": 12},
            "lg": {"min_h": 36, "pad_x": 16, "pad_y": 8, "font_px": 13},
            "icon": {"min_h": 28, "min_w": 28, "pad_x": 0, "pad_y": 0, "font_px": 12},
        }
        
        # 类型配置
        type_config = {
            "primary": {
                "bg_color": ThemeColor.PRIMARY.value,
                "text_color": ThemeColor.PRIMARY_FOREGROUND.value,
                "hover_bg": "#475569",  # slate-600
                "border": "1px solid transparent",
                "shadow": Shadow.SM.value
            },
            "secondary": {
                "bg_color": ThemeColor.SECONDARY.value,
                "text_color": ThemeColor.SECONDARY_FOREGROUND.value,
                "hover_bg": "#e2e8f0",  # slate-200
                "border": f"1px solid {ThemeColor.BORDER.value}",
                "shadow": Shadow.SM.value
            },
            "destructive": {
                "bg_color": ThemeColor.DESTRUCTIVE.value,
                "text_color": ThemeColor.DESTRUCTIVE_FOREGROUND.value,
                "hover_bg": "#dc2626",  # red-600
                "border": "1px solid transparent",
                "shadow": Shadow.SM.value
            },
            "outline": {
                "bg_color": "transparent",
                "text_color": ThemeColor.FOREGROUND.value,
                "hover_bg": ThemeColor.ACCENT.value,
                "border": f"1px solid {ThemeColor.BORDER.value}",
                "shadow": "none"
            },
            "ghost": {
                "bg_color": "transparent",
                "text_color": ThemeColor.FOREGROUND.value,
                "hover_bg": ThemeColor.ACCENT.value,
                "border": "1px solid transparent",
                "shadow": "none"
            },
            "link": {
                "bg_color": "transparent",
                "text_color": ThemeColor.PRIMARY.value,
                "hover_bg": "transparent",
                "border": "1px solid transparent",
                "shadow": "none"
            },
            # 工具栏按钮（参考提供参数）
            "toolbar": {
                "bg_color": "#f8f9fa",
                "text_color": "#495057",
                "hover_bg": "#e9ecef",
                "border": "1px solid #ced4da",
                "radius": "4px",
                "shadow": "none"
            }
        }
        
        size_cfg = size_config.get(size, size_config["default"])
        type_cfg = type_config.get(button_type, type_config["primary"])

        # 构建尺寸相关样式（Qt不支持height/width/outline/transform等）
        if size == "icon":
            padding_style = f"min-width: {size_cfg['min_w']}px; min-height: {size_cfg['min_h']}px; padding: 0px;"
        else:
            padding_style = f"min-height: {size_cfg['min_h']}px; padding: {size_cfg['pad_y']}px {size_cfg['pad_x']}px;"

        # 尺寸/间距：toolbar按设计覆盖为 6px 12px
        if button_type == "toolbar":
            padding_style = "min-height: 28px; padding: 6px 12px;"

        style = f"""
            QPushButton {{
                background-color: {type_cfg["bg_color"]};
                color: {type_cfg["text_color"]};
                border: {type_cfg["border"]};
                border-radius: {type_cfg.get('radius', '6px')};
                {padding_style}
                font-size: {size_cfg['font_px']}px;
                font-weight: {FontWeight.MEDIUM.value};
                text-align: center;
                cursor: pointinghand;
            }}
            QPushButton:hover {{
                background-color: {type_cfg["hover_bg"]};
            }}
            QPushButton:pressed {{
                background-color: {type_cfg["hover_bg"]};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColor.MUTED.value};
                color: {ThemeColor.MUTED_FOREGROUND.value};
                border: 1px solid {ThemeColor.BORDER.value};
            }}
        """
        
        # 特殊处理 link 类型按钮
        if button_type == "link":
            style += f"""
                QPushButton:hover {{
                    text-decoration: underline;
                    background-color: transparent;
                }}
            """

        # 工具栏pill按钮的选中态（用于setCheckable(True)的按钮）
        if button_type == "toolbar":
            style += f"""
                QPushButton:checked {{
                    background-color: {ThemeColor.BRAND_PRIMARY.value};
                    color: {ThemeColor.PRIMARY_FOREGROUND.value};
                    border: 2px solid #111827; /* 深色描边，贴近设计图效果 */
                    border-radius: {type_cfg.get('radius', '10px')};
                }}
                QPushButton:checked:hover {{
                    background-color: {ThemeColor.BRAND_PRIMARY_HOVER.value};
                }}
            """
        
        return style
    
    @staticmethod
    def get_label_style(label_type: str = "default") -> str:
        """获取标签样式 - 基于 shadcn/ui 文本设计
        
        Args:
            label_type: 标签类型 ("default", "large", "small", "muted", "lead", "p", "blockquote", "code")
            
        Returns:
            CSS样式字符串
        """
        styles = {
            "default": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.NORMAL.value};
                    line-height: 1.5;
                }}
            """,
            "large": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    font-size: {FontSize.LG.value};
                    font-weight: {FontWeight.SEMIBOLD.value};
                    line-height: 1.4;
                }}
            """,
            "small": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    line-height: 1.25;
                }}
            """,
            "muted": f"""
                QLabel {{
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.NORMAL.value};
                    line-height: 1.5;
                }}
            """,
            "lead": f"""
                QLabel {{
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    font-size: {FontSize.XL.value};
                    font-weight: {FontWeight.NORMAL.value};
                    line-height: 1.4;
                }}
            """,
            "p": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    font-size: {FontSize.BASE.value};
                    font-weight: {FontWeight.NORMAL.value};
                    line-height: 1.7;
                    margin: {Spacing.SM.value} 0;
                }}
            """,
            "blockquote": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    font-size: {FontSize.BASE.value};
                    font-weight: {FontWeight.NORMAL.value};
                    font-style: italic;
                    padding-left: {Spacing.XXL.value};
                    border-left: 2px solid {ThemeColor.BORDER.value};
                    margin: {Spacing.LG.value} 0;
                }}
            """,
            "code": f"""
                QLabel {{
                    color: {ThemeColor.FOREGROUND.value};
                    background-color: {ThemeColor.MUTED.value};
                    font-family: 'Courier New', monospace;
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    padding: {Spacing.XS.value} {Spacing.SM.value};
                    border-radius: {BorderRadius.SM.value};
                }}
            """,
            # 状态相关标签
            "success": f"""
                QLabel {{
                    color: #15803d;
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    line-height: 1.5;
                }}
            """,
            "warning": f"""
                QLabel {{
                    color: #d97706;
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    line-height: 1.5;
                }}
            """,
            "error": f"""
                QLabel {{
                    color: #dc2626;
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    line-height: 1.5;
                }}
            """,
            # 特殊用途标签
            "card_title": f"""
                QLabel {{
                    color: {ThemeColor.CARD_FOREGROUND.value};
                    font-size: {FontSize.LG.value};
                    font-weight: {FontWeight.SEMIBOLD.value};
                    line-height: 1.2;
                    padding: {Spacing.SM.value} 0;
                }}
            """,
            "card_description": f"""
                QLabel {{
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.NORMAL.value};
                    line-height: 1.5;
                }}
            """,
            "badge": f"""
                QLabel {{
                    background-color: {ThemeColor.PRIMARY.value};
                    color: {ThemeColor.PRIMARY_FOREGROUND.value};
                    font-size: {FontSize.XS.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    padding: {Spacing.XS.value} {Spacing.SM.value};
                    border-radius: {BorderRadius.FULL.value};
                    text-align: center;
                }}
            """
        }
        
        return styles.get(label_type, styles["default"])
    
    @staticmethod
    def get_status_indicator_style(status_type: str = "default") -> str:
        """获取状态指示器样式 - 基于 shadcn/ui Badge 设计
        
        Args:
            status_type: 状态类型 ("default", "secondary", "destructive", "outline", "success", "warning")
            
        Returns:
            CSS样式字符串
        """
        status_config = {
            "default": {
                "bg_color": ThemeColor.PRIMARY.value,
                "text_color": ThemeColor.PRIMARY_FOREGROUND.value,
                "border": "1px solid transparent"
            },
            "secondary": {
                "bg_color": ThemeColor.SECONDARY.value,
                "text_color": ThemeColor.SECONDARY_FOREGROUND.value,
                "border": "1px solid transparent"
            },
            "destructive": {
                "bg_color": ThemeColor.DESTRUCTIVE.value,
                "text_color": ThemeColor.DESTRUCTIVE_FOREGROUND.value,
                "border": "1px solid transparent"
            },
            "outline": {
                "bg_color": "transparent",
                "text_color": ThemeColor.FOREGROUND.value,
                "border": f"1px solid {ThemeColor.BORDER.value}"
            },
            "success": {
                "bg_color": ThemeColor.SUCCESS.value,
                "text_color": ThemeColor.SUCCESS_FOREGROUND.value,
                "border": "1px solid transparent"
            },
            "warning": {
                "bg_color": ThemeColor.WARNING.value,
                "text_color": ThemeColor.WARNING_FOREGROUND.value,
                "border": "1px solid transparent"
            }
        }
        
        config = status_config.get(status_type, status_config["default"])
        
        return f"""
            QLabel {{
                background-color: {config["bg_color"]};
                color: {config["text_color"]};
                border: {config["border"]};
                border-radius: {BorderRadius.FULL.value};
                padding: {Spacing.XS.value} {Spacing.SM.value};
                font-size: {FontSize.XS.value};
                font-weight: {FontWeight.MEDIUM.value};
                text-align: center;
                display: inline-flex;
                align-items: center;
                line-height: 1;
            }}
        """
    
    @staticmethod
    def get_slider_style() -> str:
        """获取滑块样式 - 基于 shadcn/ui Slider 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QSlider::groove:horizontal {{
                background: {ThemeColor.SECONDARY.value};
                height: 8px;
                border-radius: {BorderRadius.FULL.value};
                border: none;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColor.BACKGROUND.value};
                border: 2px solid {ThemeColor.PRIMARY.value};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {ThemeColor.BACKGROUND.value};
                border: 2px solid {ThemeColor.PRIMARY.value};
                box-shadow: {Shadow.MD.value};
            }}
            QSlider::handle:horizontal:pressed {{
                background: {ThemeColor.BACKGROUND.value};
                border: 2px solid {ThemeColor.PRIMARY.value};
            }}
            QSlider::handle:horizontal:focus {{
                outline: 2px solid {ThemeColor.RING.value};
                outline-offset: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ThemeColor.PRIMARY.value};
                border-radius: {BorderRadius.FULL.value};
            }}
            QSlider::add-page:horizontal {{
                background: {ThemeColor.SECONDARY.value};
                border-radius: {BorderRadius.FULL.value};
            }}
        """
    
    @staticmethod
    def get_input_style() -> str:
        """获取输入框样式 - 基于 shadcn/ui Input 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QLineEdit {{
                background-color: {ThemeColor.BACKGROUND.value};
                border: 1px solid {ThemeColor.INPUT.value};
                border-radius: {BorderRadius.DEFAULT.value};
                padding: {Spacing.SM.value} {Spacing.MD.value};
                font-size: {FontSize.SM.value};
                line-height: 1.5;
                color: {ThemeColor.FOREGROUND.value};
                height: 2.5rem;
            }}
            QLineEdit:focus {{
                outline: none;
                border: 2px solid {ThemeColor.RING.value};
                border-radius: {BorderRadius.DEFAULT.value};
            }}
            QLineEdit:disabled {{
                background-color: {ThemeColor.MUTED.value};
                color: {ThemeColor.MUTED_FOREGROUND.value};
                cursor: not-allowed;
                opacity: 0.5;
            }}
            QLineEdit::placeholder {{
                color: {ThemeColor.MUTED_FOREGROUND.value};
            }}
            
            QTextEdit {{
                background-color: {ThemeColor.BACKGROUND.value};
                border: 1px solid {ThemeColor.INPUT.value};
                border-radius: {BorderRadius.DEFAULT.value};
                padding: {Spacing.MD.value};
                font-size: {FontSize.SM.value};
                line-height: 1.5;
                color: {ThemeColor.FOREGROUND.value};
                min-height: 5rem;
            }}
            QTextEdit:focus {{
                outline: none;
                border: 2px solid {ThemeColor.RING.value};
            }}
            QTextEdit:disabled {{
                background-color: {ThemeColor.MUTED.value};
                color: {ThemeColor.MUTED_FOREGROUND.value};
                cursor: not-allowed;
                opacity: 0.5;
            }}
        """
    
    @staticmethod
    def get_group_box_style() -> str:
        """获取分组框样式 - 基于 shadcn/ui Card 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QGroupBox {{
                background-color: {ThemeColor.CARD.value};
                border: 1px solid {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.LG.value};
                padding: {Spacing.LG.value};
                margin-top: {Spacing.XXL.value};
                font-size: {FontSize.SM.value};
                font-weight: {FontWeight.MEDIUM.value};
                color: {ThemeColor.CARD_FOREGROUND.value};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: {Spacing.MD.value};
                top: -{Spacing.MD.value};
                background-color: {ThemeColor.CARD.value};
                padding: {Spacing.XS.value} {Spacing.SM.value};
                color: {ThemeColor.FOREGROUND.value};
                font-weight: {FontWeight.SEMIBOLD.value};
                border-radius: {BorderRadius.SM.value};
            }}
        """
    
    @staticmethod
    def get_card_style() -> str:
        """获取卡片样式 - 基于 shadcn/ui Card 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QWidget {{
                background-color: {ThemeColor.CARD.value};
                border: 1px solid {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.XL.value};
                box-shadow: {Shadow.SM.value};
                padding: {Spacing.LG.value};
            }}
        """
    
    @staticmethod
    def get_separator_style() -> str:
        """获取分隔符样式 - 基于 shadcn/ui Separator 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QFrame[frameShape="4"] {{
                background-color: {ThemeColor.BORDER.value};
                border: none;
                height: 1px;
                margin: {Spacing.LG.value} 0;
            }}
            QFrame[frameShape="5"] {{
                background-color: {ThemeColor.BORDER.value};
                border: none;
                width: 1px;
                margin: 0 {Spacing.LG.value};
            }}
        """
    
    @staticmethod
    def get_tooltip_style() -> str:
        """获取工具提示样式 - 基于 shadcn/ui 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QToolTip {{
                background-color: {ThemeColor.PRIMARY.value};
                color: {ThemeColor.PRIMARY_FOREGROUND.value};
                border: none;
                border-radius: {BorderRadius.DEFAULT.value};
                padding: {Spacing.SM.value} {Spacing.MD.value};
                font-size: {FontSize.SM.value};
                font-weight: {FontWeight.MEDIUM.value};
                box-shadow: {Shadow.MD.value};
            }}
        """
    
    @staticmethod
    def get_scroll_area_style() -> str:
        """获取滚动区域样式 - 基于 shadcn/ui 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QScrollArea {{
                border: 1px solid {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.DEFAULT.value};
                background-color: {ThemeColor.BACKGROUND.value};
            }}
            QScrollBar:vertical {{
                background: {ThemeColor.MUTED.value};
                width: 12px;
                border-radius: {BorderRadius.DEFAULT.value};
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.DEFAULT.value};
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeColor.MUTED_FOREGROUND.value};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """
    
    @staticmethod
    def get_scrollbar_style() -> str:
        """获取滚动条样式 - 基于 shadcn/ui 设计
        
        Returns:
            CSS样式字符串
        """
        return f"""
            QScrollBar:vertical {{
                background: {ThemeColor.MUTED.value};
                width: 12px;
                border-radius: {BorderRadius.DEFAULT.value};
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.DEFAULT.value};
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeColor.MUTED_FOREGROUND.value};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {ThemeColor.MUTED.value};
                height: 12px;
                border-radius: {BorderRadius.DEFAULT.value};
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {ThemeColor.BORDER.value};
                border-radius: {BorderRadius.DEFAULT.value};
                min-width: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {ThemeColor.MUTED_FOREGROUND.value};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0;
            }}
        """


class ComponentStyleFactory:
    """组件样式工厂 - 为特定组件提供预设样式组合"""
    
    @staticmethod
    def get_cardiac_cycle_styles() -> Dict[str, str]:
        """获取心动周期组件样式集合 - 基于 shadcn/ui 设计"""
        return {
            "phase_percent_label": StyleManager.get_label_style("primary"),
            "frame_info_label": StyleManager.get_label_style("secondary"),
            "series_description_label": StyleManager.get_label_style("muted"),
            "control_button": StyleManager.get_button_style("outline", "sm"),
            "mark_button": StyleManager.get_button_style("default", "default"),
            "marked_phase_label": StyleManager.get_label_style("secondary"),
            "slider": StyleManager.get_slider_style(),
            "range_label": StyleManager.get_label_style("muted"),
            "container": StyleManager.get_card_style(),
            "section_header": StyleManager.get_label_style("subtitle"),
            "section_separator": StyleManager.get_separator_style()
        }
    
    @staticmethod
    def get_main_ui_styles() -> Dict[str, str]:
        """获取主界面组件样式集合 - 基于 shadcn/ui 设计"""
        return {
            "app_title": f"""
                QLabel {{
                    font-size: {FontSize.XL.value};
                    font-weight: {FontWeight.BOLD.value};
                    color: {ThemeColor.FOREGROUND.value};
                    margin-bottom: {Spacing.MD.value};
                }}
            """,
            "status_indicator": StyleManager.get_status_indicator_style("default"),
            "nav_hint": f"""
                QLabel {{
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    font-size: {FontSize.SM.value};
                    margin-top: {Spacing.SM.value};
                }}
            """,
            "welcome_label": StyleManager.get_label_style("large"),
            "description_label": f"""
                QLabel {{
                    font-size: {FontSize.BASE.value};
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    margin: {Spacing.LG.value} 0;
                    line-height: 1.6;
                }}
            """,
            "module_button": f"""
                QPushButton {{
                    background-color: {ThemeColor.BACKGROUND.value};
                    color: {ThemeColor.FOREGROUND.value};
                    border: 1px solid {ThemeColor.BORDER.value};
                    border-radius: {BorderRadius.DEFAULT.value};
                    padding: {Spacing.MD.value} {Spacing.LG.value};
                    font-size: {FontSize.SM.value};
                    font-weight: {FontWeight.MEDIUM.value};
                    text-align: center;
                    min-width: 120px;
                    min-height: 40px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColor.ACCENT.value};
                    color: {ThemeColor.ACCENT_FOREGROUND.value};
                }}
                QPushButton:checked {{
                    background-color: {ThemeColor.PRIMARY.value};
                    color: {ThemeColor.PRIMARY_FOREGROUND.value};
                    border-color: {ThemeColor.PRIMARY.value};
                }}
                QPushButton:checked:hover {{
                    background-color: #475569;
                    border-color: #475569;
                }}
                QPushButton:pressed {{
                    background-color: {ThemeColor.ACCENT.value};
                }}
            """,
            "secondary_button": StyleManager.get_button_style("secondary", "default"),
            "danger_button": StyleManager.get_button_style("destructive", "default"),
            "container_card": StyleManager.get_card_style(),
            "section_separator": StyleManager.get_separator_style()
        }
    
    @staticmethod
    def get_module1_styles() -> Dict[str, str]:
        """获取模块一专用样式集合"""
        # 基于主界面样式构建
        styles = ComponentStyleFactory.get_main_ui_styles().copy()
        
        # 模块一特定样式
        styles.update({
            "instruction_label": f"""
                QLabel {{
                    padding: {Spacing.MD.value};
                    background-color: {ThemeColor.MUTED.value};
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    border: 1px solid {ThemeColor.BORDER.value};
                    border-radius: {BorderRadius.DEFAULT.value};
                    font-size: {FontSize.SM.value};
                    line-height: 1.4;
                }}
            """,
            
            "next_module_button_ready": f"""
                QPushButton {{
                    background-color: {ThemeColor.PRIMARY.value};
                    color: {ThemeColor.PRIMARY_FOREGROUND.value};
                    border: none;
                    border-radius: {BorderRadius.DEFAULT.value};
                    padding: {Spacing.MD.value} {Spacing.LG.value};
                    font-size: {FontSize.SM.value};
                    font-weight: 600;
                    min-height: 40px;
                }}
                QPushButton:hover {{
                    background-color: #475569;
                }}
                QPushButton:pressed {{
                    background-color: #334155;
                }}
                QPushButton:focus {{
                    outline: 2px solid {ThemeColor.RING};
                    outline-offset: 2px;
                }}
            """,
            
            "next_module_button_disabled": f"""
                QPushButton {{
                    background-color: {ThemeColor.MUTED.value};
                    color: {ThemeColor.MUTED_FOREGROUND.value};
                    border: none;
                    border-radius: {BorderRadius.DEFAULT.value};
                    padding: {Spacing.MD.value} {Spacing.LG.value};
                    font-size: {FontSize.SM.value};
                    font-weight: 600;
                    min-height: 40px;
                }}
            """,
        })
        
        return styles
    
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
