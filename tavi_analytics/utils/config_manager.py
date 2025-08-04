"""
配置管理工具模块

提供配置文件加载、保存、验证等功能。
"""

import os
import json
import logging
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理工具类"""

    @staticmethod
    def load_valve_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载瓣膜配置文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            配置字典
        """
        try:
            if config_path is None:
                # 使用默认路径
                current_dir = os.path.dirname(os.path.dirname(__file__))
                config_path = os.path.join(current_dir, "Resources", "valve_config.json")
            
            if not os.path.exists(config_path):
                logging.warning(f"Valve config file not found: {config_path}")
                return ConfigManager.get_default_valve_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 验证配置格式
            if ConfigManager.validate_valve_config(config):
                logging.info(f"Successfully loaded valve configuration from {config_path}")
                return config
            else:
                logging.warning(f"Invalid valve configuration format in {config_path}")
                return ConfigManager.get_default_valve_config()
                
        except Exception as e:
            logging.error(f"Failed to load valve configuration: {e}")
            return ConfigManager.get_default_valve_config()

    @staticmethod
    def save_valve_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
        """保存瓣膜配置文件
        
        Args:
            config: 配置字典
            config_path: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            保存是否成功
        """
        try:
            if config_path is None:
                # 使用默认路径
                current_dir = os.path.dirname(os.path.dirname(__file__))
                config_path = os.path.join(current_dir, "Resources", "valve_config.json")
            
            # 验证配置格式
            if not ConfigManager.validate_valve_config(config):
                logging.error("Invalid valve configuration format")
                return False
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logging.info(f"Successfully saved valve configuration to {config_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save valve configuration: {e}")
            return False

    @staticmethod
    def validate_valve_config(config: Dict[str, Any]) -> bool:
        """验证瓣膜配置格式
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        try:
            if not isinstance(config, dict):
                return False
            
            for brand, models in config.items():
                if not isinstance(brand, str) or not brand.strip():
                    return False
                if not isinstance(models, list):
                    return False
                for model in models:
                    if not isinstance(model, str) or not model.strip():
                        return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def get_default_valve_config() -> Dict[str, Any]:
        """获取默认瓣膜配置
        
        Returns:
            默认配置字典
        """
        return {
            "Medtronic": [
                "Evolut R/PRO",
                "Evolut R",
                "Evolut PRO",
                "Evolut PRO+",
                "CoreValve"
            ],
            "Edwards Lifesciences": [
                "SAPIEN 3",
                "SAPIEN 3 Ultra",
                "SAPIEN XT",
                "SAPIEN S3"
            ],
            "Venus Medtech": [
                "VenusA-Valve",
                "VenusA-Plus",
                "VenusA-Valve Plus"
            ],
            "MicroPort": [
                "VitaFlow",
                "VitaFlow II",
                "VitaFlow Liberty"
            ],
            "Peijia Medical": [
                "TaurusOne",
                "TaurusElite"
            ],
            "其他": [
                "自定义型号"
            ]
        }

    @staticmethod
    def load_json_config(file_path: str) -> Optional[Dict[str, Any]]:
        """加载通用JSON配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典，失败时返回None
        """
        try:
            if not os.path.exists(file_path):
                logging.warning(f"Config file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            logging.info(f"Successfully loaded configuration from {file_path}")
            return config
            
        except Exception as e:
            logging.error(f"Failed to load configuration from {file_path}: {e}")
            return None

    @staticmethod
    def save_json_config(config: Dict[str, Any], file_path: str) -> bool:
        """保存通用JSON配置文件
        
        Args:
            config: 配置字典
            file_path: 配置文件路径
            
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logging.info(f"Successfully saved configuration to {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save configuration to {file_path}: {e}")
            return False

    @staticmethod
    def get_config_value(config: Dict[str, Any], key_path: str, default_value: Any = None) -> Any:
        """从配置中获取嵌套键值
        
        Args:
            config: 配置字典
            key_path: 键路径，用.分隔，如"section.subsection.key"
            default_value: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default_value
                    
            return value
            
        except Exception:
            return default_value

    @staticmethod
    def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> bool:
        """设置配置中的嵌套键值
        
        Args:
            config: 配置字典
            key_path: 键路径，用.分隔，如"section.subsection.key"
            value: 要设置的值
            
        Returns:
            设置是否成功
        """
        try:
            keys = key_path.split('.')
            current = config
            
            # 导航到倒数第二级
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    return False
                current = current[key]
            
            # 设置最终值
            current[keys[-1]] = value
            return True
            
        except Exception:
            return False

    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并两个配置字典
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            合并后的配置
        """
        try:
            result = base_config.copy()
            
            for key, value in override_config.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = ConfigManager.merge_configs(result[key], value)
                else:
                    result[key] = value
                    
            return result
            
        except Exception as e:
            logging.error(f"Failed to merge configurations: {e}")
            return base_config

    @staticmethod
    def validate_config_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """验证配置是否符合指定模式
        
        Args:
            config: 要验证的配置
            schema: 配置模式定义
            
        Returns:
            验证结果
        """
        try:
            # 简单的模式验证实现
            # 可以根据需要扩展为更复杂的验证逻辑
            
            def validate_value(value, schema_def):
                if isinstance(schema_def, type):
                    return isinstance(value, schema_def)
                elif isinstance(schema_def, dict):
                    if not isinstance(value, dict):
                        return False
                    for key, sub_schema in schema_def.items():
                        if key not in value:
                            return False
                        if not validate_value(value[key], sub_schema):
                            return False
                    return True
                elif isinstance(schema_def, list):
                    if not isinstance(value, list):
                        return False
                    if len(schema_def) > 0:
                        # 验证列表中的每个元素
                        element_schema = schema_def[0]
                        for item in value:
                            if not validate_value(item, element_schema):
                                return False
                    return True
                else:
                    return True
            
            return validate_value(config, schema)
            
        except Exception as e:
            logging.error(f"Failed to validate config schema: {e}")
            return False
