"""
模块一业务逻辑类
负责数据导入与场景准备的核心业务逻辑
"""

import logging
from typing import Optional, List
import qt
import slicer
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..utils.dicom_utils import DicomUtils
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from utils.dicom_utils import DicomUtils


class Module1Logic(ScriptedLoadableModuleLogic):
    """
    模块一业务逻辑类
    
    负责处理数据导入与场景准备相关的所有业务逻辑，包括：
    - DICOM序列加载
    - 序列节点管理
    - DICOM元数据处理
    - 数据验证
    """

    def __init__(self) -> None:
        """初始化模块一逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)
        self.session = TAVRStudySession()

    def load_dicom_sequence(self) -> bool:
        """
        加载4D DICOM序列
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 清理当前会话
            self.session.reset()
            
            # 打开DICOM模块让用户导入和选择数据
            slicer.util.selectModule('DICOM')
            
            # 提示用户
            qt.QMessageBox.information(
                None, "导入DICOM数据", 
                "请在DICOM浏览器中导入并选择4D心脏CT序列数据。\n"
                "选择数据后，请点击'Load'按钮加载数据。\n"
                "加载完成后，请返回TAVR Analytics模块。"
            )
            
            # 等待用户加载数据，然后验证场景中的序列节点
            return self.wait_and_validate_loaded_sequence()
            
        except Exception as e:
            logging.error(f"Failed to load DICOM sequence: {e}")
            qt.QMessageBox.critical(None, "错误", f"加载DICOM序列失败: {str(e)}")
            return False

    def wait_and_validate_loaded_sequence(self) -> bool:
        """
        等待并验证加载的序列数据
        
        Returns:
            bool: 验证成功返回True，失败返回False
        """
        # 检查场景中是否有序列节点
        sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
        
        if not sequence_nodes:
            # 如果没有序列节点，尝试创建一个对话框让用户选择现有的容积节点来创建序列
            return self.create_sequence_from_volumes()
        
        # 如果有多个序列节点，让用户选择
        if len(sequence_nodes) > 1:
            sequence_node = self.select_sequence_node(sequence_nodes)
        else:
            sequence_node = sequence_nodes[0]
            
        if not sequence_node:
            return False
            
        # 验证序列节点
        if not self.validate_sequence_node(sequence_node):
            qt.QMessageBox.warning(
                None, "无效序列", 
                "选择的序列不是有效的4D心脏CT数据。\n"
                "请确保序列包含多个时间点的容积数据。"
            )
            return False
        
        # 创建或获取序列浏览器节点
        browser_node = self.get_or_create_sequence_browser(sequence_node)
        if not browser_node:
            return False
            
        # 保存到会话
        self.session.volume_sequence_node_id = sequence_node.GetID()
        self.session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def create_sequence_from_volumes(self) -> bool:
        """
        从现有容积节点创建序列
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        volume_nodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
        
        if len(volume_nodes) < 2:
            qt.QMessageBox.warning(
                None, "数据不足", 
                "场景中需要至少2个容积节点来创建4D序列。\n"
                "请在DICOM浏览器中加载完整的4D心脏CT数据。"
            )
            return False
        
        # 询问用户是否要从现有容积创建序列
        reply = qt.QMessageBox.question(
            None, "创建序列", 
            f"发现{len(volume_nodes)}个容积节点。\n"
            "是否要将这些容积组合成4D序列？",
            qt.QMessageBox.Yes | qt.QMessageBox.No,
            qt.QMessageBox.Yes
        )
        
        if reply != qt.QMessageBox.Yes:
            return False
            
        # 创建序列节点
        sequence_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSequenceNode')
        sequence_node.SetName("4D_Cardiac_CT_Sequence")
        
        # 添加容积到序列
        for i, volume in enumerate(volume_nodes):
            # 假设时相百分比均匀分布
            phase_percent = (i * 100.0) / (len(volume_nodes) - 1)
            sequence_node.SetDataNodeAtValue(volume, str(phase_percent))
        
        sequence_node.SetIndexName("Phase")
        sequence_node.SetIndexUnit("%")
        
        # 创建序列浏览器
        browser_node = self.get_or_create_sequence_browser(sequence_node)
        if not browser_node:
            return False
            
        # 保存到会话
        self.session.volume_sequence_node_id = sequence_node.GetID()
        self.session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def select_sequence_node(self, sequence_nodes: List) -> Optional[object]:
        """
        让用户选择序列节点
        
        Args:
            sequence_nodes: 序列节点列表
            
        Returns:
            选择的序列节点，如果取消选择则返回None
        """
        dialog = qt.QDialog()
        dialog.setWindowTitle("选择4D序列")
        dialog.setModal(True)
        
        layout = qt.QVBoxLayout(dialog)
        
        label = qt.QLabel("发现多个序列，请选择4D心脏CT序列：")
        layout.addWidget(label)
        
        list_widget = qt.QListWidget()
        for node in sequence_nodes:
            item = qt.QListWidgetItem(f"{node.GetName()} ({node.GetNumberOfDataNodes()} 帧)")
            item.setData(qt.Qt.UserRole, node)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        
        button_layout = qt.QHBoxLayout()
        ok_button = qt.QPushButton("确定")
        cancel_button = qt.QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        selected_node = None
        
        def on_ok():
            current_item = list_widget.currentItem()
            if current_item:
                nonlocal selected_node
                selected_node = current_item.data(qt.Qt.UserRole)
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
            
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)
        
        if dialog.exec_() == qt.QDialog.Accepted:
            return selected_node
        return None

    def get_or_create_sequence_browser(self, sequence_node) -> Optional[object]:
        """
        获取或创建序列浏览器节点
        
        Args:
            sequence_node: 序列节点
            
        Returns:
            序列浏览器节点，创建失败返回None
        """
        # 检查是否已有浏览器节点
        browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
        
        for browser in browser_nodes:
            if browser.GetMasterSequenceNode() == sequence_node:
                return browser
        
        # 创建新的浏览器节点
        browser_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSequenceBrowserNode')
        browser_node.SetName(f"Browser_{sequence_node.GetName()}")
        browser_node.SetAndObserveMasterSequenceNodeID(sequence_node.GetID())
        
        # 创建代理节点
        proxy_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        proxy_node.SetName(f"Proxy_{sequence_node.GetName()}")
        browser_node.SetAndObserveProxyNode(proxy_node, sequence_node)
        
        # 尝试保存DICOM元数据到序列节点和代理节点
        self.preserve_dicom_metadata(sequence_node)
        
        return browser_node
    
    def preserve_dicom_metadata(self, sequence_node) -> None:
        """
        保存DICOM元数据到序列节点中的各个数据节点
        
        Args:
            sequence_node: 序列节点
        """
        try:
            num_data_nodes = sequence_node.GetNumberOfDataNodes()
            logging.info(f"正在为 {num_data_nodes} 个数据节点保存DICOM元数据")
            
            for i in range(num_data_nodes):
                data_node = sequence_node.GetNthDataNode(i)
                if data_node:
                    DicomUtils.preserve_dicom_metadata(data_node)
                    
                    # 如果是第一个节点，也设置到序列节点
                    if i == 0:
                        series_desc = data_node.GetAttribute('DICOM.SeriesDescription')
                        if series_desc:
                            sequence_node.SetAttribute('DICOM.SeriesDescription', series_desc)
                            sequence_node.SetAttribute('SeriesDescription', series_desc)
                            logging.info(f"为序列节点保存了Series Description: {series_desc}")
                    
        except Exception as e:
            logging.warning(f"Failed to preserve DICOM metadata: {e}")
    
    def validate_sequence_node(self, node) -> bool:
        """
        验证节点是否为有效的4D序列
        
        Args:
            node: 要验证的节点
            
        Returns:
            bool: 有效返回True，无效返回False
        """
        return DicomUtils.validate_sequence_node(node)

    def parse_dicom_metadata(self) -> None:
        """解析DICOM元数据并填充患者信息"""
        DicomUtils.parse_dicom_metadata(self.session)

    def extract_dicom_info_from_database(self, volume_node, patient_data) -> None:
        """
        从DICOM数据库提取患者信息
        
        Args:
            volume_node: 容积节点
            patient_data: 患者数据对象
        """
        DicomUtils.extract_dicom_info_from_database(volume_node, patient_data)

    def read_dicom_file_info(self, file_path: str) -> dict:
        """
        读取DICOM文件信息
        
        Args:
            file_path: DICOM文件路径
            
        Returns:
            dict: DICOM信息字典
        """
        return DicomUtils.read_dicom_file_info(file_path)

    def populate_patient_data_from_dicom(self, dicom_info: dict, patient_data) -> None:
        """
        从DICOM信息填充患者数据
        
        Args:
            dicom_info: DICOM信息字典
            patient_data: 患者数据对象
        """
        DicomUtils.populate_patient_data_from_dicom(dicom_info, patient_data)

    def get_dicom_tag_value(self, volume_node, tag: str) -> str:
        """
        获取DICOM标签值
        
        Args:
            volume_node: 容积节点
            tag: DICOM标签
            
        Returns:
            str: 标签值
        """
        return DicomUtils.get_dicom_tag_value(volume_node, tag)

    def get_current_sequence_info(self) -> dict:
        """
        获取当前序列信息
        
        Returns:
            dict: 包含序列信息的字典
        """
        if not self.session.volume_sequence_node_id:
            return {}
            
        sequence_node = slicer.mrmlScene.GetNodeByID(self.session.volume_sequence_node_id)
        if not sequence_node:
            return {}
            
        return {
            'name': sequence_node.GetName(),
            'num_frames': sequence_node.GetNumberOfDataNodes(),
            'index_name': sequence_node.GetIndexName(),
            'index_unit': sequence_node.GetIndexUnit()
        }

    def reset_sequence_data(self) -> None:
        """重置序列数据"""
        self.session.reset()
        logging.info("序列数据已重置")
