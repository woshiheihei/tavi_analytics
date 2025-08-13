"""
开发者调试工具

提供基于Slicer场景与插件会话状态的保存/加载功能，
用于加速开发调试的反馈循环。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import slicer

# 相对导入核心模型
try:
    from core.session import TAVRStudySession
    from core.data_models import PatientData
except Exception:  # 兼容直接运行
    from ..core.session import TAVRStudySession
    from ..core.data_models import PatientData


class DevUtils:
    """开发者调试工具集合"""

    BASE_DIR = Path.home() / ".tavi_analytics_debug"

    @staticmethod
    def ensure_base_dir() -> Path:
        DevUtils.BASE_DIR.mkdir(parents=True, exist_ok=True)
        return DevUtils.BASE_DIR

    @staticmethod
    def list_sessions() -> List[str]:
        base = DevUtils.ensure_base_dir()
        sessions: List[str] = []
        for child in base.iterdir() if base.exists() else []:
            if child.is_dir() and (child / "session.json").exists():
                # 检查场景文件：优先检查新格式，然后检查旧格式兼容性
                scene_bundle_dir = child / "scene_bundle"
                scene_file = scene_bundle_dir / "scene_bundle.mrml"  # 新格式：{dir_name}.mrml
                old_scene_file = child / "scene.mrml"  # 旧格式
                
                if scene_file.exists() or old_scene_file.exists():
                    sessions.append(child.name)
        sessions.sort()
        return sessions

    @staticmethod
    def _session_to_dict(session: TAVRStudySession) -> Dict[str, Any]:
        """将会话关键信息序列化为字典。"""
        try:
            patient = session.patient_data.to_dict() if hasattr(session.patient_data, "to_dict") else {}
        except Exception:
            patient = {}

        # 序列化平面数据管理器
        plane_data = {}
        try:
            if hasattr(session, 'plane_data_manager') and session.plane_data_manager:
                plane_data = session.plane_data_manager.to_dict()
        except Exception as e:
            logging.warning(f"序列化平面数据失败: {e}")

        # 安全转换节点对象为ID字符串
        def safe_node_to_id(value):
            """安全地将节点对象转换为ID字符串"""
            if value is None:
                return None
            if isinstance(value, str):
                return value
            # 检查是否是Slicer节点对象
            if hasattr(value, 'GetID'):
                try:
                    return value.GetID()
                except Exception:
                    return None
            return str(value) if value else None

        # 安全转换字典中的节点对象
        def safe_dict_conversion(data):
            """递归地转换字典中的节点对象"""
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    if hasattr(value, 'GetID'):  # Slicer节点对象
                        result[key] = safe_node_to_id(value)
                    elif isinstance(value, dict):
                        result[key] = safe_dict_conversion(value)
                    elif isinstance(value, list):
                        result[key] = [safe_node_to_id(item) if hasattr(item, 'GetID') else item for item in value]
                    else:
                        result[key] = value
                return result
            return data

        return {
            "patient_data": patient,
            "volume_sequence_node_id": safe_node_to_id(session.volume_sequence_node_id),
            "sequence_browser_node_id": safe_node_to_id(session.sequence_browser_node_id),
            "marked_phases": session.marked_phases,
            "segmentation_node_id": safe_node_to_id(session.segmentation_node_id),
            "landmark_node_ids": safe_dict_conversion(session.landmark_node_ids),
            "reconstructed_planes": safe_dict_conversion(session.reconstructed_planes),
            "plane_data": plane_data,  # 新增平面数据序列化
        }

    @staticmethod
    def _get_module_states() -> Dict[str, Any]:
        """获取各个模块的特定状态"""
        module_states = {}
        
        try:
            # 获取模块管理器和当前激活的模块
            import slicer
            
            # 尝试从插件获取模块管理器
            plugin = None
            try:
                plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            except Exception:
                pass
            
            if plugin and hasattr(plugin, 'module_manager'):
                module_manager = plugin.module_manager
                
                # 保存当前激活的模块信息
                if hasattr(plugin, 'main_ui') and plugin.main_ui:
                    current_module = plugin.main_ui.get_current_module()
                    module_states['current_active_module'] = current_module
                
                # 获取module2的特定状态
                module2_adapter = module_manager.get_module_adapter("module2")
                if module2_adapter and hasattr(module2_adapter, '_logic') and module2_adapter._logic:
                    logic = module2_adapter._logic
                    module_states['module2_state'] = {
                        'selected_phase': getattr(logic, 'selected_phase', 'diastole'),
                        'current_task_id': getattr(logic, 'current_task_id', None),
                        'analysis_state': getattr(logic, 'analysis_state', 'idle')
                    }
                
                # 可以继续添加其他模块的状态
                
        except Exception as e:
            logging.warning(f"获取模块状态时出错: {e}")
        
        return module_states

    @staticmethod
    def _apply_session_dict(session: TAVRStudySession, data: Dict[str, Any]) -> None:
        """将字典数据应用到会话对象。假设场景已加载完成。"""
        session.reset()

        # 恢复患者数据
        pd = data.get("patient_data") or {}
        try:
            session.patient_data = PatientData.from_dict(pd) if pd else PatientData()
        except Exception:
            session.patient_data = PatientData()

        # 恢复节点与标记
        session.volume_sequence_node_id = data.get("volume_sequence_node_id")
        session.sequence_browser_node_id = data.get("sequence_browser_node_id")
        session.marked_phases = data.get("marked_phases") or session.marked_phases
        session.segmentation_node_id = data.get("segmentation_node_id")
        session.landmark_node_ids = data.get("landmark_node_ids") or {}
        session.reconstructed_planes = data.get("reconstructed_planes") or {}

        # 恢复平面数据管理器
        plane_data = data.get("plane_data")
        if plane_data:
            try:
                from core.domain_models import PlaneDataManager
                session.plane_data_manager = PlaneDataManager.from_dict(plane_data)
                logging.info("平面数据管理器已恢复")
            except Exception as e:
                logging.warning(f"恢复平面数据失败: {e}")
                # 创建新的空管理器
                from core.domain_models import PlaneDataManager
                session.plane_data_manager = PlaneDataManager()

    @staticmethod
    def _apply_module_states(module_states: Dict[str, Any]) -> None:
        """恢复各个模块的特定状态"""
        try:
            import slicer
            
            # 尝试从插件获取模块管理器
            plugin = None
            try:
                plugin = slicer.modules.tavi_analytics.widgetRepresentation().self()
            except Exception:
                return
            
            if not plugin or not hasattr(plugin, 'module_manager'):
                return
            
            module_manager = plugin.module_manager
            session = plugin.session
            
            # 恢复module2的状态
            module2_state = module_states.get('module2_state', {})
            if module2_state:
                module2_adapter = module_manager.get_module_adapter("module2")
                if module2_adapter and hasattr(module2_adapter, '_logic') and module2_adapter._logic:
                    logic = module2_adapter._logic
                    
                    # 恢复选择的期像
                    selected_phase = module2_state.get('selected_phase', 'diastole')
                    logic.set_selected_phase(selected_phase)
                    
                    # 恢复分析状态（但不恢复task_id，避免冲突）
                    analysis_state = module2_state.get('analysis_state', 'idle')
                    if analysis_state in ['idle', 'stopped']:
                        logic.analysis_state = analysis_state
                    
                    logging.info(f"已恢复module2状态: 期像={selected_phase}, 分析状态={analysis_state}")
            
            # 恢复平面数据的可视化（延迟执行）
            def restore_plane_visualizations():
                try:
                    if hasattr(session, 'plane_data_manager') and session.plane_data_manager:
                        # 重建所有平面的可视化
                        results = session.plane_data_manager.create_all_visualizations()
                        successful_count = sum(1 for success in results.values() if success)
                        logging.info(f"已恢复平面可视化: {successful_count}/{len(results)}个成功")
                except Exception as e:
                    logging.warning(f"恢复平面可视化失败: {e}")
            
            # 恢复当前激活的模块（稍后执行，让场景完全加载）
            current_module = module_states.get('current_active_module')
            if current_module and hasattr(plugin, 'main_ui') and plugin.main_ui:
                # 使用QTimer延迟执行模块切换和可视化恢复
                def switch_to_saved_module():
                    try:
                        plugin.main_ui.switch_to_module(current_module)
                        logging.info(f"已恢复到模块: {current_module}")
                        
                        # 在模块切换后再恢复可视化
                        import qt
                        qt.QTimer.singleShot(500, restore_plane_visualizations)
                        
                    except Exception as e:
                        logging.warning(f"恢复模块切换失败: {e}")
                
                import qt
                qt.QTimer.singleShot(1000, switch_to_saved_module)  # 1秒后切换
            else:
                # 如果没有模块切换，直接恢复可视化
                import qt
                qt.QTimer.singleShot(1500, restore_plane_visualizations)
                
        except Exception as e:
            logging.warning(f"恢复模块状态时出错: {e}")

    @staticmethod
    def _validate_json_serializable(data, path="root"):
        """递归验证数据的JSON可序列化性，并报告问题位置"""
        import json
        
        def check_object(obj, current_path):
            """递归检查对象是否可序列化"""
            try:
                # 尝试序列化当前对象
                json.dumps(obj)
                return True
            except TypeError as e:
                if isinstance(obj, dict):
                    # 如果是字典，检查每个键值对
                    for key, value in obj.items():
                        new_path = f"{current_path}.{key}"
                        if not check_object(value, new_path):
                            return False
                elif isinstance(obj, (list, tuple)):
                    # 如果是列表或元组，检查每个元素
                    for i, item in enumerate(obj):
                        new_path = f"{current_path}[{i}]"
                        if not check_object(item, new_path):
                            return False
                else:
                    # 单个对象不可序列化
                    obj_type = type(obj).__name__
                    logging.error(f"不可序列化对象位于 {current_path}: {obj_type} - {str(obj)[:100]}")
                    raise TypeError(f"位于 {current_path} 的对象类型 {obj_type} 不可JSON序列化")
                return True
        
        return check_object(data, path)

    @staticmethod
    def save_debug_session(session: TAVRStudySession, session_name: str) -> Dict[str, Any]:
        """
        保存当前Slicer场景和插件会话状态。

        Returns: 结果字典 { success: bool, message: str, path?: str }
        """
        try:
            if not session_name or not session_name.strip():
                return {"success": False, "message": "会话名称不能为空"}

            base = DevUtils.ensure_base_dir()
            target_dir = base / session_name.strip()
            target_dir.mkdir(parents=True, exist_ok=True)

            # 保存完整Slicer场景（包含数据文件）
            # 使用目录路径保存，这样会创建{dir_name}.mrml和Data/文件夹
            scene_bundle_dir = target_dir / "scene_bundle"
            scene_bundle_dir.mkdir(exist_ok=True)
            ok = slicer.util.saveScene(str(scene_bundle_dir))
            if not ok:
                return {"success": False, "message": "保存场景失败"}

            # 保存会话JSON（包含模块状态）
            try:
                payload = DevUtils._session_to_dict(session)
                logging.info(f"会话状态序列化成功")
            except Exception as e:
                logging.error(f"会话状态序列化失败: {e}")
                return {"success": False, "message": f"会话状态序列化失败: {e}"}
            
            # 获取并保存模块状态
            try:
                module_states = DevUtils._get_module_states()
                payload["module_states"] = module_states
                logging.info(f"模块状态获取成功: {list(module_states.keys())}")
            except Exception as e:
                logging.warning(f"模块状态获取失败: {e}")
                payload["module_states"] = {}
            
            # JSON序列化前的验证
            try:
                DevUtils._validate_json_serializable(payload)
                logging.info("JSON序列化验证通过")
            except Exception as e:
                logging.error(f"JSON序列化验证失败: {e}")
                return {"success": False, "message": f"数据包含不可序列化对象: {e}"}
            
            with open(target_dir / "session.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            logging.info(f"调试会话已保存: {target_dir}")
            logging.info(f"保存的模块状态: {list(module_states.keys())}")
            return {"success": True, "message": "保存成功", "path": str(target_dir)}

        except Exception as e:
            logging.exception("保存调试会话时出错")
            return {"success": False, "message": f"异常: {e}"}

    @staticmethod
    def load_debug_session(session: TAVRStudySession, session_name: str) -> Dict[str, Any]:
        """
        从保存的快照恢复Slicer场景和插件会话状态。

        Returns: 结果字典 { success: bool, message: str }
        """
        try:
            base = DevUtils.ensure_base_dir()
            target_dir = base / session_name
            json_file = target_dir / "session.json"

            if not target_dir.exists() or not json_file.exists():
                return {"success": False, "message": "会话文件不存在或不完整"}

            # 检查场景文件：新格式优先，旧格式兼容
            scene_bundle_dir = target_dir / "scene_bundle"
            new_scene_file = scene_bundle_dir / "scene_bundle.mrml"  # 新格式：{dir_name}.mrml
            old_scene_file = target_dir / "scene.mrml"  # 旧格式兼容
            
            scene_file = None
            if new_scene_file.exists():
                scene_file = new_scene_file
            elif old_scene_file.exists():
                scene_file = old_scene_file
            else:
                return {"success": False, "message": "场景文件不存在"}

            # 清空当前场景
            slicer.mrmlScene.Clear(0)

            # 加载场景（优先使用mrmlScene.Connect加载）
            slicer.mrmlScene.SetURL(str(scene_file))
            ok = bool(slicer.mrmlScene.Connect())
            if not ok:
                # 作为回退，尝试util.loadScene
                ok = bool(slicer.util.loadScene(str(scene_file)))
            if not ok:
                return {"success": False, "message": "加载场景失败（Connect与loadScene均未成功）"}

            # 恢复会话状态
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            DevUtils._apply_session_dict(session, data)

            # 恢复模块状态
            module_states = data.get("module_states", {})
            if module_states:
                DevUtils._apply_module_states(module_states)
                logging.info(f"恢复的模块状态: {list(module_states.keys())}")

            format_used = "新格式(含数据)" if scene_file == new_scene_file else "旧格式(仅元数据)"
            logging.info(f"调试会话已加载: {target_dir} ({format_used})")
            return {"success": True, "message": f"加载成功 ({format_used})"}

        except Exception as e:
            logging.exception("加载调试会话时出错")
            return {"success": False, "message": f"异常: {e}"}
