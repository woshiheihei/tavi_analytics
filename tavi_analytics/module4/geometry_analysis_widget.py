"""
模块四几何形态分析界面组件

瓣膜支架几何形态评估相关分析的标准化用户界面框架，包含：
- Inflow 分析界面
- Nadir 分析界面
- Commissure Level 分析界面
"""
import logging
from typing import Optional, Dict, Any
import qt

# 轻量依赖，仅在需要时注入session与logic
try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager, ComponentStyleFactory
    from ..utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from .geometry_analysis_logic import InflowAnalysisLogic, NadirAnalysisLogic, CommissureLevelAnalysisLogic
except ImportError:
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    # 添加父目录和当前目录到sys.path
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager, ComponentStyleFactory
    from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
    from geometry_analysis_logic import InflowAnalysisLogic, NadirAnalysisLogic, CommissureLevelAnalysisLogic


class BaseGeometryAnalysisWidget(qt.QWidget):
    """几何形态分析界面基类 - 标准化接口"""
    
    # 状态改变信号
    statusChanged = qt.Signal(dict)
    
    def __init__(self, analysis_type: str, session: TAVRStudySession, parent=None):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.session = session
        self.setObjectName(f"{analysis_type}GeometryAnalysisWidget")
        logging.info(f"{analysis_type}几何形态分析界面初始化")
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果 - 子类应该实现"""
        return {'analysis_type': self.analysis_type, 'status': '基类默认实现'}
    
    def reset_analysis(self):
        """重置分析 - 子类应该实现"""
        logging.info(f"{self.analysis_type}几何形态分析重置 - 基类默认实现")
    
    def set_session(self, session: TAVRStudySession):
        """设置会话对象"""
        self.session = session
    
    def on_activated(self):
        """激活时的回调"""
        logging.info(f"{self.analysis_type}几何形态分析界面激活")
    
    def on_deactivated(self):
        """停用时的回调"""
        logging.info(f"{self.analysis_type}几何形态分析界面停用")
    
    def cleanup(self):
        """清理资源"""
        logging.info(f"{self.analysis_type}几何形态分析界面清理完成")
    
    def _emit_status_changed(self):
        """发出状态改变信号"""
        results = self.get_analysis_results()
        self.statusChanged.emit(results)


class InflowAnalysisWidget(BaseGeometryAnalysisWidget):
    """Inflow 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[InflowAnalysisLogic] = None, parent=None):
        super().__init__("Inflow", session, parent)
        self.logic = logic or InflowAnalysisLogic()
        self.logic.set_session(session)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置Inflow分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("Inflow 流入口几何形态分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #e8f4f8;
                padding: 6px 12px;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 描述
        description = qt.QLabel("分析瓣膜支架流入口的几何形态参数")
        description.setStyleSheet(StyleManager.get_label_style("small"))
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # 分析控制面板
        control_frame = LayoutManager.create_section_frame("分析控制")
        control_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, control_frame)
        
        # 分析按钮
        self.analyze_btn = LayoutManager.create_button_with_style(
            "开始 Inflow 分析", "primary", "default", 40
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        control_layout.addWidget(self.analyze_btn)
        
        # 重置按钮
        self.reset_btn = LayoutManager.create_button_with_style(
            "重置分析", "secondary", "default", 40
        )
        self.reset_btn.clicked.connect(self._on_reset)
        control_layout.addWidget(self.reset_btn)
        
        main_layout.addWidget(control_frame)
        
        # 结果显示面板
        results_frame = LayoutManager.create_section_frame("分析结果")
        results_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, results_frame)
        
        self.results_label = qt.QLabel("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        results_layout.addWidget(self.results_label)
        
        main_layout.addWidget(results_frame)
        main_layout.addStretch()
    
    def _on_analyze(self):
        """执行Inflow分析"""
        try:
            self.analyze_btn.setEnabled(False)
            self.analyze_btn.setText("正在分析...")
            
            # 这里添加实际的分析逻辑
            logging.info("开始Inflow几何形态分析")
            
            # 模拟分析结果
            self.results_label.setText("Inflow 分析完成\n- 流入口直径: 23.5 mm\n- 流入口面积: 434.2 mm²\n- 椭圆度: 0.15")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #059669;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #d1fae5;
                    border-radius: 4px;
                    background-color: #ecfdf5;
                }
            """)
            
            self._emit_status_changed()
            
        except Exception as e:
            logging.error(f"Inflow分析失败: {e}")
            self.results_label.setText(f"分析失败: {str(e)}")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #dc2626;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #fecaca;
                    border-radius: 4px;
                    background-color: #fef2f2;
                }
            """)
        finally:
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("开始 Inflow 分析")
    
    def _on_reset(self):
        """重置分析"""
        self.reset_analysis()
        self.results_label.setText("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        logging.info("Inflow分析已重置")


class NadirAnalysisWidget(BaseGeometryAnalysisWidget):
    """Nadir 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[NadirAnalysisLogic] = None, parent=None):
        super().__init__("Nadir", session, parent)
        self.logic = logic or NadirAnalysisLogic()
        self.logic.set_session(session)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置Nadir分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("Nadir 最低点几何形态分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #e8f4f8;
                padding: 6px 12px;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 描述
        description = qt.QLabel("分析瓣膜支架最低点的几何形态参数")
        description.setStyleSheet(StyleManager.get_label_style("small"))
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # 分析控制面板
        control_frame = LayoutManager.create_section_frame("分析控制")
        control_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, control_frame)
        
        # 分析按钮
        self.analyze_btn = LayoutManager.create_button_with_style(
            "开始 Nadir 分析", "primary", "default", 40
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        control_layout.addWidget(self.analyze_btn)
        
        # 重置按钮
        self.reset_btn = LayoutManager.create_button_with_style(
            "重置分析", "secondary", "default", 40
        )
        self.reset_btn.clicked.connect(self._on_reset)
        control_layout.addWidget(self.reset_btn)
        
        main_layout.addWidget(control_frame)
        
        # 结果显示面板
        results_frame = LayoutManager.create_section_frame("分析结果")
        results_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, results_frame)
        
        self.results_label = qt.QLabel("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        results_layout.addWidget(self.results_label)
        
        main_layout.addWidget(results_frame)
        main_layout.addStretch()
    
    def _on_analyze(self):
        """执行Nadir分析"""
        try:
            self.analyze_btn.setEnabled(False)
            self.analyze_btn.setText("正在分析...")
            
            # 这里添加实际的分析逻辑
            logging.info("开始Nadir几何形态分析")
            
            # 模拟分析结果
            self.results_label.setText("Nadir 分析完成\n- 最低点高度: 12.3 mm\n- 瓣叶下陷深度: 2.1 mm\n- 对称性指数: 0.92")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #059669;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #d1fae5;
                    border-radius: 4px;
                    background-color: #ecfdf5;
                }
            """)
            
            self._emit_status_changed()
            
        except Exception as e:
            logging.error(f"Nadir分析失败: {e}")
            self.results_label.setText(f"分析失败: {str(e)}")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #dc2626;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #fecaca;
                    border-radius: 4px;
                    background-color: #fef2f2;
                }
            """)
        finally:
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("开始 Nadir 分析")
    
    def _on_reset(self):
        """重置分析"""
        self.reset_analysis()
        self.results_label.setText("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        logging.info("Nadir分析已重置")


class CommissureLevelAnalysisWidget(BaseGeometryAnalysisWidget):
    """Commissure Level 几何形态分析界面"""
    
    def __init__(self, session: TAVRStudySession, logic: Optional[CommissureLevelAnalysisLogic] = None, parent=None):
        super().__init__("CommissureLevel", session, parent)
        self.logic = logic or CommissureLevelAnalysisLogic()
        self.logic.set_session(session)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置Commissure Level分析界面"""
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 标题
        title = qt.QLabel("Commissure Level 联合水平面几何形态分析")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #e8f4f8;
                padding: 6px 12px;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(title)
        
        # 描述
        description = qt.QLabel("分析瓣膜联合处水平面的几何形态参数")
        description.setStyleSheet(StyleManager.get_label_style("small"))
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # 分析控制面板
        control_frame = LayoutManager.create_section_frame("分析控制")
        control_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, control_frame)
        
        # 分析按钮
        self.analyze_btn = LayoutManager.create_button_with_style(
            "开始 Commissure Level 分析", "primary", "default", 40
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        control_layout.addWidget(self.analyze_btn)
        
        # 重置按钮
        self.reset_btn = LayoutManager.create_button_with_style(
            "重置分析", "secondary", "default", 40
        )
        self.reset_btn.clicked.connect(self._on_reset)
        control_layout.addWidget(self.reset_btn)
        
        main_layout.addWidget(control_frame)
        
        # 结果显示面板
        results_frame = LayoutManager.create_section_frame("分析结果")
        results_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, results_frame)
        
        self.results_label = qt.QLabel("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        results_layout.addWidget(self.results_label)
        
        main_layout.addWidget(results_frame)
        main_layout.addStretch()
    
    def _on_analyze(self):
        """执行Commissure Level分析"""
        try:
            self.analyze_btn.setEnabled(False)
            self.analyze_btn.setText("正在分析...")
            
            # 这里添加实际的分析逻辑
            logging.info("开始Commissure Level几何形态分析")
            
            # 模拟分析结果
            self.results_label.setText("Commissure Level 分析完成\n- 联合处高度: 15.8 mm\n- 三联合角度: 120°, 118°, 122°\n- 平面倾斜度: 3.2°")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #059669;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #d1fae5;
                    border-radius: 4px;
                    background-color: #ecfdf5;
                }
            """)
            
            self._emit_status_changed()
            
        except Exception as e:
            logging.error(f"Commissure Level分析失败: {e}")
            self.results_label.setText(f"分析失败: {str(e)}")
            self.results_label.setStyleSheet("""
                QLabel {
                    color: #dc2626;
                    font-size: 14px;
                    padding: 20px;
                    border: 1px solid #fecaca;
                    border-radius: 4px;
                    background-color: #fef2f2;
                }
            """)
        finally:
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("开始 Commissure Level 分析")
    
    def _on_reset(self):
        """重置分析"""
        self.reset_analysis()
        self.results_label.setText("尚未进行分析")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 20px;
                border: 1px dashed #d1d5db;
                border-radius: 4px;
                background-color: #f9fafb;
            }
        """)
        logging.info("Commissure Level分析已重置")