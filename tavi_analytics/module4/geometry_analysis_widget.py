"""
模块四几何形态分析界面组件

瓣膜支架几何形态评估相关分析的标准化用户界面框架，包含：
- Inflow 分析界面
- Nadir 分析界面
- Commissure Level 分析界面

每个界面显示对应瓣膜平面的测量参数：
- 周长 (Perimeter)，单位：mm
- 面积 (Area)，单位：mm²
- 最长径 (Longest Diameter)，单位：mm
- 最短径 (Shortest Diameter)，单位：mm
- 周长平均径 (Perimeter-derived Diameter)
- 面积平均径 (Area-derived Diameter)
"""
import logging
from typing import Optional, Dict, Any
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from ..widgets.section_card import SectionCard
    from .module4_logic import Module4Logic
    from ..core.domain_models import ValvePlaneLevel
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
    from widgets.section_card import SectionCard
    from module4_logic import Module4Logic
    from core.domain_models import ValvePlaneLevel


class BaseGeometryAnalysisWidget(qt.QWidget):
    """几何形态分析界面基类 - 标准化接口"""
    
    # 状态改变信号
    statusChanged = qt.Signal(dict)
    
    def __init__(self, level_type: str, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(parent)
        self.level_type = level_type
        self.session = session
        self.logic = logic
        self.setObjectName(f"{level_type}GeometryAnalysisWidget")
        
        # 添加 logger
        self.logger = logging.getLogger(__name__)
        
        # 级别显示名（供按钮/提示复用）
        self.level_display_name = {
            'inflow': 'Inflow',
            'nadir': 'Nadir',
            'commissure_level': 'Commissure Level',
            'commissure': 'Commissure Level'
        }.get(self.level_type, self.level_type.title())
        
        # UI组件
        self.valve_info_label = None
        self.measurements_table = None
        self.load_data_btn = None
        self.locate_plane_btn = None
        self.status_label = None
        
        logging.info(f"{level_type}几何形态分析界面初始化")
        self._setup_ui()
        self._setup_phase_listener()
    
    def _setup_ui(self):
        """设置用户界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 标题区域（轻样式，避免与卡片冲突）
        title_frame = self._create_title_section()
        main_layout.addWidget(title_frame)

        # 瓣膜信息区域 - 使用统一 SectionCard
        valve_info_card = self._create_valve_info_section()
        main_layout.addWidget(valve_info_card)

        # 控制按钮区域 - 使用统一 SectionCard
        control_card = self._create_control_section()
        main_layout.addWidget(control_card)

        # 测量结果区域 - 使用统一 SectionCard
        measurements_card = self._create_measurements_section()
        main_layout.addWidget(measurements_card)

        # 状态区域
        status_frame = self._create_status_section()
        main_layout.addWidget(status_frame)

        main_layout.addStretch()

        # 在UI创建完成后，安全地初始化瓣膜选择器
        self._setup_valve_selector()
    
    def _setup_phase_listener(self):
        """设置期像切换监听"""
        if self.session:
            try:
                # 获取期像管理服务
                phase_service = self.session.get_phase_management_service()
                self.logger.info(f"{self.level_type}界面获取期像管理服务: {phase_service}")
                
                # 连接期像切换信号
                phase_service.phaseChanged.connect(self._on_phase_changed)
                self.logger.info(f"{self.level_type}几何分析界面已连接期像切换信号")
                
                # 获取当前期像状态
                current_service_phase = phase_service.get_current_phase()
                self.logger.info(f"{self.level_type}界面当前服务期像: {current_service_phase}")
                
            except Exception as e:
                self.logger.error(f"设置期像监听失败: {e}")
                import traceback
                self.logger.error(f"详细错误: {traceback.format_exc()}")
        else:
            self.logger.warning(f"{self.level_type}界面无session，跳过期像监听设置")
    
    def _on_phase_changed(self, old_phase: str, new_phase: str):
        """期像切换回调 - 更新测量数据显示"""
        self.logger.info(f"{self.level_type}界面收到期像切换信号: {old_phase} -> {new_phase}")
        try:
            # 更新测量数据显示
            self._refresh_measurements()
        except Exception as e:
            self.logger.error(f"处理期像切换失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _refresh_measurements(self):
        """刷新测量数据显示"""
        self.logger.info(f"开始刷新{self.level_type}测量数据")
        try:
            if not self.logic:
                self.logger.warning(f"{self.level_type}界面logic未设置，无法刷新测量数据")
                return
            
            # 记录logic当前期像
            current_logic_phase = self.logic.get_current_phase()
            self.logger.info(f"{self.level_type}界面Logic当前期像: {current_logic_phase}")
            
            # 获取当前期像的测量数据
            measurements = self.logic.get_plane_measurements_for_level(self.level_type)
            self.logger.info(f"{self.level_type}界面获取到的测量数据: {measurements}")
            
            if 'error' in measurements:
                self.logger.warning(f"获取{self.level_type}测量数据失败: {measurements.get('error')}")
                self._init_empty_measurements_table()
            else:
                self._update_measurements_table(measurements)
                self.logger.info(f"已刷新{self.level_type}测量数据显示")
                
        except Exception as e:
            self.logger.error(f"刷新测量数据失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _setup_valve_selector(self):
        """安全地设置瓣膜选择器"""
        try:
            # 先初始化型号选项（不连接信号）
            if hasattr(self, 'manufacturer_combo') and hasattr(self, 'model_combo'):
                self._init_model_combo_safely()
            
            # 延迟连接信号，使用QTimer确保在下一个事件循环中执行
            import qt
            qt.QTimer.singleShot(100, self._connect_valve_selector_signals)
                
        except Exception as e:
            self.logger.error(f"设置瓣膜选择器失败: {e}")
    
    def _init_model_combo_safely(self):
        """安全地初始化型号下拉框"""
        try:
            if not hasattr(self, 'model_combo'):
                return
                
            # 直接设置默认的Medtronic型号
            self.model_combo.clear()
            self.model_combo.addItems(["Evolut R/PRO", "Evolut FX", "CoreValve", "Evolut PRO+"])
            
        except Exception as e:
            self.logger.error(f"安全初始化型号下拉框失败: {e}")
    
    def _connect_valve_selector_signals(self):
        """延迟连接瓣膜选择器信号"""
        try:
            # 连接厂家选择变化信号 - 使用lambda避免参数传递问题
            if hasattr(self, 'manufacturer_combo'):
                self.manufacturer_combo.currentTextChanged.connect(lambda: self._update_model_options())
            
            # 连接设置按钮信号
            if hasattr(self, 'set_valve_btn'):
                self.set_valve_btn.clicked.connect(self._on_set_valve)
                
        except Exception as e:
            self.logger.error(f"连接瓣膜选择器信号失败: {e}")
    
    def _update_model_options(self):
        """更新型号选项"""
        try:
            if not hasattr(self, 'manufacturer_combo') or not hasattr(self, 'model_combo'):
                return
                
            manufacturer = self.manufacturer_combo.currentText
            if callable(manufacturer):
                manufacturer = manufacturer()
            self.model_combo.clear()
            
            # 添加对应厂家的型号
            if manufacturer == "Medtronic":
                self.model_combo.addItems(["Evolut R/PRO", "Evolut FX", "CoreValve", "Evolut PRO+"])
            elif manufacturer == "Edwards Lifesciences":
                self.model_combo.addItems(["SAPIEN 3", "SAPIEN 3 Ultra", "SAPIEN XT"])
            elif manufacturer == "Venus Medtech":
                self.model_combo.addItems(["VenusA-Valve", "VenusA-Plus"])
            elif manufacturer == "MicroPort":
                self.model_combo.addItems(["VitaFlow"])
            elif manufacturer == "Peijia Medical":
                self.model_combo.addItems(["TaurusOne"])
            else:
                self.model_combo.addItem("Unknown Model")
                
        except Exception as e:
            self.logger.error(f"更新型号选项失败: {e}")
    
    def _on_manufacturer_changed(self, manufacturer: str):
        """厂家选择变化时更新型号选项"""
        try:
            self._update_model_options()
        except Exception as e:
            self.logger.error(f"厂家选择变化处理失败: {e}")
    
    def _on_set_valve(self):
        """应用瓣膜设置"""
        try:
            if not hasattr(self, 'manufacturer_combo') or not hasattr(self, 'model_combo'):
                self._update_status("瓣膜选择器未初始化", "error")
                return
                
            manufacturer = self.manufacturer_combo.currentText
            model = self.model_combo.currentText
            
            # 确保获取到的是字符串值
            if callable(manufacturer):
                manufacturer = manufacturer()
            if callable(model):
                model = model()
            
            if not manufacturer or not model:
                self._update_status("请选择瓣膜厂家和型号", "warning")
                return
            
            # 设置到逻辑组件
            if self.logic:
                self.logic.set_valve_info(manufacturer, model)
                
                # 如果有会话，也更新会话中的患者数据
                if self.session:
                    patient_data = self.session.get_patient_data()
                    if patient_data:
                        patient_data.valveBrand = manufacturer
                        patient_data.valveModel = model
                        self.logger.info(f"设置瓣膜信息: {manufacturer} {model}")
                
                # 更新显示
                self._update_valve_info()
                self._update_status(f"已设置瓣膜: {manufacturer} {model}", "success")
                
                # 检查并隐藏选择器
                self._check_and_hide_valve_selector()
            else:
                self._update_status("逻辑组件未初始化", "error")
                
        except Exception as e:
            self.logger.error(f"应用瓣膜设置失败: {e}")
            self._update_status(f"设置失败: {e}", "error")
    
    def _check_and_hide_valve_selector(self):
        """检查瓣膜信息并决定是否隐藏选择器"""
        try:
            if not hasattr(self, 'valve_selector_frame'):
                return
                
            if self.logic:
                mapping_summary = self.logic.get_valve_mapping_summary()
                if 'error' not in mapping_summary:
                    # 瓣膜信息已设置，隐藏选择器
                    self.valve_selector_frame.setVisible(False)
                else:
                    # 瓣膜信息未设置，显示选择器
                    self.valve_selector_frame.setVisible(True)
        except Exception as e:
            self.logger.error(f"检查瓣膜选择器状态失败: {e}")
    
    def _create_title_section(self) -> qt.QWidget:
        """创建标题区域"""
        frame = qt.QWidget()
        layout = qt.QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 主标题
        title_text = f"{self.level_type.title()} 几何形态分析"
        title = qt.QLabel(title_text)
        title.setAlignment(qt.Qt.AlignCenter)
        # 使用统一样式系统，避免内联配色干扰全局主题
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)
        
        # 描述
        description_text = f"分析瓣膜支架 {self.level_type} 级别的几何形态参数"
        description = qt.QLabel(description_text)
        description.setAlignment(qt.Qt.AlignCenter)
        description.setStyleSheet(StyleManager.get_label_style("small"))
        description.setWordWrap(True)
        layout.addWidget(description)
        
        return frame
    
    def _create_valve_info_section(self) -> qt.QWidget:
        """创建瓣膜信息区域（SectionCard）
        - 统一使用16px状态图标 + 文本，避免emoji大小不一
        - 使用网格布局对齐“厂家/型号/应用”控件
        """
        card = SectionCard(title="瓣膜信息", icon_text="🫀", variant="dashed", parent=self)

        # 状态行：左侧固定16px图标 + 文本
        status_row = qt.QWidget()
        status_layout = qt.QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)

        self.valve_status_icon = qt.QLabel()
        self.valve_status_icon.setFixedSize(16, 16)
        # 初始设置为信息图标
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxInformation)
            self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass

        self.valve_info_label = qt.QLabel("请在下方选择瓣膜品牌和型号")
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("muted"))
        status_layout.addWidget(self.valve_status_icon)
        status_layout.addWidget(self.valve_info_label)
        status_layout.addStretch()
        card.add_widget(status_row)

        # 选择器：使用网格布局，字段对齐更清晰
        self.valve_selector_frame = qt.QWidget()
        grid = qt.QGridLayout(self.valve_selector_frame)
        grid.setContentsMargins(0, 8, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # 厂家
        brand_label = qt.QLabel("厂家")
        brand_label.setStyleSheet(StyleManager.get_label_style("small"))
        self.manufacturer_combo = qt.QComboBox()
        self.manufacturer_combo.addItems([
            "Medtronic", "Edwards Lifesciences", "Venus Medtech",
            "MicroPort", "Peijia Medical"
        ])
        self.manufacturer_combo.setFixedHeight(28)
        self.manufacturer_combo.setMinimumWidth(180)

        # 型号
        model_label = qt.QLabel("型号")
        model_label.setStyleSheet(StyleManager.get_label_style("small"))
        self.model_combo = qt.QComboBox()
        self.model_combo.setFixedHeight(28)
        self.model_combo.setMinimumWidth(200)

        # 应用按钮（保持统一高度/宽度）
        self.set_valve_btn = LayoutManager.create_button_with_style(
            "应用", "toolbar", "sm", 28
        )
        self.set_valve_btn.setMinimumWidth(88)

        # 放入网格：两列字段 + 操作区
        grid.addWidget(brand_label, 0, 0)
        grid.addWidget(self.manufacturer_combo, 0, 1)
        grid.addWidget(model_label, 0, 2)
        grid.addWidget(self.model_combo, 0, 3)
        grid.addWidget(self.set_valve_btn, 0, 4)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 0)

        card.add_widget(self.valve_selector_frame)

        return card
    
    def _create_control_section(self) -> qt.QWidget:
        """创建控制按钮区域（SectionCard）"""
        card = SectionCard(title="操作控制", icon_text="🎯", variant="dashed", parent=self)

        # 按钮行
        button_layout = qt.QHBoxLayout()
        button_layout.setSpacing(8)

        # 使用工具栏式圆角pill按钮风格
        self.locate_plane_btn = LayoutManager.create_button_with_style(
            f"定位 {self.level_display_name} 平面", "toolbar", "sm", 28
        )
        self.locate_plane_btn.clicked.connect(self._on_locate_plane)
        button_layout.addWidget(self.locate_plane_btn)

        self.load_data_btn = LayoutManager.create_button_with_style(
            "重新加载数据", "toolbar", "sm", 28
        )
        self.load_data_btn.clicked.connect(self._on_load_data)
        button_layout.addWidget(self.load_data_btn)

        button_layout.addStretch()
        card.add_layout(button_layout)
        return card

    def _on_locate_plane(self):
        """定位到当前级别平面"""
        try:
            if not self.logic:
                self._update_status("错误: 逻辑组件未初始化", "error")
                return
            # UI反馈
            if self.locate_plane_btn:
                self.locate_plane_btn.setEnabled(False)
                original_text = self.locate_plane_btn.text
                if callable(original_text):
                    original_text = original_text()
                self.locate_plane_btn.setText("🔄 正在定位…")
            
            success = self.logic.switch_to_level_plane(self.level_type)
            if success:
                self._update_status(f"已定位到 {self.level_type} 平面", "success")
                if self.locate_plane_btn:
                    self.locate_plane_btn.setText("✅ 已定位")
                    # 2秒后恢复
                    qt.QTimer.singleShot(1500, lambda: self.locate_plane_btn.setText(f"定位 {self.level_display_name} 平面"))
            else:
                self._update_status(f"定位 {self.level_type} 平面失败，请检查是否已加载数据并设置瓣膜信息", "error")
                if self.locate_plane_btn:
                    self.locate_plane_btn.setText("❌ 定位失败")
                    qt.QTimer.singleShot(1500, lambda: self.locate_plane_btn.setText(f"定位 {self.level_display_name} 平面"))
        except Exception as e:
            logging.error(f"定位 {self.level_type} 平面时出错: {e}")
            self._update_status(f"定位失败: {e}", "error")
            if self.locate_plane_btn:
                self.locate_plane_btn.setText("❌ 出错")
                qt.QTimer.singleShot(1500, lambda: self.locate_plane_btn.setText(f"定位 {self.level_display_name} 平面"))
        finally:
            if self.locate_plane_btn:
                self.locate_plane_btn.setEnabled(True)
    
    def _create_measurements_section(self) -> qt.QWidget:
        """创建测量结果区域（SectionCard）"""
        card = SectionCard(title="测量参数", icon_text="📐", variant="dashed", parent=self)

        # 创建测量参数表格
        self.measurements_table = qt.QTableWidget()
        self.measurements_table.setColumnCount(2)
        self.measurements_table.setHorizontalHeaderLabels(["参数", "数值"])

        # 设置表格样式
        self.measurements_table.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                background-color: white;
                gridline-color: #f3f4f6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                padding: 8px;
                font-weight: bold;
                color: #374151;
            }
            """
        )

        # 设置表格属性
        self.measurements_table.horizontalHeader().setStretchLastSection(True)
        self.measurements_table.verticalHeader().setVisible(False)
        self.measurements_table.setAlternatingRowColors(True)
        self.measurements_table.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        self.measurements_table.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)

        # 设置固定高度
        self.measurements_table.setFixedHeight(210)  # 减少一行的高度

        # 初始化空表格
        self._init_empty_measurements_table()

        card.add_widget(self.measurements_table)
        return card
    
    def _create_status_section(self) -> qt.QWidget:
        """创建状态区域"""
        frame = qt.QWidget()
        layout = qt.QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = qt.QLabel("等待加载数据...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                font-style: italic;
                padding: 4px 8px;
            }
        """)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        return frame
    
    def _init_empty_measurements_table(self):
        """初始化空的测量参数表格"""
        parameters = [
            ("周长 (Perimeter)", "-- mm"),
            ("面积 (Area)", "-- mm²"),
            ("最长径 (Longest Diameter)", "-- mm"),
            ("最短径 (Shortest Diameter)", "-- mm"),
            ("周长平均径 (PED)", "-- mm"),
            ("面积平均径 (AED)", "-- mm")
        ]
        
        self.measurements_table.setRowCount(len(parameters))
        
        for row, (param_name, default_value) in enumerate(parameters):
            # 参数名称
            param_item = qt.QTableWidgetItem(param_name)
            param_item.setFlags(param_item.flags() & ~qt.Qt.ItemIsEditable)
            self.measurements_table.setItem(row, 0, param_item)
            
            # 参数值
            value_item = qt.QTableWidgetItem(default_value)
            value_item.setFlags(value_item.flags() & ~qt.Qt.ItemIsEditable)
            value_item.setTextAlignment(qt.Qt.AlignRight | qt.Qt.AlignVCenter)
            self.measurements_table.setItem(row, 1, value_item)
    
    def _check_and_hide_temp_selector(self):
        """检查瓣膜信息并决定是否隐藏临时选择器（现在调用新方法）"""
        self._check_and_hide_valve_selector()
    
    def _on_load_data(self):
        """重新加载数据按钮响应 - 手动重新加载或修复数据"""
        try:
            if not self.logic:
                self._update_status("错误: 逻辑组件未初始化", "error")
                return
            
            # 检查会话和瓣膜信息
            if not self.session:
                self._update_status("错误: 会话未初始化", "error")
                return
            
            # 调试信息：检查瓣膜信息
            patient_data = self.session.get_patient_data()
            if not patient_data or not patient_data.valveBrand or not patient_data.valveModel:
                self._update_status("请先设置瓣膜信息", "warning")
                return
            
            self.logger.info(f"瓣膜信息: {patient_data.valveBrand} {patient_data.valveModel}")
            
            # 设置瓣膜信息到逻辑组件
            self.logic.set_valve_info(patient_data.valveBrand, patient_data.valveModel)
            
            # 检查多层级平面数据
            plane_data = self.session.get_multi_level_plane_data()
            self.logger.info(f"多层级平面数据: {plane_data is not None}")
            
            # 检查现有测量数据
            all_measurements = self.session.get_all_plane_measurements()
            self.logger.info(f"现有测量数据: {all_measurements is not None}")
            if all_measurements:
                self.logger.info(f"测量数据键: {list(all_measurements.keys())}")
            
            # 检查分期轮廓数据
            phase_summary = self.session.get_phase_contours_summary()
            self.logger.info(f"分期轮廓摘要: {phase_summary}")
            
            # 检查轮廓管理器
            contour_manager = self.session.contour_data_manager
            if contour_manager:
                loaded_summary = contour_manager.get_loaded_contours_summary()
                self.logger.info(f"轮廓管理器加载摘要: {loaded_summary}")
            
            # 尝试不同的数据源
            data_sources = []
            
            if plane_data:
                data_sources.append(("多层级平面数据", plane_data))
            
            if all_measurements:
                data_sources.append(("会话测量数据", all_measurements))
            
            # 尝试从分期轮廓管理器获取数据
            for phase in ['end_diastole', 'end_systole']:
                try:
                    phase_manager = self.session.get_phase_contour_manager(phase)
                    if phase_manager:
                        phase_measurements = phase_manager.get_all_measurements()
                        if phase_measurements:
                            data_sources.append((f"{phase}期像轮廓数据", phase_measurements))
                            self.logger.info(f"{phase}期像数据键: {list(phase_measurements.keys())}")
                except Exception as e:
                    self.logger.warning(f"获取{phase}期像数据失败: {e}")
            
            if not data_sources:
                self._update_status("错误: 未找到任何可用的测量数据", "error")
                return
            
            # 尝试每个数据源
            load_success = False
            for source_name, source_data in data_sources:
                self.logger.info(f"尝试使用{source_name}，数据键: {list(source_data.keys()) if source_data else 'None'}")
                
                # 检查数据格式
                expected_fields = [
                    f"Stent_Frame_base_up_{h}_plane" for h in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
                ]
                found_expected_fields = [field for field in expected_fields if field in source_data]
                
                # 检查是否有轮廓类型的数据
                contour_fields = []
                for contour_type in ["Stent_Frame_Base_plane", "SOV_plane"]:
                    if contour_type in source_data:
                        contour_fields.append(contour_type)
                
                self.logger.info(f"找到的多层级字段: {found_expected_fields}")
                self.logger.info(f"找到的轮廓字段: {contour_fields}")
                
                if found_expected_fields or contour_fields:
                    try:
                        # 将数据仅加载到当前逻辑期像，避免覆盖另一期像导致“看起来不变”
                        current_phase = self.logic.get_current_phase() if hasattr(self.logic, 'get_current_phase') else None
                        if self.logic.load_measurement_data(source_data, phase=current_phase):
                            self.logger.info(f"成功使用{source_name}加载数据")
                            load_success = True
                            break
                        else:
                            self.logger.warning(f"使用{source_name}加载数据失败")
                    except Exception as e:
                        self.logger.error(f"使用{source_name}加载数据时出错: {e}")
                else:
                    self.logger.info(f"{source_name}不包含可用的平面或轮廓数据")
            
            if not load_success:
                self._update_status("错误: 所有数据源都无法成功加载", "error")
                return
            
            self._update_status("数据加载成功", "success")
            
            # 更新显示
            self._update_valve_info()
            self._check_and_hide_temp_selector()
            
            # 获取测量数据
            measurements = self.logic.get_plane_measurements_for_level(self.level_type)
            
            if 'error' in measurements:
                error_msg = measurements.get('error', '未知错误')
                self._update_status(f"未找到 {self.level_type} 级别的平面数据: {error_msg}", "warning")
                self.logger.warning(f"平面数据错误: {error_msg}")
            else:
                self._update_measurements_table(measurements)
                self._update_status(f"成功加载 {self.level_type} 级别数据", "success")
                
        except Exception as e:
            self._update_status(f"加载数据失败: {e}", "error")
            logging.error(f"加载 {self.level_type} 数据失败: {e}")
    
    def _auto_load_data_from_session(self):
        """从会话自动加载数据，失败时显示手动选择界面"""
        try:
            if not self.session or not self.logic:
                self._update_status("错误: 会话或逻辑组件未初始化", "error")
                return
            
            # 1. 尝试从会话获取瓣膜信息
            patient_data = self.session.get_patient_data()
            if patient_data and patient_data.valveBrand and patient_data.valveModel:
                # 设置瓣膜信息到逻辑组件
                self.logic.set_valve_info(patient_data.valveBrand, patient_data.valveModel)
                self.logger.info(f"从会话获取瓣膜信息: {patient_data.valveBrand} {patient_data.valveModel}")
                
                # 2. 检查会话中是否已有轮廓数据
                if self._check_session_contour_data():
                    self._update_status("自动加载完成", "success")
                    self._update_valve_info()
                    self._check_and_hide_temp_selector()
                    
                    # 刷新当前级别的测量数据显示
                    self._refresh_measurements()
                    return
            
            # 3. 如果会话数据不完整，尝试从其他数据源加载
            self.logger.info("会话数据不完整，尝试手动加载数据")
            self._on_load_data()
            
        except Exception as e:
            self.logger.error(f"自动加载数据失败: {e}")
            self._update_status(f"自动加载失败，请手动操作: {e}", "warning")
    
    def _check_session_contour_data(self) -> bool:
        """检查会话中是否有当前期像的轮廓数据"""
        try:
            current_phase = self.logic.get_current_phase()
            manager = self.session.get_phase_contour_manager(current_phase)
            
            # 检查多层级平面数据
            planes = manager.get_multi_level_planes()
            if not planes:
                self.logger.info(f"期像 {current_phase} 无多层级平面数据")
                return False
            
            # 检查当前级别是否有对应平面
            level_plane = None
            for plane in planes:
                if plane.level_type == self.level_type:
                    level_plane = plane
                    break
            
            if level_plane:
                self.logger.info(f"找到 {self.level_type} 级别对应的平面: {level_plane.height}cm")
                return True
            else:
                self.logger.info(f"未找到 {self.level_type} 级别对应的平面")
                return False
                
        except Exception as e:
            self.logger.error(f"检查会话轮廓数据失败: {e}")
            return False
    
    
    def _update_measurements_table(self, measurements: Dict[str, Any]):
        """更新测量参数表格"""
        self.logger.info(f"更新{self.level_type}测量参数表格，数据: {measurements}")
        try:
            # 参数映射 - 使用get_plane_measurements()返回的字段名
            param_mapping = [
                ("周长 (Perimeter)", "perimeter", "mm"),
                ("面积 (Area)", "area", "mm²"),
                ("最长径 (Longest Diameter)", "longest_diameter", "mm"),  # get_plane_measurements返回longest_diameter
                ("最短径 (Shortest Diameter)", "shortest_diameter", "mm"),  # get_plane_measurements返回shortest_diameter
                ("周长平均径 (PED)", "perimeter_derived_diameter", "mm"),  # get_plane_measurements返回perimeter_derived_diameter
                ("面积平均径 (AED)", "area_derived_diameter", "mm")  # get_plane_measurements返回area_derived_diameter
            ]
            
            # 记录当前期像信息（如果有的话）
            phase_info = measurements.get('phase', 'unknown')
            self.logger.info(f"更新{self.level_type}表格，期像: {phase_info}")
            
            # 详细诊断：打印每个预期字段的值和类型
            self.logger.info(f"[UI诊断] {self.level_type} 测量数据详情:")
            for display_name, key, unit in param_mapping:
                value = measurements.get(key, None)
                value_type = type(value).__name__ if value is not None else "None"
                self.logger.info(f"  {display_name}: key='{key}' value={value} type={value_type}")
            
            for row, (display_name, key, unit) in enumerate(param_mapping):
                value = measurements.get(key, 0.0)
                self.logger.info(f"[行{row}] 处理参数 {display_name}: {key} = {value}")
                
                # 更严格的数值检查
                is_valid_number = False
                try:
                    if value is not None:
                        # 尝试转换为浮点数
                        numeric_value = float(value)
                        is_valid_number = numeric_value > 0
                        self.logger.info(f"[行{row}] 数值转换: {value} -> {numeric_value}, 有效={is_valid_number}")
                    else:
                        self.logger.info(f"[行{row}] 值为None")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"[行{row}] 数值转换失败: {value} ({type(value).__name__}) - {e}")
                    is_valid_number = False
                
                if is_valid_number:
                    formatted_value = f"{float(value):.2f} {unit}"
                    self.logger.info(f"[行{row}] 格式化为有效值: {formatted_value}")
                else:
                    formatted_value = f"-- {unit}"
                    self.logger.info(f"[行{row}] 格式化为占位符: {formatted_value} (原值={value}, 类型={type(value).__name__})")
                
                # 更新值
                value_item = self.measurements_table.item(row, 1)
                if value_item:
                    old_text = value_item.text()
                    value_item.setText(formatted_value)
                    self.logger.info(f"[行{row}] 表格更新: {display_name} '{old_text}' -> '{formatted_value}'")
                    
                    # 根据数值设置颜色
                    if is_valid_number:
                        value_item.setForeground(qt.QColor("#059669"))  # 绿色表示有效数值
                    else:
                        value_item.setForeground(qt.QColor("#6b7280"))  # 灰色表示无效数值
                else:
                    self.logger.warning(f"[行{row}] 表格项为空，无法更新 {display_name}")
                    
            # 强制刷新表格显示
            self.measurements_table.viewport().update()
            self.logger.info(f"[UI刷新] {self.level_type} 测量表格已强制刷新")
                        
        except Exception as e:
            self.logger.error(f"更新测量参数表格失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _update_valve_info(self):
        """更新瓣膜信息显示"""
        try:
            if not self.logic:
                self._show_valve_info_error("逻辑组件未初始化")
                return
                
            mapping_summary = self.logic.get_valve_mapping_summary()
            
            if 'error' in mapping_summary:
                error_msg = mapping_summary['error']
                if '瓣膜信息未设置' in error_msg:
                    self._show_valve_info_warning("请在下方选择瓣膜品牌和型号")
                else:
                    self._show_valve_info_error(error_msg)
            else:
                valve_info = mapping_summary.get('valve_info', {})
                plane_info = mapping_summary.get('plane_mappings', {}).get(self.level_type, {})
                
                manufacturer = valve_info.get('manufacturer', '')
                model = valve_info.get('model', '')
                height = plane_info.get('height', 0)
                
                info_text = f"瓣膜: {manufacturer} {model} | {self.level_type.title()} 高度: {height}cm"
                self._show_valve_info_success(info_text)
                
        except Exception as e:
            logging.error(f"更新瓣膜信息失败: {e}")
            self._show_valve_info_error(f"更新失败: {e}")
    
    def _show_valve_info_success(self, message: str):
        """显示成功的瓣膜信息（统一16px图标）"""
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_DialogApplyButton)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("success"))

    def _show_valve_info_warning(self, message: str):
        """显示警告的瓣膜信息（统一16px图标）"""
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxWarning)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("warning"))

    def _show_valve_info_error(self, message: str):
        """显示错误的瓣膜信息（统一16px图标）"""
        try:
            icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxCritical)
            if hasattr(self, 'valve_status_icon') and self.valve_status_icon:
                self.valve_status_icon.setPixmap(icon.pixmap(16, 16))
        except Exception:
            pass
        self.valve_info_label.setText(message)
        self.valve_info_label.setStyleSheet(StyleManager.get_label_style("error"))
    
    
    def _update_status(self, message: str, status_type: str = "info"):
        """更新状态信息"""
        self.status_label.setText(message)
        
        color_map = {
            "success": "#059669",
            "error": "#dc2626", 
            "warning": "#d97706",
            "info": "#6b7280"
        }
        
        color = color_map.get(status_type, "#6b7280")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-style: italic;
                padding: 4px 8px;
            }}
        """)
    
    def set_logic(self, logic: Module4Logic):
        """设置逻辑组件"""
        self.logic = logic
        # 重新设置期像监听（如果session已设置）
        if self.session:
            self._setup_phase_listener()
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if self.logic:
            self.logic.session = session
        # 重新设置期像监听
        self._setup_phase_listener()
    
    def on_activated(self):
        """激活时的回调"""
        logging.info(f"{self.level_type}几何形态分析界面激活")
        
        # 显示axial切片在3D视图中（与模块三保持一致）
        self._show_axial_slice_in_3d()
        
        # 自动加载数据（优先从会话，失败时显示手动选择）
        self._auto_load_data_from_session()
        
        # 检查并更新瓣膜信息显示
        self._check_and_hide_temp_selector()
        self._update_valve_info()
    
    def on_deactivated(self):
        """停用时的回调"""
        logging.info(f"{self.level_type}几何形态分析界面停用")
    
    # 已移除: 模拟平面数据创建逻辑（_create_mock_plane_data）
    
    def _show_axial_slice_in_3d(self):
        """在3D视图中显示axial切片（与模块三保持一致）"""
        try:
            import slicer
            
            # 获取axial切片节点（Red切片）
            axial_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed")
            
            if axial_slice_node:
                # 设置axial切片在3D视图中可见
                axial_slice_node.SetSliceVisible(True)
                
                # 确保其他切片在3D视图中不可见（保持focus在axial）
                green_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen")
                yellow_slice_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow")
                
                if green_slice_node:
                    green_slice_node.SetSliceVisible(False)
                if yellow_slice_node:
                    yellow_slice_node.SetSliceVisible(False)
                
                # 刷新3D视图以确保变更生效
                self._refresh_3d_view()
                
                logging.info("模块四: 已在3D视图中显示axial切片")
                
            else:
                logging.warning("模块四: 无法找到axial切片节点")
                
        except Exception as e:
            logging.error(f"模块四: 在3D视图中显示axial切片失败: {e}")
    
    def _refresh_3d_view(self):
        """刷新3D视图"""
        try:
            import slicer
            
            layout_manager = slicer.app.layoutManager()
            if layout_manager:
                # 刷新主3D视图
                threeDWidget = layout_manager.threeDWidget(0)
                if threeDWidget:
                    threeDView = threeDWidget.threeDView()
                    if threeDView:
                        threeDView.forceRender()
                
                # 如果有多个3D视图，也一并刷新
                for i in range(layout_manager.threeDViewCount):
                    widget = layout_manager.threeDWidget(i)
                    if widget:
                        view = widget.threeDView()
                        if view:
                            view.forceRender()
                
                logging.debug("模块四: 3D视图刷新完成")
                
        except Exception as e:
            logging.error(f"模块四: 刷新3D视图时出错: {e}")
    
    def cleanup(self):
        """清理资源"""
        # 当前无可视化资源需要处理
        logging.info(f"{self.level_type}几何形态分析界面清理完成")


class InflowAnalysisWidget(BaseGeometryAnalysisWidget):
    """Inflow 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(ValvePlaneLevel.INFLOW.value, session, logic, parent)


class NadirAnalysisWidget(BaseGeometryAnalysisWidget):
    """Nadir 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(ValvePlaneLevel.NADIR.value, session, logic, parent)


class CommissureLevelAnalysisWidget(BaseGeometryAnalysisWidget):
    """Commissure Level 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(ValvePlaneLevel.COMMISSURE.value, session, logic, parent)