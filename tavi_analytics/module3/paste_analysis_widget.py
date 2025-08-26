"""
模块三分析界面组件

瓣叶功能评估相关分析的标准化用户界面框架，包含：
- RELM (瓣叶活动度减退) 分析界面占位符
- SFD (窦内充盈缺损) 分析界面占位符  
- PFD (瓣叶下充盈缺损) 分析界面占位符

注意：HALT分析有独立的实现 (halt_analysis_widget.py)
"""
import logging
from typing import Optional, Dict, Any
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.key_view_manager_widget import KeyViewManagerWidget  # 导入关键视图组件
    from ..services.contour_positioning_service import get_contour_position_service  # 轮廓定位服务
    from .paste_analysis_logic import Module3AnalysisLogic, RelmAnalysisLogic, SfdAnalysisLogic, PfdAnalysisLogic
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
    from widgets.key_view_manager_widget import KeyViewManagerWidget  # 导入关键视图组件
    from services.contour_positioning_service import get_contour_position_service  # 轮廓定位服务
    from paste_analysis_logic import Module3AnalysisLogic, RelmAnalysisLogic, SfdAnalysisLogic, PfdAnalysisLogic



class BaseAnalysisWidget(qt.QWidget):
    """分析界面基类 - 标准化接口"""
    
    # 状态改变信号
    statusChanged = qt.Signal(dict)
    
    def __init__(self, analysis_type: str, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.session = session
        self.setObjectName(f"{analysis_type}AnalysisWidget")
        logging.info(f"{analysis_type}分析界面初始化")
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果 - 子类应该实现"""
        return {'analysis_type': self.analysis_type, 'status': '基类默认实现'}
    
    def reset_analysis(self):
        """重置分析 - 子类应该实现"""
        logging.info(f"{self.analysis_type}分析重置 - 基类默认实现")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
    
    def on_activated(self):
        """激活时的回调"""
        logging.info(f"{self.analysis_type}分析界面激活")
    
    def on_deactivated(self):
        """停用时的回调"""
        logging.info(f"{self.analysis_type}分析界面停用")
    
    def cleanup(self):
        """清理资源"""
        logging.info(f"{self.analysis_type}分析界面清理完成")
    
    def _emit_status_changed(self):
        """发出状态改变信号"""
        results = self.get_analysis_results()
        self.statusChanged.emit(results)


class RelmAnalysisWidget(BaseAnalysisWidget):
    """RELM (瓣叶活动度减退) 分析界面占位符"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[RelmAnalysisLogic] = None, parent=None):
        super().__init__("RELM", session, parent)
        self.logic = logic or RelmAnalysisLogic()
        self.logic.set_session(session)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置RELM分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("RELM 瓣叶活动度减退分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #e8f4f8;
                padding: 6px 12px;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 占位符内容区域
        content_frame = qt.QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
            }
        """)
        
        content_layout = qt.QVBoxLayout(content_frame)
        content_layout.setSpacing(10)
        
        # 瓣叶选择
        leaflet_layout = qt.QHBoxLayout()
        leaflet_label = qt.QLabel("瓣叶选择:")
        leaflet_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.leaflet_combo = qt.QComboBox()
        self.leaflet_combo.addItems(["请选择瓣叶...", "LC", "RC", "NC"])
        self.leaflet_combo.currentTextChanged.connect(self._on_leaflet_changed)
        
        leaflet_layout.addWidget(leaflet_label)
        leaflet_layout.addWidget(self.leaflet_combo)
        leaflet_layout.addStretch()
        content_layout.addLayout(leaflet_layout)
        
        
        main_layout.addWidget(content_frame)
        
        # 关键视图管理 - 新增
        self._create_key_view_section(main_layout)
        
        # 操作按钮
        self._create_action_buttons(main_layout)
    
    def _create_action_buttons(self, parent_layout):
        """创建操作按钮"""
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 重置按钮
        reset_btn = qt.QPushButton("重置分析")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_btn.clicked.connect(self.reset_analysis)
        
        # 状态按钮
        status_btn = qt.QPushButton("查看状态")
        status_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        status_btn.clicked.connect(self._show_status)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(status_btn)
        
        parent_layout.addLayout(buttons_layout)
    
    def _on_leaflet_changed(self, leaflet: str):
        """瓣叶选择改变时的回调"""
        if leaflet and not leaflet.startswith("请选择"):
            self.logic.set_leaflet(leaflet)
            self._emit_status_changed()
            logging.info(f"RELM分析选择瓣叶: {leaflet}")
    
    def _show_status(self):
        """显示当前状态"""
        results = self.get_analysis_results()
        status_text = f"分析类型: {results['analysis_type']}\\n"
        status_text += f"状态: {results['status']}\\n"
        status_text += f"当前瓣叶: {results.get('leaflet', '未选择')}\\n"
        status_text += f"占位符: {results.get('placeholder', False)}"
        
        qt.QMessageBox.information(self, "RELM分析状态", status_text)
    
    def _create_key_view_section(self, parent_layout):
        """创建关键视图管理区域"""
        # 创建关键视图管理器组件
        self.key_view_manager = KeyViewManagerWidget(
            analysis_type="RELM",
            session=self.session,
            compact_mode=True,  # 使用紧凑模式
            parent=self
        )
        
        # 连接信号
        self.key_view_manager.viewMarked.connect(self._on_view_marked)
        self.key_view_manager.viewRestored.connect(self._on_view_restored)
        self.key_view_manager.viewDeleted.connect(self._on_view_deleted)
        self.key_view_manager.statusUpdated.connect(self._on_view_status_updated)
        
        parent_layout.addWidget(self.key_view_manager)
    
    def _on_view_marked(self, view_name: str):
        """视图被标记时的回调"""
        logging.info(f"RELM分析 - 视图已标记: {view_name}")
    
    def _on_view_restored(self, view_name: str):
        """视图被恢复时的回调"""
        logging.info(f"RELM分析 - 视图已恢复: {view_name}")
    
    def _on_view_deleted(self, view_name: str):
        """视图被删除时的回调"""
        logging.info(f"RELM分析 - 视图已删除: {view_name}")
    
    def _on_view_status_updated(self, status: str):
        """关键视图状态更新时的回调"""
        logging.debug(f"RELM分析 - 关键视图状态: {status}")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        super().set_session(session)
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.set_session(session)
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.cleanup()
        super().cleanup()
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取RELM分析结果"""
        results = self.logic.get_analysis_results()
        
        # 添加关键视图统计
        if hasattr(self, 'key_view_manager'):
            results['key_views_count'] = self.key_view_manager.get_marked_views_count()
            results['key_view_names'] = self.key_view_manager.get_marked_view_names()
        
        return results
    
    def reset_analysis(self):
        """重置RELM分析"""
        self.logic.reset_analysis()
        self.leaflet_combo.setCurrentIndex(0)
        self._emit_status_changed()
        logging.info("RELM分析已重置")


class SfdAnalysisWidget(BaseAnalysisWidget):
    """SFD (窦内充盈缺损) 分析界面占位符"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[SfdAnalysisLogic] = None, parent=None):
        super().__init__("SFD", session, parent)
        self.logic = logic or SfdAnalysisLogic()
        self.logic.set_session(session)
        
        # 服务组件
        self.contour_service = get_contour_position_service()
        
        # 分析状态
        self.analysis_started = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置SFD分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("SFD 窦内充盈缺损分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #fff3cd;
                padding: 6px 12px;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 分析控制区域（开始SFD分析）
        self._create_analysis_control_section(main_layout)
        
        # 占位符内容区域
        content_frame = qt.QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
            }
        """)
        
        content_layout = qt.QVBoxLayout(content_frame)
        content_layout.setSpacing(10)
        
        # SFD状态选择 - 参考HALT样式
        status_title = qt.QLabel("1. SFD状态")
        status_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        content_layout.addWidget(status_title)
        
        # 选项按钮 - 使用HALT的样式布局
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(6)
        
        self.status_group = qt.QButtonGroup()
        
        # 样式定义 - 参考HALT的颜色配置
        button_configs = [
            ("无", "#d4f6d4", "#28a745"),
            ("有", "#fdeaea", "#dc3545"),
            ("难以判定", "#fff8dc", "#ffc107")
        ]
        
        self.status_buttons = {}
        for i, (status, bg_color, border_color) in enumerate(button_configs):
            button = qt.QRadioButton(status)
            button.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 12px;
                    margin: 1px;
                    background-color: {bg_color};
                    border: 2px solid {bg_color};
                    border-radius: 4px;
                }}
                QRadioButton:checked {{
                    border: 2px solid {border_color};
                    font-weight: bold;
                    background-color: white;
                }}
                QRadioButton:hover {{
                    border: 2px solid {border_color};
                }}
            """)
            
            self.status_group.addButton(button, i)
            self.status_buttons[status] = button
            buttons_layout.addWidget(button)
        
        # 默认选择"无"
        self.status_buttons["无"].setChecked(True)
        
        # 连接信号
        self.status_group.buttonClicked.connect(self._on_status_changed)
        
        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout)
        
        # 受累主动脉窦选择（条件显示）
        self._create_sinus_selection_section(content_layout)
        
        main_layout.addWidget(content_frame)
        
        # 关键视图管理 - 新增
        self._create_key_view_section(main_layout)
        
        # 操作按钮
        self._create_action_buttons(main_layout)
    
    def _create_action_buttons(self, parent_layout):
        """创建操作按钮"""
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 重置按钮
        reset_btn = qt.QPushButton("重置分析")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_btn.clicked.connect(self.reset_analysis)
        
        # 状态按钮
        status_btn = qt.QPushButton("查看状态")
        status_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        status_btn.clicked.connect(self._show_status)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(status_btn)
        
        parent_layout.addLayout(buttons_layout)
    
    def _on_status_changed(self, button):
        """SFD状态改变时的回调"""
        button_id = self.status_group.id(button)
        status_map = {0: 'none', 1: 'present', 2: 'indeterminate'}
        status = status_map.get(button_id, 'none')
        
        # 控制受累主动脉窦选择区域的可见性
        has_sfd = status == 'present'
        if hasattr(self, 'sinus_widget'):
            self.sinus_widget.setVisible(has_sfd)
            
            # 如果状态变为"无"或"难以判定"，重置所有窦部选择
            if not has_sfd:
                self.affected_sinuses.clear()
                if hasattr(self, 'sinus_checkboxes'):
                    for checkbox in self.sinus_checkboxes.values():
                        checkbox.setChecked(False)
        
        self.logic.set_status(status)
        if hasattr(self, 'affected_sinuses'):
            self.logic.set_affected_sinuses(list(self.affected_sinuses))
        self._emit_status_changed()
        logging.info(f"SFD状态设置为: {status}")
    
    def _on_sinus_selection_changed(self, sinus_name: str, is_selected: bool):
        """主动脉窦选择改变时的回调"""
        if is_selected:
            self.affected_sinuses.add(sinus_name)
        else:
            self.affected_sinuses.discard(sinus_name)
        
        # 更新逻辑层的受累窦部数据
        self.logic.set_affected_sinuses(list(self.affected_sinuses))
        self._emit_status_changed()
        logging.info(f"SFD受累主动脉窦更新: {list(self.affected_sinuses)}")
    
    def _show_status(self):
        """显示当前状态"""
        results = self.get_analysis_results()
        status_text = f"分析类型: {results['analysis_type']}\\n"
        status_text += f"状态: {results['status']}\\n"
        status_text += f"受累窦部: {', '.join(results.get('affected_sinuses', []))  or '无'}\\n"
        status_text += f"占位符: {results.get('placeholder', False)}"
        
        qt.QMessageBox.information(self, "SFD分析状态", status_text)
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域（仅保留开始按钮）"""
        self.control_frame = qt.QFrame()
        self.control_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        control_layout = qt.QHBoxLayout(self.control_frame)
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(6, 6, 6, 6)
        
        # 开始分析按钮
        self.start_analysis_btn = qt.QPushButton("开始分析")
        self.start_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        
        control_layout.addStretch()
        parent_layout.addWidget(self.control_frame)
    
    def _create_sinus_selection_section(self, parent_layout):
        """创建受累主动脉窦选择区域 - 与SFD状态选择风格一致"""
        # 标题 - 与SFD状态选择保持一致的样式
        sinus_title = qt.QLabel("2. 受累主动脉窦")
        sinus_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        
        # 选项按钮 - 使用与SFD状态选择相同的样式
        sinus_buttons_layout = qt.QHBoxLayout()
        sinus_buttons_layout.setSpacing(6)
        
        # 复选框组 - 使用一致的样式
        self.sinus_checkboxes = {}
        self.affected_sinuses = set()  # 跟踪受累的窦部
        
        # 为每个窦部使用统一的背景色（使用中性色调）
        sinus_bg_color = "#f8f9fa"
        sinus_border_color = "#007bff"
        
        for sinus_name in ["LC", "RC", "NC"]:  # 左、右、无冠状窦
            checkbox = qt.QCheckBox(sinus_name)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 12px;
                    margin: 1px;
                    background-color: {sinus_bg_color};
                    border: 2px solid {sinus_bg_color};
                    border-radius: 4px;
                }}
                QCheckBox:checked {{
                    border: 2px solid {sinus_border_color};
                    font-weight: bold;
                    background-color: white;
                }}
                QCheckBox:hover {{
                    border: 2px solid {sinus_border_color};
                }}
            """)
            checkbox.stateChanged.connect(lambda state, name=sinus_name: self._on_sinus_selection_changed(name, state == qt.Qt.Checked))
            self.sinus_checkboxes[sinus_name] = checkbox
            sinus_buttons_layout.addWidget(checkbox)
        
        sinus_buttons_layout.addStretch()
        
        # 创建容器widget，以便控制可见性
        self.sinus_widget = qt.QWidget()
        sinus_widget_layout = qt.QVBoxLayout(self.sinus_widget)
        sinus_widget_layout.setContentsMargins(0, 0, 0, 0)
        sinus_widget_layout.setSpacing(6)
        sinus_widget_layout.addWidget(sinus_title)
        sinus_widget_layout.addLayout(sinus_buttons_layout)
        
        self.sinus_widget.setVisible(False)  # 默认隐藏
        
        parent_layout.addWidget(self.sinus_widget)
    
    def _on_start_analysis(self):
        """开始SFD分析"""
        try:
            logging.info("用户开始SFD分析")
            
            # 禁用开始按钮，避免重复点击
            self.start_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 1. 切换到收缩末期
            qt.QApplication.processEvents()
            
            # 检查是否有收缩末期标记
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info or end_systole_info.get('frame_index') is None:
                qt.QMessageBox.warning(
                    self,
                    "警告",
                    "未找到收缩末期标记！\n\n"
                    "请先在模块一中标记收缩末期时相。"
                )
                self._reset_analysis_buttons()
                return
            
            # 切换到收缩末期
            success = self._switch_to_end_systole()
            if not success:
                qt.QMessageBox.warning(
                    self,
                    "错误",
                    "切换到收缩末期失败！请检查模块一中的期像标记。"
                )
                self._reset_analysis_buttons()
                return
            
            # 2. MPR定位到瓦氏窦平面
            qt.QApplication.processEvents()
            
            success = self._position_to_sinus_valsalva()
            if not success:
                qt.QMessageBox.information(
                    self,
                    "提示",
                    "自动定位失败，请手动调整MPR视图到合适位置。\n分析可以继续进行。"
                )
            
            # 3. 完成准备
            self._complete_analysis_preparation()
            
            logging.info("SFD分析环境准备完成")
            
        except Exception as e:
            logging.error(f"开始SFD分析失败: {e}")
            qt.QMessageBox.critical(
                self,
                "错误", 
                f"分析启动失败：\n{e}"
            )
            self._reset_analysis_buttons()
    
    def _complete_analysis_preparation(self):
        """完成分析准备"""
        self.analysis_started = True
        
        # 隐藏分析控制区域
        self.control_frame.setVisible(False)
        
        logging.info("SFD分析准备完成")
    
    def _reset_analysis_buttons(self):
        """重置分析按钮状态"""
        self.start_analysis_btn.setEnabled(True)
    
    def _switch_to_end_systole(self) -> bool:
        """切换到收缩末期 - 使用集中化期像管理服务"""
        try:
            # 使用session的期像管理服务进行切换
            success = self.session.switch_to_systole("SFD_Analysis")
            
            if success:
                # 同步更新轮廓服务的期像设置
                self.contour_service.set_current_phase('end_systole')
                
                logging.info("成功切换到收缩末期（使用期像管理服务）")
                return True
            else:
                logging.error("使用期像管理服务切换到收缩末期失败")
                return False
            
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False
    
    def _position_to_sinus_valsalva(self) -> bool:
        """MPR定位到瓦氏窦平面"""
        try:
            # 尝试使用轮廓定位服务
            success = self.contour_service.switch_to_contour('sinus_of_valsalva', phase='end_systole')
            
            if success:
                logging.info("成功定位到瓦氏窦平面")
                return True
            else:
                logging.warning("定位到瓦氏窦平面失败，但分析可以继续")
                return False
            
        except Exception as e:
            logging.error(f"定位到瓦氏窦平面失败: {e}")
            return False
    
    def _create_key_view_section(self, parent_layout):
        """创建关键视图管理区域"""
        # 创建关键视图管理器组件
        self.key_view_manager = KeyViewManagerWidget(
            analysis_type="SFD",
            session=self.session,
            compact_mode=True,  # 使用紧凑模式
            parent=self
        )
        
        # 连接信号
        self.key_view_manager.viewMarked.connect(self._on_view_marked)
        self.key_view_manager.viewRestored.connect(self._on_view_restored)
        self.key_view_manager.viewDeleted.connect(self._on_view_deleted)
        self.key_view_manager.statusUpdated.connect(self._on_view_status_updated)
        
        parent_layout.addWidget(self.key_view_manager)
    
    def _on_view_marked(self, view_name: str):
        """视图被标记时的回调"""
        logging.info(f"SFD分析 - 视图已标记: {view_name}")
    
    def _on_view_restored(self, view_name: str):
        """视图被恢复时的回调"""
        logging.info(f"SFD分析 - 视图已恢复: {view_name}")
    
    def _on_view_deleted(self, view_name: str):
        """视图被删除时的回调"""
        logging.info(f"SFD分析 - 视图已删除: {view_name}")
    
    def _on_view_status_updated(self, status: str):
        """关键视图状态更新时的回调"""
        logging.debug(f"SFD分析 - 关键视图状态: {status}")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        super().set_session(session)
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.set_session(session)
    
    def cleanup(self):
        """清理资源"""
        # 清理关键视图管理器
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.cleanup()
        super().cleanup()
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取SFD分析结果"""
        results = self.logic.get_analysis_results()
        
        # 添加关键视图统计
        if hasattr(self, 'key_view_manager'):
            results['key_views_count'] = self.key_view_manager.get_marked_views_count()
            results['key_view_names'] = self.key_view_manager.get_marked_view_names()
        
        return results
    
    def reset_analysis(self):
        """重置SFD分析"""
        # 重置分析状态
        self.analysis_started = False
        
        # 重置分析控制区域
        if hasattr(self, 'control_frame'):
            self.control_frame.setVisible(True)
            self.start_analysis_btn.setEnabled(True)
        
        # 重置逻辑状态
        self.logic.reset_analysis()
        self.status_buttons["无"].setChecked(True)
        
        # 重置受累主动脉窦选择
        if hasattr(self, 'affected_sinuses'):
            self.affected_sinuses.clear()
        if hasattr(self, 'sinus_checkboxes'):
            for checkbox in self.sinus_checkboxes.values():
                checkbox.setChecked(False)
        if hasattr(self, 'sinus_widget'):
            self.sinus_widget.setVisible(False)
        
        self._emit_status_changed()
        logging.info("SFD分析已重置")


class PfdAnalysisWidget(BaseAnalysisWidget):
    """PFD (瓣叶下充盈缺损) 分析界面占位符"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[PfdAnalysisLogic] = None, parent=None):
        super().__init__("PFD", session, parent)
        self.logic = logic or PfdAnalysisLogic()
        self.logic.set_session(session)
        
        # 服务组件
        self.contour_service = get_contour_position_service()
        
        # 分析状态
        self.analysis_started = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置PFD分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("PFD 瓣叶下充盈缺损分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #fdeaea;
                padding: 6px 12px;
                border: 1px solid #fadbd8;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 分析控制区域（开始PFD分析）
        self._create_analysis_control_section(main_layout)
        
        # 占位符内容区域
        content_frame = qt.QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
            }
        """)
        
        content_layout = qt.QVBoxLayout(content_frame)
        content_layout.setSpacing(10)
        
        # PFD状态选择 - 参考SFD样式
        status_title = qt.QLabel("1. PFD状态")
        status_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        content_layout.addWidget(status_title)
        
        # 选项按钮 - 使用SFD的样式布局
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(6)
        
        self.status_group = qt.QButtonGroup()
        
        # 样式定义 - 参考SFD的颜色配置
        button_configs = [
            ("无", "#d4f6d4", "#28a745"),
            ("有", "#fdeaea", "#dc3545"),
            ("难以判定", "#fff8dc", "#ffc107")
        ]
        
        self.status_buttons = {}
        for i, (status, bg_color, border_color) in enumerate(button_configs):
            button = qt.QRadioButton(status)
            button.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 12px;
                    margin: 1px;
                    background-color: {bg_color};
                    border: 2px solid {bg_color};
                    border-radius: 4px;
                }}
                QRadioButton:checked {{
                    border: 2px solid {border_color};
                    font-weight: bold;
                    background-color: white;
                }}
                QRadioButton:hover {{
                    border: 2px solid {border_color};
                }}
            """)
            
            self.status_group.addButton(button, i)
            self.status_buttons[status] = button
            buttons_layout.addWidget(button)
        
        # 默认选择"无"
        self.status_buttons["无"].setChecked(True)
        
        # 连接信号
        self.status_group.buttonClicked.connect(self._on_status_changed)
        
        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout)
        
        # 厚度输入（条件显示） - 与状态选择风格一致
        self._create_thickness_section(content_layout)
        
        
        main_layout.addWidget(content_frame)
        
        # 关键视图管理 - 新增
        self._create_key_view_section(main_layout)
        
        # 操作按钮
        self._create_action_buttons(main_layout)
    
    def _create_action_buttons(self, parent_layout):
        """创建操作按钮"""
        buttons_layout = qt.QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 重置按钮
        reset_btn = qt.QPushButton("重置分析")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_btn.clicked.connect(self.reset_analysis)
        
        # 状态按钮
        status_btn = qt.QPushButton("查看状态")
        status_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        status_btn.clicked.connect(self._show_status)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(status_btn)
        
        parent_layout.addLayout(buttons_layout)
    
    def _create_thickness_section(self, parent_layout):
        """创建厚度输入区域 - 与PFD状态选择风格一致"""
        # 标题 - 与PFD状态选择保持一致的样式
        thickness_title = qt.QLabel("2. 最大厚度")
        thickness_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #343a40; margin-bottom: 3px;")
        
        # 厚度输入布局
        thickness_layout = qt.QHBoxLayout()
        thickness_label = qt.QLabel("厚度 (mm):")
        thickness_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #495057;")
        
        self.thickness_spinbox = qt.QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.0, 50.0)
        self.thickness_spinbox.setDecimals(1)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.valueChanged.connect(self._on_thickness_changed)
        
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addStretch()
        
        # 创建容器widget，以便控制可见性
        self.thickness_widget = qt.QWidget()
        thickness_widget_layout = qt.QVBoxLayout(self.thickness_widget)
        thickness_widget_layout.setContentsMargins(0, 0, 0, 0)
        thickness_widget_layout.setSpacing(6)
        thickness_widget_layout.addWidget(thickness_title)
        thickness_widget_layout.addLayout(thickness_layout)
        
        self.thickness_widget.setVisible(False)  # 默认隐藏
        
        parent_layout.addWidget(self.thickness_widget)
    
    def _on_status_changed(self, button):
        """PFD状态改变时的回调"""
        button_id = self.status_group.id(button)
        status_map = {0: 'none', 1: 'present', 2: 'indeterminate'}
        status = status_map.get(button_id, 'none')
        
        # 控制厚度输入区域的可见性
        has_pfd = status == 'present'
        if hasattr(self, 'thickness_widget'):
            self.thickness_widget.setVisible(has_pfd)
            
            # 如果状态变为"无"或"难以判定"，重置厚度值
            if not has_pfd:
                self.thickness_spinbox.setValue(0.0)
        
        self.logic.set_status(status)
        self._emit_status_changed()
        logging.info(f"PFD状态设置为: {status}")
    
    def _on_thickness_changed(self, value):
        """厚度值改变时的回调"""
        self.logic.set_thickness(value)
        self._emit_status_changed()
        logging.info(f"PFD厚度设置为: {value} mm")
    
    def _show_status(self):
        """显示当前状态"""
        results = self.get_analysis_results()
        status_text = f"分析类型: {results['analysis_type']}\\n"
        status_text += f"状态: {results['status']}\\n"
        thickness = results.get('max_thickness')
        thickness_text = f"{thickness} mm" if thickness is not None else "未设置"
        status_text += f"最大厚度: {thickness_text}\\n"
        status_text += f"占位符: {results.get('placeholder', False)}"
        
        qt.QMessageBox.information(self, "PFD分析状态", status_text)
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域（仅保留开始按钮）"""
        self.control_frame = qt.QFrame()
        self.control_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        control_layout = qt.QHBoxLayout(self.control_frame)
        control_layout.setSpacing(6)
        control_layout.setContentsMargins(6, 6, 6, 6)
        
        # 开始分析按钮
        self.start_analysis_btn = qt.QPushButton("开始分析")
        self.start_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        
        control_layout.addStretch()
        parent_layout.addWidget(self.control_frame)
    
    def _on_start_analysis(self):
        """开始PFD分析"""
        try:
            logging.info("用户开始PFD分析")
            
            # 禁用开始按钮，避免重复点击
            self.start_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 1. 切换到收缩末期
            qt.QApplication.processEvents()
            
            # 检查是否有收缩末期标记
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info or end_systole_info.get('frame_index') is None:
                qt.QMessageBox.warning(
                    self,
                    "警告",
                    "未找到收缩末期标记！\n\n"
                    "请先在模块一中标记收缩末期时相。"
                )
                self._reset_analysis_buttons()
                return
            
            # 切换到收缩末期
            success = self._switch_to_end_systole()
            if not success:
                qt.QMessageBox.warning(
                    self,
                    "错误",
                    "切换到收缩末期失败！请检查模块一中的期像标记。"
                )
                self._reset_analysis_buttons()
                return
            
            # 2. MPR定位到瓦氏窦平面
            qt.QApplication.processEvents()
            
            success = self._position_to_sinus_valsalva()
            if not success:
                qt.QMessageBox.information(
                    self,
                    "提示",
                    "自动定位失败，请手动调整MPR视图到合适位置。\n分析可以继续进行。"
                )
            
            # 3. 完成准备
            self._complete_analysis_preparation()
            
            logging.info("PFD分析环境准备完成")
            
        except Exception as e:
            logging.error(f"开始PFD分析失败: {e}")
            qt.QMessageBox.critical(
                self,
                "错误", 
                f"分析启动失败：\n{e}"
            )
            self._reset_analysis_buttons()
    
    def _complete_analysis_preparation(self):
        """完成分析准备"""
        self.analysis_started = True
        
        # 隐藏分析控制区域
        self.control_frame.setVisible(False)
        
        logging.info("PFD分析准备完成")
    
    def _reset_analysis_buttons(self):
        """重置分析按钮状态"""
        self.start_analysis_btn.setEnabled(True)
    
    def _switch_to_end_systole(self) -> bool:
        """切换到收缩末期 - 使用集中化期像管理服务"""
        try:
            # 使用session的期像管理服务进行切换
            success = self.session.switch_to_systole("PFD_Analysis")
            
            if success:
                # 同步更新轮廓服务的期像设置
                self.contour_service.set_current_phase('end_systole')
                
                logging.info("成功切换到收缩末期（使用期像管理服务）")
                return True
            else:
                logging.error("使用期像管理服务切换到收缩末期失败")
                return False
            
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False
    
    def _position_to_sinus_valsalva(self) -> bool:
        """MPR定位到瓦氏窦平面"""
        try:
            # 尝试使用轮廓定位服务
            success = self.contour_service.switch_to_contour('sinus_of_valsalva', phase='end_systole')
            
            if success:
                logging.info("成功定位到瓦氏窦平面")
                return True
            else:
                logging.warning("定位到瓦氏窦平面失败，但分析可以继续")
                return False
            
        except Exception as e:
            logging.error(f"定位到瓦氏窦平面失败: {e}")
            return False
    
    def _create_key_view_section(self, parent_layout):
        """创建关键视图管理区域"""
        # 创建关键视图管理器组件
        self.key_view_manager = KeyViewManagerWidget(
            analysis_type="PFD",
            session=self.session,
            compact_mode=True,  # 使用紧凑模式
            parent=self
        )
        
        # 连接信号
        self.key_view_manager.viewMarked.connect(self._on_view_marked)
        self.key_view_manager.viewRestored.connect(self._on_view_restored)
        self.key_view_manager.viewDeleted.connect(self._on_view_deleted)
        self.key_view_manager.statusUpdated.connect(self._on_view_status_updated)
        
        parent_layout.addWidget(self.key_view_manager)
    
    def _on_view_marked(self, view_name: str):
        """视图被标记时的回调"""
        logging.info(f"PFD分析 - 视图已标记: {view_name}")
    
    def _on_view_restored(self, view_name: str):
        """视图被恢复时的回调"""
        logging.info(f"PFD分析 - 视图已恢复: {view_name}")
    
    def _on_view_deleted(self, view_name: str):
        """视图被删除时的回调"""
        logging.info(f"PFD分析 - 视图已删除: {view_name}")
    
    def _on_view_status_updated(self, status: str):
        """关键视图状态更新时的回调"""
        logging.debug(f"PFD分析 - 关键视图状态: {status}")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        super().set_session(session)
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.set_session(session)
    
    def cleanup(self):
        """清理资源"""
        # 清理关键视图管理器
        if hasattr(self, 'key_view_manager'):
            self.key_view_manager.cleanup()
        super().cleanup()
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取PFD分析结果"""
        results = self.logic.get_analysis_results()
        
        # 添加关键视图统计
        if hasattr(self, 'key_view_manager'):
            results['key_views_count'] = self.key_view_manager.get_marked_views_count()
            results['key_view_names'] = self.key_view_manager.get_marked_view_names()
        
        return results
    
    def reset_analysis(self):
        """重置PFD分析"""
        # 重置分析状态
        self.analysis_started = False
        
        # 重置分析控制区域
        if hasattr(self, 'control_frame'):
            self.control_frame.setVisible(True)
            self.start_analysis_btn.setEnabled(True)
        
        # 重置逻辑状态
        self.logic.reset_analysis()
        self.status_buttons["无"].setChecked(True)
        
        # 重置厚度输入
        if hasattr(self, 'thickness_spinbox'):
            self.thickness_spinbox.setValue(0.0)
        if hasattr(self, 'thickness_widget'):
            self.thickness_widget.setVisible(False)
        
        self._emit_status_changed()
        logging.info("PFD分析已重置")


class Module3AnalysisWidget(qt.QWidget):
    """模块三标准化分析主界面"""
    
    # 状态改变信号
    statusChanged = qt.Signal(dict)
    
    def __init__(self, session: TAVRStudySession, logic: Optional[Module3AnalysisLogic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic or Module3AnalysisLogic()
        self.logic.set_session(session)
        
        self.setObjectName("Module3AnalysisWidget")
        self._setup_ui()
        logging.info("模块三分析界面初始化完成")
    
    def _setup_ui(self):
        """设置主界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)
        
        # 主标题
        title = qt.QLabel("模块三：瓣叶功能评估分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 8px 16px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-bottom: 5px;
            }
        """)
        main_layout.addWidget(title)
        
        # 创建选项卡容器
        self.analysis_tabs = qt.QTabWidget()
        self.analysis_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
        """)
        
        # 创建分析模块
        self.relm_widget = RelmAnalysisWidget(self.session, self.logic.get_relm_logic(), self)
        self.sfd_widget = SfdAnalysisWidget(self.session, self.logic.get_sfd_logic(), self)
        self.pfd_widget = PfdAnalysisWidget(self.session, self.logic.get_pfd_logic(), self)
        
        # 连接信号
        self.relm_widget.statusChanged.connect(self._on_child_status_changed)
        self.sfd_widget.statusChanged.connect(self._on_child_status_changed)
        self.pfd_widget.statusChanged.connect(self._on_child_status_changed)
        
        # 添加到选项卡
        self.analysis_tabs.addTab(self.relm_widget, "RELM分析")
        self.analysis_tabs.addTab(self.sfd_widget, "SFD分析")
        self.analysis_tabs.addTab(self.pfd_widget, "PFD分析")
        
        main_layout.addWidget(self.analysis_tabs, 1)
        
        # 全局操作按钮
        self._create_global_actions(main_layout)
    
    def _create_global_actions(self, parent_layout):
        """创建全局操作按钮"""
        actions_frame = qt.QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        actions_layout = qt.QHBoxLayout(actions_frame)
        actions_layout.setSpacing(8)
        
        # 重置所有按钮
        reset_all_btn = qt.QPushButton("重置所有分析")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 11px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        reset_all_btn.clicked.connect(self._reset_all_analyses)
        
        # 导出结果按钮
        export_btn = qt.QPushButton("导出分析结果")
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 11px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        export_btn.clicked.connect(self._export_results)
        
        # 查看摘要按钮
        summary_btn = qt.QPushButton("查看分析摘要")
        summary_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 11px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        summary_btn.clicked.connect(self._show_summary)
        
        actions_layout.addWidget(reset_all_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(summary_btn)
        actions_layout.addWidget(export_btn)
        
        parent_layout.addWidget(actions_frame)
    
    def _on_child_status_changed(self, results):
        """子模块状态改变时的回调"""
        # 汇总所有结果并发出信号
        all_results = self.get_all_analysis_results()
        self.statusChanged.emit(all_results)
    
    def _reset_all_analyses(self):
        """重置所有分析"""
        reply = qt.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有分析吗？\\n\\n这将清除所有输入的数据。",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self.logic.reset_all_analyses()
            self.relm_widget.reset_analysis()
            self.sfd_widget.reset_analysis() 
            self.pfd_widget.reset_analysis()
            logging.info("所有模块三分析已重置")
    
    def _export_results(self):
        """导出分析结果"""
        try:
            results = self.get_all_analysis_results()
            
            # 简单的文本导出
            from pathlib import Path
            import json
            
            export_dir = Path.home() / "TAVR_Analytics_Exports"
            export_dir.mkdir(exist_ok=True)
            
            timestamp = qt.QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
            
            # 导出JSON数据
            json_file = export_dir / f"Module3_Analysis_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 导出摘要报告
            summary = self.logic.get_analysis_summary()
            report_file = export_dir / f"Module3_Summary_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            qt.QMessageBox.information(
                self,
                "导出成功",
                f"模块三分析结果已导出：\\n\\n"
                f"数据文件：{json_file}\\n"
                f"摘要文件：{report_file}"
            )
            
        except Exception as e:
            logging.error(f"导出模块三分析结果失败: {e}")
            qt.QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中出现错误：\\n{e}"
            )
    
    def _show_summary(self):
        """显示分析摘要"""
        summary = self.logic.get_analysis_summary()
        
        # 创建摘要对话框
        dialog = qt.QDialog(self)
        dialog.setWindowTitle("模块三分析摘要")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = qt.QVBoxLayout(dialog)
        
        # 摘要文本
        summary_text = qt.QTextEdit()
        summary_text.setPlainText(summary)
        summary_text.setReadOnly(True)
        summary_text.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                font-size: 11px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(summary_text)
        
        # 关闭按钮
        close_btn = qt.QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def get_all_analysis_results(self) -> Dict[str, Any]:
        """获取所有分析结果"""
        return self.logic.get_all_results()
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        self.logic.set_session(session)
        self.relm_widget.session = session
        self.sfd_widget.session = session
        self.pfd_widget.session = session
    
    def on_activated(self):
        """激活时的回调"""
        logging.info("模块三分析界面激活")
        self.relm_widget.on_activated()
        self.sfd_widget.on_activated()
        self.pfd_widget.on_activated()
    
    def on_deactivated(self):
        """停用时的回调"""
        logging.info("模块三分析界面停用")
        self.relm_widget.on_deactivated()
        self.sfd_widget.on_deactivated()
        self.pfd_widget.on_deactivated()
    
    def cleanup(self):
        """清理资源"""
        self.relm_widget.cleanup()
        self.sfd_widget.cleanup()
        self.pfd_widget.cleanup()
        self.logic.cleanup()
        logging.info("模块三分析界面清理完成")


# 向后兼容性别名
PasteAnalysisWidget = Module3AnalysisWidget

# 导出的公共接口
__all__ = [
    'BaseAnalysisWidget',
    'RelmAnalysisWidget',
    'SfdAnalysisWidget', 
    'PfdAnalysisWidget',
    'Module3AnalysisWidget',
    'PasteAnalysisWidget'  # 向后兼容
]