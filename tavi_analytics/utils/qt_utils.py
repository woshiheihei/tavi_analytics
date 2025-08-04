"""
Qt工具函数模块

提供Qt控件的安全访问、样式设置、对话框等通用功能。
"""

import logging
from typing import Any, Optional, Union

import qt


class QtUtils:
    """Qt工具类"""

    @staticmethod
    def get_widget_text(widget, method_name: str = 'text') -> str:
        """安全获取Qt部件的文本，兼容属性和方法访问方式
        
        Args:
            widget: Qt控件
            method_name: 方法或属性名称
            
        Returns:
            控件文本，失败时返回空字符串
        """
        try:
            # 尝试方法调用
            method = getattr(widget, method_name, None)
            if callable(method):
                return method()
            # 尝试属性访问
            elif method is not None:
                return str(method)
            else:
                return ""
        except Exception as e:
            logging.debug(f"Failed to get widget text: {e}")
            return ""

    @staticmethod
    def get_widget_value(widget, method_name: str = 'value') -> Any:
        """安全获取Qt部件的值，兼容属性和方法访问方式
        
        Args:
            widget: Qt控件
            method_name: 方法或属性名称
            
        Returns:
            控件值，失败时返回None
        """
        try:
            # 尝试方法调用
            method = getattr(widget, method_name, None)
            if callable(method):
                return method()
            # 尝试属性访问
            elif method is not None:
                return method
            else:
                return None
        except Exception as e:
            logging.debug(f"Failed to get widget value: {e}")
            return None

    @staticmethod
    def set_widget_text(widget, text: str, method_name: str = 'setText') -> bool:
        """安全设置Qt部件的文本
        
        Args:
            widget: Qt控件
            text: 要设置的文本
            method_name: 方法名称
            
        Returns:
            设置是否成功
        """
        try:
            method = getattr(widget, method_name, None)
            if callable(method):
                method(text)
                return True
            else:
                return False
        except Exception as e:
            logging.debug(f"Failed to set widget text: {e}")
            return False

    @staticmethod
    def set_widget_value(widget, value: Any, method_name: str = 'setValue') -> bool:
        """安全设置Qt部件的值
        
        Args:
            widget: Qt控件
            value: 要设置的值
            method_name: 方法名称
            
        Returns:
            设置是否成功
        """
        try:
            method = getattr(widget, method_name, None)
            if callable(method):
                method(value)
                return True
            else:
                return False
        except Exception as e:
            logging.debug(f"Failed to set widget value: {e}")
            return False

    @staticmethod
    def create_styled_button(text: str, style_class: str = "primary") -> qt.QPushButton:
        """创建带样式的按钮
        
        Args:
            text: 按钮文本
            style_class: 样式类别 ("primary", "secondary", "success", "warning", "danger")
            
        Returns:
            样式化的按钮
        """
        button = qt.QPushButton(text)
        
        # 定义样式映射
        styles = {
            "primary": "QPushButton { background-color: #2196F3; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #1976D2; }",
            "secondary": "QPushButton { background-color: #9E9E9E; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #757575; }",
            "success": "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #388E3C; }",
            "warning": "QPushButton { background-color: #FF9800; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #F57C00; }",
            "danger": "QPushButton { background-color: #F44336; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #D32F2F; }"
        }
        
        style = styles.get(style_class, styles["primary"])
        button.setStyleSheet(style)
        
        return button

    @staticmethod
    def create_info_label(text: str, style_class: str = "normal") -> qt.QLabel:
        """创建信息标签
        
        Args:
            text: 标签文本
            style_class: 样式类别 ("normal", "title", "subtitle", "info", "warning", "error")
            
        Returns:
            样式化的标签
        """
        label = qt.QLabel(text)
        label.setWordWrap(True)
        
        # 定义样式映射
        styles = {
            "normal": "QLabel { padding: 5px; }",
            "title": "QLabel { font-size: 18px; font-weight: bold; margin: 10px; }",
            "subtitle": "QLabel { font-size: 16px; font-weight: bold; margin: 5px; }",
            "info": "QLabel { background-color: #E3F2FD; color: #1976D2; padding: 10px; border: 1px solid #BBDEFB; border-radius: 4px; }",
            "warning": "QLabel { background-color: #FFF3E0; color: #F57C00; padding: 10px; border: 1px solid #FFCC02; border-radius: 4px; }",
            "error": "QLabel { background-color: #FFEBEE; color: #D32F2F; padding: 10px; border: 1px solid #FFCDD2; border-radius: 4px; }"
        }
        
        style = styles.get(style_class, styles["normal"])
        label.setStyleSheet(style)
        
        return label

    @staticmethod
    def create_group_box(title: str, layout_type: str = "vertical") -> qt.QGroupBox:
        """创建分组框
        
        Args:
            title: 分组框标题
            layout_type: 布局类型 ("vertical", "horizontal", "form", "grid")
            
        Returns:
            分组框及其布局
        """
        group_box = qt.QGroupBox(title)
        
        # 创建布局
        if layout_type == "vertical":
            layout = qt.QVBoxLayout(group_box)
        elif layout_type == "horizontal":
            layout = qt.QHBoxLayout(group_box)
        elif layout_type == "form":
            layout = qt.QFormLayout(group_box)
        elif layout_type == "grid":
            layout = qt.QGridLayout(group_box)
        else:
            layout = qt.QVBoxLayout(group_box)
        
        return group_box

    @staticmethod
    def show_message_box(parent, title: str, message: str, box_type: str = "information") -> int:
        """显示消息框
        
        Args:
            parent: 父控件
            title: 标题
            message: 消息内容
            box_type: 消息框类型 ("information", "warning", "critical", "question")
            
        Returns:
            用户响应
        """
        try:
            if box_type == "information":
                return qt.QMessageBox.information(parent, title, message)
            elif box_type == "warning":
                return qt.QMessageBox.warning(parent, title, message)
            elif box_type == "critical":
                return qt.QMessageBox.critical(parent, title, message)
            elif box_type == "question":
                return qt.QMessageBox.question(parent, title, message, 
                                              qt.QMessageBox.Yes | qt.QMessageBox.No)
            else:
                return qt.QMessageBox.information(parent, title, message)
                
        except Exception as e:
            logging.error(f"Failed to show message box: {e}")
            return qt.QMessageBox.NoButton

    @staticmethod
    def create_date_input(default_date=None) -> qt.QDateEdit:
        """创建日期输入控件
        
        Args:
            default_date: 默认日期，如果为None则使用当前日期
            
        Returns:
            日期输入控件
        """
        date_edit = qt.QDateEdit()
        date_edit.setCalendarPopup(True)
        
        if default_date:
            date_edit.setDate(default_date)
        else:
            date_edit.setDate(qt.QDate.currentDate())
        
        return date_edit

    @staticmethod
    def create_number_input(min_value: float = 0, max_value: float = 100, 
                           decimals: int = 0, default_value: float = 0) -> Union[qt.QSpinBox, qt.QDoubleSpinBox]:
        """创建数字输入控件
        
        Args:
            min_value: 最小值
            max_value: 最大值
            decimals: 小数位数，0表示整数
            default_value: 默认值
            
        Returns:
            数字输入控件
        """
        if decimals == 0:
            spin_box = qt.QSpinBox()
            spin_box.setMinimum(int(min_value))
            spin_box.setMaximum(int(max_value))
            spin_box.setValue(int(default_value))
        else:
            spin_box = qt.QDoubleSpinBox()
            spin_box.setMinimum(min_value)
            spin_box.setMaximum(max_value)
            spin_box.setDecimals(decimals)
            spin_box.setValue(default_value)
        
        return spin_box

    @staticmethod
    def create_combo_box(items: list, default_index: int = 0, editable: bool = False) -> qt.QComboBox:
        """创建下拉选择框
        
        Args:
            items: 选项列表
            default_index: 默认选择索引
            editable: 是否可编辑
            
        Returns:
            下拉选择框
        """
        combo_box = qt.QComboBox()
        combo_box.addItems(items)
        combo_box.setEditable(editable)
        
        if 0 <= default_index < len(items):
            combo_box.setCurrentIndex(default_index)
        
        return combo_box

    @staticmethod
    def create_text_input(placeholder: str = "", multiline: bool = False) -> Union[qt.QLineEdit, qt.QTextEdit]:
        """创建文本输入控件
        
        Args:
            placeholder: 占位符文本
            multiline: 是否多行
            
        Returns:
            文本输入控件
        """
        if multiline:
            text_edit = qt.QTextEdit()
            text_edit.setPlaceholderText(placeholder)
            return text_edit
        else:
            line_edit = qt.QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            return line_edit

    @staticmethod
    def center_widget_on_parent(widget, parent):
        """将控件居中显示在父控件上
        
        Args:
            widget: 要居中的控件
            parent: 父控件
        """
        try:
            if parent:
                parent_geometry = parent.geometry()
                widget_geometry = widget.geometry()
                
                x = parent_geometry.x() + (parent_geometry.width() - widget_geometry.width()) // 2
                y = parent_geometry.y() + (parent_geometry.height() - widget_geometry.height()) // 2
                
                widget.move(x, y)
        except Exception as e:
            logging.debug(f"Failed to center widget: {e}")

    @staticmethod
    def set_widget_enabled_state(widgets: list, enabled: bool):
        """批量设置控件的启用状态
        
        Args:
            widgets: 控件列表
            enabled: 启用状态
        """
        for widget in widgets:
            try:
                widget.setEnabled(enabled)
            except Exception as e:
                logging.debug(f"Failed to set widget enabled state: {e}")

    @staticmethod
    def clear_layout(layout):
        """清空布局中的所有控件
        
        Args:
            layout: 要清空的布局
        """
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    QtUtils.clear_layout(child.layout())
        except Exception as e:
            logging.error(f"Failed to clear layout: {e}")

    @staticmethod
    def connect_widget_signal(widget, signal_name: str, slot):
        """安全连接控件信号
        
        Args:
            widget: 控件
            signal_name: 信号名称
            slot: 槽函数
            
        Returns:
            连接是否成功
        """
        try:
            signal = getattr(widget, signal_name, None)
            if signal and hasattr(signal, 'connect'):
                signal.connect(slot)
                return True
            else:
                logging.warning(f"Signal {signal_name} not found in widget")
                return False
        except Exception as e:
            logging.error(f"Failed to connect signal {signal_name}: {e}")
            return False
