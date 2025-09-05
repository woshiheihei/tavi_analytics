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
        self._root_layout = root

        # 标题栏
        header_container = qt.QWidget()
        header_layout = qt.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        self._header_layout = header_layout

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

        # 是否使用虚线边框（支持传入 "dashed" 或 "*-dashed"）
        use_dashed = (variant == "dashed") or ("dashed" in variant)

        # 颜色方案映射（与现有UI风格对齐）
        if variant.startswith("blue"):
            card_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb)"
            border_color = "#2196f3"
            title_color = "#1565c0"
            icon_color = "#1976d2"
        elif variant.startswith("green"):
            # 参考: border-color: #10b981; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            # 使用 Qt 的 qlineargradient 近似 135deg 的方向
            card_bg = "qlineargradient(x1:1, y1:0, x2:0, y2:1, stop:0 #d1fae5, stop:1 #a7f3d0)"
            border_color = "#10b981"
            title_color = "#065f46"
            icon_color = "#10b981"
        elif variant.startswith("purple"):
            card_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f3e5f5, stop:1 #e1bee7)"
            border_color = "#9c27b0"
            title_color = "#6a1b9a"
            icon_color = "#7b1fa2"
        else:
            # neutral 默认卡片（纯白背景）
            card_bg = "#ffffff"
            border_color = "#e2e8f0"  # slate-200
            title_color = "#0f172a"
            icon_color = "#64748b"

        # 边框样式（按需求：虚线 2px dashed #dee2e6，圆角 8px）
        border_width = 2 if use_dashed else 2
        border_style = "dashed" if use_dashed else "solid"
        # 虚线时使用专用颜色与更小圆角
        if use_dashed:
            border_color = "#dee2e6"
            border_radius = 8
        else:
            border_radius = 16

        # 卡片样式
        self.setStyleSheet(
            f"""
            QWidget#SectionCard {{
                background: {card_bg};
                border: {border_width}px {border_style} {border_color};
                border-radius: {border_radius}px;
                margin: 4px;
            }}
            """
        )

        # 紧凑模式：用于子 section（如 dashed 变体）
        if use_dashed:
            # 缩小内边距与间距
            if hasattr(self, "_root_layout") and self._root_layout is not None:
                self._root_layout.setContentsMargins(16, 12, 16, 16)
                self._root_layout.setSpacing(12)
            if hasattr(self, "_header_layout") and self._header_layout is not None:
                self._header_layout.setSpacing(8)
            icon_px = 20
            icon_box = 32
            title_px = 16
            title_weight = "600"  # semibold
        else:
            icon_px = 28
            icon_box = 48
            title_px = 18
            title_weight = "700"  # bold

        # 更新图标尺寸
        if self.icon_label is not None:
            try:
                self.icon_label.setFixedSize(icon_box, icon_box)
            except Exception:
                pass
            self.icon_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: {icon_px}px;
                    color: {icon_color};
                    background: transparent;
                    padding: 4px;
                }}
                """
            )

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: {title_px}px;
                font-weight: {title_weight};
                color: {title_color};
                background: transparent;
                padding-left: 4px;
            }}
            """
        )
