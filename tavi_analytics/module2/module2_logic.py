"""
模块二业务逻辑类
负责全自动分析的核心业务逻辑
"""

import logging
import os
import tempfile
import requests
import time
import json
from typing import Optional, List, Tuple, Dict
import qt
import slicer
import vtk
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from .alg_client import DCMProcessor
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from module2.alg_client import DCMProcessor


class Module2Logic(ScriptedLoadableModuleLogic):
    """
    模块二业务逻辑类
    
    负责处理全自动分析相关的所有业务逻辑，包括：
    - 全自动主动脉根部分析
    - 远程分析服务器通信
    - 分析结果导入和管理
    """

    def __init__(self) -> None:
        """初始化模块二逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)
        self.session = TAVRStudySession()
        
        # 全自动分析相关
        self.dcm_processor = DCMProcessor()
        self.current_task_id = None
        self.analysis_temp_dir = None
        
        # 异步分析状态管理
        self.analysis_state = 'idle'  # 当前分析状态
        self.analysis_error = None    # 错误信息
        self.analysis_progress = 0    # 进度百分比
        
        logging.info("Module2Logic 初始化完成 - 全自动分析模式")

    def initialize_segmentation(self) -> bool:
        """
        初始化分割环境
        
        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        try:
            # 这里将来会添加具体的分割初始化逻辑
            logging.info("分割环境初始化完成")
            return True
        except Exception as e:
            logging.error(f"分割环境初始化失败: {e}")
            return False

    def create_aortic_root_segmentation(self) -> Optional[object]:
        """
        创建主动脉根部分割
        
        Returns:
            分割节点，创建失败返回None
        """
        try:
            # 占位实现，将来会添加具体的分割逻辑
            logging.info("主动脉根部分割创建完成")
            return None
        except Exception as e:
            logging.error(f"创建主动脉根部分割失败: {e}")
            return None

    def validate_segmentation_results(self) -> bool:
        """
        验证分割结果
        
        Returns:
            bool: 验证通过返回True，失败返回False
        """
        try:
            # 占位实现，将来会添加具体的验证逻辑
            logging.info("分割结果验证完成")
            return True
        except Exception as e:
            logging.error(f"分割结果验证失败: {e}")
            return False

    def get_segmentation_progress(self) -> dict:
        """
        获取分割进度信息
        
        Returns:
            dict: 包含分割进度信息的字典
        """
        # 占位实现，将来会添加具体的进度跟踪逻辑
        return {
            'aortic_root_completed': False,
            'valve_stent_completed': False,
            'overall_progress': 0.0
        }

    def reset_segmentation_data(self) -> None:
        """重置分割数据"""
        try:
            # 占位实现，将来会添加具体的重置逻辑
            logging.info("分割数据已重置")
        except Exception as e:
            logging.error(f"重置分割数据失败: {e}")

    # ====== 全自动分析相关方法 ======
    
    def start_auto_analysis(self) -> bool:
        """
        启动全自动分析流程（非阻塞版本）
        
        使用状态机模式和QTimer来避免UI阻塞：
        1. 立即返回，开始异步处理流程
        2. 使用QTimer分步骤执行耗时操作
        3. 通过回调函数更新进度状态
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        try:
            logging.info("开始启动全自动分析流程（非阻塞模式）")
            
            # 重置状态
            self.analysis_state = 'initializing'
            self.analysis_error = None
            self.analysis_progress = 0
            
            # 创建异步处理定时器
            if not hasattr(self, 'async_analysis_timer'):
                self.async_analysis_timer = qt.QTimer()
                self.async_analysis_timer.setSingleShot(True)
                self.async_analysis_timer.timeout.connect(self._process_analysis_step)
            
            # 启动第一步：检查服务器连接
            self.analysis_state = 'checking_connection'
            self.async_analysis_timer.start(100)  # 100ms后开始处理
            
            return True
                
        except Exception as e:
            logging.error(f"启动全自动分析失败: {e}")
            self.analysis_error = str(e)
            return False

    def _process_analysis_step(self):
        """
        处理分析步骤（状态机模式）
        
        根据当前状态执行相应的步骤，每个步骤完成后安排下一步
        """
        try:
            if self.analysis_state == 'checking_connection':
                self._step_check_connection()
            elif self.analysis_state == 'checking_connection_result':
                self._check_connection_result()
            elif self.analysis_state == 'getting_volume':
                self._step_get_volume()
            elif self.analysis_state == 'saving_nrrd':
                self._step_save_nrrd()
            elif self.analysis_state == 'saving_nrrd_result':
                self._check_save_result()
            elif self.analysis_state == 'uploading_file':
                self._step_upload_file()
            elif self.analysis_state == 'uploading_file_result':
                self._check_upload_result()
            elif self.analysis_state == 'completed':
                logging.info("全自动分析启动流程完成")
            elif self.analysis_state == 'failed':
                logging.error(f"全自动分析失败: {self.analysis_error}")
            
        except Exception as e:
            logging.error(f"处理分析步骤失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = str(e)

    def _check_connection_result(self):
        """检查连接测试结果"""
        try:
            if hasattr(self, 'connection_future'):
                if self.connection_future.done():
                    # 连接测试完成
                    result = self.connection_future.result()
                    if result:
                        logging.info("服务器连接正常，进入下一步")
                        self.analysis_state = 'getting_volume'
                        self.async_analysis_timer.start(100)
                    else:
                        self.analysis_state = 'failed'
                        self.analysis_error = "无法连接到分析服务器"
                else:
                    # 还在检查中，继续等待
                    self.async_analysis_timer.start(500)
        except Exception as e:
            logging.error(f"检查连接结果失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"连接检查失败: {str(e)}"

    def _check_save_result(self):
        """检查保存nrrd文件的结果"""
        try:
            if hasattr(self, 'save_future'):
                if self.save_future.done():
                    # 保存完成
                    result = self.save_future.result()
                    if result:
                        logging.info("nrrd文件保存成功，进入上传步骤")
                        self.analysis_state = 'uploading_file'
                        self.async_analysis_timer.start(100)
                    else:
                        self.analysis_state = 'failed'
                        self.analysis_error = "保存nrrd文件失败"
                else:
                    # 还在保存中，继续等待，更新进度
                    progress = min(40 + (time.time() - getattr(self, 'save_start_time', time.time())) * 2, 55)
                    self.analysis_progress = int(progress)
                    self.async_analysis_timer.start(1000)
        except Exception as e:
            logging.error(f"检查保存结果失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"保存检查失败: {str(e)}"

    def _check_upload_result(self):
        """检查上传文件的结果"""
        try:
            if hasattr(self, 'upload_future'):
                if self.upload_future.done():
                    # 上传完成
                    try:
                        task_id = self.upload_future.result()
                        if task_id:
                            self.current_task_id = task_id
                            logging.info(f"文件上传成功，任务ID: {task_id}")
                            self.analysis_progress = 100
                            self.analysis_state = 'completed'
                        else:
                            self.analysis_state = 'failed'
                            self.analysis_error = "文件上传失败，未获得任务ID"
                    except Exception as e:
                        self.analysis_state = 'failed'
                        self.analysis_error = f"上传失败: {str(e)}"
                else:
                    # 还在上传中，继续等待，更新进度
                    progress = min(60 + (time.time() - getattr(self, 'upload_start_time', time.time())) * 3, 95)
                    self.analysis_progress = int(progress)
                    self.async_analysis_timer.start(2000)
        except Exception as e:
            logging.error(f"检查上传结果失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"上传检查失败: {str(e)}"

    def _step_check_connection(self):
        """步骤1: 检查服务器连接"""
        try:
            logging.info("步骤1: 检查服务器连接...")
            self.analysis_progress = 10
            
            # 使用线程池进行连接测试，避免阻塞
            import concurrent.futures
            
            def check_connection():
                return self.test_analysis_connection()
            
            # 创建线程池执行器
            if not hasattr(self, 'thread_executor'):
                self.thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            
            # 提交连接测试任务
            future = self.thread_executor.submit(check_connection)
            
            # 启动定时器检查连接结果
            self.connection_future = future
            self.async_analysis_timer.start(500)  # 500ms后检查结果
            self.analysis_state = 'checking_connection_result'
            
        except Exception as e:
            logging.error(f"检查服务器连接步骤失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"服务器连接检查失败: {str(e)}"

    def _step_get_volume(self):
        """步骤2: 获取当前体积数据"""
        try:
            logging.info("步骤2: 获取当前体积数据...")
            self.analysis_progress = 20
            
            # 获取当前体积数据（这个操作通常很快）
            volume_node = self._get_current_volume_node()
            if not volume_node:
                self.analysis_state = 'failed'
                self.analysis_error = "未找到当前体积数据"
                return
            
            self.current_volume_node = volume_node
            
            # 创建临时目录
            self.analysis_temp_dir = tempfile.mkdtemp(prefix="tavi_analysis_")
            self.temp_nrrd_path = os.path.join(self.analysis_temp_dir, "current_volume.nrrd")
            
            # 安排下一步
            self.analysis_state = 'saving_nrrd'
            self.async_analysis_timer.start(100)
            
        except Exception as e:
            logging.error(f"获取体积数据步骤失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"获取体积数据失败: {str(e)}"

    def _step_save_nrrd(self):
        """步骤3: 保存nrrd文件（异步）"""
        try:
            logging.info("步骤3: 保存nrrd文件...")
            self.analysis_progress = 40
            self.save_start_time = time.time()  # 记录开始时间
            
            # 使用线程池进行文件保存，避免阻塞UI
            def save_nrrd():
                return self._save_volume_to_nrrd(self.current_volume_node, self.temp_nrrd_path)
            
            # 提交保存任务
            future = self.thread_executor.submit(save_nrrd)
            
            # 启动定时器检查保存结果
            self.save_future = future
            self.async_analysis_timer.start(1000)  # 1秒后检查结果
            self.analysis_state = 'saving_nrrd_result'
            
        except Exception as e:
            logging.error(f"保存nrrd文件步骤失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"保存nrrd文件失败: {str(e)}"

    def _step_upload_file(self):
        """步骤4: 上传文件（异步）"""
        try:
            logging.info("步骤4: 上传文件到服务器...")
            self.analysis_progress = 60
            self.upload_start_time = time.time()  # 记录开始时间
            
            # 使用线程池进行文件上传，避免阻塞UI
            def upload_file():
                return self.dcm_processor.upload_file(self.temp_nrrd_path)
            
            # 提交上传任务
            future = self.thread_executor.submit(upload_file)
            
            # 启动定时器检查上传结果
            self.upload_future = future
            self.async_analysis_timer.start(2000)  # 2秒后检查结果
            self.analysis_state = 'uploading_file_result'
            
        except Exception as e:
            logging.error(f"上传文件步骤失败: {e}")
            self.analysis_state = 'failed'
            self.analysis_error = f"上传文件失败: {str(e)}"

    def stop_auto_analysis(self) -> bool:
        """
        停止全自动分析
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            # 停止异步处理定时器
            if hasattr(self, 'async_analysis_timer') and self.async_analysis_timer:
                self.async_analysis_timer.stop()
            
            # 关闭线程池执行器
            if hasattr(self, 'thread_executor'):
                self.thread_executor.shutdown(wait=False)
                delattr(self, 'thread_executor')
            
            # 重置任务ID和状态
            self.current_task_id = None
            self.analysis_state = 'stopped'
            self.analysis_error = None
            self.analysis_progress = 0
            
            # 清理临时文件
            self._cleanup_temp_files()
            
            logging.info("全自动分析已停止")
            return True
            
        except Exception as e:
            logging.error(f"停止全自动分析失败: {e}")
            return False

    def get_analysis_status(self) -> Optional[Dict]:
        """
        获取分析状态
        
        Returns:
            Dict: 包含状态信息的字典，失败返回None
        """
        try:
            # 检查是否有正在进行的启动流程
            if hasattr(self, 'analysis_state'):
                if self.analysis_state == 'failed':
                    return {
                        'status': 'failed',
                        'progress': 0,
                        'message': '启动失败',
                        'error': self.analysis_error or '未知错误'
                    }
                elif self.analysis_state == 'completed':
                    # 启动流程完成，检查远程任务状态
                    if self.current_task_id:
                        # 查询远程服务器的任务状态
                        status = self.dcm_processor.check_status(self.current_task_id)
                        
                        # 转换为标准化状态格式
                        if status == 'completed':
                            return {
                                'status': 'completed',
                                'progress': 100,
                                'message': '分析已完成'
                            }
                        elif status == 'failed':
                            return {
                                'status': 'failed',
                                'progress': 0,
                                'message': '分析失败',
                                'error': '远程服务器分析失败'
                            }
                        elif status in ['processing', 'running']:
                            return {
                                'status': 'processing',
                                'progress': 50,  # 假设50%进度
                                'message': '正在进行分析'
                            }
                        else:
                            return {
                                'status': 'processing',
                                'progress': 25,
                                'message': f'任务状态: {status}'
                            }
                    else:
                        return {
                            'status': 'failed',
                            'progress': 0,
                            'error': '任务ID丢失'
                        }
                else:
                    # 启动流程进行中
                    progress = getattr(self, 'analysis_progress', 0)
                    state_messages = {
                        'initializing': '正在初始化...',
                        'checking_connection': '正在检查服务器连接...',
                        'checking_connection_result': '正在检查连接结果...',
                        'getting_volume': '正在获取体积数据...',
                        'saving_nrrd': '正在保存nrrd文件...',
                        'saving_nrrd_result': '正在保存文件...',
                        'uploading_file': '正在上传文件...',
                        'uploading_file_result': '正在上传到服务器...'
                    }
                    
                    message = state_messages.get(self.analysis_state, f'正在处理: {self.analysis_state}')
                    
                    return {
                        'status': 'uploading' if 'upload' in self.analysis_state else 'processing',
                        'progress': progress,
                        'message': message
                    }
            
            # 如果没有启动流程状态，但有任务ID，检查远程状态
            if self.current_task_id:
                # 查询远程服务器的任务状态
                status = self.dcm_processor.check_status(self.current_task_id)
                
                # 转换为标准化状态格式
                if status == 'completed':
                    return {
                        'status': 'completed',
                        'progress': 100,
                        'message': '分析已完成'
                    }
                elif status == 'failed':
                    return {
                        'status': 'failed',
                        'progress': 0,
                        'message': '分析失败',
                        'error': '远程服务器分析失败'
                    }
                elif status in ['processing', 'running']:
                    return {
                        'status': 'processing',
                        'progress': 50,  # 假设50%进度
                        'message': '正在进行分析'
                    }
                else:
                    return {
                        'status': 'processing',
                        'progress': 25,
                        'message': f'任务状态: {status}'
                    }
            
            # 没有活动的分析任务
            return None
                
        except Exception as e:
            logging.error(f"获取分析状态失败: {e}")
            return {
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            }

    def import_analysis_results(self) -> Optional[Dict]:
        """
        导入分析结果
        
        下载分割文件和测量数据，并导入到Slicer中
        
        Returns:
            Dict: 包含导入结果信息的字典，失败返回None
        """
        try:
            if not self.current_task_id:
                logging.error("没有有效的任务ID")
                return None
            
            logging.info("开始导入分析结果")
            
            # 创建结果存储目录
            results_dir = os.path.join(self.analysis_temp_dir, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # 下载分割结果
            segmentation_path = os.path.join(results_dir, "segment_result.nrrd")
            measurement_path = os.path.join(results_dir, "measurement.json")
            
            imported_files = []
            
            try:
                # 下载分割文件
                self.dcm_processor.download_segmentation_result(
                    self.current_task_id, 
                    segmentation_path
                )
                
                if os.path.exists(segmentation_path):
                    # 导入分割文件到Slicer
                    seg_node = self._import_segmentation_file(segmentation_path)
                    if seg_node:
                        imported_files.append("分割结果")
                        logging.info("分割结果导入成功")
                    
            except Exception as e:
                logging.warning(f"下载/导入分割文件失败: {e}")
            
            curves_count = 0
            try:
                # 下载测量数据
                self.dcm_processor.download_measurement_result(
                    self.current_task_id,
                    measurement_path
                )
                
                if os.path.exists(measurement_path):
                    # 导入测量数据（使用模块三的逻辑）
                    curves_count = self._import_measurement_data(measurement_path)
                    if curves_count > 0:
                        imported_files.append("测量数据")
                        logging.info(f"测量数据导入成功，创建了 {curves_count} 条曲线")
                    
            except Exception as e:
                logging.warning(f"下载/导入测量数据失败: {e}")
            
            # 清理任务
            self.current_task_id = None
            
            return {
                'imported_files': imported_files,
                'curves_count': curves_count,
                'segmentation_imported': "分割结果" in imported_files,
                'measurement_imported': "测量数据" in imported_files
            }
            
        except Exception as e:
            logging.error(f"导入分析结果失败: {e}")
            return None

    def _get_current_volume_node(self):
        """
        获取当前的体积节点
        
        对于4D CT序列数据，获取序列浏览器当前显示的体积节点
        
        Returns:
            vtkMRMLScalarVolumeNode: 当前体积节点，失败返回None
        """
        try:
            # 获取序列节点和序列浏览器节点
            sequence_node = self.session.get_volume_sequence_node()
            browser_node = self.session.get_sequence_browser_node()
            
            if browser_node and sequence_node:
                # 从序列浏览器获取当前显示的体积节点代理
                # 这是4D CT序列中当前时间点的体积
                proxy_node = browser_node.GetProxyNode(sequence_node)
                if proxy_node and proxy_node.IsA("vtkMRMLScalarVolumeNode"):
                    logging.info(f"从序列浏览器获取到当前体积节点: {proxy_node.GetName()}")
                    return proxy_node
            
            # 如果代理方法失败，尝试直接从序列节点获取当前数据项
            if sequence_node and browser_node:
                # 获取当前选中的数据项索引
                current_index = browser_node.GetSelectedItemNumber()
                if current_index >= 0 and current_index < sequence_node.GetNumberOfDataNodes():
                    # 从序列节点获取指定索引的数据
                    data_node = sequence_node.GetNthDataNode(current_index)
                    if data_node and data_node.IsA("vtkMRMLScalarVolumeNode"):
                        logging.info(f"从序列节点获取到体积数据: {data_node.GetName()}")
                        return data_node
            
            # 如果序列方法都失败，尝试获取当前活动的体积节点
            selection_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
            if selection_node:
                active_volume_id = selection_node.GetActiveVolumeID()
                if active_volume_id:
                    volume_node = slicer.mrmlScene.GetNodeByID(active_volume_id)
                    if volume_node:
                        logging.info(f"从活动节点获取到体积数据: {volume_node.GetName()}")
                        return volume_node
            
            # 最后尝试获取场景中的第一个体积节点
            volume_nodes = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
            if volume_nodes:
                volume_node = volume_nodes[0]
                logging.info(f"使用场景中第一个体积节点: {volume_node.GetName()}")
                return volume_node
            
            logging.error("未找到任何体积节点")
            return None
            
        except Exception as e:
            logging.error(f"获取当前体积节点失败: {e}")
            return None

    def _save_volume_to_nrrd(self, volume_node, file_path: str) -> bool:
        """
        将体积节点保存为nrrd文件
        
        Args:
            volume_node: 体积节点
            file_path: 保存路径
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            if not volume_node:
                logging.error("体积节点为空")
                return False
            
            # 使用Slicer的保存功能
            success = slicer.util.saveNode(volume_node, file_path)
            
            if success and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logging.info(f"体积数据已保存到: {file_path} (大小: {file_size / 1024 / 1024:.1f} MB)")
                return True
            else:
                logging.error("保存体积数据失败")
                return False
                
        except Exception as e:
            logging.error(f"保存体积数据到nrrd失败: {e}")
            return False

    def _import_segmentation_file(self, file_path: str):
        """
        导入分割文件到Slicer
        
        Args:
            file_path: 分割文件路径
            
        Returns:
            导入的分割节点，失败返回None
        """
        try:
            if not os.path.exists(file_path):
                logging.error(f"分割文件不存在: {file_path}")
                return None
            
            # 加载分割文件作为分割节点
            try:
                # 方法1: 直接使用loadSegmentation加载
                seg_node = slicer.util.loadSegmentation(file_path)
                if seg_node:
                    seg_node.SetName("自动分析分割结果")
                    num_segments = seg_node.GetSegmentation().GetNumberOfSegments()
                    logging.info(f"分割文件已导入为分割节点，包含 {num_segments} 个分段")
                    
                    # 将分割节点存储到会话中
                    self.session.set_segmentation_node(seg_node)
                    
                    # 设置分段显示属性
                    self._configure_segmentation_display(seg_node)
                    
                    return seg_node
                else:
                    raise Exception("loadSegmentation返回None")
                    
            except Exception as e1:
                logging.warning(f"直接加载分割失败: {e1}，尝试体积转换方法")
                
                # 方法2: 先加载为体积，再转换为分割（回退方案）
                volume_node = slicer.util.loadVolume(file_path)
                if volume_node:
                    # 创建分割节点
                    seg_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
                    seg_node.SetName("自动分析分割结果")
                    
                    # 将体积转换为分割
                    segmentations_logic = slicer.modules.segmentations.logic()
                    segmentations_logic.ImportLabelmapToSegmentationNode(volume_node, seg_node)
                    
                    # 清理临时体积节点
                    slicer.mrmlScene.RemoveNode(volume_node)
                    
                    num_segments = seg_node.GetSegmentation().GetNumberOfSegments()
                    logging.info(f"通过体积转换成功导入分割节点，包含 {num_segments} 个分段")
                    
                    # 将分割节点存储到会话中
                    self.session.set_segmentation_node(seg_node)
                    
                    # 设置分段显示属性
                    self._configure_segmentation_display(seg_node)
                    
                    return seg_node
                else:
                    logging.error("体积加载也失败")
                    return None
                
        except Exception as e:
            logging.error(f"导入分割文件失败: {e}")
            return None

    def _configure_segmentation_display(self, seg_node):
        """
        配置分割节点的显示属性
        
        Args:
            seg_node: 分割节点
        """
        try:
            segmentation = seg_node.GetSegmentation()
            
            # 心脏解剖结构的常见分段名称映射
            # 根据常见的心脏CT分割标签进行映射
            segment_names = {
                1: "主动脉根部",
                2: "左心室心肌", 
                5: "主动脉瓣环",
                6: "冠状动脉",
                7: "心房",
                12: "其他心脏结构"
            }
            
            # 为每个分段设置有意义的名称
            for i in range(segmentation.GetNumberOfSegments()):
                segment = segmentation.GetNthSegment(i)
                original_name = segment.GetName()
                
                # 尝试从原始名称中提取分段编号
                try:
                    if "Segment_" in original_name:
                        segment_id = int(original_name.replace("Segment_", ""))
                        if segment_id in segment_names:
                            new_name = segment_names[segment_id]
                            segment.SetName(new_name)
                            logging.info(f"分段重命名: {original_name} -> {new_name}")
                        else:
                            # 如果没有预定义名称，使用通用名称
                            segment.SetName(f"心脏结构_{segment_id}")
                except ValueError:
                    # 如果无法解析分段编号，保持原名称
                    pass
            
            # 设置分割显示属性
            display_node = seg_node.GetDisplayNode()
            if display_node:
                # 设置为3D显示
                display_node.SetVisibility3D(True)
                # 设置透明度
                display_node.SetOpacity3D(0.6)
                # 设置2D显示
                display_node.SetVisibility2DFill(True)
                display_node.SetOpacity2DFill(0.4)
                display_node.SetVisibility2DOutline(True)
                
                logging.info("分割显示属性已配置")
            
        except Exception as e:
            logging.warning(f"配置分割显示属性失败: {e}")

    def _import_measurement_data(self, json_path: str) -> int:
        """
        导入测量数据到Slicer（参考模块三的实现）
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            int: 创建的曲线数量
        """
        try:
            if not os.path.exists(json_path):
                logging.error(f"测量数据文件不存在: {json_path}")
                return 0
            
            # 使用类似模块三的逻辑加载JSON数据
            try:
                from ..module3.services.json_loader import JSONCurveLoader
                from ..module3.services.slicer_curve_service import SlicerCurveService
            except ImportError:
                # 回退导入方式
                import sys
                module3_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'module3')
                if module3_path not in sys.path:
                    sys.path.insert(0, module3_path)
                
                from services.json_loader import JSONCurveLoader
                from services.slicer_curve_service import SlicerCurveService
            
            json_loader = JSONCurveLoader()
            slicer_curve = SlicerCurveService()
            
            # 解析JSON文件
            plane_fields = json_loader.load(json_path)
            
            # 清理现有的plane节点（可选）
            cleared = slicer_curve.clear_plane_nodes()
            if cleared > 0:
                logging.info(f"清理了 {cleared} 个现有plane节点")
            
            # 创建曲线
            result = slicer_curve.create_closed_curves(plane_fields)
            curves_count = result.get('created_count', 0)
            
            if curves_count > 0:
                logging.info(f"测量数据导入成功，创建了 {curves_count} 条曲线")
            
            return curves_count
            
        except Exception as e:
            logging.error(f"导入测量数据失败: {e}")
            return 0

    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if self.analysis_temp_dir and os.path.exists(self.analysis_temp_dir):
                import shutil
                shutil.rmtree(self.analysis_temp_dir)
                logging.info(f"已清理临时目录: {self.analysis_temp_dir}")
                self.analysis_temp_dir = None
        except Exception as e:
            logging.error(f"清理临时文件失败: {e}")

    def test_analysis_connection(self) -> bool:
        """
        测试与分析服务器的连接
        
        Returns:
            bool: 连接成功返回True
        """
        try:
            # 测试服务器连接 - 使用upload端点进行连接测试
            import requests
            
            # 发送一个空的POST请求到upload端点来测试连接
            # 预期会返回400错误（没有文件），但这证明服务器在运行
            response = requests.post(f"{self.dcm_processor.base_url}/upload", timeout=10)
            
            if response.status_code == 400:
                # 400错误通常表示"没有文件"，这证明服务器正常运行
                logging.info("分析服务器连接正常")
                return True
            elif response.status_code == 200:
                # 200也是正常的
                logging.info("分析服务器连接正常")
                return True
            else:
                logging.warning(f"分析服务器响应异常: {response.status_code}")
                # 即使是其他状态码，只要能连接上就认为服务器可用
                return True
                
        except requests.exceptions.ConnectTimeout:
            logging.error("连接分析服务器超时")
            return False
        except requests.exceptions.ConnectionError:
            logging.error("无法连接到分析服务器 - 服务器可能未运行")
            return False
        except Exception as e:
            logging.error(f"测试分析服务器连接失败: {e}")
            return False

    def cleanup(self):
        """
        清理资源
        """
        try:
            # 停止分析并清理临时文件
            self.stop_auto_analysis()
            
            logging.info("Module2Logic 清理完成")
            
        except Exception as e:
            logging.error(f"Module2Logic 清理失败: {e}")
