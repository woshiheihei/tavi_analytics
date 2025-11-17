"""
测试文件：PatientData 数据模型验证

本测试文件用于验证PatientData类的功能：
1. 数据字段验证
2. 数据序列化
3. 默认值处理
4. 瓣膜信息管理

作者：TAVR Analytics Team
"""

import unittest
from unittest.mock import MagicMock
import sys
import os
from datetime import datetime

# 添加路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 模拟slicer模块
sys.modules['slicer'] = MagicMock()
sys.modules['vtk'] = MagicMock()

try:
    from core.data_models import PatientData
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的目录中运行测试")
    sys.exit(1)


class TestPatientData(unittest.TestCase):
    """PatientData 测试类"""

    def setUp(self):
        """测试前设置"""
        self.patient_data = PatientData()

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.patient_data.patientID, "")
        self.assertEqual(self.patient_data.patientName, "")
        self.assertEqual(self.patient_data.patientAge, 0)
        self.assertEqual(self.patient_data.patientSex, "")
        self.assertIsNone(self.patient_data.studyDate)
        self.assertEqual(self.patient_data.valveBrand, "")
        self.assertEqual(self.patient_data.valveModel, "")

    def test_patient_id_assignment(self):
        """测试患者ID赋值"""
        test_id = "TEST001"
        self.patient_data.patientID = test_id
        self.assertEqual(self.patient_data.patientID, test_id)

    def test_patient_name_assignment(self):
        """测试患者姓名赋值"""
        test_name = "张三"
        self.patient_data.patientName = test_name
        self.assertEqual(self.patient_data.patientName, test_name)

    def test_patient_age_assignment(self):
        """测试患者年龄赋值"""
        test_age = 65
        self.patient_data.patientAge = test_age
        self.assertEqual(self.patient_data.patientAge, test_age)

    def test_patient_sex_assignment(self):
        """测试患者性别赋值"""
        test_sex = "M"
        self.patient_data.patientSex = test_sex
        self.assertEqual(self.patient_data.patientSex, test_sex)

    def test_study_date_assignment(self):
        """测试检查日期赋值"""
        test_date = "2024-01-15"
        self.patient_data.studyDate = test_date
        self.assertEqual(self.patient_data.studyDate, test_date)

    def test_valve_brand_assignment(self):
        """测试瓣膜品牌赋值"""
        test_brand = "Medtronic"
        self.patient_data.valveBrand = test_brand
        self.assertEqual(self.patient_data.valveBrand, test_brand)

    def test_valve_model_assignment(self):
        """测试瓣膜型号赋值"""
        test_model = "Evolut R/PRO"
        self.patient_data.valveModel = test_model
        self.assertEqual(self.patient_data.valveModel, test_model)

    def test_complete_patient_data(self):
        """测试完整患者数据"""
        self.patient_data.patientID = "TEST001"
        self.patient_data.patientName = "张三"
        self.patient_data.patientAge = 65
        self.patient_data.patientSex = "M"
        self.patient_data.studyDate = "2024-01-15"
        self.patient_data.valveBrand = "Medtronic"
        self.patient_data.valveModel = "Evolut R/PRO"
        self.patient_data.valveSize = "29mm"

        # 验证所有字段
        self.assertEqual(self.patient_data.patientID, "TEST001")
        self.assertEqual(self.patient_data.patientName, "张三")
        self.assertEqual(self.patient_data.patientAge, 65)
        self.assertEqual(self.patient_data.patientSex, "M")
        self.assertEqual(self.patient_data.studyDate, "2024-01-15")
        self.assertEqual(self.patient_data.valveBrand, "Medtronic")
        self.assertEqual(self.patient_data.valveModel, "Evolut R/PRO")
        self.assertEqual(self.patient_data.valveSize, "29mm")

    def test_valve_information(self):
        """测试瓣膜信息"""
        # 测试不同品牌和型号
        valve_combinations = [
            ("Medtronic", "Evolut R/PRO", "29mm"),
            ("Edwards", "SAPIEN 3", "26mm"),
            ("Boston Scientific", "ACURATE neo", "L"),
        ]

        for brand, model, size in valve_combinations:
            self.patient_data.valveBrand = brand
            self.patient_data.valveModel = model
            self.patient_data.valveSize = size

            self.assertEqual(self.patient_data.valveBrand, brand)
            self.assertEqual(self.patient_data.valveModel, model)
            self.assertEqual(self.patient_data.valveSize, size)

    def test_age_validation(self):
        """测试年龄验证"""
        # 测试有效年龄
        valid_ages = [45, 65, 80, 95]
        for age in valid_ages:
            self.patient_data.patientAge = age
            self.assertEqual(self.patient_data.patientAge, age)

    def test_sex_values(self):
        """测试性别值"""
        valid_sexes = ["M", "F", "Male", "Female", "男", "女"]
        for sex in valid_sexes:
            self.patient_data.patientSex = sex
            self.assertEqual(self.patient_data.patientSex, sex)

    def test_empty_strings(self):
        """测试空字符串处理"""
        self.patient_data.patientID = ""
        self.patient_data.patientName = ""
        self.patient_data.valveBrand = ""

        self.assertEqual(self.patient_data.patientID, "")
        self.assertEqual(self.patient_data.patientName, "")
        self.assertEqual(self.patient_data.valveBrand, "")

    def test_data_reset(self):
        """测试数据重置"""
        # 设置数据
        self.patient_data.patientID = "TEST001"
        self.patient_data.patientName = "张三"
        self.patient_data.valveBrand = "Medtronic"

        # 创建新实例（相当于重置）
        new_data = PatientData()

        # 验证新实例是空的
        self.assertEqual(new_data.patientID, "")
        self.assertEqual(new_data.patientName, "")
        self.assertEqual(new_data.valveBrand, "")

    def test_chinese_characters(self):
        """测试中文字符支持"""
        chinese_name = "李明华"
        self.patient_data.patientName = chinese_name
        self.assertEqual(self.patient_data.patientName, chinese_name)

    def test_special_characters_in_id(self):
        """测试ID中的特殊字符"""
        special_ids = ["TEST-001", "TEST_001", "TEST.001", "TEST 001"]
        for test_id in special_ids:
            self.patient_data.patientID = test_id
            self.assertEqual(self.patient_data.patientID, test_id)

    def test_multiple_instances(self):
        """测试多个实例的独立性"""
        data1 = PatientData()
        data2 = PatientData()

        data1.patientID = "TEST001"
        data2.patientID = "TEST002"

        self.assertEqual(data1.patientID, "TEST001")
        self.assertEqual(data2.patientID, "TEST002")
        self.assertNotEqual(data1.patientID, data2.patientID)


if __name__ == '__main__':
    unittest.main()
