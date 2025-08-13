"""
模块三界面组件

自动化测量功能界面。
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
    """模块三界面"""

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
        logging.info("Module3Widget 初始化完成")

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
    
    def _on_phase_status_updated(self, status: str):
        """
        期像状态更新时的回调
        
        Args:
            status: 状态消息
        """
        logging.debug(f"模块三期像状态更新: {status}")
    
    def _on_switch_to_valve_plane(self):
        """
        切换到ValveStent_Bottom_Plane平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块三逻辑未初始化")
                return
            
            logging.info("开始切换到ValveStent_Bottom_Plane平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_valve_plane_btn.setEnabled(False)
            self.switch_to_valve_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_valve_stent_bottom_plane()
            
            if success:
                logging.info("成功切换到ValveStent_Bottom_Plane平面")
                # 可以在这里添加成功提示
                self.switch_to_valve_plane_btn.setText("✅ 切换完成")
                # 2秒后恢复按钮文本
                qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 切换到ValveStent_Bottom_Plane平面"))
            else:
                logging.error("切换到ValveStent_Bottom_Plane平面失败")
                self.switch_to_valve_plane_btn.setText("❌ 切换失败")
                # 2秒后恢复按钮文本
                qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 切换到ValveStent_Bottom_Plane平面"))
            
        except Exception as e:
            logging.error(f"切换到ValveStent_Bottom_Plane平面时出错: {e}")
            self.switch_to_valve_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 切换到ValveStent_Bottom_Plane平面"))
        finally:
            # 重新启用按钮
            self.switch_to_valve_plane_btn.setEnabled(True)
    
    def _setup_ui(self):
        # 使用统一布局与样式体系，和模块1、2保持一致
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)

        # 标题区
        title = qt.QLabel("模块三：自动化测量")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))

        # 添加期像选择组件
        self.phase_selection.set_info_text(
            "💡 提示：请选择要进行测量分析的期像。\n"
            "不同期像的测量结果可能会有所差异。"
        )

        # 创建平面切换控制区域
        plane_control_frame = LayoutManager.create_section_frame("平面视图控制")
        plane_control_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, plane_control_frame)
        
        # 平面切换说明
        plane_info = qt.QLabel(
            "📐 平面视图控制\n"
            "点击下方按钮将当前MPR视图切换到ValveStent_Bottom_Plane平面。\n"
            "轴状面将切换到该平面，矢状面和冠状面与之垂直相交。"
        )
        plane_info.setWordWrap(True)
        plane_info.setStyleSheet(StyleManager.get_label_style("info"))
        
        # 平面切换按钮
        self.switch_to_valve_plane_btn = LayoutManager.create_button_with_style(
            "🎯 切换到ValveStent_Bottom_Plane平面", 
            "primary", 
            "default", 
            45
        )
        self.switch_to_valve_plane_btn.clicked.connect(self._on_switch_to_valve_plane)
        
        # 组装平面控制区域
        plane_control_layout.addWidget(plane_info)
        plane_control_layout.addWidget(self.switch_to_valve_plane_btn)

        # 容器组装
        container = LayoutManager.create_section_frame("模块三")
        container_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, container)
        container_layout.addWidget(title)
        container_layout.addWidget(self.phase_selection)  # 添加期像选择组件
        container_layout.addWidget(plane_control_frame)   # 添加平面控制区域

        main_layout.addWidget(container, 1)
        LayoutManager.add_stretch_with_ratio(main_layout, 1)

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
