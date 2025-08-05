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
    from .module1.module1_logic import Module1Logic
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
    from module1.module1_logic import Module1Logic


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
        self.module1_logic = None
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
        self.module1_logic = Module1Logic()
        
        # 创建主界面
        self.create_main_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 检查场景中是否已有序列数据
        self.check_and_process_existing_sequences()

    def create_main_ui(self):
        """创建主界面"""
        # 创建模块一组件，传入Module1Logic
        self.module1_widget = Module1Widget(self.session, logic=self.module1_logic)
        
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
                self.module1_logic.preserve_dicom_metadata(sequence_node)
                
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
    """插件逻辑类 - 保留全局逻辑功能"""

    def __init__(self) -> None:
        """初始化逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)


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
