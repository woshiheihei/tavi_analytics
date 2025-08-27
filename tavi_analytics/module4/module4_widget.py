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
    from .geometry_analysis_widget import InflowAnalysisWidget, NadirAnalysisWidget, CommissureLevelAnalysisWidget
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
    from geometry_analysis_widget import InflowAnalysisWidget, NadirAnalysisWidget, CommissureLevelAnalysisWidget


class Module4Widget(qt.QWidget):
    """模块四界面"""

    def __init__(self, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module4Logic(session)
        
        # 创建紧凑期像切换组件
        self.compact_phase_toggle = CompactPhaseToggle(session, self)
        self.compact_phase_toggle.phaseChanged.connect(self._on_phase_changed)
        
        # 创建几何形态分析组件，传入逻辑组件
        self.inflow_analysis = InflowAnalysisWidget(session, self.logic, parent=self)
        self.nadir_analysis = NadirAnalysisWidget(session, self.logic, parent=self)
        self.commissure_level_analysis = CommissureLevelAnalysisWidget(session, self.logic, parent=self)
        
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
    
    def _on_switch_to_valve_plane(self):
        """
        切换到ValveStent_Bottom_Plane平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块四逻辑未初始化")
                return
            
            logging.info("开始切换到ValveStent_Bottom_Plane平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_valve_plane_btn.setEnabled(False)
            self.switch_to_valve_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_valve_stent_bottom_contour()
            
            if success:
                logging.info("成功切换到ValveStent_Bottom_Plane平面")
                self.switch_to_valve_plane_btn.setText("✅ 切换完成")
                # 2秒后恢复按钮文本
                qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 瓣膜支架底部平面"))
            else:
                logging.error("切换到ValveStent_Bottom_Plane平面失败")
                self.switch_to_valve_plane_btn.setText("❌ 切换失败")
                # 2秒后恢复按钮文本
                qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 瓣膜支架底部平面"))
            
        except Exception as e:
            logging.error(f"切换到ValveStent_Bottom_Plane平面时出错: {e}")
            self.switch_to_valve_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_valve_plane_btn.setText("🎯 瓣膜支架底部平面"))
        finally:
            # 重新启用按钮
            self.switch_to_valve_plane_btn.setEnabled(True)
    
    def _on_switch_to_sinus_plane(self):
        """
        切换到SinusOfValsalva_Plane平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块四逻辑未初始化")
                return
            
            logging.info("开始切换到SinusOfValsalva_Plane平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_sinus_plane_btn.setEnabled(False)
            self.switch_to_sinus_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_sinus_of_valsalva_plane()
            
            if success:
                logging.info("成功切换到SinusOfValsalva_Plane平面")
                self.switch_to_sinus_plane_btn.setText("✅ 切换完成")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 瓦氏窦平面"))
            else:
                logging.error("切换到SinusOfValsalva_Plane平面失败")
                self.switch_to_sinus_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 瓦氏窦平面"))
            
        except Exception as e:
            logging.error(f"切换到SinusOfValsalva_Plane平面时出错: {e}")
            self.switch_to_sinus_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 瓦氏窦平面"))
        finally:
            # 重新启用按钮
            self.switch_to_sinus_plane_btn.setEnabled(True)
    
    def _on_switch_to_inflow_plane(self):
        """
        切换到Inflow平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块四逻辑未初始化")
                return
            
            logging.info("开始切换到Inflow平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_inflow_plane_btn.setEnabled(False)
            self.switch_to_inflow_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_level_plane('inflow')
            
            if success:
                logging.info("成功切换到Inflow平面")
                self.switch_to_inflow_plane_btn.setText("✅ 切换完成")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_inflow_plane_btn.setText("⬆️ Inflow 平面"))
            else:
                logging.error("切换到Inflow平面失败")
                self.switch_to_inflow_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_inflow_plane_btn.setText("⬆️ Inflow 平面"))
            
        except Exception as e:
            logging.error(f"切换到Inflow平面时出错: {e}")
            self.switch_to_inflow_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_inflow_plane_btn.setText("⬆️ Inflow 平面"))
        finally:
            # 重新启用按钮
            self.switch_to_inflow_plane_btn.setEnabled(True)
    
    def _on_switch_to_nadir_plane(self):
        """
        切换到Nadir平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块四逻辑未初始化")
                return
            
            logging.info("开始切换到Nadir平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_nadir_plane_btn.setEnabled(False)
            self.switch_to_nadir_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_level_plane('nadir')
            
            if success:
                logging.info("成功切换到Nadir平面")
                self.switch_to_nadir_plane_btn.setText("✅ 切换完成")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_nadir_plane_btn.setText("🔽 Nadir 平面"))
            else:
                logging.error("切换到Nadir平面失败")
                self.switch_to_nadir_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_nadir_plane_btn.setText("🔽 Nadir 平面"))
            
        except Exception as e:
            logging.error(f"切换到Nadir平面时出错: {e}")
            self.switch_to_nadir_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_nadir_plane_btn.setText("🔽 Nadir 平面"))
        finally:
            # 重新启用按钮
            self.switch_to_nadir_plane_btn.setEnabled(True)
    
    def _on_switch_to_commissure_plane(self):
        """
        切换到Commissure Level平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块四逻辑未初始化")
                return
            
            logging.info("开始切换到Commissure Level平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_commissure_plane_btn.setEnabled(False)
            self.switch_to_commissure_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_level_plane('commissure_level')
            
            if success:
                logging.info("成功切换到Commissure Level平面")
                self.switch_to_commissure_plane_btn.setText("✅ 切换完成")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_commissure_plane_btn.setText("⚡ Commissure Level 平面"))
            else:
                logging.error("切换到Commissure Level平面失败")
                self.switch_to_commissure_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_commissure_plane_btn.setText("⚡ Commissure Level 平面"))
            
        except Exception as e:
            logging.error(f"切换到Commissure Level平面时出错: {e}")
            self.switch_to_commissure_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_commissure_plane_btn.setText("⚡ Commissure Level 平面"))
        finally:
            # 重新启用按钮
            self.switch_to_commissure_plane_btn.setEnabled(True)
    
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

        # 平面切换控制区域
        plane_control_frame = LayoutManager.create_section_frame("快速定位关键平面")
        plane_control_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, plane_control_frame)
        buttons_widget = qt.QWidget()
        buttons_layout = qt.QGridLayout(buttons_widget)
        buttons_layout.setSpacing(10)

        # 创建定位平面按钮
        self.switch_to_valve_plane_btn = LayoutManager.create_button_with_style(
            "🎯 瓣膜支架底部平面", "primary", "default", 45
        )
        self.switch_to_valve_plane_btn.clicked.connect(self._on_switch_to_valve_plane)

        self.switch_to_sinus_plane_btn = LayoutManager.create_button_with_style(
            "🫀 瓦氏窦平面", "secondary", "default", 45
        )
        self.switch_to_sinus_plane_btn.clicked.connect(self._on_switch_to_sinus_plane)

        self.switch_to_inflow_plane_btn = LayoutManager.create_button_with_style(
            "⬆️ Inflow 平面", "secondary", "default", 45
        )
        self.switch_to_inflow_plane_btn.clicked.connect(self._on_switch_to_inflow_plane)

        self.switch_to_nadir_plane_btn = LayoutManager.create_button_with_style(
            "🔽 Nadir 平面", "secondary", "default", 45
        )
        self.switch_to_nadir_plane_btn.clicked.connect(self._on_switch_to_nadir_plane)

        self.switch_to_commissure_plane_btn = LayoutManager.create_button_with_style(
            "⚡ Commissure Level 平面", "secondary", "default", 45
        )
        self.switch_to_commissure_plane_btn.clicked.connect(self._on_switch_to_commissure_plane)

        buttons_layout.addWidget(self.switch_to_valve_plane_btn, 0, 0)
        buttons_layout.addWidget(self.switch_to_sinus_plane_btn, 0, 1)
        buttons_layout.addWidget(self.switch_to_inflow_plane_btn, 1, 0)
        buttons_layout.addWidget(self.switch_to_nadir_plane_btn, 1, 1)
        buttons_layout.addWidget(self.switch_to_commissure_plane_btn, 2, 0, 1, 2)  # 跨两列
        plane_control_layout.addWidget(buttons_widget)

        # 分析区域 - 选项卡（去除外层"瓣膜支架几何形态分析"Section，直接使用Tab）
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
        self.analysis_tabs.addTab(self.inflow_analysis, "Inflow")
        self.analysis_tabs.addTab(self.nadir_analysis, "Nadir")
        self.analysis_tabs.addTab(self.commissure_level_analysis, "Commissure Level")

        # 汇总布局（滚动在主界面 MainUI 中提供）
        main_layout.addWidget(title_container)
        # 平面控制区域
        main_layout.addWidget(plane_control_frame)
        # 直接将选项卡添加到主布局
        main_layout.addWidget(self.analysis_tabs)
        main_layout.addStretch()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        if hasattr(self, 'compact_phase_toggle'):
            self.compact_phase_toggle.session = session
        if hasattr(self, 'inflow_analysis'):
            self.inflow_analysis.set_session(session)
        if hasattr(self, 'nadir_analysis'):
            self.nadir_analysis.set_session(session)
        if hasattr(self, 'commissure_level_analysis'):
            self.commissure_level_analysis.set_session(session)
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
        
        # 激活几何形态分析组件
        if hasattr(self, 'inflow_analysis'):
            self.inflow_analysis.on_activated()
        if hasattr(self, 'nadir_analysis'):
            self.nadir_analysis.on_activated()
        if hasattr(self, 'commissure_level_analysis'):
            self.commissure_level_analysis.on_activated()
        
        # 3D窗口居中显示
        self._center_3d_view()

    def on_deactivated(self):
        logging.info("模块四已停用")
        if hasattr(self, 'inflow_analysis'):
            self.inflow_analysis.on_deactivated()
        if hasattr(self, 'nadir_analysis'):
            self.nadir_analysis.on_deactivated()
        if hasattr(self, 'commissure_level_analysis'):
            self.commissure_level_analysis.on_deactivated()

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
        if hasattr(self, 'inflow_analysis'):
            self.inflow_analysis.cleanup()
        if hasattr(self, 'nadir_analysis'):
            self.nadir_analysis.cleanup()
        if hasattr(self, 'commissure_level_analysis'):
            self.commissure_level_analysis.cleanup()
        if self.logic:
            self.logic.cleanup()
        logging.info("模块四界面清理完成")