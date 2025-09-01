"""
瓣膜叠加组件 - Valve Overlay Widget

提供一键将瓣膜支架（valve）叠加到Red切片视图的功能，支持：
- 瓣膜支架自动对齐到当前Red切片位置
- 透明度调节功能
- 叠加状态显示与控制
- 变换微调选项

作者：TAVR Research Team
创建时间：2025年9月
"""

import logging
import os
import sys
from typing import Optional, Callable
import qt

# 轻量依赖，仅在需要时注入
try:
    from ..core.session import TAVRStudySession
    from ..widgets.section_card import SectionCard
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from widgets.section_card import SectionCard


class ValveOverlayWidget(qt.QWidget):
    """
    瓣膜叠加组件
    
    提供瓣膜支架到Red切片视图的一键叠加功能，包括：
    - 自动检测瓣膜数据
    - 一键叠加/取消叠加
    - 透明度实时调节
    - 变换微调选项
    - 状态指示与反馈
    """
    
    # 定义信号
    overlayEnabled = qt.Signal(bool)      # 叠加启用/禁用信号
    opacityChanged = qt.Signal(float)     # 透明度改变信号
    statusUpdated = qt.Signal(str)        # 状态更新信号
    
    def __init__(self, session: Optional[TAVRStudySession] = None, parent=None):
        """
        初始化瓣膜叠加组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.valve_node = None
        self.transform_node = None
        self.is_overlay_active = False
        self.current_opacity = 0.6
        
        # 设置组件属性
        self.setObjectName("ValveOverlayWidget")
        
        # 回调函数列表
        self.overlay_callbacks = []
        self.opacity_callbacks = []
        
        # 创建界面
        self._setup_ui()
        
        # 初始化检查瓣膜数据
        self._check_valve_availability()
        
        logging.info("ValveOverlayWidget 初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # 使用SectionCard包装
        self.section_card = SectionCard(
            title="瓣膜支架叠加", 
            icon_text="🩺", 
            variant="blue",
            parent=self
        )
        
        # 在卡片内容区创建控件
        self._create_controls()
        
        main_layout.addWidget(self.section_card)
    
    def _create_controls(self):
        """创建控制组件"""
        # 状态显示区域
        self._create_status_section()
        
        # 主操作按钮区域
        self._create_action_section()
        
        # 透明度调节区域
        self._create_opacity_section()
        
        # 高级选项区域
        self._create_advanced_section()
    
    def _create_status_section(self):
        """创建状态显示区域"""
        status_frame = qt.QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        status_layout = qt.QHBoxLayout(status_frame)
        status_layout.setSpacing(8)
        
        # 瓣膜状态图标
        self.valve_status_icon = qt.QLabel("❓")
        self.valve_status_icon.setStyleSheet("font-size: 16px; color: #6c757d;")
        self.valve_status_icon.setToolTip("瓣膜数据状态")
        
        # 状态文本
        self.status_label = qt.QLabel("正在检查瓣膜数据...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #495057;
                background: transparent;
            }
        """)
        
        status_layout.addWidget(self.valve_status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.section_card.add_widget(status_frame)
    
    def _create_action_section(self):
        """创建主操作按钮区域"""
        action_layout = qt.QHBoxLayout()
        action_layout.setSpacing(12)
        
        # 主操作按钮
        self.overlay_btn = qt.QPushButton("🔄 启用叠加")
        self.overlay_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.overlay_btn.clicked.connect(self._toggle_overlay)
        self.overlay_btn.setEnabled(False)
        
        # 刷新按钮
        refresh_btn = qt.QPushButton("🔄")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                max-width: 36px;
                min-width: 36px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.setToolTip("重新检查瓣膜数据")
        refresh_btn.clicked.connect(self._check_valve_availability)
        
        action_layout.addWidget(self.overlay_btn)
        action_layout.addWidget(refresh_btn)
        action_layout.addStretch()
        
        self.section_card.add_layout(action_layout)
    
    def _create_opacity_section(self):
        """创建透明度调节区域"""
        opacity_frame = qt.QFrame()
        opacity_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        opacity_layout = qt.QVBoxLayout(opacity_frame)
        opacity_layout.setSpacing(6)
        
        # 透明度标签
        opacity_header = qt.QHBoxLayout()
        opacity_label = qt.QLabel("透明度调节")
        opacity_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #495057;
                background: transparent;
            }
        """)
        
        self.opacity_value_label = qt.QLabel("60%")
        self.opacity_value_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #007bff;
                background: transparent;
                font-weight: bold;
            }
        """)
        
        opacity_header.addWidget(opacity_label)
        opacity_header.addStretch()
        opacity_header.addWidget(self.opacity_value_label)
        
        opacity_layout.addLayout(opacity_header)
        
        # 透明度滑块
        self.opacity_slider = qt.QSlider(qt.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(60)  # 默认60%
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007bff;
                border: 1px solid #007bff;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #dee2e6;
                border: 1px solid #dee2e6;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007bff;
                border: 1px solid #007bff;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.opacity_slider.setEnabled(False)
        
        opacity_layout.addWidget(self.opacity_slider)
        
        self.section_card.add_widget(opacity_frame)
    
    def _create_advanced_section(self):
        """创建高级选项区域"""
        advanced_layout = qt.QHBoxLayout()
        advanced_layout.setSpacing(8)
        
        # 微调变换按钮
        adjust_btn = qt.QPushButton("⚙️ 微调位置")
        adjust_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        adjust_btn.setToolTip("打开Transforms模块进行精细位置调整")
        adjust_btn.clicked.connect(self._open_transforms_module)
        self.adjust_btn = adjust_btn
        adjust_btn.setEnabled(False)
        
        # 重置按钮
        reset_btn = qt.QPushButton("🔄 重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        reset_btn.setToolTip("重置瓣膜叠加到初始状态")
        reset_btn.clicked.connect(self._reset_overlay)
        self.reset_btn = reset_btn
        reset_btn.setEnabled(False)
        
        advanced_layout.addWidget(adjust_btn)
        advanced_layout.addWidget(reset_btn)
        advanced_layout.addStretch()
        
        self.section_card.add_layout(advanced_layout)
    
    def _check_valve_availability(self):
        """检查瓣膜数据可用性"""
        try:
            # 尝试在Slicer中查找valve节点
            import slicer
            
            def find_volume_by_name(class_name, target_name):
                nodes = slicer.util.getNodesByClass(class_name)
                exact = [n for n in nodes if n.GetName() == target_name]
                if exact:
                    return exact[0]
                lower = target_name.lower()
                partial = [n for n in nodes if lower in n.GetName().lower()]
                return partial[0] if partial else None
            
            # 查找valve节点
            valve_node = find_volume_by_name('vtkMRMLVectorVolumeNode', 'valve')
            if valve_node is None:
                valve_node = find_volume_by_name('vtkMRMLScalarVolumeNode', 'valve')
            
            if valve_node:
                self.valve_node = valve_node
                self.valve_status_icon.setText("✅")
                self.valve_status_icon.setStyleSheet("font-size: 16px; color: #28a745;")
                self.status_label.setText(f"已找到瓣膜数据: {valve_node.GetName()}")
                self.overlay_btn.setEnabled(True)
                
                # 检查是否已有叠加状态
                self._check_overlay_status()
                
            else:
                self.valve_node = None
                self.valve_status_icon.setText("❌")
                self.valve_status_icon.setStyleSheet("font-size: 16px; color: #dc3545;")
                self.status_label.setText("未找到瓣膜数据 (名称: valve)")
                self.overlay_btn.setEnabled(False)
                self._update_overlay_status(False)
            
        except Exception as e:
            logging.error(f"检查瓣膜数据时出错: {e}")
            self.valve_status_icon.setText("⚠️")
            self.valve_status_icon.setStyleSheet("font-size: 16px; color: #ffc107;")
            self.status_label.setText(f"检查失败: {str(e)}")
            self.overlay_btn.setEnabled(False)
    
    def _check_overlay_status(self):
        """检查当前叠加状态"""
        try:
            import slicer
            
            # 检查变换节点是否存在
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', 'ValveToRedSlice')
            
            # 检查Red视图前景设置
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if red_widget:
                comp_node = red_widget.mrmlSliceCompositeNode()
                foreground_id = comp_node.GetForegroundVolumeID()
                
                # 判断是否已经叠加
                is_active = (transform_node is not None and 
                           self.valve_node is not None and 
                           foreground_id == self.valve_node.GetID())
                
                self._update_overlay_status(is_active)
                
                if is_active:
                    # 更新透明度显示
                    opacity = comp_node.GetForegroundOpacity()
                    self.current_opacity = opacity
                    self.opacity_slider.setValue(int(opacity * 100))
                    self.opacity_value_label.setText(f"{int(opacity * 100)}%")
                
        except Exception as e:
            logging.error(f"检查叠加状态时出错: {e}")
    
    def _toggle_overlay(self):
        """切换叠加状态"""
        if self.is_overlay_active:
            self._disable_overlay()
        else:
            self._enable_overlay()
    
    def _enable_overlay(self):
        """启用瓣膜叠加"""
        try:
            import slicer
            import vtk
            
            if not self.valve_node:
                self.statusUpdated.emit("错误: 瓣膜数据不可用")
                return
            
            # 显示进度反馈
            self.overlay_btn.setText("🔄 正在叠加...")
            self.overlay_btn.setEnabled(False)
            qt.QApplication.processEvents()
            
            # 执行叠加脚本（基于文档中的逻辑）
            success = self._execute_valve_overlay()
            
            if success:
                self._update_overlay_status(True)
                self.statusUpdated.emit("瓣膜叠加已启用")
                self.overlayEnabled.emit(True)
                
                # 调用回调函数
                for callback in self.overlay_callbacks:
                    try:
                        callback(True)
                    except Exception as e:
                        logging.error(f"执行叠加回调失败: {e}")
            else:
                self.overlay_btn.setText("🔄 启用叠加")
                self.overlay_btn.setEnabled(True)
                self.statusUpdated.emit("瓣膜叠加失败")
                
        except Exception as e:
            logging.error(f"启用瓣膜叠加时出错: {e}")
            self.overlay_btn.setText("🔄 启用叠加")
            self.overlay_btn.setEnabled(True)
            self.statusUpdated.emit(f"叠加错误: {str(e)}")
    
    def _disable_overlay(self):
        """禁用瓣膜叠加"""
        try:
            import slicer
            
            # 获取Red视图
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if red_widget:
                comp_node = red_widget.mrmlSliceCompositeNode()
                
                # 清除前景设置
                comp_node.SetForegroundVolumeID("")
                comp_node.SetForegroundOpacity(0.0)
                
                # 移除变换（可选）
                if self.valve_node:
                    self.valve_node.SetAndObserveTransformNodeID("")
                
                red_widget.sliceView().scheduleRender()
            
            self._update_overlay_status(False)
            self.statusUpdated.emit("瓣膜叠加已禁用")
            self.overlayEnabled.emit(False)
            
            # 调用回调函数
            for callback in self.overlay_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    logging.error(f"执行禁用回调失败: {e}")
                    
        except Exception as e:
            logging.error(f"禁用瓣膜叠加时出错: {e}")
            self.statusUpdated.emit(f"禁用错误: {str(e)}")
    
    def _execute_valve_overlay(self) -> bool:
        """执行瓣膜叠加（基于文档逻辑）"""
        try:
            import slicer
            import vtk
            
            # 获取Red切片方向
            lm = slicer.app.layoutManager()
            red_widget = lm.sliceWidget('Red')
            if not red_widget:
                logging.error('未找到 Red 视图')
                return False
            
            red_slice_node = red_widget.mrmlSliceNode()
            slice_to_ras = red_slice_node.GetSliceToRAS()
            
            # 构建中心化+缩放矩阵
            img = self.valve_node.GetImageData()
            if not img:
                logging.error('valve 体数据没有 ImageData')
                return False
            
            width, height, depth = img.GetDimensions()
            spx, spy, spz = self.valve_node.GetSpacing()
            
            S = vtk.vtkMatrix4x4()
            S.Identity()
            S.SetElement(0, 0, float(spx) if spx else 1.0)
            S.SetElement(1, 1, float(spy) if spy else 1.0)
            S.SetElement(2, 2, 1.0)
            
            cx = (width - 1) * 0.5
            cy = (height - 1) * 0.5
            S.SetElement(0, 3, -cx * (float(spx) if spx else 1.0))
            S.SetElement(1, 3, -cy * (float(spy) if spy else 1.0))
            
            # 获取valve IJK->RAS并求逆
            M_ijkToRas = vtk.vtkMatrix4x4()
            self.valve_node.GetIJKToRASMatrix(M_ijkToRas)
            M_ijkToRas_inv = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Invert(M_ijkToRas, M_ijkToRas_inv)
            
            # 计算父变换: P = SliceToRAS * S * (IJKToRAS)^-1
            P_tmp = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(S, M_ijkToRas_inv, P_tmp)
            P = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(slice_to_ras, P_tmp, P)
            
            # 创建/应用变换节点
            transform_name = 'ValveToRedSlice'
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', transform_name)
            if not transform_node:
                transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', transform_name)
            
            transform_node.SetMatrixTransformToParent(P)
            self.valve_node.SetAndObserveTransformNodeID(transform_node.GetID())
            self.transform_node = transform_node
            
            # 配置Red切片叠加
            comp_node = red_widget.mrmlSliceCompositeNode()
            comp_node.SetForegroundVolumeID(self.valve_node.GetID())
            comp_node.SetForegroundOpacity(self.current_opacity)
            
            # 显示优化
            valve_display = self.valve_node.GetDisplayNode()
            if valve_display:
                try:
                    valve_display.SetInterpolate(False)
                except Exception:
                    pass
            
            red_widget.sliceView().scheduleRender()
            
            logging.info(f"瓣膜叠加成功: {self.valve_node.GetName()}")
            return True
            
        except Exception as e:
            logging.error(f"执行瓣膜叠加失败: {e}")
            return False
    
    def _update_overlay_status(self, is_active: bool):
        """更新叠加状态UI"""
        self.is_overlay_active = is_active
        
        if is_active:
            self.overlay_btn.setText("❌ 禁用叠加")
            self.overlay_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.opacity_slider.setEnabled(True)
            self.adjust_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
        else:
            self.overlay_btn.setText("🔄 启用叠加")
            self.overlay_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.opacity_slider.setEnabled(False)
            self.adjust_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
        
        self.overlay_btn.setEnabled(True)
    
    def _on_opacity_changed(self, value: int):
        """透明度改变时的回调"""
        opacity = value / 100.0
        self.current_opacity = opacity
        self.opacity_value_label.setText(f"{value}%")
        
        # 如果叠加已激活，立即应用透明度变化
        if self.is_overlay_active:
            try:
                import slicer
                lm = slicer.app.layoutManager()
                red_widget = lm.sliceWidget('Red')
                if red_widget:
                    comp_node = red_widget.mrmlSliceCompositeNode()
                    comp_node.SetForegroundOpacity(opacity)
                    red_widget.sliceView().scheduleRender()
            except Exception as e:
                logging.error(f"应用透明度变化失败: {e}")
        
        # 发出信号
        self.opacityChanged.emit(opacity)
        
        # 调用回调函数
        for callback in self.opacity_callbacks:
            try:
                callback(opacity)
            except Exception as e:
                logging.error(f"执行透明度回调失败: {e}")
    
    def _open_transforms_module(self):
        """打开Transforms模块进行微调"""
        try:
            import slicer
            
            # 切换到Transforms模块
            slicer.util.selectModule('Transforms')
            
            # 如果有变换节点，选择它
            if self.transform_node:
                slicer.mrmlScene.SetActiveID("vtkMRMLLinearTransformNode", self.transform_node.GetID())
            
            self.statusUpdated.emit("已打开Transforms模块进行微调")
            
        except Exception as e:
            logging.error(f"打开Transforms模块失败: {e}")
            self.statusUpdated.emit("打开Transforms模块失败")
    
    def _reset_overlay(self):
        """重置瓣膜叠加"""
        try:
            if self.is_overlay_active:
                self._disable_overlay()
            
            # 重置透明度
            self.current_opacity = 0.6
            self.opacity_slider.setValue(60)
            self.opacity_value_label.setText("60%")
            
            # 删除变换节点
            import slicer
            transform_node = slicer.util.getFirstNodeByClassByName('vtkMRMLLinearTransformNode', 'ValveToRedSlice')
            if transform_node:
                slicer.mrmlScene.RemoveNode(transform_node)
                self.transform_node = None
            
            self.statusUpdated.emit("瓣膜叠加已重置")
            
        except Exception as e:
            logging.error(f"重置瓣膜叠加失败: {e}")
            self.statusUpdated.emit(f"重置失败: {str(e)}")
    
    # 公共接口方法
    def add_overlay_callback(self, callback: Callable[[bool], None]):
        """添加叠加状态变化回调函数"""
        self.overlay_callbacks.append(callback)
    
    def add_opacity_callback(self, callback: Callable[[float], None]):
        """添加透明度变化回调函数"""
        self.opacity_callbacks.append(callback)
    
    def get_overlay_status(self) -> bool:
        """获取当前叠加状态"""
        return self.is_overlay_active
    
    def get_current_opacity(self) -> float:
        """获取当前透明度"""
        return self.current_opacity
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        opacity = max(0.0, min(1.0, opacity))  # 限制范围[0,1]
        self.opacity_slider.setValue(int(opacity * 100))
    
    def force_enable_overlay(self):
        """强制启用叠加（外部调用）"""
        if not self.is_overlay_active and self.valve_node:
            self._enable_overlay()
    
    def force_disable_overlay(self):
        """强制禁用叠加（外部调用）"""
        if self.is_overlay_active:
            self._disable_overlay()
    
    def refresh_valve_data(self):
        """刷新瓣膜数据检查（外部调用）"""
        self._check_valve_availability()
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
    
    def cleanup(self):
        """清理资源"""
        # 清理回调函数列表
        self.overlay_callbacks.clear()
        self.opacity_callbacks.clear()
        
        # 如果叠加处于激活状态，先禁用
        if self.is_overlay_active:
            try:
                self._disable_overlay()
            except Exception as e:
                logging.error(f"清理时禁用叠加失败: {e}")
        
        logging.info("ValveOverlayWidget 清理完成")


# 工厂函数，方便创建组件
def create_valve_overlay_widget(session: Optional[TAVRStudySession] = None, parent=None) -> ValveOverlayWidget:
    """
    创建瓣膜叠加组件的工厂函数
    
    Args:
        session: 会话对象
        parent: 父组件
        
    Returns:
        ValveOverlayWidget: 瓣膜叠加组件实例
    """
    return ValveOverlayWidget(session, parent)
