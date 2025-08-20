"""
模块四界面组件

瓣膜支架几何形态评估界面。
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
    from .module4_logic import Module4Logic
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
    from module4_logic import Module4Logic


class Module4Widget(qt.QWidget):
    """模块四界面"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module4Logic()
        
        # 创建紧凑期像切换组件
        self.compact_phase_toggle = CompactPhaseToggle(session, self)
        self.compact_phase_toggle.phaseChanged.connect(self._on_phase_changed)
        
        self.setObjectName("Module4Widget")
        self._setup_ui()
        logging.info("Module4Widget 初始化完成")

    def _on_phase_changed(self, phase: str):
        """
        期像改变时的回调
        
        Args:
            phase: 新的期像 ('diastole' 或 'systole')
        """
        logging.info(f"模块四期像已切换到: {phase}")
        
        # 更新逻辑层的当前期像
        if self.logic:
            # 将期像格式转换为领域模型格式
            domain_phase = 'end_diastole' if phase == 'diastole' else 'end_systole'
            self.logic.set_current_phase(domain_phase)
        
        # 同步期像选择组件的状态
        self._sync_phase_widgets(phase)
    
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
    
    def _setup_ui(self):
        # 使用统一布局与样式体系，和其他模块保持一致
        main_layout = LayoutManager.create_layout(LayoutType.MODULE_CONTAINER, self)
        try:
            main_layout.setSizeConstraint(qt.QLayout.SetMinimumSize)
            self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
        except Exception:
            pass

        # 标题区 - 创建水平布局包含标题和期像切换器
        title_container = qt.QWidget()
        title_layout = qt.QHBoxLayout(title_container)
        title_layout.setContentsMargins(8, 8, 8, 8)
        title_layout.setSpacing(20)

        title = qt.QLabel("模块四：瓣膜支架几何形态评估")
        title.setAlignment(qt.Qt.AlignLeft | qt.Qt.AlignVCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        title_layout.addWidget(title)
        title_layout.addWidget(self.compact_phase_toggle)
        title_layout.addStretch()

        # 主要内容区域 - 暂时显示占位符内容
        content_frame = LayoutManager.create_section_frame("瓣膜支架几何形态分析")
        content_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, content_frame)
        
        # 占位符标签
        placeholder_label = qt.QLabel("模块四功能正在开发中...")
        placeholder_label.setAlignment(qt.Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 16px;
                font-style: italic;
                padding: 40px;
                border: 2px dashed #d1d5db;
                border-radius: 8px;
                background-color: #f9fafb;
            }
        """)
        content_layout.addWidget(placeholder_label)

        # 汇总布局（滚动在主界面 MainUI 中提供）
        main_layout.addWidget(title_container)
        main_layout.addWidget(content_frame)
        main_layout.addStretch()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.session = session
        if self.logic:
            # 如需使用session，可在后续逻辑中扩展
            pass

    def on_activated(self):
        logging.info("模块四已激活")
        
        # 启用MPR交互式切片相交线功能
        self._enable_mpr_crosshairs()
        
        # 设置默认期像到紧凑切换器并同步逻辑
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.set_current_phase('diastole')
        
        # 3D窗口居中显示
        self._center_3d_view()

    def on_deactivated(self):
        logging.info("模块四已停用")

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
        if self.logic:
            self.logic.cleanup()
        logging.info("模块四界面清理完成")