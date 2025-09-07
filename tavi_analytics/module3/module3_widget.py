"""
模块三界面组件

瓣叶功能评估界面。
"""
import logging
from typing import Optional
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.compact_phase_toggle import CompactPhaseToggle
    from .module3_logic import Module3Logic
    from .halt_analysis_widget import HaltAnalysisWidget
    from .paste_analysis_widget import Module3AnalysisWidget, RelmAnalysisWidget, SfdAnalysisWidget, PfdAnalysisWidget
except ImportError:
    import os
    import sys
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
    from widgets.compact_phase_toggle import CompactPhaseToggle
    from module3_logic import Module3Logic
    from halt_analysis_widget import HaltAnalysisWidget
    from paste_analysis_widget import Module3AnalysisWidget, RelmAnalysisWidget, SfdAnalysisWidget, PfdAnalysisWidget


class Module3Widget(qt.QWidget):
    """模块三界面"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module3Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module3Logic()
        
        # 创建紧凑期像切换组件
        self.compact_phase_toggle = CompactPhaseToggle(session, self)
        self.compact_phase_toggle.phaseChanged.connect(self._on_phase_changed)
        
        # 创建HALT分析组件
        self.halt_analysis = HaltAnalysisWidget(session, parent=self)
        
        # 注释：原来的module3_analysis已被拆分为独立的RELM、SFD、PFD组件
        # 保留引用以向后兼容，但在新的UI中不再使用
        # self.module3_analysis = Module3AnalysisWidget(session, parent=self)
        
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
        
        # 更新逻辑层的当前期像
        if self.logic:
            # 将期像格式转换为领域模型格式
            domain_phase = 'end_diastole' if phase == 'diastole' else 'end_systole'
            self.logic.set_current_phase(domain_phase)
        
        # 同步两个期像选择组件的状态
        self._sync_phase_widgets(phase)
    # 快速定位关键平面组件已移除，无需刷新平面状态
    
    def _sync_phase_widgets(self, phase: str):
        """
        同步期像切换组件的状态（仅紧凑版）
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
        """
        try:
            # 同步紧凑期像切换组件
            if hasattr(self, 'compact_phase_toggle'):
                current_phase = self.compact_phase_toggle.get_current_phase()
                if current_phase != phase:
                    self.compact_phase_toggle.sync_phase_from_external(phase)
                    
        except Exception as e:
            logging.error(f"同步期像组件状态失败: {e}")
    
    def _on_phase_status_updated(self, status: str):
        """
        期像状态更新时的回调
        
        Args:
            status: 状态消息
        """
        logging.debug(f"模块三期像状态更新: {status}")
    
    
    def _setup_ui(self):
        # 使用统一布局与样式体系，和模块1、2保持一致
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)
        try:
            main_layout.setSizeConstraint(qt.QLayout.SetMinimumSize)
            self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
        except Exception:
            pass

        # 期像切换器区域
        title_container = qt.QWidget()
        title_layout = qt.QHBoxLayout(title_container)
        title_layout.setContentsMargins(8, 8, 8, 8)
        title_layout.setSpacing(20)

        title_layout.addWidget(self.compact_phase_toggle)
        title_layout.addStretch()

        # 快速定位关键平面控制区域已移除

        # 分析区域 - 选项卡（去除外层"瓣叶功能评估"Section，直接使用Tab）
        self.analysis_tabs = qt.QTabWidget()
        try:
            self.analysis_tabs.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
            self.analysis_tabs.setElideMode(qt.Qt.ElideNone)
        except Exception:
            pass
        self.analysis_tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #dee2e6; border-radius: 4px; background-color: white; }
            QTabBar::tab { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: white; border-bottom-color: white; }
            """
        )

        # 创建并添加分析组件
        self.analysis_tabs.addTab(self.halt_analysis, "HALT分析")

        # 功能开关：暂时隐藏 RELM 分析（未设计完成）
        SHOW_RELM = False
        if SHOW_RELM:
            self.relm_analysis = RelmAnalysisWidget(self.session, parent=self)
            self.analysis_tabs.addTab(self.relm_analysis, "RELM分析")

        self.sfd_analysis = SfdAnalysisWidget(self.session, parent=self)
        self.pfd_analysis = PfdAnalysisWidget(self.session, parent=self)
        self.analysis_tabs.addTab(self.sfd_analysis, "SFD分析")
        self.analysis_tabs.addTab(self.pfd_analysis, "PFD分析")

        # 汇总布局（滚动在主界面 MainUI 中提供）
        main_layout.addWidget(title_container)
        # 直接将选项卡添加到主布局
        main_layout.addWidget(self.analysis_tabs)
        main_layout.addStretch()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.session = session
        if hasattr(self, 'halt_analysis'):
            self.halt_analysis.set_session(session)
        if hasattr(self, 'relm_analysis'):
            self.relm_analysis.set_session(session)
        if hasattr(self, 'sfd_analysis'):
            self.sfd_analysis.set_session(session)
        if hasattr(self, 'pfd_analysis'):
            self.pfd_analysis.set_session(session)
        # 保留原有的module3_analysis支持（向后兼容）
        if hasattr(self, 'module3_analysis'):
            self.module3_analysis.set_session(session)
        if self.logic:
            # 如需使用session，可在后续逻辑中扩展
            pass

    def on_activated(self):
        logging.info("模块三已激活")
        
        # 启用MPR交互式切片相交线功能
        self._enable_mpr_crosshairs()
        
        # 设置默认期像到紧凑切换器并同步逻辑
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.set_current_phase('diastole')
            # 由组件信号驱动逻辑同步
        
        # 激活HALT分析组件
        if hasattr(self, 'halt_analysis'):
            self.halt_analysis.on_activated()
        
        # 激活独立的分析组件
        if hasattr(self, 'relm_analysis'):
            self.relm_analysis.on_activated()
        if hasattr(self, 'sfd_analysis'):
            self.sfd_analysis.on_activated()
        if hasattr(self, 'pfd_analysis'):
            self.pfd_analysis.on_activated()
        
        # 保留原有的module3_analysis支持（向后兼容）
        if hasattr(self, 'module3_analysis'):
            self.module3_analysis.on_activated()
        
        # 3D窗口居中显示
        self._center_3d_view()
        
    # 快速定位关键平面组件已移除，不再检查平面状态

    def on_deactivated(self):
        logging.info("模块三已停用")
        if hasattr(self, 'halt_analysis'):
            self.halt_analysis.on_deactivated()
        if hasattr(self, 'relm_analysis'):
            self.relm_analysis.on_deactivated()
        if hasattr(self, 'sfd_analysis'):
            self.sfd_analysis.on_deactivated()
        if hasattr(self, 'pfd_analysis'):
            self.pfd_analysis.on_deactivated()
        # 保留原有的module3_analysis支持（向后兼容）
        if hasattr(self, 'module3_analysis'):
            self.module3_analysis.on_deactivated()

    def _center_3d_view(self):
        """
        3D窗口居中显示功能
        """
        try:
            import slicer
            
            # 获取3D视图控制器并执行居中操作
            threeDWidget = slicer.app.layoutManager().threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.resetFocalPoint()
            
            logging.info("✅ 3D窗口已居中显示")
            print("🎯 3D窗口已居中显示")
            
        except Exception as e:
            error_message = f"3D窗口居中时出错: {e}"
            logging.error(error_message)
            print(f"❌ {error_message}")

    def _enable_mpr_crosshairs(self):
        """
        启用MPR交互式切片相交线功能
        
        根据 3D Slicer 交互式切片相交线功能开启方法，启用：
        - 切片相交线可见性
        - 交互式拖动
        - 平移
        - 旋转
        """
        try:
            import slicer
            
            # 获取 Application Logic
            appLogic = slicer.app.applicationLogic()
            if not appLogic:
                logging.error("无法获取 Application Logic")
                return False
            
            # 获取枚举标志位
            flag = slicer.vtkMRMLApplicationLogic
            
            # 启用各项功能
            logging.info("启用MPR交互式切片相交线功能...")
            
            # 开启切片相交线可见性
            appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesVisibility, True)
            logging.info("✅ 切片相交线可见性已启用")
            
            # 支持交互式拖动
            appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesInteractive, True)
            logging.info("✅ 交互式拖动已启用")
            
            # 支持平移
            appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesTranslation, True)
            logging.info("✅ 平移功能已启用")
            
            # 支持旋转
            appLogic.SetIntersectingSlicesEnabled(flag.IntersectingSlicesRotation, True)
            logging.info("✅ 旋转功能已启用")
            
            # 检查功能状态并输出
            states = {
                'Visibility': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesVisibility)),
                'Interactive': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesInteractive)),
                'Translation': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesTranslation)),
                'Rotation': bool(appLogic.GetIntersectingSlicesEnabled(flag.IntersectingSlicesRotation)),
            }
            
            logging.info(f"MPR Crosshairs 功能状态: {states}")
            
            # 在控制台也输出状态
            print("🎯 MPR Crosshairs 功能已启用:")
            for feature, enabled in states.items():
                status_icon = "✅" if enabled else "❌"
                print(f"  {status_icon} {feature}: {enabled}")
            
            return all(states.values())
            
        except Exception as e:
            error_message = f"启用MPR Crosshairs功能时出错: {e}"
            logging.error(error_message)
            print(f"❌ {error_message}")
            return False
    
    def cleanup(self):
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.cleanup()
        if hasattr(self, 'halt_analysis'):
            self.halt_analysis.cleanup()
        if hasattr(self, 'relm_analysis'):
            self.relm_analysis.cleanup()
        if hasattr(self, 'sfd_analysis'):
            self.sfd_analysis.cleanup()
        if hasattr(self, 'pfd_analysis'):
            self.pfd_analysis.cleanup()
        # 保留原有的module3_analysis支持（向后兼容）
        if hasattr(self, 'module3_analysis'):
            self.module3_analysis.cleanup()
        if self.logic:
            self.logic.cleanup()
        logging.info("模块三界面清理完成")
