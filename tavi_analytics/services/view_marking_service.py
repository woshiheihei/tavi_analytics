"""
视图标记服务 - 纯逻辑层实现

提供MPR视图的标记、保存、恢复等核心功能，与UI层解耦。
这个服务可以被不同的分析模块复用。

作者：TAVR Research Team
创建时间：2025年8月
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List, Tuple
import qt
import json
from pathlib import Path

# 轻量依赖，仅在需要时注入
try:
    from ..core.session import TAVRStudySession
    from ..utils.mpr_positioning.plane_position_manager import get_plane_position_manager
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from utils.mpr_positioning.plane_position_manager import get_plane_position_manager


class ViewMarkingService:
    """
    视图标记服务 - 管理MPR视图状态的保存和恢复
    
    这个服务提供了视图标记的核心逻辑，可以被不同的分析模块复用：
    - HALT分析
    - RELM分析
    - SFD分析
    - PFD分析
    """
    
    def __init__(self, analysis_type: str = "GENERAL", session: Optional[TAVRStudySession] = None):
        """
        初始化视图标记服务
        
        Args:
            analysis_type: 分析类型（HALT, RELM, SFD, PFD等）
            session: TAVR研究会话对象
        """
        self.analysis_type = analysis_type
        self.session = session
        self.marked_views: Dict[str, Dict[str, Any]] = {}
        self.plane_manager = get_plane_position_manager()
        
        # 设置持久化路径
        self._setup_persistence_path()
        
        # 加载已保存的视图标记
        self._load_marked_views()
        
        logging.info(f"ViewMarkingService 初始化完成 - 分析类型: {analysis_type}")
    
    def _setup_persistence_path(self):
        """设置持久化存储路径"""
        try:
            # 使用用户主目录下的应用数据目录
            app_data_dir = Path.home() / ".tavi_analytics" / "view_marks"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 根据分析类型和会话信息创建文件名
            session_id = getattr(self.session, 'study_name', 'default') if self.session else 'default'
            self.persistence_file = app_data_dir / f"{self.analysis_type}_{session_id}_views.json"
            
            logging.debug(f"视图标记持久化文件: {self.persistence_file}")
            
        except Exception as e:
            logging.error(f"设置持久化路径失败: {e}")
            self.persistence_file = None
    
    def _load_marked_views(self):
        """从文件加载已保存的视图标记"""
        if not self.persistence_file or not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.marked_views = data.get('marked_views', {})
                
            logging.info(f"加载了 {len(self.marked_views)} 个视图标记")
            
        except Exception as e:
            logging.error(f"加载视图标记失败: {e}")
            self.marked_views = {}
    
    def _save_marked_views(self):
        """保存视图标记到文件"""
        if not self.persistence_file:
            return
        
        try:
            data = {
                'analysis_type': self.analysis_type,
                'session_info': {
                    'study_name': getattr(self.session, 'study_name', 'Unknown') if self.session else 'Unknown',
                    'patient_id': getattr(self.session, 'patient_id', 'Unknown') if self.session else 'Unknown'
                },
                'last_updated': qt.QDateTime.currentDateTime().toString(),
                'marked_views': self.marked_views
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logging.debug(f"视图标记已保存到: {self.persistence_file}")
            
        except Exception as e:
            logging.error(f"保存视图标记失败: {e}")
    
    def mark_current_view(self, view_name: str, description: Optional[str] = None) -> bool:
        """
        标记当前MPR视图状态
        
        Args:
            view_name: 视图标记名称
            description: 可选的视图描述
            
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
            
            # 获取当前期像信息
            current_phase = None
            phase_display = None
            phase_icon = '❓'  # 默认未知期像图标
            
            if self.session:
                try:
                    phase_info = self.session.get_current_phase_info()
                    current_phase = phase_info.get('phase')
                    phase_display = phase_info.get('display_name')
                    phase_icon = phase_info.get('icon', '❓')
                    logging.debug(f"获取当前期像信息: {current_phase} ({phase_display})")
                except Exception as e:
                    logging.warning(f"获取期像信息失败: {e}")
            
            # 生成默认描述（包含期像信息）
            if not description:
                if phase_display:
                    description = f"{self.analysis_type}分析关键视图 - {view_name} ({phase_display})"
                else:
                    description = f"{self.analysis_type}分析关键视图 - {view_name}"
            
            # 保存视图状态（包含期像信息）
            self.marked_views[view_name] = {
                'center_point': center_point.tolist(),
                'normal_vector': normal_vector.tolist(),
                'phase': current_phase,
                'phase_display': phase_display,
                'phase_icon': phase_icon,
                'timestamp': qt.QDateTime.currentDateTime().toString(),
                'description': description,
                'analysis_type': self.analysis_type
            }
            
            # 持久化保存
            self._save_marked_views()
            
            logging.info(f"已标记视图: {view_name} ({self.analysis_type})")
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
            
            # 获取期像信息（向后兼容：旧数据可能没有期像信息）
            view_phase = view_data.get('phase')
            phase_display = view_data.get('phase_display', '未知期像')
            
            phase_restored = True  # 期像恢复标志
            mpr_restored = False   # MPR恢复标志
            
            # 步骤1：如果有期像信息，先恢复期像
            if view_phase and self.session:
                try:
                    logging.info(f"正在恢复期像: {phase_display} ({view_phase})")
                    phase_restored = self.session.switch_to_phase(view_phase, "ViewRestoration")
                    if not phase_restored:
                        logging.warning(f"期像恢复失败，将继续恢复MPR位置: {view_name}")
                except Exception as e:
                    logging.warning(f"期像恢复异常，将继续恢复MPR位置: {e}")
                    phase_restored = False
            elif view_phase:
                logging.info(f"视图包含期像信息 ({phase_display})，但未设置session，跳过期像恢复")
            else:
                logging.debug(f"视图无期像信息，跳过期像恢复（向后兼容）: {view_name}")
            
            # 步骤2：恢复MPR视图位置
            try:
                logging.debug(f"正在恢复MPR位置: {view_name}")
                mpr_restored = self.plane_manager.position_to_plane(center_point, normal_vector)
                if not mpr_restored:
                    logging.error(f"MPR位置恢复失败: {view_name}")
            except Exception as e:
                logging.error(f"MPR位置恢复异常: {e}")
                mpr_restored = False
            
            # 评估整体恢复结果
            overall_success = mpr_restored  # MPR恢复是核心要求
            
            if overall_success:
                if view_phase and phase_restored:
                    logging.info(f"已完整恢复视图: {view_name} (期像: {phase_display}, MPR: 成功)")
                elif view_phase and not phase_restored:
                    logging.info(f"已部分恢复视图: {view_name} (期像: 失败, MPR: 成功)")
                else:
                    logging.info(f"已恢复视图: {view_name} (仅MPR位置)")
            else:
                logging.error(f"视图恢复失败: {view_name}")
            
            return overall_success
            
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
    
    def get_view_details(self, view_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定视图的详细信息
        
        Args:
            view_name: 视图名称
            
        Returns:
            Optional[Dict[str, Any]]: 视图详细信息，如果不存在返回None
        """
        return self.marked_views.get(view_name)
    
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
                self._save_marked_views()
                logging.info(f"已清除视图标记: {view_name} ({self.analysis_type})")
                return True
            else:
                logging.warning(f"视图标记不存在: {view_name}")
                return False
        except Exception as e:
            logging.error(f"清除视图标记失败: {e}")
            return False
    
    def clear_all_marks(self) -> bool:
        """
        清除所有视图标记
        
        Returns:
            bool: 清除成功返回True
        """
        try:
            count = len(self.marked_views)
            self.marked_views.clear()
            self._save_marked_views()
            logging.info(f"已清除所有视图标记 ({count}个) - {self.analysis_type}")
            return True
        except Exception as e:
            logging.error(f"清除所有视图标记失败: {e}")
            return False
    
    def rename_view_mark(self, old_name: str, new_name: str) -> bool:
        """
        重命名视图标记
        
        Args:
            old_name: 原视图名称
            new_name: 新视图名称
            
        Returns:
            bool: 重命名成功返回True
        """
        try:
            if old_name not in self.marked_views:
                logging.error(f"原视图标记不存在: {old_name}")
                return False
            
            if new_name in self.marked_views:
                logging.error(f"新视图名称已存在: {new_name}")
                return False
            
            # 复制数据到新名称
            self.marked_views[new_name] = self.marked_views[old_name].copy()
            self.marked_views[new_name]['description'] = f"{self.analysis_type}分析关键视图 - {new_name}"
            
            # 删除原数据
            del self.marked_views[old_name]
            
            self._save_marked_views()
            logging.info(f"视图标记已重命名: {old_name} -> {new_name}")
            return True
            
        except Exception as e:
            logging.error(f"重命名视图标记失败: {e}")
            return False
    
    def export_views(self, export_path: Optional[str] = None) -> Optional[str]:
        """
        导出视图标记到文件
        
        Args:
            export_path: 可选的导出文件路径
            
        Returns:
            Optional[str]: 导出成功返回文件路径，失败返回None
        """
        try:
            if not export_path:
                timestamp = qt.QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
                export_dir = Path.home() / "TAVR_Analytics_Exports"
                export_dir.mkdir(exist_ok=True)
                export_path = export_dir / f"{self.analysis_type}_Views_{timestamp}.json"
            
            export_data = {
                'export_info': {
                    'analysis_type': self.analysis_type,
                    'export_time': qt.QDateTime.currentDateTime().toString(),
                    'view_count': len(self.marked_views)
                },
                'session_info': {
                    'study_name': getattr(self.session, 'study_name', 'Unknown') if self.session else 'Unknown',
                    'patient_id': getattr(self.session, 'patient_id', 'Unknown') if self.session else 'Unknown'
                },
                'marked_views': self.marked_views
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"视图标记已导出到: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logging.error(f"导出视图标记失败: {e}")
            return None
    
    def import_views(self, import_path: str, merge: bool = True) -> bool:
        """
        从文件导入视图标记
        
        Args:
            import_path: 导入文件路径
            merge: 是否合并到现有标记（True）还是替换（False）
            
        Returns:
            bool: 导入成功返回True
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_views = import_data.get('marked_views', {})
            
            if not merge:
                self.marked_views.clear()
            
            # 合并或替换视图标记
            for name, data in imported_views.items():
                # 确保导入的数据有正确的分析类型标记
                data['analysis_type'] = self.analysis_type
                self.marked_views[name] = data
            
            self._save_marked_views()
            
            count = len(imported_views)
            action = "合并" if merge else "替换"
            logging.info(f"已{action}导入 {count} 个视图标记")
            return True
            
        except Exception as e:
            logging.error(f"导入视图标记失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取视图标记统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.marked_views:
            return {
                'total_count': 0,
                'analysis_type': self.analysis_type,
                'oldest_mark': None,
                'newest_mark': None
            }
        
        timestamps = [data['timestamp'] for data in self.marked_views.values()]
        
        return {
            'total_count': len(self.marked_views),
            'analysis_type': self.analysis_type,
            'oldest_mark': min(timestamps) if timestamps else None,
            'newest_mark': max(timestamps) if timestamps else None,
            'view_names': list(self.marked_views.keys())
        }
    
    def get_views_by_phase(self) -> Dict[str, Dict[str, str]]:
        """
        按期像分组获取视图
        
        Returns:
            Dict[str, Dict[str, str]]: 按期像分组的视图字典
                格式：{'diastole': {'view1': 'desc1'}, 'systole': {'view2': 'desc2'}, 'unknown': {'view3': 'desc3'}}
        """
        phase_groups = {
            'diastole': {},
            'systole': {},
            'unknown': {}
        }
        
        for view_name, view_data in self.marked_views.items():
            phase = view_data.get('phase', 'unknown')
            if phase not in ['diastole', 'systole']:
                phase = 'unknown'
            
            phase_groups[phase][view_name] = view_data.get('description', view_name)
        
        return phase_groups
    
    def get_phase_statistics(self) -> Dict[str, Any]:
        """
        获取各期像的视图统计信息
        
        Returns:
            Dict[str, Any]: 期像统计信息
        """
        phase_groups = self.get_views_by_phase()
        
        return {
            'total_count': len(self.marked_views),
            'diastole_count': len(phase_groups['diastole']),
            'systole_count': len(phase_groups['systole']),
            'unknown_count': len(phase_groups['unknown']),
            'phase_distribution': {
                'diastole': {
                    'count': len(phase_groups['diastole']),
                    'display_name': '舒张末期',
                    'icon': '🫀',
                    'views': list(phase_groups['diastole'].keys())
                },
                'systole': {
                    'count': len(phase_groups['systole']),
                    'display_name': '收缩末期', 
                    'icon': '❤️',
                    'views': list(phase_groups['systole'].keys())
                },
                'unknown': {
                    'count': len(phase_groups['unknown']),
                    'display_name': '未知期像',
                    'icon': '❓',
                    'views': list(phase_groups['unknown'].keys())
                }
            }
        }
    
    def get_phase_display_icon(self, phase: Optional[str]) -> str:
        """
        获取期像显示图标
        
        Args:
            phase: 期像类型
            
        Returns:
            str: 期像图标
        """
        icons = {
            'diastole': '🫀',  # 舒张末期
            'systole': '❤️',   # 收缩末期
        }
        return icons.get(phase, '❓')  # 未知期像
    
    def has_phase_info(self, view_name: str) -> bool:
        """
        检查指定视图是否包含期像信息
        
        Args:
            view_name: 视图名称
            
        Returns:
            bool: 包含期像信息返回True
        """
        if view_name not in self.marked_views:
            return False
        
        view_data = self.marked_views[view_name]
        return view_data.get('phase') is not None
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        # 重新设置持久化路径
        self._setup_persistence_path()
        # 重新加载视图标记
        self._load_marked_views()
    
    def cleanup(self):
        """清理资源"""
        # 保存当前状态
        self._save_marked_views()
        logging.info(f"ViewMarkingService 清理完成 - {self.analysis_type}")


# 单例模式的服务获取函数
_view_marking_services: Dict[str, ViewMarkingService] = {}

def get_view_marking_service(analysis_type: str = "GENERAL", session: Optional[TAVRStudySession] = None) -> ViewMarkingService:
    """
    获取视图标记服务实例（单例模式）
    
    Args:
        analysis_type: 分析类型
        session: 会话对象
        
    Returns:
        ViewMarkingService: 视图标记服务实例
    """
    global _view_marking_services
    
    service_key = f"{analysis_type}_{id(session) if session else 'default'}"
    
    if service_key not in _view_marking_services:
        _view_marking_services[service_key] = ViewMarkingService(analysis_type, session)
    
    return _view_marking_services[service_key]


def cleanup_view_marking_services():
    """清理所有视图标记服务实例"""
    global _view_marking_services
    
    for service in _view_marking_services.values():
        service.cleanup()
    
    _view_marking_services.clear()
    logging.info("所有视图标记服务已清理")
