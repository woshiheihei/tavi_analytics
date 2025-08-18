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
        
        # 占位符提示
        placeholder_label = qt.QLabel("📝 RELM分析功能占位符")
        placeholder_label.setAlignment(qt.Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        content_layout.addWidget(placeholder_label)
        
        # 详细说明
        description = qt.QLabel(
            "RELM分析将包含以下功能：\n"
            "• 增厚瓣叶宽度测量\n"
            "• 支架内径测量\n" 
            "• RELM值自动计算\n"
            "• 分级评估与报告生成"
        )
        description.setStyleSheet("color: #495057; font-size: 11px; line-height: 1.4;")
        content_layout.addWidget(description)
        
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
        
        # SFD状态选择
        status_layout = qt.QHBoxLayout()
        status_label = qt.QLabel("SFD状态:")
        status_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.status_group = qt.QButtonGroup()
        self.none_radio = qt.QRadioButton("无")
        self.present_radio = qt.QRadioButton("有")
        self.indeterminate_radio = qt.QRadioButton("难以判定")
        
        self.none_radio.setChecked(True)  # 默认选择
        
        self.status_group.addButton(self.none_radio, 0)
        self.status_group.addButton(self.present_radio, 1)
        self.status_group.addButton(self.indeterminate_radio, 2)
        self.status_group.buttonClicked.connect(self._on_status_changed)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.none_radio)
        status_layout.addWidget(self.present_radio)
        status_layout.addWidget(self.indeterminate_radio)
        status_layout.addStretch()
        content_layout.addLayout(status_layout)
        
        # 占位符提示
        placeholder_label = qt.QLabel("📝 SFD分析功能占位符")
        placeholder_label.setAlignment(qt.Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        content_layout.addWidget(placeholder_label)
        
        # 详细说明
        description = qt.QLabel(
            "SFD分析将包含以下功能：\n"
            "• 主动脉窦充盈缺损检测\n"
            "• 受累窦部标记与记录\n" 
            "• 缺损程度评估\n"
            "• 临床意义分析报告"
        )
        description.setStyleSheet("color: #495057; font-size: 11px; line-height: 1.4;")
        content_layout.addWidget(description)
        
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
        
        self.logic.set_status(status)
        self._emit_status_changed()
        logging.info(f"SFD状态设置为: {status}")
    
    def _show_status(self):
        """显示当前状态"""
        results = self.get_analysis_results()
        status_text = f"分析类型: {results['analysis_type']}\\n"
        status_text += f"状态: {results['status']}\\n"
        status_text += f"受累窦部: {', '.join(results.get('affected_sinuses', []))  or '无'}\\n"
        status_text += f"占位符: {results.get('placeholder', False)}"
        
        qt.QMessageBox.information(self, "SFD分析状态", status_text)
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域"""
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
        
        # 说明
        instruction_label = qt.QLabel("💡 准备分析环境")
        instruction_label.setStyleSheet("font-size: 10px; color: #495057; font-weight: 500;")
        control_layout.addWidget(instruction_label)
        
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
        
        # 跳过按钮
        self.skip_analysis_btn = qt.QPushButton("跳过")
        self.skip_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 6px;
                font-size: 10px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_analysis_btn.clicked.connect(self._on_skip_analysis)
        control_layout.addWidget(self.skip_analysis_btn)
        
        # 状态显示
        self.analysis_status_label = qt.QLabel("等待开始")
        self.analysis_status_label.setStyleSheet("font-size: 9px; color: #868e96; font-style: italic;")
        control_layout.addWidget(self.analysis_status_label)
        
        control_layout.addStretch()
        parent_layout.addWidget(self.control_frame)
    
    def _on_start_analysis(self):
        """开始SFD分析"""
        try:
            logging.info("用户开始SFD分析")
            
            # 更新状态
            self.analysis_status_label.setText("准备中...")
            self.start_analysis_btn.setEnabled(False)
            self.skip_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 1. 切换到收缩末期
            self.analysis_status_label.setText("切换期相...")
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
            self.analysis_status_label.setText("定位平面...")
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
    
    def _on_skip_analysis(self):
        """跳过自动分析，直接进入评估"""
        reply = qt.QMessageBox.question(
            self,
            "跳过自动分析",
            "跳过自动分析，直接开始评估？",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self._complete_analysis_preparation()
            logging.info("SFD用户选择跳过自动分析")
    
    def _complete_analysis_preparation(self):
        """完成分析准备"""
        self.analysis_started = True
        self.analysis_status_label.setText("已就绪")
        
        # 隐藏分析控制区域
        self.control_frame.setVisible(False)
        
        logging.info("SFD分析准备完成")
    
    def _reset_analysis_buttons(self):
        """重置分析按钮状态"""
        self.start_analysis_btn.setEnabled(True)
        self.skip_analysis_btn.setEnabled(True)
        self.analysis_status_label.setText("等待开始")
    
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
            self.skip_analysis_btn.setEnabled(True)
            self.analysis_status_label.setText("等待开始")
        
        # 重置逻辑状态
        self.logic.reset_analysis()
        self.none_radio.setChecked(True)
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
        
        # PFD状态选择
        status_layout = qt.QHBoxLayout()
        status_label = qt.QLabel("PFD状态:")
        status_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.status_group = qt.QButtonGroup()
        self.none_radio = qt.QRadioButton("无")
        self.present_radio = qt.QRadioButton("有")
        self.indeterminate_radio = qt.QRadioButton("难以判定")
        
        self.none_radio.setChecked(True)  # 默认选择
        
        self.status_group.addButton(self.none_radio, 0)
        self.status_group.addButton(self.present_radio, 1)
        self.status_group.addButton(self.indeterminate_radio, 2)
        self.status_group.buttonClicked.connect(self._on_status_changed)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.none_radio)
        status_layout.addWidget(self.present_radio)
        status_layout.addWidget(self.indeterminate_radio)
        status_layout.addStretch()
        content_layout.addLayout(status_layout)
        
        # 厚度输入（条件显示）
        thickness_layout = qt.QHBoxLayout()
        thickness_label = qt.QLabel("厚度 (mm):")
        thickness_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.thickness_spinbox = qt.QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.0, 50.0)
        self.thickness_spinbox.setDecimals(1)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.setEnabled(False)
        self.thickness_spinbox.valueChanged.connect(self._on_thickness_changed)
        
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addStretch()
        content_layout.addLayout(thickness_layout)
        
        # 占位符提示
        placeholder_label = qt.QLabel("📝 PFD分析功能占位符")
        placeholder_label.setAlignment(qt.Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        content_layout.addWidget(placeholder_label)
        
        # 详细说明
        description = qt.QLabel(
            "PFD分析将包含以下功能：\n"
            "• 瓣叶下充盈缺损检测\n"
            "• 最大厚度测量工具\n" 
            "• 缺损范围与程度评估\n"
            "• 血流动力学影响分析"
        )
        description.setStyleSheet("color: #495057; font-size: 11px; line-height: 1.4;")
        content_layout.addWidget(description)
        
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
    
    def _on_status_changed(self, button):
        """PFD状态改变时的回调"""
        button_id = self.status_group.id(button)
        status_map = {0: 'none', 1: 'present', 2: 'indeterminate'}
        status = status_map.get(button_id, 'none')
        
        # 启用或禁用厚度输入
        self.thickness_spinbox.setEnabled(status == 'present')
        if status != 'present':
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
        """创建分析控制区域"""
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
        
        # 说明
        instruction_label = qt.QLabel("💡 准备分析环境")
        instruction_label.setStyleSheet("font-size: 10px; color: #495057; font-weight: 500;")
        control_layout.addWidget(instruction_label)
        
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
        
        # 跳过按钮
        self.skip_analysis_btn = qt.QPushButton("跳过")
        self.skip_analysis_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 6px;
                font-size: 10px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_analysis_btn.clicked.connect(self._on_skip_analysis)
        control_layout.addWidget(self.skip_analysis_btn)
        
        # 状态显示
        self.analysis_status_label = qt.QLabel("等待开始")
        self.analysis_status_label.setStyleSheet("font-size: 9px; color: #868e96; font-style: italic;")
        control_layout.addWidget(self.analysis_status_label)
        
        control_layout.addStretch()
        parent_layout.addWidget(self.control_frame)
    
    def _on_start_analysis(self):
        """开始PFD分析"""
        try:
            logging.info("用户开始PFD分析")
            
            # 更新状态
            self.analysis_status_label.setText("准备中...")
            self.start_analysis_btn.setEnabled(False)
            self.skip_analysis_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 1. 切换到收缩末期
            self.analysis_status_label.setText("切换期相...")
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
            self.analysis_status_label.setText("定位平面...")
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
    
    def _on_skip_analysis(self):
        """跳过自动分析，直接进入评估"""
        reply = qt.QMessageBox.question(
            self,
            "跳过自动分析",
            "跳过自动分析，直接开始评估？",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self._complete_analysis_preparation()
            logging.info("PFD用户选择跳过自动分析")
    
    def _complete_analysis_preparation(self):
        """完成分析准备"""
        self.analysis_started = True
        self.analysis_status_label.setText("已就绪")
        
        # 隐藏分析控制区域
        self.control_frame.setVisible(False)
        
        logging.info("PFD分析准备完成")
    
    def _reset_analysis_buttons(self):
        """重置分析按钮状态"""
        self.start_analysis_btn.setEnabled(True)
        self.skip_analysis_btn.setEnabled(True)
        self.analysis_status_label.setText("等待开始")
    
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
            self.skip_analysis_btn.setEnabled(True)
            self.analysis_status_label.setText("等待开始")
        
        # 重置逻辑状态
        self.logic.reset_analysis()
        self.none_radio.setChecked(True)
        self.thickness_spinbox.setValue(0.0)
        self.thickness_spinbox.setEnabled(False)
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