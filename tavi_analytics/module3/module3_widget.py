"""
模块三界面组件（骨架）

仅展示一个 Mock 标题，支持在主导航中切换到本页面。
"""
import logging
from typing import Optional
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.phase_selection_widget import PhaseSelectionWidget
    from .module3_logic import Module3Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from widgets.phase_selection_widget import PhaseSelectionWidget
    from module3.module3_logic import Module3Logic


class Module3Widget(qt.QWidget):
    """模块三界面（仅Mock标题 + JSON加载交互）"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module3Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module3Logic()
        
        # 创建期像选择组件
        self.phase_selection = PhaseSelectionWidget(session, self)
        self.phase_selection.phaseChanged.connect(self._on_phase_changed)
        self.phase_selection.statusUpdated.connect(self._on_phase_status_updated)
        
        self.setObjectName("Module3Widget")
        self._setup_ui()
        logging.info("Module3Widget 初始化完成 (skeleton)")

    def _on_phase_changed(self, phase: str):
        """
        期像改变时的回调
        
        Args:
            phase: 新的期像 ('diastole' 或 'systole')
        """
        logging.info(f"模块三期像已切换到: {phase}")
        
        # 这里可以根据期像变更更新模块三的分析逻辑
        if self.logic:
            # 如果需要，可以在逻辑类中添加期像相关的方法
            pass
        
        # 更新结果显示
        phase_name = "舒张末期" if phase == 'diastole' else "收缩末期"
        self.result_label.setText(f"当前期像: {phase_name}，可以开始测量分析")
    
    def _on_phase_status_updated(self, status: str):
        """
        期像状态更新时的回调
        
        Args:
            status: 状态消息
        """
        logging.debug(f"模块三期像状态更新: {status}")
    
    # 兼容性工具：有的环境 QLineEdit.text 是方法，有的可能是属性
    def _get_line_edit_text(self, le: qt.QLineEdit) -> str:
        try:
            # 优先按方法调用
            return le.text().strip()
        except TypeError:
            # 若 text 是字符串属性，则不要调用
            t = getattr(le, 'text', '')
            return t.strip() if isinstance(t, str) else str(t).strip()

    def _setup_ui(self):
        # 使用统一布局与样式体系，和模块1、2保持一致
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 标题区（Mock）
        title = qt.QLabel("模块三：自动化测量（Mock 页面）")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))

        desc = qt.QLabel("此处为占位页面，用于确认导航切换与框架搭建是否正常。\n现已加入JSON曲线加载的UI演示和期像选择功能。")
        desc.setAlignment(qt.Qt.AlignCenter)
        desc.setStyleSheet(StyleManager.get_label_style("muted"))

        # 添加期像选择组件
        self.phase_selection.set_info_text(
            "💡 提示：请选择要进行测量分析的期像。\n"
            "不同期像的测量结果可能会有所差异。"
        )

        # JSON 加载区
        io_group = LayoutManager.create_section_frame("加载测量JSON并绘制闭合曲线")
        io_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, io_group)

        # 路径输入 + 浏览 + 清理开关
        path_row = LayoutManager.create_horizontal_layout(LayoutType.BUTTON_GROUP)
        self.json_path_edit = qt.QLineEdit()
        self.json_path_edit.setPlaceholderText("请输入JSON文件路径，例如 C:/data/measurement.json")
        self.json_path_edit.setMinimumHeight(32)
        self.json_path_edit.setStyleSheet(StyleManager.get_input_style())
        # 默认填写路径，便于快速调试
        self.json_path_edit.setText(r"C:\code\python\slicer\tavi_analytics\data\measurement.json")

        browse_btn = LayoutManager.create_button_with_style(
            text="浏览...", button_type="secondary", size="default", min_height=32
        )
        browse_btn.clicked.connect(self._on_browse_json)

        self.clear_checkbox = qt.QCheckBox("加载前清理现有 plane 节点")
        self.clear_checkbox.setChecked(True)

        path_row.addWidget(self.json_path_edit, 4)
        path_row.addWidget(browse_btn, 0)
        path_row.addWidget(self.clear_checkbox, 0)

        # 加载按钮
        load_btn = LayoutManager.create_button_with_style(
            text="加载数据", button_type="primary", size="default", min_height=38
        )
        load_btn.clicked.connect(self._on_load_clicked)

        # 结果/状态显示
        self.result_label = qt.QLabel("等待加载...")
        self.result_label.setStyleSheet(StyleManager.get_label_style("muted"))

        io_layout.addLayout(path_row)
        io_layout.addWidget(load_btn)
        io_layout.addWidget(self.result_label)

        # 容器组装
        container = LayoutManager.create_section_frame("模块三")
        container_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, container)
        container_layout.addWidget(title)
        container_layout.addWidget(desc)
        container_layout.addWidget(self.phase_selection)  # 添加期像选择组件
        container_layout.addWidget(io_group)

        main_layout.addWidget(container, 1)
        LayoutManager.add_stretch_with_ratio(main_layout, 1)

    def _on_browse_json(self):
        try:
            dlg = qt.QFileDialog(self, "选择测量JSON文件")
            dlg.setNameFilter("JSON Files (*.json)")
            dlg.setFileMode(qt.QFileDialog.ExistingFile)
            if dlg.exec_():
                files = dlg.selectedFiles()
                if files:
                    self.json_path_edit.setText(files[0])
        except Exception as e:
            logging.error(f"选择文件失败: {e}")

    def _on_load_clicked(self):
        try:
            path = self._get_line_edit_text(self.json_path_edit)
            if not path:
                qt.QMessageBox.information(self, "提示", "请先填写JSON文件路径")
                return

            self.result_label.setText("⏳ 正在加载，请稍候...")
            qt.QApplication.processEvents()  # 强制更新界面

            clear_existing = self.clear_checkbox.isChecked()
            result = self.logic.load_plane_curves_from_json(path, clear_existing=clear_existing)

            if result.get("error"):
                self.result_label.setText(f"❌ 加载失败: {result['error']}")
                return

            created = result.get("created_count", 0)
            lines = result.get("curve_info", [])
            summary = "\n".join(lines) if lines else "无曲线创建"
            self.result_label.setText(f"✅ 创建 {created} 条闭合曲线\n{summary}")
            logging.info(f"模块三加载完成: {created} 条曲线")
        except Exception as e:
            logging.error(f"加载数据失败: {e}")
            self.result_label.setText(f"❌ 发生错误: {str(e)}")

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if hasattr(self, 'phase_selection'):
            self.phase_selection.set_session(session)
        if self.logic:
            # 如需使用session，可在后续逻辑中扩展
            pass

    def on_activated(self):
        logging.info("模块三已激活")
        
        # 激活期像选择组件，默认选择舒张末期
        if hasattr(self, 'phase_selection'):
            self.phase_selection.auto_activate(preferred_phase='diastole')

    def on_deactivated(self):
        logging.info("模块三已停用")

    def cleanup(self):
        if hasattr(self, 'phase_selection'):
            self.phase_selection.cleanup()
        if self.logic:
            self.logic.cleanup()
        logging.info("模块三界面清理完成")
