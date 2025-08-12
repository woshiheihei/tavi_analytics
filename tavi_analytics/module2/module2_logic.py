"""
模块二业务逻辑类
负责全自动分析与解剖标志点定义的核心业务逻辑
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
    
    负责处理全自动分析与解剖标志点定义相关的所有业务逻辑，包括：
    - 全自动主动脉根部分析
    - 远程分析服务器通信
    - 分析结果导入和管理
    - 解剖标志点定义
    """

    def __init__(self) -> None:
        """初始化模块二逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)
        self.session = TAVRStudySession()
        
        # 观察者管理
        self.landmark_observers = {}  # 存储标志点节点的观察者ID
        
        # 全自动分析相关
        self.dcm_processor = DCMProcessor()
        self.current_task_id = None
        self.analysis_temp_dir = None
        
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

    def define_anatomical_landmarks(self) -> bool:
        """
        定义解剖标志点
        
        Returns:
            bool: 定义成功返回True，失败返回False
        """
        try:
            # 占位实现，将来会添加具体的标志点定义逻辑
            logging.info("解剖标志点定义完成")
            return True
        except Exception as e:
            logging.error(f"定义解剖标志点失败: {e}")
            return False

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
            'landmarks_defined': False,
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
        启动全自动分析流程
        
        执行以下步骤：
        1. 检查服务器连接
        2. 获取当前舒张末期的体积数据
        3. 保存为临时nrrd文件
        4. 上传到远程分析服务器
        5. 返回分析启动状态
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        try:
            logging.info("开始启动全自动分析流程")
            
            # 1. 检查服务器连接
            if not self.test_analysis_connection():
                logging.error("无法连接到分析服务器")
                return False
            
            # 2. 获取当前体积数据
            volume_node = self._get_current_volume_node()
            if not volume_node:
                logging.error("未找到当前体积数据")
                return False
            
            # 3. 创建临时目录
            self.analysis_temp_dir = tempfile.mkdtemp(prefix="tavi_analysis_")
            temp_nrrd_path = os.path.join(self.analysis_temp_dir, "current_volume.nrrd")
            
            # 4. 保存当前体积为nrrd文件
            if not self._save_volume_to_nrrd(volume_node, temp_nrrd_path):
                logging.error("保存体积数据失败")
                return False
            
            # 5. 上传文件到远程服务器
            try:
                self.current_task_id = self.dcm_processor.upload_file(temp_nrrd_path)
                if self.current_task_id:
                    logging.info(f"文件上传成功，任务ID: {self.current_task_id}")
                    return True
                else:
                    logging.error("文件上传失败，未获得任务ID")
                    return False
            except Exception as e:
                logging.error(f"上传文件到远程服务器失败: {e}")
                return False
                
        except Exception as e:
            logging.error(f"启动全自动分析失败: {e}")
            return False

    def stop_auto_analysis(self) -> bool:
        """
        停止全自动分析
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            # 重置任务ID
            self.current_task_id = None
            
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
            if not self.current_task_id:
                return None
            
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

    def reconstruct_native_annulus_plane(self) -> bool:
        """
        重建原生主动脉瓣环平面
        
        该方法实现以下功能：
        1. 创建并激活名为 Native_Annulus_Points 的标志点节点
        2. 等待用户放置3个点后，获取这些点的三维坐标
        3. 使用VTK库计算最佳拟合平面
        4. 将计算出的平面对象存储到TAVRStudySession中
        
        Returns:
            bool: 重建成功返回True，失败返回False
        """
        try:
            logging.info("开始重建原生主动脉瓣环平面")
            
            # 1. 创建并激活标志点节点
            landmark_node = self._create_landmark_node("Native_Annulus_Points")
            if not landmark_node:
                logging.error("创建Native_Annulus_Points节点失败")
                return False
            
            # 将节点ID存储到会话中
            self.session.set_landmark_node("Native_Annulus_Points", landmark_node.GetID())
            
            # 添加观察者来监听标志点变化
            self._add_landmark_observer(landmark_node)
            
            # 激活标志点放置模式
            self._activate_landmark_placement(landmark_node)
            
            logging.info("Native_Annulus_Points节点已创建并激活，等待用户放置3个点")
            return True
            
        except Exception as e:
            logging.error(f"重建原生主动脉瓣环平面失败: {e}")
            return False
    
    def _create_landmark_node(self, node_name: str):
        """
        创建标志点节点
        
        Args:
            node_name (str): 节点名称
            
        Returns:
            vtkMRMLMarkupsFiducialNode: 创建的标志点节点
        """
        try:
            # 检查是否已存在同名节点
            existing_node = slicer.mrmlScene.GetFirstNodeByName(node_name)
            if existing_node:
                logging.info(f"节点 {node_name} 已存在，将清除并重新使用")
                existing_node.RemoveAllControlPoints()
                return existing_node
            
            # 创建新的标志点节点
            landmark_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
            landmark_node.SetName(node_name)
            
            # 设置节点属性
            landmark_node.GetDisplayNode().SetTextScale(2.0)  # 设置文本大小
            landmark_node.GetDisplayNode().SetGlyphScale(3.0)  # 设置标志点大小
            
            # 禁用自动平面创建功能
            landmark_node.SetAttribute("Markups.AutoCreatePlane", "false")
            landmark_node.SetAttribute("Markups.PlaneAutoGeneration", "disabled")
            
            # 设置最大控制点数为3，防止放置更多点
            landmark_node.SetMaximumNumberOfControlPoints(3)
            
            logging.info(f"创建标志点节点: {node_name}")
            return landmark_node
            
        except Exception as e:
            logging.error(f"创建标志点节点失败: {e}")
            return None
    
    def _activate_landmark_placement(self, landmark_node):
        """
        激活标志点放置模式（不跳转模块）
        
        Args:
            landmark_node: 标志点节点
        """
        try:
            # 直接设置当前活动节点，无需跳转到markups模块
            selection_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
            if selection_node:
                selection_node.SetActivePlaceNodeID(landmark_node.GetID())
                
            # 激活放置模式
            interaction_node = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interaction_node:
                interaction_node.SetCurrentInteractionMode(interaction_node.Place)
                
            # 设置markups放置模式为持续放置，直到用户取消
            if landmark_node:
                landmark_node.SetAttribute("Markups.PlacementMode", "persistent")
                
            logging.info("标志点放置模式已激活（当前模块内）")
            
        except Exception as e:
            logging.error(f"激活标志点放置模式失败: {e}")
    
    def check_and_compute_plane_if_ready(self, landmark_node_name: str = "Native_Annulus_Points") -> bool:
        """
        检查标志点是否已准备好，如果是则计算平面
        
        Args:
            landmark_node_name (str): 标志点节点名称
            
        Returns:
            bool: 计算成功返回True，失败或未准备好返回False
        """
        try:
            # 获取标志点节点
            landmark_node = self.session.get_landmark_node(landmark_node_name)
            if not landmark_node:
                logging.debug(f"标志点节点 {landmark_node_name} 不存在")
                return False
            
            # 检查是否有3个点
            num_points = landmark_node.GetNumberOfControlPoints()
            if num_points < 3:
                logging.debug(f"标志点数量不足，当前: {num_points}/3")
                return False
            
            # 获取三个点的坐标
            points = []
            for i in range(3):
                coords = [0.0, 0.0, 0.0]
                landmark_node.GetNthControlPointPosition(i, coords)
                points.append(coords)
                logging.info(f"点 {i+1}: ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})")
            
            # 计算最佳拟合平面
            plane_data = self._compute_best_fitting_plane(points)
            if plane_data:
                # 在创建我们的平面之前，删除任何可能自动创建的平面
                self._remove_auto_generated_planes()
                
                # 存储平面到会话中
                self.session.set_reconstructed_plane("native_annulus", plane_data)
                
                # 创建平面的Model可视化
                plane_model = self._create_plane_visualization(plane_data, "Native_Annulus_Plane")
                if plane_model:
                    logging.info("原生主动脉瓣环平面Model已创建")
                else:
                    logging.warning("平面Model创建失败，但数据计算成功")
                
                logging.info("原生主动脉瓣环平面计算并存储成功")
                return True
            else:
                logging.error("平面计算失败")
                return False
                
        except Exception as e:
            logging.error(f"检查和计算平面失败: {e}")
            return False
    
    def _compute_best_fitting_plane(self, points: List[List[float]]) -> Optional[dict]:
        """
        使用VTK计算通过3个点的最佳拟合平面
        
        Args:
            points: 三个点的坐标列表，每个点为[x, y, z]
            
        Returns:
            dict: 包含平面原点和法向量的字典，失败返回None
        """
        try:
            if len(points) < 3:
                logging.error("计算平面需要至少3个点")
                return None
            
            # 创建VTK点集
            vtk_points = vtk.vtkPoints()
            for point in points:
                vtk_points.InsertNextPoint(point[0], point[1], point[2])
            
            # 计算平面
            origin = [0.0, 0.0, 0.0]
            normal = [0.0, 0.0, 0.0]
            
            # 使用VTK的平面拟合算法
            vtk.vtkPlane.ComputeBestFittingPlane(vtk_points, origin, normal)
            
            # 创建平面数据字典
            plane_data = {
                'origin': origin.copy(),
                'normal': normal.copy(),
                'points_used': points.copy()
            }
            
            logging.info(f"计算得到平面 - 原点: ({origin[0]:.2f}, {origin[1]:.2f}, {origin[2]:.2f})")
            logging.info(f"法向量: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})")
            
            return plane_data
            
        except Exception as e:
            logging.error(f"计算最佳拟合平面失败: {e}")
            return None
    
    def _remove_auto_generated_planes(self):
        """
        删除可能由markups自动生成的平面
        
        当放置3个fiducial点时，markups可能会自动创建平面，我们需要删除这些自动平面
        """
        try:
            # 获取场景中所有的markups平面节点
            plane_nodes = slicer.util.getNodesByClass("vtkMRMLMarkupsPlaneNode")
            
            removed_count = 0
            for plane_node in plane_nodes:
                # 检查是否是自动生成的平面（通常名称包含fiducial节点名）
                plane_name = plane_node.GetName()
                
                # 如果平面名称包含"Native_Annulus_Points"但不是我们要创建的"Native_Annulus_Plane"
                if ("Native_Annulus_Points" in plane_name and 
                    plane_name != "Native_Annulus_Plane" and
                    not plane_name.endswith("_Plane")):
                    
                    logging.info(f"删除自动生成的平面: {plane_name}")
                    slicer.mrmlScene.RemoveNode(plane_node)
                    removed_count += 1
                
                # 也删除任何未命名的或默认命名的平面
                elif (plane_name.startswith("P") and len(plane_name) <= 3) or plane_name == "Plane":
                    logging.info(f"删除默认命名的平面: {plane_name}")
                    slicer.mrmlScene.RemoveNode(plane_node)
                    removed_count += 1
            
            if removed_count > 0:
                logging.info(f"删除了 {removed_count} 个自动生成的平面")
            
        except Exception as e:
            logging.error(f"删除自动生成平面失败: {e}")
    
    def _create_plane_visualization(self, plane_data: dict, plane_name: str = "Native_Annulus_Plane"):
        """
        创建平面的Model可视化表示
        
        Args:
            plane_data (dict): 平面数据，包含origin和normal
            plane_name (str): 平面Model名称
            
        Returns:
            vtkMRMLModelNode: 创建的平面Model节点，失败返回None
        """
        try:
            # 检查是否已存在同名平面Model
            existing_plane = slicer.mrmlScene.GetFirstNodeByName(plane_name)
            if existing_plane:
                logging.info(f"平面Model {plane_name} 已存在，将删除并重新创建")
                slicer.mrmlScene.RemoveNode(existing_plane)
            
            origin = plane_data['origin']
            normal = plane_data['normal']
            points_used = plane_data.get('points_used', [])
            
            # 计算平面大小（根据标志点位置动态调整）
            if points_used:
                # 计算标志点的边界框来确定平面大小
                min_coords = [min(p[i] for p in points_used) for i in range(3)]
                max_coords = [max(p[i] for p in points_used) for i in range(3)]
                size = max(max_coords[i] - min_coords[i] for i in range(3)) * 2.0
                size = max(size, 50.0)  # 最小50mm
            else:
                size = 60.0  # 默认60mm
            
            # 创建平面几何体
            plane_poly_data = self._create_plane_polydata(origin, normal, size)
            
            # 创建Model节点
            plane_model = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            plane_model.SetName(plane_name)
            plane_model.SetAndObservePolyData(plane_poly_data)
            
            # 创建并设置显示节点
            display_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
            plane_model.SetAndObserveDisplayNodeID(display_node.GetID())
            
            # 设置显示属性
            display_node.SetColor(0.2, 0.8, 0.3)  # 绿色
            display_node.SetOpacity(0.7)  # 半透明
            display_node.SetBackfaceCulling(False)  # 双面显示
            display_node.SetSliceIntersectionVisibility(True)  # 在切片视图中显示
            display_node.SetVisibility(True)
            
            # 设置表面属性
            display_node.SetRepresentation(display_node.SurfaceRepresentation)
            display_node.SetLighting(True)
            display_node.SetInterpolation(display_node.GouraudInterpolation)
            
            # 设置边缘显示
            display_node.SetEdgeVisibility(True)
            display_node.SetEdgeColor(0.1, 0.6, 0.2)  # 深绿色边缘
            
            # 设置Model属性
            plane_model.SetAttribute("Description", f"原生瓣环平面 - 原点: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})")
            plane_model.SetAttribute("PlaneType", "NativeAnnulus")
            plane_model.SetAttribute("CreatedBy", "TAVIAnalytics")
            plane_model.SetAttribute("PlaneSize", str(size))
            
            # 存储平面数据到Model属性中，以便后续更新
            plane_model.SetAttribute("PlaneOriginX", str(origin[0]))
            plane_model.SetAttribute("PlaneOriginY", str(origin[1]))
            plane_model.SetAttribute("PlaneOriginZ", str(origin[2]))
            plane_model.SetAttribute("PlaneNormalX", str(normal[0]))
            plane_model.SetAttribute("PlaneNormalY", str(normal[1]))
            plane_model.SetAttribute("PlaneNormalZ", str(normal[2]))
            
            # 存储平面节点ID到会话
            self.session.set_landmark_node("Native_Annulus_Plane_Model", plane_model.GetID())
            
            logging.info(f"成功创建平面Model: {plane_name}")
            logging.info(f"平面大小: {size:.1f}mm, 位置: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})")
            logging.info(f"平面法向量: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})")
            
            return plane_model
            
        except Exception as e:
            logging.error(f"创建平面Model失败: {e}")
            return None
    
    def _create_plane_polydata(self, origin, normal, size):
        """
        创建平面的PolyData几何体
        
        Args:
            origin: 平面原点 [x, y, z]
            normal: 平面法向量 [nx, ny, nz]
            size: 平面大小（边长）
            
        Returns:
            vtkPolyData: 平面几何体
        """
        import vtk
        import numpy as np
        
        # 规范化法向量
        normal = np.array(normal)
        normal = normal / np.linalg.norm(normal)
        
        # 创建两个正交的切向量
        # 首先找一个不平行于法向量的向量
        if abs(normal[0]) < 0.9:
            temp = np.array([1.0, 0.0, 0.0])
        else:
            temp = np.array([0.0, 1.0, 0.0])
        
        # 使用叉积计算第一个切向量
        tangent1 = np.cross(normal, temp)
        tangent1 = tangent1 / np.linalg.norm(tangent1)
        
        # 计算第二个切向量
        tangent2 = np.cross(normal, tangent1)
        tangent2 = tangent2 / np.linalg.norm(tangent2)
        
        # 计算平面四个顶点
        half_size = size / 2.0
        origin = np.array(origin)
        
        vertices = [
            origin - half_size * tangent1 - half_size * tangent2,  # 左下
            origin + half_size * tangent1 - half_size * tangent2,  # 右下
            origin + half_size * tangent1 + half_size * tangent2,  # 右上
            origin - half_size * tangent1 + half_size * tangent2   # 左上
        ]
        
        # 创建VTK点集
        points = vtk.vtkPoints()
        for vertex in vertices:
            points.InsertNextPoint(vertex[0], vertex[1], vertex[2])
        
        # 创建多边形（四边形）
        quad = vtk.vtkQuad()
        quad.GetPointIds().SetId(0, 0)
        quad.GetPointIds().SetId(1, 1)
        quad.GetPointIds().SetId(2, 2)
        quad.GetPointIds().SetId(3, 3)
        
        # 创建多边形数组
        polys = vtk.vtkCellArray()
        polys.InsertNextCell(quad)
        
        # 创建PolyData
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(polys)
        
        # 计算法向量
        normals = vtk.vtkFloatArray()
        normals.SetNumberOfComponents(3)
        normals.SetNumberOfTuples(4)
        for i in range(4):
            normals.SetTuple3(i, normal[0], normal[1], normal[2])
        
        polydata.GetPointData().SetNormals(normals)
        
        return polydata
    
    def _add_landmark_observer(self, landmark_node):
        """
        为标志点节点添加观察者，监听点的变化
        
        Args:
            landmark_node: 标志点节点
        """
        try:
            if not landmark_node:
                return
                
            node_id = landmark_node.GetID()
            
            # 如果已经有观察者，先移除
            if node_id in self.landmark_observers:
                self._remove_landmark_observer(landmark_node)
            
            # 添加观察者监听点的修改事件
            observer_id = landmark_node.AddObserver(
                landmark_node.PointModifiedEvent, 
                self._on_landmark_point_modified
            )
            
            # 添加观察者监听点的添加/删除事件
            observer_id2 = landmark_node.AddObserver(
                landmark_node.PointAddedEvent,
                self._on_landmark_point_added
            )
            
            observer_id3 = landmark_node.AddObserver(
                landmark_node.PointRemovedEvent,
                self._on_landmark_point_removed
            )
            
            # 存储观察者ID
            self.landmark_observers[node_id] = [observer_id, observer_id2, observer_id3]
            
            logging.info(f"已为标志点节点 {landmark_node.GetName()} 添加观察者")
            
        except Exception as e:
            logging.error(f"添加标志点观察者失败: {e}")
    
    def _remove_landmark_observer(self, landmark_node):
        """
        移除标志点节点的观察者
        
        Args:
            landmark_node: 标志点节点
        """
        try:
            if not landmark_node:
                return
                
            node_id = landmark_node.GetID()
            
            if node_id in self.landmark_observers:
                # 移除所有观察者
                for observer_id in self.landmark_observers[node_id]:
                    landmark_node.RemoveObserver(observer_id)
                
                del self.landmark_observers[node_id]
                logging.info(f"已移除标志点节点 {landmark_node.GetName()} 的观察者")
                
        except Exception as e:
            logging.error(f"移除标志点观察者失败: {e}")
    
    def _on_landmark_point_modified(self, caller, event):
        """
        标志点被修改时的回调函数
        
        Args:
            caller: 调用者（标志点节点）
            event: 事件类型
        """
        try:
            landmark_node = caller
            if landmark_node:
                node_name = landmark_node.GetName()
                num_points = landmark_node.GetNumberOfControlPoints()
                
                if node_name == "Native_Annulus_Points":
                    logging.info(f"检测到瓣环标志点修改，当前点数: {num_points}")
                    
                    # 如果有3个或更多点，自动重新计算平面
                    if num_points >= 3:
                        self._update_plane_from_landmarks(landmark_node)
                    else:
                        # 点数不足3个，移除现有平面
                        self._remove_existing_plane_model()
                        
                elif node_name == "Native_Commissure_Points":
                    logging.info(f"检测到连合标志点修改，当前点数: {num_points}")
                    
                    # 连合点修改后的处理
                    if num_points >= 3:
                        self._handle_commissure_points_complete(landmark_node)
                
                elif node_name == "Neo_Commissure_Points":
                    logging.info(f"检测到新连合标志点修改，当前点数: {num_points}")
                    
                    # 新连合点修改后的处理
                    if num_points >= 3:
                        self._handle_neo_commissure_points_complete(landmark_node)
                    
        except Exception as e:
            logging.error(f"处理标志点修改事件失败: {e}")
    
    def _on_landmark_point_added(self, caller, event):
        """
        标志点被添加时的回调函数
        """
        try:
            landmark_node = caller
            if landmark_node:
                node_name = landmark_node.GetName()
                num_points = landmark_node.GetNumberOfControlPoints()
                
                if node_name == "Native_Annulus_Points":
                    logging.info(f"检测到瓣环标志点添加，当前点数: {num_points}")
                    
                    # 如果达到3个点，自动计算平面
                    if num_points >= 3:
                        self._update_plane_from_landmarks(landmark_node)
                        
                elif node_name == "Native_Commissure_Points":
                    logging.info(f"检测到连合标志点添加，当前点数: {num_points}")
                    
                    # 连合点添加后的处理
                    if num_points >= 3:
                        self._handle_commissure_points_complete(landmark_node)
                
                elif node_name == "Neo_Commissure_Points":
                    logging.info(f"检测到新连合标志点添加，当前点数: {num_points}")
                    
                    # 新连合点添加后的处理
                    if num_points >= 3:
                        self._handle_neo_commissure_points_complete(landmark_node)
                    
        except Exception as e:
            logging.error(f"处理标志点添加事件失败: {e}")
    
    def _on_landmark_point_removed(self, caller, event):
        """
        标志点被删除时的回调函数
        """
        try:
            landmark_node = caller
            if landmark_node:
                node_name = landmark_node.GetName()
                num_points = landmark_node.GetNumberOfControlPoints()
                
                if node_name == "Native_Annulus_Points":
                    logging.info(f"检测到瓣环标志点删除，当前点数: {num_points}")
                    
                    if num_points >= 3:
                        # 仍有足够的点，重新计算平面
                        self._update_plane_from_landmarks(landmark_node)
                    else:
                        # 点数不足，移除平面
                        self._remove_existing_plane_model()
                        
                elif node_name == "Native_Commissure_Points":
                    logging.info(f"检测到连合标志点删除，当前点数: {num_points}")
                    
                    # 连合点删除后的处理
                    if num_points < 3:
                        # 点数不足，重置完成状态
                        landmark_node.SetAttribute("DefinitionComplete", "false")
                        landmark_node.SetAttribute("CommissurePointsNamed", "false")
                
                elif node_name == "Neo_Commissure_Points":
                    logging.info(f"检测到新连合标志点删除，当前点数: {num_points}")
                    
                    # 新连合点删除后的处理
                    if num_points < 3:
                        # 点数不足，重置完成状态
                        landmark_node.SetAttribute("DefinitionComplete", "false")
                        landmark_node.SetAttribute("NeoCommissurePointsNamed", "false")
                    
        except Exception as e:
            logging.error(f"处理标志点删除事件失败: {e}")

    def _handle_commissure_points_complete(self, landmark_node):
        """
        处理连合点完成事件
        
        当连合点达到3个时，自动执行命名和完成流程
        
        Args:
            landmark_node: 连合标志点节点
        """
        try:
            # 检查是否已经处理过
            if landmark_node.GetAttribute("DefinitionComplete") == "true":
                return
            
            # 自动完成连合定义
            self.finalize_native_commissure_definition()
            
        except Exception as e:
            logging.error(f"处理连合点完成事件失败: {e}")
    
    def _handle_neo_commissure_points_complete(self, landmark_node):
        """
        处理新连合点完成事件
        
        当新连合点达到3个时，自动执行命名和完成流程
        
        Args:
            landmark_node: 新连合标志点节点
        """
        try:
            # 检查是否已经处理过
            if landmark_node.GetAttribute("DefinitionComplete") == "true":
                return
            
            # 自动完成新连合定义
            self.finalize_neo_commissure_definition()
            
        except Exception as e:
            logging.error(f"处理新连合点完成事件失败: {e}")
    
    def _update_plane_from_landmarks(self, landmark_node):
        """
        根据当前标志点重新计算和更新平面
        
        Args:
            landmark_node: 标志点节点
        """
        try:
            if not landmark_node or landmark_node.GetNumberOfControlPoints() < 3:
                logging.warning("标志点不足，无法更新平面")
                return False
            
            # 获取前3个点的坐标
            points = []
            for i in range(3):
                coords = [0.0, 0.0, 0.0]
                landmark_node.GetNthControlPointPosition(i, coords)
                points.append(coords)
            
            # 重新计算平面
            plane_data = self._compute_best_fitting_plane(points)
            if plane_data:
                # 更新会话中的平面数据
                self.session.set_reconstructed_plane("native_annulus", plane_data)
                
                # 更新平面Model
                self._update_plane_model(plane_data)
                
                logging.info("平面已根据标志点变化自动更新")
                return True
            else:
                logging.error("平面重新计算失败")
                return False
                
        except Exception as e:
            logging.error(f"更新平面失败: {e}")
            return False
    
    def _update_plane_model(self, plane_data):
        """
        更新现有的平面Model
        
        Args:
            plane_data: 新的平面数据
        """
        try:
            # 获取现有的平面Model
            plane_model = self.session.get_landmark_node("Native_Annulus_Plane_Model")
            
            if plane_model:
                # 更新现有Model的几何体
                origin = plane_data['origin']
                normal = plane_data['normal']
                points_used = plane_data.get('points_used', [])
                
                # 计算新的平面大小
                if points_used:
                    min_coords = [min(p[i] for p in points_used) for i in range(3)]
                    max_coords = [max(p[i] for p in points_used) for i in range(3)]
                    size = max(max_coords[i] - min_coords[i] for i in range(3)) * 2.0
                    size = max(size, 50.0)
                else:
                    size = 60.0
                
                # 创建新的几何体
                new_polydata = self._create_plane_polydata(origin, normal, size)
                
                # 更新Model的几何体
                plane_model.SetAndObservePolyData(new_polydata)
                
                # 更新属性
                plane_model.SetAttribute("Description", f"原生瓣环平面 - 原点: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})")
                plane_model.SetAttribute("PlaneOriginX", str(origin[0]))
                plane_model.SetAttribute("PlaneOriginY", str(origin[1]))
                plane_model.SetAttribute("PlaneOriginZ", str(origin[2]))
                plane_model.SetAttribute("PlaneNormalX", str(normal[0]))
                plane_model.SetAttribute("PlaneNormalY", str(normal[1]))
                plane_model.SetAttribute("PlaneNormalZ", str(normal[2]))
                plane_model.SetAttribute("PlaneSize", str(size))
                
                # 更新Modified时间，触发渲染更新
                plane_model.Modified()
                
                logging.info(f"平面Model已更新 - 新原点: ({origin[0]:.1f}, {origin[1]:.1f}, {origin[2]:.1f})")
                
            else:
                # 如果不存在，创建新的平面Model
                logging.info("平面Model不存在，创建新的Model")
                self._create_plane_visualization(plane_data, "Native_Annulus_Plane")
                
        except Exception as e:
            logging.error(f"更新平面Model失败: {e}")
    
    def _remove_existing_plane_model(self):
        """
        移除现有的平面Model
        """
        try:
            # 从会话获取平面Model
            plane_model = self.session.get_landmark_node("Native_Annulus_Plane_Model")
            
            if plane_model:
                slicer.mrmlScene.RemoveNode(plane_model)
                self.session.set_landmark_node("Native_Annulus_Plane_Model", None)
                logging.info("已移除现有的平面Model")
            
            # 同时清除会话中的平面数据
            self.session.set_reconstructed_plane("native_annulus", None)
            
        except Exception as e:
            logging.error(f"移除平面Model失败: {e}")
    
    def cleanup(self):
        """
        清理资源，移除所有观察者
        """
        try:
            # 停止分析并清理临时文件
            self.stop_auto_analysis()
            
            # 移除所有标志点观察者
            for node_id, observer_ids in list(self.landmark_observers.items()):
                node = slicer.mrmlScene.GetNodeByID(node_id)
                if node:
                    for observer_id in observer_ids:
                        node.RemoveObserver(observer_id)
            
            self.landmark_observers.clear()
            logging.info("Module2Logic 清理完成")
            
        except Exception as e:
            logging.error(f"Module2Logic 清理失败: {e}")
    
    def get_native_annulus_plane_status(self) -> dict:
        """
        获取原生瓣环平面的状态信息
        
        Returns:
            dict: 包含状态信息的字典
        """
        try:
            # 获取标志点节点
            landmark_node = self.session.get_landmark_node("Native_Annulus_Points")
            
            if not landmark_node:
                return {
                    'node_exists': False,
                    'points_placed': 0,
                    'points_needed': 3,
                    'plane_computed': False,
                    'ready_to_compute': False
                }
            
            points_placed = landmark_node.GetNumberOfControlPoints()
            plane_computed = self.session.get_reconstructed_plane("native_annulus") is not None
            ready_to_compute = points_placed >= 3 and not plane_computed
            
            return {
                'node_exists': True,
                'points_placed': points_placed,
                'points_needed': 3,
                'plane_computed': plane_computed,
                'ready_to_compute': ready_to_compute
            }
            
        except Exception as e:
            logging.error(f"获取原生瓣环平面状态失败: {e}")
            return {
                'node_exists': False,
                'points_placed': 0,
                'points_needed': 3,
                'plane_computed': False,
                'ready_to_compute': False
            }

    def define_native_commissure_points(self) -> bool:
        """
        定义原生连合标志点
        
        根据设计文档要求，创建Native_Commissure_Points标志点节点，
        用于标记原始主动脉瓣的三个连合位置。
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            logging.info("开始定义原生连合标志点")
            
            # 1. 创建并激活标志点节点
            landmark_node = self._create_landmark_node("Native_Commissure_Points")
            if not landmark_node:
                logging.error("创建Native_Commissure_Points节点失败")
                return False
            
            # 设置节点特殊属性
            landmark_node.GetDisplayNode().SetTextScale(2.2)  # 稍大的文本
            landmark_node.GetDisplayNode().SetGlyphScale(3.5)  # 稍大的标志点
            landmark_node.GetDisplayNode().SetSelectedColor(1.0, 0.5, 0.0)  # 橙色显示
            
            # 将节点ID存储到会话中
            self.session.set_landmark_node("Native_Commissure_Points", landmark_node.GetID())
            
            # 添加观察者来监听标志点变化
            self._add_landmark_observer(landmark_node)
            
            # 激活标志点放置模式
            self._activate_landmark_placement(landmark_node)
            
            logging.info("Native_Commissure_Points节点已创建并激活，等待用户放置3个连合点")
            return True
            
        except Exception as e:
            logging.error(f"定义原生连合标志点失败: {e}")
            return False

    def get_native_commissure_status(self) -> dict:
        """
        获取原生连合标志点的状态信息
        
        Returns:
            dict: 包含状态信息的字典
        """
        try:
            # 获取标志点节点
            landmark_node = self.session.get_landmark_node("Native_Commissure_Points")
            
            if not landmark_node:
                return {
                    'node_exists': False,
                    'points_placed': 0,
                    'points_needed': 3,
                    'points_complete': False,
                    'points_named': False
                }
            
            points_placed = landmark_node.GetNumberOfControlPoints()
            points_complete = points_placed >= 3
            
            # 检查点是否已命名
            points_named = False
            if points_complete:
                points_named = self._check_commissure_points_named(landmark_node)
            
            return {
                'node_exists': True,
                'points_placed': points_placed,
                'points_needed': 3,
                'points_complete': points_complete,
                'points_named': points_named
            }
            
        except Exception as e:
            logging.error(f"获取原生连合状态失败: {e}")
            return {
                'node_exists': False,
                'points_placed': 0,
                'points_needed': 3,
                'points_complete': False,
                'points_named': False
            }

    def _check_commissure_points_named(self, landmark_node) -> bool:
        """
        检查连合点是否已经命名
        
        Args:
            landmark_node: 标志点节点
            
        Returns:
            bool: 所有点都已命名返回True
        """
        try:
            if landmark_node.GetNumberOfControlPoints() < 3:
                return False
            
            expected_names = ['RCC_LC', 'LCC_NC', 'NC_RCC']  # 右冠-左冠, 左冠-无冠, 无冠-右冠
            
            for i in range(3):
                label = landmark_node.GetNthControlPointLabel(i)
                if not label or label not in expected_names:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"检查连合点命名失败: {e}")
            return False

    def auto_name_commissure_points(self) -> bool:
        """
        自动为连合点命名
        
        当用户放置了3个连合点后，按照解剖学顺序自动命名
        
        Returns:
            bool: 命名成功返回True
        """
        try:
            landmark_node = self.session.get_landmark_node("Native_Commissure_Points")
            if not landmark_node or landmark_node.GetNumberOfControlPoints() < 3:
                logging.warning("连合点不足3个，无法自动命名")
                return False
            
            # 连合点命名：按照解剖学位置
            commissure_names = [
                'RCC_LCC',  # 右冠-左冠连合
                'LCC_NCC',  # 左冠-无冠连合  
                'NCC_RCC'   # 无冠-右冠连合
            ]
            
            commissure_descriptions = [
                '右冠-左冠连合',
                '左冠-无冠连合',
                '无冠-右冠连合'
            ]
            
            # 为前3个点命名
            for i in range(min(3, landmark_node.GetNumberOfControlPoints())):
                landmark_node.SetNthControlPointLabel(i, commissure_names[i])
                landmark_node.SetNthControlPointDescription(i, commissure_descriptions[i])
                logging.info(f"连合点 {i+1} 已命名为: {commissure_names[i]} ({commissure_descriptions[i]})")
            
            # 设置节点属性，标记为已命名
            landmark_node.SetAttribute("CommissurePointsNamed", "true")
            landmark_node.SetAttribute("NamingTimestamp", str(slicer.app.timeStamp()))
            
            logging.info("原生连合点自动命名完成")
            return True
            
        except Exception as e:
            logging.error(f"自动命名连合点失败: {e}")
            return False

    def finalize_native_commissure_definition(self) -> bool:
        """
        完成原生连合定义
        
        当用户放置完3个连合点后，执行最终确认和数据整理
        
        Returns:
            bool: 完成成功返回True
        """
        try:
            landmark_node = self.session.get_landmark_node("Native_Commissure_Points")
            if not landmark_node:
                logging.error("未找到原生连合标志点节点")
                return False
            
            if landmark_node.GetNumberOfControlPoints() < 3:
                logging.error("连合点数量不足3个")
                return False
            
            # 自动命名连合点
            if not self.auto_name_commissure_points():
                logging.warning("自动命名失败，但继续完成定义")
            
            # 计算连合点的几何中心
            center = self._calculate_commissure_center(landmark_node)
            if center:
                # 存储连合中心到会话
                self.session.set_landmark_node("Native_Commissure_Center", center)
                logging.info(f"连合中心计算完成: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
            
            # 设置完成标记
            landmark_node.SetAttribute("DefinitionComplete", "true")
            landmark_node.SetAttribute("CompletionTimestamp", str(slicer.app.timeStamp()))
            
            # 停用放置模式
            interaction_node = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interaction_node:
                interaction_node.SetCurrentInteractionMode(interaction_node.ViewTransform)
            
            logging.info("原生连合定义已完成")
            return True
            
        except Exception as e:
            logging.error(f"完成原生连合定义失败: {e}")
            return False

    def _calculate_commissure_center(self, landmark_node) -> Optional[List[float]]:
        """
        计算连合点的几何中心
        
        Args:
            landmark_node: 连合标志点节点
            
        Returns:
            List[float]: 中心坐标[x, y, z]，失败返回None
        """
        try:
            if landmark_node.GetNumberOfControlPoints() < 3:
                return None
            
            # 获取3个连合点的坐标
            total_x, total_y, total_z = 0.0, 0.0, 0.0
            
            for i in range(3):
                coords = [0.0, 0.0, 0.0]
                landmark_node.GetNthControlPointPosition(i, coords)
                total_x += coords[0]
                total_y += coords[1]
                total_z += coords[2]
            
            # 计算平均值（几何中心）
            center = [total_x / 3.0, total_y / 3.0, total_z / 3.0]
            
            return center
            
        except Exception as e:
            logging.error(f"计算连合中心失败: {e}")
            return None

    def define_neo_commissure_points(self) -> bool:
        """
        定义新连合标志点
        
        根据设计文档要求，创建Neo_Commissure_Points标志点节点，
        用于标记植入的TAVR瓣膜的三个新连合位置。
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            logging.info("开始定义新连合标志点")
            
            # 1. 创建并激活标志点节点
            landmark_node = self._create_landmark_node("Neo_Commissure_Points")
            if not landmark_node:
                logging.error("创建Neo_Commissure_Points节点失败")
                return False
            
            # 设置节点特殊属性
            landmark_node.GetDisplayNode().SetTextScale(2.2)  # 稍大的文本
            landmark_node.GetDisplayNode().SetGlyphScale(3.5)  # 稍大的标志点
            landmark_node.GetDisplayNode().SetSelectedColor(0.0, 0.8, 1.0)  # 青蓝色显示
            
            # 将节点ID存储到会话中
            self.session.set_landmark_node("Neo_Commissure_Points", landmark_node.GetID())
            
            # 添加观察者来监听标志点变化
            self._add_landmark_observer(landmark_node)
            
            # 激活标志点放置模式
            self._activate_landmark_placement(landmark_node)
            
            logging.info("Neo_Commissure_Points节点已创建并激活，等待用户放置3个新连合点")
            return True
            
        except Exception as e:
            logging.error(f"定义新连合标志点失败: {e}")
            return False

    def get_neo_commissure_status(self) -> dict:
        """
        获取新连合标志点的状态信息
        
        Returns:
            dict: 包含状态信息的字典
        """
        try:
            # 获取标志点节点
            landmark_node = self.session.get_landmark_node("Neo_Commissure_Points")
            
            if not landmark_node:
                return {
                    'node_exists': False,
                    'points_placed': 0,
                    'points_needed': 3,
                    'points_complete': False,
                    'points_named': False
                }
            
            points_placed = landmark_node.GetNumberOfControlPoints()
            points_complete = points_placed >= 3
            
            # 检查点是否已命名
            points_named = False
            if points_complete:
                points_named = self._check_neo_commissure_points_named(landmark_node)
            
            return {
                'node_exists': True,
                'points_placed': points_placed,
                'points_needed': 3,
                'points_complete': points_complete,
                'points_named': points_named
            }
            
        except Exception as e:
            logging.error(f"获取新连合状态失败: {e}")
            return {
                'node_exists': False,
                'points_placed': 0,
                'points_needed': 3,
                'points_complete': False,
                'points_named': False
            }

    def _check_neo_commissure_points_named(self, landmark_node) -> bool:
        """
        检查新连合点是否已经命名
        
        Args:
            landmark_node: 标志点节点
            
        Returns:
            bool: 所有点都已命名返回True
        """
        try:
            if landmark_node.GetNumberOfControlPoints() < 3:
                return False
            
            expected_names = ['Neo_RCC_LCC', 'Neo_LCC_NCC', 'Neo_NCC_RCC']  # 新连合命名
            
            for i in range(3):
                label = landmark_node.GetNthControlPointLabel(i)
                if not label or label not in expected_names:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"检查新连合点命名失败: {e}")
            return False

    def auto_name_neo_commissure_points(self) -> bool:
        """
        自动为新连合点命名
        
        当用户放置了3个新连合点后，按照解剖学顺序自动命名
        
        Returns:
            bool: 命名成功返回True
        """
        try:
            landmark_node = self.session.get_landmark_node("Neo_Commissure_Points")
            if not landmark_node or landmark_node.GetNumberOfControlPoints() < 3:
                logging.warning("新连合点不足3个，无法自动命名")
                return False
            
            # 新连合点命名：按照解剖学位置
            commissure_names = [
                'Neo_RCC_LCC',  # 新右冠-左冠连合
                'Neo_LCC_NCC',  # 新左冠-无冠连合  
                'Neo_NCC_RCC'   # 新无冠-右冠连合
            ]
            
            commissure_descriptions = [
                '新右冠-左冠连合',
                '新左冠-无冠连合',
                '新无冠-右冠连合'
            ]
            
            # 为前3个点命名
            for i in range(min(3, landmark_node.GetNumberOfControlPoints())):
                landmark_node.SetNthControlPointLabel(i, commissure_names[i])
                landmark_node.SetNthControlPointDescription(i, commissure_descriptions[i])
                logging.info(f"新连合点 {i+1} 已命名为: {commissure_names[i]} ({commissure_descriptions[i]})")
            
            # 设置节点属性，标记为已命名
            landmark_node.SetAttribute("NeoCommissurePointsNamed", "true")
            landmark_node.SetAttribute("NamingTimestamp", str(slicer.app.timeStamp()))
            
            logging.info("新连合点自动命名完成")
            return True
            
        except Exception as e:
            logging.error(f"自动命名新连合点失败: {e}")
            return False

    def finalize_neo_commissure_definition(self) -> bool:
        """
        完成新连合定义
        
        当用户放置完3个新连合点后，执行最终确认和数据整理
        
        Returns:
            bool: 完成成功返回True
        """
        try:
            landmark_node = self.session.get_landmark_node("Neo_Commissure_Points")
            if not landmark_node:
                logging.error("未找到新连合标志点节点")
                return False
            
            if landmark_node.GetNumberOfControlPoints() < 3:
                logging.error("新连合点数量不足3个")
                return False
            
            # 自动命名新连合点
            if not self.auto_name_neo_commissure_points():
                logging.warning("自动命名失败，但继续完成定义")
            
            # 计算新连合点的几何中心
            center = self._calculate_neo_commissure_center(landmark_node)
            if center:
                # 存储新连合中心到会话
                self.session.set_landmark_node("Neo_Commissure_Center", center)
                logging.info(f"新连合中心计算完成: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
            
            # 设置完成标记
            landmark_node.SetAttribute("DefinitionComplete", "true")
            landmark_node.SetAttribute("CompletionTimestamp", str(slicer.app.timeStamp()))
            
            # 停用放置模式
            interaction_node = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interaction_node:
                interaction_node.SetCurrentInteractionMode(interaction_node.ViewTransform)
            
            logging.info("新连合定义已完成")
            return True
            
        except Exception as e:
            logging.error(f"完成新连合定义失败: {e}")
            return False

    def _calculate_neo_commissure_center(self, landmark_node) -> Optional[List[float]]:
        """
        计算新连合点的几何中心
        
        Args:
            landmark_node: 新连合标志点节点
            
        Returns:
            List[float]: 中心坐标[x, y, z]，失败返回None
        """
        try:
            if landmark_node.GetNumberOfControlPoints() < 3:
                return None
            
            # 获取3个新连合点的坐标
            total_x, total_y, total_z = 0.0, 0.0, 0.0
            
            for i in range(3):
                coords = [0.0, 0.0, 0.0]
                landmark_node.GetNthControlPointPosition(i, coords)
                total_x += coords[0]
                total_y += coords[1]
                total_z += coords[2]
            
            # 计算平均值（几何中心）
            center = [total_x / 3.0, total_y / 3.0, total_z / 3.0]
            
            return center
            
        except Exception as e:
            logging.error(f"计算新连合中心失败: {e}")
            return None
