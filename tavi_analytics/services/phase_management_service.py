"""
期像管理服务

提供集中化的期像状态管理和事件发布，解决多个PhaseSelectionWidget实例之间
的同步问题。采用单例模式确保全局状态一致性。

主要功能：
- 全局期像状态管理
- 期像切换API
- 期像变更事件发布
- 与TAVRStudySession集成

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import re
from typing import Optional, Dict, Any, Callable, List
import qt

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession


class PhaseManagementService(qt.QObject):
    """
    期像管理服务 - 单例模式
    
    负责协调所有期像选择组件的状态同步，提供集中化的期像管理。
    """
    
    # 期像变更信号 - 全局事件
    phaseChanged = qt.Signal(str, str)  # (old_phase, new_phase)
    phaseSwitchRequested = qt.Signal(str, str)  # (phase, source_component)
    phaseStatusUpdated = qt.Signal(str)  # (status_message)
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, session: Optional[TAVRStudySession] = None):
        """
        初始化期像管理服务
        
        Args:
            session: TAVR研究会话对象
        """
        if self._initialized:
            return
        
        super().__init__()
        self.session = session
        self.current_phase: Optional[str] = None  # 当前激活的期像
        self.available_phases = ['diastole', 'systole']  # 可用期像
        
        # 期像相关节点命名模式（与PhaseSelectionWidget保持一致）
        self.phase_suffixes = {
            'diastole': 'End_Diastole',
            'systole': 'End_Systole'
        }
        
        # 领域模型使用的期像键
        self.phase_domain_keys = {
            'diastole': 'end_diastole',
            'systole': 'end_systole',
        }
        
        # 订阅者列表 - 期像选择组件的回调函数
        self._phase_sync_callbacks: List[Callable[[str], None]] = []
        
        self._initialized = True
        logging.info("PhaseManagementService 初始化完成（单例模式）")
    
    def set_session(self, session: TAVRStudySession):
        """
        设置会话对象
        
        Args:
            session: TAVR研究会话对象
        """
        self.session = session
        logging.info("PhaseManagementService 设置session")
        
        # 自动检查分割节点注册的一致性
        try:
            self._check_and_fix_segmentation_consistency()
        except Exception as e:
            logging.warning(f"分割一致性检查失败: {e}")
    
    def register_phase_sync_callback(self, callback: Callable[[str], None]):
        """
        注册期像同步回调函数
        
        期像选择组件可以注册回调函数，当期像发生变化时会被调用
        
        Args:
            callback: 回调函数，参数为新的期像
        """
        if callback not in self._phase_sync_callbacks:
            self._phase_sync_callbacks.append(callback)
            logging.debug(f"注册期像同步回调，当前回调数量: {len(self._phase_sync_callbacks)}")
    
    def unregister_phase_sync_callback(self, callback: Callable[[str], None]):
        """
        取消注册期像同步回调函数
        
        Args:
            callback: 要取消注册的回调函数
        """
        if callback in self._phase_sync_callbacks:
            self._phase_sync_callbacks.remove(callback)
            logging.debug(f"取消注册期像同步回调，当前回调数量: {len(self._phase_sync_callbacks)}")
    
    def get_current_phase(self) -> Optional[str]:
        """
        获取当前期像
        
        Returns:
            str: 当前期像 ('diastole' 或 'systole')，未设置时返回None
        """
        return self.current_phase
    
    def set_current_phase(self, phase: str, source_component: str = "unknown") -> bool:
        """
        设置当前期像并触发全局同步
        
        Args:
            phase: 期像类型 ('diastole' 或 'systole')
            source_component: 触发期像切换的组件名称
            
        Returns:
            bool: 设置成功返回True
        """
        if phase not in self.available_phases:
            logging.warning(f"无效的期像类型: {phase}")
            return False
        
        old_phase = self.current_phase
        
        # 如果期像没有变化，仍然触发同步（用于修复UI状态不一致的情况）
        self.current_phase = phase
        
        # 发出期像变更信号
        self.phaseChanged.emit(old_phase or "", phase)
        
        # 通知所有注册的回调函数进行同步
        self._notify_phase_sync_callbacks(phase)
        
        logging.info(f"期像管理服务：期像从 {old_phase} 切换到 {phase}（来源：{source_component}）")
        return True
    
    def switch_to_diastole(self, source_component: str = "unknown") -> bool:
        """
        切换到舒张末期
        
        Args:
            source_component: 触发切换的组件名称
            
        Returns:
            bool: 切换成功返回True
        """
        if not self.session:
            logging.error("期像管理服务：未设置session，无法切换期像")
            return False
        
        try:
            # 发出期像切换请求信号
            self.phaseSwitchRequested.emit('diastole', source_component)
            
            # 获取舒张末期时相信息
            end_diastole_info = self.session.get_marked_phase('end_diastole')
            if not end_diastole_info:
                logging.info("期像管理服务：未找到舒张末期标记，跳过时相切换")
                self.set_current_phase('diastole', source_component)
                return True
            
            frame_index = end_diastole_info.get('frame_index')
            if frame_index is None:
                logging.info("期像管理服务：舒张末期标记中缺少帧索引信息，跳过时相切换")
                self.set_current_phase('diastole', source_component)
                return True
            
            # 获取序列浏览器节点并切换帧
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("期像管理服务：未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新期像状态
            self.set_current_phase('diastole', source_component)
            
            # 统一处理数据可视化（新增）
            self._manage_phase_visualization('diastole')
            
            # 调试：切换后检查节点状态
            self.debug_phase_nodes_status()
            
            # 发出状态更新信号
            self.phaseStatusUpdated.emit("已切换到舒张末期")
            
            logging.info(f"期像管理服务：成功切换到帧 {frame_index} (舒张末期)")
            return True
            
        except Exception as e:
            logging.error(f"期像管理服务：切换到舒张末期失败: {e}")
            return False
    
    def switch_to_systole(self, source_component: str = "unknown") -> bool:
        """
        切换到收缩末期
        
        Args:
            source_component: 触发切换的组件名称
            
        Returns:
            bool: 切换成功返回True
        """
        if not self.session:
            logging.error("期像管理服务：未设置session，无法切换期像")
            return False
        
        try:
            # 发出期像切换请求信号
            self.phaseSwitchRequested.emit('systole', source_component)
            
            # 获取收缩末期时相信息
            end_systole_info = self.session.get_marked_phase('end_systole')
            if not end_systole_info:
                logging.warning("期像管理服务：未找到收缩末期标记")
                return False
            
            frame_index = end_systole_info.get('frame_index')
            if frame_index is None:
                logging.warning("期像管理服务：收缩末期标记中缺少帧索引信息")
                return False
            
            # 获取序列浏览器节点并切换帧
            browser_node = self.session.get_sequence_browser_node()
            if not browser_node:
                logging.warning("期像管理服务：未找到序列浏览器节点")
                return False
            
            # 切换到指定帧
            browser_node.SetSelectedItemNumber(frame_index)
            
            # 更新期像状态
            self.set_current_phase('systole', source_component)
            
            # 统一处理数据可视化（新增）
            self._manage_phase_visualization('systole')
            
            # 调试：切换后检查节点状态
            self.debug_phase_nodes_status()
            
            # 发出状态更新信号
            self.phaseStatusUpdated.emit("已切换到收缩末期")
            
            logging.info(f"期像管理服务：成功切换到帧 {frame_index} (收缩末期)")
            return True
            
        except Exception as e:
            logging.error(f"期像管理服务：切换到收缩末期失败: {e}")
            return False
    
    def _notify_phase_sync_callbacks(self, phase: str):
        """
        通知所有注册的期像同步回调函数
        
        Args:
            phase: 新的期像
        """
        for callback in self._phase_sync_callbacks:
            try:
                callback(phase)
            except Exception as e:
                logging.error(f"期像同步回调执行失败: {e}")
    
    def get_available_phases(self) -> List[str]:
        """
        获取可用的期像列表
        
        Returns:
            List[str]: 可用期像列表
        """
        return self.available_phases.copy()
    
    def get_phase_info(self) -> Dict[str, Any]:
        """
        获取期像管理服务的状态信息
        
        Returns:
            dict: 包含当前期像、可用期像等信息的字典
        """
        return {
            'current_phase': self.current_phase,
            'available_phases': self.available_phases.copy(),
            'callback_count': len(self._phase_sync_callbacks),
            'has_session': self.session is not None
        }
    
    def cleanup(self):
        """清理资源"""
        self._phase_sync_callbacks.clear()
        logging.info("期像管理服务：清理完成")
    
    def debug_phase_nodes_status(self):
        """
        调试方法：检查所有期像相关节点的当前状态
        
        用于排查期像切换问题，输出所有期像相关节点的可视化状态
        """
        try:
            import slicer
            logging.info("=== 期像节点状态调试开始 ===")
            
            # 检查所有分割节点
            segmentation_patterns = [
                "Auto_Analysis_Segmentation_End_Diastole",
                "Auto_Analysis_Segmentation_End_Systole", 
                "TAVR_Segmentation_End_Diastole",
                "TAVR_Segmentation_End_Systole",
                "Segmentation_End_Diastole",
                "Segmentation_End_Systole",
            ]
            
            for pattern in segmentation_patterns:
                nodes = slicer.mrmlScene.GetNodesByName(pattern)
                if nodes.GetNumberOfItems() > 0:
                    for i in range(nodes.GetNumberOfItems()):
                        node = nodes.GetItemAsObject(i)
                        if node and node.GetClassName() == 'vtkMRMLSegmentationNode':
                            disp = node.GetDisplayNode()
                            if disp:
                                visibility = disp.GetVisibility()
                                visibility_3d = disp.GetVisibility3D()
                                logging.info(f"分割节点: {node.GetName()} (ID: {node.GetID()}) - Visible: {visibility}, 3D: {visibility_3d}")
                            else:
                                logging.info(f"分割节点: {node.GetName()} (ID: {node.GetID()}) - 无显示节点")
                else:
                    logging.info(f"未找到分割节点: {pattern}")
            
            # 检查所有轮廓节点
            contour_patterns = [
                "ValveStent_Bottom_Contour_End_Diastole",
                "ValveStent_Bottom_Contour_End_Systole",
                "SinusOfValsalva_Contour_End_Diastole", 
                "SinusOfValsalva_Contour_End_Systole",
            ]
            
            for pattern in contour_patterns:
                node = slicer.mrmlScene.GetFirstNodeByName(pattern)
                if node:
                    disp = node.GetDisplayNode()
                    if disp:
                        visibility = disp.GetVisibility()
                        visibility_3d = disp.GetVisibility3D()
                        logging.info(f"轮廓节点: {node.GetName()} - Visible: {visibility}, 3D: {visibility_3d}")
                    else:
                        logging.info(f"轮廓节点: {node.GetName()} - 无显示节点")
                else:
                    logging.info(f"未找到轮廓节点: {pattern}")
            
            # 检查领域模型注册的节点 - 增强检查
            diastole_node = None
            systole_node = None
            
            for phase in ['diastole', 'systole']:
                phase_key = self.phase_domain_keys.get(phase)
                if phase_key and hasattr(self.session, 'get_phase_segmentation_node'):
                    try:
                        seg_node = self.session.get_phase_segmentation_node(phase_key)
                        if seg_node:
                            disp = seg_node.GetDisplayNode()
                            if disp:
                                visibility = disp.GetVisibility()
                                visibility_3d = disp.GetVisibility3D()
                                logging.info(f"领域模型分割节点 ({phase}): {seg_node.GetName()} (ID: {seg_node.GetID()}) - Visible: {visibility}, 3D: {visibility_3d}")
                                
                                # 记录节点以检查重复注册
                                if phase == 'diastole':
                                    diastole_node = seg_node
                                else:
                                    systole_node = seg_node
                        else:
                            logging.info(f"领域模型未注册分割节点: {phase_key}")
                    except Exception as e:
                        logging.warning(f"检查领域模型节点失败 ({phase}): {e}")
            
            # 检查是否存在重复注册问题
            if diastole_node and systole_node and diastole_node.GetID() == systole_node.GetID():
                logging.error(f"🚨 发现严重问题：舒张期和收缩期注册了同一个节点！节点: {diastole_node.GetName()} (ID: {diastole_node.GetID()})")
                logging.error("这会导致期像切换时无法正确隐藏对应的mask！")
                
                # 尝试自动修复注册错误
                self._fix_phase_registration_error()
            
            logging.info(f"当前期像管理服务状态: current_phase={self.current_phase}")
            logging.info("=== 期像节点状态调试结束 ===")
            
        except Exception as e:
            logging.error(f"调试期像节点状态失败: {e}")
    
    def _fix_phase_registration_error(self):
        """
        修复期像注册错误
        
        当发现舒张期和收缩期注册了同一个节点时，尝试重新正确注册
        """
        try:
            import slicer
            logging.info("期像管理服务：开始修复期像注册错误...")
            
            # 查找正确的舒张期和收缩期分割节点
            diastole_node = slicer.mrmlScene.GetFirstNodeByName("Auto_Analysis_Segmentation_End_Diastole")
            systole_node = slicer.mrmlScene.GetFirstNodeByName("Auto_Analysis_Segmentation_End_Systole")
            
            if diastole_node and systole_node:
                # 重新注册到领域模型
                if hasattr(self.session, 'set_phase_segmentation_node'):
                    try:
                        self.session.set_phase_segmentation_node('end_diastole', diastole_node.GetID())
                        self.session.set_phase_segmentation_node('end_systole', systole_node.GetID())
                        logging.info(f"期像管理服务：已修复注册 - 舒张期: {diastole_node.GetName()}, 收缩期: {systole_node.GetName()}")
                    except Exception as e:
                        logging.error(f"期像管理服务：修复注册失败: {e}")
            else:
                logging.warning(f"期像管理服务：无法找到正确的期像节点进行修复 (舒张期:{diastole_node}, 收缩期:{systole_node})")
                
        except Exception as e:
            logging.error(f"期像管理服务：修复期像注册错误失败: {e}")
    
    def _check_and_fix_segmentation_consistency(self):
        """
        检查并修复分割节点注册的一致性
        
        在服务初始化时自动调用，确保分割节点注册状态正确
        """
        if not self.session:
            return
        
        try:
            # 执行一致性检查
            consistency_report = self.session.validate_segmentation_consistency()
            
            if consistency_report["consistent"]:
                logging.info("✅ 分割节点注册一致性检查通过")
                
                # 详细输出节点状态
                for phase, details in consistency_report["details"].items():
                    if details["node_id"]:
                        logging.info(f"  {phase}: {details['node_name']} ({details['node_id']}) - 匹配: {details['name_matches_phase']}")
                    else:
                        logging.info(f"  {phase}: 未注册")
            else:
                logging.warning("⚠️ 分割节点注册一致性检查发现问题:")
                for issue in consistency_report["issues"]:
                    logging.warning(f"  - {issue}")
                
                # 详细输出节点状态
                for phase, details in consistency_report["details"].items():
                    if details["node_id"]:
                        status = "✅" if details["name_matches_phase"] else "❌"
                        logging.info(f"  {phase}: {details['node_name']} ({details['node_id']}) {status}")
                
                # 尝试自动修复
                logging.info("🔧 尝试自动修复分割节点注册...")
                fix_success = self.session.fix_segmentation_registrations()
                
                if fix_success:
                    logging.info("✅ 分割节点注册修复成功")
                    # 重新检查
                    final_report = self.session.validate_segmentation_consistency()
                    if final_report["consistent"]:
                        logging.info("✅ 修复后一致性检查通过")
                    else:
                        logging.warning("⚠️ 修复后仍有问题，请手动检查")
                else:
                    logging.error("❌ 自动修复失败，请手动检查分割节点注册")
                    
        except Exception as e:
            logging.error(f"一致性检查异常: {e}")
    
    def get_segmentation_status_report(self) -> Dict[str, Any]:
        """
        获取分割节点状态报告
        
        Returns:
            dict: 包含分割节点状态的详细报告
        """
        if not self.session:
            return {"error": "会话未设置"}
        
        try:
            # 基础一致性报告
            consistency_report = self.session.validate_segmentation_consistency()
            
            # 添加运行时信息
            runtime_info = {
                "current_phase": self.current_phase,
                "scene_node_count": 0,
                "segmentation_nodes": []
            }
            
            try:
                import slicer
                # 统计场景中的分割节点
                seg_nodes = []
                for i in range(slicer.mrmlScene.GetNumberOfNodes()):
                    node = slicer.mrmlScene.GetNthNode(i)
                    if node and node.GetClassName() == 'vtkMRMLSegmentationNode':
                        seg_nodes.append({
                            "name": node.GetName(),
                            "id": node.GetID(),
                            "visible": node.GetDisplayNode().GetVisibility() if node.GetDisplayNode() else False
                        })
                
                runtime_info["scene_node_count"] = len(seg_nodes)
                runtime_info["segmentation_nodes"] = seg_nodes
                
            except Exception as e:
                runtime_info["scene_scan_error"] = str(e)
            
            return {
                "consistency": consistency_report,
                "runtime": runtime_info
            }
            
        except Exception as e:
            return {"error": f"状态报告生成失败: {e}"}
    
    def _manage_phase_visualization(self, active_phase: str):
        """
        统一管理期像相关节点的可视化状态
        
        这是核心的数据可视化管理方法，所有期像切换的可视化都应该在这里统一处理。
        UI组件不再需要处理数据可视化，只负责UI状态同步。
        
        Args:
            active_phase: 要显示的期像 ('diastole' 或 'systole')
        """
        try:
            logging.info(f"期像管理服务：开始可视化管理 - 激活期像: {active_phase}")
            
            # 第一步：全面扫描并强制隐藏所有期像相关节点
            self._force_hide_all_phase_nodes()
            
            # 第二步：仅显示活动期像的节点
            logging.info(f"期像管理服务：正在显示期像 {active_phase}...")
            self._set_phase_nodes_visibility(active_phase, visible=True)
            
            logging.info(f"期像管理服务：可视化管理完成 - 仅显示 {active_phase}")
            
        except Exception as e:
            logging.error(f"期像管理服务：可视化管理失败: {e}")
    
    def _force_hide_all_phase_nodes(self):
        """
        强制隐藏所有期像相关节点
        
        这个方法会扫描所有可能的期像相关节点并强制隐藏，
        确保没有遗漏的节点影响显示。
        """
        try:
            import slicer
            logging.info("期像管理服务：开始强制隐藏所有期像相关节点")
            
            hidden_count = 0
            
            # 1. 获取所有分割节点并强制隐藏
            all_segmentation_nodes = []
            for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLSegmentationNode")):
                node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLSegmentationNode")
                if node:
                    node_name = node.GetName()
                    # 检查是否是期像相关的分割节点
                    if any(suffix in node_name for suffix in ["End_Diastole", "End_Systole"]):
                        all_segmentation_nodes.append(node)
            
            # 强制隐藏所有期像相关的分割节点
            for node in all_segmentation_nodes:
                disp = node.GetDisplayNode()
                if disp:
                    try:
                        disp.SetVisibility(False)
                        disp.SetVisibility3D(False)
                        disp.SetVisibility2DFill(False)
                        disp.SetVisibility2DOutline(False)
                        
                        # 也要隐藏所有分段
                        segmentation = node.GetSegmentation()
                        for i in range(segmentation.GetNumberOfSegments()):
                            segment_id = segmentation.GetNthSegmentID(i)
                            disp.SetSegmentVisibility3D(segment_id, False)
                            disp.SetSegmentVisibility(segment_id, False)
                        
                        hidden_count += 1
                        logging.info(f"期像管理服务：强制隐藏分割节点: {node.GetName()} (ID: {node.GetID()})")
                    except Exception as e:
                        logging.warning(f"期像管理服务：强制隐藏分割节点失败: {e}")
            
            # 2. 动态发现并强制隐藏所有期像相关的轮廓节点
            # 2.1 先处理固定的三个基础轮廓类型
            basic_contour_patterns = [
                "ValveStent_Bottom_Contour_End_Diastole",
                "ValveStent_Bottom_Contour_End_Systole",
                "SinusOfValsalva_Contour_End_Diastole", 
                "SinusOfValsalva_Contour_End_Systole",
            ]
            
            for pattern in basic_contour_patterns:
                node = slicer.mrmlScene.GetFirstNodeByName(pattern)
                if node:
                    disp = node.GetDisplayNode()
                    if disp:
                        try:
                            disp.SetVisibility(False)
                            disp.SetVisibility2D(False)
                            disp.SetVisibility3D(False)
                            hidden_count += 1
                            logging.info(f"期像管理服务：强制隐藏基础轮廓节点: {node.GetName()}")
                        except Exception as e:
                            logging.warning(f"期像管理服务：强制隐藏基础轮廓节点失败: {e}")
            
            # 2.2 动态发现并隐藏多层级平面轮廓节点
            import re
            multi_level_pattern = re.compile(r"^StentPlane_.*cm.*_End_(Diastole|Systole)$")
            
            # 扫描所有标记点节点查找多层级轮廓
            for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLMarkupsCurveNode")):
                node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLMarkupsCurveNode")
                if node:
                    node_name = node.GetName()
                    if multi_level_pattern.match(node_name):
                        disp = node.GetDisplayNode()
                        if disp:
                            try:
                                disp.SetVisibility(False)
                                disp.SetVisibility2D(False)
                                disp.SetVisibility3D(False)
                                hidden_count += 1
                                logging.info(f"期像管理服务：强制隐藏多层级轮廓节点: {node_name}")
                            except Exception as e:
                                logging.warning(f"期像管理服务：强制隐藏多层级轮廓节点失败: {e}")
            
            # 2.3 也检查可能的其他标记点节点类型
            for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLMarkupsFiducialNode")):
                node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLMarkupsFiducialNode")
                if node:
                    node_name = node.GetName()
                    if multi_level_pattern.match(node_name):
                        disp = node.GetDisplayNode()
                        if disp:
                            try:
                                disp.SetVisibility(False)
                                disp.SetVisibility2D(False)
                                disp.SetVisibility3D(False)
                                hidden_count += 1
                                logging.info(f"期像管理服务：强制隐藏多层级标记点节点: {node_name}")
                            except Exception as e:
                                logging.warning(f"期像管理服务：强制隐藏多层级标记点节点失败: {e}")
            
            logging.info(f"期像管理服务：强制隐藏完成，共处理 {hidden_count} 个节点")
            
        except Exception as e:
            logging.error(f"期像管理服务：强制隐藏所有期像节点失败: {e}")
    
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
            
            logging.info(f"期像管理服务：开始设置期像 {phase} (phase_key={phase_key}) 可视化为 {visible}")
            
            # 统计处理的节点数量
            processed_nodes = {'segmentation': 0, 'contour': 0}
            
            # 1) 分割节点处理 - 领域模型方式
            try:
                if hasattr(self.session, 'get_phase_segmentation_node'):
                    seg_node = self.session.get_phase_segmentation_node(phase_key)
                    if seg_node:
                        seg_disp = seg_node.GetDisplayNode()
                        if seg_disp:
                            # 主要可视化状态
                            seg_disp.SetVisibility(visible)
                            
                            # 3D 显示控制
                            try:
                                seg_disp.SetVisibility3D(visible)
                                
                                # 确保所有分段也按期像控制3D显示
                                segmentation = seg_node.GetSegmentation()
                                segment_count = segmentation.GetNumberOfSegments()
                                for i in range(segment_count):
                                    segment_id = segmentation.GetNthSegmentID(i)
                                    seg_disp.SetSegmentVisibility3D(segment_id, visible)
                                    seg_disp.SetSegmentVisibility(segment_id, visible)
                            except Exception as e:
                                logging.warning(f"期像管理服务：3D可视化设置失败: {e}")
                            
                            # 2D 显示控制 - 统一关闭
                            try:
                                seg_disp.SetVisibility2DFill(False)
                                seg_disp.SetVisibility2DOutline(False)
                            except Exception as e:
                                logging.warning(f"期像管理服务：2D可视化设置失败: {e}")
                            
                            processed_nodes['segmentation'] += 1
                            logging.info(f"期像管理服务：领域模型分割节点 {seg_node.GetName()} (ID: {seg_node.GetID()}) 可视化设置为 {visible}")
                    else:
                        logging.warning(f"期像管理服务：领域模型未找到分割节点 (phase_key={phase_key})")
                else:
                    logging.warning(f"期像管理服务：session缺少get_phase_segmentation_node方法")
            except Exception as e:
                logging.warning(f"期像管理服务：领域模型分割节点处理失败(phase={phase_key}): {e}")
            
            # 2) 轮廓节点处理 - 领域模型方式
            try:
                if hasattr(self.session, 'get_phase_contour_manager'):
                    contour_mgr = self.session.get_phase_contour_manager(phase_key)
                    if contour_mgr and hasattr(contour_mgr, 'get_all_contours'):
                        contours = contour_mgr.get_all_contours()
                        for contour in contours:
                            if not contour:
                                continue
                            
                            node = contour.get_slicer_node() if hasattr(contour, 'get_slicer_node') else None
                            if node:
                                disp = node.GetDisplayNode()
                                if disp:
                                    try:
                                        disp.SetVisibility(visible)
                                        disp.SetVisibility2D(False)
                                        disp.SetVisibility3D(visible)
                                        processed_nodes['contour'] += 1
                                        n = node.GetName() if hasattr(node, 'GetName') else ''
                                        logging.info(f"期像管理服务：领域模型轮廓节点 {n} 可视化设置为 {visible}")
                                    except Exception as e:
                                        logging.warning(f"期像管理服务：轮廓节点可视化设置失败: {e}")
            except Exception as e:
                logging.warning(f"期像管理服务：领域模型轮廓节点处理失败(phase={phase_key}): {e}")
            
            # 3) 补充处理：直接扫描多层级平面轮廓节点
            # 因为多层级轮廓可能没有完全整合到领域模型的轮廓管理器中
            try:
                # 将期像键转换为显示后缀格式
                if phase_key == 'end_diastole':
                    phase_suffix = 'End_Diastole'
                elif phase_key == 'end_systole':
                    phase_suffix = 'End_Systole'
                else:
                    phase_suffix = phase_key
                
                multi_level_pattern = re.compile(rf"^StentPlane_.*cm.*_{phase_suffix}$")
                
                # 扫描所有标记点节点查找当前期像的多层级轮廓
                for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLMarkupsCurveNode")):
                    node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLMarkupsCurveNode")
                    if node:
                        node_name = node.GetName()
                        if multi_level_pattern.match(node_name):
                            disp = node.GetDisplayNode()
                            if disp:
                                try:
                                    disp.SetVisibility(visible)
                                    disp.SetVisibility2D(False)
                                    disp.SetVisibility3D(visible)
                                    processed_nodes['contour'] += 1
                                    logging.info(f"期像管理服务：直接处理多层级轮廓节点 {node_name} 可视化设置为 {visible}")
                                except Exception as e:
                                    logging.warning(f"期像管理服务：多层级轮廓节点可视化设置失败: {e}")
                
                # 也检查可能的其他标记点节点类型
                for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLMarkupsFiducialNode")):
                    node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLMarkupsFiducialNode")
                    if node:
                        node_name = node.GetName()
                        if multi_level_pattern.match(node_name):
                            disp = node.GetDisplayNode()
                            if disp:
                                try:
                                    disp.SetVisibility(visible)
                                    disp.SetVisibility2D(False)
                                    disp.SetVisibility3D(visible)
                                    processed_nodes['contour'] += 1
                                    logging.info(f"期像管理服务：直接处理多层级标记点节点 {node_name} 可视化设置为 {visible}")
                                except Exception as e:
                                    logging.warning(f"期像管理服务：多层级标记点节点可视化设置失败: {e}")
                                    
            except Exception as e:
                logging.warning(f"期像管理服务：直接扫描多层级轮廓节点失败(phase={phase_key}): {e}")
            
            # 总结处理结果
            total_processed = sum(processed_nodes.values())
            logging.info(f"期像管理服务：期像 {phase} 可视化设置完成，处理节点统计: {processed_nodes}，总计: {total_processed}")
            
            if total_processed == 0:
                logging.warning(f"期像管理服务：⚠️ 期像 {phase} 没有找到任何相关节点进行可视化设置！")
                        
        except Exception as e:
            logging.error(f"期像管理服务：设置期像 {phase} 节点可视化失败: {e}")


# 全局服务实例获取函数
_phase_management_service_instance = None

def get_phase_management_service(session: Optional[TAVRStudySession] = None) -> PhaseManagementService:
    """
    获取期像管理服务单例实例
    
    Args:
        session: TAVR研究会话对象（首次调用时需要提供）
        
    Returns:
        PhaseManagementService: 期像管理服务实例
    """
    global _phase_management_service_instance
    
    if _phase_management_service_instance is None:
        _phase_management_service_instance = PhaseManagementService(session)
    elif session is not None:
        _phase_management_service_instance.set_session(session)
    
    return _phase_management_service_instance