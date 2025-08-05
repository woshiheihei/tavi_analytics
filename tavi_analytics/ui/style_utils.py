"""
样式工具类 - 为控件提供便捷的样式应用方法

提供简化的API来应用统一样式到各种Qt控件。
这个模块作为样式系统的高级接口，让开发者更容易使用。

作者：TAVR Research Team
创建时间：2024
"""

import qt
from typing import Optional, Dict, Any, Union
from ui.styles import StyleManager, ComponentStyleFactory, ThemeColor


class StyledWidget:
    """样式化控件基类 - 为常用控件提供样式应用方法"""
    
    @staticmethod
    def create_button(text: str, 
                     button_type: str = "primary", 
                     size: str = "normal",
                     **kwargs) -> qt.QPushButton:
        """创建样式化按钮
        
        Args:
            text: 按钮文本
            button_type: 按钮类型 ("primary", "secondary", "success", "warning", "danger")
            size: 按钮大小 ("small", "normal", "large")
            **kwargs: 其他按钮属性
            
        Returns:
            样式化的按钮
        """
        button = qt.QPushButton(text)
        style = StyleManager.get_button_style(button_type, size)
        button.setStyleSheet(style)
        
        # 应用其他属性
        for attr, value in kwargs.items():
            if hasattr(button, attr):
                getattr(button, attr)(value)
        
        return button
    
    @staticmethod
    def create_label(text: str, 
                    label_type: str = "normal",
                    **kwargs) -> qt.QLabel:
        """创建样式化标签
        
        Args:
            text: 标签文本
            label_type: 标签类型 ("normal", "title", "subtitle", "info", "primary", "secondary")
            **kwargs: 其他标签属性
            
        Returns:
            样式化的标签
        """
        label = qt.QLabel(text)
        style = StyleManager.get_label_style(label_type)
        label.setStyleSheet(style)
        
        # 应用其他属性
        for attr, value in kwargs.items():
            if hasattr(label, attr):
                getattr(label, attr)(value)
        
        return label
    
    @staticmethod
    def create_status_indicator(text: str = "就绪", 
                               status_type: str = "normal") -> qt.QLabel:
        """创建状态指示器
        
        Args:
            text: 状态文本
            status_type: 状态类型 ("normal", "success", "warning", "error")
            
        Returns:
            样式化的状态指示器
        """
        indicator = qt.QLabel(text)
        style = StyleManager.get_status_indicator_style(status_type)
        indicator.setStyleSheet(style)
        
        return indicator
    
    @staticmethod
    def create_slider(orientation: qt.Qt.Orientation = qt.Qt.Horizontal) -> qt.QSlider:
        """创建样式化滑块
        
        Args:
            orientation: 滑块方向
            
        Returns:
            样式化的滑块
        """
        slider = qt.QSlider(orientation)
        style = StyleManager.get_slider_style()
        slider.setStyleSheet(style)
        
        return slider
    
    @staticmethod
    def create_input(placeholder: str = "", 
                    multiline: bool = False) -> Union[qt.QLineEdit, qt.QTextEdit]:
        """创建样式化输入框
        
        Args:
            placeholder: 占位符文本
            multiline: 是否多行
            
        Returns:
            样式化的输入框
        """
        if multiline:
            input_widget = qt.QTextEdit()
            input_widget.setPlaceholderText(placeholder)
        else:
            input_widget = qt.QLineEdit()
            input_widget.setPlaceholderText(placeholder)
        
        style = StyleManager.get_input_style()
        input_widget.setStyleSheet(style)
        
        return input_widget
    
    @staticmethod
    def create_group_box(title: str) -> qt.QGroupBox:
        """创建样式化分组框
        
        Args:
            title: 分组框标题
            
        Returns:
            样式化的分组框
        """
        group_box = qt.QGroupBox(title)
        style = StyleManager.get_group_box_style()
        group_box.setStyleSheet(style)
        
        return group_box


class StyleUtils:
    """样式工具类 - 提供样式相关的实用方法"""
    
    @staticmethod
    def apply_component_styles(widget, component_name: str):
        """为组件应用预设样式
        
        Args:
            widget: 要应用样式的控件
            component_name: 组件名称 ("cardiac_cycle", "main_ui")
        """
        if component_name == "cardiac_cycle":
            styles = ComponentStyleFactory.get_cardiac_cycle_styles()
        elif component_name == "main_ui":
            styles = ComponentStyleFactory.get_main_ui_styles()
        else:
            return
        
        # 根据控件类型应用样式
        widget_type = type(widget).__name__
        
        if widget_type == "QPushButton":
            if hasattr(widget, '_style_role'):
                style_name = widget._style_role
                if style_name in styles:
                    widget.setStyleSheet(styles[style_name])
        elif widget_type == "QLabel":
            if hasattr(widget, '_style_role'):
                style_name = widget._style_role
                if style_name in styles:
                    widget.setStyleSheet(styles[style_name])
    
    @staticmethod
    def set_widget_style_role(widget, role: str):
        """为控件设置样式角色
        
        Args:
            widget: 控件
            role: 样式角色名称
        """
        widget._style_role = role
    
    @staticmethod
    def update_theme_color(color_name: str, color_value: str):
        """更新主题颜色（动态主题支持）
        
        Args:
            color_name: 颜色名称
            color_value: 颜色值
        """
        # 这里可以实现动态主题更新
        # 目前只是占位实现
        pass
    
    @staticmethod
    def create_custom_style(base_style: str, custom_properties: Dict[str, str]) -> str:
        """创建自定义样式
        
        Args:
            base_style: 基础样式字符串
            custom_properties: 自定义属性字典
            
        Returns:
            合并后的样式字符串
        """
        # 简单的样式合并实现
        custom_css = ""
        for prop, value in custom_properties.items():
            custom_css += f"{prop}: {value}; "
        
        # 在基础样式中插入自定义属性
        if "}" in base_style:
            base_style = base_style.replace("}", f"{custom_css}}}")
        
        return base_style
    
    @staticmethod
    def get_theme_colors() -> Dict[str, str]:
        """获取当前主题颜色
        
        Returns:
            主题颜色字典
        """
        return {
            "primary": ThemeColor.PRIMARY.value,
            "background_light": ThemeColor.BACKGROUND_LIGHT.value,
            "text_primary": ThemeColor.TEXT_PRIMARY.value,
            "success": ThemeColor.SUCCESS.value,
            "warning": ThemeColor.WARNING.value,
            "error": ThemeColor.ERROR.value
        }


class WidgetStyler:
    """控件样式器 - 为现有控件应用样式的便捷类"""
    
    def __init__(self, widget):
        """初始化样式器
        
        Args:
            widget: 要样式化的控件
        """
        self.widget = widget
    
    def as_button(self, button_type: str = "primary", size: str = "normal"):
        """将控件样式化为按钮
        
        Args:
            button_type: 按钮类型
            size: 按钮大小
            
        Returns:
            self，支持链式调用
        """
        if isinstance(self.widget, qt.QPushButton):
            style = StyleManager.get_button_style(button_type, size)
            self.widget.setStyleSheet(style)
        return self
    
    def as_label(self, label_type: str = "normal"):
        """将控件样式化为标签
        
        Args:
            label_type: 标签类型
            
        Returns:
            self，支持链式调用
        """
        if isinstance(self.widget, qt.QLabel):
            style = StyleManager.get_label_style(label_type)
            self.widget.setStyleSheet(style)
        return self
    
    def as_status_indicator(self, status_type: str = "normal"):
        """将控件样式化为状态指示器
        
        Args:
            status_type: 状态类型
            
        Returns:
            self，支持链式调用
        """
        if isinstance(self.widget, qt.QLabel):
            style = StyleManager.get_status_indicator_style(status_type)
            self.widget.setStyleSheet(style)
        return self
    
    def with_custom_style(self, custom_properties: Dict[str, str]):
        """应用自定义样式属性
        
        Args:
            custom_properties: 自定义属性字典
            
        Returns:
            self，支持链式调用
        """
        current_style = self.widget.styleSheet()
        new_style = StyleUtils.create_custom_style(current_style, custom_properties)
        self.widget.setStyleSheet(new_style)
        return self


def style(widget) -> WidgetStyler:
    """创建控件样式器的便捷函数
    
    Args:
        widget: 要样式化的控件
        
    Returns:
        控件样式器实例
        
    Example:
        style(my_button).as_button("primary", "large")
        style(my_label).as_label("title")
    """
    return WidgetStyler(widget)


# 导出主要类和函数
__all__ = [
    'StyledWidget',
    'StyleUtils', 
    'WidgetStyler',
    'style'
]
