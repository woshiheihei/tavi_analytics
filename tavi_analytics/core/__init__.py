"""
核心功能模块

包含会话管理、数据模型、枚举定义等核心组件。
这些组件被所有其他模块共同使用。
"""

# 核心组件导入
# from .session import TAVRStudySession  # 待任务1.3完成
from .data_models import PatientData
from .enums import ImageQuality, FollowUpTimepoint

__all__ = [
    # "TAVRStudySession",  # 待任务1.3完成
    "PatientData", 
    "ImageQuality",
    "FollowUpTimepoint"
]
