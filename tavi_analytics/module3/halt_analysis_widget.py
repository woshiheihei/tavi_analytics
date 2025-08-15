"""
HALT分析界面组件

瓣叶功能评估中的HALT (低密度瓣叶增厚) 分析的专门用户界面实现，包含：
- 引导式分析流程（自动切换到舒张末期 + MPR定位到支架底部）
- 三个瓣叶的HALT状态记录表单
- 关键视图标记功能
- 测量工具集成

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.phase_selection_widget import PhaseSelectionWidget
    from ..services.contour_positioning_service import get_contour_position_service
    from ..utils.mpr_positioning.plane_position_manager import get_plane_position_manager
except ImportError:
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
    from widgets.phase_selection_widget import PhaseSelectionWidget
    from services.contour_positioning_service import get_contour_position_service
    from utils.mpr_positioning.plane_position_manager import get_plane_position_manager


class ViewMarkingManager:
    """视图标记管理器 - 保存和恢复MPR视图状态"""
    
    def __init__(self):
        self.marked_views: Dict[str, Dict[str, Any]] = {}
        self.plane_manager = get_plane_position_manager()
    
    def mark_current_view(self, view_name: str) -> bool:
        """
        标记当前MPR视图状态
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 标记成功返回True
        """
        try:
            # 获取当前MPR平面参数
            plane_params = self.plane_manager.get_current_plane_parameters()
            if not plane_params:
                logging.error("无法获取当前MPR平面参数")
                return False
            
            center_point, normal_vector = plane_params
            
            # 保存视图状态
            self.marked_views[view_name] = {
                'center_point': center_point.tolist(),
                'normal_vector': normal_vector.tolist(),
                'timestamp': qt.QDateTime.currentDateTime().toString(),
                'description': f"HALT分析关键视图 - {view_name}"
            }
            
            logging.info(f"已标记视图: {view_name}")
            return True
            
        except Exception as e:
            logging.error(f"标记视图失败: {e}")
            return False
    
    def restore_view(self, view_name: str) -> bool:
        """
        恢复指定的视图标记
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 恢复成功返回True
        """
        try:
            if view_name not in self.marked_views:
                logging.error(f"未找到视图标记: {view_name}")
                return False
            
            view_data = self.marked_views[view_name]
            import numpy as np
            center_point = np.array(view_data['center_point'])
            normal_vector = np.array(view_data['normal_vector'])
            
            # 恢复MPR视图
            success = self.plane_manager.position_to_plane(center_point, normal_vector)
            
            if success:
                logging.info(f"已恢复视图: {view_name}")
            else:
                logging.error(f"恢复视图失败: {view_name}")
            
            return success
            
        except Exception as e:
            logging.error(f"恢复视图失败: {e}")
            return False
    
    def get_marked_views(self) -> Dict[str, str]:
        """
        获取所有已标记的视图
        
        Returns:
            Dict[str, str]: 视图名称到描述的映射
        """
        return {name: data['description'] for name, data in self.marked_views.items()}
    
    def clear_view_mark(self, view_name: str) -> bool:
        """
        清除指定的视图标记
        
        Args:
            view_name: 视图标记名称
            
        Returns:
            bool: 清除成功返回True
        """
        try:
            if view_name in self.marked_views:
                del self.marked_views[view_name]
                logging.info(f"已清除视图标记: {view_name}")
                return True
            else:
                logging.warning(f"视图标记不存在: {view_name}")
                return False
        except Exception as e:
            logging.error(f"清除视图标记失败: {e}")
            return False


class LeafletHaltForm(qt.QWidget):
    """单个瓣叶的HALT状态记录表单"""
    
    # 信号：当状态改变时发出
    statusChanged = qt.Signal(str, dict)  # (leaflet_name, status_data)
    
    def __init__(self, leaflet_name: str, parent=None):
        super().__init__(parent)
        self.leaflet_name = leaflet_name
        self.setObjectName(f"LeafletHaltForm_{leaflet_name}")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置瓣叶HALT表单界面"""
        main_layout = LayoutManager.create_layout(LayoutType.FORM_CONTAINER, self)
        
        # 瓣叶标题
        title = qt.QLabel(f"{self.leaflet_name} 瓣叶")
        title.setStyleSheet(StyleManager.get_label_style("medium"))
        title.setAlignment(qt.Qt.AlignCenter)
        main_layout.addRow(title)
        
        # HALT存在性评估
        self.halt_status_group = qt.QButtonGroup()
        self.halt_none_radio = qt.QRadioButton("无HALT")
        self.halt_present_radio = qt.QRadioButton("有HALT")
        self.halt_unclear_radio = qt.QRadioButton("难以判定")
        
        self.halt_status_group.addButton(self.halt_none_radio, 0)
        self.halt_status_group.addButton(self.halt_present_radio, 1)
        self.halt_status_group.addButton(self.halt_unclear_radio, 2)
        
        # 默认选择"无HALT"
        self.halt_none_radio.setChecked(True)
        
        self.halt_status_group.buttonClicked.connect(self._on_halt_status_changed)
        
        status_layout = qt.QHBoxLayout()
        status_layout.addWidget(self.halt_none_radio)
        status_layout.addWidget(self.halt_present_radio)
        status_layout.addWidget(self.halt_unclear_radio)
        
        main_layout.addRow("HALT状态:", status_layout)
        
        # 面积测量（当有HALT时启用）
        self.area_spinbox = qt.QDoubleSpinBox()
        self.area_spinbox.setRange(0.0, 100.0)
        self.area_spinbox.setDecimals(1)
        self.area_spinbox.setSuffix(" mm²")
        self.area_spinbox.setEnabled(False)
        self.area_spinbox.valueChanged.connect(self._on_measurement_changed)
        
        main_layout.addRow("面积:", self.area_spinbox)
        
        # 占比计算（当有HALT时启用）
        self.percentage_spinbox = qt.QDoubleSpinBox()
        self.percentage_spinbox.setRange(0.0, 100.0)
        self.percentage_spinbox.setDecimals(1)
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setEnabled(False)
        self.percentage_spinbox.valueChanged.connect(self._on_measurement_changed)
        
        main_layout.addRow("占比:", self.percentage_spinbox)
        
        # 分级评估
        self.grade_combo = qt.QComboBox()
        self.grade_combo.addItems([
            "无HALT", "≤25%", "25-50%", "50%-75%", ">75%"
        ])
        self.grade_combo.setEnabled(False)
        self.grade_combo.currentTextChanged.connect(self._on_grade_changed)
        
        main_layout.addRow("分级:", self.grade_combo)
        
        # 备注
        self.notes_edit = qt.QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("备注信息...")
        self.notes_edit.textChanged.connect(self._on_notes_changed)
        
        main_layout.addRow("备注:", self.notes_edit)
        
        # 设置表单样式
        self.setStyleSheet("""
            QWidget#LeafletHaltForm_LC,
            QWidget#LeafletHaltForm_RC,
            QWidget#LeafletHaltForm_NC {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f9f9f9;
                padding: 8px;
                margin: 4px;
            }
        """)
    
    def _on_halt_status_changed(self, button):
        """HALT状态改变时的回调"""
        button_id = self.halt_status_group.id(button)
        
        if button_id == 1:  # 有HALT
            self.area_spinbox.setEnabled(True)
            self.percentage_spinbox.setEnabled(True)
            self.grade_combo.setEnabled(True)
            self.grade_combo.setCurrentIndex(1)  # 默认设为"≤25%"
        else:  # 无HALT或难以判定
            self.area_spinbox.setEnabled(False)
            self.percentage_spinbox.setEnabled(False)
            self.grade_combo.setEnabled(False)
            self.grade_combo.setCurrentIndex(0)  # 设为"无HALT"
            
            # 清空测量值
            self.area_spinbox.setValue(0.0)
            self.percentage_spinbox.setValue(0.0)
        
        self._emit_status_changed()
    
    def _on_measurement_changed(self):
        """测量值改变时的回调"""
        self._emit_status_changed()
    
    def _on_grade_changed(self):
        """分级改变时的回调"""
        self._emit_status_changed()
    
    def _on_notes_changed(self):
        """备注改变时的回调"""
        self._emit_status_changed()
    
    def _emit_status_changed(self):
        """发出状态改变信号"""
        status_data = self.get_status_data()
        self.statusChanged.emit(self.leaflet_name, status_data)
    
    def get_status_data(self) -> Dict[str, Any]:
        """获取当前状态数据"""
        button_id = self.halt_status_group.checkedId()
        
        if button_id == 0:
            halt_status = "无HALT"
        elif button_id == 1:
            halt_status = "有HALT"
        else:
            halt_status = "难以判定"
        
        return {
            'leaflet': self.leaflet_name,
            'halt_status': halt_status,
            'area': self.area_spinbox.value() if self.area_spinbox.isEnabled() else 0.0,
            'percentage': self.percentage_spinbox.value() if self.percentage_spinbox.isEnabled() else 0.0,
            'grade': self.grade_combo.currentText(),
            'notes': self.notes_edit.toPlainText().strip()
        }
    
    def set_status_data(self, data: Dict[str, Any]):
        """设置状态数据"""
        try:
            halt_status = data.get('halt_status', '无HALT')
            
            if halt_status == '无HALT':
                self.halt_none_radio.setChecked(True)
            elif halt_status == '有HALT':
                self.halt_present_radio.setChecked(True)
            else:
                self.halt_unclear_radio.setChecked(True)
            
            # 触发状态更新
            self._on_halt_status_changed(self.halt_status_group.checkedButton())
            
            # 设置测量值
            self.area_spinbox.setValue(data.get('area', 0.0))
            self.percentage_spinbox.setValue(data.get('percentage', 0.0))
            
            # 设置分级
            grade = data.get('grade', '无HALT')
            index = self.grade_combo.findText(grade)
            if index >= 0:
                self.grade_combo.setCurrentIndex(index)
            
            # 设置备注
            self.notes_edit.setPlainText(data.get('notes', ''))
            
        except Exception as e:
            logging.error(f"设置瓣叶状态数据失败: {e}")


class HaltAnalysisWidget(qt.QWidget):
    """HALT分析主界面"""
    
    # 信号：分析开始、结束、状态改变
    analysisStarted = qt.Signal()
    analysisFinished = qt.Signal()
    statusChanged = qt.Signal(dict)  # 发出完整的HALT分析状态
    
    def __init__(self, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.session = session
        
        # 服务组件
        self.contour_service = get_contour_position_service()
        self.view_marking_manager = ViewMarkingManager()
        
        # 期像选择组件 - 复用已有的期像切换逻辑
        self.phase_widget = PhaseSelectionWidget(session, parent=self)
        self.phase_widget.setVisible(False)  # 隐藏，仅用于逻辑复用
        
        # 分析状态
        self.analysis_started = False
        self.leaflet_data: Dict[str, Dict[str, Any]] = {}
        
        self.setObjectName("HaltAnalysisWidget")
        self._setup_ui()
        logging.info("HaltAnalysisWidget 初始化完成")
    
    def _setup_ui(self):
        """设置HALT分析主界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 主标题
        title = qt.QLabel("HALT分析 (低密度瓣叶增厚)")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        main_layout.addWidget(title)
        
        # 分析控制区域
        self._create_analysis_control_section(main_layout)
        
        # 分隔线
        separator1 = qt.QFrame()
        separator1.setFrameShape(qt.QFrame.HLine)
        separator1.setFrameShadow(qt.QFrame.Sunken)
        main_layout.addWidget(separator1)
        
        # 瓣叶状态记录区域
        self._create_leaflet_forms_section(main_layout)
        
        # 分隔线
        separator2 = qt.QFrame()
        separator2.setFrameShape(qt.QFrame.HLine)
        separator2.setFrameShadow(qt.QFrame.Sunken)
        main_layout.addWidget(separator2)
        
        # 视图标记区域
        self._create_view_marking_section(main_layout)
        
        # 分隔线
        separator3 = qt.QFrame()
        separator3.setFrameShape(qt.QFrame.HLine)
        separator3.setFrameShadow(qt.QFrame.Sunken)
        main_layout.addWidget(separator3)
        
        # 操作按钮区域
        self._create_action_buttons_section(main_layout)
    
    def _create_analysis_control_section(self, parent_layout):
        """创建分析控制区域"""
        control_frame = LayoutManager.create_section_frame("分析控制")
        control_layout = qt.QVBoxLayout(control_frame)
        
        # 说明文字
        instruction_label = qt.QLabel(
            "点击'开始HALT分析'将自动:\n"
            "1. 切换到舒张末期时相\n"
            "2. MPR自动定位到支架底部平面\n"
            "3. 启用瓣叶状态记录表单"
        )
        instruction_label.setStyleSheet(StyleManager.get_label_style("info"))
        instruction_label.setWordWrap(True)
        control_layout.addWidget(instruction_label)
        
        # 开始分析按钮
        self.start_analysis_btn = LayoutManager.create_button_with_style(
            "开始HALT分析", "primary", "default", 45
        )
        self.start_analysis_btn.clicked.connect(self._on_start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        
        # 状态显示
        self.analysis_status_label = qt.QLabel("等待开始分析...")
        self.analysis_status_label.setStyleSheet(StyleManager.get_label_style("secondary"))
        self.analysis_status_label.setAlignment(qt.Qt.AlignCenter)
        control_layout.addWidget(self.analysis_status_label)
        
        parent_layout.addWidget(control_frame)
    
    def _create_leaflet_forms_section(self, parent_layout):
        """创建瓣叶状态记录区域"""
        forms_frame = LayoutManager.create_section_frame("瓣叶HALT状态记录")
        forms_layout = qt.QHBoxLayout(forms_frame)
        
        # 创建三个瓣叶的表单
        self.leaflet_forms: Dict[str, LeafletHaltForm] = {}
        
        for leaflet in ['LC', 'RC', 'NC']:
            form = LeafletHaltForm(leaflet)
            form.statusChanged.connect(self._on_leaflet_status_changed)
            form.setEnabled(False)  # 初始状态禁用
            
            self.leaflet_forms[leaflet] = form
            forms_layout.addWidget(form)
        
        parent_layout.addWidget(forms_frame)
    
    def _create_view_marking_section(self, parent_layout):
        """创建视图标记区域"""
        marking_frame = LayoutManager.create_section_frame("关键视图标记")
        marking_layout = qt.QVBoxLayout(marking_frame)
        
        # 说明文字
        marking_instruction = qt.QLabel(
            "通过调节MPR视图观察三个瓣叶的HALT情况，"
            "可以标记关键视图以便后续快速回到该状态"
        )
        marking_instruction.setStyleSheet(StyleManager.get_label_style("info"))
        marking_instruction.setWordWrap(True)
        marking_layout.addWidget(marking_instruction)
        
        # 视图标记控制
        marking_controls_layout = qt.QHBoxLayout()
        
        # 视图名称输入
        self.view_name_edit = qt.QLineEdit()
        self.view_name_edit.setPlaceholderText("输入视图标记名称...")
        self.view_name_edit.setEnabled(False)
        
        # 标记按钮
        self.mark_view_btn = LayoutManager.create_button_with_style(
            "标记当前视图", "secondary", "default", 35
        )
        self.mark_view_btn.clicked.connect(self._on_mark_view)
        self.mark_view_btn.setEnabled(False)
        
        marking_controls_layout.addWidget(qt.QLabel("视图名称:"))
        marking_controls_layout.addWidget(self.view_name_edit)
        marking_controls_layout.addWidget(self.mark_view_btn)
        
        marking_layout.addLayout(marking_controls_layout)
        
        # 已标记视图列表
        self.marked_views_list = qt.QListWidget()
        self.marked_views_list.setMaximumHeight(100)
        self.marked_views_list.setEnabled(False)
        self.marked_views_list.itemDoubleClicked.connect(self._on_restore_view)
        
        marking_layout.addWidget(qt.QLabel("已标记视图（双击恢复）:"))
        marking_layout.addWidget(self.marked_views_list)
        
        parent_layout.addWidget(marking_frame)
    
    def _create_action_buttons_section(self, parent_layout):
        """创建操作按钮区域"""
        actions_layout = qt.QHBoxLayout()
        
        # 重置按钮
        self.reset_btn = LayoutManager.create_button_with_style(
            "重置分析", "warning", "default", 40
        )
        self.reset_btn.clicked.connect(self._on_reset_analysis)
        self.reset_btn.setEnabled(False)
        
        # 完成分析按钮
        self.finish_btn = LayoutManager.create_button_with_style(
            "完成分析", "success", "default", 40
        )
        self.finish_btn.clicked.connect(self._on_finish_analysis)
        self.finish_btn.setEnabled(False)
        
        # 导出结果按钮
        self.export_btn = LayoutManager.create_button_with_style(
            "导出结果", "primary", "default", 40
        )
        self.export_btn.clicked.connect(self._on_export_results)
        self.export_btn.setEnabled(False)
        
        actions_layout.addWidget(self.reset_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.finish_btn)
        actions_layout.addWidget(self.export_btn)
        
        parent_layout.addLayout(actions_layout)
    
    def _on_start_analysis(self):
        """开始HALT分析"""
        try:
            logging.info("用户开始HALT分析")
            
            # 更新状态
            self.analysis_status_label.setText("正在准备分析环境...")
            
            # 1. 切换到舒张末期
            self.analysis_status_label.setText("切换到舒张末期...")
            qt.QApplication.processEvents()
            
            # 检查是否有舒张末期标记
            end_diastole_info = self.session.get_marked_phase('end_diastole')
            if not end_diastole_info or end_diastole_info.get('frame_index') is None:
                qt.QMessageBox.warning(
                    self,
                    "警告",
                    "未找到舒张末期标记！\n\n"
                    "请先在模块一中标记舒张末期时相，然后重新开始HALT分析。"
                )
                self.analysis_status_label.setText("等待开始分析...")
                return
            
            # 切换到舒张末期
            success = self._switch_to_end_diastole()
            if not success:
                qt.QMessageBox.warning(
                    self,
                    "错误",
                    "切换到舒张末期失败！\n\n"
                    "请检查模块一中的期像标记。"
                )
                self.analysis_status_label.setText("等待开始分析...")
                return
            
            # 2. MPR定位到支架底部平面
            self.analysis_status_label.setText("定位到支架底部平面...")
            qt.QApplication.processEvents()
            
            success = self._position_to_stent_bottom()
            if not success:
                qt.QMessageBox.warning(
                    self,
                    "警告",
                    "定位到支架底部平面失败！\n\n"
                    "可能原因：\n"
                    "1. 未找到期像相关的轮廓节点 'ValveStent_Bottom_Contour_End_Diastole'\n"
                    "2. 轮廓数据不完整或损坏\n"
                    "3. 模块二中的轮廓重建未完成\n\n"
                    "HALT分析可以继续进行，但建议：\n"
                    "• 检查模块二中的轮廓重建结果\n"
                    "• 确认舒张末期的支架底部轮廓已正确标记\n"
                    "• 手动调整MPR视图到合适的观察位置"
                )
            
            # 3. 启用界面
            self._enable_analysis_interface()
            
            # 更新状态
            self.analysis_started = True
            self.analysis_status_label.setText("✓ 分析环境准备完成，请观察三个瓣叶的HALT情况")
            
            # 发出信号
            self.analysisStarted.emit()
            
            logging.info("HALT分析环境准备完成")
            
        except Exception as e:
            logging.error(f"开始HALT分析失败: {e}")
            qt.QMessageBox.critical(
                self,
                "错误", 
                f"开始HALT分析时出现错误：\n{e}"
            )
            self.analysis_status_label.setText("分析启动失败")
    
    def _switch_to_end_diastole(self) -> bool:
        """切换到舒张末期 - 复用PhaseSelectionWidget的逻辑"""
        try:
            # 使用PhaseSelectionWidget的自动切换逻辑
            success = self.phase_widget._auto_switch_to_end_diastole()
            
            if success:
                # 同步更新轮廓服务的期像设置
                self.contour_service.set_current_phase('end_diastole')
                
                # 设置当前期像并触发显示管理
                self.phase_widget.set_current_phase('diastole')
                
                logging.info("成功切换到舒张末期（复用PhaseSelectionWidget逻辑）")
                return True
            else:
                logging.error("使用PhaseSelectionWidget切换到舒张末期失败")
                return False
            
        except Exception as e:
            logging.error(f"切换到舒张末期失败: {e}")
            return False
    
    def _position_to_stent_bottom(self) -> bool:
        """MPR定位到支架底部平面"""
        try:
            # 首先检查并记录场景中所有可能相关的轮廓节点
            self._log_available_contour_nodes()
            
            # 尝试使用轮廓定位服务
            success = self.contour_service.switch_to_contour('valve_stent_bottom', phase='end_diastole')
            
            if success:
                logging.info("成功定位到支架底部平面")
                return True
            
            # 如果失败，尝试使用ContourPositionManager作为后备方案
            logging.warning("轮廓定位服务失败，尝试后备方案...")
            
            try:
                from ..utils.contour_position.contour_position_manager import ContourPositionManager
                contour_manager = ContourPositionManager()
                contour_manager.set_current_phase('end_diastole')
                
                # 尝试使用ContourPositionManager
                success = contour_manager.switch_to_contour('valve_stent_bottom', phase='end_diastole')
                
                if success:
                    logging.info("使用后备方案成功定位到支架底部平面")
                    return True
                else:
                    logging.warning("后备方案也失败，但分析可以继续")
                    return False
                    
            except Exception as fallback_error:
                logging.error(f"后备方案失败: {fallback_error}")
                logging.warning("定位到支架底部平面失败，但分析可以继续")
                return False
            
        except Exception as e:
            logging.error(f"定位到支架底部平面失败: {e}")
            return False
    
    def _log_available_contour_nodes(self):
        """记录场景中所有可能的轮廓节点，用于调试"""
        try:
            import slicer
            
            # 查找所有可能的轮廓相关节点
            keywords = ['contour', 'stent', 'valve', 'bottom', 'diastole', 'ValveStent']
            found_nodes = []
            
            # 获取所有节点
            scene = slicer.mrmlScene
            for i in range(scene.GetNumberOfNodes()):
                node = scene.GetNthNode(i)
                if node and hasattr(node, 'GetName'):
                    node_name = node.GetName()
                    # 检查是否包含任何关键词
                    if any(keyword.lower() in node_name.lower() for keyword in keywords):
                        found_nodes.append({
                            'name': node_name,
                            'type': node.GetClassName(),
                            'id': node.GetID()
                        })
            
            if found_nodes:
                logging.info("场景中发现的可能相关轮廓节点:")
                for node_info in found_nodes:
                    logging.info(f"  - {node_info['name']} ({node_info['type']})")
            else:
                logging.warning("场景中未发现任何轮廓相关节点")
                logging.info("提示：请确认模块二已运行并成功生成轮廓数据")
                
        except Exception as e:
            logging.error(f"记录可用轮廓节点时出错: {e}")
    
    def _enable_analysis_interface(self):
        """启用分析界面"""
        # 禁用开始按钮
        self.start_analysis_btn.setEnabled(False)
        
        # 启用瓣叶表单
        for form in self.leaflet_forms.values():
            form.setEnabled(True)
        
        # 启用视图标记
        self.view_name_edit.setEnabled(True)
        self.mark_view_btn.setEnabled(True)
        self.marked_views_list.setEnabled(True)
        
        # 启用操作按钮
        self.reset_btn.setEnabled(True)
        self.finish_btn.setEnabled(True)
    
    def _on_leaflet_status_changed(self, leaflet_name: str, status_data: Dict[str, Any]):
        """瓣叶状态改变时的回调"""
        self.leaflet_data[leaflet_name] = status_data
        
        # 检查是否所有瓣叶都有数据
        complete_data = len(self.leaflet_data) == 3
        
        if complete_data:
            self.export_btn.setEnabled(True)
        
        # 发出状态改变信号
        self.statusChanged.emit(self.get_analysis_results())
        
        logging.info(f"瓣叶 {leaflet_name} 状态更新: {status_data['halt_status']}")
    
    def _on_mark_view(self):
        """标记当前视图"""
        view_name = self.view_name_edit.text().strip()
        if not view_name:
            qt.QMessageBox.warning(
                self,
                "警告",
                "请输入视图标记名称！"
            )
            return
        
        # 检查名称是否已存在
        marked_views = self.view_marking_manager.get_marked_views()
        if view_name in marked_views:
            reply = qt.QMessageBox.question(
                self,
                "确认",
                f"视图标记 '{view_name}' 已存在，是否覆盖？",
                qt.QMessageBox.Yes | qt.QMessageBox.No
            )
            if reply != qt.QMessageBox.Yes:
                return
        
        # 标记视图
        success = self.view_marking_manager.mark_current_view(view_name)
        if success:
            self._update_marked_views_list()
            self.view_name_edit.clear()
            qt.QMessageBox.information(
                self,
                "成功",
                f"视图 '{view_name}' 已标记！\n\n"
                "双击列表中的项目可以快速恢复到该视图。"
            )
        else:
            qt.QMessageBox.warning(
                self,
                "错误",
                "标记视图失败！"
            )
    
    def _on_restore_view(self, item):
        """恢复视图标记"""
        view_name = item.text()
        success = self.view_marking_manager.restore_view(view_name)
        
        if success:
            self.analysis_status_label.setText(f"✓ 已恢复视图: {view_name}")
        else:
            qt.QMessageBox.warning(
                self,
                "错误",
                f"恢复视图 '{view_name}' 失败！"
            )
    
    def _update_marked_views_list(self):
        """更新已标记视图列表"""
        self.marked_views_list.clear()
        marked_views = self.view_marking_manager.get_marked_views()
        
        for view_name in marked_views.keys():
            self.marked_views_list.addItem(view_name)
    
    def _on_reset_analysis(self):
        """重置分析"""
        reply = qt.QMessageBox.question(
            self,
            "确认重置",
            "确定要重置HALT分析吗？\n\n"
            "这将清除所有瓣叶状态记录和视图标记。",
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        
        if reply == qt.QMessageBox.Yes:
            self._reset_analysis_state()
    
    def _reset_analysis_state(self):
        """重置分析状态"""
        # 重置标志
        self.analysis_started = False
        
        # 清空瓣叶数据
        self.leaflet_data.clear()
        
        # 重置瓣叶表单
        for form in self.leaflet_forms.values():
            form.halt_none_radio.setChecked(True)
            form._on_halt_status_changed(form.halt_none_radio)
            form.notes_edit.clear()
            form.setEnabled(False)
        
        # 清空视图标记
        self.view_marking_manager.marked_views.clear()
        self.view_name_edit.clear()
        self.marked_views_list.clear()
        
        # 重置界面状态
        self.start_analysis_btn.setEnabled(True)
        self.view_name_edit.setEnabled(False)
        self.mark_view_btn.setEnabled(False)
        self.marked_views_list.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.finish_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # 更新状态
        self.analysis_status_label.setText("等待开始分析...")
        
        logging.info("HALT分析已重置")
    
    def _on_finish_analysis(self):
        """完成分析"""
        # 检查是否有数据
        if not self.leaflet_data:
            qt.QMessageBox.warning(
                self,
                "警告",
                "尚未记录任何瓣叶状态！\n\n"
                "请先记录各瓣叶的HALT状态。"
            )
            return
        
        # 显示分析结果摘要
        self._show_analysis_summary()
        
        # 发出完成信号
        self.analysisFinished.emit()
    
    def _show_analysis_summary(self):
        """显示分析结果摘要"""
        summary_text = "HALT分析结果摘要:\n\n"
        
        for leaflet, data in self.leaflet_data.items():
            summary_text += f"{leaflet} 瓣叶:\n"
            summary_text += f"  状态: {data['halt_status']}\n"
            
            if data['halt_status'] == '有HALT':
                summary_text += f"  面积: {data['area']:.1f} mm²\n"
                summary_text += f"  占比: {data['percentage']:.1f}%\n"
                summary_text += f"  分级: {data['grade']}\n"
            
            if data['notes']:
                summary_text += f"  备注: {data['notes']}\n"
            
            summary_text += "\n"
        
        # 视图标记信息
        marked_views = self.view_marking_manager.get_marked_views()
        if marked_views:
            summary_text += f"已标记关键视图 {len(marked_views)} 个:\n"
            for view_name in marked_views.keys():
                summary_text += f"  - {view_name}\n"
        
        qt.QMessageBox.information(
            self,
            "分析完成",
            summary_text
        )
    
    def _on_export_results(self):
        """导出结果"""
        try:
            results = self.get_analysis_results()
            
            # 简单的JSON导出示例
            import json
            from pathlib import Path
            
            # 创建导出目录
            export_dir = Path.home() / "TAVR_Analytics_Exports"
            export_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = qt.QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
            filename = f"HALT_Analysis_{timestamp}.json"
            filepath = export_dir / filename
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            qt.QMessageBox.information(
                self,
                "导出成功",
                f"HALT分析结果已导出到:\n{filepath}"
            )
            
            logging.info(f"HALT分析结果已导出: {filepath}")
            
        except Exception as e:
            logging.error(f"导出HALT分析结果失败: {e}")
            qt.QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中出现错误:\n{e}"
            )
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取完整的分析结果"""
        return {
            'analysis_type': 'HALT',
            'analysis_started': self.analysis_started,
            'leaflets': dict(self.leaflet_data),
            'marked_views': self.view_marking_manager.marked_views,
            'analysis_timestamp': qt.QDateTime.currentDateTime().toString(),
            'session_info': {
                'study_name': getattr(self.session, 'study_name', 'Unknown'),
                'patient_id': getattr(self.session, 'patient_id', 'Unknown')
            }
        }
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        # 同步更新phase_widget的session
        if hasattr(self, 'phase_widget'):
            self.phase_widget.set_session(session)
    
    def on_activated(self):
        """模块激活时调用"""
        logging.info("HALT分析界面激活")
    
    def on_deactivated(self):
        """模块取消激活时调用"""
        logging.info("HALT分析界面取消激活")
    
    def cleanup(self):
        """清理资源"""
        # 清理phase_widget
        if hasattr(self, 'phase_widget'):
            self.phase_widget.cleanup()
        
        logging.info("HALT分析界面清理资源")
