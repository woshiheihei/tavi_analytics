"""
资源管理器

职责：
- 在模块加载时预加载必须的资源（如 assets/valve.nrrd）
- 对外提供统一的资源获取接口（如获取预加载的节点）

设计：
- 单例类，避免重复加载
- 运行在非 Slicer 环境时优雅降级（仅解析路径，不加载）
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional


def _has_slicer() -> bool:
	try:
		import slicer  # type: ignore
		_ = slicer
		return True
	except Exception:
		return False


class ResourceManager:
	"""全局资源管理器（单例）"""

	_instance: Optional["ResourceManager"] = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self) -> None:
		if getattr(self, "_initialized", False):
			return
		self._logger = logging.getLogger(__name__)
		self._resources: Dict[str, Any] = {}
		self._initialized = True

	# ---------- 公共 API ----------
	def ensure_preloaded(self) -> None:
		"""确保预加载资源已加载（幂等）。"""
		if self._resources.get("_preloaded", False):
			return
		self._preload_default_resources()
		self._resources["_preloaded"] = True

	def get(self, key: str, default: Any = None) -> Any:
		"""获取资源。常用键：
		- valve_template_node: 预加载的瓣膜模板体数据（vtkMRMLScalarVolumeNode 或 None）
		- valve_template_node_id: 上述节点的ID（str 或 None）
		- valve_template_path: 资源文件路径（str 或 None）
		"""
		return self._resources.get(key, default)

	def get_valve_template_node(self):
		"""获取预加载的 valve.nrrd 节点（可能为 None）。"""
		return self._resources.get("valve_template_node")

	def get_valve_template_node_id(self) -> Optional[str]:
		return self._resources.get("valve_template_node_id")

	# ---------- 内部实现 ----------
	def _preload_default_resources(self) -> None:
		"""预加载项目默认资源。"""
		try:
			path = self._resolve_valve_nrrd_path()
			self._resources["valve_template_path"] = path

			if path and _has_slicer():
				# 延迟导入，避免非 Slicer 环境报错
				import slicer  # type: ignore
				from slicer import util as slicer_util  # type: ignore

				# 如果场景中已存在同名节点则复用（避免 getNode 抛错）
				existing = slicer.mrmlScene.GetFirstNodeByName("ValveTemplate")
				if existing is not None:
					self._resources["valve_template_node"] = existing
					self._resources["valve_template_node_id"] = existing.GetID()
					# 确保不在 MPR 与 3D 视图中显示
					self._ensure_node_hidden(existing)
					self._logger.info("复用已存在的 ValveTemplate 节点，并保持隐藏显示状态")
					return

				if os.path.exists(path):
					# 使用 show=False 避免在 MPR & 3D 中自动显示
					node = slicer_util.loadVolume(path, properties={"name": "ValveTemplate", "show": False})
					if node:
						self._resources["valve_template_node"] = node
						self._resources["valve_template_node_id"] = node.GetID()
						# 保险处理：确保不在 MPR 与 3D 视图中显示
						self._ensure_node_hidden(node)
						self._logger.info(f"已预加载资源: valve.nrrd -> 节点ID={node.GetID()}（隐藏显示）")
				else:
					self._logger.warning(f"未找到资源文件: {path}")
			else:
				# 非 Slicer 环境：仅记录路径
				if not path:
					self._logger.warning("无法解析 valve.nrrd 路径；将在 Slicer 环境中再尝试加载")
		except Exception as e:
			self._logger.error(f"预加载资源失败: {e}")

	def _ensure_node_hidden(self, node: Any) -> None:
		"""确保体数据在 MPR 与 3D 视图中不显示。

		策略：
		- 加载时已使用 show=False，避免被设置为切片背景。
		- 保险：从各 SliceCompositeNode 中移除作为背景/前景/标签的引用。
		- 关闭体渲染显示（若存在体渲染显示节点）。
		- 隐藏体的显示节点可见性。
		"""
		try:
			import slicer  # type: ignore
			from slicer import util as slicer_util  # type: ignore

			# 从所有切片复合节点移除该体
			for scn in slicer_util.getNodesByClass('vtkMRMLSliceCompositeNode'):
				try:
					if scn.GetBackgroundVolumeID() == node.GetID():
						scn.SetBackgroundVolumeID(None)
					if scn.GetForegroundVolumeID() == node.GetID():
						scn.SetForegroundVolumeID(None)
					if scn.GetLabelVolumeID() == node.GetID():
						scn.SetLabelVolumeID(None)
				except Exception:
					pass

			# 隐藏体显示节点（与2D相关）
			display_node = node.GetDisplayNode() if hasattr(node, 'GetDisplayNode') else None
			if display_node and hasattr(display_node, 'SetVisibility'):
				display_node.SetVisibility(False)

			# 关闭体渲染（3D）
			try:
				vr_logic = slicer.modules.volumerendering.logic()
				vr_display_node = vr_logic.GetFirstVolumeRenderingDisplayNode(node)
				if vr_display_node:
					vr_display_node.SetVisibility(False)
			except Exception:
				pass
		except Exception:
			# 非 Slicer 环境或其他异常：忽略
			pass

	def _resolve_valve_nrrd_path(self) -> Optional[str]:
		"""解析 assets/valve.nrrd 的路径，提供多种回退方案。"""
		try:
			# 本文件位于 <repo>/tavi_analytics/core/resource_manager.py
			# 包根目录：<repo>/tavi_analytics
			package_root = os.path.dirname(os.path.dirname(__file__))
			repo_root = os.path.dirname(package_root)

			candidates = [
				os.path.join(repo_root, "assets", "valve.nrrd"),  # 开发环境
				os.path.join(package_root, "assets", "valve.nrrd"),  # 安装后资源目录
				os.path.join(package_root, "Resources", "valve.nrrd"),  # 若未来打包到Resources
			]

			for p in candidates:
				if os.path.exists(p):
					return p

			# 最后一种：当前工作目录（不推荐，但作为兜底）
			cwd_candidate = os.path.join(os.getcwd(), "assets", "valve.nrrd")
			if os.path.exists(cwd_candidate):
				return cwd_candidate

			return None
		except Exception:
			return None


def get_resource_manager() -> ResourceManager:
	"""便捷函数，获取单例资源管理器。"""
	return ResourceManager()

