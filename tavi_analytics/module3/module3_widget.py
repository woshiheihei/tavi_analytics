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
        
        # 更新逻辑层的当前期像
        if self.logic:
            # 将期像格式转换为领域模型格式
            domain_phase = 'end_diastole' if phase == 'diastole' else 'end_systole'
            self.logic.set_current_phase(domain_phase)
        
        # 自动刷新平面状态以显示当前期像下的可用平面
        qt.QTimer.singleShot(100, self._on_refresh_plane_status)  # 延迟100ms刷新
    
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
            success = self.logic.switch_to_valve_stent_bottom_contour()
            
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
    
    def _on_switch_to_sinus_plane(self):
        """
        切换到SinusOfValsalva_Plane平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块三逻辑未初始化")
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
                qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 切换到SinusOfValsalva_Plane平面"))
            else:
                logging.error("切换到SinusOfValsalva_Plane平面失败")
                self.switch_to_sinus_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 切换到SinusOfValsalva_Plane平面"))
            
        except Exception as e:
            logging.error(f"切换到SinusOfValsalva_Plane平面时出错: {e}")
            self.switch_to_sinus_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_sinus_plane_btn.setText("🫀 切换到SinusOfValsalva_Plane平面"))
        finally:
            # 重新启用按钮
            self.switch_to_sinus_plane_btn.setEnabled(True)
    
    def _on_switch_to_stent_fit_plane(self):
        """
        切换到StentBestFit_Plane平面的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块三逻辑未初始化")
                return
            
            logging.info("开始切换到StentBestFit_Plane平面...")
            
            # 禁用按钮，防止重复点击
            self.switch_to_stent_fit_plane_btn.setEnabled(False)
            self.switch_to_stent_fit_plane_btn.setText("🔄 正在切换...")
            
            # 执行切换
            success = self.logic.switch_to_stent_best_fit_plane()
            
            if success:
                logging.info("成功切换到StentBestFit_Plane平面")
                self.switch_to_stent_fit_plane_btn.setText("✅ 切换完成")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_stent_fit_plane_btn.setText("🔧 切换到StentBestFit_Plane平面"))
            else:
                logging.error("切换到StentBestFit_Plane平面失败")
                self.switch_to_stent_fit_plane_btn.setText("❌ 切换失败")
                qt.QTimer.singleShot(2000, lambda: self.switch_to_stent_fit_plane_btn.setText("🔧 切换到StentBestFit_Plane平面"))
            
        except Exception as e:
            logging.error(f"切换到StentBestFit_Plane平面时出错: {e}")
            self.switch_to_stent_fit_plane_btn.setText("❌ 出错")
            qt.QTimer.singleShot(2000, lambda: self.switch_to_stent_fit_plane_btn.setText("🔧 切换到StentBestFit_Plane平面"))
        finally:
            # 重新启用按钮
            self.switch_to_stent_fit_plane_btn.setEnabled(True)
    
    def _on_refresh_plane_status(self):
        """
        刷新平面状态的回调方法
        """
        try:
            if not self.logic:
                logging.error("模块三逻辑未初始化")
                return
            
            # 获取当前期像
            current_phase = self.logic.get_current_phase()
            phase_display = {
                'end_diastole': '舒张末期',
                'end_systole': '收缩末期'
            }.get(current_phase, '未知期像')
            
            # 检查轮廓可用性
            availability = self.logic.check_contour_availability()
            
            # 构建状态文本
            status_lines = [f"📋 轮廓状态检查结果 (期像: {phase_display}):"]
            
            contour_names = {
                'valve_stent_bottom': 'ValveStent_Bottom_Contour (瓣膜支架底部轮廓)',
                'sinus_of_valsalva': 'SinusOfValsalva_Contour (窦部轮廓)',
                'stent_best_fit': 'StentBestFit_Contour (支架拟合轮廓)'
            }
            
            for contour_type, info in availability.items():
                if contour_type in contour_names:
                    contour_display_name = contour_names[contour_type]
                    if info.get('available', False):
                        status_icon = "✅"
                        extra_info = ""
                        if 'num_points' in info:
                            extra_info = f" ({info['num_points']}个点)"
                        # 显示期像感知的节点名称
                        if 'phase_aware_name' in info:
                            extra_info += f" [{info['phase_aware_name']}]"
                        status_lines.append(f"{status_icon} {contour_display_name}{extra_info}")
                    else:
                        status_icon = "❌"
                        # 显示期像感知的节点名称（如果有）
                        missing_name = info.get('phase_aware_name', info.get('base_name', ''))
                        status_lines.append(f"{status_icon} {contour_display_name} - 未找到 [{missing_name}]")
            
            # 更新状态显示
            status_text = "\n".join(status_lines)
            self.plane_status_label.setText(status_text)
            
            # 根据状态启用/禁用按钮
            self._update_button_states(availability)
            
        except Exception as e:
            logging.error(f"刷新平面状态时出错: {e}")
            self.plane_status_label.setText("❌ 检查平面状态时出错")
    
    def _update_button_states(self, availability):
        """
        根据平面可用性更新按钮状态
        
        Args:
            availability: 平面可用性字典
        """
        try:
            # 更新瓣膜支架底部平面按钮
            if 'valve_stent_bottom' in availability:
                is_available = availability['valve_stent_bottom'].get('available', False)
                self.switch_to_valve_plane_btn.setEnabled(is_available)
                if not is_available:
                    self.switch_to_valve_plane_btn.setToolTip("当前期像下该平面不可用")
                else:
                    self.switch_to_valve_plane_btn.setToolTip("切换到瓣膜支架底部平面")
            
            # 更新Sinus Of Valsalva平面按钮
            if 'sinus_of_valsalva' in availability:
                is_available = availability['sinus_of_valsalva'].get('available', False)
                self.switch_to_sinus_plane_btn.setEnabled(is_available)
                if not is_available:
                    self.switch_to_sinus_plane_btn.setToolTip("当前期像下该平面不可用")
                else:
                    self.switch_to_sinus_plane_btn.setToolTip("切换到Sinus Of Valsalva平面")
            
            # 更新支架最佳拟合平面按钮
            if 'stent_best_fit' in availability:
                is_available = availability['stent_best_fit'].get('available', False)
                self.switch_to_stent_fit_plane_btn.setEnabled(is_available)
                if not is_available:
                    self.switch_to_stent_fit_plane_btn.setToolTip("当前期像下该平面不可用")
                else:
                    self.switch_to_stent_fit_plane_btn.setToolTip("切换到支架最佳拟合平面")
            
        except Exception as e:
            logging.error(f"更新按钮状态时出错: {e}")
    
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
            "点击下方按钮将当前MPR视图切换到对应的关键平面。\n"
            "轴状面将切换到该平面，矢状面和冠状面与之垂直相交。"
        )
        plane_info.setWordWrap(True)
        plane_info.setStyleSheet(StyleManager.get_label_style("info"))
        
        # 创建按钮网格布局
        buttons_widget = qt.QWidget()
        buttons_layout = qt.QGridLayout(buttons_widget)
        buttons_layout.setSpacing(10)
        
        # 瓣膜支架底部平面按钮
        self.switch_to_valve_plane_btn = LayoutManager.create_button_with_style(
            "🎯 切换到ValveStent_Bottom_Plane平面", 
            "primary", 
            "default", 
            45
        )
        self.switch_to_valve_plane_btn.clicked.connect(self._on_switch_to_valve_plane)
        
        # Sinus Of Valsalva平面按钮
        self.switch_to_sinus_plane_btn = LayoutManager.create_button_with_style(
            "🫀 切换到SinusOfValsalva_Plane平面", 
            "secondary", 
            "default", 
            45
        )
        self.switch_to_sinus_plane_btn.clicked.connect(self._on_switch_to_sinus_plane)
        
        # 支架最佳拟合平面按钮
        self.switch_to_stent_fit_plane_btn = LayoutManager.create_button_with_style(
            "🔧 切换到StentBestFit_Plane平面", 
            "accent", 
            "default", 
            45
        )
        self.switch_to_stent_fit_plane_btn.clicked.connect(self._on_switch_to_stent_fit_plane)
        
        # 排列按钮（2行3列或3行1列，根据空间调整）
        buttons_layout.addWidget(self.switch_to_valve_plane_btn, 0, 0)
        buttons_layout.addWidget(self.switch_to_sinus_plane_btn, 0, 1)
        buttons_layout.addWidget(self.switch_to_stent_fit_plane_btn, 1, 0, 1, 2)  # 占两列
        
        # 组装平面控制区域
        plane_control_layout.addWidget(plane_info)
        plane_control_layout.addWidget(buttons_widget)
        
        # 添加平面状态显示区域
        self.plane_status_label = qt.QLabel("🔍 检查平面状态...")
        self.plane_status_label.setWordWrap(True)
        self.plane_status_label.setStyleSheet(StyleManager.get_label_style("info"))
        plane_control_layout.addWidget(self.plane_status_label)
        
        # 添加刷新状态按钮
        self.refresh_status_btn = LayoutManager.create_button_with_style(
            "🔄 检查平面状态", 
            "info", 
            "small", 
            30
        )
        self.refresh_status_btn.clicked.connect(self._on_refresh_plane_status)
        plane_control_layout.addWidget(self.refresh_status_btn)

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
        
        # 自动检查平面状态
        qt.QTimer.singleShot(500, self._on_refresh_plane_status)  # 延迟500ms执行，确保UI完全加载

    def on_deactivated(self):
        logging.info("模块三已停用")

    def cleanup(self):
        if hasattr(self, 'phase_selection'):
            self.phase_selection.cleanup()
        if self.logic:
            self.logic.cleanup()
        logging.info("模块三界面清理完成")
