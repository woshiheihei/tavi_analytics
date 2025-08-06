"""
模块二测试脚本
用于验证模块二的基础框架是否正确搭建
"""

import sys
import os

# 添加路径以便导入
current_dir = os.path.dirname(__file__)
tavi_analytics_dir = os.path.join(current_dir, "tavi_analytics")
if tavi_analytics_dir not in sys.path:
    sys.path.insert(0, tavi_analytics_dir)

def test_module2_imports():
    """测试模块二的导入"""
    try:
        # 测试逻辑层导入
        from module2.module2_logic import Module2Logic
        print("✓ Module2Logic 导入成功")
        
        # 测试界面层导入
        from module2.module2_widget import Module2Widget
        print("✓ Module2Widget 导入成功")
        
        # 测试适配器导入
        from module2.module2_adapter import Module2Adapter
        print("✓ Module2Adapter 导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_module2_instantiation():
    """测试模块二的实例化"""
    try:
        from module2.module2_logic import Module2Logic
        from module2.module2_adapter import Module2Adapter
        
        # 测试逻辑类实例化
        logic = Module2Logic()
        print("✓ Module2Logic 实例化成功")
        
        # 测试适配器实例化
        adapter = Module2Adapter()
        print("✓ Module2Adapter 实例化成功")
        
        # 测试适配器方法
        module_name = adapter.get_module_name()
        display_name = adapter.get_display_name()
        dependencies = adapter.get_dependencies()
        
        print(f"  - 模块名称: {module_name}")
        print(f"  - 显示名称: {display_name}")
        print(f"  - 依赖关系: {dependencies}")
        
        # 验证返回值
        assert module_name == "module2", f"期望 'module2', 实际 '{module_name}'"
        assert display_name == "引导式分割", f"期望 '引导式分割', 实际 '{display_name}'"
        assert dependencies == ["module1"], f"期望 ['module1'], 实际 {dependencies}"
        
        print("✓ 适配器方法测试通过")
        
        return True
    except Exception as e:
        print(f"✗ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """测试配置"""
    try:
        from core.plugin_config import PluginConfig
        
        config = PluginConfig()
        module2_enabled = config.is_module_enabled("module2")
        
        print(f"✓ 模块二配置状态: {'启用' if module2_enabled else '禁用'}")
        
        if not module2_enabled:
            print("  警告: 模块二在配置中被禁用，请检查 config.json")
        
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始模块二框架验证...")
    print("=" * 40)
    
    # 运行所有测试
    tests = [
        ("导入测试", test_module2_imports),
        ("实例化测试", test_module2_instantiation),
        ("配置测试", test_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n执行 {test_name}:")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 通过")
        else:
            print(f"✗ {test_name} 失败")
    
    print("\n" + "=" * 40)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 模块二框架搭建成功！")
        print("\n下一步：")
        print("1. 重启 3D Slicer")
        print("2. 打开 TAVR Analytics 插件")
        print("3. 验证在导航栏中是否有 '引导式分割' 按钮")
        print("4. 点击该按钮，验证是否显示模块二界面")
    else:
        print("❌ 存在问题，请检查错误信息")

if __name__ == "__main__":
    main()
