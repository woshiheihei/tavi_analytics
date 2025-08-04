import logging
import os
import json
import datetime
from typing import Optional, Dict, Any

import vtk
import qt

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleTest
)
from slicer.util import VTKObservationMixin

from slicer import vtkMRMLSequenceNode, vtkMRMLSequenceBrowserNode, vtkMRMLScalarVolumeNode

# 导入重构后的核心模块
try:
    # 尝试相对导入（用于包内导入）
    from .core.data_models import PatientData
    from .core.enums import ImageQuality, FollowUpTimepoint
    from .core.session import TAVRStudySession
    from .utils.dicom_utils import DicomUtils
    from .utils.config_manager import ConfigManager
    from .utils.qt_utils import QtUtils
    from .utils.logging_utils import LoggingUtils
    from .module1.module1_widget import Module1Widget
except ImportError:
    # 回退到绝对导入（用于3D Slicer直接加载）
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from core.data_models import PatientData
    from core.enums import ImageQuality, FollowUpTimepoint
    from core.session import TAVRStudySession
    from utils.dicom_utils import DicomUtils
    from utils.config_manager import ConfigManager
    from utils.qt_utils import QtUtils
    from utils.logging_utils import LoggingUtils
    from module1.module1_widget import Module1Widget


# TAVRStudySession 类已移动到 core/session.py
# DataLoadingDialog 类已移动到 module1/data_loading_dialog.py


#
# tavi_analytics
#

class tavi_analytics(ScriptedLoadableModule):
    """TAVR-Analytics Workflow 3D Slicer插件主模块"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("TAVR Analytics")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Cardiac")]
        self.parent.dependencies = ["Sequences"]
        self.parent.contributors = ["TAVR Research Team"]
        self.parent.helpText = _("""
TAVR-Analytics Workflow插件用于经导管主动脉瓣置换术（TAVR）术后的四维心脏CT分析。
该插件提供完整的分析工作流，包括数据导入、场景准备、分割、测量和报告生成。
""")
        self.parent.acknowledgementText = _("""
该插件基于杭州方案术后CT核心实验室评估表开发，用于标准化TAVR术后分析流程。
""")


#
# tavi_analyticsWidget
#

class tavi_analyticsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """插件主界面类"""

    def __init__(self, parent=None) -> None:
        """初始化界面"""
        # 先初始化必要的属性
        self.logic = None
        self.session = TAVRStudySession()
        self.module1_widget = None
        
        # 然后调用父类初始化（这会触发setup()方法）
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        
    def setup(self) -> None:
        """设置界面"""
        ScriptedLoadableModuleWidget.setup(self)
        
        # 加载简单的UI文件作为容器
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/tavi_analytics.ui"))
        self.layout.addWidget(uiWidget)
        
        # 创建逻辑类
        self.logic = tavi_analyticsLogic()
        
        # 创建主界面
        self.create_main_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 检查场景中是否已有序列数据
        self.check_and_process_existing_sequences()

    def create_main_ui(self):
        """创建主界面"""
        # 创建模块一组件
        self.module1_widget = Module1Widget(self.session, logic=self.logic)
        
        # 连接模块一信号
        self.module1_widget.dataConfigured.connect(self.on_module1_data_configured)
        self.module1_widget.readyForNextModule.connect(self.on_ready_for_module2)
        
        # 添加到主布局
        self.layout.addWidget(self.module1_widget)
        self.layout.addStretch()
        
    def on_module1_data_configured(self):
        """处理模块一数据配置完成"""
        pass  # 可以在这里添加额外的处理逻辑
        
    def on_ready_for_module2(self):
        """处理准备进入模块二"""
        # 这里可以显示模块二界面或切换到模块二
        pass  # 暂时保留为空，等待模块二实现

    def setup_connections(self):
        """设置信号连接"""
        # 监听场景变化
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    def onSceneStartClose(self, caller, event):
        """场景关闭开始时的处理"""
        pass

    def onSceneEndClose(self, caller, event):
        """场景关闭结束时的处理"""
        # 重置会话
        self.session.reset()
        
        # 如果模块一组件存在，更新其状态
        if self.module1_widget:
            # 模块一组件会自动检测会话状态并更新界面
            pass

    def check_and_process_existing_sequences(self):
        """检查并处理现有的序列数据"""
        try:
            # 查找场景中的序列节点
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
            
            if sequence_nodes and browser_nodes:
                import logging
                logging.info("发现现有序列数据，正在重新处理DICOM元数据...")
                
                # 选择第一个序列节点
                sequence_node = sequence_nodes[0]
                browser_node = browser_nodes[0]
                
                # 更新会话
                self.session.volume_sequence_node_id = sequence_node.GetID()
                self.session.sequence_browser_node_id = browser_node.GetID()
                
                # 重新处理DICOM元数据
                self.logic.preserve_dicom_metadata(sequence_node)
                
                logging.info("完成现有序列数据的DICOM元数据处理")
                
        except Exception as e:
            import logging
            logging.error(f"处理现有序列数据时出错: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self) -> None:
        """清理资源"""
        self.removeObservers()
        
        # 清理模块一组件
        if self.module1_widget:
            self.module1_widget.cleanup()

    def enter(self) -> None:
        """进入模块"""
        pass

    def exit(self) -> None:
        """退出模块"""
        pass


#
# tavi_analyticsLogic
#

class tavi_analyticsLogic(ScriptedLoadableModuleLogic):
    """插件逻辑类"""

    def __init__(self) -> None:
        """初始化逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)

    def load_dicom_sequence(self) -> bool:
        """加载4D DICOM序列"""
        try:
            # 清理当前会话
            session = TAVRStudySession()
            session.reset()
            
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
            return self.wait_and_validate_loaded_sequence(session)
            
        except Exception as e:
            logging.error(f"Failed to load DICOM sequence: {e}")
            qt.QMessageBox.critical(None, "错误", f"加载DICOM序列失败: {str(e)}")
            return False

    def wait_and_validate_loaded_sequence(self, session: TAVRStudySession) -> bool:
        """等待并验证加载的序列数据"""
        # 检查场景中是否有序列节点
        sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
        
        if not sequence_nodes:
            # 如果没有序列节点，尝试创建一个对话框让用户选择现有的容积节点来创建序列
            return self.create_sequence_from_volumes(session)
        
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
        session.volume_sequence_node_id = sequence_node.GetID()
        session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def create_sequence_from_volumes(self, session: TAVRStudySession) -> bool:
        """从现有容积节点创建序列"""
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
        session.volume_sequence_node_id = sequence_node.GetID()
        session.sequence_browser_node_id = browser_node.GetID()
        
        return True

    def select_sequence_node(self, sequence_nodes):
        """让用户选择序列节点"""
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

    def get_or_create_sequence_browser(self, sequence_node):
        """获取或创建序列浏览器节点"""
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
    
    def preserve_dicom_metadata(self, sequence_node):
        """保存DICOM元数据到序列节点中的各个数据节点"""
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
        """验证节点是否为有效的4D序列"""
        return DicomUtils.validate_sequence_node(node)

    def parse_dicom_metadata(self, session: TAVRStudySession):
        """解析DICOM元数据并填充患者信息"""
        DicomUtils.parse_dicom_metadata(session)

    def extract_dicom_info_from_database(self, volume_node, patient_data):
        """从DICOM数据库提取患者信息"""
        DicomUtils.extract_dicom_info_from_database(volume_node, patient_data)

    def read_dicom_file_info(self, file_path):
        """读取DICOM文件信息"""
        return DicomUtils.read_dicom_file_info(file_path)

    def populate_patient_data_from_dicom(self, dicom_info, patient_data):
        """从DICOM信息填充患者数据"""
        DicomUtils.populate_patient_data_from_dicom(dicom_info, patient_data)

    def get_dicom_tag_value(self, volume_node, tag):
        """获取DICOM标签值"""
        return DicomUtils.get_dicom_tag_value(volume_node, tag)


#
# tavi_analyticsTest
#

class tavi_analyticsTest(ScriptedLoadableModuleTest):
    """测试类"""

    def setUp(self):
        """设置测试环境"""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """运行测试"""
        self.setUp()
        self.test_session_singleton()
        self.test_patient_data()

    def test_session_singleton(self):
        """测试会话单例模式"""
        session1 = TAVRStudySession()
        session2 = TAVRStudySession()
        self.assertEqual(session1, session2)

    def test_patient_data(self):
        """测试患者数据"""
        session = TAVRStudySession()
        session.reset()
        
        data = session.get_patient_data()
        self.assertIsInstance(data, PatientData)
        self.assertEqual(data.patientID, "")
        
        data.patientID = "TEST001"
        data.valveBrand = "Medtronic"
        data.valveModel = "Evolut R/PRO"
        
        valve_info = session.get_selected_valve()
        self.assertEqual(valve_info['brand'], "Medtronic")
        self.assertEqual(valve_info['model'], "Evolut R/PRO")

        self.delayDisplay("测试通过")
