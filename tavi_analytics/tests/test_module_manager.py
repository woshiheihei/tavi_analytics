"""
测试文件：ModuleManager 功能验证

本测试文件用于验证ModuleManager类的功能：
1. 模块注册和获取
2. 模块激活和停用
3. 模块依赖管理
4. 会话集成

作者：TAVR Analytics Team
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# 添加路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 模拟slicer模块
sys.modules['slicer'] = MagicMock()
sys.modules['vtk'] = MagicMock()
sys.modules['qt'] = MagicMock()

try:
    from core.module_manager import ModuleManager, ModuleInfo
    from core.session import TAVRStudySession
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的目录中运行测试")
    sys.exit(1)


class TestModuleManager(unittest.TestCase):
    """ModuleManager 测试类"""

    def setUp(self):
        """测试前设置"""
        # 重置单例实例
        ModuleManager._instance = None
        ModuleManager._initialized = False
        TAVRStudySession._instance = None
        TAVRStudySession._initialized = False

        # 创建实例
        self.manager = ModuleManager()
        self.session = TAVRStudySession()
        self.manager.set_session(self.session)

    def tearDown(self):
        """测试后清理"""
        self.manager.cleanup_all_modules()

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = ModuleManager()
        manager2 = ModuleManager()
        self.assertEqual(manager1, manager2)
        self.assertIs(manager1, manager2)

    def test_module_registration(self):
        """测试模块注册"""
        # 创建测试模块信息
        mock_class = MagicMock()
        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class,
            dependencies=[],
            enabled=True
        )

        # 注册模块
        self.manager.register_module(module_info)

        # 验证模块已注册
        available_modules = self.manager.get_available_modules()
        self.assertIn("test_module", available_modules)

    def test_get_module_info(self):
        """测试获取模块信息"""
        mock_class = MagicMock()
        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class
        )

        self.manager.register_module(module_info)

        # 获取模块信息
        retrieved_info = self.manager.get_module_info("test_module")
        self.assertIsNotNone(retrieved_info)
        self.assertEqual(retrieved_info.name, "test_module")
        self.assertEqual(retrieved_info.display_name, "测试模块")

    def test_module_activation(self):
        """测试模块激活"""
        # 创建模拟模块类
        mock_module = MagicMock()
        mock_class = MagicMock(return_value=mock_module)

        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class
        )

        self.manager.register_module(module_info)

        # 激活模块
        success = self.manager.activate_module("test_module")
        self.assertTrue(success)

        # 验证模块已激活
        active_modules = self.manager.get_active_modules()
        self.assertIn("test_module", active_modules)

    def test_module_deactivation(self):
        """测试模块停用"""
        # 创建并激活模块
        mock_module = MagicMock()
        mock_class = MagicMock(return_value=mock_module)

        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class
        )

        self.manager.register_module(module_info)
        self.manager.activate_module("test_module")

        # 停用模块
        self.manager.deactivate_module("test_module")

        # 验证模块已停用
        active_modules = self.manager.get_active_modules()
        self.assertNotIn("test_module", active_modules)

    def test_module_dependencies(self):
        """测试模块依赖"""
        # 创建两个模块，module2依赖module1
        mock_class1 = MagicMock(return_value=MagicMock())
        mock_class2 = MagicMock(return_value=MagicMock())

        module1_info = ModuleInfo(
            name="module1",
            display_name="模块一",
            module_class=mock_class1
        )

        module2_info = ModuleInfo(
            name="module2",
            display_name="模块二",
            module_class=mock_class2,
            dependencies=["module1"]
        )

        self.manager.register_module(module1_info)
        self.manager.register_module(module2_info)

        # 验证依赖关系
        deps = self.manager._modules["module2"].dependencies
        self.assertIn("module1", deps)

    def test_get_module_widget(self):
        """测试获取模块组件"""
        # 创建模拟模块
        mock_widget = MagicMock()
        mock_module = MagicMock()
        mock_module.get_widget.return_value = mock_widget
        mock_class = MagicMock(return_value=mock_module)

        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class
        )

        self.manager.register_module(module_info)
        self.manager.activate_module("test_module")

        # 获取组件
        widget = self.manager.get_module_widget("test_module")
        self.assertIsNotNone(widget)
        self.assertEqual(widget, mock_widget)

    def test_cleanup_all_modules(self):
        """测试清理所有模块"""
        # 创建并激活多个模块
        for i in range(3):
            mock_module = MagicMock()
            mock_class = MagicMock(return_value=mock_module)

            module_info = ModuleInfo(
                name=f"test_module_{i}",
                display_name=f"测试模块{i}",
                module_class=mock_class
            )

            self.manager.register_module(module_info)
            self.manager.activate_module(f"test_module_{i}")

        # 清理所有模块
        self.manager.cleanup_all_modules()

        # 验证所有模块已清理
        active_modules = self.manager.get_active_modules()
        self.assertEqual(len(active_modules), 0)

    def test_session_integration(self):
        """测试会话集成"""
        # 验证会话已设置
        self.assertIsNotNone(self.manager._session)
        self.assertEqual(self.manager._session, self.session)

    def test_invalid_module_activation(self):
        """测试激活不存在的模块"""
        success = self.manager.activate_module("non_existent_module")
        self.assertFalse(success)

    def test_duplicate_module_registration(self):
        """测试重复注册模块"""
        mock_class = MagicMock()
        module_info = ModuleInfo(
            name="test_module",
            display_name="测试模块",
            module_class=mock_class
        )

        # 第一次注册
        self.manager.register_module(module_info)

        # 第二次注册（应该覆盖或忽略）
        self.manager.register_module(module_info)

        # 验证只有一个模块
        available_modules = self.manager.get_available_modules()
        count = sum(1 for name in available_modules if name == "test_module")
        self.assertEqual(count, 1)


if __name__ == '__main__':
    unittest.main()
