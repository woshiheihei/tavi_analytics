"""
模块二界面组件
负责引导式分割与解剖标志点定义的用户界面
"""

import logging
from typing import Optional
import qt
import slicer

# 导入核心模块
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from .module2_logic import Module2Logic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from module2.module2_logic import Module2Logic


class Module2Widget(qt.QWidget):
    """
    模块二界面组件
    
    提供引导式分割与解剖标志点定义的用户界面，包括：
    - 分割工具界面
    - 标志点定义界面
    - 进度显示
    - 结果预览
    """

    def __init__(self, session: TAVRStudySession, logic: Optional[Module2Logic] = None, parent=None):
        """
        初始化模块二界面组件
        
        Args:
            session: TAVR研究会话对象
            logic: 模块二业务逻辑对象
            parent: 父组件
        """
        super().__init__(parent)
        
        self.session = session
        self.logic = logic or Module2Logic()
        
        # 设置组件属性
        self.setObjectName("Module2Widget")
        
        # 创建界面
        self._setup_ui()
        
        logging.info("Module2Widget 初始化完成")

    def _setup_ui(self):
        """设置用户界面"""
        # 创建主布局
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        self._create_title_section(layout)
        
        # 添加分割工具区域
        self._create_segmentation_section(layout)
        
        # 添加标志点定义区域
        self._create_landmarks_section(layout)
        
        # 添加进度显示区域
        self._create_progress_section(layout)
        
        # 添加控制按钮区域
        self._create_controls_section(layout)
        
        # 添加弹性空间
        layout.addStretch()

    def _create_title_section(self, layout):
        """创建标题区域"""
        title_label = qt.QLabel("模块二：引导式分割与解剖标志点定义")
        title_label.setAlignment(qt.Qt.AlignCenter)
        title_label.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title_label)
        
        # 添加描述
        description_label = qt.QLabel(
            "本模块提供主动脉根部和瓣膜支架的半自动分割功能，\n"
            "以及关键解剖标志点的定义和管理工具。"
        )
        description_label.setAlignment(qt.Qt.AlignCenter)
        description_label.setStyleSheet(StyleManager.get_label_style("muted"))
        layout.addWidget(description_label)

    def _create_segmentation_section(self, layout):
        """创建分割工具区域"""
        # 创建分组框
        segmentation_group = qt.QGroupBox("分割工具")
        segmentation_group.setStyleSheet(StyleManager.get_card_style())
        segmentation_layout = qt.QVBoxLayout(segmentation_group)
        
        # 主动脉根部分割按钮
        aortic_root_button = qt.QPushButton("开始主动脉根部分割")
        aortic_root_button.setStyleSheet(StyleManager.get_button_style("primary"))
        aortic_root_button.clicked.connect(self._on_start_aortic_root_segmentation)
        segmentation_layout.addWidget(aortic_root_button)
        
        # 瓣膜支架分割按钮
        valve_stent_button = qt.QPushButton("开始瓣膜支架分割")
        valve_stent_button.setStyleSheet(StyleManager.get_button_style("secondary"))
        valve_stent_button.clicked.connect(self._on_start_valve_stent_segmentation)
        segmentation_layout.addWidget(valve_stent_button)
        
        # 分割验证按钮
        validate_button = qt.QPushButton("验证分割结果")
        validate_button.setStyleSheet(StyleManager.get_button_style("outline"))
        validate_button.clicked.connect(self._on_validate_segmentation)
        segmentation_layout.addWidget(validate_button)
        
        layout.addWidget(segmentation_group)

    def _create_landmarks_section(self, layout):
        """创建标志点定义区域"""
        # 创建分组框
        landmarks_group = qt.QGroupBox("解剖标志点定义")
        landmarks_group.setStyleSheet(StyleManager.get_card_style())
        landmarks_layout = qt.QVBoxLayout(landmarks_group)
        
        # 标志点定义按钮
        define_landmarks_button = qt.QPushButton("定义解剖标志点")
        define_landmarks_button.setStyleSheet(StyleManager.get_button_style("primary"))
        define_landmarks_button.clicked.connect(self._on_define_landmarks)
        landmarks_layout.addWidget(define_landmarks_button)
        
        # 标志点列表（占位）
        landmarks_list = qt.QListWidget()
        landmarks_list.setMaximumHeight(100)
        landmarks_list.setStyleSheet(StyleManager.get_input_style())
        landmarks_layout.addWidget(landmarks_list)
        
        # 保存标志点按钮
        save_landmarks_button = qt.QPushButton("保存标志点")
        save_landmarks_button.setStyleSheet(StyleManager.get_button_style("secondary"))
        save_landmarks_button.clicked.connect(self._on_save_landmarks)
        landmarks_layout.addWidget(save_landmarks_button)
        
        layout.addWidget(landmarks_group)

    def _create_progress_section(self, layout):
        """创建进度显示区域"""
        # 创建分组框
        progress_group = qt.QGroupBox("进度状态")
        progress_group.setStyleSheet(StyleManager.get_card_style())
        progress_layout = qt.QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(StyleManager.get_input_style())
        progress_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = qt.QLabel("准备开始分割...")
        self.status_label.setStyleSheet(StyleManager.get_status_indicator_style("default"))
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)

    def _create_controls_section(self, layout):
        """创建控制按钮区域"""
        controls_layout = qt.QHBoxLayout()
        
        # 重置按钮
        reset_button = qt.QPushButton("重置")
        reset_button.setStyleSheet(StyleManager.get_button_style("destructive"))
        reset_button.clicked.connect(self._on_reset)
        controls_layout.addWidget(reset_button)
        
        # 完成按钮
        complete_button = qt.QPushButton("完成模块")
        complete_button.setStyleSheet(StyleManager.get_button_style("primary"))
        complete_button.clicked.connect(self._on_complete_module)
        controls_layout.addWidget(complete_button)
        
        layout.addLayout(controls_layout)

    def _on_start_aortic_root_segmentation(self):
        """开始主动脉根部分割"""
        try:
            self.status_label.setText("正在进行主动脉根部分割...")
            self.progress_bar.setValue(25)
            
            # 调用业务逻辑
            result = self.logic.create_aortic_root_segmentation()
            
            if result is not None:
                self.status_label.setText("主动脉根部分割完成")
                self.progress_bar.setValue(50)
                qt.QMessageBox.information(self, "成功", "主动脉根部分割完成")
            else:
                self.status_label.setText("主动脉根部分割失败")
                qt.QMessageBox.warning(self, "警告", "主动脉根部分割失败，请重试")
                
        except Exception as e:
            logging.error(f"主动脉根部分割出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"分割过程中出错: {str(e)}")

    def _on_start_valve_stent_segmentation(self):
        """开始瓣膜支架分割"""
        try:
            self.status_label.setText("正在进行瓣膜支架分割...")
            self.progress_bar.setValue(50)
            
            # 占位实现
            qt.QMessageBox.information(self, "提示", "瓣膜支架分割功能正在开发中")
            
        except Exception as e:
            logging.error(f"瓣膜支架分割出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"分割过程中出错: {str(e)}")

    def _on_validate_segmentation(self):
        """验证分割结果"""
        try:
            self.status_label.setText("正在验证分割结果...")
            
            # 调用业务逻辑
            is_valid = self.logic.validate_segmentation_results()
            
            if is_valid:
                self.status_label.setText("分割结果验证通过")
                self.progress_bar.setValue(75)
                qt.QMessageBox.information(self, "成功", "分割结果验证通过")
            else:
                self.status_label.setText("分割结果验证失败")
                qt.QMessageBox.warning(self, "警告", "分割结果验证失败，请检查并重新分割")
                
        except Exception as e:
            logging.error(f"分割验证出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"验证过程中出错: {str(e)}")

    def _on_define_landmarks(self):
        """定义解剖标志点"""
        try:
            self.status_label.setText("正在定义解剖标志点...")
            
            # 调用业务逻辑
            result = self.logic.define_anatomical_landmarks()
            
            if result:
                self.status_label.setText("解剖标志点定义完成")
                self.progress_bar.setValue(90)
                qt.QMessageBox.information(self, "成功", "解剖标志点定义完成")
            else:
                self.status_label.setText("解剖标志点定义失败")
                qt.QMessageBox.warning(self, "警告", "解剖标志点定义失败，请重试")
                
        except Exception as e:
            logging.error(f"标志点定义出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"定义过程中出错: {str(e)}")

    def _on_save_landmarks(self):
        """保存标志点"""
        try:
            # 占位实现
            qt.QMessageBox.information(self, "成功", "标志点已保存")
            self.progress_bar.setValue(100)
            self.status_label.setText("模块二任务完成")
            
        except Exception as e:
            logging.error(f"保存标志点出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"保存过程中出错: {str(e)}")

    def _on_reset(self):
        """重置模块"""
        try:
            reply = qt.QMessageBox.question(
                self, "确认重置",
                "确定要重置模块二的所有数据吗？\n这将清除所有分割结果和标志点。",
                qt.QMessageBox.Yes | qt.QMessageBox.No,
                qt.QMessageBox.No
            )
            
            if reply == qt.QMessageBox.Yes:
                self.logic.reset_segmentation_data()
                self.progress_bar.setValue(0)
                self.status_label.setText("准备开始分割...")
                qt.QMessageBox.information(self, "成功", "模块数据已重置")
                
        except Exception as e:
            logging.error(f"重置模块出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"重置过程中出错: {str(e)}")

    def _on_complete_module(self):
        """完成模块"""
        try:
            # 检查模块完成状态
            progress = self.logic.get_segmentation_progress()
            
            if progress.get('overall_progress', 0) >= 100:
                qt.QMessageBox.information(self, "成功", "模块二任务已完成！")
            else:
                qt.QMessageBox.warning(self, "提示", "请完成所有分割和标志点定义任务后再点击完成")
                
        except Exception as e:
            logging.error(f"完成模块出错: {e}")
            qt.QMessageBox.critical(self, "错误", f"完成过程中出错: {str(e)}")

    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
        if self.logic:
            self.logic.session = session

    def on_activated(self):
        """模块激活时调用"""
        logging.info("模块二已激活")
        self.status_label.setText("模块二已激活，准备开始分割...")

    def on_deactivated(self):
        """模块停用时调用"""
        logging.info("模块二已停用")

    def cleanup(self):
        """清理资源"""
        logging.info("模块二界面清理完成")
