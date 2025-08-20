"""
插件配置管理器 - 统一管理TAVR Analytics插件的配置
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import slicer


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    license: str
    dependencies: List[str]
    slicer_version_min: str
    slicer_version_max: Optional[str] = None


class PluginConfig:
    """插件配置管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._logger = logging.getLogger(__name__)
            self._config_data: Dict[str, Any] = {}
            self._plugin_dir = None
            self._config_file_path = None
            self._valve_config_path = None
            self._metadata = None
            self._initialize_paths()
            self._load_configuration()
            PluginConfig._initialized = True
    
    def _initialize_paths(self):
        """初始化配置文件路径"""
        try:
            # 获取插件目录
            import inspect
            current_file = inspect.getfile(inspect.currentframe())
            self._plugin_dir = os.path.dirname(os.path.dirname(current_file))
            
            # 设置配置文件路径
            self._config_file_path = os.path.join(self._plugin_dir, "config.json")
            self._valve_config_path = os.path.join(self._plugin_dir, "Resources", "valve_config.json")
            
            self._logger.info(f"插件目录: {self._plugin_dir}")
            self._logger.info(f"配置文件路径: {self._config_file_path}")
            
        except Exception as e:
            self._logger.error(f"初始化配置路径时出错: {e}")
            # 使用默认路径
            self._plugin_dir = os.path.dirname(__file__)
            self._config_file_path = os.path.join(self._plugin_dir, "config.json")
    
    def _load_configuration(self):
        """加载配置文件"""
        # 加载默认配置
        self._load_default_config()
        
        # 尝试加载用户配置文件
        if os.path.exists(self._config_file_path):
            try:
                with open(self._config_file_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
                self._logger.info("用户配置文件加载成功")
            except Exception as e:
                self._logger.error(f"加载用户配置文件时出错: {e}")
        else:
            self._logger.info("用户配置文件不存在，使用默认配置")
    
    def _load_default_config(self):
        """加载默认配置"""
        self._config_data = {
            "plugin": {
                "name": "TAVR Analytics",
                "version": "1.0.0",
                "description": "TAVR术后四维心脏CT分析插件",
                "author": "TAVR Research Team",
                "license": "MIT",
                "dependencies": ["Sequences"],
                "slicer_version_min": "5.0.0"
            },
            "ui": {
                "theme": "default",
                "language": "zh_CN",
                "show_advanced_options": False,
                "auto_save_enabled": True,
                "auto_save_interval": 300  # 秒
            },
            "modules": {
                "module1": {
                    "enabled": True,
                    "auto_load_dicom": True,
                    "preserve_original_names": True,
                    "default_quality": "GOOD"
                },
                "module2": {
                    "enabled": False,
                    "auto_segment": False
                },
                "module3": {
                    "enabled": False,
                    "auto_measure": False
                },
                "module4": {
                    "enabled": True,
                    "auto_generate_report": False
                },
                "module5": {
                    "enabled": False,
                    "auto_export": False
                }
            },
            "data": {
                "default_output_dir": "",
                "backup_enabled": True,
                "max_backup_files": 10,
                "compress_backups": True
            },
            "performance": {
                "max_memory_usage": 8192,  # MB
                "use_gpu_acceleration": False,
                "parallel_processing": True,
                "max_threads": 4
            },
            "debug": {
                "logging_level": "INFO",
                "debug_mode": False,
                "show_debug_info": False,
                "profiling_enabled": False
            }
        }
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """合并用户配置"""
        def merge_dict(base_dict: Dict, update_dict: Dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    merge_dict(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        merge_dict(self._config_data, user_config)
    
    def get_config(self, key_path: str, default=None) -> Any:
        """获取配置值"""
        keys = key_path.split('.')
        current = self._config_data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set_config(self, key_path: str, value: Any):
        """设置配置值"""
        keys = key_path.split('.')
        current = self._config_data
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        current[keys[-1]] = value
        self._logger.info(f"配置项 {key_path} 已设置为: {value}")
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._config_file_path), exist_ok=True)
            
            with open(self._config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"配置已保存到: {self._config_file_path}")
            return True
        except Exception as e:
            self._logger.error(f"保存配置时出错: {e}")
            return False
    
    def reset_config(self):
        """重置配置为默认值"""
        self._load_default_config()
        self._logger.info("配置已重置为默认值")
    
    def get_plugin_metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        if self._metadata is None:
            plugin_config = self.get_config("plugin", {})
            self._metadata = PluginMetadata(
                name=plugin_config.get("name", "TAVR Analytics"),
                version=plugin_config.get("version", "1.0.0"),
                description=plugin_config.get("description", ""),
                author=plugin_config.get("author", ""),
                license=plugin_config.get("license", "MIT"),
                dependencies=plugin_config.get("dependencies", []),
                slicer_version_min=plugin_config.get("slicer_version_min", "5.0.0"),
                slicer_version_max=plugin_config.get("slicer_version_max")
            )
        return self._metadata
    
    def get_valve_config(self) -> Dict[str, Any]:
        """获取瓣膜配置"""
        if not hasattr(self, '_valve_config'):
            self._valve_config = {}
            
            if os.path.exists(self._valve_config_path):
                try:
                    with open(self._valve_config_path, 'r', encoding='utf-8') as f:
                        self._valve_config = json.load(f)
                    self._logger.info("瓣膜配置加载成功")
                except Exception as e:
                    self._logger.error(f"加载瓣膜配置时出错: {e}")
                    self._valve_config = self._get_default_valve_config()
            else:
                self._logger.warning("瓣膜配置文件不存在，使用默认配置")
                self._valve_config = self._get_default_valve_config()
        
        return self._valve_config
    
    def _get_default_valve_config(self) -> Dict[str, Any]:
        """获取默认瓣膜配置"""
        return {
            "valve_brands": {
                "Medtronic": {
                    "models": ["Evolut R/PRO", "Evolut FX", "CoreValve"],
                    "sizes": ["23mm", "26mm", "29mm", "34mm"]
                },
                "Edwards": {
                    "models": ["SAPIEN 3", "SAPIEN 3 Ultra"],
                    "sizes": ["20mm", "23mm", "26mm", "29mm"]
                },
                "Abbott": {
                    "models": ["Portico", "Navitor"],
                    "sizes": ["23mm", "25mm", "27mm", "29mm"]
                }
            },
            "default_brand": "Medtronic",
            "default_model": "Evolut R/PRO",
            "default_size": "26mm"
        }
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """获取模块配置"""
        return self.get_config(f"modules.{module_name}", {})
    
    def set_module_config(self, module_name: str, config: Dict[str, Any]):
        """设置模块配置"""
        self.set_config(f"modules.{module_name}", config)
    
    def is_module_enabled(self, module_name: str) -> bool:
        """检查模块是否启用"""
        return self.get_config(f"modules.{module_name}.enabled", False)
    
    def enable_module(self, module_name: str):
        """启用模块"""
        self.set_config(f"modules.{module_name}.enabled", True)
    
    def disable_module(self, module_name: str):
        """禁用模块"""
        self.set_config(f"modules.{module_name}.enabled", False)
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self.get_config("ui", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.get_config("performance", {})
    
    def get_debug_config(self) -> Dict[str, Any]:
        """获取调试配置"""
        return self.get_config("debug", {})
    
    def setup_logging(self):
        """根据配置设置日志"""
        debug_config = self.get_debug_config()
        logging_level = debug_config.get("logging_level", "INFO")
        
        # 设置日志级别
        numeric_level = getattr(logging, logging_level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        
        self._logger.info(f"日志级别设置为: {logging_level}")
    
    def get_resource_path(self, relative_path: str) -> str:
        """获取资源文件路径"""
        return os.path.join(self._plugin_dir, "Resources", relative_path)
    
    def get_plugin_dir(self) -> str:
        """获取插件目录"""
        return self._plugin_dir
    
    def validate_config(self) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        # 验证插件元数据
        plugin_config = self.get_config("plugin", {})
        if not plugin_config.get("name"):
            errors.append("插件名称不能为空")
        
        if not plugin_config.get("version"):
            errors.append("插件版本不能为空")
        
        # 验证性能配置
        perf_config = self.get_performance_config()
        max_memory = perf_config.get("max_memory_usage", 0)
        if max_memory < 1024:
            errors.append("最大内存使用量不能小于1024MB")
        
        max_threads = perf_config.get("max_threads", 0)
        if max_threads < 1:
            errors.append("最大线程数不能小于1")
        
        return errors
