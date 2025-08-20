import logging
import os
import sys
from typing import Optional

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

# 确保插件路径在系统路径中
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入核心组件
from core.plugin_config import PluginConfig
from core.module_manager import ModuleManager, ModuleInfo
from core.session import TAVRStudySession
from core.data_models import PatientData
from module1.module1_adapter import Module1Adapter
from ui.main_ui import MainUI


#
# tavi_analytics
#

class tavi_analytics(ScriptedLoadableModule):
    """TAVR-Analytics Workflow 3D Slicer插件主模块"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        
        # 初始化插件配置
        self._config = PluginConfig()
        metadata = self._config.get_plugin_metadata()
        
        # 设置插件元数据
        self.parent.title = _(metadata.name)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Cardiac")]
        self.parent.dependencies = metadata.dependencies
        self.parent.contributors = [metadata.author]
        self.parent.helpText = _(metadata.description)
        self.parent.acknowledgementText = _("""
该插件基于杭州方案术后CT核心实验室评估表开发，用于标准化TAVR术后分析流程。
""")
        
        # 设置日志
        self._config.setup_logging()
        
        # 初始化模块管理器
        self._initialize_modules()
    
    def _initialize_modules(self):
        """初始化并注册模块"""
        try:
            manager = ModuleManager()
            
            # 注册模块一
            if self._config.is_module_enabled("module1"):
                module1_info = ModuleInfo(
                    name="module1",
                    display_name="数据导入与场景准备",
                    module_class=Module1Adapter,
                    dependencies=[],
                    enabled=True
                )
                manager.register_module(module1_info)
                logging.info("模块一注册成功")
            
            # 注册模块二
            if self._config.is_module_enabled("module2"):  # 假设未来会用配置控制
                from module2.module2_adapter import Module2Adapter  # 导入适配器
                module2_info = ModuleInfo(
                    name="module2",
                    display_name="全自动分析",  # 与适配器中保持一致
                    module_class=Module2Adapter,
                    dependencies=["module1"],
                    enabled=True
                )
                manager.register_module(module2_info)
                logging.info("模块二注册成功")
            
            # 注册模块三（骨架）
            if self._config.is_module_enabled("module3"):
                from module3.module3_adapter import Module3Adapter
                module3_info = ModuleInfo(
                    name="module3",
                    display_name="瓣叶功能评估",
                    module_class=Module3Adapter,
                    dependencies=["module1"],  # 暂仅依赖模块一，后续可加module2
                    enabled=True
                )
                manager.register_module(module3_info)
                logging.info("模块三注册成功")
            
            # 注册模块四
            if self._config.is_module_enabled("module4"):
                from module4.module4_adapter import Module4Adapter
                module4_info = ModuleInfo(
                    name="module4",
                    display_name="瓣膜支架几何形态评估",
                    module_class=Module4Adapter,
                    dependencies=["module1"],  # 暂仅依赖模块一，后续可加其他依赖
                    enabled=True
                )
                manager.register_module(module4_info)
                logging.info("模块四注册成功")
            
            # 这里可以注册其他模块（模块五等）
            # TODO: 注册其他模块
            
        except Exception as e:
            logging.error(f"初始化模块时出错: {e}")
            import traceback
            traceback.print_exc()


#
# tavi_analyticsWidget
#

class tavi_analyticsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """插件主界面类 - 轻量级入口点"""

    def __init__(self, parent=None) -> None:
        """初始化界面"""
        # 核心组件必须在调用父类构造函数之前初始化
        # 因为父类构造函数会自动调用setup()方法
        self._config = PluginConfig()
        self._manager = ModuleManager()
        self._session = TAVRStudySession()
        self.logic = None
        
        # 主界面组件
        self._main_ui = None
        
        # 调用父类构造函数（会自动调用setup方法）
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
    
    # 对外暴露便捷属性，供其他模块访问
    @property
    def module_manager(self) -> ModuleManager:
        return self._manager

    @property
    def main_ui(self) -> Optional[MainUI]:
        return self._main_ui

    @property
    def session(self) -> TAVRStudySession:
        return self._session
        
    def setup(self) -> None:
        """设置界面"""
        ScriptedLoadableModuleWidget.setup(self)
        
        # 创建逻辑实例
        self.logic = tavi_analyticsLogic()
        
        # 设置模块管理器
        self._manager.set_session(self._session)
        self._manager.set_main_widget(self)
        
        # 创建主界面
        self._create_main_ui()
        
        # 设置连接
        self._setup_connections()
        
        # 自动激活模块一（如果启用）
        self._auto_activate_modules()

    def _create_main_ui(self):
        """创建主界面"""
        try:
            # 创建主界面组件
            self._main_ui = MainUI(self._session, self._manager, parent=self)
            
            # 将主界面添加到布局
            self.layout.addWidget(self._main_ui)
            
            logging.info("主界面创建成功")
            
        except Exception as e:
            logging.error(f"创建主界面失败: {e}")
            # 使用默认布局作为后备
            self._create_default_layout()
    
    def _create_default_layout(self):
        """创建默认布局（后备方案）"""
        # 创建一个简单的容器组件
        container_widget = qt.QWidget()
        container_layout = qt.QVBoxLayout(container_widget)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        
        # 添加错误信息
        error_label = qt.QLabel("界面加载失败，使用默认模式")
        # 使用统一的样式系统
        from ui.styles import StyleManager
        error_label.setStyleSheet(StyleManager.get_status_indicator_style("error"))
        container_layout.addWidget(error_label)
        
        self.layout.addWidget(container_widget)
        self._module_container = container_layout
    
    def _setup_connections(self):
        """设置信号连接"""
        # 监听场景变化
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self._on_scene_start_close)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self._on_scene_end_close)
    
    def _auto_activate_modules(self):
        """自动激活模块"""
        try:
            # 检查是否有现有的序列数据
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
            
            # 如果主界面创建成功，使用主界面的自动激活功能
            if self._main_ui:
                self._main_ui.auto_activate_default_module()
                
                # 如果存在序列数据，自动处理
                if sequence_nodes and browser_nodes:
                    self._process_existing_sequences(sequence_nodes[0], browser_nodes[0])
                
                logging.info("通过主界面自动激活模块")
                return
            
            # 后备方案：直接激活模块一（保持兼容性）
            if self._config.is_module_enabled("module1"):
                success = self._manager.activate_module("module1")
                if success:
                    # 获取模块一组件并添加到界面
                    module1_widget = self._manager.get_module_widget("module1")
                    if module1_widget:
                        # 根据容器类型添加组件
                        if hasattr(self._module_container, 'addWidget'):
                            # 如果是布局对象
                            self._module_container.addWidget(module1_widget)
                        elif hasattr(self._module_container, 'layout') and self._module_container.layout():
                            # 如果是有布局的组件
                            self._module_container.layout().addWidget(module1_widget)
                        else:
                            # 回退到主布局
                            self.layout.addWidget(module1_widget)
                        
                        logging.info("模块一已激活并添加到界面（后备模式）")
                        
                        # 如果存在序列数据，自动处理
                        if sequence_nodes and browser_nodes:
                            self._process_existing_sequences(sequence_nodes[0], browser_nodes[0])
                else:
                    logging.error("激活模块一失败")
            
            # 添加拉伸因子
            if hasattr(self._module_container, 'addStretch'):
                self._module_container.addStretch()
            
        except Exception as e:
            logging.error(f"自动激活模块时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_existing_sequences(self, sequence_node, browser_node):
        """处理现有的序列数据"""
        try:
            logging.info("发现现有序列数据，正在处理...")
            
            # 更新会话
            self._session.volume_sequence_node_id = sequence_node.GetID()
            self._session.sequence_browser_node_id = browser_node.GetID()
            
            # 获取模块一组件
            module1_widget = self._manager.get_module_widget("module1")
            if module1_widget and hasattr(module1_widget, 'logic'):
                # 重新处理DICOM元数据
                module1_widget.logic.preserve_dicom_metadata(sequence_node)
                logging.info("完成现有序列数据的DICOM元数据处理")
            
        except Exception as e:
            logging.error(f"处理现有序列数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_scene_start_close(self, caller, event):
        """场景关闭开始时的处理"""
        pass

    def _on_scene_end_close(self, caller, event):
        """场景关闭结束时的处理"""
        # 重置会话
        self._session.reset()
        
        # 更新主界面状态
        if self._main_ui:
            self._main_ui.update_patient_info()  # 清除患者信息
            self._main_ui.update_session_status("空闲")
            self._main_ui.update_status("就绪")
        
        # 通知模块管理器场景已关闭
        # 模块组件会自动检测会话状态并更新界面
        logging.info("场景已关闭，会话已重置")

    def cleanup(self) -> None:
        """清理资源"""
        self.removeObservers()
        
        # 清理主界面
        if self._main_ui:
            self._main_ui.cleanup()
            self._main_ui = None
        
        # 清理所有模块
        self._manager.cleanup_all_modules()

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
    """插件逻辑类 - 轻量级全局逻辑"""

    def __init__(self) -> None:
        """初始化逻辑类"""
        ScriptedLoadableModuleLogic.__init__(self)
        self._config = PluginConfig()
        self._manager = ModuleManager()
        
    def get_module_manager(self) -> ModuleManager:
        """获取模块管理器"""
        return self._manager
    
    def get_plugin_config(self) -> PluginConfig:
        """获取插件配置"""
        return self._config


#
# tavi_analyticsTest
#

class tavi_analyticsTest(ScriptedLoadableModuleTest):
    """测试类"""

    def setUp(self):
        """设置测试环境"""
        slicer.mrmlScene.Clear()
        
        # 重置所有单例
        TAVRStudySession._instance = None
        TAVRStudySession._initialized = False
        ModuleManager._instance = None
        ModuleManager._initialized = False
        PluginConfig._instance = None
        PluginConfig._initialized = False

    def runTest(self):
        """运行测试"""
        self.setUp()
        self.test_plugin_config()
        self.test_module_manager()
        self.test_session_singleton()
        self.test_patient_data()

    def test_plugin_config(self):
        """测试插件配置"""
        config = PluginConfig()
        metadata = config.get_plugin_metadata()
        
        self.assertEqual(metadata.name, "TAVR Analytics")
        self.assertTrue(config.is_module_enabled("module1"))
        
        logging.info("插件配置测试通过")
    
    def test_module_manager(self):
        """测试模块管理器"""
        manager = ModuleManager()
        session = TAVRStudySession()
        
        manager.set_session(session)
        
        # 测试模块注册
        from module1.module1_adapter import Module1Adapter
        module_info = ModuleInfo("test_module", "测试模块", Module1Adapter)
        manager.register_module(module_info)
        
        available_modules = manager.get_available_modules()
        self.assertIn("test_module", available_modules)
        
        logging.info("模块管理器测试通过")

    def test_session_singleton(self):
        """测试会话单例模式"""
        session1 = TAVRStudySession()
        session2 = TAVRStudySession()
        self.assertEqual(session1, session2)
        
        logging.info("会话单例测试通过")

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

        logging.info("患者数据测试通过")
        self.delayDisplay("所有测试通过")
