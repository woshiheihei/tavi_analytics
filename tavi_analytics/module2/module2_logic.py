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
        # 兼容字段（旧单任务ID）不再使用，保留避免外部访问报错
        self.current_task_id = None
        self.analysis_temp_dir = None
        # 异步分析状态管理
        self.analysis_state = 'idle'  # 当前分析状态
        self.analysis_error = None    # 错误信息
        self.analysis_progress = 0    # 进度百分比
        # 当前选择的期像状态
        self.selected_phase = 'diastole'  # 默认选择舒张期，可选 'diastole' 或 'systole'（兼容字段，保留用于结果命名，不再由UI控制）
        # 多期像分析状态
        self.phase_order = ['diastole', 'systole']
        self.phases_to_analyze = []   # 实际要分析的期像列表
        self.phase_index = -1         # 当前处理到的期像索引
        # 每个期像的任务信息：{ phase: { 'task_id': str|None, 'nrrd_path': str|None, 'upload_done': bool } }
        self.phase_tasks = {}
        logging.info("Module2Logic 初始化完成 - 全自动分析模式")

    def set_selected_phase(self, phase: str):
        """兼容接口：不再暴露给UI，内部用于结果命名"""
        if phase in ['diastole', 'systole']:
            self.selected_phase = phase
            logging.info(f"设置当前选择期像为: {phase}")

    def get_selected_phase(self) -> str:
        """兼容接口：返回内部期像状态，用于结果命名"""
        return self.selected_phase

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

            # 计算本次需要分析的期像
            self._prepare_phases_to_analyze()
            # 初始化每期像任务记录
            self.phase_tasks = {p: {'task_id': None, 'nrrd_path': None, 'upload_done': False} for p in self.phases_to_analyze}
            self.phase_index = -1

            # 创建根级临时目录（单次分析复用）
            if not self.analysis_temp_dir:
                self.analysis_temp_dir = tempfile.mkdtemp(prefix="tavi_analysis_")
            
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
                        # 开始第一个期像
                        self.phase_index = 0
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
                    # 针对多期像，保存阶段按每期像占用约25%的总进度
                    base = self._current_phase_base_progress()
                    progress = min(base + 15 + (time.time() - getattr(self, 'save_start_time', time.time())) * 2, base + 25)
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
                            # 记录到当前期像
                            current_phase = self._get_current_phase()
                            self.phase_tasks[current_phase]['task_id'] = task_id
                            self.phase_tasks[current_phase]['upload_done'] = True
                            logging.info(f"文件上传成功，期像={current_phase}，任务ID: {task_id}")

                            # 进入下一期像或完成启动流程
                            if self._advance_to_next_phase():
                                # 继续下一期像的导出/上传
                                self.analysis_state = 'getting_volume'
                                self.async_analysis_timer.start(200)
                            else:
                                # 两个期像均已上传完成
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
                    # 每个期像上传阶段约占总进度的25%-50%区间
                    base = self._current_phase_base_progress()
                    progress = min(base + 30 + (time.time() - getattr(self, 'upload_start_time', time.time())) * 3, base + 45)
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
            # 预估进度 - 当前期像阶段起始
            self.analysis_progress = max(self.analysis_progress, int(self._current_phase_base_progress() + 5))

            # 如可用则尝试切换到对应期像
            current_phase = self._get_current_phase()
            self._try_switch_to_phase(current_phase)

            # 获取当前体积数据（通常很快）
            volume_node = self._get_current_volume_node()
            if not volume_node:
                self.analysis_state = 'failed'
                self.analysis_error = "未找到当前体积数据"
                return

            self.current_volume_node = volume_node

            # 以期像命名，以便区分
            phase_suffix = 'End_Diastole' if current_phase == 'diastole' else 'End_Systole'
            self.temp_nrrd_path = os.path.join(self.analysis_temp_dir, f"{phase_suffix}.nrrd")
            # 记录到期像任务
            if current_phase in self.phase_tasks:
                self.phase_tasks[current_phase]['nrrd_path'] = self.temp_nrrd_path

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
            self.analysis_progress = max(self.analysis_progress, int(self._current_phase_base_progress() + 15))
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
            self.analysis_progress = max(self.analysis_progress, int(self._current_phase_base_progress() + 30))
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
                    # 启动流程完成，检查远程任务状态（多期像）
                    if not self.phase_tasks:
                        return {
                            'status': 'failed',
                            'progress': 0,
                            'error': '无有效任务'
                        }

                    total = len(self.phase_tasks)
                    completed = 0
                    failed = 0
                    phase_messages = []
                    for phase, info in self.phase_tasks.items():
                        task_id = info.get('task_id')
                        if not task_id:
                            phase_messages.append(f"{phase}: 无任务ID")
                            continue
                        try:
                            s = self.dcm_processor.check_status(task_id)
                            if s == 'completed':
                                completed += 1
                                phase_messages.append(f"{phase}: 完成")
                            elif s == 'failed':
                                failed += 1
                                phase_messages.append(f"{phase}: 失败")
                            else:
                                phase_messages.append(f"{phase}: {s}")
                        except Exception as e:
                            phase_messages.append(f"{phase}: 状态查询异常 {e}")

                    if failed > 0 and completed + failed == total:
                        return {
                            'status': 'failed',
                            'progress': int(80 + completed/total*20),
                            'message': '部分任务失败',
                            'error': '; '.join(phase_messages)
                        }
                    if completed == total:
                        return {
                            'status': 'completed',
                            'progress': 100,
                            'message': '两期像分析均已完成'
                        }
                    # 仍在处理中
                    return {
                        'status': 'processing',
                        'progress': int(70 + completed/total*20),
                        'message': '远程分析进行中: ' + ' | '.join(phase_messages)
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
                    
                    current_phase = self._get_current_phase()
                    phase_cn = '舒张末期' if current_phase == 'diastole' else '收缩末期'
                    message = f"[{phase_cn}] " + state_messages.get(self.analysis_state, f'正在处理: {self.analysis_state}')
                    
                    return {
                        'status': 'uploading' if 'upload' in self.analysis_state else 'processing',
                        'progress': progress,
                        'message': message
                    }
            
            # 如果没有启动流程状态，但有任务，检查远程状态（例如应用重启后）
            if self.phase_tasks:
                total = len(self.phase_tasks)
                completed = 0
                failed = 0
                for phase, info in self.phase_tasks.items():
                    task_id = info.get('task_id')
                    if not task_id:
                        continue
                    try:
                        s = self.dcm_processor.check_status(task_id)
                        if s == 'completed':
                            completed += 1
                        elif s == 'failed':
                            failed += 1
                    except Exception:
                        pass
                if completed == total and total > 0:
                    return {'status': 'completed', 'progress': 100, 'message': '两期像分析均已完成'}
                if failed > 0:
                    return {'status': 'failed', 'progress': int(80 + completed/total*20), 'message': '部分任务失败'}
                if total > 0:
                    return {'status': 'processing', 'progress': int(70 + completed/total*20), 'message': '远程分析进行中'}
            
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
            if not self.phase_tasks:
                logging.error("没有可导入的任务")
                return None
            
            logging.info("开始导入分析结果")
            
            # 创建结果存储目录
            results_dir = os.path.join(self.analysis_temp_dir, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            summary = {
                'phases': {},
                'total_curves': 0,
                'total_segmentations': 0
            }
            
            for phase in self.phases_to_analyze:
                info = self.phase_tasks.get(phase, {})
                task_id = info.get('task_id')
                if not task_id:
                    summary['phases'][phase] = {'status': 'no_task'}
                    continue
                phase_dir = os.path.join(results_dir, phase)
                os.makedirs(phase_dir, exist_ok=True)
                seg_path = os.path.join(phase_dir, f"segment_result_{phase}.nrrd")
                meas_path = os.path.join(phase_dir, f"measurement_{phase}.json")

                seg_imported = False
                curves_count = 0

                # 下载并导入分割
                try:
                    self.dcm_processor.download_segmentation_result(task_id, seg_path)
                    if os.path.exists(seg_path):
                        # 为命名正确，临时设置当前期像
                        old_phase = self.selected_phase
                        try:
                            self.selected_phase = 'diastole' if phase == 'diastole' else 'systole'
                            seg_node = self._import_segmentation_file(seg_path)
                            if seg_node:
                                seg_imported = True
                                summary['total_segmentations'] += 1
                                logging.info(f"[{phase}] 分割结果导入成功")
                        finally:
                            self.selected_phase = old_phase
                except Exception as e:
                    logging.warning(f"[{phase}] 下载/导入分割文件失败: {e}")

                # 下载测量数据（将两期像都导入到各自的平面管理器中）
                try:
                    self.dcm_processor.download_measurement_result(task_id, meas_path)
                    if os.path.exists(meas_path):
                        phase_key = 'end_diastole' if phase == 'diastole' else 'end_systole'
                        curves_count = self._import_measurement_data_for_phase(meas_path, phase_key)
                        if curves_count > 0:
                            summary['total_curves'] += curves_count
                            logging.info(f"[{phase}] 测量数据导入成功，创建了 {curves_count} 条曲线")
                except Exception as e:
                    logging.warning(f"[{phase}] 下载/处理测量数据失败: {e}")

                summary['phases'][phase] = {
                    'segmentation_imported': seg_imported,
                    'measurement_path': meas_path if os.path.exists(meas_path) else None,
                    'segmentation_path': seg_path if os.path.exists(seg_path) else None,
                    'curves_count': curves_count
                }

            # 清理旧兼容字段
            self.current_task_id = None
            
            return summary
            
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
                    # 获取当前期像信息并生成英文名称
                    phase_info = self._get_current_phase_info()
                    segmentation_name = f"Auto_Analysis_Segmentation_{phase_info}"
                    seg_node.SetName(segmentation_name)
                    num_segments = seg_node.GetSegmentation().GetNumberOfSegments()
                    logging.info(f"分割文件已导入为分割节点，包含 {num_segments} 个分段")
                    
                    # 使用新的统一注册API将分割节点注册到对应期像
                    node_id = seg_node.GetID()
                    phase_key = self._extract_phase_from_filename(file_path)
                    
                    # 使用新的统一API注册分割节点（自动处理验证和一致性检查）
                    success = self.session.set_phase_segmentation_node(phase_key, node_id)
                    if success:
                        logging.info(f"分割节点已成功注册到期像: {phase_key} -> {seg_node.GetName()} ({node_id})")
                    else:
                        logging.error(f"分割节点注册失败: {phase_key} -> {seg_node.GetName()} ({node_id})")
                    
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
                    # 获取当前期像信息并生成英文名称
                    phase_info = self._get_current_phase_info()
                    segmentation_name = f"Auto_Analysis_Segmentation_{phase_info}"
                    seg_node.SetName(segmentation_name)
                    
                    # 将体积转换为分割
                    segmentations_logic = slicer.modules.segmentations.logic()
                    segmentations_logic.ImportLabelmapToSegmentationNode(volume_node, seg_node)
                    
                    # 清理临时体积节点
                    slicer.mrmlScene.RemoveNode(volume_node)
                    
                    num_segments = seg_node.GetSegmentation().GetNumberOfSegments()
                    logging.info(f"通过体积转换成功导入分割节点，包含 {num_segments} 个分段")
                    
                    # 使用新的统一注册API将分割节点注册到对应期像
                    node_id = seg_node.GetID()
                    phase_key = self._extract_phase_from_filename(file_path)
                    
                    # 使用新的统一API注册分割节点（自动处理验证和一致性检查）
                    success = self.session.set_phase_segmentation_node(phase_key, node_id)
                    if success:
                        logging.info(f"分割节点已成功注册到期像: {phase_key} -> {seg_node.GetName()} ({node_id})")
                    else:
                        logging.error(f"分割节点注册失败: {phase_key} -> {seg_node.GetName()} ({node_id})")
                    
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
            # 根据常见的心脏CT分割标签进行映射，使用英文名称
            segment_names = {
                1: "Aortic_Root",
                2: "Left_Ventricle", 
                5: "Left_Coronary_Artery",
                6: "Right_Coronary_Artery",
                7: "Calcification",
                12: "Valve_Stent"
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
                            # 如果没有预定义名称，使用英文通用名称
                            segment.SetName(f"Cardiac_Structure_{segment_id}")
                except ValueError:
                    # 如果无法解析分段编号，保持原名称
                    pass
            
            # 关键步骤：创建3D闭合表面表示（类似点击"Show 3D"按钮）
            logging.info("创建分割的3D闭合表面表示...")
            try:
                # 方法1：直接创建闭合表面表示
                segmentation.CreateRepresentation("Closed surface")
                logging.info("✓ 成功创建3D闭合表面表示")
            except Exception as e:
                logging.warning(f"创建3D表面失败: {e}")
                # 如果失败，尝试强制重新创建
                try:
                    segmentation.CreateRepresentation("Closed surface", True)  # True表示强制重新创建
                    logging.info("✓ 强制重新创建3D表面成功")
                except Exception as e2:
                    logging.error(f"强制创建3D表面也失败: {e2}")
            
            # 确保有显示节点
            if not seg_node.GetDisplayNode():
                seg_node.CreateDefaultDisplayNodes()
                logging.info("创建了默认显示节点")
            
            # 设置分割显示属性
            display_node = seg_node.GetDisplayNode()
            if display_node:
                # 设置主要可见性为True（需求：在3D窗口中默认显示分割模型）
                display_node.SetVisibility(True)
                # 设置为3D显示
                display_node.SetVisibility3D(True)
                # 设置透明度
                display_node.SetOpacity3D(0.6)
                
                # 关键步骤：为每个分段启用3D可见性
                for i in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(i)
                    segment_name = segmentation.GetSegment(segment_id).GetName()
                    
                    # 启用分段的3D显示
                    display_node.SetSegmentVisibility3D(segment_id, True)
                    display_node.SetSegmentVisibility(segment_id, True)
                    
                    logging.info(f"✓ 启用分段 {segment_name} 的3D显示")
                
                # 设置2D显示（需求：在三个 slice 窗口中不显示分割）
                try:
                    display_node.SetVisibility2DFill(False)
                    display_node.SetOpacity2DFill(0.0)
                    display_node.SetVisibility2DOutline(False)
                except Exception:
                    # 某些版本API差异，忽略
                    pass
                
                # 刷新显示
                display_node.Modified()
                
                logging.info("分割显示属性已配置，3D表面已启用")
            
        except Exception as e:
            logging.warning(f"配置分割显示属性失败: {e}")

    def _import_measurement_data(self, json_path: str) -> int:
        """
        导入测量数据到Slicer（纯领域化平面管理方式）
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            int: 成功加载的关键平面数量
        """
        try:
            if not os.path.exists(json_path):
                logging.error(f"测量数据文件不存在: {json_path}")
                return 0
            
            # 加载原始JSON数据
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                measurement_data = json.load(f)
            
            logging.info(f"成功读取测量数据文件: {json_path}")
            
            # 使用会话的领域化平面管理器加载关键平面
            success = self.session.load_measurement_planes(measurement_data)
            
            if success:
                logging.info("关键轮廓数据已成功加载到会话中")
                
                # 获取详细的加载摘要
                business_summary = self.session.contour_manager.get_business_summary()
                loaded_contours = business_summary['loaded_contours']
                
                # 记录加载的轮廓信息
                loaded_contour_names = [k for k, v in loaded_contours.items() if v and k != 'has_any_critical_contour']
                logging.info(f"已加载的关键轮廓: {loaded_contour_names}")
                
                # 输出详细的业务摘要
                for plane_name, plane_details in business_summary['plane_details'].items():
                    logging.info(f"{plane_name}: {plane_details['description']}")
                    if 'point_count' in plane_details:
                        logging.info(f"  - 点数: {plane_details['point_count']}")
                    if 'area' in plane_details:
                        logging.info(f"  - 面积: {plane_details['area']:.2f}")
                    if 'perimeter' in plane_details:
                        logging.info(f"  - 周长: {plane_details['perimeter']:.2f}")
                    if 'distance_to_zjd' in plane_details:
                        logging.info(f"  - 到参考点距离: {plane_details['distance_to_zjd']:.2f}")
                
                # 创建所有平面的可视化
                visualization_results = self.session.contour_manager.create_all_visualizations()
                successful_visualizations = sum(1 for success in visualization_results.values() if success)
                
                logging.info(f"可视化创建结果: {successful_visualizations}/{len(visualization_results)}个成功")
                
                # 输出测量数据
                measurements = business_summary['measurements']
                for contour_name, contour_measurements in measurements.items():
                    logging.info(f"{contour_name} 测量数据: {contour_measurements}")
                
                # 返回成功加载的关键轮廓数量
                successful_contours = sum(1 for v in loaded_contours.values() if v and isinstance(v, bool))
                return successful_contours
                
            else:
                logging.warning("未能加载任何关键轮廓数据")
                return 0
            
        except Exception as e:
            logging.error(f"导入测量数据失败: {e}")
            return 0

    def _import_measurement_data_for_phase(self, json_path: str, phase_key: str) -> int:
        """导入测量数据到指定期像的平面管理器

        Args:
            json_path: JSON文件路径
            phase_key: 'end_diastole' 或 'end_systole'

        Returns:
            int: 成功加载的关键平面数量
        """
        try:
            if not os.path.exists(json_path):
                logging.error(f"测量数据文件不存在: {json_path}")
                return 0

            with open(json_path, 'r', encoding='utf-8') as f:
                measurement_data = json.load(f)

            logging.info(f"成功读取测量数据文件: {json_path} -> 导入到 {phase_key}")

            # 加载到对应期像
            success = self.session.load_measurement_contours_for_phase(phase_key, measurement_data)
            if not success:
                logging.warning(f"[{phase_key}] 未能加载任何关键轮廓数据")
                return 0

            mgr = self.session.get_phase_contour_manager(phase_key)
            business_summary = mgr.get_business_summary()
            loaded_contours = business_summary['loaded_contours']

            loaded_contour_names = [k for k, v in loaded_contours.items() if v and k != 'has_any_critical_contour']
            logging.info(f"[{phase_key}] 已加载的关键轮廓: {loaded_contour_names}")

            # 创建可视化
            visualization_results = mgr.create_all_visualizations()
            successful_visualizations = sum(1 for s in visualization_results.values() if s)
            logging.info(f"[{phase_key}] 可视化创建结果: {successful_visualizations}/{len(visualization_results)} 个成功")

            # 输出测量数据
            measurements = business_summary['measurements']
            for contour_name, contour_measurements in measurements.items():
                logging.info(f"[{phase_key}] {contour_name} 测量数据: {contour_measurements}")

            successful_contours = sum(1 for v in loaded_contours.values() if v and isinstance(v, bool))
            return successful_contours
        except Exception as e:
            logging.error(f"[{phase_key}] 导入测量数据失败: {e}")
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

    def _get_current_phase_info(self) -> str:
        """
        根据用户选择的期像按钮获取期像信息，用于生成分割结果名称
        
        Returns:
            str: 期像信息字符串，"End_Diastole" 或 "End_Systole"
        """
        try:
            # 直接根据当前选择的期像返回对应的英文名称
            if self.selected_phase == 'diastole':
                return "End_Diastole"
            elif self.selected_phase == 'systole':
                return "End_Systole"
            else:
                # 如果状态异常，记录日志并返回默认值
                logging.warning(f"未知的期像状态: {self.selected_phase}")
                return "Unknown_Phase"
            
        except Exception as e:
            logging.error(f"获取期像信息失败: {e}")
            return "Unknown_Phase"

    def _extract_phase_from_filename(self, file_path: str) -> str:
        """
        从文件名中解析期像信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 期像键 ('end_diastole' 或 'end_systole')
        """
        try:
            import os
            filename = os.path.basename(file_path).lower()
            
            # 从文件名中检测期像关键词
            if any(keyword in filename for keyword in ['diastole', '舒张', 'ed', 'end_diastole']):
                return 'end_diastole'
            elif any(keyword in filename for keyword in ['systole', '收缩', 'es', 'end_systole']):
                return 'end_systole'
            else:
                # 如果无法从文件名判断，回退到当前选择的期像
                logging.warning(f"无法从文件名 {filename} 中解析期像信息，使用当前选择的期像")
                return 'end_diastole' if self.selected_phase == 'diastole' else 'end_systole'
                
        except Exception as e:
            logging.error(f"解析文件名期像信息失败: {e}")
            # 出错时回退到当前选择的期像
            return 'end_diastole' if self.selected_phase == 'diastole' else 'end_systole'

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

    # ====== 多期像辅助方法 ======
    def _prepare_phases_to_analyze(self):
        """根据会话标记准备需要分析的期像列表（默认两期像都需要，缺失则跳过）"""
        phases = []
        try:
            ed = self.session.get_marked_phase('end_diastole')
            es = self.session.get_marked_phase('end_systole')
            # 总是分析舒张末期
            if not (ed and ed.get('frame_index') is not None):
                logging.warning("未标记舒张末期，将使用当前帧作为替代进行分析")
            phases.append('diastole')
            # 收缩末期也默认分析，但若未标记则无法自动跳帧
            if not (es and es.get('frame_index') is not None):
                logging.warning("未标记收缩末期，将分析当前帧状态（如未手动切换可能与舒张相同帧）")
            phases.append('systole')
        except Exception as e:
            logging.warning(f"准备期像列表时发生异常: {e}")
            phases = ['diastole']
        self.phases_to_analyze = phases

    def _get_current_phase(self) -> str:
        """获取当前处理的期像标识"""
        if 0 <= self.phase_index < len(self.phases_to_analyze):
            return self.phases_to_analyze[self.phase_index]
        # 默认返回舒张末期
        return 'diastole'

    def _advance_to_next_phase(self) -> bool:
        """推进到下一期像，返回是否还有下一期像需要处理"""
        if self.phase_index < 0:
            self.phase_index = 0
        else:
            self.phase_index += 1
        has_more = self.phase_index < len(self.phases_to_analyze)
        if has_more:
            logging.info(f"准备处理期像: {self._get_current_phase()}")
        return has_more

    def _current_phase_base_progress(self) -> int:
        """根据当前期像返回进度的基线（两期像：0与50）"""
        idx = 0
        if 0 <= self.phase_index < len(self.phases_to_analyze):
            idx = self.phase_index
        return 0 if idx == 0 else 50

    def _try_switch_to_phase(self, phase: str) -> bool:
        """尝试切换序列浏览器到指定期像的帧（若有标记）"""
        try:
            browser = self.session.get_sequence_browser_node()
            if not browser:
                return False
            if phase == 'diastole':
                info = self.session.get_marked_phase('end_diastole')
            else:
                info = self.session.get_marked_phase('end_systole')
            if info and info.get('frame_index') is not None:
                browser.SetSelectedItemNumber(int(info['frame_index']))
                logging.info(f"已切换到{('舒张末期' if phase=='diastole' else '收缩末期')}帧: {info['frame_index']}")
                return True
        except Exception as e:
            logging.warning(f"切换到期像 {phase} 失败: {e}")
        return False
