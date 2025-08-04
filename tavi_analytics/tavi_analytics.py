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
    from module1.data_loading_dialog import DataLoadingDialog


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
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self.session = TAVRStudySession()
        self.valve_config = {}
        self.data_loading_dialog = None
        
    def setup(self) -> None:
        """设置界面"""
        ScriptedLoadableModuleWidget.setup(self)
        
        # 加载简单的UI文件作为容器
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/tavi_analytics.ui"))
        self.layout.addWidget(uiWidget)
        
        # 创建逻辑类
        self.logic = tavi_analyticsLogic()
        
        # 加载瓣膜配置
        self.load_valve_config()
        
        # 创建主界面
        self.create_main_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 检查场景中是否已有序列数据，如果有则重新处理DICOM元数据
        self.check_and_process_existing_sequences()

    def load_valve_config(self):
        """加载瓣膜配置文件"""
        self.valve_config = ConfigManager.load_valve_config()

    def create_main_ui(self):
        """创建主界面"""
        # 状态显示区域
        status_group = qt.QGroupBox("当前状态")
        status_layout = qt.QVBoxLayout(status_group)
        
        self.status_label = qt.QLabel("未配置数据")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; }")
        status_layout.addWidget(self.status_label)
        
        # 操作按钮区域
        button_layout = qt.QHBoxLayout()
        
        self.setup_data_button = qt.QPushButton("数据导入与配置")
        self.setup_data_button.setStyleSheet("QPushButton { font-size: 16px; padding: 15px; background-color: #2196F3; color: white; }")
        self.setup_data_button.clicked.connect(self.show_data_loading_dialog)
        button_layout.addWidget(self.setup_data_button)
        
        # 心动周期管理面板
        self.create_cardiac_cycle_section()
        
        # 添加到主布局
        self.layout.addWidget(status_group)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.cycle_management_widget)
        self.layout.addStretch()
        
        # 初始更新状态
        self.update_status_display()

    def show_data_loading_dialog(self):
        """显示数据加载对话框"""
        dialog = DataLoadingDialog(parent=self.parent, session=self.session, valve_config=self.valve_config, logic=self.logic)
        
        if dialog.exec_() == qt.QDialog.Accepted:
            # 用户确认了配置，激活心动周期管理
            self.activate_cardiac_cycle_management()
            self.update_status_display()

    def update_status_display(self):
        """更新状态显示"""
        if self.session.is_ready():
            patient_data = self.session.get_patient_data()
            valve_info = self.session.get_selected_valve()
            
            status_text = f"""
<b>数据已配置完成</b><br/>
<b>患者ID:</b> {patient_data.patientID}<br/>
<b>瓣膜:</b> {valve_info['brand']} - {valve_info['model']}<br/>
<b>序列:</b> {self.session.get_volume_sequence_node().GetName() if self.session.get_volume_sequence_node() else '未知'}
"""
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #e8f5e8; border: 1px solid #4CAF50; }")
            self.setup_data_button.setText("重新配置数据")
        else:
            self.status_label.setText("请点击下方按钮开始数据导入与配置")
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; }")
            self.setup_data_button.setText("数据导入与配置")

    def create_patient_info_section(self, parent_layout):
        """创建患者信息输入区域"""
        # 这个方法已经移动到DataLoadingDialog中，这里保留为空以避免错误
        pass

    def create_cardiac_cycle_section(self):
        """创建心动周期管理区域"""
        # 心动周期管理折叠面板
        self.cycle_management_widget = qt.QGroupBox("心动周期管理")
        self.cycle_management_widget.setVisible(False)  # 初始隐藏
        
        cycle_layout = qt.QVBoxLayout(self.cycle_management_widget)
        
        # 时相百分比显示
        self.phase_percent_label = qt.QLabel("当前时相: 0.0%")
        self.phase_percent_label.setAlignment(qt.Qt.AlignCenter)
        self.phase_percent_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 10px; }")
        cycle_layout.addWidget(self.phase_percent_label)
        
        # Series Description 显示
        self.series_description_label = qt.QLabel("序列描述: 未加载")
        self.series_description_label.setAlignment(qt.Qt.AlignCenter)
        self.series_description_label.setStyleSheet("QLabel { font-size: 14px; margin: 5px; padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; }")
        self.series_description_label.setWordWrap(True)  # 允许文本换行
        cycle_layout.addWidget(self.series_description_label)
        
        # 心动周期时间轴滑块
        self.timeline_slider = qt.QSlider(qt.Qt.Horizontal)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.valueChanged.connect(self.on_timeline_slider_changed)
        cycle_layout.addWidget(self.timeline_slider)
        
        # 时相标记按钮
        button_layout = qt.QHBoxLayout()
        
        self.mark_end_diastole_button = qt.QPushButton("标记舒张末期")
        self.mark_end_diastole_button.setEnabled(False)
        self.mark_end_diastole_button.setStyleSheet("QPushButton { padding: 8px; background-color: #FF9800; color: white; }")
        self.mark_end_diastole_button.clicked.connect(lambda: self.mark_phase('end_diastole'))
        button_layout.addWidget(self.mark_end_diastole_button)
        
        self.mark_end_systole_button = qt.QPushButton("标记收缩末期")
        self.mark_end_systole_button.setEnabled(False)
        self.mark_end_systole_button.setStyleSheet("QPushButton { padding: 8px; background-color: #9C27B0; color: white; }")
        self.mark_end_systole_button.clicked.connect(lambda: self.mark_phase('end_systole'))
        button_layout.addWidget(self.mark_end_systole_button)
        
        cycle_layout.addLayout(button_layout)
        
        # 已标记时相显示
        marked_phases_layout = qt.QVBoxLayout()
        self.end_diastole_label = qt.QLabel("舒张末期: 未标记")
        self.end_diastole_label.setStyleSheet("QLabel { padding: 5px; background-color: #fff3e0; border: 1px solid #ff9800; }")
        self.end_diastole_label.setWordWrap(True)  # 允许文本换行
        
        self.end_systole_label = qt.QLabel("收缩末期: 未标记")
        self.end_systole_label.setStyleSheet("QLabel { padding: 5px; background-color: #f3e5f5; border: 1px solid #9c27b0; }")
        self.end_systole_label.setWordWrap(True)  # 允许文本换行
        
        marked_phases_layout.addWidget(self.end_diastole_label)
        marked_phases_layout.addWidget(self.end_systole_label)
        cycle_layout.addLayout(marked_phases_layout)

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
        self.update_status_display()
        self.cycle_management_widget.setVisible(False)

    def check_and_process_existing_sequences(self):
        """检查并处理现有的序列数据"""
        try:
            # 查找场景中的序列节点
            sequence_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceNode')
            browser_nodes = slicer.util.getNodesByClass('vtkMRMLSequenceBrowserNode')
            
            if sequence_nodes and browser_nodes:
                print("DEBUG: 发现现有序列数据，正在重新处理DICOM元数据...")
                
                # 选择第一个序列节点
                sequence_node = sequence_nodes[0]
                browser_node = browser_nodes[0]
                
                # 更新会话
                self.session.volume_sequence_node_id = sequence_node.GetID()
                self.session.sequence_browser_node_id = browser_node.GetID()
                
                # 重新处理DICOM元数据
                self.logic.preserve_dicom_metadata(sequence_node)
                
                # 更新状态显示
                self.update_status_display()
                
                print("DEBUG: 完成现有序列数据的DICOM元数据处理")
                
        except Exception as e:
            print(f"DEBUG: 处理现有序列数据时出错: {e}")
            import traceback
            traceback.print_exc()

    def on_load_data_clicked(self):
        """处理加载数据按钮点击（已废弃，保留用于兼容性）"""
        pass

    def on_valve_brand_changed(self, brand):
        """处理瓣膜品牌选择变化（已废弃，保留用于兼容性）"""
        pass

    def check_confirm_button_state(self):
        """检查确认按钮状态（已废弃，保留用于兼容性）"""
        pass

    def on_confirm_clicked(self):
        """处理确认按钮点击（已废弃，保留用于兼容性）"""
        pass

    def save_patient_data_to_session(self):
        """保存患者信息到会话（已废弃，保留用于兼容性）"""
        pass

    def activate_cardiac_cycle_management(self):
        """激活心动周期管理"""
        sequence_node = self.session.get_volume_sequence_node()
        browser_node = self.session.get_sequence_browser_node()
        
        if sequence_node and browser_node:
            # 设置滑块范围
            num_frames = sequence_node.GetNumberOfDataNodes()
            self.timeline_slider.setMaximum(num_frames - 1)
            self.timeline_slider.setEnabled(True)
            
            # 启用标记按钮
            self.mark_end_diastole_button.setEnabled(True)
            self.mark_end_systole_button.setEnabled(True)
            
            # 显示管理面板
            self.cycle_management_widget.setVisible(True)
            
            # 初始化当前帧
            self.on_timeline_slider_changed(0)

    def update_sequence_info(self):
        """更新序列信息显示（已废弃，保留用于兼容性）"""
        pass

    def parse_dicom_metadata(self):
        """解析DICOM元数据并填充患者信息（已废弃，保留用于兼容性）"""
        pass

    def update_patient_info_ui(self):
        """更新患者信息界面（已废弃，保留用于兼容性）"""
        pass

    def on_timeline_slider_changed(self, value):
        """处理时间轴滑块变化"""
        browser_node = self.session.get_sequence_browser_node()
        sequence_node = self.session.get_volume_sequence_node()
        
        if browser_node and sequence_node:
            # 设置当前帧
            browser_node.SetSelectedItemNumber(value)
            
            # 获取并显示时相百分比
            try:
                index_value = sequence_node.GetNthIndexValue(value)
                phase_percent = float(index_value)
                self.phase_percent_label.setText(f"当前时相: {phase_percent:.1f}%")
            except:
                self.phase_percent_label.setText(f"当前时相: 帧 {value}")

            # 获取并显示Series Description
            series_desc = self.session.get_current_frame_series_description()
            self.series_description_label.setText(f"序列描述: {series_desc}")

    def mark_phase(self, phase_name):
        """标记关键时相"""
        browser_node = self.session.get_sequence_browser_node()
        sequence_node = self.session.get_volume_sequence_node()
        
        if browser_node and sequence_node:
            frame_index = browser_node.GetSelectedItemNumber()
            
            try:
                index_value = sequence_node.GetNthIndexValue(frame_index)
                phase_percent = float(index_value)
            except:
                phase_percent = 0.0
            
            # 获取当前帧的序列描述信息
            series_description = self.session.get_current_frame_series_description()
            
            # 保存到会话
            self.session.mark_phase(phase_name, frame_index, phase_percent, series_description)
            
            # 更新界面显示
            self.update_phase_labels()

    def update_phase_labels(self):
        """更新时相标记显示"""
        end_diastole = self.session.get_marked_phase('end_diastole')
        end_systole = self.session.get_marked_phase('end_systole')
        
        if end_diastole and end_diastole['frame_index'] is not None:
            phase_text = f"舒张末期: 已标记 @ {end_diastole['phase_percent']:.1f}%"
            if end_diastole.get('series_description'):
                phase_text += f"\n序列描述: {end_diastole['series_description']}"
            self.end_diastole_label.setText(phase_text)
        else:
            self.end_diastole_label.setText("舒张末期: 未标记")
            
        if end_systole and end_systole['frame_index'] is not None:
            phase_text = f"收缩末期: 已标记 @ {end_systole['phase_percent']:.1f}%"
            if end_systole.get('series_description'):
                phase_text += f"\n序列描述: {end_systole['series_description']}"
            self.end_systole_label.setText(phase_text)
        else:
            self.end_systole_label.setText("收缩末期: 未标记")

    def cleanup(self) -> None:
        """清理资源"""
        self.removeObservers()

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
