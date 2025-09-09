"""
瓣膜植入深度子模块（Module4）

功能：
- 提供“测量工具”按钮，调起 3D Slicer Markups 的长度（线段）测量工具。
- 引导用户在 MPR 中放置两个点完成长度标注，然后将结果（单位 mm）手动填写到 NC/LC/RC 输入框。
"""
import logging
from typing import Optional, Dict, Any
import qt

try:
    from ..core.session import TAVRStudySession
    from ..ui.styles import StyleManager
    from ..utils.layout_manager import LayoutManager
    from ..widgets.section_card import SectionCard
    from .module4_logic import Module4Logic
except ImportError:
    # 兼容独立运行
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession
    from ui.styles import StyleManager
    from utils.layout_manager import LayoutManager
    from widgets.section_card import SectionCard
    from module4_logic import Module4Logic


class ValveImplantDepthWidget(qt.QWidget):
    """瓣膜植入深度测量与记录界面"""

    valuesChanged = qt.Signal(dict)

    def __init__(self, session: Optional[TAVRStudySession] = None, logic: Optional[Module4Logic] = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.logic = logic
        self.setObjectName("ValveImplantDepthWidget")
        # runtime state
        self._activeLineNode = None
        self._lineObserverTag = None
        self._interactionNode = None
        self._escShortcut = None
        self._setup_ui()

    # --------------------- UI ---------------------
    def _setup_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 标题
        title = qt.QLabel("瓣膜植入深度")
        title.setAlignment(qt.Qt.AlignCenter)
        title.setStyleSheet(StyleManager.get_label_style("large"))
        layout.addWidget(title)

        # 工具卡片
        tool_card = SectionCard(title="测量工具", icon_text="🧰", variant="dashed", parent=self)
        tool_row = qt.QHBoxLayout()
        self.measure_tool_btn = LayoutManager.create_button_with_style("测量工具", "toolbar", "sm", 28)
        self.measure_tool_btn.clicked.connect(self._on_measure_tool_clicked)
        tool_row.addWidget(self.measure_tool_btn)
        tool_row.addStretch()
        tool_card.add_layout(tool_row)

        tip = qt.QLabel("将启动 Markups 长度测量工具，请在 MPR 中放置两个点完成长度测量，随后将读数填入下方表单。按 ESC 可取消当前测量。")
        tip.setWordWrap(True)
        tip.setStyleSheet(StyleManager.get_label_style("muted"))
        tool_card.add_widget(tip)
        layout.addWidget(tool_card)

        # 结果卡片
        result_card = SectionCard(title="填写结果 (mm)", icon_text="📄", variant="dashed", parent=self)

        form = qt.QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.nc_spin = self._create_mm_spin()
        self.lc_spin = self._create_mm_spin()
        self.rc_spin = self._create_mm_spin()

        form.addWidget(qt.QLabel("NC"), 0, 0)
        form.addWidget(self.nc_spin, 0, 1)
        form.addWidget(qt.QLabel("LC"), 1, 0)
        form.addWidget(self.lc_spin, 1, 1)
        form.addWidget(qt.QLabel("RC"), 2, 0)
        form.addWidget(self.rc_spin, 2, 1)

        # 右侧占位拉伸
        form.setColumnStretch(2, 1)

        # 监听变更
        self.nc_spin.valueChanged.connect(self._emit_values)
        self.lc_spin.valueChanged.connect(self._emit_values)
        self.rc_spin.valueChanged.connect(self._emit_values)

        result_frame = qt.QWidget()
        result_frame.setLayout(form)
        result_card.add_widget(result_frame)
        layout.addWidget(result_card)

        # 状态行
        self.status_label = qt.QLabel("提示：点击“测量工具”后在 MPR 中进行标注并读取数值；按 ESC 可取消当前测量。")
        self.status_label.setStyleSheet(StyleManager.get_label_style("small"))
        layout.addWidget(self.status_label)

        layout.addStretch()

        # ESC 取消快捷键（全局），用于随时终止当前放置
        try:
            self._escShortcut = qt.QShortcut(qt.QKeySequence("Escape"), self)
            self._escShortcut.setContext(qt.Qt.ApplicationShortcut)
            self._escShortcut.activated.connect(self._cancel_measurement)
        except Exception:
            pass

    def _create_mm_spin(self) -> qt.QDoubleSpinBox:
        spin = qt.QDoubleSpinBox()
        spin.setDecimals(1)
        spin.setRange(0.0, 50.0)
        spin.setSingleStep(0.5)
        spin.setSuffix(" mm")
        spin.setFixedHeight(28)
        spin.setMinimumWidth(120)
        return spin

    # --------------------- Actions ---------------------
    def _on_measure_tool_clicked(self):
        """启动 3D Slicer Markups 长度（线段）测量工具，并给出操作提示"""
        try:
            import slicer  # 仅在 Slicer 环境下可用

            # 若上次未完成的测量存在，先移除
            try:
                if getattr(self, "_activeLineNode", None) and self._activeLineNode.GetScene() is slicer.mrmlScene:
                    if self._count_defined_points(self._activeLineNode) < 2:
                        slicer.mrmlScene.RemoveNode(self._activeLineNode)
            except Exception:
                pass

            # 创建线段（长度）节点（本次单次测量）
            line_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode", "植入深度测量")
            try:
                line_node.CreateDefaultDisplayNodes()
            except Exception:
                pass
            self._activeLineNode = line_node

            # 方式一：使用 Markups 逻辑设置活动列表并进入放置模式（非持久，单次测量）
            try:
                markups_logic = slicer.modules.markups.logic()
                if markups_logic:
                    # 确保仅单次放置
                    self._interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                    if self._interactionNode:
                        self._interactionNode.SetPlaceModePersistence(0)
                    markups_logic.SetActiveListID(line_node)
                    markups_logic.StartPlaceMode()
            except Exception:
                pass

            # 方式二（备用）：通过 Selection/Interaction 节点进入放置模式（某些版本更稳定）
            try:
                selection_node = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
                self._interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                if selection_node and self._interactionNode:
                    try:
                        selection_node.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsLineNode")
                    except Exception:
                        pass
                    selection_node.SetActivePlaceNodeID(line_node.GetID())
                    # 非持久化：完成一次放置后自动退出
                    self._interactionNode.SetPlaceModePersistence(0)
                    self._interactionNode.SetCurrentInteractionMode(self._interactionNode.Place)
            except Exception:
                pass

            # 观察点放置，两个点就自动结束本次测量
            try:
                if self._lineObserverTag:
                    try:
                        self._activeLineNode.RemoveObserver(self._lineObserverTag)
                    except Exception:
                        pass
                    self._lineObserverTag = None

                def _on_point_defined(caller, event):
                    try:
                        if self._count_defined_points(caller) >= 2:
                            self._finalize_single_measure()
                    except Exception:
                        pass

                self._lineObserverTag = line_node.AddObserver(slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent, _on_point_defined)
            except Exception:
                pass

            # 友好提示
            self._show_info_dialog(
                "已启用长度测量工具",
                "请在 MPR 中依次点击放置两个点完成长度标注（单位 mm）。\n\n"
                "完成测量后，将读数填入下方 NC/LC/RC。\n\n按下 ESC 可取消本次测量。"
            )
            self._set_status("长度测量工具已启用，在 MPR 中放置两个点以完成标注；按 ESC 可取消。", "info")

        except Exception as e:
            logging.error(f"启动长度测量工具失败: {e}")
            self._set_status(f"无法启动测量工具：{e}", "error")

    # 仅本次放置完成后退出放置模式
    def _finalize_single_measure(self):
        try:
            import slicer
            if self._interactionNode is None:
                self._interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if self._interactionNode:
                self._interactionNode.SetCurrentInteractionMode(self._interactionNode.ViewTransform)
            # 移除观察者
            if self._activeLineNode and self._lineObserverTag:
                try:
                    self._activeLineNode.RemoveObserver(self._lineObserverTag)
                except Exception:
                    pass
                self._lineObserverTag = None
            # 清空引用，结束一次测量
            self._activeLineNode = None
            self._set_status("测量已完成（单次）。如需再次测量，请再次点击“测量工具”。", "success")
        except Exception:
            pass

    def _cancel_measurement(self):
        """按下 ESC 时取消当前单次测量：退出放置模式并移除未完成的线段。"""
        try:
            import slicer
            if self._interactionNode is None:
                self._interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if self._interactionNode:
                self._interactionNode.SetCurrentInteractionMode(self._interactionNode.ViewTransform)
                self._interactionNode.SetPlaceModePersistence(0)

            # 若当前线段未完成（少于 2 个点），从场景移除
            if getattr(self, "_activeLineNode", None) and self._activeLineNode.GetScene() is slicer.mrmlScene:
                if self._count_defined_points(self._activeLineNode) < 2:
                    try:
                        slicer.mrmlScene.RemoveNode(self._activeLineNode)
                    except Exception:
                        pass
            # 清理观察者
            if self._activeLineNode and self._lineObserverTag:
                try:
                    self._activeLineNode.RemoveObserver(self._lineObserverTag)
                except Exception:
                    pass
                self._lineObserverTag = None
            self._activeLineNode = None

            self._set_status("已取消当前测量。", "warning")
        except Exception:
            pass

    def _count_defined_points(self, node) -> int:
        """统计已定义（落点有效）的控制点数量，兼容不同 Slicer 版本。"""
        try:
            # Slicer 5.x 提供该方法
            return int(node.GetNumberOfDefinedControlPoints())
        except Exception:
            try:
                n = int(node.GetNumberOfControlPoints())
                count = 0
                # 回退：认为存在的位置即有效
                for i in range(n):
                    try:
                        # 如果有状态枚举可用，尽量判断为 PositionDefined
                        status = node.GetNthControlPointPositionStatus(i)
                        # 2=Defined，1=Preview（不同版本枚举可能不同，这里尽量只接受已定义）
                        if int(status) == 2:
                            count += 1
                    except Exception:
                        count += 1
                return count
            except Exception:
                return 0

    # --------------------- Helpers ---------------------
    def _show_info_dialog(self, title: str, text: str):
        msg = qt.QMessageBox(self)
        msg.setIcon(qt.QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(qt.QMessageBox.Ok)
        msg.exec_()

    def _set_status(self, message: str, status_type: str = "info"):
        color_map = {
            "success": "#059669",
            "error": "#dc2626",
            "warning": "#d97706",
            "info": "#6b7280"
        }
        color = color_map.get(status_type, "#6b7280")
        self.status_label.setStyleSheet(f"QLabel {{ color: {color}; font-size: 11px; }}")
        self.status_label.setText(message)

    def _emit_values(self):
        vals = self.get_values()
        self.valuesChanged.emit(vals)
        try:
            if self.session:
                # 写入会话以便报告使用
                self.session.set_implant_depth({
                    'NC': vals.get('NC'),
                    'LC': vals.get('LC'),
                    'RC': vals.get('RC'),
                })
        except Exception:
            pass

    # --------------------- Public API ---------------------
    def get_values(self) -> Dict[str, Any]:
        def _spin_value(spin: qt.QDoubleSpinBox) -> float:
            """获取数值，兼容 PyQt/PySide 在不同 Slicer 版本中 .value 可能为属性或方法的差异。"""
            try:
                vattr = getattr(spin, 'value', None)
                if callable(vattr):
                    return float(vattr())
                if vattr is not None:
                    return float(vattr)
            except Exception:
                pass
            # 兜底：尝试 text 再解析数字
            try:
                txt = spin.text if hasattr(spin, 'text') else None
                if callable(txt):
                    txt = txt()
                if isinstance(txt, str):
                    # 去掉可能的后缀，如 " mm"
                    txt = txt.replace('mm', '').strip()
                    return float(txt)
            except Exception:
                pass
            # 最后退回 0.0
            return 0.0

        return {
            "NC": _spin_value(self.nc_spin),
            "LC": _spin_value(self.lc_spin),
            "RC": _spin_value(self.rc_spin),
            "unit": "mm"
        }

    def set_values(self, nc: float = 0.0, lc: float = 0.0, rc: float = 0.0):
        # 避免 signal 风暴
        try:
            self.nc_spin.blockSignals(True)
            self.lc_spin.blockSignals(True)
            self.rc_spin.blockSignals(True)
            self.nc_spin.setValue(nc)
            self.lc_spin.setValue(lc)
            self.rc_spin.setValue(rc)
        finally:
            self.nc_spin.blockSignals(False)
            self.lc_spin.blockSignals(False)
            self.rc_spin.blockSignals(False)
        self._emit_values()

    def set_session(self, session: TAVRStudySession):
        self.session = session
        # 从会话预填值（若存在）
        try:
            if self.session and hasattr(self.session, 'get_implant_depth'):
                d = self.session.get_implant_depth() or {}
                nc = d.get('NC') or 0.0
                lc = d.get('LC') or 0.0
                rc = d.get('RC') or 0.0
                self.set_values(float(nc or 0.0), float(lc or 0.0), float(rc or 0.0))
        except Exception:
            pass

    def set_logic(self, logic: Module4Logic):
        self.logic = logic

    def on_activated(self):
        pass

    def on_deactivated(self):
        # 离开页面时，如果还在放置或有未完成的线段，则取消本次测量
        self._cancel_measurement()

    def cleanup(self):
        # 模块销毁时也做一次清理
        self._cancel_measurement()
