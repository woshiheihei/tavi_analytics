"""
瓣膜平面配置服务

提供基于瓣膜厂家和型号的平面高度配置管理，
用于 inflow、nadir、commissure level 的分析。
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ValvePlaneConfig:
    """瓣膜平面配置数据类"""
    inflow: float
    nadir: float
    commissure: float
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'inflow': self.inflow,
            'nadir': self.nadir,
            'commissure': self.commissure,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValvePlaneConfig':
        return cls(
            inflow=data.get('inflow', 0.5),
            nadir=data.get('nadir', 1.0),
            commissure=data.get('commissure', 1.5),
            description=data.get('description', '')
        )


class ValvePlaneConfigService:
    """瓣膜平面配置服务类"""
    
    def __init__(self):
        """初始化配置服务"""
        self.logger = logging.getLogger(__name__)
        self._config_data: Optional[Dict[str, Any]] = None
        self._config_path = self._get_config_path()
        
    def _get_config_path(self) -> str:
        """获取配置文件路径"""
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        return os.path.join(parent_dir, "Resources", "valve_plane_config.json")
    
    def load_config(self) -> bool:
        """
        加载瓣膜平面配置
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                self.logger.info("瓣膜平面配置加载成功")
                return True
            else:
                self.logger.warning(f"配置文件不存在: {self._config_path}")
                self._config_data = self._get_default_config()
                return False
        except Exception as e:
            self.logger.error(f"加载瓣膜平面配置失败: {e}")
            self._config_data = self._get_default_config()
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "configurations": {},
            "default": {
                "inflow": 0.5,
                "nadir": 1.0,
                "commissure": 1.5,
                "description": "Default configuration"
            },
            "available_heights": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
            "measurement_parameters": ["perimeter", "area", "max_dist", "min_dist", "ped", "aed"]
        }
    
    def get_valve_plane_config(self, manufacturer: str, model: str) -> ValvePlaneConfig:
        """
        获取指定瓣膜的平面配置
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
            
        Returns:
            ValvePlaneConfig: 瓣膜平面配置
        """
        if not self._config_data:
            self.load_config()
        
        try:
            # 尝试获取特定瓣膜配置
            configs = self._config_data.get('configurations', {})
            manufacturer_configs = configs.get(manufacturer, {})
            model_config = manufacturer_configs.get(model)
            
            if model_config:
                self.logger.info(f"找到瓣膜 {manufacturer} {model} 的专用配置")
                return ValvePlaneConfig.from_dict(model_config)
            
            # 回退到默认配置
            default_config = self._config_data.get('default', {})
            self.logger.warning(f"未找到瓣膜 {manufacturer} {model} 的专用配置，使用默认配置")
            return ValvePlaneConfig.from_dict(default_config)
            
        except Exception as e:
            self.logger.error(f"获取瓣膜平面配置失败: {e}")
            # 返回硬编码默认配置
            return ValvePlaneConfig(inflow=0.5, nadir=1.0, commissure=1.5, description="Emergency default")
    
    def get_plane_height_for_level(self, manufacturer: str, model: str, level: str) -> float:
        """
        获取指定级别的平面高度
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
            level: 平面级别 ('inflow', 'nadir', 'commissure')
            
        Returns:
            float: 平面高度 (cm)
        """
        config = self.get_valve_plane_config(manufacturer, model)
        
        if level == 'inflow':
            return config.inflow
        elif level == 'nadir':
            return config.nadir
        elif level == 'commissure':
            return config.commissure
        else:
            self.logger.warning(f"未知的平面级别: {level}")
            return config.inflow  # 默认返回 inflow
    
    def get_json_field_name_for_height(self, height: float) -> str:
        """
        获取指定高度对应的JSON字段名
        
        Args:
            height: 高度值 (cm)
            
        Returns:
            str: JSON字段名，如 'Stent_Frame_base_up_0.5_plane'
        """
        return f"Stent_Frame_base_up_{height}_plane"
    
    def get_available_heights(self) -> List[float]:
        """
        获取所有可用的平面高度
        
        Returns:
            List[float]: 可用高度列表
        """
        if not self._config_data:
            self.load_config()
        
        return self._config_data.get('available_heights', [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
    
    def get_measurement_parameters(self) -> List[str]:
        """
        获取测量参数列表
        
        Returns:
            List[str]: 测量参数名称列表
        """
        if not self._config_data:
            self.load_config()
        
        return self._config_data.get('measurement_parameters', ["perimeter", "area", "max_dist", "min_dist", "ped", "aed"])
    
    def validate_configuration(self, manufacturer: str, model: str) -> bool:
        """
        验证瓣膜配置是否有效
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
            
        Returns:
            bool: 配置是否有效
        """
        try:
            config = self.get_valve_plane_config(manufacturer, model)
            
            # 检查配置值是否合理
            valid = (
                0 < config.inflow <= 5.0 and
                0 < config.nadir <= 5.0 and
                0 < config.commissure <= 5.0 and
                config.inflow <= config.nadir <= config.commissure
            )
            
            if not valid:
                self.logger.warning(f"瓣膜 {manufacturer} {model} 配置值不合理")
            
            return valid
            
        except Exception as e:
            self.logger.error(f"验证瓣膜配置失败: {e}")
            return False
    
    def get_all_supported_valves(self) -> List[Tuple[str, str]]:
        """
        获取所有支持的瓣膜列表
        
        Returns:
            List[Tuple[str, str]]: (厂家, 型号) 元组列表
        """
        if not self._config_data:
            self.load_config()
        
        valves = []
        configs = self._config_data.get('configurations', {})
        
        for manufacturer, models in configs.items():
            for model in models.keys():
                valves.append((manufacturer, model))
        
        return valves
    
    def get_valve_mapping_summary(self, manufacturer: str, model: str) -> Dict[str, Any]:
        """
        获取瓣膜映射摘要信息
        
        Args:
            manufacturer: 瓣膜厂家
            model: 瓣膜型号
            
        Returns:
            Dict[str, Any]: 映射摘要信息
        """
        config = self.get_valve_plane_config(manufacturer, model)
        
        return {
            'valve_info': {
                'manufacturer': manufacturer,
                'model': model,
                'description': config.description
            },
            'plane_mappings': {
                'inflow': {
                    'height': config.inflow,
                    'json_field': self.get_json_field_name_for_height(config.inflow)
                },
                'nadir': {
                    'height': config.nadir,
                    'json_field': self.get_json_field_name_for_height(config.nadir)
                },
                'commissure': {
                    'height': config.commissure,
                    'json_field': self.get_json_field_name_for_height(config.commissure)
                }
            },
            'validation': self.validate_configuration(manufacturer, model)
        }


# 单例实例
_valve_plane_config_service = None


def get_valve_plane_config_service() -> ValvePlaneConfigService:
    """
    获取瓣膜平面配置服务单例实例
    
    Returns:
        ValvePlaneConfigService: 配置服务实例
    """
    global _valve_plane_config_service
    if _valve_plane_config_service is None:
        _valve_plane_config_service = ValvePlaneConfigService()
        _valve_plane_config_service.load_config()
    return _valve_plane_config_service