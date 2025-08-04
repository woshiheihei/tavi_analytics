"""
日志工具模块

提供统一的日志配置、格式化、文件输出等功能。
"""

import os
import logging
import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


class LoggingUtils:
    """日志工具类"""

    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False

    @staticmethod
    def initialize_logging(
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True
    ):
        """初始化日志系统
        
        Args:
            log_level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            log_dir: 日志文件目录，如果为None则不写入文件
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
            console_output: 是否输出到控制台
        """
        if LoggingUtils._initialized:
            return

        # 设置根日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)

        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)

        # 文件输出
        if log_dir:
            try:
                os.makedirs(log_dir, exist_ok=True)
                
                log_file = os.path.join(log_dir, "tavi_analytics.log")
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logging.getLogger().addHandler(file_handler)
                
            except Exception as e:
                logging.error(f"Failed to setup file logging: {e}")

        LoggingUtils._initialized = True
        logging.info("Logging system initialized")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """获取指定名称的日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            日志器实例
        """
        if name not in LoggingUtils._loggers:
            logger = logging.getLogger(name)
            LoggingUtils._loggers[name] = logger
        
        return LoggingUtils._loggers[name]

    @staticmethod
    def log_function_call(func):
        """装饰器：记录函数调用
        
        Args:
            func: 要装饰的函数
            
        Returns:
            装饰后的函数
        """
        def wrapper(*args, **kwargs):
            logger = LoggingUtils.get_logger(func.__module__)
            logger.debug(f"Calling function: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Function {func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
        
        return wrapper

    @staticmethod
    def log_exception(logger: logging.Logger, message: str, exc_info: bool = True):
        """记录异常信息
        
        Args:
            logger: 日志器
            message: 错误消息
            exc_info: 是否包含异常堆栈信息
        """
        try:
            logger.error(message, exc_info=exc_info)
        except Exception:
            # 如果日志记录本身失败，至少打印到标准错误
            import sys
            print(f"Logging failed: {message}", file=sys.stderr)

    @staticmethod
    def create_session_logger(session_id: str, log_dir: Optional[str] = None) -> logging.Logger:
        """为会话创建专用日志器
        
        Args:
            session_id: 会话ID
            log_dir: 日志目录
            
        Returns:
            会话日志器
        """
        logger_name = f"session_{session_id}"
        logger = logging.getLogger(logger_name)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.DEBUG)
        
        # 创建格式器
        formatter = logging.Formatter(
            f'%(asctime)s - {session_id} - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件输出
        if log_dir:
            try:
                os.makedirs(log_dir, exist_ok=True)
                
                log_file = os.path.join(log_dir, f"session_{session_id}.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
            except Exception as e:
                logging.error(f"Failed to create session logger: {e}")
        
        LoggingUtils._loggers[logger_name] = logger
        return logger

    @staticmethod
    def log_patient_operation(patient_id: str, operation: str, details: Optional[str] = None):
        """记录患者操作
        
        Args:
            patient_id: 患者ID
            operation: 操作类型
            details: 操作详情
        """
        logger = LoggingUtils.get_logger("patient_operations")
        
        timestamp = datetime.datetime.now().isoformat()
        log_message = f"Patient: {patient_id}, Operation: {operation}, Time: {timestamp}"
        
        if details:
            log_message += f", Details: {details}"
        
        logger.info(log_message)

    @staticmethod
    def log_dicom_operation(operation: str, file_path: Optional[str] = None, 
                           series_uid: Optional[str] = None, details: Optional[str] = None):
        """记录DICOM操作
        
        Args:
            operation: 操作类型
            file_path: DICOM文件路径
            series_uid: 序列UID
            details: 操作详情
        """
        logger = LoggingUtils.get_logger("dicom_operations")
        
        timestamp = datetime.datetime.now().isoformat()
        log_message = f"DICOM Operation: {operation}, Time: {timestamp}"
        
        if file_path:
            log_message += f", File: {file_path}"
        
        if series_uid:
            log_message += f", Series UID: {series_uid}"
        
        if details:
            log_message += f", Details: {details}"
        
        logger.info(log_message)

    @staticmethod
    def log_system_info():
        """记录系统信息"""
        logger = LoggingUtils.get_logger("system")
        
        try:
            import platform
            import sys
            
            logger.info(f"System: {platform.system()} {platform.release()}")
            logger.info(f"Python: {sys.version}")
            logger.info(f"Platform: {platform.platform()}")
            
            # 尝试获取3D Slicer版本信息
            try:
                import slicer
                logger.info(f"3D Slicer version: {slicer.app.applicationVersion}")
            except:
                logger.info("3D Slicer version: Unknown")
                
        except Exception as e:
            logger.error(f"Failed to log system info: {e}")

    @staticmethod
    def setup_performance_logging(enable: bool = True):
        """设置性能日志记录
        
        Args:
            enable: 是否启用性能日志
        """
        if not enable:
            return
        
        logger = LoggingUtils.get_logger("performance")
        
        def log_memory_usage():
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                logger.debug(f"Memory usage: {memory_mb:.2f} MB")
            except ImportError:
                logger.debug("psutil not available for memory monitoring")
            except Exception as e:
                logger.debug(f"Failed to log memory usage: {e}")
        
        # 可以定期调用 log_memory_usage()
        return log_memory_usage

    @staticmethod
    def create_operation_context(operation_name: str) -> 'OperationContext':
        """创建操作上下文，用于记录操作的开始和结束
        
        Args:
            operation_name: 操作名称
            
        Returns:
            操作上下文管理器
        """
        return OperationContext(operation_name)

    @staticmethod
    def export_logs(export_dir: str, logger_names: Optional[list] = None) -> bool:
        """导出日志文件
        
        Args:
            export_dir: 导出目录
            logger_names: 要导出的日志器名称列表，如果为None则导出所有
            
        Returns:
            导出是否成功
        """
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            # 获取所有处理器的文件路径
            file_handlers = []
            for logger_name, logger in LoggingUtils._loggers.items():
                if logger_names and logger_name not in logger_names:
                    continue
                    
                for handler in logger.handlers:
                    if isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
                        file_handlers.append(handler.baseFilename)
            
            # 复制日志文件
            import shutil
            for file_path in file_handlers:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(export_dir, filename)
                    shutil.copy2(file_path, dest_path)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to export logs: {e}")
            return False


class OperationContext:
    """操作上下文管理器，用于记录操作的开始和结束时间"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.logger = LoggingUtils.get_logger("operations")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed operation: {self.operation_name} (Duration: {duration:.2f}s)")
        else:
            self.logger.error(f"Failed operation: {self.operation_name} (Duration: {duration:.2f}s, Error: {exc_val})")
        
        return False  # 不抑制异常
