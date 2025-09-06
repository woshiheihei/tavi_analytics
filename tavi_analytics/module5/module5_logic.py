"""
模块五业务逻辑层（占位）

交接对齐相关逻辑将在后续补充。
"""

import logging
from typing import Optional

try:
    from ..core.session import TAVRStudySession
except ImportError:
    # 兼容直接运行
    import os
    import sys
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.session import TAVRStudySession


class Module5Logic:
    """模块五业务逻辑类"""

    def __init__(self, session: Optional[TAVRStudySession] = None) -> None:
        self.session: Optional[TAVRStudySession] = session
        self._current_phase: str = 'end_diastole'
        self._logger = logging.getLogger(__name__)
        self._logger.info("Module5Logic 初始化完成")

    def set_session(self, session: TAVRStudySession) -> None:
        self.session = session
        self._logger.info("Module5Logic session 已更新")

    def cleanup(self) -> None:
        self._logger.info("清理模块五逻辑资源")

    # 期像状态（与模块3/4接口保持一致）
    def set_current_phase(self, phase: str) -> None:
        if phase in ('end_diastole', 'end_systole'):
            self._current_phase = phase
            self._logger.info(f"Module5Logic 当前期像: {phase}")
        else:
            self._logger.warning(f"Module5Logic 收到无效期像: {phase}")

    def get_current_phase(self) -> str:
        return self._current_phase
