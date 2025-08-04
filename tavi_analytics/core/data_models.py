"""
TAVR Analytics 数据模型定义模块

该模块包含了TAVR Analytics工作流中使用的所有数据模型类，
主要用于结构化存储患者信息、研究数据和分析结果。
"""

import datetime
from dataclasses import dataclass
from typing import Optional

from .enums import ImageQuality, FollowUpTimepoint


@dataclass
class PatientData:
    """患者数据类
    
    对应杭州方案术后CT核心实验室评估表的基本情况部分，
    用于存储TAVR患者的基本信息和临床数据。
    
    Attributes:
        patientID: 受试者编号（必填）
        patientName: 患者姓名
        patientAge: 患者年龄
        patientSex: 患者性别
        surgeryDate: 手术日期
        ctScanDate: CT扫描日期
        imageQuality: 图像质量评估
        followUpTimepoint: 术后随访时间节点
        valveBrand: 瓣膜品牌（必填）
        valveModel: 瓣膜型号（必填）
        stsScore: STS评分（可选）
        euroScoreII: EuroScore II评分（可选）
    """
    patientID: str = ""
    patientName: str = ""
    patientAge: int = 0
    patientSex: str = ""
    surgeryDate: Optional[datetime.date] = None
    ctScanDate: Optional[datetime.date] = None
    imageQuality: ImageQuality = ImageQuality.GOOD
    followUpTimepoint: FollowUpTimepoint = FollowUpTimepoint.ONE_MONTH
    valveBrand: str = ""
    valveModel: str = ""
    stsScore: Optional[float] = None
    euroScoreII: Optional[float] = None
    
    def is_valid(self) -> bool:
        """检查患者数据是否包含必填字段
        
        Returns:
            bool: 如果包含必填字段返回True，否则返回False
        """
        return (
            self.patientID.strip() != "" and
            self.valveBrand.strip() != "" and
            self.valveModel.strip() != ""
        )
    
    def get_display_name(self) -> str:
        """获取用于显示的患者标识
        
        Returns:
            str: 患者显示名称，格式为"姓名(编号)"或仅编号
        """
        if self.patientName.strip():
            return f"{self.patientName}({self.patientID})"
        return self.patientID
    
    def to_dict(self) -> dict:
        """将患者数据转换为字典格式
        
        Returns:
            dict: 包含所有患者数据的字典
        """
        return {
            'patientID': self.patientID,
            'patientName': self.patientName,
            'patientAge': self.patientAge,
            'patientSex': self.patientSex,
            'surgeryDate': self.surgeryDate.isoformat() if self.surgeryDate else None,
            'ctScanDate': self.ctScanDate.isoformat() if self.ctScanDate else None,
            'imageQuality': self.imageQuality.value,
            'followUpTimepoint': self.followUpTimepoint.value,
            'valveBrand': self.valveBrand,
            'valveModel': self.valveModel,
            'stsScore': self.stsScore,
            'euroScoreII': self.euroScoreII
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PatientData':
        """从字典创建患者数据对象
        
        Args:
            data: 包含患者数据的字典
            
        Returns:
            PatientData: 新的患者数据对象
        """
        patient_data = cls()
        patient_data.patientID = data.get('patientID', '')
        patient_data.patientName = data.get('patientName', '')
        patient_data.patientAge = data.get('patientAge', 0)
        patient_data.patientSex = data.get('patientSex', '')
        
        # 处理日期字段
        surgery_date_str = data.get('surgeryDate')
        if surgery_date_str:
            patient_data.surgeryDate = datetime.date.fromisoformat(surgery_date_str)
            
        ct_scan_date_str = data.get('ctScanDate')
        if ct_scan_date_str:
            patient_data.ctScanDate = datetime.date.fromisoformat(ct_scan_date_str)
        
        # 处理枚举字段
        image_quality_str = data.get('imageQuality', ImageQuality.GOOD.value)
        patient_data.imageQuality = ImageQuality(image_quality_str)
        
        followup_timepoint_str = data.get('followUpTimepoint', FollowUpTimepoint.ONE_MONTH.value)
        patient_data.followUpTimepoint = FollowUpTimepoint(followup_timepoint_str)
        
        patient_data.valveBrand = data.get('valveBrand', '')
        patient_data.valveModel = data.get('valveModel', '')
        patient_data.stsScore = data.get('stsScore')
        patient_data.euroScoreII = data.get('euroScoreII')
        
        return patient_data
