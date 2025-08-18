"""
服务模块

提供业务逻辑层的服务组件。
"""

from .contour_positioning_service import get_contour_position_service
from .view_marking_service import get_view_marking_service, cleanup_view_marking_services

__all__ = [
    'get_contour_position_service',
    'get_view_marking_service',
    'cleanup_view_marking_services'
]