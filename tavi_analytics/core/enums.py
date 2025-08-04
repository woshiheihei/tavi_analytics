"""
TAVR Analytics 枚举定义模块

该模块包含了TAVR Analytics工作流中使用的所有枚举类型，
主要用于标准化数据分类和用户界面选项。
"""

from enum import Enum


class ImageQuality(Enum):
    """图像质量枚举
    
    用于评估CT图像的质量等级，对应杭州方案术后CT核心实验室评估表中的图像质量字段。
    """
    EXCELLENT = "优"
    GOOD = "一般"
    POOR = "差"


class FollowUpTimepoint(Enum):
    """随访时间点枚举
    
    定义TAVR术后随访的标准时间节点，用于标准化随访数据收集。
    """
    ONE_MONTH = "1月"
    THREE_MONTHS = "3月"
    SIX_MONTHS = "6月"
    ONE_YEAR = "1年"
    TWO_YEARS = "2年"
    OTHER = "其他"
