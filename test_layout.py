"""
布局测试脚本

用于测试新的布局管理器是否正常工作
"""

import qt
import slicer

# 测试布局管理器
def test_layout_manager():
    """测试布局管理器功能"""
    try:
        # 导入布局管理器
        from utils.layout_manager import LayoutManager, LayoutType, SizePolicy
        
        # 创建测试窗口
        test_window = qt.QWidget()
        test_window.setWindowTitle("布局管理器测试")
        test_window.resize(800, 600)
        
        # 使用布局管理器创建主布局
        main_layout = LayoutManager.create_layout(LayoutType.MAIN_CONTAINER, test_window)
        
        # 创建测试区域
        section1 = LayoutManager.create_section_frame("测试区域1", LayoutType.SECTION_CONTAINER)
        section1_layout = LayoutManager.create_layout(LayoutType.SECTION_CONTAINER, section1)
        
        # 添加测试按钮
        button1 = LayoutManager.create_button_with_style("主要按钮", "primary")
        button2 = LayoutManager.create_button_with_style("成功按钮", "success") 
        button3 = LayoutManager.create_button_with_style("警告按钮", "warning")
        button4 = LayoutManager.create_button_with_style("危险按钮", "danger")
        
        section1_layout.addWidget(button1)
        section1_layout.addWidget(button2)
        section1_layout.addWidget(button3)
        section1_layout.addWidget(button4)
        
        main_layout.addWidget(section1)
        
        # 设置大小策略
        LayoutManager.setup_widget_size_policy(test_window, LayoutType.MAIN_CONTAINER, SizePolicy.EXPANDING)
        
        # 显示窗口
        test_window.show()
        
        print("布局管理器测试窗口已显示")
        return test_window
        
    except Exception as e:
        print(f"测试布局管理器时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 运行测试
if __name__ == "__main__":
    test_window = test_layout_manager()
