"""
通用 SectionCard 组件

提供可复用的卡片式分区布局与标题栏（图标+标题），用于统一各模块的 Section 外观与排版。
"""

import qt


class SectionCard(qt.QWidget):
    """统一的分区卡片组件（标题栏 + 内容区）

    特性:
    - 统一的卡片圆角/边框/阴影/内边距
    - 标题栏包含左侧图标与标题文本
    - 内容区(body)提供 QVBoxLayout，供外部自由添加控件
    - 支持多种配色风格（blue/purple/neutral）以匹配现有UI
    """

    def __init__(self, title: str, icon_text: str = "", variant: str = "neutral", parent=None):
        super().__init__(parent)

        # 设置卡片基础属性
        self.setObjectName("SectionCard")
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Maximum)

        # 根布局
        root = qt.QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # 标题栏
        header_container = qt.QWidget()
        header_layout = qt.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        if icon_text:
            self.icon_label = qt.QLabel(icon_text)
            self.icon_label.setAlignment(qt.Qt.AlignCenter)
            self.icon_label.setFixedSize(48, 48)
            header_layout.addWidget(self.icon_label)
        else:
            self.icon_label = None

        self.title_label = qt.QLabel(title)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        root.addWidget(header_container)

        # 内容区
        self.body = qt.QWidget()
        self.body_layout = qt.QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)
        root.addWidget(self.body)

        # 根据主题变体应用样式
        self._apply_variant_style(variant)

    # 便捷方法
    def add_widget(self, widget):
        self.body_layout.addWidget(widget)

    def add_layout(self, layout):
        self.body_layout.addLayout(layout)

    def _apply_variant_style(self, variant: str):
        variant = (variant or "neutral").lower()
        # 颜色方案映射（与现有UI风格对齐）
        if variant == "blue":
            card_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb)"
            border = "#2196f3"
            title_color = "#1565c0"
            icon_color = "#1976d2"
        elif variant == "purple":
            card_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f3e5f5, stop:1 #e1bee7)"
            border = "#9c27b0"
            title_color = "#6a1b9a"
            icon_color = "#7b1fa2"
        else:
            # neutral 默认卡片
            card_bg = "#ffffff"
            border = "#e2e8f0"
            title_color = "#0f172a"
            icon_color = "#64748b"

        # 卡片样式
        self.setStyleSheet(
            f"""
            QWidget#SectionCard {{
                background: {card_bg};
                border: 2px solid {border};
                border-radius: 16px;
                margin: 4px;
            }}
            """
        )

        # 标题与图标样式
        if self.icon_label is not None:
            self.icon_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 28px;
                    color: {icon_color};
                    background: transparent;
                    padding: 4px;
                }}
                """
            )

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {title_color};
                background: transparent;
                padding-left: 4px;
            }}
            """
        )
