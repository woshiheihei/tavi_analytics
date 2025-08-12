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

        return {
            "patient_data": patient,
            "volume_sequence_node_id": session.volume_sequence_node_id,
            "sequence_browser_node_id": session.sequence_browser_node_id,
            "marked_phases": session.marked_phases,
            "segmentation_node_id": session.segmentation_node_id,
            "landmark_node_ids": session.landmark_node_ids,
            "reconstructed_planes": session.reconstructed_planes,
        }

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

            # 保存会话JSON
            payload = DevUtils._session_to_dict(session)
            with open(target_dir / "session.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            logging.info(f"调试会话已保存: {target_dir}")
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

            format_used = "新格式(含数据)" if scene_file == new_scene_file else "旧格式(仅元数据)"
            logging.info(f"调试会话已加载: {target_dir} ({format_used})")
            return {"success": True, "message": f"加载成功 ({format_used})"}

        except Exception as e:
            logging.exception("加载调试会话时出错")
            return {"success": False, "message": f"异常: {e}"}
