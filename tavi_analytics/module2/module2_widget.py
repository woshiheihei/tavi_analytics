"""
模块二界面组件
负责引导式分割与解剖标志点定义的用户界面
"""

import logging
from typing import Optional
import qt
import slicer

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager
    from .module2_logic import Module2Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager
    from module2.module2_logic import Module2Logic


class Module2Widget(qt.QWidget):
    """
    模块二界面组件
    
    提供引导式分割与解剖标志点定义的用户界面，包括：
    - 分割工具界面
    - 标志点定义界面
    - 进度显示
    - 结果预览
    """

    def __init__(self, session: TAVRStudySession, logic: Optional[Module2Logic] = None, parent=None):
        """
        初始化模块二界面组件
        
        Args:
            session: TAVR研究会话对象
            logic: 模块二业务逻辑对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.logic = logic or Module2Logic()
        
        # 设置组件属性
        self.setObjectName("Module2Widget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("Module2Widget 初始化完成")

    def on_activated(self):
        """
        模块激活时的回调方法
        
        自动切换到舒张末期时相，为分割和标志点定义做准备
        """
        logging.info("模块二已激活，开始自动时相切换")
        
        try:
            # 尝试切换到舒张末期
            if self._auto_switch_to_end_diastole():
                logging.info("成功切换到舒张末期时相")
                self._update_status("已切换到舒张末期，准备开始分割...")
            else:
                logging.warning("未能自动切换到舒张末期时相")
                self._update_status("请先在模块一中标记舒张末期时相")
                
        except Exception as e:
            logging.error(f"自动时相切换失败: {e}")
            self._update_status("时相切换失败，请检查时相标记")

    def _auto_switch_to_end_diastole(self) -> bool:
        """
        自动切换到舒张末期时相
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        # 1. 从session获取舒张末期时相信息
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        if not end_diastole_info:
            logging.info("未找到舒张末期标记，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        frame_index = end_diastole_info.get('frame_index')
        if frame_index is None:
            logging.info("舒张末期标记中缺少帧索引信息，跳过时相切换")
            return True  # 不强制要求有时相标记
        
        # 2. 获取序列浏览器节点
        browser_node = self.session.get_sequence_browser_node()
        if not browser_node:
            logging.warning("未找到序列浏览器节点")
            return False
        
        # 3. 切换到指定帧
        try:
            browser_node.SetSelectedItemNumber(frame_index)
            logging.info(f"成功切换到帧 {frame_index} (舒张末期)")
            return True
        except Exception as e:
            logging.error(f"切换帧失败: {e}")
            return False

    def _update_status(self, message: str):
        """更新状态显示"""
        if hasattr(self, 'status_label'):
            self.status_label.text = message
            logging.info(f"状态更新: {message}")

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        self._create_title_section(layout)
        
        # 添加分割工具区域 (Segmentation)
        self._create_segmentation_section(layout)
        
        # 添加解剖标志点定义区域 (Landmark Placement)
        self._create_landmark_placement_section(layout)
        
        # 添加进度状态区域 (Progress Status)
        self._create_progress_section(layout)
        
        # 添加操作控制区域 (Operations)
        self._create_operations_section(layout)
        
        # 添加弹性空间
        layout.addStretch()

    def _create_title_section(self, layout):
        """创建标题区域"""
        title_label = qt.QLabel("模块二：引导式分割与解剖标志点定义")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title_label)
        
        # 添加描述
        description_label = qt.QLabel(
            "本模块提供主动脉根部和瓣膜支架的半自动分割功能，\n"
            "以及关键解剖标志点的定义和管理工具。"
        )
        description_label.setAlignment(qt.Qt.AlignCenter)
        description_label.setStyleSheet(StyleManager.get_label_style("muted"))
        layout.addWidget(description_label)

    def _create_segmentation_section(self, layout):
        """创建分割工具区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        segmentation_group = LayoutManager.create_section_frame("分割工具 (Segmentation)")
        segmentation_layout = qt.QVBoxLayout(segmentation_group)
        
        # 按照详细设计文档和开发计划任务2的要求，添加三个分割按钮
        # 使用推荐的LayoutManager.create_button_with_style()方法创建按钮
        
        # 1. 开始主动脉根部分割按钮 - 主要操作
        aortic_root_button = LayoutManager.create_button_with_style(
            text="开始主动脉根部分割",
            button_type="primary",
            size="default",
            min_height=40
        )
        aortic_root_button.setObjectName("aorticRootSegmentationButton")
        aortic_root_button.clicked.connect(lambda: self._on_button_clicked("开始主动脉根部分割"))
        segmentation_layout.addWidget(aortic_root_button)
        
        # 2. 开始瓣膜支架分割按钮 - 次要操作
        valve_stent_button = LayoutManager.create_button_with_style(
            text="开始瓣膜支架分割",
            button_type="secondary",
            size="default",
            min_height=40
        )
        valve_stent_button.setObjectName("valveStentSegmentationButton")
        valve_stent_button.clicked.connect(lambda: self._on_button_clicked("开始瓣膜支架分割"))
        segmentation_layout.addWidget(valve_stent_button)
        
        # 3. 验证分割结果按钮 - 轮廓按钮
        validate_button = LayoutManager.create_button_with_style(
            text="验证分割结果",
            button_type="outline",
            size="default",
            min_height=35
        )
        validate_button.setObjectName("validateSegmentationButton")
        validate_button.clicked.connect(lambda: self._on_button_clicked("验证分割结果"))
        segmentation_layout.addWidget(validate_button)
        
        layout.addWidget(segmentation_group)

    def _create_landmark_placement_section(self, layout):
        """创建解剖标志点定义区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        landmark_group = LayoutManager.create_section_frame("解剖标志点定义 (Landmark Placement)")
        landmark_layout = qt.QVBoxLayout(landmark_group)
        
        # 添加实时操作提示组件
        self._create_landmark_instruction_panel(landmark_layout)
        
        # 按照详细设计文档和开发计划任务3的要求，添加四个标志点定义按钮
        # 使用推荐的LayoutManager.create_button_with_style()方法创建按钮
        
        # 1. 定义原生瓣环按钮 - 主要操作，连接到第12个任务实现的逻辑方法
        self.native_annulus_button = LayoutManager.create_button_with_style(
            text="定义原生瓣环",
            button_type="primary",
            size="default",
            min_height=40
        )
        self.native_annulus_button.setObjectName("defineNativeAnnulusButton")
        self.native_annulus_button.clicked.connect(self._on_define_native_annulus)
        landmark_layout.addWidget(self.native_annulus_button)
        
        # 2. 定义原生连合按钮 - 次要操作
        self.native_commissure_button = LayoutManager.create_button_with_style(
            text="定义原生连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        self.native_commissure_button.setObjectName("defineNativeCommissureButton")
        self.native_commissure_button.clicked.connect(self._on_define_native_commissure)
        landmark_layout.addWidget(self.native_commissure_button)
        
        # 3. 定义新连合按钮 - 次要操作
        neo_commissure_button = LayoutManager.create_button_with_style(
            text="定义新连合",
            button_type="secondary",
            size="default",
            min_height=40
        )
        neo_commissure_button.setObjectName("defineNeoCommissureButton")
        neo_commissure_button.clicked.connect(lambda: self._on_button_clicked("定义新连合"))
        landmark_layout.addWidget(neo_commissure_button)
        
        # 4. 定义冠脉开口按钮 - 轮廓按钮
        coronary_ostia_button = LayoutManager.create_button_with_style(
            text="定义冠脉开口",
            button_type="outline",
            size="default",
            min_height=35
        )
        coronary_ostia_button.setObjectName("defineCoronaryOstiaButton")
        coronary_ostia_button.clicked.connect(lambda: self._on_button_clicked("定义冠脉开口"))
        landmark_layout.addWidget(coronary_ostia_button)
        
        layout.addWidget(landmark_group)

    def _create_progress_section(self, layout):
        """创建进度状态区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        progress_group = LayoutManager.create_section_frame("进度状态")
        progress_layout = qt.QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(StyleManager.get_input_style())
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态文本标签
        self.status_label = qt.QLabel("准备开始分割...")
        self.status_label.setAlignment(qt.Qt.AlignCenter)
        self.status_label.setStyleSheet(StyleManager.get_label_style("muted"))
        self.status_label.setMinimumHeight(30)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)

    def _create_operations_section(self, layout):
        """创建操作控制区域"""
        # 使用标准化的section_frame替代直接创建QGroupBox - 与模块一保持一致
        operations_group = LayoutManager.create_section_frame("操作")
        operations_layout = qt.QHBoxLayout(operations_group)
        
        # 重置按钮 - 使用destructive样式表示危险操作
        reset_button = LayoutManager.create_button_with_style(
            text="重置",
            button_type="destructive",
            size="default",
            min_height=40
        )
        reset_button.setObjectName("resetModuleButton")
        reset_button.clicked.connect(lambda: self._on_button_clicked("重置"))
        operations_layout.addWidget(reset_button)
        
        # 完成模块按钮 - 使用primary样式表示主要操作
        complete_button = LayoutManager.create_button_with_style(
            text="完成模块",
            button_type="primary",
            size="default",
            min_height=40
        )
        complete_button.setObjectName("completeModuleButton")
        complete_button.clicked.connect(lambda: self._on_button_clicked("完成模块"))
        operations_layout.addWidget(complete_button)
        
        layout.addWidget(operations_group)

    def _create_landmark_instruction_panel(self, layout):
        """
        创建实时操作提示面板
        
        提供动态的用户操作指导和状态反馈
        """
        # 创建指令面板容器
        instruction_frame = qt.QFrame()
        instruction_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        instruction_layout = qt.QVBoxLayout(instruction_frame)
        instruction_layout.setSpacing(8)
        instruction_layout.setContentsMargins(12, 12, 12, 12)
        
        # 添加指令标题
        instruction_title = qt.QLabel("📍 操作指导")
        instruction_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #495057;
                font-size: 14px;
                margin-bottom: 4px;
            }
        """)
        instruction_layout.addWidget(instruction_title)
        
        # 添加动态指令文本
        self.instruction_label = qt.QLabel("请选择要定义的解剖标志点类型")
        self.instruction_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 13px;
                line-height: 18px;
                margin: 0px;
            }
        """)
        self.instruction_label.setWordWrap(True)
        instruction_layout.addWidget(self.instruction_label)
        
        # 添加进度状态指示器
        self.landmark_progress_label = qt.QLabel("等待用户操作...")
        self.landmark_progress_label.setStyleSheet("""
            QLabel {
                color: #007bff;
                font-size: 12px;
                font-style: italic;
                margin-top: 4px;
            }
        """)
        instruction_layout.addWidget(self.landmark_progress_label)
        
        # 添加嵌入式标志点控制面板
        self._create_embedded_markups_controls(instruction_layout)
        
        layout.addWidget(instruction_frame)

    def _create_embedded_markups_controls(self, layout):
        """
        创建嵌入式标志点控制面板
        
        在当前模块中直接提供markups相关的控制功能，无需跳转模块
        """
        # 创建控制按钮面板
        controls_frame = qt.QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 8px;
                padding: 8px;
            }
        """)
        controls_layout = qt.QHBoxLayout(controls_frame)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        
        # 标志点操作按钮
        self.place_mode_button = qt.QPushButton("🎯 放置模式")
        self.place_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.place_mode_button.clicked.connect(self._on_toggle_place_mode)
        self.place_mode_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.place_mode_button)
        
        # 删除最后一个点
        self.delete_last_button = qt.QPushButton("↶ 撤销")
        self.delete_last_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        self.delete_last_button.clicked.connect(self._on_delete_last_point)
        self.delete_last_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.delete_last_button)
        
        # 清除所有点
        self.clear_points_button = qt.QPushButton("🗑️ 清除")
        self.clear_points_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.clear_points_button.clicked.connect(self._on_clear_all_points)
        self.clear_points_button.setVisible(False)  # 初始隐藏
        controls_layout.addWidget(self.clear_points_button)
        
        # 添加弹性空间
        controls_layout.addStretch()
        
        layout.addWidget(controls_frame)
        
        # 保存控制面板引用
        self.markups_controls_frame = controls_frame

    def _on_define_native_annulus(self):
        """
        处理定义原生瓣环按钮点击事件
        
        连接到第12个任务实现的平面重建算法
        """
        logging.info("用户点击了'定义原生瓣环'按钮")
        
        try:
            # 更新UI状态
            self._update_instruction("正在创建原生瓣环标志点节点...")
            self._update_landmark_progress("⏳ 初始化中...")
            
            # 禁用按钮，防止重复点击
            self.native_annulus_button.setEnabled(False)
            self.native_annulus_button.setText("正在初始化...")
            
            # 调用逻辑层的平面重建方法
            result = self.logic.reconstruct_native_annulus_plane()
            
            if result:
                self._update_instruction(
                    "✅ 标志点节点已创建！\n"
                    "请在3D视图中依次放置3个原生瓣环上的点：\n"
                    "1️⃣ 第一个点：右冠状动脉小叶对应的瓣环点\n"
                    "2️⃣ 第二个点：左冠状动脉小叶对应的瓣环点\n" 
                    "3️⃣ 第三个点：无冠状动脉小叶对应的瓣环点"
                )
                self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
                
                # 显示嵌入式标志点控制面板
                self._show_markups_controls()
                
                # 启动定时器监控标志点放置进度
                self._start_landmark_monitoring()
                
                # 更新状态栏
                self._update_status("Native_Annulus_Points节点已激活，请开始放置标志点")
                
                logging.info("原生瓣环平面重建流程已启动")
                
            else:
                self._update_instruction("❌ 标志点节点创建失败，请重试")
                self._update_landmark_progress("❌ 创建失败")
                self._enable_native_annulus_button()
                self._update_status("原生瓣环标志点创建失败")
                logging.error("原生瓣环平面重建流程启动失败")
                
        except Exception as e:
            logging.error(f"定义原生瓣环失败: {e}")
            self._update_instruction(f"❌ 发生错误: {str(e)}")
            self._update_landmark_progress("❌ 操作失败")
            self._enable_native_annulus_button()
            self._update_status("原生瓣环定义失败，请检查日志")

    def _start_landmark_monitoring(self):
        """
        启动标志点放置监控
        
        定期检查用户放置的标志点数量，并在达到3个点时自动触发平面计算
        """
        # 创建定时器
        self.landmark_timer = qt.QTimer()
        self.landmark_timer.timeout.connect(self._check_landmark_progress)
        self.landmark_timer.start(1000)  # 每秒检查一次
        
        logging.info("标志点监控定时器已启动")

    def _check_landmark_progress(self):
        """
        检查标志点放置进度
        
        监控用户在3D视图中放置的标志点数量，并提供实时反馈
        """
        try:
            # 获取状态信息
            status = self.logic.get_native_annulus_plane_status()
            
            if not status['node_exists']:
                # 节点不存在，停止监控
                self._stop_landmark_monitoring()
                self._enable_native_annulus_button()
                return
            
            points_placed = status['points_placed']
            points_needed = status['points_needed']
            
            # 更新进度显示
            if points_placed == 0:
                self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
            elif points_placed == 1:
                self._update_landmark_progress("📍 已放置1个点，还需要2个点 (1/3)")
                self._update_instruction(
                    "✅ 第一个点已放置！\n"
                    "请继续放置第二个瓣环点（左冠状动脉小叶对应位置）"
                )
            elif points_placed == 2:
                self._update_landmark_progress("📍 已放置2个点，还需要1个点 (2/3)")
                self._update_instruction(
                    "✅ 前两个点已放置！\n"
                    "请放置第三个瓣环点（无冠状动脉小叶对应位置）"
                )
            elif points_placed >= 3:
                # 检查是否已经计算了平面
                if status['plane_computed']:
                    # 平面已计算完成
                    self._on_plane_calculation_completed()
                elif status['ready_to_compute']:
                    # 可以计算平面
                    self._trigger_plane_calculation()
                
        except Exception as e:
            logging.error(f"检查标志点进度失败: {e}")

    def _trigger_plane_calculation(self):
        """
        触发平面计算
        
        当用户放置了3个点后，自动触发平面计算
        """
        logging.info("触发平面计算...")
        
        try:
            self._update_landmark_progress("🔄 正在计算平面...")
            self._update_instruction("⏳ 正在计算最佳拟合平面，请稍候...")
            
            # 调用平面计算
            result = self.logic.check_and_compute_plane_if_ready("Native_Annulus_Points")
            
            if result:
                logging.info("平面计算成功")
                # 计算完成的处理在 _on_plane_calculation_completed 中进行
            else:
                logging.error("平面计算失败")
                self._update_instruction("❌ 平面计算失败，请检查标志点位置")
                self._update_landmark_progress("❌ 计算失败")
                self._stop_landmark_monitoring()
                self._enable_native_annulus_button()
                
        except Exception as e:
            logging.error(f"平面计算触发失败: {e}")
            self._update_instruction(f"❌ 平面计算失败: {str(e)}")
            self._update_landmark_progress("❌ 计算错误")
            self._stop_landmark_monitoring()
            self._enable_native_annulus_button()

    def _on_plane_calculation_completed(self):
        """
        平面计算完成的处理
        
        显示计算结果并提供下一步操作指导
        """
        logging.info("平面计算完成")
        
        try:
            # 停止监控
            self._stop_landmark_monitoring()
            
            # 获取计算结果
            plane_data = self.session.get_reconstructed_plane("native_annulus")
            
            if plane_data:
                # 显示成功信息
                origin = plane_data['origin']
                normal = plane_data['normal']
                
                self._update_instruction(
                    "🎉 原生瓣环平面重建完成！\n"
                    f"平面原点: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})\n"
                    f"法向量: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})\n"
                    "您可以继续定义其他解剖标志点。"
                )
                self._update_landmark_progress("✅ 平面重建完成")
                self._update_status("原生瓣环平面重建成功完成")
                
                # 刷新视图并对准新创建的平面Model
                self._refresh_3d_view()
                self._center_view_on_model("Native_Annulus_Plane")
                
                # 重新启用按钮，允许重新定义
                self._enable_native_annulus_button()
                
                # 隐藏嵌入式控制面板
                self._hide_markups_controls()
                
                # 刷新3D视图以显示新创建的平面
                self._refresh_3d_view()
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(25)  # 假设原生瓣环完成后进度为25%
                
                logging.info("原生瓣环平面重建流程完成")
                
            else:
                self._update_instruction("❌ 未能获取平面计算结果")
                self._update_landmark_progress("❌ 结果获取失败")
                self._enable_native_annulus_button()
                
        except Exception as e:
            logging.error(f"平面计算完成处理失败: {e}")
            self._update_instruction(f"❌ 处理结果时发生错误: {str(e)}")
            self._update_landmark_progress("❌ 处理失败")
            self._enable_native_annulus_button()

    def _on_define_native_commissure(self):
        """
        处理定义原生连合按钮点击事件
        
        启动原生连合标志点定义流程
        """
        logging.info("用户点击了'定义原生连合'按钮")
        
        try:
            # 更新UI状态
            self._update_instruction("正在创建原生连合标志点节点...")
            self._update_landmark_progress("⏳ 初始化连合定义...")
            
            # 禁用按钮，防止重复点击
            self.native_commissure_button.setEnabled(False)
            self.native_commissure_button.setText("正在初始化...")
            
            # 调用逻辑层的连合定义方法
            result = self.logic.define_native_commissure_points()
            
            if result:
                self._update_instruction(
                    "✅ 原生连合标志点节点已创建！\n"
                    "请在3D视图中依次放置3个原生连合点：\n"
                    "1️⃣ 第一个点：右冠-左冠连合位置\n"
                    "2️⃣ 第二个点：左冠-无冠连合位置\n" 
                    "3️⃣ 第三个点：无冠-右冠连合位置"
                )
                self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
                
                # 显示嵌入式标志点控制面板
                self._show_markups_controls()
                
                # 启动定时器监控连合点放置进度
                self._start_commissure_monitoring()
                
                # 更新状态栏
                self._update_status("Native_Commissure_Points节点已激活，请开始放置连合点")
                
                logging.info("原生连合定义流程已启动")
                
            else:
                self._update_instruction("❌ 连合标志点节点创建失败，请重试")
                self._update_landmark_progress("❌ 创建失败")
                self._enable_native_commissure_button()
                self._update_status("原生连合标志点创建失败")
                logging.error("原生连合定义流程启动失败")
                
        except Exception as e:
            logging.error(f"定义原生连合失败: {e}")
            self._update_instruction(f"❌ 发生错误: {str(e)}")
            self._update_landmark_progress("❌ 操作失败")
            self._enable_native_commissure_button()
            self._update_status("原生连合定义失败，请检查日志")

    def _start_commissure_monitoring(self):
        """
        启动连合点放置监控
        
        定期检查用户放置的连合点数量，并在达到3个点时自动处理
        """
        # 创建定时器（如果还没有的话）
        if not hasattr(self, 'commissure_timer'):
            self.commissure_timer = qt.QTimer()
            self.commissure_timer.timeout.connect(self._check_commissure_progress)
        
        self.commissure_timer.start(1000)  # 每秒检查一次
        
        logging.info("连合点监控定时器已启动")

    def _check_commissure_progress(self):
        """
        检查连合点放置进度
        
        监控用户在3D视图中放置的连合点数量，并提供实时反馈
        """
        try:
            # 获取状态信息
            status = self.logic.get_native_commissure_status()
            
            if not status['node_exists']:
                # 节点不存在，停止监控
                self._stop_commissure_monitoring()
                self._enable_native_commissure_button()
                return
            
            points_placed = status['points_placed']
            points_needed = status['points_needed']
            
            # 更新进度显示
            if points_placed == 0:
                self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
            elif points_placed == 1:
                self._update_landmark_progress("📍 已放置1个连合点，还需要2个点 (1/3)")
                self._update_instruction(
                    "✅ 第一个连合点已放置！\n"
                    "请继续放置第二个连合点（左冠-无冠连合位置）"
                )
            elif points_placed == 2:
                self._update_landmark_progress("📍 已放置2个连合点，还需要1个点 (2/3)")
                self._update_instruction(
                    "✅ 前两个连合点已放置！\n"
                    "请放置第三个连合点（无冠-右冠连合位置）"
                )
            elif points_placed >= 3:
                # 检查是否已经完成定义
                if status['points_complete']:
                    self._on_commissure_definition_completed()
                
        except Exception as e:
            logging.error(f"检查连合点进度失败: {e}")

    def _on_commissure_definition_completed(self):
        """
        连合点定义完成的处理
        
        显示完成结果并提供后续操作指导
        """
        logging.info("连合点定义完成")
        
        try:
            # 停止监控
            self._stop_commissure_monitoring()
            
            # 获取连合点信息
            landmark_node = self.session.get_landmark_node("Native_Commissure_Points")
            
            if landmark_node:
                # 显示成功信息
                self._update_instruction(
                    "🎉 原生连合点定义完成！\n"
                    "✅ 已自动命名3个连合点：\n"
                    "• RCC_LCC: 右冠-左冠连合\n"
                    "• LCC_NCC: 左冠-无冠连合\n"
                    "• NCC_RCC: 无冠-右冠连合\n"
                    "您可以继续定义其他解剖标志点。"
                )
                self._update_landmark_progress("✅ 连合点定义完成")
                self._update_status("原生连合点定义成功完成")
                
                # 刷新视图
                self._refresh_3d_view()
                self._center_view_on_markups("Native_Commissure_Points")
                
                # 重新启用按钮，允许重新定义
                self._enable_native_commissure_button()
                
                # 隐藏嵌入式控制面板
                self._hide_markups_controls()
                
                # 更新进度条
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(50)  # 假设连合点完成后进度为50%
                
                logging.info("原生连合点定义流程完成")
                
            else:
                self._update_instruction("❌ 未能获取连合点信息")
                self._update_landmark_progress("❌ 获取信息失败")
                self._enable_native_commissure_button()
                
        except Exception as e:
            logging.error(f"连合定义完成处理失败: {e}")
            self._update_instruction(f"❌ 处理结果时发生错误: {str(e)}")
            self._update_landmark_progress("❌ 处理失败")
            self._enable_native_commissure_button()

    def _stop_commissure_monitoring(self):
        """停止连合点监控定时器"""
        if hasattr(self, 'commissure_timer') and self.commissure_timer:
            self.commissure_timer.stop()
            self.commissure_timer = None
            logging.info("连合点监控定时器已停止")
        
        # 同时隐藏控制面板
        self._hide_markups_controls()

    def _enable_native_commissure_button(self):
        """重新启用原生连合按钮"""
        if hasattr(self, 'native_commissure_button'):
            self.native_commissure_button.setEnabled(True)
            self.native_commissure_button.setText("定义原生连合")

    def _stop_landmark_monitoring(self):
        """停止标志点监控定时器"""
        if hasattr(self, 'landmark_timer') and self.landmark_timer:
            self.landmark_timer.stop()
            self.landmark_timer = None
            logging.info("标志点监控定时器已停止")
        
        # 同时隐藏控制面板
        self._hide_markups_controls()

    def _stop_all_monitoring(self):
        """停止所有监控定时器"""
        # 停止瓣环监控
        self._stop_landmark_monitoring()
        
        # 停止连合点监控
        self._stop_commissure_monitoring()
        
        logging.info("所有监控定时器已停止")

    def _enable_native_annulus_button(self):
        """重新启用原生瓣环按钮"""
        if hasattr(self, 'native_annulus_button'):
            self.native_annulus_button.setEnabled(True)
            self.native_annulus_button.setText("定义原生瓣环")

    def _update_instruction(self, message: str):
        """更新操作指导文本"""
        if hasattr(self, 'instruction_label'):
            self.instruction_label.setText(message)
            logging.debug(f"指导更新: {message}")

    def _update_landmark_progress(self, message: str):
        """更新标志点进度状态"""
        if hasattr(self, 'landmark_progress_label'):
            self.landmark_progress_label.setText(message)
            logging.debug(f"进度更新: {message}")

    def _show_markups_controls(self):
        """显示嵌入式标志点控制面板"""
        if hasattr(self, 'place_mode_button'):
            self.place_mode_button.setVisible(True)
        if hasattr(self, 'delete_last_button'):
            self.delete_last_button.setVisible(True)
        if hasattr(self, 'clear_points_button'):
            self.clear_points_button.setVisible(True)
        logging.info("标志点控制面板已显示")

    def _hide_markups_controls(self):
        """隐藏嵌入式标志点控制面板"""
        if hasattr(self, 'place_mode_button'):
            self.place_mode_button.setVisible(False)
        if hasattr(self, 'delete_last_button'):
            self.delete_last_button.setVisible(False)
        if hasattr(self, 'clear_points_button'):
            self.clear_points_button.setVisible(False)
        logging.info("标志点控制面板已隐藏")

    def _on_toggle_place_mode(self):
        """切换标志点放置模式"""
        try:
            interaction_node = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interaction_node:
                current_mode = interaction_node.GetCurrentInteractionMode()
                if current_mode == interaction_node.Place:
                    # 当前是放置模式，切换到查看模式
                    interaction_node.SetCurrentInteractionMode(interaction_node.ViewTransform)
                    self.place_mode_button.setText("🎯 放置模式")
                    # 设置为灰色（查看模式）
                    self.place_mode_button.setStyleSheet("""
                        QPushButton {
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 11px;
                            min-width: 80px;
                        }
                        QPushButton:hover {
                            background-color: #5a6268;
                        }
                        QPushButton:pressed {
                            background-color: #545b62;
                        }
                    """)
                    logging.info("切换到查看模式")
                else:
                    # 当前不是放置模式，切换到放置模式
                    interaction_node.SetCurrentInteractionMode(interaction_node.Place)
                    self.place_mode_button.setText("👁️ 查看模式")
                    # 设置为绿色（放置模式）
                    self.place_mode_button.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 11px;
                            min-width: 80px;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                        QPushButton:pressed {
                            background-color: #1e7e34;
                        }
                    """)
                    logging.info("切换到放置模式")
        except Exception as e:
            logging.error(f"切换放置模式失败: {e}")

    def _on_delete_last_point(self):
        """删除最后放置的标志点"""
        try:
            # 确定当前活动的标志点节点
            active_landmark_node = None
            active_node_name = ""
            
            # 检查瓣环点
            annulus_node = self.session.get_landmark_node("Native_Annulus_Points")
            if annulus_node and hasattr(self, 'landmark_timer') and self.landmark_timer and self.landmark_timer.isActive():
                active_landmark_node = annulus_node
                active_node_name = "Native_Annulus_Points"
            
            # 检查连合点
            commissure_node = self.session.get_landmark_node("Native_Commissure_Points")
            if commissure_node and hasattr(self, 'commissure_timer') and self.commissure_timer and self.commissure_timer.isActive():
                active_landmark_node = commissure_node
                active_node_name = "Native_Commissure_Points"
            
            if active_landmark_node and active_landmark_node.GetNumberOfControlPoints() > 0:
                last_index = active_landmark_node.GetNumberOfControlPoints() - 1
                active_landmark_node.RemoveNthControlPoint(last_index)
                logging.info(f"删除了{active_node_name}的第 {last_index + 1} 个标志点")
                
                # 更新进度显示
                remaining_points = active_landmark_node.GetNumberOfControlPoints()
                if active_node_name == "Native_Annulus_Points":
                    self._update_landmark_progress(f"📍 已放置 {remaining_points} 个点，还需要 {3 - remaining_points} 个点 ({remaining_points}/3)")
                elif active_node_name == "Native_Commissure_Points":
                    self._update_landmark_progress(f"📍 已放置 {remaining_points} 个连合点，还需要 {3 - remaining_points} 个点 ({remaining_points}/3)")
                
            else:
                logging.warning("没有可删除的标志点或没有活动的标志点节点")
                
        except Exception as e:
            logging.error(f"删除标志点失败: {e}")

    def _on_clear_all_points(self):
        """清除所有标志点"""
        try:
            # 确定当前活动的标志点节点
            active_landmark_node = None
            active_node_name = ""
            
            # 检查瓣环点
            annulus_node = self.session.get_landmark_node("Native_Annulus_Points")
            if annulus_node and hasattr(self, 'landmark_timer') and self.landmark_timer and self.landmark_timer.isActive():
                active_landmark_node = annulus_node
                active_node_name = "Native_Annulus_Points"
            
            # 检查连合点
            commissure_node = self.session.get_landmark_node("Native_Commissure_Points")
            if commissure_node and hasattr(self, 'commissure_timer') and self.commissure_timer and self.commissure_timer.isActive():
                active_landmark_node = commissure_node
                active_node_name = "Native_Commissure_Points"
            
            if active_landmark_node:
                active_landmark_node.RemoveAllControlPoints()
                logging.info(f"清除了{active_node_name}的所有标志点")
                
                # 重置进度显示
                if active_node_name == "Native_Annulus_Points":
                    self._update_landmark_progress("📍 请在3D视图中放置3个瓣环点 (0/3)")
                    self._update_instruction(
                        "🔄 已清除所有瓣环标志点\n"
                        "请重新在3D视图中依次放置3个原生瓣环上的点"
                    )
                elif active_node_name == "Native_Commissure_Points":
                    self._update_landmark_progress("📍 请在3D视图中放置3个连合点 (0/3)")
                    self._update_instruction(
                        "🔄 已清除所有连合标志点\n"
                        "请重新在3D视图中依次放置3个原生连合点"
                    )
            else:
                logging.warning("未找到活动的标志点节点")
                
        except Exception as e:
            logging.error(f"清除标志点失败: {e}")

    def _refresh_3d_view(self):
        """
        刷新3D视图以显示新创建的markups
        """
        try:
            # 获取3D视图
            threeDWidget = slicer.app.layoutManager().threeDWidget(0)
            if threeDWidget:
                threeDView = threeDWidget.threeDView()
                threeDView.resetFocalPoint()
                
            # 强制渲染更新
            slicer.app.processEvents()
            
            # 确保markups模块的工具栏可见
            markupsToolBar = slicer.util.findChild(slicer.util.mainWindow(), 'MarkupsToolBar')
            if markupsToolBar:
                markupsToolBar.setVisible(True)
            
            logging.info("3D视图已刷新，markups可见")
            
        except Exception as e:
            logging.error(f"刷新3D视图失败: {e}")

    def _center_view_on_model(self, node_name: str):
        """将视图中心对准指定的Model节点"""
        try:
            node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if node and hasattr(node, 'GetPolyData'):
                polydata = node.GetPolyData()
                if polydata:
                    bounds = [0.0] * 6
                    polydata.GetBounds(bounds)
                    
                    # 计算中心点
                    center = [(bounds[0] + bounds[1])/2, 
                             (bounds[2] + bounds[3])/2, 
                             (bounds[4] + bounds[5])/2]
                    
                    # 设置3D视图的焦点
                    threeDWidget = slicer.app.layoutManager().threeDWidget(0)
                    if threeDWidget:
                        threeDView = threeDWidget.threeDView()
                        camera = threeDView.camera()
                        camera.SetFocalPoint(center)
                        camera.SetPosition(center[0], center[1] - 100, center[2] + 50)
                        camera.SetViewUp(0, 0, 1)
                        threeDView.forceRender()
                        
                    logging.info(f"视图已对准Model {node_name}")
                    
        except Exception as e:
            logging.error(f"对准Model视图失败: {e}")

    def _center_view_on_markups(self, node_name: str):
        """将视图中心对准指定的markups节点"""
        try:
            node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if node and hasattr(node, 'GetBounds'):
                bounds = [0.0] * 6
                node.GetBounds(bounds)
                
                # 计算中心点
                center = [(bounds[0] + bounds[1])/2, 
                         (bounds[2] + bounds[3])/2, 
                         (bounds[4] + bounds[5])/2]
                
                # 设置3D视图的焦点
                threeDWidget = slicer.app.layoutManager().threeDWidget(0)
                if threeDWidget:
                    threeDView = threeDWidget.threeDView()
                    camera = threeDView.camera()
                    camera.SetFocalPoint(center)
                    camera.SetPosition(center[0], center[1] - 100, center[2] + 50)
                    camera.SetViewUp(0, 0, 1)
                    threeDView.forceRender()
                    
                logging.info(f"视图已对准 {node_name}")
                
        except Exception as e:
            logging.error(f"对准视图失败: {e}")

    def _on_button_clicked(self, button_name: str):
        """
        通用按钮点击槽函数 - 任务5要求
        
        Args:
            button_name: 被点击按钮的名称
        """
        logging.info(f"{button_name} clicked")
        
        # 同时更新状态显示，提供用户反馈
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"用户点击了: {button_name}")

    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if self.logic:
            self.logic.session = session

    def on_deactivated(self):
        """模块停用时调用"""
        logging.info("模块二已停用")
        # 停止所有监控定时器
        self._stop_all_monitoring()

    def cleanup(self):
        """清理资源"""
        # 停止所有监控定时器
        self._stop_all_monitoring()
        
        # 清理逻辑层资源
        if self.logic:
            self.logic.cleanup()
        
        logging.info("模块二界面清理完成")
