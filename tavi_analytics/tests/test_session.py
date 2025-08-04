"""
测试文件：TAVRStudySession 单例和功能验证

本测试文件用于验证重构后的TAVRStudySession类的功能：
1. 单例模式正确实现
2. 数据管理功能正常
3. 时相标记功能正常
4. 会话状态管理正常

运行此测试可以验证重构是否成功。
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

try:
    from core.session import TAVRStudySession
    from core.data_models import PatientData
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的目录中运行测试")
    sys.exit(1)


class TestTAVRStudySession(unittest.TestCase):
    """TAVRStudySession 测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 重置单例实例（用于测试）
        TAVRStudySession._instance = None
        TAVRStudySession._initialized = False
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建两个实例
        session1 = TAVRStudySession()
        session2 = TAVRStudySession()
        
        # 验证它们是同一个实例
        self.assertIs(session1, session2)
        self.assertEqual(id(session1), id(session2))
    
    def test_singleton_get_instance(self):
        """测试get_instance类方法"""
        session1 = TAVRStudySession.get_instance()
        session2 = TAVRStudySession()
        
        self.assertIs(session1, session2)
    
    def test_initialization(self):
        """测试初始化"""
        session = TAVRStudySession()
        
        # 验证初始状态
        self.assertIsInstance(session.patient_data, PatientData)
        self.assertIsNone(session.volume_sequence_node_id)
        self.assertIsNone(session.sequence_browser_node_id)
        self.assertIn('end_diastole', session.marked_phases)
        self.assertIn('end_systole', session.marked_phases)
    
    def test_patient_data_management(self):
        """测试患者数据管理"""
        session = TAVRStudySession()
        patient_data = session.get_patient_data()
        
        # 修改患者数据
        patient_data.patientID = "TEST001"
        patient_data.patientName = "Test Patient"
        patient_data.valveBrand = "Test Brand"
        patient_data.valveModel = "Test Model"
        
        # 验证数据正确存储
        self.assertEqual(session.patient_data.patientID, "TEST001")
        self.assertEqual(session.patient_data.patientName, "Test Patient")
        
        valve_info = session.get_selected_valve()
        self.assertEqual(valve_info['brand'], "Test Brand")
        self.assertEqual(valve_info['model'], "Test Model")
    
    def test_sequence_data_management(self):
        """测试序列数据管理"""
        session = TAVRStudySession()
        
        # 设置序列数据
        session.set_volume_sequence_data("volume_123", "browser_456")
        
        # 验证设置正确
        self.assertEqual(session.volume_sequence_node_id, "volume_123")
        self.assertEqual(session.sequence_browser_node_id, "browser_456")
    
    def test_phase_marking(self):
        """测试时相标记功能"""
        session = TAVRStudySession()
        
        # 标记舒张末期
        session.mark_phase('end_diastole', frame_index=10, phase_percent=30.0, series_description="Test Series")
        
        # 验证标记正确
        phase_info = session.get_marked_phase('end_diastole')
        self.assertIsNotNone(phase_info)
        self.assertEqual(phase_info['frame_index'], 10)
        self.assertEqual(phase_info['phase_percent'], 30.0)
        self.assertEqual(phase_info['series_description'], "Test Series")
        
        # 测试无效时相名称
        with self.assertRaises(ValueError):
            session.mark_phase('invalid_phase', frame_index=5, phase_percent=20.0)
    
    def test_session_state_validation(self):
        """测试会话状态验证"""
        session = TAVRStudySession()
        
        # 初始状态应该不ready
        self.assertFalse(session.is_ready())
        
        # 设置必要数据
        session.volume_sequence_node_id = "volume_123"
        session.patient_data.valveBrand = "Test Brand"
        session.patient_data.valveModel = "Test Model"
        
        # 现在应该ready
        self.assertTrue(session.is_ready())
    
    def test_phase_summary(self):
        """测试时相摘要功能"""
        session = TAVRStudySession()
        
        # 初始状态
        self.assertFalse(session.has_marked_phases())
        
        # 标记一个时相
        session.mark_phase('end_diastole', frame_index=10, phase_percent=30.0)
        self.assertFalse(session.has_marked_phases())  # 还需要标记另一个
        
        # 标记第二个时相
        session.mark_phase('end_systole', frame_index=20, phase_percent=70.0)
        self.assertTrue(session.has_marked_phases())  # 现在都标记了
        
        # 测试摘要
        summary = session.get_phase_summary()
        self.assertTrue(summary['end_diastole_marked'])
        self.assertTrue(summary['end_systole_marked'])
    
    def test_session_info(self):
        """测试会话信息摘要"""
        session = TAVRStudySession()
        
        # 设置一些测试数据
        session.patient_data.patientID = "TEST001"
        session.patient_data.valveBrand = "Test Brand"
        session.volume_sequence_node_id = "volume_123"
        session.mark_phase('end_diastole', frame_index=10, phase_percent=30.0)
        
        info = session.get_session_info()
        
        # 验证信息正确
        self.assertEqual(info['patient_id'], "TEST001")
        self.assertEqual(info['valve_brand'], "Test Brand")
        self.assertTrue(info['has_sequence_data'])
        self.assertFalse(info['has_marked_phases'])  # 只标记了一个时相
    
    def test_session_reset(self):
        """测试会话重置"""
        session = TAVRStudySession()
        
        # 设置一些数据
        session.patient_data.patientID = "TEST001"
        session.volume_sequence_node_id = "volume_123"
        session.mark_phase('end_diastole', frame_index=10, phase_percent=30.0)
        
        # 重置会话
        session.reset()
        
        # 验证数据已清除
        self.assertEqual(session.patient_data.patientID, "")
        self.assertIsNone(session.volume_sequence_node_id)
        self.assertIsNone(session.get_marked_phase('end_diastole')['frame_index'])
    
    def test_only_one_initialization(self):
        """测试只初始化一次"""
        # 创建第一个实例
        session1 = TAVRStudySession()
        session1.patient_data.patientID = "TEST001"
        
        # 创建第二个实例
        session2 = TAVRStudySession()
        
        # 验证数据保持不变
        self.assertEqual(session2.patient_data.patientID, "TEST001")
        self.assertIs(session1, session2)


if __name__ == '__main__':
    print("开始测试TAVRStudySession重构...")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)
