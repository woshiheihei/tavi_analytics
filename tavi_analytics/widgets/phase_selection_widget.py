"""
期像选择组件 - 公共UI组件

提供舒张末期和收缩末期的切换功能，可在多个模块中复用。
"""

import logging
from typing import Optional, Dict, Any, Callable
import qt

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager


class PhaseSelectionWidget(qt.QWidget):
    """
    期像选择组件
    
    提供舒张末期和收缩末期的切换界面和功能，包括：
    - 期像切换按钮
    - 自动期像切换
    - 期像状态检查
    - 状态更新回调
    - 分割和平面的显示/隐藏管理
    """
    
    # 定义信号
    phaseChanged = qt.Signal(str)  # 期像改变信号，参数为期像类型 ('diastole' 或 'systole')
    statusUpdated = qt.Signal(str)  # 状态更新信号，参数为状态消息
    
    def __init__(self, session: TAVRStudySession, parent=None):
        """
        初始化期像选择组件
        
        Args:
            session: TAVR研究会话对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.current_phase = None  # 当前选择的期像
        
        # 期像相关节点命名模式
        self.phase_suffixes = {
            'diastole': 'End_Diastole',
            'systole': 'End_Systole'
        }
        # 领域模型使用的期像键（与CardiacPhase保持一致）
        self.phase_domain_keys = {
            'diastole': 'end_diastole',
            'systole': 'end_systole',
        }
        
        # 设置组件属性
        self.setObjectName("PhaseSelectionWidget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("PhaseSelectionWidget 初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建期像控制框架
        phase_frame = LayoutManager.create_section_frame("期像选择")
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(phase_frame)
        
        phase_layout = qt.QVBoxLayout(phase_frame)
        
        # 期像切换按钮组
        switch_layout = qt.QHBoxLayout()
        switch_layout.setSpacing(8)
        
        # 切换到舒张末期按钮
        self.switch_to_diastole_button = LayoutManager.create_button_with_style(
            text="🫀 舒张末期",
            button_type="primary",
            size="small",
            min_height=32
        )
        self.switch_to_diastole_button.setObjectName("switchToDiastoleButton")
        self.switch_to_diastole_button.clicked.connect(self._on_switch_to_diastole)
        self.switch_to_diastole_button.setToolTip("切换到舒张末期进行分析（推荐用于全自动分析）")
        switch_layout.addWidget(self.switch_to_diastole_button)
        
        # 切换到收缩末期按钮
        self.switch_to_systole_button = LayoutManager.create_button_with_style(
            text="💓 收缩末期",
            button_type="secondary",
            size="small",
            min_height=32
        )
        self.switch_to_systole_button.setObjectName("switchToSystoleButton")
        self.switch_to_systole_button.clicked.connect(self._on_switch_to_systole)
        self.switch_to_systole_button.setToolTip("切换到收缩末期进行分析（用于动态分析）")
        switch_layout.addWidget(self.switch_to_systole_button)
        
        phase_layout.addLayout(switch_layout)
        
        # 添加说明文本
        self.phase_info_label = qt.QLabel(
            "💡 提示：请确保在模块一中已正确标记相应期像，然后点击上方按钮切换。"
        )
        self.phase_info_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                font-style: italic;
                padding: 4px;
                margin: 2px;
            }
        """)
        self.phase_info_label.setWordWrap(True)
        phase_layout.addWidget(self.phase_info_label)
        
        # 状态显示标签
        self.status_label = qt.QLabel("准备进行期像切换...")
        self.status_label.setAlignment(qt.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                margin: 2px 0px;
            }
        """)
        self.status_label.setWordWrap(True)
        phase_layout.addWidget(self.status_label)
    
    def set_info_text(self, text: str):
        """
        设置说明文本
        
        Args:
            text: 说明文本内容
        """
        if hasattr(self, 'phase_info_label'):
            self.phase_info_label.setText(text)
    
    def get_current_phase(self) -> Optional[str]:
        """
        获取当前选择的期像
        
        Returns:
            str: 当前期像 ('diastole' 或 'systole')，未选择时返回None
        """
        return self.current_phase
    
    def set_current_phase(self, phase: str):
        """
        设置当前期像并更新按钮状态以及节点可视化
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
        """
        if phase in ['diastole', 'systole']:
            old_phase = self.current_phase
            self.current_phase = phase
            self._update_phase_button_states(active_phase=phase)
            
            # 管理节点可视化：隐藏旧期像，显示新期像
            self._manage_phase_visibility(active_phase=phase, inactive_phase=old_phase)
            
            logging.info(f"期像设置为: {phase}")
    
    def _manage_phase_visibility(self, active_phase: str, inactive_phase: Optional[str] = None):
        """
        管理期像相关节点的可视化状态
        
        Args:
            active_phase: 要显示的期像 ('diastole' 或 'systole')
            inactive_phase: 要隐藏的期像 ('diastole' 或 'systole')，为None时隐藏所有其他期像
        """
        try:
            # 隐藏非活动期像的节点
            phases_to_hide = []
            if inactive_phase:
                phases_to_hide = [inactive_phase]
            else:
                # 隐藏所有其他期像
                phases_to_hide = [p for p in ['diastole', 'systole'] if p != active_phase]
            
            for phase in phases_to_hide:
                self._set_phase_nodes_visibility(phase, visible=False)
            
            # 显示活动期像的节点
            self._set_phase_nodes_visibility(active_phase, visible=True)
            
            logging.info(f"期像可视化管理完成: 显示 {active_phase}, 隐藏 {phases_to_hide}")
            
        except Exception as e:
            logging.error(f"管理期像可视化失败: {e}")
    
    def _set_phase_nodes_visibility(self, phase: str, visible: bool):
        """
        设置指定期像的所有节点的可视化状态
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
            visible: 是否可见
        """
        try:
            import slicer

            # 转换为领域模型的期像键
            phase_key = self.phase_domain_keys.get(phase)
            if not phase_key:
                logging.warning(f"未知期像: {phase}")
                return

            toggled_any = False
            segmentation_handled = False  # 新增：标记分割节点是否被成功处理

            # 1) 分割节点：从会话聚合根获取
            try:
                seg_node = None
                seg_node_valid = False
                if hasattr(self.session, 'get_phase_segmentation_node'):
                    seg_node = self.session.get_phase_segmentation_node(phase_key)
                    # 验证节点名称是否与期像匹配（防止错误注册）
                    if seg_node:
                        node_name = seg_node.GetName().lower()
                        phase_suffix = self.phase_suffixes.get(phase, '').lower()
                        if phase_suffix and phase_suffix.replace('_', '') in node_name.replace('_', ''):
                            seg_node_valid = True
                            logging.info(f"领域模型找到匹配的分割节点: {seg_node.GetName()}")
                        else:
                            logging.warning(f"分割节点名称与期像不匹配: {seg_node.GetName()} vs {phase}")
                            # 尝试重新注册正确的节点
                            correct_node = self._find_correct_segmentation_node(phase)
                            if correct_node:
                                self.session.set_phase_segmentation_node(phase_key, correct_node.GetID())
                                seg_node = correct_node
                                seg_node_valid = True
                                logging.info(f"重新注册正确的分割节点: {correct_node.GetName()}")
                            else:
                                seg_node = None  # 清空无效节点，让兜底机制处理
                
                if seg_node and seg_node_valid:
                    seg_disp = seg_node.GetDisplayNode()
                    if seg_disp:
                        # 设置主要可视化状态 - 根据期像可见性控制
                        seg_disp.SetVisibility(visible)
                        
                        # 3D 显示控制 - 根据期像显示/隐藏分割模型
                        try:
                            seg_disp.SetVisibility3D(visible)
                            
                            # 确保所有分段也按期像控制3D显示
                            segmentation = seg_node.GetSegmentation()
                            for i in range(segmentation.GetNumberOfSegments()):
                                segment_id = segmentation.GetNthSegmentID(i)
                                seg_disp.SetSegmentVisibility3D(segment_id, visible)
                                seg_disp.SetSegmentVisibility(segment_id, visible)
                        except Exception:
                            pass
                        
                        # 2D 显示控制 - 需求：在三个 slice 窗口中不显示分割
                        # 无论当前期像是否激活，统一关闭 2D 填充与轮廓
                        try:
                            seg_disp.SetVisibility2DFill(False)
                            seg_disp.SetVisibility2DOutline(False)
                        except Exception:
                            pass
                        
                        logging.info(f"设置分割(phase={phase_key}) 可视化: {visible}")
                        toggled_any = True
                        segmentation_handled = True
            except Exception as e:
                logging.warning(f"更新分割可视化失败(phase={phase_key}): {e}")

            # 2) 轮廓节点：通过PhaseContourRepository -> ContourDataManager -> 所有轮廓对象
            try:
                contour_mgr = None
                if hasattr(self.session, 'get_phase_contour_manager'):
                    contour_mgr = self.session.get_phase_contour_manager(phase_key)
                if contour_mgr and hasattr(contour_mgr, 'get_all_contours'):
                    # 使用领域模型的通用API获取所有轮廓，而不是硬编码特定类型
                    contours = contour_mgr.get_all_contours()
                    for contour in contours:
                        if not contour:
                            continue

                        # 获取或按需创建可视化节点（仅在需要显示时创建）
                        node = contour.get_slicer_node() if hasattr(contour, 'get_slicer_node') else None
                        if visible and node is None and hasattr(contour, 'create_visualization'):
                            try:
                                created = contour.create_visualization()
                                if created:
                                    node = contour.get_slicer_node()
                            except Exception:
                                pass

                        if node is None:
                            continue

                        disp = node.GetDisplayNode()
                        if disp:
                            try:
                                disp.SetVisibility(visible)
                            except Exception:
                                pass
                            # 2D 禁用
                            try:
                                disp.SetVisibility2D(False)
                            except Exception:
                                pass
                            # 3D：StentBestFit 永远关闭，其它按期像控制
                            try:
                                n = node.GetName() if hasattr(node, 'GetName') else ''
                                is_stent_best_fit = isinstance(n, str) and n.startswith('StentBestFit_Contour')
                                disp.SetVisibility3D(False if is_stent_best_fit else visible)
                            except Exception:
                                pass
                            toggled_any = True
            except Exception as e:
                logging.warning(f"更新轮廓可视化失败(phase={phase_key}): {e}")

            # 3) 兜底：若领域模型未能定位任何节点，或分割节点处理失败，退回到名称匹配（保证兼容性）
            if not toggled_any or not segmentation_handled:
                phase_suffix = self.phase_suffixes.get(phase)
                if phase_suffix:
                    # 分割节点名称兜底（仅在分割节点处理失败时）
                    if not segmentation_handled:
                        logging.info(f"启用分割节点兜底机制，期像: {phase}")
                    # 分割节点名称兜底（仅在分割节点处理失败时）
                    if not segmentation_handled:
                        logging.info(f"启用分割节点兜底机制，期像: {phase}")
                        for name in (
                            f"Auto_Analysis_Segmentation_{phase_suffix}",
                            f"TAVR_Segmentation_{phase_suffix}",
                            f"Segmentation_{phase_suffix}",
                        ):
                            # 改进：处理重复节点名称的情况
                            nodes = slicer.mrmlScene.GetNodesByName(name)
                            target_node = None
                            
                            if nodes.GetNumberOfItems() == 1:
                                # 只有一个节点，直接使用
                                target_node = nodes.GetItemAsObject(0)
                            elif nodes.GetNumberOfItems() > 1:
                                # 有多个同名节点，选择最新的分割节点
                                logging.warning(f"发现{nodes.GetNumberOfItems()}个同名分割节点: {name}")
                                candidates = []
                                for i in range(nodes.GetNumberOfItems()):
                                    node = nodes.GetItemAsObject(i)
                                    if node.GetClassName() == 'vtkMRMLSegmentationNode':
                                        candidates.append(node)
                                
                                if candidates:
                                    # 按ID排序选择最新的
                                    candidates.sort(key=lambda n: int(n.GetID().split('Node')[-1]) if 'Node' in n.GetID() else 0, reverse=True)
                                    target_node = candidates[0]
                                    logging.info(f"选择最新的分割节点: {target_node.GetID()}")
                            
                            if not target_node:
                                continue
                                
                            disp = target_node.GetDisplayNode()
                            if not disp:
                                continue
                                
                            try:
                                disp.SetVisibility(visible)
                                # 3D：根据期像显示/隐藏分割模型，并确保分段级别可见性
                                try:
                                    disp.SetVisibility3D(visible)
                                    
                                    # 确保所有分段也按期像控制3D显示
                                    if target_node.GetClassName() == 'vtkMRMLSegmentationNode':
                                        segmentation = target_node.GetSegmentation()
                                        for i in range(segmentation.GetNumberOfSegments()):
                                            segment_id = segmentation.GetNthSegmentID(i)
                                            disp.SetSegmentVisibility3D(segment_id, visible)
                                            disp.SetSegmentVisibility(segment_id, visible)
                                except Exception:
                                    pass
                                # 2D 一律关闭
                                try:
                                    disp.SetVisibility2DFill(False)
                                    disp.SetVisibility2DOutline(False)
                                except Exception:
                                    pass
                                
                                logging.info(f"兜底机制成功设置分割节点: {name} (ID: {target_node.GetID()})")
                                toggled_any = True
                                
                                # 将正确的节点注册到领域模型
                                try:
                                    self.session.set_phase_segmentation_node(phase_key, target_node.GetID())
                                    logging.info(f"已将分割节点注册到领域模型: {phase_key} -> {target_node.GetID()}")
                                except Exception as reg_e:
                                    logging.warning(f"注册分割节点到领域模型失败: {reg_e}")
                                
                                break  # 找到并处理了正确的节点，跳出循环
                                
                            except Exception:
                                pass
                    # 轮廓节点名称兜底
                    for name in (
                        f"ValveStent_Bottom_Contour_{phase_suffix}",
                        f"SinusOfValsalva_Contour_{phase_suffix}",
                        f"StentBestFit_Contour_{phase_suffix}",
                    ):
                        node = slicer.mrmlScene.GetFirstNodeByName(name)
                        if not node:
                            continue
                        disp = node.GetDisplayNode()
                        if not disp:
                            continue
                        try:
                            disp.SetVisibility(visible)
                        except Exception:
                            pass
                        # 2D 禁用
                        try:
                            disp.SetVisibility2D(False)
                        except Exception:
                            pass
                        # 3D：StentBestFit 永远关闭
                        try:
                            n = node.GetName() if hasattr(node, 'GetName') else ''
                            is_stent_best_fit = isinstance(n, str) and n.startswith('StentBestFit_Contour')
                            disp.SetVisibility3D(False if is_stent_best_fit else visible)
                        except Exception:
                            pass
                        toggled_any = True

        except Exception as e:
            logging.error(f"设置期像 {phase} 节点可视化失败: {e}")
    
    def show_only_current_phase(self):
        """
        只显示当前期像的节点，隐藏其他期像的节点
        """
        if self.current_phase:
            self._manage_phase_visibility(self.current_phase)
        else:
            # 如果没有选择期像，隐藏所有期像相关节点
            for phase in ['diastole', 'systole']:
                self._set_phase_nodes_visibility(phase, visible=False)
    
    def show_all_phases(self):
        """
        显示所有期像的节点（用于对比）
        """
        for phase in ['diastole', 'systole']:
            self._set_phase_nodes_visibility(phase, visible=True)
        logging.info("显示所有期像的节点")
    
    def auto_activate(self, preferred_phase: str = 'diastole'):
        """
        自动激活期像选择
        
        尝试切换到指定的期像，通常在模块激活时调用
        
        Args:
            preferred_phase: 首选期像 ('diastole' 或 'systole')
        """
        logging.info(f"期像选择组件激活，首选期像: {preferred_phase}")
        
        try:
            # 检查标记的期像状态
            phase_status = self._check_marked_phases()
            
            # 尝试切换到首选期像
            if preferred_phase == 'diastole':
                if self._auto_switch_to_end_diastole():
                    self._update_status("已切换到舒张末期")
                    self.set_current_phase('diastole')
                    self.phaseChanged.emit('diastole')
                else:
                    self._update_status("请先在模块一中标记舒张末期时相")
            elif preferred_phase == 'systole':
                if self._switch_to_end_systole():
                    self._update_status("已切换到收缩末期")
                    self.set_current_phase('systole')
                    self.phaseChanged.emit('systole')
                else:
                    self._update_status("请先在模块一中标记收缩末期时相")
                    
        except Exception as e:
            logging.error(f"自动期像切换失败: {e}")
            self._update_status("自动期像切换失败，请手动切换")
    
    def _check_marked_phases(self) -> Dict[str, Any]:
        """
        检查已标记的期像状态
        
        Returns:
            dict: 期像标记状态信息
        """
        end_diastole_info = self.session.get_marked_phase('end_diastole')
        end_systole_info = self.session.get_marked_phase('end_systole')
        
        # 记录期像标记状态
        diastole_marked = end_diastole_info is not None and end_diastole_info.get('frame_index') is not None
        systole_marked = end_systole_info is not None and end_systole_info.get('frame_index') is not None
        
        if diastole_marked and systole_marked:
            logging.info("✓ 舒张末期和收缩末期均已标记")
        elif diastole_marked:
            logging.info("✓ 舒张末期已标记，收缩末期未标记")
        elif systole_marked:
            logging.warning("⚠ 收缩末期已标记，但舒张末期未标记（建议先标记舒张末期）")
        else:
            logging.warning("⚠ 舒张末期和收缩末期均未标记")
        
        return {
            'end_diastole_marked': diastole_marked,
            'end_systole_marked': systole_marked,
            'end_diastole_info': end_diastole_info,
            'end_systole_info': end_systole_info
        }
    
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
    
    def _switch_to_end_systole(self) -> bool:
        """
        切换到收缩末期
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        try:
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info:
                logging.warning("未找到收缩末期标记")
                return False
            
            frame_index = end_systole_info.get('frame_index')
            if frame_index is None:
                logging.warning("收缩末期标记中缺少帧索引信息")
                return False
            
            # 获取序列浏览器节点
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新状态显示
            phase_percent = end_systole_info.get('phase_percent', 0.0)
            logging.info(f"成功切换到帧 {frame_index} (收缩末期)")
            return True
            
        except Exception as e:
            logging.error(f"切换到收缩末期失败: {e}")
            return False
    
    def _on_switch_to_diastole(self):
        """处理切换到舒张末期按钮点击"""
        logging.info("用户要求切换到舒张末期")
        
        try:
            if self._auto_switch_to_end_diastole():
                # 更新按钮状态和当前期像
                self.set_current_phase('diastole')
                self._update_status("已切换到舒张末期")
                
                # 发送期像改变信号
                self.phaseChanged.emit('diastole')
                
                logging.info("手动切换到舒张末期成功")
            else:
                self._update_status("切换到舒张末期失败，请检查模块一中的期像标记")
                logging.warning("手动切换到舒张末期失败")
                
        except Exception as e:
            logging.error(f"手动切换到舒张末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")
    
    def _on_switch_to_systole(self):
        """处理切换到收缩末期按钮点击"""
        logging.info("用户要求切换到收缩末期")
        
        try:
            if self._switch_to_end_systole():
                # 更新按钮状态和当前期像
                self.set_current_phase('systole')
                self._update_status("已切换到收缩末期")
                
                # 发送期像改变信号
                self.phaseChanged.emit('systole')
                
                logging.info("手动切换到收缩末期成功")
            else:
                self._update_status("切换到收缩末期失败，请检查模块一中的期像标记")
                logging.warning("手动切换到收缩末期失败")
                
        except Exception as e:
            logging.error(f"手动切换到收缩末期失败: {e}")
            self._update_status("切换失败，请检查期像标记")
    
    def _update_phase_button_states(self, active_phase: str):
        """
        更新期像切换按钮的状态
        
        Args:
            active_phase: 当前激活的期像 ('diastole' 或 'systole')
        """
        if active_phase == 'diastole':
            # 舒张末期激活
            if hasattr(self, 'switch_to_diastole_button'):
                self.switch_to_diastole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: 2px solid #1e7e34;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
            if hasattr(self, 'switch_to_systole_button'):
                # 恢复次要样式
                self.switch_to_systole_button.setStyleSheet("")  # 重置为默认次要样式
                
        elif active_phase == 'systole':
            # 收缩末期激活
            if hasattr(self, 'switch_to_systole_button'):
                self.switch_to_systole_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 2px solid #bd2130;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
            if hasattr(self, 'switch_to_diastole_button'):
                # 恢复主要样式  
                self.switch_to_diastole_button.setStyleSheet("")  # 重置为默认主要样式
    
    def _update_status(self, message: str):
        """
        更新状态显示
        
        Args:
            message: 状态消息
        """
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
            logging.info(f"期像选择状态更新: {message}")
        
        # 发送状态更新信号
        self.statusUpdated.emit(message)
    
    def set_session(self, session: TAVRStudySession):
        """
        设置会话对象
        
        Args:
            session: TAVR研究会话对象
        """
        self.session = session
    
    def _find_correct_segmentation_node(self, phase: str):
        """
        查找正确的分割节点
        
        当领域模型中注册的节点与期像不匹配时，重新查找正确的节点
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
            
        Returns:
            正确的分割节点或None
        """
        try:
            import slicer
            phase_suffix = self.phase_suffixes.get(phase)
            if not phase_suffix:
                return None
            
            # 按优先级搜索分割节点
            search_patterns = [
                f"Auto_Analysis_Segmentation_{phase_suffix}",
                f"TAVR_Segmentation_{phase_suffix}",
                f"Segmentation_{phase_suffix}",
            ]
            
            candidates = []
            for pattern in search_patterns:
                # 使用GetNodesByName获取所有匹配的节点
                nodes = slicer.mrmlScene.GetNodesByName(pattern)
                if nodes.GetNumberOfItems() > 0:
                    for i in range(nodes.GetNumberOfItems()):
                        node = nodes.GetItemAsObject(i)
                        if node.GetClassName() == 'vtkMRMLSegmentationNode':
                            candidates.append(node)
            
            # 如果有多个候选节点，选择最新创建的
            if candidates:
                # 按ID排序，通常较新的节点有较大的ID
                candidates.sort(key=lambda n: int(n.GetID().split('Node')[-1]) if 'Node' in n.GetID() else 0, reverse=True)
                selected_node = candidates[0]
                logging.info(f"找到正确的分割节点: {selected_node.GetName()} (ID: {selected_node.GetID()})")
                return selected_node
            
            return None
            
        except Exception as e:
            logging.error(f"查找正确分割节点时出错: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        logging.info("期像选择组件清理完成")
