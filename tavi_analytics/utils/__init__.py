"""
工具类模块

包含DICOM处理、配置管理、日志记录等通用工具函数。
为所有模块提供基础的工具支持。
"""

# 导入工具类 - 使用try-except确保兼容性
try:
    from .dicom_utils import DicomUtils
except ImportError:
    from dicom_utils import DicomUtils

try:
    from .config_manager import ConfigManager
except ImportError:
    from config_manager import ConfigManager

try:
    from .qt_utils import QtUtils
except ImportError:
    from qt_utils import QtUtils

try:
    from .logging_utils import LoggingUtils
except ImportError:
    from logging_utils import LoggingUtils

try:
    from .contour_position import ContourPositionManager, get_contour_manager, switch_to_contour
except ImportError:
    from contour_position import ContourPositionManager, get_contour_manager, switch_to_contour

__all__ = [
    "DicomUtils",
    "ConfigManager", 
    "QtUtils",
    "LoggingUtils",
    "ContourPositionManager",
    "get_contour_manager",
    "switch_to_contour"
]
