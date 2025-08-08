"""
步骤清单组件（Module1 专用）

显示模块一关键步骤完成状态：
- 数据导入
- 患者信息
- 舒张末期
- 收缩末期

提供 update_steps(status: dict) 接口实时更新。
"""
import qt
from typing import Dict, Optional

try:
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager, LayoutType
except ImportError:
    # 兼容独立运行
    import os, sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager, LayoutType


class _StepRow(qt.QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = qt.QLabel("○")  # 未完成
        self.icon.setMinimumWidth(18)
        self.text = qt.QLabel(title)
        self.hint = qt.QLabel("")
        self.hint.setStyleSheet(StyleManager.get_label_style("muted"))

        row = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        row.addWidget(self.icon, 0)
        row.addWidget(self.text, 1)
        row.addWidget(self.hint, 1)
        self.setLayout(row)

    def set_status(self, done: bool, hint: Optional[str] = None):
        if done:
            self.icon.setText("✔")
            self.icon.setStyleSheet("color: #16a34a; font-weight: bold;")  # 绿色
            self.text.setStyleSheet(StyleManager.get_label_style("default"))
            self.hint.setText("")
        else:
            self.icon.setText("○")
            self.icon.setStyleSheet("color: #9ca3af;")  # 灰色
            self.text.setStyleSheet(StyleManager.get_label_style("default"))
            self.hint.setText(hint or "")


class StepChecklistWidget(qt.QFrame):
    """模块一步骤清单组件

    使用 update_steps 接口更新四个步骤的完成状态。
    keys: data_imported, patient_info, phase_ed, phase_es
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StepChecklistWidget")
        # 避免过度拉伸
        self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
        self._build_ui()

    def _build_ui(self):
        # 外层容器（附着到自身）
        outer = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, self)

        # 使用标准分组框，保证标题与边框一致
        group = LayoutManager.create_section_frame("任务进度", LayoutType.SECTION_CONTAINER)
        group_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, group)

        # 行项目
        self.row_data = _StepRow("数据导入")
        self.row_patient = _StepRow("患者信息")
        self.row_ed = _StepRow("舒张末期时相")
        self.row_es = _StepRow("收缩末期时相")

        group_layout.addWidget(self.row_data)
        group_layout.addWidget(self.row_patient)
        group_layout.addWidget(self.row_ed)
        group_layout.addWidget(self.row_es)

        outer.addWidget(group)
        # 轻量边框风格
        self.setFrameShape(qt.QFrame.NoFrame)

    def update_steps(self, status: Dict[str, bool]):
        """根据状态字典更新清单显示
        status keys: data_imported, patient_info, phase_ed, phase_es
        """
        data_ok = bool(status.get("data_imported"))
        patient_ok = bool(status.get("patient_info"))
        ed_ok = bool(status.get("phase_ed"))
        es_ok = bool(status.get("phase_es"))

        self.row_data.set_status(data_ok, None if data_ok else "去导入")
        self.row_patient.set_status(patient_ok, None if patient_ok else "完善患者信息")
        self.row_ed.set_status(ed_ok, None if ed_ok else "标记舒张末期")
        self.row_es.set_status(es_ok, None if es_ok else "标记收缩末期")

        # 自适应高度（防止留下大空白）
        self.updateGeometry()
        self.adjustSize()
