"""
PASTE分析逻辑组件

瓣叶功能评估（PASTE Analysis）的业务逻辑实现，包含：
- HALT (低密度瓣叶增厚) 分析逻辑
- RELM (瓣叶活动度减退) 分析逻辑  
- SFD (窦内充盈缺损) 分析逻辑
- PFD (瓣叶下充盈缺损) 分析逻辑
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

try:
    from ..core.session import TAVRStudySession
    from ..core.domain_models import LeafletType, CardiacPhase
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
    from core.domain_models import LeafletType, CardiacPhase


class HaltAnalysisLogic:
    """HALT (低密度瓣叶增厚) 分析逻辑"""
    
    def __init__(self):
        self.current_leaflet = None
        self.halt_segment = None
        self.leaflet_area = None
        self.halt_area = None
        
    def start_halt_segmentation(self, leaflet: str) -> bool:
        """
        开始HALT区域分割
        
        Args:
            leaflet: 目标瓣叶 ('LC', 'RC', 'NC')
        
        Returns:
            bool: 是否成功开始分割
        """
        try:
            self.current_leaflet = leaflet
            logging.info(f"开始对{leaflet}瓣叶进行HALT分割")
            
            # TODO: 实现实际的分割逻辑
            # 1. 创建分割节点
            # 2. 设置分割编辑器
            # 3. 激活Paint工具
            
            return True
        except Exception as e:
            logging.error(f"开始HALT分割失败: {e}")
            return False
    
    def finish_halt_segmentation(self) -> Dict[str, Any]:
        """
        完成HALT区域分割并计算结果
        
        Returns:
            Dict: 包含分析结果的字典
        """
        try:
            if not self.current_leaflet:
                raise ValueError("未选择瓣叶")
            
            # TODO: 实现实际的计算逻辑
            # 1. 获取分割区域
            # 2. 计算HALT面积
            # 3. 计算瓣叶总面积
            # 4. 计算占比
            # 5. 确定分级
            
            # 临时模拟结果
            self.halt_area = 15.2  # mm²
            self.leaflet_area = 42.5  # mm²
            percentage = (self.halt_area / self.leaflet_area) * 100
            grade = self._calculate_halt_grade(percentage)
            
            result = {
                'leaflet': self.current_leaflet,
                'halt_area': self.halt_area,
                'leaflet_area': self.leaflet_area,
                'percentage': percentage,
                'grade': grade,
                'success': True
            }
            
            logging.info(f"HALT分析完成: {result}")
            return result
            
        except Exception as e:
            logging.error(f"完成HALT分割失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_halt_grade(self, percentage: float) -> str:
        """
        根据HALT占比计算分级
        
        Args:
            percentage: HALT占瓣叶面积的百分比
        
        Returns:
            str: HALT分级
        """
        if percentage <= 25:
            return "≤25%"
        elif percentage <= 50:
            return "25-50%"
        elif percentage <= 75:
            return "50%-75%"
        else:
            return ">75%"
    
    def reset(self):
        """重置HALT分析"""
        self.current_leaflet = None
        self.halt_segment = None
        self.leaflet_area = None
        self.halt_area = None
        logging.info("HALT分析已重置")


class RelmAnalysisLogic:
    """RELM (瓣叶活动度减退) 分析逻辑"""
    
    def __init__(self):
        self.current_leaflet = None
        self.thickened_width = None
        self.stent_diameter = None
        self.relm_value = None
        
    def measure_thickened_width(self, leaflet: str) -> float:
        """
        测量增厚瓣叶宽度
        
        Args:
            leaflet: 目标瓣叶
        
        Returns:
            float: 增厚宽度（mm）
        """
        try:
            self.current_leaflet = leaflet
            logging.info(f"开始测量{leaflet}瓣叶增厚宽度")
            
            # TODO: 实现实际的测量逻辑
            # 1. 激活线性测量工具
            # 2. 引导用户在增厚区域进行测量
            # 3. 获取测量结果
            
            # 临时模拟结果
            self.thickened_width = 3.2  # mm
            
            logging.info(f"增厚宽度测量完成: {self.thickened_width} mm")
            return self.thickened_width
            
        except Exception as e:
            logging.error(f"测量增厚宽度失败: {e}")
            return 0.0
    
    def measure_stent_diameter(self) -> float:
        """
        测量同平面支架内径
        
        Returns:
            float: 支架内径（mm）
        """
        try:
            logging.info("开始测量支架内径")
            
            # TODO: 实现实际的测量逻辑
            # 1. 确定测量平面
            # 2. 在平面上测量支架内径
            # 3. 获取测量结果
            
            # 临时模拟结果
            self.stent_diameter = 22.5  # mm
            
            logging.info(f"支架内径测量完成: {self.stent_diameter} mm")
            return self.stent_diameter
            
        except Exception as e:
            logging.error(f"测量支架内径失败: {e}")
            return 0.0
    
    def calculate_relm(self) -> Dict[str, Any]:
        """
        计算RELM值和分级
        
        Returns:
            Dict: 包含RELM分析结果的字典
        """
        try:
            if self.thickened_width is None or self.stent_diameter is None:
                raise ValueError("缺少必要的测量数据")
            
            # 使用公式: RELM = W / (1/2 × D)
            self.relm_value = self.thickened_width / (0.5 * self.stent_diameter)
            relm_percentage = self.relm_value * 100
            
            grade = self._calculate_relm_grade(relm_percentage)
            
            result = {
                'leaflet': self.current_leaflet,
                'thickened_width': self.thickened_width,
                'stent_diameter': self.stent_diameter,
                'relm_value': relm_percentage,
                'grade': grade,
                'success': True
            }
            
            logging.info(f"RELM计算完成: {result}")
            return result
            
        except Exception as e:
            logging.error(f"RELM计算失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_relm_grade(self, percentage: float) -> str:
        """
        根据RELM百分比计算分级
        
        Args:
            percentage: RELM百分比
        
        Returns:
            str: RELM分级
        """
        if percentage < 50:
            return "轻度"
        elif percentage < 70:
            return "中度"
        else:
            return "重度"
    
    def reset(self):
        """重置RELM分析"""
        self.current_leaflet = None
        self.thickened_width = None
        self.stent_diameter = None
        self.relm_value = None
        logging.info("RELM分析已重置")


class SfdAnalysisLogic:
    """SFD (窦内充盈缺损) 分析逻辑"""
    
    def __init__(self):
        self.sfd_status = "none"  # none, present, indeterminate
        self.affected_sinuses = []
        
    def set_sfd_status(self, status: str) -> bool:
        """
        设置SFD存在状态
        
        Args:
            status: SFD状态 ('none', 'present', 'indeterminate')
        
        Returns:
            bool: 是否设置成功
        """
        try:
            if status not in ['none', 'present', 'indeterminate']:
                raise ValueError(f"无效的SFD状态: {status}")
            
            self.sfd_status = status
            
            # 如果不是"present"，清除受累窦部
            if status != 'present':
                self.affected_sinuses = []
            
            logging.info(f"SFD状态设置为: {status}")
            return True
            
        except Exception as e:
            logging.error(f"设置SFD状态失败: {e}")
            return False
    
    def set_affected_sinuses(self, sinuses: List[str]) -> bool:
        """
        设置受累的主动脉窦
        
        Args:
            sinuses: 受累窦部列表 (['LC', 'RC', 'NC'])
        
        Returns:
            bool: 是否设置成功
        """
        try:
            valid_sinuses = ['LC', 'RC', 'NC']
            for sinus in sinuses:
                if sinus not in valid_sinuses:
                    raise ValueError(f"无效的窦部: {sinus}")
            
            self.affected_sinuses = sinuses.copy()
            logging.info(f"受累窦部设置为: {sinuses}")
            return True
            
        except Exception as e:
            logging.error(f"设置受累窦部失败: {e}")
            return False
    
    def get_sfd_results(self) -> Dict[str, Any]:
        """
        获取SFD分析结果
        
        Returns:
            Dict: SFD分析结果
        """
        status_map = {
            'none': '无SFD',
            'present': '存在SFD',
            'indeterminate': '难以判定'
        }
        
        result = {
            'status': status_map.get(self.sfd_status, '未知'),
            'affected_sinuses': self.affected_sinuses.copy(),
            'raw_status': self.sfd_status
        }
        
        return result
    
    def reset(self):
        """重置SFD分析"""
        self.sfd_status = "none"
        self.affected_sinuses = []
        logging.info("SFD分析已重置")


class PfdAnalysisLogic:
    """PFD (瓣叶下充盈缺损) 分析逻辑"""
    
    def __init__(self):
        self.pfd_status = "none"  # none, present, indeterminate
        self.max_thickness = None
        
    def set_pfd_status(self, status: str) -> bool:
        """
        设置PFD存在状态
        
        Args:
            status: PFD状态 ('none', 'present', 'indeterminate')
        
        Returns:
            bool: 是否设置成功
        """
        try:
            if status not in ['none', 'present', 'indeterminate']:
                raise ValueError(f"无效的PFD状态: {status}")
            
            self.pfd_status = status
            
            # 如果不是"present"，清除厚度测量
            if status != 'present':
                self.max_thickness = None
            
            logging.info(f"PFD状态设置为: {status}")
            return True
            
        except Exception as e:
            logging.error(f"设置PFD状态失败: {e}")
            return False
    
    def measure_max_thickness(self) -> float:
        """
        测量最大充盈缺损厚度
        
        Returns:
            float: 最大厚度（mm）
        """
        try:
            logging.info("开始测量PFD最大厚度")
            
            # TODO: 实现实际的测量逻辑
            # 1. 激活线性测量工具
            # 2. 引导用户在充盈缺损最厚处进行测量
            # 3. 获取测量结果
            
            # 临时模拟结果
            self.max_thickness = 2.3  # mm
            
            logging.info(f"PFD最大厚度测量完成: {self.max_thickness} mm")
            return self.max_thickness
            
        except Exception as e:
            logging.error(f"测量PFD厚度失败: {e}")
            return 0.0
    
    def set_manual_thickness(self, thickness: float) -> bool:
        """
        手动设置充盈缺损厚度
        
        Args:
            thickness: 厚度值（mm）
        
        Returns:
            bool: 是否设置成功
        """
        try:
            if thickness < 0:
                raise ValueError("厚度值不能为负数")
            
            self.max_thickness = thickness
            logging.info(f"手动设置PFD厚度: {thickness} mm")
            return True
            
        except Exception as e:
            logging.error(f"设置PFD厚度失败: {e}")
            return False
    
    def get_pfd_results(self) -> Dict[str, Any]:
        """
        获取PFD分析结果
        
        Returns:
            Dict: PFD分析结果
        """
        status_map = {
            'none': '无PFD',
            'present': '存在PFD',
            'indeterminate': '难以判定'
        }
        
        result = {
            'status': status_map.get(self.pfd_status, '未知'),
            'max_thickness': self.max_thickness,
            'raw_status': self.pfd_status
        }
        
        return result
    
    def reset(self):
        """重置PFD分析"""
        self.pfd_status = "none"
        self.max_thickness = None
        logging.info("PFD分析已重置")


class PasteAnalysisLogic:
    """PASTE分析主逻辑"""
    
    def __init__(self):
        self.halt_logic = HaltAnalysisLogic()
        self.relm_logic = RelmAnalysisLogic()
        self.sfd_logic = SfdAnalysisLogic()
        self.pfd_logic = PfdAnalysisLogic()
        
        logging.info("PASTE分析逻辑初始化完成")
    
    def get_halt_logic(self) -> HaltAnalysisLogic:
        """获取HALT分析逻辑"""
        return self.halt_logic
    
    def get_relm_logic(self) -> RelmAnalysisLogic:
        """获取RELM分析逻辑"""
        return self.relm_logic
    
    def get_sfd_logic(self) -> SfdAnalysisLogic:
        """获取SFD分析逻辑"""
        return self.sfd_logic
    
    def get_pfd_logic(self) -> PfdAnalysisLogic:
        """获取PFD分析逻辑"""
        return self.pfd_logic
    
    def get_complete_results(self) -> Dict[str, Any]:
        """
        获取完整的PASTE分析结果
        
        Returns:
            Dict: 完整的分析结果
        """
        try:
            results = {
                'halt': self.halt_logic.finish_halt_segmentation() if self.halt_logic.current_leaflet else None,
                'relm': self.relm_logic.calculate_relm() if (self.relm_logic.thickened_width and self.relm_logic.stent_diameter) else None,
                'sfd': self.sfd_logic.get_sfd_results(),
                'pfd': self.pfd_logic.get_pfd_results(),
                'timestamp': self._get_current_timestamp()
            }
            
            logging.info("获取完整PASTE分析结果")
            return results
            
        except Exception as e:
            logging.error(f"获取PASTE分析结果失败: {e}")
            return {'error': str(e)}
    
    def reset_all_analyses(self):
        """重置所有分析"""
        self.halt_logic.reset()
        self.relm_logic.reset()
        self.sfd_logic.reset()
        self.pfd_logic.reset()
        logging.info("所有PASTE分析已重置")
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """
        导出结果为字典格式（用于保存或传输）
        
        Returns:
            Dict: 可序列化的结果字典
        """
        return self.get_complete_results()
    
    def load_results_from_dict(self, data: Dict[str, Any]) -> bool:
        """
        从字典加载结果（用于恢复会话）
        
        Args:
            data: 包含分析结果的字典
        
        Returns:
            bool: 是否加载成功
        """
        try:
            # TODO: 实现从字典恢复状态的逻辑
            logging.info("从字典加载PASTE分析结果")
            return True
            
        except Exception as e:
            logging.error(f"加载PASTE分析结果失败: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def cleanup(self):
        """清理资源"""
        self.reset_all_analyses()
        logging.info("PASTE分析逻辑清理完成")

    def validate_analysis_completeness(self) -> Dict[str, bool]:
        """
        验证各项分析的完整性
        
        Returns:
            Dict: 各项分析的完成状态
        """
        completeness = {
            'halt_complete': self.halt_logic.current_leaflet is not None and self.halt_logic.halt_area is not None,
            'relm_complete': (self.relm_logic.thickened_width is not None and 
                            self.relm_logic.stent_diameter is not None),
            'sfd_complete': True,  # SFD只需要状态选择
            'pfd_complete': True,  # PFD只需要状态选择（如果是present则需要厚度）
        }
        
        # 对于PFD，如果状态是present，则需要厚度测量
        if self.pfd_logic.pfd_status == 'present':
            completeness['pfd_complete'] = self.pfd_logic.max_thickness is not None
        
        return completeness

    def get_summary_report(self) -> str:
        """
        生成PASTE分析摘要报告
        
        Returns:
            str: 摘要报告文本
        """
        try:
            completeness = self.validate_analysis_completeness()
            results = self.get_complete_results()
            
            report_lines = [
                "PASTE分析摘要报告",
                "=" * 30,
                ""
            ]
            
            # HALT摘要
            if completeness['halt_complete'] and results.get('halt'):
                halt_data = results['halt']
                report_lines.extend([
                    f"HALT分析 - {halt_data.get('leaflet', 'Unknown')}瓣叶:",
                    f"  • 增厚面积: {halt_data.get('halt_area', 'N/A')} mm²",
                    f"  • 占比: {halt_data.get('percentage', 'N/A'):.1f}%",
                    f"  • 分级: {halt_data.get('grade', 'N/A')}",
                    ""
                ])
            else:
                report_lines.extend(["HALT分析: 未完成", ""])
            
            # RELM摘要
            if completeness['relm_complete'] and results.get('relm'):
                relm_data = results['relm']
                report_lines.extend([
                    f"RELM分析 - {relm_data.get('leaflet', 'Unknown')}瓣叶:",
                    f"  • 增厚宽度: {relm_data.get('thickened_width', 'N/A')} mm",
                    f"  • 支架内径: {relm_data.get('stent_diameter', 'N/A')} mm",
                    f"  • RELM值: {relm_data.get('relm_value', 'N/A'):.1f}%",
                    f"  • 分级: {relm_data.get('grade', 'N/A')}",
                    ""
                ])
            else:
                report_lines.extend(["RELM分析: 未完成", ""])
            
            # SFD摘要
            sfd_data = results.get('sfd', {})
            report_lines.extend([
                f"SFD分析: {sfd_data.get('status', 'N/A')}",
                f"  • 受累窦部: {', '.join(sfd_data.get('affected_sinuses', [])) or '无'}",
                ""
            ])
            
            # PFD摘要
            pfd_data = results.get('pfd', {})
            thickness_text = f"{pfd_data.get('max_thickness', 'N/A')} mm" if pfd_data.get('max_thickness') else '无需测量'
            report_lines.extend([
                f"PFD分析: {pfd_data.get('status', 'N/A')}",
                f"  • 最大厚度: {thickness_text}",
                ""
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logging.error(f"生成PASTE摘要报告失败: {e}")
            return f"生成摘要报告时出错: {str(e)}"
